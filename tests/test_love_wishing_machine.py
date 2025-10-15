from __future__ import annotations

from compute_god.love_wishing_machine import (
    WishParameters,
    love_wishing_fixpoint,
    love_wishing_map,
    love_wishing_metric,
    wish_granted,
)


def _leq(state_a, state_b):
    return all(
        state_a[key] <= state_b[key]
        for key in ("self_love", "openness", "resonance", "blessing")
    )


def test_love_wishing_map_is_monotone():
    params = WishParameters(
        self_cultivation=0.3,
        openness_gain=0.25,
        resonance_rate=0.4,
        blessing_feed=0.5,
        patience=0.6,
        release_rate=0.3,
        radiance=0.1,
    )

    state_low = {"self_love": 0.1, "openness": 0.05, "resonance": 0.02, "blessing": 0.03}
    state_high = {"self_love": 0.2, "openness": 0.15, "resonance": 0.12, "blessing": 0.18}

    assert _leq(state_low, state_high)

    next_low = love_wishing_map(state_low, params)
    next_high = love_wishing_map(state_high, params)

    assert _leq(next_low, next_high)


def test_love_wishing_fixpoint_converges_and_is_fixed_point():
    params = WishParameters(
        self_cultivation=0.4,
        openness_gain=0.35,
        resonance_rate=0.5,
        blessing_feed=0.45,
        patience=0.55,
        release_rate=0.25,
        radiance=0.08,
    )

    initial_state = {
        "self_love": 0.0,
        "openness": 0.0,
        "resonance": 0.0,
        "blessing": 0.0,
    }

    result = love_wishing_fixpoint(initial_state, params, epsilon=1e-9, max_epoch=128)

    assert result.converged
    assert result.epochs < 128

    final_state = result.universe.state
    next_state = love_wishing_map(final_state, params)

    assert love_wishing_metric(final_state, next_state) <= 1e-8


def test_wish_granted_uses_threshold_and_validates_input():
    fulfilled_state = {"self_love": 0.92, "openness": 0.9, "resonance": 0.95, "blessing": 0.91}
    shy_state = {"self_love": 0.8, "openness": 0.82, "resonance": 0.81, "blessing": 0.83}

    assert wish_granted(fulfilled_state)
    assert not wish_granted(shy_state, threshold=0.9)

    try:
        wish_granted(fulfilled_state, threshold=-0.1)
    except ValueError:
        pass
    else:  # pragma: no cover - defensive guard to ensure the exception happens
        raise AssertionError("negative threshold should raise ValueError")

