"""Fixture Victron dbus-mqtt payloads (decoded `{"value": ...}` envelope),
shaped per `.scratch/renewvan-hub-v0/issues/05-victron-mqtt-battery-topics-research.md`.
"""

# Single-bank Batteries array, instance 0 mapped to "house" per v0's
# static instance-map.
BATTERIES_SINGLE_BANK = {
    "value": [
        {
            "instance": 0,
            "name": "House battery",
            "soc": 87.2,
            "voltage": 13.1,
            "current": -4.6,
            "power": -60.3,
            "temperature": 21.5,
            # Coarse Idle/Charging/Discharging + raw BMS passthrough —
            # deliberately never read for charge_state.
            "state": 2,
            "bmsstate": 2,
        }
    ]
}

# An extra bank at an instance not in the v0 static map — must be dropped.
BATTERIES_WITH_UNMAPPED_INSTANCE = {
    "value": [
        {
            "instance": 0,
            "soc": 50.0,
            "voltage": 12.8,
            "current": 0.0,
            "power": 0.0,
            "temperature": 20.0,
        },
        {
            "instance": 1,
            "soc": 90.0,
            "voltage": 12.9,
            "current": 1.0,
            "power": 12.9,
            "temperature": 19.0,
        },
    ]
}

BATTERIES_EMPTY = {"value": []}

SYSTEM_STATE_BULK = {"value": 3}
SYSTEM_STATE_OFF = {"value": 0}
SYSTEM_STATE_SCHEDULED_RECHARGE = {"value": 259}
SYSTEM_STATE_UNRECOGNIZED_CODE = {"value": 9999}
