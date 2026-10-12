"""Decoding of BM2 / BM6 notifications (built by encrypting known frames)."""
from custom_components.leagend_ble.const import (
    BM6_REQUEST,
    KEYS,
    MODEL_BM2,
    MODEL_BM6,
)
from custom_components.leagend_ble.protocol import crypt, parse


def _frame(model: str, plain: bytes) -> bytes:
    return crypt(KEYS[model], plain.ljust(16, b"\0"), encrypt=True)


def test_crypt_round_trip():
    enc = crypt(KEYS[MODEL_BM6], BM6_REQUEST, encrypt=True)
    assert enc != BM6_REQUEST
    assert crypt(KEYS[MODEL_BM6], enc, encrypt=False) == BM6_REQUEST


def test_bm6_reading():
    # d15507 | sign 0 | 25 C | status 0 | 80 % | 12.60 V (0x4EC)
    plain = bytes([0xD1, 0x55, 0x07, 0x00, 25, 0x00, 80, 0x04, 0xEC])
    assert parse(MODEL_BM6, _frame(MODEL_BM6, plain)) == {
        "voltage": 12.6,
        "temperature": 25,
        "state_of_charge": 80,
        "status": "Normal",
    }


def test_bm6_negative_temperature_and_status():
    plain = bytes([0xD1, 0x55, 0x07, 0x01, 5, 0x02, 99, 0x05, 0x46])
    reading = parse(MODEL_BM6, _frame(MODEL_BM6, plain))
    assert reading["temperature"] == -5
    assert reading["status"] == "Charging"
    assert reading["voltage"] == 13.5
    plain = bytes([0xD1, 0x55, 0x07, 0x00, 20, 0x01, 10, 0x04, 0x4C])
    assert parse(MODEL_BM6, _frame(MODEL_BM6, plain))["status"] == "Low charge"


def test_bm6_ignores_acks_other_replies_and_short_frames():
    ack = bytes([0xD1, 0x55, 0x07, 0xFF])
    assert parse(MODEL_BM6, _frame(MODEL_BM6, ack)) is None
    other = bytes([0xD1, 0x55, 0x08, 0x00, 25, 0, 80, 0x04, 0xEC])
    assert parse(MODEL_BM6, _frame(MODEL_BM6, other)) is None
    assert parse(MODEL_BM6, b"\x01\x02") is None


def test_bm2_reading():
    # 12.34 V -> 1234 << 4 = 0x4D20 in bytes 1-2
    plain = bytes([0xF5, 0x4D, 0x20])
    assert parse(MODEL_BM2, _frame(MODEL_BM2, plain)) == {"voltage": 12.34}


def test_bm2_zero_voltage_is_not_a_reading():
    assert parse(MODEL_BM2, _frame(MODEL_BM2, bytes([0xF5, 0, 0]))) is None
