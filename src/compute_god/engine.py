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
    def __init__(
        self,
        *,
        observer: Observer,
        metric: Metric,
        epsilon: float,
        initial_state: State,
    ) -> None:
        self._observer = observer
        self._metric = metric
        self._epsilon = epsilon
        self._previous_state: State = dict(initial_state)

    def record(self, state: State, *, epoch: int) -> bool:
        delta = self._metric(self._previous_state, state)
        self._previous_state = dict(state)
        if delta <= self._epsilon:
            self._observer(
                ObserverEvent.FIXPOINT_CONVERGED,
                state,
                epoch=epoch,
                delta=delta,
            )
            return True

        self._observer(ObserverEvent.EPOCH, state, epoch=epoch, delta=delta)
        return False


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
    epoch_ctx = _EpochContext(
        observer=observer,
        metric=metric,
        epsilon=epsilon,
        initial_state=universe.state,
    )

    for epoch in range(1, max_epoch + 1):
        new_state = _apply_rules(universe, ctx, observer)
        universe = Universe(new_state, universe.rules, universe.observers)
        if epoch_ctx.record(new_state, epoch=epoch):
            return FixpointResult(universe=universe, converged=True, epochs=epoch)

    observer(ObserverEvent.FIXPOINT_MAXED, universe.state, epoch=max_epoch)
    return FixpointResult(universe=universe, converged=False, epochs=max_epoch)
