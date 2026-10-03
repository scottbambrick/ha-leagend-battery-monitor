"""Polls a Leagend BM2 / BM6 battery monitor.

Every few minutes: connect (through whichever connectable adapter or proxy
hears it best), take one reading, disconnect. A reading is also taken as
soon as the monitor is heard again after a gap, so a car coming home shows
up quickly. Values keep their last reading while the car is away.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    BM6_REQUEST,
    KEYS,
    MODEL_BM6,
    NOTIFY_CHAR,
    POLL_MINUTES,
    READ_TIMEOUT,
    WRITE_CHAR,
)

_LOGGER = logging.getLogger(__name__)


def _crypt(key: bytes, data: bytes, encrypt: bool) -> bytes:
    """AES-128-CBC with an all-zero IV over the first 16 bytes."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
    op = cipher.encryptor() if encrypt else cipher.decryptor()
    return op.update(data[:16]) + op.finalize()


def parse(model: str, raw: bytes) -> dict | None:
    """Decode one notification; None if it isn't a usable reading."""
    if len(raw) < 16:
        return None
    out = _crypt(KEYS[model], raw, encrypt=False)

    if model == MODEL_BM6:
        # Only replies to our d15507 request; byte 3 = 0xFF is the empty
        # acknowledgement frame
        if out[0:3] != b"\xd1\x55\x07" or out[3] == 0xFF:
            return None
        volts = (((out[7] & 0x0F) << 8) | out[8]) / 100  # 12-bit field
        if volts <= 0:
            return None
        temp = -out[4] if out[3] == 0x01 else out[4]  # sign flag
        status = {0: "Normal", 2: "Charging"}.get(out[5], "Low charge")
        return {
            "voltage": volts,
            "temperature": temp,
            "state_of_charge": out[6],
            "status": status,
        }

    # The BM2 streams readings as soon as it's connected
    volts = ((out[2] | (out[1] << 8)) >> 4) / 100
    return {"voltage": volts} if volts > 0 else None


class LeagendCoordinator(DataUpdateCoordinator[dict]):
    """One battery monitor."""

    def __init__(
        self, hass: HomeAssistant, address: str, model: str, name: str
    ) -> None:
        """Set up polling for the monitor at `address`."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(minutes=POLL_MINUTES),
        )
        self.address = address.upper()
        self.model = model
        self.last_seen: datetime | None = None   # last successful reading
        self.last_heard: datetime | None = None  # last advertisement
        self.last_error: str | None = None
        self._lock = asyncio.Lock()
        self.data = {}

    @callback
    def async_advertisement(self, service_info, change) -> None:
        """Heard it advertise: read now if the last reading is stale."""
        self.last_heard = dt_util.utcnow()
        stale = self.last_seen is None or (
            dt_util.utcnow() - self.last_seen
            > timedelta(minutes=POLL_MINUTES)
        )
        if stale and not self._lock.locked():
            self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> dict:
        """Take one reading; keep the previous one if it fails."""
        async with self._lock:
            try:
                reading = await self._read()
            except Exception as err:  # noqa: BLE001
                # Out of range, busy proxy, timeout...: not an error
                self.last_error = f"{type(err).__name__}: {err}"
                _LOGGER.debug("%s: no reading (%s)", self.name,
                              self.last_error)
                return self.data or {}
            self.last_error = None
            self.last_seen = dt_util.utcnow()
            return reading

    async def _read(self) -> dict:
        """Connect, ask for (BM6) or wait for (BM2) a reading, hang up."""
        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            raise ConnectionError(
                "not heard by any connectable Bluetooth adapter or proxy"
            )
        got: asyncio.Future = self.hass.loop.create_future()

        def on_notify(_sender, data: bytearray) -> None:
            if got.done():
                return
            reading = parse(self.model, bytes(data))
            if reading:
                got.set_result(reading)

        client = await establish_connection(
            BleakClientWithServiceCache, device, self.name, max_attempts=2
        )
        try:
            await client.start_notify(NOTIFY_CHAR, on_notify)
            if self.model == MODEL_BM6:
                # Let the subscription settle, then ask for a reading
                await asyncio.sleep(1)
                payload = _crypt(KEYS[MODEL_BM6], BM6_REQUEST, encrypt=True)
                try:
                    await client.write_gatt_char(
                        WRITE_CHAR, payload, response=True
                    )
                except Exception:  # noqa: BLE001
                    # Some firmware only takes write-without-response
                    await client.write_gatt_char(
                        WRITE_CHAR, payload, response=False
                    )
            return await asyncio.wait_for(got, READ_TIMEOUT)
        finally:
            await client.disconnect()
