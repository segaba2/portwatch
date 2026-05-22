"""Command-line interface for portwatch."""

import argparse
import sys
from pathlib import Path

from portwatch.config import load_config_or_default
from portwatch.daemon import run_once, run_daemon


DEFAULT_CONFIG_PATH = Path("portwatch/portwatch.toml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portwatch",
        description="Monitor open ports and alert on unexpected changes.",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="FILE",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to TOML config file (default: %(default)s)",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # scan-once subcommand
    scan_parser = subparsers.add_parser(
        "scan",
        help="Run a single scan and exit.",
    )
    scan_parser.add_argument(
        "--no-notify",
        action="store_true",
        default=False,
        help="Skip sending notifications even if changes are detected.",
    )

    # daemon subcommand
    daemon_parser = subparsers.add_parser(
        "daemon",
        help="Run continuously, scanning at the configured interval.",
    )
    daemon_parser.add_argument(
        "--interval",
        type=int,
        default=None,
        metavar="SECONDS",
        help="Override the scan interval from config.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    config = load_config_or_default(args.config)

    if args.command == "scan":
        notify = not args.no_notify
        run_once(config, notify=notify)
        return 0

    if args.command == "daemon":
        if args.interval is not None:
            config = config._replace(interval=args.interval)
        run_daemon(config)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
