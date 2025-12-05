"""Spatial projections of the guidance catalogue.

`topos` (the Greek for "place") models the catalogue as a radial map so
researchers can see how stations relate to one another at a glance.  The
projection is deterministic and derived solely from the catalogue blueprint, so
CLI consumers and documentation generators can rely on stable coordinates even
as the catalogue grows.

Three helper classes capture the projection:

``ToposNode``
    A station or entry anchored at a 2D coordinate with a short payload.

``ToposEdge``
    A parent/child relationship connecting a station node to an entry node.

``ToposMap``
    The full projection containing nodes, edges, and layout metadata.  It offers
    a `to_payload` helper used by the CLI and downstream tools.

The :func:`build_topos_map` helper assembles a :class:`ToposMap` from the
catalogue blueprint.  By default it pulls the canonical desk via
:func:`compute_god.catalogue.build_guidance_desk`, but callers can also supply an
explicit blueprint for custom visualisations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping

from .catalogue import StationLayout
from .information_architecture import restructure_information_architecture


@dataclass(frozen=True, slots=True)
class ToposNode:
    """A node in the radial topos projection."""

    identifier: str
    label: str
    kind: str
    coordinate: tuple[float, float]
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ToposEdge:
    """A directed edge connecting a station to an entry."""

    parent: str
    child: str


@dataclass(frozen=True, slots=True)
class ToposMap:
    """A deterministic radial projection of catalogue stations and entries."""

    nodes: tuple[ToposNode, ...]
    edges: tuple[ToposEdge, ...]
    metadata: Mapping[str, object]

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-serialisable payload representing the topos map."""

        return {
            "nodes": [
                {
                    "id": node.identifier,
                    "label": node.label,
                    "kind": node.kind,
                    "coordinate": node.coordinate,
                    "metadata": dict(node.metadata),
                }
                for node in self.nodes
            ],
            "edges": [
                {"parent": edge.parent, "child": edge.child} for edge in self.edges
            ],
            "metadata": dict(self.metadata),
        }


def _polar(angle: float, radius: float) -> tuple[float, float]:
    return (math.cos(angle) * radius, math.sin(angle) * radius)


def _station_angle(index: int, count: int) -> float:
    if count <= 0:
        return 0.0
    return (2.0 * math.pi * index) / float(count)


def _entry_offset(index: int, total: int, spread: float) -> float:
    if total <= 1:
        return 0.0
    origin = (total - 1) / 2.0
    return (index - origin) * spread


def build_topos_map(
    blueprint: Iterable[StationLayout] | None = None,
    *,
    station_ring: float = 1.0,
    entry_ring_spacing: float = 0.28,
    entry_angle_spread: float = 0.08,
) -> ToposMap:
    """Return a :class:`ToposMap` describing the catalogue layout."""

    if blueprint is None:
        from . import guidance_desk as _guidance_desk

        desk = _guidance_desk()
        blueprint = (
            (name, station.description, tuple(station.entries))
            for name, station in desk.items()
        )

    restructured = restructure_information_architecture(blueprint)
    station_count = len(restructured)

    nodes: list[ToposNode] = []
    edges: list[ToposEdge] = []

    for station_index, (name, description, entries) in enumerate(restructured):
        angle = _station_angle(station_index, station_count)
        station_coordinate = _polar(angle, station_ring)
        station_id = f"station:{name}"
        nodes.append(
            ToposNode(
                identifier=station_id,
                label=name,
                kind="station",
                coordinate=station_coordinate,
                metadata={
                    "description": description,
                    "index": station_index,
                },
            )
        )

        entry_radius = station_ring + entry_ring_spacing
        for entry_index, entry in enumerate(entries):
            entry_angle = angle + _entry_offset(entry_index, len(entries), entry_angle_spread)
            entry_coordinate = _polar(entry_angle, entry_radius)
            entry_id = f"entry:{name}.{entry}"
            nodes.append(
                ToposNode(
                    identifier=entry_id,
                    label=entry,
                    kind="entry",
                    coordinate=entry_coordinate,
                    metadata={
                        "station": name,
                        "index": entry_index,
                    },
                )
            )
            edges.append(ToposEdge(parent=station_id, child=entry_id))

    return ToposMap(
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "station_ring": station_ring,
            "entry_ring_spacing": entry_ring_spacing,
            "entry_angle_spread": entry_angle_spread,
        },
    )


def format_topos_text(topos_map: ToposMap) -> str:
    """Return a human-readable representation of the topos map."""

    stations = [node for node in topos_map.nodes if node.kind == "station"]
    entries = [node for node in topos_map.nodes if node.kind == "entry"]
    lines = ["Topos projection of the guidance desk:"]
    for station in sorted(stations, key=lambda node: node.metadata.get("index", 0)):
        x, y = station.coordinate
        lines.append(
            f"- {station.label} @ ({x:.3f}, {y:.3f}) — {station.metadata.get('description', '')}"
        )
        children = [
            entry
            for entry in entries
            if entry.metadata.get("station") == station.label
        ]
        for entry in sorted(children, key=lambda node: node.metadata.get("index", 0)):
            x_entry, y_entry = entry.coordinate
            lines.append(
                f"  • {entry.label} @ ({x_entry:.3f}, {y_entry:.3f})"
            )
    return "\n".join(lines) + "\n"


__all__ = [
    "ToposNode",
    "ToposEdge",
    "ToposMap",
    "build_topos_map",
    "format_topos_text",
]
