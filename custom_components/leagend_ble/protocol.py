"""Leagend BM2 / BM6 notification decoding (no Home Assistant imports).

Notifications and requests are AES-128-CBC with an all-zero IV over the
first 16 bytes, using a fixed key per model (see const.KEYS).
"""
from __future__ import annotations

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .const import KEYS, MODEL_BM6

BM6_STATUS = {0: "Normal", 2: "Charging"}
BM6_STATUS_OTHER = "Low charge"


def crypt(key: bytes, data: bytes, encrypt: bool) -> bytes:
    """AES-128-CBC with an all-zero IV over the first 16 bytes."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
    op = cipher.encryptor() if encrypt else cipher.decryptor()
    return op.update(data[:16]) + op.finalize()


def parse(model: str, raw: bytes) -> dict | None:
    """Decode one notification; None if it isn't a usable reading."""
    if len(raw) < 16:
        return None
    out = crypt(KEYS[model], raw, encrypt=False)

    if model == MODEL_BM6:
        # Only replies to our d15507 request; byte 3 = 0xFF is the empty
        # acknowledgement frame
        if out[0:3] != b"\xd1\x55\x07" or out[3] == 0xFF:
            return None
        volts = (((out[7] & 0x0F) << 8) | out[8]) / 100  # 12-bit field
        if volts <= 0:
            return None
        temp = -out[4] if out[3] == 0x01 else out[4]  # sign flag
        return {
            "voltage": volts,
            "temperature": temp,
            "state_of_charge": out[6],
            "status": BM6_STATUS.get(out[5], BM6_STATUS_OTHER),
        }

    # The BM2 streams readings as soon as it's connected
    volts = ((out[2] | (out[1] << 8)) >> 4) / 100
    return {"voltage": volts} if volts > 0 else None
