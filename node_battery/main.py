#!/usr/bin/env python3
"""node-battery entrypoint."""

from __future__ import annotations

import argparse
import logging

from node_battery.config import load_config
from node_battery.publisher import Publisher
from node_battery.subscriber import Subscriber


def main() -> None:
    parser = argparse.ArgumentParser(
        description="node-battery: Victron Venus OS MQTT -> renewvan-bus battery remap"
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    config = load_config()
    publisher = Publisher(config.mqtt)
    publisher.connect()
    subscriber = Subscriber(config, publisher)
    try:
        subscriber.run_forever()
    finally:
        publisher.disconnect()


if __name__ == "__main__":
    main()
