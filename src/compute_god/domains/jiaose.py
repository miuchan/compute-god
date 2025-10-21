"""Circular and chromatic observers lovingly nicknamed ``角子`` and ``色子``.

``Jiaozi`` (角子) focuses on angular quantities that wrap around a fixed period.
It mirrors the ergonomics of the temperature observers from :mod:`compute_god
.bingzi` by acting as a tiny observer that remembers the state whose angle is
closest to a reference direction.  The observer stores a defensive copy of the
state so that callers can safely inspect the snapshot even if the original
mapping is mutated by the surrounding code.

``Sezi`` (色子) plays a complementary role by tracking colour-like vectors.  It
expects a callable returning a sequence of channels (for example RGB, HSV or
lab values).  The observer evaluates the *vibrancy* of each vector via its
Euclidean norm and keeps the state with the strongest magnitude.  Both helpers
can be combined with :func:`chromatic_dual` to produce a compact summary of the
angular misalignment and chromatic intensity observed so far.

Even though the naming is playful, the implementation aims to be small and
predictable so that it can serve as a building block inside larger observers or
offline analyses.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, MutableMapping, Optional, Sequence, Tuple

from compute_god.core import ObserverEvent

State = MutableMapping[str, object]
AngleMetric = Callable[[State], float]
ColourMetric = Callable[[State], Sequence[float]]


def _normalise_angle(value: float, period: float) -> float:
    """Return ``value`` wrapped into ``[0, period)``."""

    wrapped = math.fmod(value, period)
    if wrapped < 0:
        wrapped += period
    return wrapped


def _circular_delta(a: float, b: float, period: float) -> float:
    """Return the absolute circular distance between ``a`` and ``b``."""

    delta = _normalise_angle(a - b, period)
    if delta > period / 2.0:
        delta = period - delta
    return abs(delta)


@dataclass
class Jiaozi:
    """Observer that keeps the state closest to a reference angle.

    Parameters
    ----------
    metric:
        Callable returning an angle-like value for a state.  The value is
        wrapped onto the range ``[0, period)``.
    reference:
        Direction against which the observer measures the circular distance.
        Defaults to ``0.0``.
    period:
        Length of the angular cycle.  Defaults to ``360.0`` so that the helper
        works naturally with degree based metrics.  Radian based workflows can
        pass :data:`math.tau` instead.
    """

    metric: AngleMetric
    reference: float = 0.0
    period: float = 360.0
    history: List[Tuple[ObserverEvent, float, float]] = field(default_factory=list, init=False)
    sharpest_delta: Optional[float] = field(default=None, init=False)
    _sharpest_state: Optional[State] = field(default=None, init=False, repr=False)
    _reference_normalised: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("period must be positive for a Jiaozi")
        self._reference_normalised = _normalise_angle(float(self.reference), self.period)

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Record ``state`` and remember the sharpest angular delta."""

        angle = float(self.metric(state))
        normalised = _normalise_angle(angle, self.period)
        delta = _circular_delta(normalised, self._reference_normalised, self.period)
        self.history.append((event, normalised, delta))

        if self.sharpest_delta is None or delta < self.sharpest_delta:
            self.sharpest_delta = delta
            self._sharpest_state = dict(state)

    def sharpest_state(self) -> Optional[State]:
        """Return a defensive copy of the sharpest state observed so far."""

        if self._sharpest_state is None:
            return None
        return dict(self._sharpest_state)

    def is_pointed(self, *, tolerance: float) -> bool:
        """Check whether the best observation lies within ``tolerance`` degrees."""

        return self.sharpest_delta is not None and self.sharpest_delta <= tolerance

    def reset(self) -> None:
        """Clear the recorded history so the observer can be reused."""

        self.history.clear()
        self.sharpest_delta = None
        self._sharpest_state = None


@dataclass
class Sezi:
    """Observer that tracks the most vibrant colour-like vector seen so far."""

    metric: ColourMetric
    history: List[Tuple[ObserverEvent, Tuple[float, ...], float]] = field(default_factory=list, init=False)
    most_vibrant_value: Optional[float] = field(default=None, init=False)
    _most_vibrant_vector: Optional[Tuple[float, ...]] = field(default=None, init=False, repr=False)
    _most_vibrant_state: Optional[State] = field(default=None, init=False, repr=False)

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Record ``state`` and keep the one with the strongest vibrancy."""

        vector = tuple(float(value) for value in self.metric(state))
        if not vector:
            raise ValueError("colour metric must return at least one channel")

        vibrancy = math.sqrt(sum(channel * channel for channel in vector))
        self.history.append((event, vector, vibrancy))

        if self.most_vibrant_value is None or vibrancy > self.most_vibrant_value:
            self.most_vibrant_value = vibrancy
            self._most_vibrant_vector = vector
            self._most_vibrant_state = dict(state)

    def most_vibrant_state(self) -> Optional[State]:
        """Return a defensive copy of the most vibrant state observed so far."""

        if self._most_vibrant_state is None:
            return None
        return dict(self._most_vibrant_state)

    def most_vibrant_vector(self) -> Optional[Tuple[float, ...]]:
        """Return the colour vector associated with the most vibrant state."""

        if self._most_vibrant_vector is None:
            return None
        return tuple(self._most_vibrant_vector)

    def is_vibrant(self, *, threshold: float) -> bool:
        """Check whether the strongest vibrancy exceeds ``threshold``."""

        return self.most_vibrant_value is not None and self.most_vibrant_value >= threshold

    def reset(self) -> None:
        """Clear the recorded history so the observer can be reused."""

        self.history.clear()
        self.most_vibrant_value = None
        self._most_vibrant_vector = None
        self._most_vibrant_state = None


@dataclass(frozen=True)
class ChromaticDual:
    """Summary describing the chromatic duality between :class:`Jiaozi` and :class:`Sezi`."""

    angle_delta: float
    vibrancy: float
    harmony: float
    complementary_angle: float


def chromatic_dual(jiaozi: Jiaozi, sezi: Sezi) -> Optional[ChromaticDual]:
    """Return a chromatic summary once both observers recorded information."""

    if jiaozi.sharpest_delta is None or sezi.most_vibrant_value is None:
        return None

    complementary_angle = _normalise_angle(
        jiaozi._reference_normalised + jiaozi.period / 2.0, jiaozi.period
    )
    harmony = sezi.most_vibrant_value - jiaozi.sharpest_delta
    return ChromaticDual(
        angle_delta=float(jiaozi.sharpest_delta),
        vibrancy=float(sezi.most_vibrant_value),
        harmony=float(harmony),
        complementary_angle=float(complementary_angle),
    )


# Chinese aliases so callers can embrace the playful API surface.
角子 = Jiaozi
色子 = Sezi
色角对偶 = chromatic_dual


__all__ = [
    "Jiaozi",
    "Sezi",
    "ChromaticDual",
    "chromatic_dual",
    "角子",
    "色子",
    "色角对偶",
]

