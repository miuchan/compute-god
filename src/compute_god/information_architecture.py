"""Recursive gradient descent tools for restructuring the guidance catalogue.

This module encapsulates a small optimisation routine that recursively applies
gradient descent to a sequence of feature vectors.  The routine is used to
re-order both stations and entries inside :mod:`compute_god.catalogue`, giving
the information architecture a deterministic layout derived from lightweight
string statistics rather than hand-curated ordering.  While intentionally
simple, the optimiser mirrors the gradient-based style used throughout the
project so documentation and tooling can reason about the catalogue in the same
language as other optimisation utilities.

Three helper functions are exposed:

``encode_entry``
    Convert a symbol name into a feature vector capturing coarse lexical
    properties.  The features remain inexpensive to compute while still
    providing enough variation for the optimiser to latch onto.

``encode_station``
    Aggregate entry features alongside station metadata to construct a vector
    describing the station as a whole.  The function combines means and
    standard deviations of entry features so the layout is sensitive to both
    the size of the station and the diversity of its contents.

``recursive_gradient_descent_order``
    Apply a recursive gradient descent loop to a sequence of feature vectors.
    The loop expresses each optimisation step as a recursive call, matching the
    "recursive gradient descent" phrasing often used in the Compute-God
    narratives.  The returned list contains the indices that sort the original
    sequence by the optimised coordinates.

``restructure_information_architecture`` ties everything together: given a raw
station blueprint, it recursively optimises entry orderings and then the
station ordering itself, yielding a fully restructured architecture ready for
consumption by :class:`compute_god.guidance.GuidanceDesk`.
"""

from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Iterable, Sequence

StationLayout = tuple[str, str, tuple[str, ...]]

Vector = tuple[float, ...]


def encode_entry(name: str) -> Vector:
    """Return a lightweight feature embedding for ``name``.

    The encoding intentionally keeps only inexpensive lexical statistics.  They
    nevertheless provide enough variety for the optimiser to differentiate
    between entries when reconstructing the catalogue layout.
    """

    ascii_sum = sum(ord(char) for char in name)
    length = float(len(name))
    underscores = float(name.count("_"))
    digits = float(sum(char.isdigit() for char in name))
    vowels = float(sum(char.lower() in "aeiou" for char in name))
    uppercase = float(sum(char.isupper() for char in name))
    punctuation = float(sum(not char.isalnum() and char != "_" for char in name))
    return (
        length,
        float(ascii_sum),
        underscores,
        digits,
        vowels,
        uppercase,
        punctuation,
    )


def encode_station(name: str, entries: Sequence[str]) -> Vector:
    """Aggregate ``entries`` into a station-level feature vector."""

    entry_vectors = [encode_entry(entry) for entry in entries]
    if entry_vectors:
        # Mean and population standard deviation per feature dimension.
        means = tuple(mean(dimension) for dimension in zip(*entry_vectors))
        spreads = tuple(pstdev(dimension) for dimension in zip(*entry_vectors))
    else:
        means = (0.0,) * len(encode_entry(""))
        spreads = (0.0,) * len(encode_entry(""))

    ascii_sum = float(sum(ord(char) for char in name))
    length = float(len(name))
    underscores = float(name.count("_"))

    return (
        float(len(entries)),
        length,
        ascii_sum,
        underscores,
        *means,
        *spreads,
    )


def _vector_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def _objective_and_gradient(
    positions: Sequence[float],
    anchors: Sequence[float],
) -> tuple[float, list[float]]:
    energy = 0.0
    gradient = [0.0 for _ in positions]
    # Anchor each position close to its original norm.
    for idx, (position, anchor) in enumerate(zip(positions, anchors)):
        diff = position - anchor
        energy += diff * diff
        gradient[idx] += 2.0 * diff
    # Encourage neighbouring positions to preserve relative distances.
    for idx in range(len(positions) - 1):
        neighbour = idx + 1
        diff = (positions[neighbour] - positions[idx]) - (
            anchors[neighbour] - anchors[idx]
        )
        energy += diff * diff
        gradient[idx] -= 2.0 * diff
        gradient[neighbour] += 2.0 * diff
    return energy, gradient


def _recursive_descent(
    positions: list[float],
    anchors: Sequence[float],
    *,
    learning_rate: float,
    tolerance: float,
    depth: int,
    max_depth: int,
) -> list[float]:
    _, gradient = _objective_and_gradient(positions, anchors)
    grad_norm = math.sqrt(sum(component * component for component in gradient))
    if grad_norm <= tolerance or depth >= max_depth:
        return positions

    updated = [
        value - learning_rate * component
        for value, component in zip(positions, gradient)
    ]
    return _recursive_descent(
        updated,
        anchors,
        learning_rate=learning_rate,
        tolerance=tolerance,
        depth=depth + 1,
        max_depth=max_depth,
    )


def recursive_gradient_descent_order(
    vectors: Sequence[Sequence[float]],
    *,
    learning_rate: float = 0.125,
    tolerance: float = 1e-6,
    max_depth: int = 2048,
) -> list[int]:
    """Return the permutation indices produced by recursive gradient descent."""

    if not vectors:
        return []

    anchors = [_vector_norm(vector) for vector in vectors]
    optimised = _recursive_descent(
        list(anchors),
        anchors,
        learning_rate=learning_rate,
        tolerance=tolerance,
        depth=0,
        max_depth=max_depth,
    )
    return sorted(range(len(vectors)), key=lambda idx: (optimised[idx], idx))


def restructure_information_architecture(
    blueprint: Iterable[StationLayout],
    *,
    entry_learning_rate: float = 0.1,
    station_learning_rate: float = 0.05,
) -> tuple[StationLayout, ...]:
    """Return a recursively optimised catalogue layout."""

    stations: list[tuple[str, str, tuple[str, ...]]] = []
    station_vectors: list[Vector] = []
    for name, description, entries in blueprint:
        entry_vectors = [encode_entry(entry) for entry in entries]
        order = recursive_gradient_descent_order(
            entry_vectors,
            learning_rate=entry_learning_rate,
        )
        sorted_entries = tuple(entries[idx] for idx in order)
        stations.append((name, description, sorted_entries))
        station_vectors.append(encode_station(name, sorted_entries))

    station_order = recursive_gradient_descent_order(
        station_vectors,
        learning_rate=station_learning_rate,
    )
    return tuple(stations[idx] for idx in station_order)


__all__ = [
    "Vector",
    "encode_entry",
    "encode_station",
    "recursive_gradient_descent_order",
    "restructure_information_architecture",
]

