from __future__ import annotations

from compute_god.marketing import (
    FunnelParameters,
    funnel_map,
    l1_metric,
    marketing_fixpoint,
)


def _leq(state_a, state_b):
    return all(state_a[key] <= state_b[key] for key in ("awareness", "engagement", "customers"))


def test_funnel_map_is_monotone():
    params = FunnelParameters(
        awareness_budget=0.2,
        engagement_rate=0.4,
        conversion_rate=0.3,
        retention_rate=0.7,
    )

    state_low = {"awareness": 0.1, "engagement": 0.05, "customers": 0.02}
    state_high = {"awareness": 0.2, "engagement": 0.1, "customers": 0.05}

    assert _leq(state_low, state_high)

    next_low = funnel_map(state_low, params)
    next_high = funnel_map(state_high, params)

    assert _leq(next_low, next_high)


def test_marketing_fixpoint_converges_and_is_a_fixed_point():
    params = FunnelParameters(
        awareness_budget=0.3,
        engagement_rate=0.5,
        conversion_rate=0.35,
        retention_rate=0.6,
    )

    initial_state = {"awareness": 0.0, "engagement": 0.0, "customers": 0.0}

    result = marketing_fixpoint(initial_state, params, epsilon=1e-9, max_epoch=64)

    assert result.converged
    assert result.epochs < 64

    final_state = result.universe.state
    next_state = funnel_map(final_state, params)

    assert l1_metric(final_state, next_state) <= 1e-8
