from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .observer import Observer, ObserverEvent, combine_observers
from .rule import RuleContext, State
from .universe import God, Universe

Metric = Callable[[State, State], float]


@dataclass
class FixpointResult:
    universe: Universe
    converged: bool
    epochs: int


class _EpochContext:
    def __init__(self, *, observer: Observer, metric: Metric, epsilon: float) -> None:
        self._observer = observer
        self._metric = metric
        self._epsilon = epsilon
        self._last_state: Optional[State] = None

    def record(self, state: State) -> None:
        if self._last_state is None:
            self._last_state = dict(state)
            return
        delta = self._metric(self._last_state, state)
        self._last_state = dict(state)
        if delta <= self._epsilon:
            self._observer(ObserverEvent.FIXPOINT_CONVERGED, state, delta=delta)
        else:
            self._observer(ObserverEvent.EPOCH, state, delta=delta)


def _clone_state(state: State) -> State:
    return dict(state)


def _apply_rules(universe: Universe, ctx: RuleContext, observer: Observer) -> State:
    state = _clone_state(universe.state)
    for rule in universe.sorted_rules():
        if not rule.should_fire(state, ctx):
            continue
        new_state = rule.apply(state, ctx)
        maybe_state = new_state
        if hasattr(maybe_state, "__await__"):
            raise TypeError("Async rules are not supported in sync execution")
        state = maybe_state
        ctx.increment()
        observer(ObserverEvent.STEP, state, rule=rule.name, steps=ctx.steps())
        if rule.should_stop(state, ctx):
            break
    return state


def fixpoint(
    universe: Universe,
    *,
    metric: Metric,
    epsilon: float,
    max_epoch: int,
    observer: Optional[Observer] = None,
) -> FixpointResult:
    ctx = God.rule_context()
    if observer is None:
        observer = combine_observers(*universe.observers)
    epoch_ctx = _EpochContext(observer=observer, metric=metric, epsilon=epsilon)

    for epoch in range(1, max_epoch + 1):
        new_state = _apply_rules(universe, ctx, observer)
        observer(ObserverEvent.EPOCH, new_state, epoch=epoch)
        epoch_ctx.record(new_state)
        if new_state == universe.state:
            observer(ObserverEvent.FIXPOINT_CONVERGED, new_state, epoch=epoch)
            return FixpointResult(universe=Universe(new_state, universe.rules, universe.observers), converged=True, epochs=epoch)
        universe = Universe(new_state, universe.rules, universe.observers)

    observer(ObserverEvent.FIXPOINT_MAXED, universe.state, epoch=max_epoch)
    return FixpointResult(universe=universe, converged=False, epochs=max_epoch)
