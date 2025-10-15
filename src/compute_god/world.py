"""Utilities for dramatizing the canonical "world.execute(me);" invocation.

The helpers in this module provide a very small wrapper around the fixpoint
engine.  They construct a universe whose only goal is to take an arbitrary
subject and turn it into the self-referential ``world.execute(subject);``
incantation.  The process is intentionally over-engineered to mirror the rest
of the project: even tiny strings are treated as states that evolve under a
rule until a fixpoint is reached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .engine import FixpointResult, Metric, fixpoint
from .rule import State, rule
from .universe import God


@dataclass(frozen=True)
class WorldExecutionRequest:
    """Configuration describing how the world should "execute" a subject."""

    subject: str = "me"
    world: str = "world"
    punctuation: str = ";"
    history_key: str = "history"
    script_key: str = "script"

    def invocation(self) -> str:
        return f"{self.world}.execute({self.subject}){self.punctuation}"


def _default_metric(key: str) -> Metric:
    def metric(previous: State, current: State) -> float:
        return 0.0 if previous.get(key) == current.get(key) else 1.0

    return metric


def world_execute(
    request: Optional[WorldExecutionRequest] = None,
    *,
    metric: Optional[Metric] = None,
    max_epoch: int = 4,
) -> FixpointResult:
    """Drive a toy universe to manifest ``world.execute(subject);``.

    Parameters
    ----------
    request:
        Optional :class:`WorldExecutionRequest` describing how to format the
        invocation.  When omitted a default request for ``"me"`` is used.
    metric:
        An optional metric to determine convergence.  The default checks whether
        the ``script`` entry of the state changes between epochs.
    max_epoch:
        Maximum number of epochs to spend searching for a fixpoint.  The default
        of four is plenty because the constructed universe converges in one
        epoch.
    """

    if request is None:
        request = WorldExecutionRequest()

    script_key = request.script_key
    history_key = request.history_key

    invocation = request.invocation()

    def assemble_state(subject: str) -> State:
        return {
            script_key: subject,
            history_key: [subject],
        }

    if metric is None:
        metric = _default_metric(script_key)

    def apply_rule(state: State) -> State:
        if state.get(script_key) == invocation:
            return state
        new_state = dict(state)
        history = list(new_state.get(history_key, ()))
        history.append(invocation)
        new_state[history_key] = history
        new_state[script_key] = invocation
        return new_state

    execution_universe = God.universe(
        state=assemble_state(request.subject),
        rules=[
            rule(
                "world.execute",
                apply_rule,
                guard=lambda state, _ctx: state.get(script_key) != invocation,
                until=lambda state, _ctx: state.get(script_key) == invocation,
            )
        ],
    )

    return fixpoint(
        execution_universe,
        metric=metric,
        epsilon=0.0,
        max_epoch=max_epoch,
    )
