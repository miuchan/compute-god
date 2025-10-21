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
from pathlib import Path
import sys
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING

from . import guidance_desk as _guidance_desk
from . import __version__ as _package_version

try:  # pragma: no cover - optional NumPy dependency
    from .domains.feynman_wormhole_lab import DiagramLeg, Propagator, run_feynman_wormhole_lab
except ImportError:  # pragma: no cover - align with lazy import semantics
    DiagramLeg = Propagator = run_feynman_wormhole_lab = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from .domains.feynman_wormhole_lab import BridgeSummary


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


def _matches_query(value: str, query: str, *, case_sensitive: bool) -> bool:
    if not value:
        return False
    return (query in value) if case_sensitive else (query.casefold() in value.casefold())


def _search_catalogue(
    query: str,
    *,
    case_sensitive: bool,
) -> list[tuple[str, str, str]]:
    desk = _guidance_desk()
    if not query:
        raise ValueError("search query must not be empty")

    matches: list[tuple[str, str, str]] = []
    for station_name, station in desk.items():
        station_match = _matches_query(station_name, query, case_sensitive=case_sensitive) or _matches_query(
            station.description, query, case_sensitive=case_sensitive
        )
        for entry in station.catalog():
            if station_match or _matches_query(entry, query, case_sensitive=case_sensitive):
                matches.append((station_name, entry, station.description))
    return matches


def _format_search_text(query: str, matches: Iterable[tuple[str, str, str]]) -> str:
    lines = [f"Search results for {query!r}:"]
    appended = False
    for station, entry, _ in matches:
        lines.append(f"  - {station}.{entry}")
        appended = True
    if not appended:
        lines.append("  (no matches found)")
    return "\n".join(lines)


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


def _handle_search(args: argparse.Namespace) -> int:
    try:
        matches = _search_catalogue(args.query, case_sensitive=args.case_sensitive)
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    if args.format == "json":
        payload = {
            "query": args.query,
            "case_sensitive": args.case_sensitive,
            "matches": [
                {
                    "station": station,
                    "entry": entry,
                    "reference": f"{station}.{entry}",
                    "station_description": description,
                }
                for station, entry, description in matches
            ],
        }
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(_format_search_text(args.query, matches) + "\n")
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


def _wormhole_payload(summary: "BridgeSummary") -> dict[str, object]:
    return {
        "left_labels": list(summary.left_labels),
        "right_labels": list(summary.right_labels),
        "temperature": summary.temperature,
        "bridge_strength": summary.bridge_strength,
        "entanglement_bits": summary.entanglement_bits,
        "schmidt_coefficients": list(summary.schmidt_coefficients),
        "propagator_matrix": summary.propagator_matrix.tolist(),
        "state_vector": summary.state_vector.tolist(),
    }


def _format_wormhole_text(summary: "BridgeSummary") -> str:
    import numpy as np  # local import to avoid mandatory dependency at module import time

    matrix_str = np.array2string(summary.propagator_matrix, precision=6)
    state_str = np.array2string(summary.state_vector, precision=6)
    lines = [
        "Feynman wormhole bridge summary",
        f"  Left boundary legs: {', '.join(summary.left_labels)}",
        f"  Right boundary legs: {', '.join(summary.right_labels)}",
        f"  Temperature: {summary.temperature:.6g}",
        f"  Bridge strength: {summary.bridge_strength:.6g}",
        f"  Entanglement entropy (bits): {summary.entanglement_bits:.6g}",
        f"  Schmidt coefficients: {', '.join(f'{value:.6g}' for value in summary.schmidt_coefficients)}",
        "  Propagator matrix:",
        "    " + matrix_str.replace("\n", "\n    "),
        "  State vector:",
        "    " + state_str.replace("\n", "\n    "),
    ]
    return "\n".join(lines)


def _load_wormhole_configuration(path: Path) -> tuple[list["DiagramLeg"], list["Propagator"], float]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"configuration file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to decode JSON: {exc}") from None

    try:
        legs_data = payload["legs"]
        propagators_data = payload["propagators"]
    except KeyError as exc:
        raise ValueError(f"missing field in configuration: {exc.args[0]}") from None

    if not isinstance(legs_data, list) or not isinstance(propagators_data, list):
        raise ValueError("'legs' and 'propagators' must be lists")

    if DiagramLeg is None or Propagator is None:
        raise ImportError("compute_god.feynman_wormhole_lab requires numpy")

    legs = []
    for entry in legs_data:
        if not isinstance(entry, dict):
            raise ValueError("each leg must be an object with 'label' and 'boundary'")
        try:
            legs.append(DiagramLeg(label=entry["label"], boundary=entry["boundary"]))
        except KeyError as exc:
            raise ValueError(f"leg definition missing field: {exc.args[0]}") from None

    propagators = []
    for entry in propagators_data:
        if not isinstance(entry, dict):
            raise ValueError("each propagator must be an object with 'source' and 'target'")
        try:
            propagators.append(
                Propagator(
                    source=entry["source"],
                    target=entry["target"],
                    amplitude=float(entry.get("amplitude", 1.0)),
                    proper_time=float(entry.get("proper_time", 1.0)),
                )
            )
        except KeyError as exc:
            raise ValueError(f"propagator definition missing field: {exc.args[0]}") from None

    temperature_raw = payload.get("temperature", 1.0)
    try:
        temperature = float(temperature_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("temperature must be a number") from exc

    return legs, propagators, temperature


def _handle_wormhole_lab(args: argparse.Namespace) -> int:
    if run_feynman_wormhole_lab is None:
        sys.stderr.write("compute_god.feynman_wormhole_lab requires numpy\n")
        return 1

    try:
        legs, propagators, temperature = _load_wormhole_configuration(Path(args.config))
    except (ValueError, ImportError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    summary = run_feynman_wormhole_lab(legs, propagators, temperature=temperature)

    if args.format == "json":
        json.dump(_wormhole_payload(summary), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(_format_wormhole_text(summary) + "\n")
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

    search_parser = subparsers.add_parser(
        "search", help="Search entries across all stations."
    )
    search_parser.add_argument("query", help="Substring to match against station and entry names.")
    search_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    search_parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Perform a case-sensitive search.",
    )
    search_parser.set_defaults(handler=_handle_search)

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

    wormhole_parser = subparsers.add_parser(
        "wormhole-lab", help="Analyse a Feynman diagram as a wormhole bridge."
    )
    wormhole_parser.add_argument("config", help="Path to a JSON configuration file.")
    wormhole_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the bridge summary.",
    )
    wormhole_parser.set_defaults(handler=_handle_wormhole_lab)

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

