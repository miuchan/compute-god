"""Cooling observer utilities affectionately referred to as :class:`冰子`.

The project tends to give its helpers poetic names and ``Bingzi`` continues
that tradition.  Conceptually the class acts as a tiny observer that keeps
track of how "cold" the evolving universe becomes under a user supplied
temperature metric.  The coldest state observed is frozen via a defensive
copy so that callers can safely inspect it after the fixpoint engine has
finished running.

While whimsical, the helper is intentionally straightforward: each
observation stores the emitted event together with the evaluated temperature.
When a new minimum is seen both the value and the associated state snapshot
are recorded.  Consumers can then ask whether the sequence ever cooled beyond
their ``freeze_point`` or retrieve the coldest snapshot for further analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, MutableMapping, Optional, Tuple

from .observer import ObserverEvent

State = MutableMapping[str, object]
TemperatureMetric = Callable[[State], float]


@dataclass
class Bingzi:
    """Observer that freezes the coldest state seen so far.

    Parameters
    ----------
    metric:
        Callable returning a temperature-like measure for a state.  Smaller
        values are considered colder.
    freeze_point:
        Threshold under which the observer is considered frozen.  Defaults to
        ``0.0`` which matches the intuition of going below the freezing point
        of water in Celsius, but callers are free to pick whatever sentinel is
        meaningful for their domain.
    """

    metric: TemperatureMetric
    freeze_point: float = 0.0
    history: List[Tuple[ObserverEvent, float]] = field(default_factory=list, init=False)
    coldest_value: Optional[float] = field(default=None, init=False)
    _coldest_state: Optional[State] = field(default=None, init=False, repr=False)

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Record ``state`` together with its evaluated temperature."""

        temperature = float(self.metric(state))
        self.history.append((event, temperature))

        if self.coldest_value is None or temperature < self.coldest_value:
            self.coldest_value = temperature
            self._coldest_state = dict(state)

    @property
    def is_frozen(self) -> bool:
        """Return ``True`` once a temperature at or below ``freeze_point`` is seen."""

        return self.coldest_value is not None and self.coldest_value <= self.freeze_point

    def coldest_state(self) -> Optional[State]:
        """Return a defensive copy of the coldest state encountered so far."""

        if self._coldest_state is None:
            return None
        return dict(self._coldest_state)

    def reset(self) -> None:
        """Clear recorded information so the observer can be reused."""

        self.history.clear()
        self.coldest_value = None
        self._coldest_state = None


# Chinese alias so users can embrace the playful API surface.
冰子 = Bingzi


@dataclass
class Pingzi:
    """Observer that tracks the hottest state encountered so far.

    ``Pingzi`` mirrors :class:`Bingzi` but focuses on heat instead of cold.  It
    records the *maximum* value reported by its temperature metric together with
    a snapshot of the corresponding state.  Once a value at or above the
    ``boil_point`` is seen the observer is considered overheated.

    Parameters
    ----------
    metric:
        Callable returning a temperature-like measure for a state.  Larger
        values are considered hotter.
    boil_point:
        Threshold above which the observer is considered overheated.  Defaults
        to ``100.0`` mirroring the boiling point of water in Celsius.
    """

    metric: TemperatureMetric
    boil_point: float = 100.0
    history: List[Tuple[ObserverEvent, float]] = field(default_factory=list, init=False)
    hottest_value: Optional[float] = field(default=None, init=False)
    _hottest_state: Optional[State] = field(default=None, init=False, repr=False)

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Record ``state`` together with its evaluated temperature."""

        temperature = float(self.metric(state))
        self.history.append((event, temperature))

        if self.hottest_value is None or temperature > self.hottest_value:
            self.hottest_value = temperature
            self._hottest_state = dict(state)

    @property
    def is_overheated(self) -> bool:
        """Return ``True`` once a temperature at or above ``boil_point`` is seen."""

        return self.hottest_value is not None and self.hottest_value >= self.boil_point

    def hottest_state(self) -> Optional[State]:
        """Return a defensive copy of the hottest state encountered so far."""

        if self._hottest_state is None:
            return None
        return dict(self._hottest_state)

    def reset(self) -> None:
        """Clear recorded information so the observer can be reused."""

        self.history.clear()
        self.hottest_value = None
        self._hottest_state = None


def peculiar_asymmetry(bingzi: Bingzi, pingzi: Pingzi) -> Optional[float]:
    """Return the temperature gap between ``Bingzi`` and ``Pingzi``.

    The helper captures the "奇异性" (peculiarity) between cold and hot
    observations.  ``None`` is returned until both observers have recorded at
    least one value.
    """

    if bingzi.coldest_value is None or pingzi.hottest_value is None:
        return None
    return float(pingzi.hottest_value - bingzi.coldest_value)


# Chinese aliases so users can embrace the playful API surface.
冰子 = Bingzi
瓶子 = Pingzi


__all__ = ["Bingzi", "Pingzi", "peculiar_asymmetry", "冰子", "瓶子"]

