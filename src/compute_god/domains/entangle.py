"""Utilities for creating and tracking entangled state pairs.

The playful naming follows the existing tone of the project: ``纠子`` (``Jiuzi``)
focuses on *correcting* a single state towards a desired target, ``缠子``
(``Chanzi``) keeps track of how tightly two states are woven together, while
``纠缠子`` (``Entangler``) combines both to evaluate and record the joint
relationship of a pair of states.

These helpers mirror the ergonomics of :class:`compute_god.miyu.MiyuBond` but
are specialised for scenarios where two universes (or two projections of the
same universe) need to be analysed together.  They are intentionally kept free
from the observer protocol so that they can be used in offline analyses or as
building blocks inside custom observers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, MutableMapping, Optional, Tuple

State = MutableMapping[str, object]
Metric = Callable[[State, State], float]


@dataclass
class Jiuzi:
    """Track how close a state stays to a desired target.

    Parameters
    ----------
    target_state:
        The reference state we would like to converge towards.  A defensive
        copy is stored so that later mutations from the caller do not affect the
        comparisons performed by the instance.
    metric:
        Callable returning a distance-like value between two states.  Smaller
        values indicate that the observed state is closer to the desired target.

    Notes
    -----
    Each call to :meth:`observe` registers the inspected state together with the
    computed delta.  The smallest delta seen so far is kept alongside a copy of
    the corresponding state so it can be retrieved even if the original mapping
    gets mutated by user code.
    """

    target_state: State
    metric: Metric
    history: List[Tuple[State, float]] = field(default_factory=list, init=False)
    best_state: Optional[State] = field(default=None, init=False)
    best_delta: Optional[float] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.target_state = dict(self.target_state)

    def observe(self, state: State, /) -> float:
        """Record the provided state and return the distance to the target."""

        snapshot = dict(state)
        delta = self.metric(snapshot, self.target_state)
        self.history.append((snapshot, delta))

        if self.best_delta is None or delta < self.best_delta:
            self.best_delta = delta
            self.best_state = snapshot

        return delta

    def strongest_state(self) -> Optional[State]:
        """Return the closest state encountered so far, if any."""

        if self.best_state is None:
            return None
        return dict(self.best_state)

    def is_strong(self, threshold: float) -> bool:
        """Check whether the best delta observed is within ``threshold``."""

        return self.best_delta is not None and self.best_delta <= threshold


@dataclass
class Chanzi:
    """Measure and store how tightly two states are interwoven."""

    metric: Metric
    history: List[Tuple[State, State, float]] = field(default_factory=list, init=False)
    best_pair: Optional[Tuple[State, State]] = field(default=None, init=False)
    best_delta: Optional[float] = field(default=None, init=False)

    def weave(self, left: State, right: State, /) -> float:
        """Record a pair of states and return their entanglement delta."""

        left_snapshot = dict(left)
        right_snapshot = dict(right)
        delta = self.metric(left_snapshot, right_snapshot)
        self.history.append((left_snapshot, right_snapshot, delta))

        if self.best_delta is None or delta < self.best_delta:
            self.best_delta = delta
            self.best_pair = (left_snapshot, right_snapshot)

        return delta

    def strongest_pair(self) -> Optional[Tuple[State, State]]:
        """Return a defensive copy of the tightest pair seen so far."""

        if self.best_pair is None:
            return None
        left, right = self.best_pair
        return dict(left), dict(right)

    def is_strong(self, threshold: float) -> bool:
        """Check whether the best entanglement delta is within ``threshold``."""

        return self.best_delta is not None and self.best_delta <= threshold


@dataclass
class EntanglementSnapshot:
    """Information captured by a :class:`纠缠子` during a single observation."""

    left_state: State
    right_state: State
    left_delta: float
    right_delta: float
    pair_delta: float


@dataclass
class Entangler:
    """Combine two :class:`Jiuzi` instances with a :class:`Chanzi` tracker."""

    left: Jiuzi
    right: Jiuzi
    pair: Chanzi
    history: List[EntanglementSnapshot] = field(default_factory=list, init=False)

    def entangle(self, left_state: State, right_state: State, /) -> EntanglementSnapshot:
        """Observe both states and keep a record of their entanglement."""

        left_delta = self.left.observe(left_state)
        right_delta = self.right.observe(right_state)
        pair_delta = self.pair.weave(left_state, right_state)

        snapshot = EntanglementSnapshot(
            left_state=dict(left_state),
            right_state=dict(right_state),
            left_delta=left_delta,
            right_delta=right_delta,
            pair_delta=pair_delta,
        )
        self.history.append(snapshot)
        return snapshot

    def strongest_pair(self) -> Optional[Tuple[State, State]]:
        """Return the tightest pair of states encountered."""

        return self.pair.strongest_pair()

    def is_strong(self, threshold: float) -> bool:
        """Check whether all tracked components are within ``threshold``."""

        return (
            self.left.is_strong(threshold)
            and self.right.is_strong(threshold)
            and self.pair.is_strong(threshold)
        )


# Chinese aliases so callers can embrace the playful API if desired.
纠子 = Jiuzi
缠子 = Chanzi
纠缠子 = Entangler


__all__ = [
    "Jiuzi",
    "Chanzi",
    "Entangler",
    "EntanglementSnapshot",
    "纠子",
    "缠子",
    "纠缠子",
]

