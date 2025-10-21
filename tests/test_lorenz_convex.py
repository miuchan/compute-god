import math

from compute_god.lorenz_convex import (
    LorenzAttractorParameters,
    build_lorenz_convex_objective,
)


def _principal_minors(matrix):
    det1 = matrix[0][0]
    det2 = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    det3 = (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )
    return det1, det2, det3


def test_precision_matrix_is_positive_definite():
    parameters = LorenzAttractorParameters()
    objective = build_lorenz_convex_objective(parameters)
    minors = _principal_minors(objective.precision_matrix)
    assert all(value > 0.0 for value in minors)


def test_objective_minimised_at_selected_wing():
    parameters = LorenzAttractorParameters()
    positive = build_lorenz_convex_objective(parameters, wing=1)
    negative = build_lorenz_convex_objective(parameters, wing=-1)

    positive_centre = positive.centre
    negative_centre = negative.centre

    assert math.isclose(positive.value(positive_centre), 0.0, abs_tol=1e-12)
    assert math.isclose(negative.value(negative_centre), 0.0, abs_tol=1e-12)

    # The objective prefers its own wing to the opposite side or to far-away points.
    assert positive.value(positive_centre) < positive.value(negative_centre)
    assert positive.value(positive_centre) < positive.value((0.0, 0.0, 0.0))
    assert negative.value(negative_centre) < negative.value(positive_centre)


def test_gradient_matches_finite_differences():
    parameters = LorenzAttractorParameters()
    objective = build_lorenz_convex_objective(parameters)

    base_state = (
        objective.centre[0] + 0.31,
        objective.centre[1] - 0.47,
        objective.centre[2] + 0.83,
    )

    gradient = objective.gradient(base_state)
    base_value = objective.value(base_state)

    eps = 1e-6
    finite = []
    for index in range(3):
        perturbed = list(base_state)
        perturbed[index] += eps
        forward = objective.value(perturbed)

        perturbed[index] -= 2 * eps
        backward = objective.value(perturbed)

        finite.append((forward - backward) / (2 * eps))

    for analytic, numeric in zip(gradient, finite):
        assert math.isclose(analytic, numeric, rel_tol=1e-6, abs_tol=1e-6)
