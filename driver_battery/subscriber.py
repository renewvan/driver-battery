"""Persistent MQTT subscription against the Victron Venus OS GX device's
own broker — separate connection from the van-bus Publisher. Per
research ticket 05: Venus OS stops publishing a path once its last
subscriber disconnects, so both topics below must stay subscribed
continuously, never connect/read/disconnect.

Thin I/O adapter around paho-mqtt; not unit-tested (see mapping.py for
the tested seam).
"""
from __future__ import annotations

import json
import logging

import paho.mqtt.client as mqtt

from driver_battery.config import AppConfig
from driver_battery.mapping import map_batteries, map_charge_state
from driver_battery.publisher import Publisher

logger = logging.getLogger(__name__)


def _batteries_topic(portal_id: str) -> str:
    return f"N/{portal_id}/system/0/Batteries"


def _system_state_topic(portal_id: str) -> str:
    return f"N/{portal_id}/system/0/SystemState/State"


class Subscriber:
    def __init__(self, config: AppConfig, publisher: Publisher) -> None:
        self._config = config
        self._publisher = publisher
        self._batteries_topic = _batteries_topic(config.victron.portal_id)
        self._system_state_topic = _system_state_topic(config.victron.portal_id)

        self._client = mqtt.Client(client_id="driver-battery-victron", clean_session=False)
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):  # noqa: ANN001
        if rc == 0:
            logger.info(
                "Connected to Victron GX broker %s:%s", self._config.victron.host, self._config.victron.port
            )
            # Persistent subscriptions — Venus OS stops publishing once
            # the last subscriber disconnects, so these must never drop.
            client.subscribe(self._batteries_topic, qos=1)
            client.subscribe(self._system_state_topic, qos=1)
        else:
            logger.error("Victron GX broker connect failed with rc=%s", rc)

    def _on_message(self, client, userdata, msg):  # noqa: ANN001
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Malformed Victron payload on topic=%s", msg.topic)
            return

        if msg.topic == self._batteries_topic:
            pairs = map_batteries(payload, self._config.instance_to_id)
        elif msg.topic == self._system_state_topic:
            pairs = map_charge_state(payload, self._config.instance_to_id)
        else:
            return

        for topic, value in pairs:
            self._publisher.publish(topic, value)

    def run_forever(self) -> None:
        self._client.connect(self._config.victron.host, self._config.victron.port)
        self._client.loop_forever()
