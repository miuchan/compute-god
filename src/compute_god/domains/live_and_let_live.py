"""Live and let live dynamics for resilient, mutual prosperity systems.

This module encodes a tiny governance loop inspired by the "让自己活也让别人活"
philosophy.  The state keeps track of how well a community cares for itself,
how much support it extends to others, and whether the commons remain
resilient.  Each iteration re-balances those quantities so no dimension can
dominate at the expense of the others.  The dynamics are intentionally
lightweight: they only rely on weighted averages, clamping within ``[0, 1]``
and a handful of feedback rates.

The defaults are calibrated to be numerically stable.  They converge to a
region where self support and shared support approach parity, trust grows
monotonically, and the commons stabilise above a configurable floor.  The
helper :func:`run_live_and_let_live` exposes the loop as a convenient
trajectory generator for notebooks and tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence


def _clamp(value: float, /, *, lower: float = 0.0, upper: float = 1.0) -> float:
    """Clamp ``value`` to the inclusive ``[lower, upper]`` interval."""

    return max(lower, min(upper, value))


def _blend(value: float, target: float, rate: float) -> float:
    """Move ``value`` toward ``target`` using a convex combination."""

    rate = _clamp(rate, lower=0.0, upper=1.0)
    return value + (target - value) * rate


@dataclass(frozen=True)
class LiveAndLetLiveParameters:
    """Configuration knobs steering the mutual prosperity dynamics."""

    adjustment_rate: float = 0.45
    empathy_feedback: float = 0.32
    commons_feedback: float = 0.38
    resilience_feedback: float = 0.42
    balance_sensitivity: float = 0.6
    self_bias: float = 0.62
    shared_bias: float = 0.58
    self_floor: float = 0.34
    shared_floor: float = 0.34
    resilience_floor: float = 0.36


LiveAndLetLiveState = MutableMapping[str, float]


DEFAULT_LIVE_AND_LET_LIVE_STATE: LiveAndLetLiveState = {
    "self_support": 0.48,
    "shared_support": 0.46,
    "trust": 0.41,
    "commons_health": 0.45,
    "resilience": 0.39,
    "fairness": 0.98,
    "vitality": 0.45,
    "live_and_let_live_index": 0.71,
}


def _prepare_state(state: Mapping[str, float] | None) -> LiveAndLetLiveState:
    prepared = dict(DEFAULT_LIVE_AND_LET_LIVE_STATE)
    if not state:
        return prepared

    for key, default in DEFAULT_LIVE_AND_LET_LIVE_STATE.items():
        if key in state:
            prepared[key] = _clamp(float(state[key]))
        else:
            prepared[key] = float(default)
    return prepared


def live_and_let_live_step(
    state: Mapping[str, float] | None = None,
    params: LiveAndLetLiveParameters | None = None,
) -> LiveAndLetLiveState:
    """Advance the live-and-let-live state by one mutual aid iteration."""

    params = params or LiveAndLetLiveParameters()
    current = _prepare_state(state)

    self_support = current["self_support"]
    shared_support = current["shared_support"]
    trust = current["trust"]
    commons = current["commons_health"]
    resilience = current["resilience"]

    # Encourage balance so neither self-support nor shared-support dominates.
    gap = self_support - shared_support
    correction = gap * params.balance_sensitivity
    self_support = _clamp(self_support - correction / 2.0)
    shared_support = _clamp(shared_support + correction / 2.0)

    peer_anchor = max(params.self_floor, (self_support + shared_support) / 2.0)
    self_target = _clamp(
        params.self_bias * self_support + (1.0 - params.self_bias) * peer_anchor
    )
    self_support = _blend(self_support, self_target, params.adjustment_rate)

    commons_anchor = max(params.shared_floor, (trust + commons) / 2.0)
    shared_target = _clamp(
        params.shared_bias * shared_support
        + (1.0 - params.shared_bias) * commons_anchor
    )
    shared_support = _blend(shared_support, shared_target, params.adjustment_rate)

    trust_target = _clamp((self_support + shared_support) / 2.0)
    trust = _blend(trust, trust_target, params.empathy_feedback)

    commons_target = _clamp(0.4 * shared_support + 0.35 * trust + 0.25 * resilience)
    commons = _blend(commons, commons_target, params.commons_feedback)

    resilience_target = _clamp((trust + commons) / 2.0)
    resilience = max(
        params.resilience_floor,
        _blend(resilience, resilience_target, params.resilience_feedback),
    )

    fairness = _clamp(1.0 - abs(self_support - shared_support))
    vitality = _clamp(
        0.35 * self_support + 0.35 * shared_support + 0.15 * trust + 0.15 * commons
    )
    index = _clamp(0.5 * fairness + 0.5 * vitality)

    return {
        "self_support": self_support,
        "shared_support": shared_support,
        "trust": trust,
        "commons_health": commons,
        "resilience": resilience,
        "fairness": fairness,
        "vitality": vitality,
        "live_and_let_live_index": index,
    }


def run_live_and_let_live(
    *,
    initial_state: Mapping[str, float] | None = None,
    params: LiveAndLetLiveParameters | None = None,
    epochs: int = 48,
) -> Sequence[LiveAndLetLiveState]:
    """Generate a trajectory of live-and-let-live states."""

    params = params or LiveAndLetLiveParameters()
    current = _prepare_state(initial_state)
    history = [dict(current)]

    for _ in range(max(0, epochs)):
        current = live_and_let_live_step(current, params)
        history.append(dict(current))

    return history


# Chinese alias mirroring the philosophy's original phrasing.
让自己活也让别人活 = run_live_and_let_live


__all__ = [
    "LiveAndLetLiveParameters",
    "LiveAndLetLiveState",
    "DEFAULT_LIVE_AND_LET_LIVE_STATE",
    "live_and_let_live_step",
    "run_live_and_let_live",
    "让自己活也让别人活",
]

