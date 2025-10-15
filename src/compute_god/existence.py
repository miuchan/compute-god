"""Witness utilities for existence and stability claims.

This module introduces two light-weight helpers that mirror the playful naming
pattern used across the project.  ``存在子`` (``ExistenceWitness``) keeps track of
whether a sequence of states has produced a concrete witness for a desired
property.  ``稳定子`` (``StabilityWitness``) monitors the change between
consecutive states and records when the sequence becomes stable under a provided
metric.

Both helpers are intentionally tiny so that they can be composed inside tests or
custom observers without introducing extra dependencies.  They trade raw speed
for clarity and defensive copies, which makes them pleasant to use in pedagogy
and debugging scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, MutableMapping, Optional

State = MutableMapping[str, object]
Predicate = Callable[[State], bool]
Metric = Callable[[State, State], float]


def _clone_state(state: State) -> State:
    """Return a shallow copy of ``state`` for defensive storage."""

    return dict(state)


@dataclass
class ExistenceWitness:
    """Track whether a predicate has ever been satisfied.

    Parameters
    ----------
    predicate:
        Callable returning ``True`` when the observed state should be considered
        a witness.  The first state that satisfies the predicate is stored so it
        can be retrieved later even if the original mapping is mutated.
    """

    predicate: Predicate
    history: List[State] = field(default_factory=list, init=False)
    _witness: Optional[State] = field(default=None, init=False, repr=False)

    def observe(self, state: State, /) -> bool:
        """Record ``state`` and return whether it satisfies the predicate."""

        snapshot = _clone_state(state)
        self.history.append(snapshot)
        result = self.predicate(snapshot)
        if result and self._witness is None:
            self._witness = snapshot
        return result

    @property
    def exists(self) -> bool:
        """Return ``True`` once a witness has been recorded."""

        return self._witness is not None

    def witness_state(self) -> Optional[State]:
        """Return a defensive copy of the witness state, if any."""

        if self._witness is None:
            return None
        return _clone_state(self._witness)


@dataclass
class StabilityWitness:
    """Monitor how a sequence of states settles under a metric.

    Parameters
    ----------
    metric:
        Callable returning a non-negative delta between two states.
    epsilon:
        Threshold under which the sequence is considered stable.  Defaults to
        ``1e-6`` which matches the tolerances commonly used in the tests.
    tolerance:
        Small slack when checking for monotonic decreases.  Floating point noise
        can otherwise flag harmless oscillations as instability.
    """

    metric: Metric
    epsilon: float = 1e-6
    tolerance: float = 1e-12
    deltas: List[float] = field(default_factory=list, init=False)
    _previous_state: Optional[State] = field(default=None, init=False, repr=False)
    _monotone: bool = field(default=True, init=False, repr=False)
    _stable_index: Optional[int] = field(default=None, init=False, repr=False)

    def observe(self, state: State, /) -> float:
        """Record ``state`` and return the delta to the previous state."""

        snapshot = _clone_state(state)

        if self._previous_state is None:
            self._previous_state = snapshot
            return 0.0

        delta = self.metric(self._previous_state, snapshot)
        self._previous_state = snapshot
        self.deltas.append(delta)

        if len(self.deltas) > 1:
            previous_delta = self.deltas[-2]
            if delta > previous_delta + self.tolerance:
                self._monotone = False

        if delta <= self.epsilon and self._stable_index is None:
            self._stable_index = len(self.deltas)

        return delta

    @property
    def is_monotone(self) -> bool:
        """Return whether the recorded deltas have been monotone non-increasing."""

        return self._monotone

    @property
    def is_stable(self) -> bool:
        """Return ``True`` when a delta within ``epsilon`` has been observed."""

        return self._stable_index is not None

    @property
    def stable_epoch(self) -> Optional[int]:
        """Return the number of transitions observed when stability was achieved."""

        return self._stable_index

    def reset(self) -> None:
        """Clear the recorded history so the witness can be reused."""

        self.deltas.clear()
        self._previous_state = None
        self._monotone = True
        self._stable_index = None


# Chinese aliases matching the playful API surface.
存在子 = ExistenceWitness
稳定子 = StabilityWitness


__all__ = [
    "ExistenceWitness",
    "StabilityWitness",
    "存在子",
    "稳定子",
]

