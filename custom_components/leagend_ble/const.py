"""Constants for the Leagend BM2 / BM6 battery monitors."""

DOMAIN = "leagend_ble"

CONF_MODEL = "model"
MODEL_BM2 = "bm2"
MODEL_BM6 = "bm6"

# Notifications and commands are AES-128-CBC with an all-zero IV, using a
# fixed key per model (the same for every unit of that model, as used by
# the manufacturer's app and documented by several open-source projects).
KEYS = {
    MODEL_BM2: bytes.fromhex("6c656167656e64fffe31383832343636"),
    MODEL_BM6: bytes.fromhex("6c656167656e64fffe30313030303039"),
}

# GATT characteristics (service FFF0)
NOTIFY_CHAR = "0000fff4-0000-1000-8000-00805f9b34fb"
WRITE_CHAR = "0000fff3-0000-1000-8000-00805f9b34fb"

# The BM6 only replies when asked: d15507 = voltage / temperature / charge
BM6_REQUEST = bytes.fromhex("d1550700000000000000000000000000")

POLL_MINUTES = 5
# "In range" while it answered within this long (tolerates two missed polls)
IN_RANGE_MINUTES = 16
READ_TIMEOUT = 15
