"""Pure mapping: Victron Venus OS MQTT payloads -> `renewvan/battery/<id>/*`
publishes. No network, no MQTT client — this is the seam the ticket's
acceptance criteria unit-test against fixture Victron payloads.

Two independent upstream topics, two independent mapping functions (see
`.scratch/renewvan-hub-v0/issues/04-battery-soc-topic-mapping.md`):

- `map_batteries`: `N/{portalId}/system/0/Batteries` array -> per-battery
  direct-copy fields, keyed by the static `instance -> id` map. An
  element whose `instance` isn't in the map is dropped (id unknown).
  `state`/`bmsstate` are deliberately never read — coarse Idle/Charging/
  Discharging and a raw per-battery BMS passthrough, neither carrying the
  charge-phase info `charge_state` needs.
- `map_charge_state`: `N/{portalId}/system/0/SystemState/State` -> the
  single system-wide charge-stage value, fanned out to every id in the
  map (Victron exposes charge stage per-system, not per-bank).
"""

from __future__ import annotations

# Victron `Batteries[]` field -> v0.1 battery entity property. Direct
# copies: Victron already uses the same +charging/-discharging sign
# convention as the v0.1 schema, no unit conversion needed.
_BATTERY_FIELDS: dict[str, str] = {
    "soc": "soc_pct",
    "voltage": "voltage_v",
    "current": "current_a",
    "power": "power_w",
    "temperature": "temperature_c",
}

# Victron SystemState/State code -> v0.1 charge_state enum. Any code not
# in this table maps to "unknown" (forward-compat with future Venus OS
# firmware). Source: victronenergy/venus wiki "Aggregated System State".
CHARGE_STATE_CODES: dict[int, str] = {
    0: "off",
    1: "low_power",
    2: "fault",
    3: "bulk",
    4: "absorption",
    5: "float",
    6: "storage",
    7: "equalize",
    8: "passthru",
    9: "inverting",
    10: "assisting",
    244: "sustain",
    252: "external_control",
    256: "discharging",
    257: "sustain_ess",
    258: "recharge",
    259: "scheduled_recharge",
}


def battery_topic(entity_id: str, prop: str) -> str:
    return f"renewvan/battery/{entity_id}/{prop}"


def map_batteries(payload: dict, instance_to_id: dict[int, str]) -> list[tuple[str, object]]:
    """Map a decoded `N/{portalId}/system/0/Batteries` payload
    (`{"value": [...]}`) to a list of `(topic, value)` pairs.

    Elements for an `instance` not present in `instance_to_id` are
    dropped — no id to publish under.
    """
    elements = payload.get("value") or []
    results: list[tuple[str, object]] = []
    for element in elements:
        instance = element.get("instance")
        entity_id = instance_to_id.get(instance)
        if entity_id is None:
            continue
        for victron_field, prop in _BATTERY_FIELDS.items():
            if victron_field in element:
                results.append((battery_topic(entity_id, prop), element[victron_field]))
    return results


def map_charge_state(payload: dict, instance_to_id: dict[int, str]) -> list[tuple[str, object]]:
    """Map a decoded `N/{portalId}/system/0/SystemState/State` payload
    (`{"value": <code>}`) to a `(topic, charge_state)` pair per id in
    `instance_to_id` — the single system-wide value fans out to every
    battery bank this driver emits.
    """
    code = payload.get("value")
    charge_state = CHARGE_STATE_CODES.get(code, "unknown")
    return [
        (battery_topic(entity_id, "charge_state"), charge_state)
        for entity_id in instance_to_id.values()
    ]
