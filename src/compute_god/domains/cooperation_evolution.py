"""Replicator-style helpers for evolving cooperation in social systems.

The routines model how a population of cooperating and defecting strategies can
shift over time when iterated under a light-weight replicator dynamic.  The
implementation purposefully keeps the state compact so that other universes in
the repository can import the helpers and blend them with their own
observations.

Only a handful of numeric inputs are required: the four canonical Prisoner's
Dilemma payoffs, a learning rate describing how quickly the population reacts
to incentives, and a small mutation rate to prevent the system from collapsing
to extreme points.  Additional trust and reputation channels help encode how a
community rewards consistent cooperative behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence


def _bounded(value: float) -> float:
    """Clamp ``value`` to the inclusive ``[0.0, 1.0]`` range."""

    return max(0.0, min(1.0, value))


def _normalise_pair(cooperation: float, defection: float) -> Sequence[float]:
    total = cooperation + defection
    if total <= 0:
        return 0.5, 0.5
    cooperation /= total
    return cooperation, 1.0 - cooperation


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


@dataclass(frozen=True)
class CooperationParameters:
    """Parameters describing how cooperation evolves within the population."""

    reward: float = 1.2
    temptation: float = 0.9
    punishment: float = 0.25
    sucker: float = 0.05
    learning_rate: float = 0.4
    mutation_rate: float = 0.02
    trust_feedback: float = 0.25
    reputation_feedback: float = 0.18


CooperationState = MutableMapping[str, float]


DEFAULT_COOPERATION_STATE: CooperationState = {
    "cooperation": 0.46,
    "defection": 0.54,
    "trust": 0.38,
    "reputation": 0.35,
    "stability": 0.32,
}


def evolve_cooperation(
    state: Mapping[str, float],
    params: CooperationParameters | None = None,
) -> CooperationState:
    """Advance a cooperation state using a discrete replicator update."""

    params = params or CooperationParameters()

    cooperation = _bounded(float(state.get("cooperation", 0.5)))
    defection = _bounded(float(state.get("defection", 1.0 - cooperation)))
    cooperation, defection = _normalise_pair(cooperation, defection)

    payoff_coop = params.reward * cooperation + params.sucker * defection
    payoff_defect = params.temptation * cooperation + params.punishment * defection
    avg_payoff = cooperation * payoff_coop + defection * payoff_defect

    base_cooperation = cooperation + params.learning_rate * cooperation * (payoff_coop - avg_payoff)
    base_cooperation = (1.0 - params.mutation_rate) * base_cooperation + params.mutation_rate * 0.5
    base_cooperation = _bounded(base_cooperation)

    trust = _bounded(float(state.get("trust", 0.4)))
    reputation = _bounded(float(state.get("reputation", 0.4)))
    stability = _bounded(float(state.get("stability", 0.4)))

    trust = _towards(trust, base_cooperation, params.trust_feedback)
    reputation = _towards(reputation, trust, params.reputation_feedback)

    social_target = _bounded(0.55 * trust + 0.45 * base_cooperation)
    next_cooperation = _towards(base_cooperation, social_target, 0.5)
    next_cooperation = _bounded(next_cooperation)
    next_defection = _bounded(1.0 - next_cooperation)

    stability_target = (next_cooperation + trust + reputation) / 3.0
    stability = _towards(stability, stability_target, 0.3)

    return {
        "cooperation": next_cooperation,
        "defection": next_defection,
        "trust": trust,
        "reputation": reputation,
        "stability": stability,
        "avg_payoff": avg_payoff,
    }


def run_cooperation_evolution(
    *,
    initial_state: Mapping[str, float] | None = None,
    params: CooperationParameters | None = None,
    epochs: int = 96,
) -> Sequence[CooperationState]:
    """Iterate :func:`evolve_cooperation` and return the full trajectory."""

    params = params or CooperationParameters()
    current = dict(initial_state or DEFAULT_COOPERATION_STATE)
    history = [dict(current)]

    for _ in range(max(0, epochs)):
        current = evolve_cooperation(current, params)
        history.append(dict(current))

    return history


__all__ = [
    "CooperationParameters",
    "CooperationState",
    "DEFAULT_COOPERATION_STATE",
    "evolve_cooperation",
    "run_cooperation_evolution",
]
