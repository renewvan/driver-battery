"""Fixture-payload tests for the Victron -> `van/battery/<id>/*` mapping
— no live broker or GX device required.
"""
from driver_battery.mapping import map_batteries, map_charge_state
from tests.fixtures import victron as fx

INSTANCE_TO_ID = {0: "house"}


def test_batteries_single_bank_maps_all_direct_copy_fields():
    pairs = dict(map_batteries(fx.BATTERIES_SINGLE_BANK, INSTANCE_TO_ID))
    assert pairs["van/battery/house/soc_pct"] == 87.2
    assert pairs["van/battery/house/voltage_v"] == 13.1
    assert pairs["van/battery/house/current_a"] == -4.6
    assert pairs["van/battery/house/power_w"] == -60.3
    assert pairs["van/battery/house/temperature_c"] == 21.5


def test_batteries_never_emits_state_or_bmsstate_fields():
    pairs = dict(map_batteries(fx.BATTERIES_SINGLE_BANK, INSTANCE_TO_ID))
    assert not any("state" in topic and "charge_state" not in topic for topic in pairs)
    assert "van/battery/house/state" not in pairs
    assert "van/battery/house/bmsstate" not in pairs


def test_unmapped_instance_is_dropped():
    pairs = dict(map_batteries(fx.BATTERIES_WITH_UNMAPPED_INSTANCE, INSTANCE_TO_ID))
    # Only instance 0 ("house") is in the static map; instance 1 has no id.
    assert pairs["van/battery/house/soc_pct"] == 50.0
    assert not any(topic.startswith("van/battery/1/") for topic in pairs)
    assert len(pairs) == 5  # exactly the 5 direct-copy fields for "house"


def test_empty_batteries_array_maps_to_nothing():
    assert map_batteries(fx.BATTERIES_EMPTY, INSTANCE_TO_ID) == []


def test_charge_state_bulk():
    pairs = dict(map_charge_state(fx.SYSTEM_STATE_BULK, INSTANCE_TO_ID))
    assert pairs["van/battery/house/charge_state"] == "bulk"


def test_charge_state_off():
    pairs = dict(map_charge_state(fx.SYSTEM_STATE_OFF, INSTANCE_TO_ID))
    assert pairs["van/battery/house/charge_state"] == "off"


def test_charge_state_scheduled_recharge_high_code():
    pairs = dict(map_charge_state(fx.SYSTEM_STATE_SCHEDULED_RECHARGE, INSTANCE_TO_ID))
    assert pairs["van/battery/house/charge_state"] == "scheduled_recharge"


def test_charge_state_unrecognized_code_falls_back_to_unknown():
    pairs = dict(map_charge_state(fx.SYSTEM_STATE_UNRECOGNIZED_CODE, INSTANCE_TO_ID))
    assert pairs["van/battery/house/charge_state"] == "unknown"


def test_charge_state_fans_out_to_every_id_in_the_map():
    multi_bank_map = {0: "house", 1: "starter"}
    pairs = dict(map_charge_state(fx.SYSTEM_STATE_BULK, multi_bank_map))
    assert pairs["van/battery/house/charge_state"] == "bulk"
    assert pairs["van/battery/starter/charge_state"] == "bulk"
