"""Command line entrypoints for navigating the Compute-God universe catalogue.

The project exposes a rich set of playful yet mathematically precise modules.
While the :func:`compute_god.guidance_desk` helper already provides a Pythonic
API to explore the catalogue, reaching for it from the terminal previously
required ad-hoc scripts.  This module introduces a small but ergonomic command
line interface so explorers can list stations, inspect entries and resolve
references without writing Python code.

Example usage::

    $ compute-god stations
    core
      - God
      - Universe
      ...

    $ compute-god station marketing --format json
    {
      "description": "营销漏斗动力学。",
      "entries": [
        "FunnelParameters",
        "marketing_universe",
        ...
      ]
    }

    $ compute-god resolve core.God
    <class 'compute_god.core.universe.God'>

The interface favours discoverability and deterministic output, making it
useful both for human operators and for generating documentation snippets.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping

from . import guidance_desk as _guidance_desk
from . import __version__ as _package_version


def _format_station_text(name: str, description: str, entries: Iterable[str]) -> str:
    lines = [name]
    if description:
        lines.append(f"  {description}")
    for entry in entries:
        lines.append(f"  - {entry}")
    return "\n".join(lines)


def _station_payload(description: str, entries: Iterable[str]) -> Mapping[str, object]:
    return {
        "description": description,
        "entries": list(entries),
    }


def _handle_stations(args: argparse.Namespace) -> int:
    desk = _guidance_desk()
    if args.format == "json":
        payload = {
            name: _station_payload(station.description, station.catalog())
            for name, station in desk.items()
        }
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    blocks = [
        _format_station_text(name, station.description, station.catalog())
        for name, station in desk.items()
    ]
    sys.stdout.write("\n\n".join(blocks) + "\n")
    return 0


def _handle_station(args: argparse.Namespace) -> int:
    desk = _guidance_desk()
    try:
        station = desk[args.name]
    except KeyError:
        sys.stderr.write(f"unknown station: {args.name}\n")
        return 1

    if args.format == "json":
        json.dump(
            _station_payload(station.description, station.catalog()),
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(_format_station_text(args.name, station.description, station.catalog()) + "\n")
    return 0


def _handle_resolve(args: argparse.Namespace) -> int:
    desk = _guidance_desk()
    try:
        obj = desk.resolve(args.reference)
    except KeyError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    sys.stdout.write(repr(obj) + "\n")
    return 0


def _handle_version(_: argparse.Namespace) -> int:
    sys.stdout.write(f"{_package_version}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level CLI argument parser."""

    parser = argparse.ArgumentParser(description="Navigate the Compute-God station catalogue.")
    subparsers = parser.add_subparsers(dest="command")

    stations_parser = subparsers.add_parser(
        "stations", help="List all stations and their entries."
    )
    stations_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    stations_parser.set_defaults(handler=_handle_stations)

    station_parser = subparsers.add_parser(
        "station", help="Inspect a single station in detail."
    )
    station_parser.add_argument("name", help="Station identifier (e.g. 'core').")
    station_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    station_parser.set_defaults(handler=_handle_station)

    resolve_parser = subparsers.add_parser(
        "resolve", help="Resolve a reference such as 'core.God'."
    )
    resolve_parser.add_argument(
        "reference", help="Guidance reference in 'station.entry' form."
    )
    resolve_parser.set_defaults(handler=_handle_resolve)

    version_parser = subparsers.add_parser(
        "version", help="Show the installed Compute-God package version."
    )
    version_parser.set_defaults(handler=_handle_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point used by the ``compute-god`` console script."""

    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


__all__ = ["build_parser", "main"]

