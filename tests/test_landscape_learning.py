"""Regression tests for :mod:`compute_god.landscape_learning`."""

from __future__ import annotations

import math

import pytest

from compute_god.landscape_learning import (
    LandscapeLearningParameters,
    LandscapeSample,
    initialise_grid,
    landscape_learning_universe,
    learn_landscape,
)


def grid_values(result_grid):
    """Return the grid as a plain ``dict`` with consistent float precision."""

    return {coord: float(value) for coord, value in result_grid.items()}


def test_initialise_grid_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError):
        initialise_grid(0, 2)

    with pytest.raises(ValueError):
        initialise_grid(2, 0)


def test_landscape_universe_history_toggle() -> None:
    grid = initialise_grid(2, 2)
    samples = [LandscapeSample((0, 0), elevation=1.0)]
    params = LandscapeLearningParameters(learning_rate=0.5, smoothing=0.0)

    universe_with_history = landscape_learning_universe(
        grid,
        samples,
        params,
        track_history=True,
    )
    assert "history" in universe_with_history.state
    assert universe_with_history.state["history"] == [grid_values(grid)]

    universe_without_history = landscape_learning_universe(
        grid,
        samples,
        params,
        track_history=False,
    )
    assert "history" not in universe_without_history.state


def test_learn_landscape_converges_to_sample_height() -> None:
    grid = initialise_grid(2, 2)
    samples = [LandscapeSample((0, 1), elevation=1.0)]
    params = LandscapeLearningParameters(learning_rate=0.5, smoothing=0.0)

    result = learn_landscape(
        grid,
        samples,
        params,
        epsilon=1e-6,
        max_epoch=64,
        track_history=True,
    )

    assert result.converged
    learned_grid = result.universe.state["grid"]
    assert math.isclose(learned_grid[(0, 1)], 1.0, rel_tol=1e-6, abs_tol=1e-6)
    for coord, value in learned_grid.items():
        if coord != (0, 1):
            assert math.isclose(value, 0.0, abs_tol=1e-6)

    history = result.universe.state["history"]
    assert history[0] == grid_values(grid)
    assert history[-1] == grid_values(learned_grid)


def test_learn_landscape_respects_noise_floor() -> None:
    grid = initialise_grid(1, 1)
    samples = [LandscapeSample((0, 0), elevation=0.04)]
    params = LandscapeLearningParameters(
        learning_rate=0.5,
        smoothing=0.0,
        noise_floor=0.05,
    )

    result = learn_landscape(
        grid,
        samples,
        params,
        epsilon=1e-6,
        max_epoch=16,
    )

    assert result.converged
    assert result.universe.state["grid"][(0, 0)] == pytest.approx(0.0)


def test_learn_landscape_rejects_out_of_bounds_samples() -> None:
    grid = initialise_grid(2, 2)
    samples = [LandscapeSample((3, 0), elevation=1.0)]

    with pytest.raises(KeyError):
        learn_landscape(grid, samples)
