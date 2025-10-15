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


__all__ = ["Bingzi", "冰子"]

