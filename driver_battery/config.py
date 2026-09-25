"""Config sourced from environment variables — matches `hub`'s
`docker-compose.yml` `battery:` service block, the contract between this
repo and the deployment manifest. Two separate MQTT connections: the van
bus (publish) and the Victron GX device's own broker (subscribe).

`INSTANCE_TO_ID` is the static `instance -> id` map from
`.scratch/renewvan-hub-v0/issues/04-battery-soc-topic-mapping.md`: `id`
(the `van/battery/<id>/...` path segment) is deliberately not derived
from Victron's `name` field. v0 ships exactly the one bank this house has.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

INSTANCE_TO_ID: dict[int, str] = {
    0: "house",
}


@dataclass(frozen=True)
class MqttConfig:
    host: str
    port: int
    username: str | None
    password: str | None


@dataclass(frozen=True)
class VictronConfig:
    host: str
    port: int
    portal_id: str


@dataclass(frozen=True)
class AppConfig:
    mqtt: MqttConfig
    victron: VictronConfig
    instance_to_id: dict[int, str]


def load_config() -> AppConfig:
    return AppConfig(
        mqtt=MqttConfig(
            host=os.environ.get("MQTT_HOST", "mosquitto"),
            port=int(os.environ.get("MQTT_PORT", "1883")),
            username=os.environ.get("MQTT_USERNAME") or None,
            password=os.environ.get("MQTT_PASSWORD") or None,
        ),
        victron=VictronConfig(
            host=os.environ["VICTRON_MQTT_HOST"],
            port=int(os.environ.get("VICTRON_MQTT_PORT", "1883")),
            portal_id=os.environ["VICTRON_PORTAL_ID"],
        ),
        instance_to_id=INSTANCE_TO_ID,
    )
