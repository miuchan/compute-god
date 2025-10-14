from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, MutableMapping, Protocol

State = MutableMapping[str, object]


class ObserverEvent(Enum):
    STEP = auto()
    EPOCH = auto()
    FIXPOINT_CONVERGED = auto()
    FIXPOINT_DIVERGED = auto()
    FIXPOINT_MAXED = auto()


class Observer(Protocol):
    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        ...


@dataclass
class NoopObserver:
    """Default observer that records nothing."""

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        return None


def combine_observers(*observers: Observer) -> Observer:
    def _combined(event: ObserverEvent, state: State, /, **metadata: object) -> None:
        for observer in observers:
            observer(event, state, **metadata)

    return _combined
