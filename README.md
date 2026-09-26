# driver-battery

Victron Venus OS MQTT → renewvan-bus battery remap. Bridges the house
battery bank's existing native-MQTT feed (Venus OS's `dbus-mqtt`
service on the GX device) onto the shared `renewvan/battery/<id>/*` schema —
no new sensing, just a topic remap, same shape as `driver-tank` but for
an existing feed. Per
`hub/.scratch/renewvan-hub-v0-build/issues/04-victron-battery-bridge.md`
and the topic-mapping decision in
`hub/.scratch/renewvan-hub-v0/issues/04-battery-soc-topic-mapping.md`.

## Two persistent MQTT connections

- **Victron GX device broker** (subscribe only): `N/{portalId}/system/0/Batteries`
  and `N/{portalId}/system/0/SystemState/State`. Both stay subscribed
  continuously — Venus OS stops publishing a path once its last
  subscriber disconnects.
- **Renewvan bus** (publish only, retained): `renewvan/battery/<id>/*`, plus
  driver liveness on `renewvan/battery/health` (`online`/`offline` via MQTT
  LWT) — deliberately 3 segments, not 4, so it can't be mistaken for a
  `battery` entity keyed by a fake `health`/`driver` id.

## Mapping

`id` is looked up via a static `instance -> id` map
(`driver_battery/config.py:INSTANCE_TO_ID`), never from Victron's `name`
field. v0 ships one entry: `0 -> "house"`.

| Victron `Batteries[]` field | → topic | |
|---|---|---|
| `soc` | `renewvan/battery/<id>/soc_pct` | direct copy |
| `voltage` | `renewvan/battery/<id>/voltage_v` | direct copy |
| `current` | `renewvan/battery/<id>/current_a` | direct copy, signed |
| `power` | `renewvan/battery/<id>/power_w` | direct copy, signed |
| `temperature` | `renewvan/battery/<id>/temperature_c` | direct copy |

`Batteries[].state`/`.bmsstate` are never read — coarse per-battery
Idle/Charging/Discharging and a raw BMS passthrough, neither carries
charge-phase info.

`charge_state` comes from the separate `SystemState/State` topic (a
single system-wide value, not per-bank) and is fanned out to every `id`
in the static map. Full code → `charge_state` table in
`driver_battery/mapping.py:CHARGE_STATE_CODES`; any code not in the
table maps to `unknown`.

The mapping is a pure function (`driver_battery/mapping.py`, no
network/MQTT client) — this is what `tests/test_mapping.py` exercises
against fixture Victron payloads, no live broker or GX device required.

## Configuration

Environment variables (matches `hub`'s `docker-compose.yml` `driver-battery:`
service block):

| Variable | Default | Notes |
|---|---|---|
| `MQTT_HOST` | `mosquitto` | Renewvan bus broker |
| `MQTT_PORT` | `1883` | |
| `MQTT_USERNAME` | _(none)_ | |
| `MQTT_PASSWORD` | _(none)_ | |
| `VICTRON_MQTT_HOST` | _(required)_ | The GX device's own broker |
| `VICTRON_MQTT_PORT` | `1883` | |
| `VICTRON_PORTAL_ID` | _(required)_ | Venus OS portal ID, from the GX device |

## Running

```bash
pip install -r requirements.txt
VICTRON_MQTT_HOST=192.168.1.50 VICTRON_PORTAL_ID=abc123 python -m driver_battery.main
```

## Testing

```bash
pip install -r requirements.txt -r requirements-test.txt
pytest tests/ -v
```

Mapping tests run with fixture Victron payloads only — no MQTT broker
or GX device required.

## Releasing

Tagging a GitHub release builds and publishes
`ghcr.io/<owner>/driver-battery:<tag>`, which `hub`'s deployment compose
file pins by tag (never builds from source — see
`hub/docs/adr/0001-compose-services-via-pinned-images-not-git-submodules.md`).
