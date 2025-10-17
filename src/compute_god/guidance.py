"""Runtime navigation helpers for the Compute-God package.

This module introduces a lightweight "导诊台" (guidance desk) that groups the
vast catalogue of Compute-God components into thematic stations.  Each station
acts as a curated entry point – similar to the reception desk of a hospital –
and provides a structured, discoverable index of related concepts.  The goal is
to make the sprawling collection of universes, dualities, and playful
constructs easier to explore programmatically while keeping backwards
compatibility with the existing flat exports.

Two small abstractions are provided:

``DeskStation``
    A mutable mapping that stores the objects belonging to a particular
    category.  Stations remember a short human-readable description so the
    catalogue can be surfaced in documentation or CLI tooling.

``GuidanceDesk``
    A mapping of station name to :class:`DeskStation`.  Besides the mapping
    protocol it exposes helpers to register new stations, extend existing ones
    and resolve references of the form ``"station.entry"`` or
    ``"station:entry"``.

The abstractions are intentionally lightweight – they avoid any heavy runtime
dependencies and simply wrap ordered dictionaries so the exported catalogue is
stable and deterministic.  This keeps them suitable for library code and unit
tests alike.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from typing import Iterator, Tuple
from types import MappingProxyType


@dataclass
class DeskStation(MutableMapping[str, object]):
    """Container grouping a curated set of Compute-God exports.

    Parameters
    ----------
    name:
        Identifier used to reference the station.  It must be unique within a
        :class:`GuidanceDesk` catalogue.
    description:
        Optional human-readable summary describing the intention of the
        station.  The string is stored verbatim and can therefore include
        Markdown or other formatting as needed by higher-level tooling.
    entries:
        Mapping of symbolic names to the underlying runtime objects.
    """

    name: str
    description: str = ""
    entries: Mapping[str, object] | None = None

    def __post_init__(self) -> None:  # pragma: no cover - trivial defensive copy
        if not self.name:
            raise ValueError("station name must not be empty")
        # ``OrderedDict`` ensures deterministic iteration order which becomes
        # important when rendering documentation or serialising the catalogue.
        self._entries = OrderedDict(self.entries or {})

    # ``MutableMapping`` API -------------------------------------------------
    def __getitem__(self, key: str) -> object:
        return self._entries[key]

    def __setitem__(self, key: str, value: object) -> None:
        if not key:
            raise ValueError("entry name must not be empty")
        self._entries[key] = value

    def __delitem__(self, key: str) -> None:
        del self._entries[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    # Convenience helpers ----------------------------------------------------
    def add(self, name: str, obj: object) -> None:
        """Register ``obj`` under ``name`` within the station."""

        self[name] = obj

    def extend(self, entries: Mapping[str, object]) -> None:
        """Bulk-register ``entries`` preserving the deterministic order."""

        for name, obj in entries.items():
            self[name] = obj

    def snapshot(self) -> Mapping[str, object]:
        """Return an immutable view of the registered entries."""

        return MappingProxyType(dict(self._entries))

    def catalog(self) -> Tuple[str, ...]:
        """Return the ordered tuple of exported names."""

        return tuple(self._entries.keys())

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"DeskStation(name={self.name!r}, entries={list(self._entries)!r})"


class GuidanceDesk(Mapping[str, DeskStation]):
    """Registry of :class:`DeskStation` instances.

    The desk behaves like a mapping from station name to station instance.  It
    additionally offers a ``resolve`` helper to access entries via
    ``"station.entry"`` or ``"station:entry"`` references, as well as builders
    to mutate the catalogue.  Station order is preserved according to the order
    in which they were registered.
    """

    def __init__(self, stations: Iterable[DeskStation] | None = None) -> None:
        self._stations: OrderedDict[str, DeskStation] = OrderedDict()
        if stations:
            for station in stations:
                self.add_station(station)

    # ``Mapping`` API --------------------------------------------------------
    def __getitem__(self, key: str) -> DeskStation:
        return self._stations[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._stations)

    def __len__(self) -> int:
        return len(self._stations)

    # Station management -----------------------------------------------------
    def add_station(self, station: DeskStation) -> None:
        """Insert or replace ``station`` by its name."""

        self._stations[station.name] = station

    def register(self, station: str, name: str, obj: object, *, description: str | None = None) -> None:
        """Register an entry, creating the station if necessary."""

        bucket = self._stations.get(station)
        if bucket is None:
            bucket = DeskStation(station, description or "")
            self._stations[station] = bucket
        elif description and not bucket.description:
            bucket.description = description
        bucket[name] = obj

    def extend_station(
        self,
        station: str,
        entries: Mapping[str, object],
        *,
        description: str | None = None,
    ) -> None:
        """Register multiple entries inside ``station``."""

        bucket = self._stations.get(station)
        if bucket is None:
            bucket = DeskStation(station, description or "", entries)
            self._stations[station] = bucket
            return
        if description and not bucket.description:
            bucket.description = description
        bucket.extend(entries)

    # Lookup helpers ---------------------------------------------------------
    def resolve(self, reference: str) -> object:
        """Resolve ``reference`` of the form ``"station.entry"`` or ``"station:entry"``."""

        station_name, entry_name = self._split_reference(reference)
        try:
            return self._stations[station_name][entry_name]
        except KeyError as exc:  # pragma: no cover - defensive clarity
            raise KeyError(f"unknown guidance reference: {reference!r}") from exc

    def get_entry(self, station: str, name: str, default: object | None = None) -> object | None:
        """Return ``station[name]`` if present, otherwise ``default``."""

        station_obj = self._stations.get(station)
        if station_obj is None:
            return default
        return station_obj.get(name, default)

    def has_entry(self, reference: str) -> bool:
        """Return ``True`` if ``reference`` can be resolved."""

        try:
            self.resolve(reference)
        except KeyError:
            return False
        return True

    def summary(self) -> Mapping[str, Mapping[str, object]]:
        """Return an immutable snapshot of the entire catalogue."""

        return MappingProxyType(
            {
                name: station.snapshot()
                for name, station in self._stations.items()
            }
        )

    def catalog(self) -> Mapping[str, Tuple[str, ...]]:
        """Return station-to-entry name mapping suitable for UIs or docs."""

        return MappingProxyType(
            {name: station.catalog() for name, station in self._stations.items()}
        )

    # Internal utilities -----------------------------------------------------
    @staticmethod
    def _split_reference(reference: str) -> Tuple[str, str]:
        for separator in (".", ":", "/"):
            if separator in reference:
                return tuple(reference.split(separator, 1))  # type: ignore[return-value]
        raise KeyError(f"invalid guidance reference: {reference!r}")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"GuidanceDesk(stations={list(self._stations)!r})"


__all__ = [
    "DeskStation",
    "GuidanceDesk",
]

