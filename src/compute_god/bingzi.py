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
from typing import Callable, Iterable, List, MutableMapping, Optional, Tuple

from .observer import ObserverEvent

State = MutableMapping[str, object]
TemperatureMetric = Callable[[State], float]
Observation = Tuple[ObserverEvent, State]


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


@dataclass
class PingziRelation:
    """Bridge capturing the relationship between :class:`Bingzi` and :class:`Pingzi`.

    ``PingziRelation`` – nicknamed ``平子`` – keeps references to the cold and hot
    observers so that callers can reason about their combined behaviour.  It can
    report the observed temperature span, compute the mid-point ("equilibrium")
    between the two extremes and offer a convenience check to see whether the
    system has settled within an acceptable tolerance around that mid-point.
    """

    bingzi: Bingzi
    pingzi: Pingzi

    def has_extremes(self) -> bool:
        """Return ``True`` when both observers have recorded at least one value."""

        return self.bingzi.coldest_value is not None and self.pingzi.hottest_value is not None

    def temperature_span(self) -> Optional[float]:
        """Return the temperature gap spanned by ``Bingzi`` and ``Pingzi``."""

        if not self.has_extremes():
            return None
        return peculiar_asymmetry(self.bingzi, self.pingzi)

    def equilibrium(self) -> Optional[float]:
        """Return the mid-point temperature between the recorded extremes."""

        if not self.has_extremes():
            return None
        assert self.bingzi.coldest_value is not None  # for the type-checker
        assert self.pingzi.hottest_value is not None
        return float((self.bingzi.coldest_value + self.pingzi.hottest_value) / 2.0)

    def is_balanced(self, *, tolerance: float = 0.0) -> bool:
        """Check whether the equilibrium lies within ``tolerance`` of zero."""

        midpoint = self.equilibrium()
        if midpoint is None:
            return False
        return abs(midpoint) <= tolerance


def qianli_bingfeng(
    observations: Iterable[Observation],
    *,
    metric: TemperatureMetric,
    freeze_point: float = 0.0,
) -> Optional[State]:
    """Return the coldest state once the observer freezes across the expanse.

    The helper acts as a tiny convenience façade around :class:`Bingzi` for the
    poetic ``千里冰封`` imagery.  Callers provide an iterable of observations –
    event/state pairs – together with a temperature metric.  The sequence is fed
    through a fresh ``Bingzi`` instance and the coldest recorded state is
    returned once the observer reaches or crosses ``freeze_point``.  If the
    threshold is never met ``None`` is produced instead.

    Parameters
    ----------
    observations:
        Iterable of :class:`ObserverEvent` / state pairs to evaluate.
    metric:
        Callable measuring the "temperature" of each state.
    freeze_point:
        Threshold deciding when the observer is considered frozen.  Defaults to
        ``0.0`` mirroring :class:`Bingzi`'s constructor.
    """

    observer = Bingzi(metric=metric, freeze_point=freeze_point)
    for event, state in observations:
        observer(event, state)

    if not observer.is_frozen:
        return None
    return observer.coldest_state()


# Chinese aliases so users can embrace the playful API surface.
冰子 = Bingzi
瓶子 = Pingzi
平子 = PingziRelation
千里冰封 = qianli_bingfeng


__all__ = [
    "Bingzi",
    "Pingzi",
    "PingziRelation",
    "peculiar_asymmetry",
    "冰子",
    "瓶子",
    "平子",
    "qianli_bingfeng",
    "千里冰封",
]

