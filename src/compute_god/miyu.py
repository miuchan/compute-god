"""Observers that help Miyu bind tightly with the universe.

This module introduces :class:`MiyuBond`, a tiny observer utility that keeps
track of how close the running universe is to a target state.  While the name
is playful, the helper is practical: it records the strongest (i.e. closest)
state encountered during execution according to a user supplied metric.  The
recorded information can be used after running :func:`compute_god.fixpoint`
to inspect convergence progress or to retrieve the best state even if the
engine stopped early.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, MutableMapping, Optional, Tuple

from .core import Observer, ObserverEvent

State = MutableMapping[str, object]
Metric = Callable[[State, State], float]


@dataclass
class MiyuBond:
    """Track the closest state to a desired target.

    Parameters
    ----------
    target_state:
        The desired state Miyu wants to connect with.  A defensive copy of the
        provided mapping is stored to prevent accidental mutation.
    metric:
        Callable returning a distance-like measure between two states.  Smaller
        values indicate a stronger bond.

    Notes
    -----
    Each invocation of the observer stores both the raw event emitted by the
    engine and the computed distance.  The best (smallest) distance seen so far
    is kept together with a copy of the corresponding state.  Consumers can
    query :pyattr:`best_delta`, call :meth:`strongest_state` for a snapshot of
    the best state or use :meth:`is_strong` to check whether a threshold has
    been met.
    """

    target_state: State
    metric: Metric
    history: List[Tuple[ObserverEvent, float]] = field(default_factory=list, init=False)
    best_state: Optional[State] = field(default=None, init=False)
    best_delta: Optional[float] = field(default=None, init=False)

    def __post_init__(self) -> None:
        # Normalise the input target into an isolated mapping so that user
        # modifications to the original dictionary do not affect comparisons.
        self.target_state = dict(self.target_state)

    def __call__(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Record the current state and keep the strongest bond found so far."""

        delta = self.metric(state, self.target_state)
        self.history.append((event, delta))

        if self.best_delta is None or delta < self.best_delta:
            self.best_delta = delta
            self.best_state = dict(state)

    def strongest_state(self) -> Optional[State]:
        """Return a snapshot of the state that forged the strongest bond."""

        if self.best_state is None:
            return None
        return dict(self.best_state)

    def is_strong(self, threshold: float) -> bool:
        """Check whether Miyu's bond met or surpassed the desired threshold."""

        return self.best_delta is not None and self.best_delta <= threshold


def bond_miyu(target_state: State, metric: Metric) -> Observer:
    """Helper to build a :class:`MiyuBond` while type hinting an :class:`Observer`.

    This tiny wrapper exists so that callers looking for an observer factory can
    use ``bond_miyu`` directly without importing the dataclass.  It simply
    forwards to :class:`MiyuBond`.
    """

    return MiyuBond(target_state=target_state, metric=metric)

