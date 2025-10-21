"""Existence and stability explorer affectionately named :class:`磐子`.

``Panzi`` (磐子) extends the whimsical observer ecosystem found throughout the
project.  Where :class:`compute_god.existence.ExistenceWitness` focuses on
recording whether a predicate was ever satisfied, and
:class:`compute_god.existence.StabilityWitness` keeps track of how a sequence of
states settles, ``Panzi`` weaves the two stories together.  The helper tracks
the exact moment existence was first witnessed – the "origin" – and couples it
with stability information so that callers can reason about what happened
before and after that pivotal instant.

The implementation intentionally composes the existing witnesses rather than
re-implementing their logic.  This keeps behaviour consistent across the code
base and makes the helper pleasant to test.  ``observe`` returns a lightweight
summary describing the latest step, while :func:`explore_origin` provides a tiny
utility to run a whole sequence through a fresh ``Panzi`` instance and retrieve
its origin story.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, MutableMapping, Optional

from .existence import ExistenceWitness, StabilityWitness

State = MutableMapping[str, object]
Predicate = Callable[[State], bool]
Metric = Callable[[State, State], float]


@dataclass(frozen=True)
class PanziObservation:
    """Summary describing the latest observation recorded by :class:`Panzi`."""

    exists: bool
    delta: float
    is_stable: bool
    is_monotone: bool


@dataclass(frozen=True)
class PanziOrigin:
    """Snapshot describing when existence first emerged."""

    index: int
    delta: float
    state: State
    stable_epoch: Optional[int]
    is_stable: bool
    is_monotone: bool


@dataclass
class Panzi:
    """Bridge combining existence and stability witnesses."""

    predicate: Predicate
    metric: Metric
    epsilon: float = 1e-6
    tolerance: float = 1e-12
    existence: ExistenceWitness = field(init=False)
    stability: StabilityWitness = field(init=False)
    _origin_index: Optional[int] = field(default=None, init=False, repr=False)
    _origin_delta: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.existence = ExistenceWitness(self.predicate)
        self.stability = StabilityWitness(
            self.metric, epsilon=self.epsilon, tolerance=self.tolerance
        )

    def observe(self, state: State, /) -> PanziObservation:
        """Record ``state`` and return a summary of the observation."""

        delta = float(self.stability.observe(state))
        exists = bool(self.existence.observe(state))

        if exists and self._origin_index is None:
            self._origin_index = len(self.existence.history) - 1
            self._origin_delta = delta

        return PanziObservation(
            exists=exists,
            delta=delta,
            is_stable=self.stability.is_stable,
            is_monotone=self.stability.is_monotone,
        )

    @property
    def origin_index(self) -> Optional[int]:
        """Return the index of the state where existence first appeared."""

        return self._origin_index

    def origin_state(self) -> Optional[State]:
        """Return a defensive copy of the origin state, if any."""

        if not self.existence.exists:
            return None
        return self.existence.witness_state()

    def origin_delta(self) -> Optional[float]:
        """Return the delta between the origin state and its predecessor."""

        if self._origin_index is None:
            return None
        assert self._origin_delta is not None  # defensive, kept for the type-checker
        return float(self._origin_delta)

    def origin_story(self) -> Optional[PanziOrigin]:
        """Return a detailed summary of the origin if it exists."""

        if self._origin_index is None:
            return None

        state = self.origin_state()
        if state is None:
            return None

        delta = self.origin_delta()
        assert delta is not None  # ``origin_index`` implies ``origin_delta``

        return PanziOrigin(
            index=self._origin_index,
            delta=delta,
            state=state,
            stable_epoch=self.stability.stable_epoch,
            is_stable=self.stability.is_stable,
            is_monotone=self.stability.is_monotone,
        )

    def reset(self) -> None:
        """Clear recorded information so the helper can be reused."""

        self.existence = ExistenceWitness(self.predicate)
        self.stability = StabilityWitness(
            self.metric, epsilon=self.epsilon, tolerance=self.tolerance
        )
        self._origin_index = None
        self._origin_delta = None


def explore_origin(
    states: Iterable[State],
    *,
    predicate: Predicate,
    metric: Metric,
    epsilon: float = 1e-6,
    tolerance: float = 1e-12,
) -> Optional[PanziOrigin]:
    """Return the origin story discovered while traversing ``states``."""

    panzi = Panzi(
        predicate=predicate,
        metric=metric,
        epsilon=epsilon,
        tolerance=tolerance,
    )

    for state in states:
        panzi.observe(state)
        story = panzi.origin_story()
        if story is not None:
            return story

    return None


# Playful alias embracing the poetic naming convention.
磐子 = Panzi


__all__ = [
    "PanziObservation",
    "PanziOrigin",
    "Panzi",
    "explore_origin",
    "磐子",
]

