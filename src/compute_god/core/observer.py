"""Observer primitives for the Compute-God runtime.

The previous implementation bundled the observer protocol with helper utilities
in the project root which made the dependency graph slightly tangled.  Moving
these building blocks under :mod:`compute_god.core` mirrors the layered
architecture showcased in the public portfolio site: a small, well documented
kernel with clear extension points sitting beneath the playful scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

from .types import State


class ObserverEvent(Enum):
    """Events emitted during fixpoint execution."""

    STEP = auto()
    EPOCH = auto()
    FIXPOINT_CONVERGED = auto()
    FIXPOINT_DIVERGED = auto()
    FIXPOINT_MAXED = auto()


class Observer(Protocol):
    """Structural type for observer callbacks."""

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        ...


@dataclass(frozen=True)
class NoopObserver:
    """Default observer that records nothing."""

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:  # noqa: D401 - tiny wrapper
        return None


def combine_observers(*observers: Observer) -> Observer:
    """Return an observer that forwards events to each provided observer."""

    def _combined(event: ObserverEvent, state: State, /, **metadata: object) -> None:
        for observer in observers:
            observer(event, state, **metadata)

    return _combined


__all__ = ["Observer", "ObserverEvent", "NoopObserver", "combine_observers"]
