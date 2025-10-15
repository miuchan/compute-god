import math

from compute_god import (
    ThresholdOptimisationResult,
    ThresholdSpace,
    optimise_threshold_space,
)


def quadratic_objective(target):
    def objective(vector):
        value = 0.0
        gradient = []
        for v, t in zip(vector, target):
            diff = v - t
            value += diff * diff
            gradient.append(2 * diff)
        return value, gradient

    return objective


def test_threshold_convex_optimisation_hits_target():
    space = ThresholdSpace(
        lower_bounds=[0.1, 0.2, 0.3],
        upper_bounds=[0.6, 0.8, 0.9],
        total=1.2,
        initial=[0.3, 0.4, 0.5],
    )

    target = [0.2, 0.5, 0.5]

    result = optimise_threshold_space(
        space,
        quadratic_objective(target),
        learning_rate=0.25,
        max_iter=256,
        tolerance=1e-6,
    )

    assert isinstance(result, ThresholdOptimisationResult)
    assert result.converged is True
    assert result.iterations < 256

    vector = space.as_vector()
    assert math.isclose(sum(vector), 1.2, rel_tol=1e-8, abs_tol=1e-8)
    for value, low, high in zip(vector, [0.1, 0.2, 0.3], [0.6, 0.8, 0.9]):
        assert low - 1e-9 <= value <= high + 1e-9


def test_threshold_projection_respects_bounds():
    space = ThresholdSpace(
        lower_bounds=[0.2, 0.1, 0.4, 0.3],
        upper_bounds=[1.2, 0.9, 1.5, 1.0],
        total=2.5,
    )

    target = [0.4, 0.4, 1.4, 0.3]

    result = optimise_threshold_space(
        space,
        quadratic_objective(target),
        learning_rate=0.2,
        max_iter=128,
        tolerance=1e-6,
    )

    assert result.converged is True

    vector = space.as_vector()
    assert math.isclose(sum(vector), 2.5, rel_tol=1e-8, abs_tol=1e-8)
    for value, low, high in zip(vector, [0.2, 0.1, 0.4, 0.3], [1.2, 0.9, 1.5, 1.0]):
        assert low - 1e-9 <= value <= high + 1e-9

