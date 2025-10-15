from __future__ import annotations

import math

import pytest

from compute_god.shuangxiang import (
    BiphasicState,
    optimise_biphasic_state,
)


def test_biphasic_gradient_descends_to_target() -> None:
    target = BiphasicState(hot=1.0, cold=-1.0)
    state = BiphasicState(hot=5.0, cold=-5.0)

    def objective(candidate: BiphasicState) -> tuple[float, tuple[float, float]]:
        hot_error = candidate.hot - target.hot
        cold_error = candidate.cold - target.cold
        value = 0.5 * (hot_error * hot_error + cold_error * cold_error)
        gradient = (hot_error, cold_error)
        return value, gradient

    result = optimise_biphasic_state(
        state,
        objective,
        learning_rate=0.2,
        tolerance=1e-9,
        max_iter=256,
    )

    assert result.converged is True
    assert result.iterations < 256
    assert state.hot == pytest.approx(target.hot, abs=1e-6)
    assert state.cold == pytest.approx(target.cold, abs=1e-6)
    assert result.objective_value == pytest.approx(0.0, abs=1e-9)


def test_biphasic_gradient_respects_projection() -> None:
    state = BiphasicState(hot=0.0, cold=0.0)

    def objective(candidate: BiphasicState) -> tuple[float, tuple[float, float]]:
        hot_error = candidate.hot - 5.0
        cold_error = candidate.cold + 5.0
        value = 0.5 * (hot_error * hot_error + cold_error * cold_error)
        gradient = (hot_error, cold_error)
        return value, gradient

    def projection(values: list[float]) -> tuple[float, float]:
        return tuple(max(-1.0, min(1.0, value)) for value in values)

    result = optimise_biphasic_state(
        state,
        objective,
        learning_rate=0.5,
        tolerance=1e-9,
        max_iter=64,
        projection=projection,
    )

    assert result.converged is True
    assert -1.0 <= state.hot <= 1.0
    assert -1.0 <= state.cold <= 1.0
    assert math.isclose(state.gap, 2.0, abs_tol=1e-9)


def test_biphasic_gradient_validates_inputs() -> None:
    state = BiphasicState(hot=0.0, cold=0.0)

    def invalid_objective(candidate: BiphasicState) -> tuple[float, tuple[float]]:
        return 0.0, (1.0,)

    with pytest.raises(ValueError):
        optimise_biphasic_state(state, invalid_objective)  # type: ignore[arg-type]

    def objective(candidate: BiphasicState) -> tuple[float, tuple[float, float]]:
        return 0.0, (0.0, 0.0)

    with pytest.raises(ValueError):
        optimise_biphasic_state(state, objective, learning_rate=0.0)

