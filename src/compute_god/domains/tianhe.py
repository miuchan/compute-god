"""Celestial harmony lines that bridge two conceptual states.

The library tends to give poetic names to otherwise pragmatic helpers.  The
``TianheLine`` follows that tradition by modelling a one-dimensional affine
space between two states—``earth`` (the starting point) and ``heaven`` (the
desired alignment).  Callers can blend points along the line, project
arbitrary states back onto it and measure how far a given configuration is
from the harmonious corridor.

The implementation intentionally stays lightweight: states are treated as
labelled vectors of floats and the geometry only relies on elementary dot
products.  This keeps the helper dependency free while still providing a
useful abstraction that integrates nicely with the rest of the package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, MutableMapping, Tuple


State = MutableMapping[str, float]


def _coerce_state(
    state: Mapping[str, object] | Iterable[Tuple[str, object]]
) -> dict[str, float]:
    """Normalise a mapping-like structure into ``str -> float`` coordinates."""

    if hasattr(state, "items"):
        items = state.items()  # type: ignore[assignment]
    else:
        items = state

    coerced: dict[str, float] = {}
    for key, value in items:
        coerced[str(key)] = float(value)
    return coerced


def _dot_product(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    """Return the dot product between two sparse vectors."""

    total = 0.0
    for key, left_value in left.items():
        total += left_value * right.get(key, 0.0)
    return total


@dataclass
class TianheLine:
    """Represent a harmony line between an ``earth`` and a ``heaven`` state."""

    heaven: Mapping[str, object] | Iterable[Tuple[str, object]]
    earth: Mapping[str, object] | Iterable[Tuple[str, object]]
    clamp: bool = True
    _keys: Tuple[str, ...] = field(init=False, repr=False)
    _direction: dict[str, float] = field(init=False, repr=False)
    _earth: dict[str, float] = field(init=False, repr=False)
    _heaven: dict[str, float] = field(init=False, repr=False)
    _direction_norm: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        heaven = _coerce_state(self.heaven)
        earth = _coerce_state(self.earth)

        keys = set(heaven) | set(earth)
        if not keys:
            raise ValueError("tianhe line requires at least one coordinate")

        direction = {key: heaven.get(key, 0.0) - earth.get(key, 0.0) for key in keys}
        norm = _dot_product(direction, direction)
        if norm == 0.0:
            raise ValueError("heaven and earth states must not coincide")

        self._heaven = heaven
        self._earth = earth
        self._keys = tuple(sorted(keys))
        self._direction = direction
        self._direction_norm = norm

    def _project_ratio(self, state: Mapping[str, object], *, clamp: bool | None) -> float:
        if clamp is None:
            clamp = self.clamp

        vector = _coerce_state(state)

        translated = {
            key: vector.get(key, 0.0) - self._earth.get(key, 0.0) for key in self._keys
        }
        numerator = _dot_product(translated, self._direction)
        ratio = numerator / self._direction_norm

        if clamp:
            if ratio < 0.0:
                return 0.0
            if ratio > 1.0:
                return 1.0
        return ratio

    def blend(self, ratio: float, *, clamp: bool | None = None) -> State:
        """Return the state located ``ratio`` along the harmony line."""

        if clamp is None:
            clamp = self.clamp

        if clamp:
            if ratio < 0.0:
                ratio = 0.0
            elif ratio > 1.0:
                ratio = 1.0

        blended: dict[str, float] = {}
        for key in self._keys:
            start = self._earth.get(key, 0.0)
            blended[key] = start + self._direction[key] * ratio
        return blended

    def project_ratio(
        self, state: Mapping[str, object], *, clamp: bool | None = True
    ) -> float:
        """Return the harmonic coordinate of ``state`` along the line."""

        return self._project_ratio(state, clamp=clamp)

    def project(
        self, state: Mapping[str, object], *, clamp: bool | None = True
    ) -> State:
        """Project ``state`` onto the harmony line and return the closest point."""

        ratio = self._project_ratio(state, clamp=clamp)
        return self.blend(ratio, clamp=clamp)

    def deviation(
        self, state: Mapping[str, object], *, clamp: bool | None = True
    ) -> float:
        """Return the L1 deviation between ``state`` and its harmony projection."""

        vector = _coerce_state(state)
        projection = self.project(state, clamp=clamp)

        total = 0.0
        for key in self._keys:
            total += abs(projection[key] - vector.get(key, 0.0))
        return total


# Chinese alias mirroring the project's playful API surface.
天和线 = TianheLine


__all__ = ["TianheLine", "天和线"]

