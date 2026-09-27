"""Persistent MQTT connection to the renewvan bus with LWT and a retained-topic
publish helper. Same shape as node-tank's publisher.py.
"""
from __future__ import annotations

import json
import logging

import paho.mqtt.client as mqtt

from node_battery.config import MqttConfig

logger = logging.getLogger(__name__)

HEALTH_TOPIC = "renewvan/battery/health"


class Publisher:
    def __init__(self, config: MqttConfig) -> None:
        self._config = config
        self._client = mqtt.Client(client_id="node-battery", clean_session=False)
        if config.username:
            self._client.username_pw_set(config.username, config.password)
        self._client.will_set(HEALTH_TOPIC, payload="offline", qos=1, retain=True)
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        self._client.on_connect = self._on_connect

    def _on_connect(self, client, userdata, flags, rc):  # noqa: ANN001
        if rc == 0:
            logger.info("Connected to renewvan-bus MQTT broker %s:%s", self._config.host, self._config.port)
            client.publish(HEALTH_TOPIC, payload="online", qos=1, retain=True)
        else:
            logger.error("Renewvan-bus MQTT connect failed with rc=%s", rc)

    def connect(self) -> None:
        self._client.connect(self._config.host, self._config.port)
        self._client.loop_start()

    def publish(self, topic: str, payload: object) -> None:
        self._client.publish(topic, payload=json.dumps(payload), qos=1, retain=True)

    def disconnect(self) -> None:
        self._client.publish(HEALTH_TOPIC, payload="offline", qos=1, retain=True)
        self._client.loop_stop()
        self._client.disconnect()
