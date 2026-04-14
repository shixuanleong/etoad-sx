#!/usr/bin/env python3
"""Quick connectivity check for a Bio-Logic potentiostat.

This script:
1) Loads a potentiostat config YAML.
2) Attempts to connect using EChemController.
3) Runs BL_TestConnection.
4) Disconnects cleanly.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from etoad.HardwareController.Potentiostat import EChemController


class HeadlessLogger:
    """Minimal logger adapter expected by EChemController."""

    def __init__(self, name: str = "potentiostat-connection-check"):
        self._logger = logging.getLogger(name)

    def debug(self, message: str) -> None:
        self._logger.debug(message)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def start_plot(self, *_args, **_kwargs) -> None:
        return

    def update_plot(self, *_args, **_kwargs) -> None:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Bio-Logic potentiostat connectivity")
    parser.add_argument(
        "--config-file",
        default="Tests/test_settings/potentiostat_settings_ch_1.yaml",
        help="Path to potentiostat config YAML",
    )
    parser.add_argument(
        "--simulation-mode",
        action="store_true",
        help="Run in simulation mode (for software-only checks)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config_file = Path(args.config_file).expanduser().resolve()
    if not config_file.exists():
        print(f"FAIL: config file not found: {config_file}")
        return 2

    logger = HeadlessLogger()
    controller = None

    try:
        controller = EChemController(
            config_file=config_file,
            logger=logger,
            simulation_mode=args.simulation_mode,
        )

        if not args.simulation_mode:
            controller._dll_functions("BL_TestConnection", controller.device_id)

        port = controller.config.get("port", "unknown")
        print("PASS: potentiostat is reachable")
        print(f"config: {config_file}")
        print(f"port: {port}")
        print(f"device_id: {controller.device_id}")
        return 0

    except Exception as exc:
        print("FAIL: potentiostat is not reachable")
        print(f"reason: {type(exc).__name__}: {exc}")
        return 1

    finally:
        if controller is not None:
            try:
                controller.disconnect()
            except Exception:
                logger.error("Failed to disconnect cleanly after connectivity check.")


if __name__ == "__main__":
    sys.exit(main())
