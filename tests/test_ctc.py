import math

from compute_god import (
    ClosedTimelikeCurve,
    optimise_closed_timelike_curve,
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


def test_ctc_convex_optimisation_reaches_target():
    curve = ClosedTimelikeCurve(segments=[0.6, 0.4], period=1.0)
    target = [0.2, 0.8]

    result = optimise_closed_timelike_curve(
        curve,
        quadratic_objective(target),
        learning_rate=0.2,
        max_iter=200,
        tolerance=1e-6,
    )

    assert result.converged is True
    assert result.iterations < 200
    optimised = curve.as_vector()
    assert math.isclose(sum(optimised), 1.0, rel_tol=1e-8, abs_tol=1e-8)
    for value, target_value in zip(optimised, target):
        assert math.isclose(value, target_value, rel_tol=1e-3, abs_tol=1e-3)


def test_ctc_convex_optimisation_respects_simplex():
    curve = ClosedTimelikeCurve(segments=[0.1, 0.2, 0.7], period=2.0)
    target = [1.0, 0.4, 0.6]

    result = optimise_closed_timelike_curve(
        curve,
        quadratic_objective(target),
        learning_rate=0.15,
        max_iter=128,
        tolerance=1e-6,
    )

    assert result.converged is True
    vector = curve.as_vector()
    assert math.isclose(sum(vector), 2.0, rel_tol=1e-8, abs_tol=1e-8)
    assert all(value >= 0 for value in vector)


def test_ctc_bounded_projection_respects_limits():
    curve = ClosedTimelikeCurve(
        segments=[0.6, 0.3, 0.1],
        period=1.2,
        lower_bounds=[0.2, 0.1, 0.1],
        upper_bounds=[0.7, 0.5, 0.4],
    )

    target = [0.5, 0.6, 0.1]

    result = optimise_closed_timelike_curve(
        curve,
        quadratic_objective(target),
        learning_rate=0.2,
        max_iter=256,
        tolerance=1e-7,
    )

    assert result.converged is True

    vector = curve.as_vector()
    assert math.isclose(sum(vector), 1.2, rel_tol=1e-8, abs_tol=1e-8)
    for value, low, high in zip(vector, [0.2, 0.1, 0.1], [0.7, 0.5, 0.4]):
        assert low - 1e-9 <= value <= high + 1e-9

    # The target for the second segment exceeds its upper bound, so the
    # optimiser should saturate it at the provided limit.
    assert math.isclose(vector[1], 0.5, rel_tol=1e-8, abs_tol=1e-8)
