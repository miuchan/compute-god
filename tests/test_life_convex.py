import math

from compute_god.life import LifeLattice, optimise_game_of_life, optimise_game_of_life_multistep


def _flatten(matrix):
    return [value for row in matrix for value in row]


def _linear_response(vector, neighbours, *, survival_weight, birth_weight):
    neighbour_factor = birth_weight / 3.0
    response = []
    for value, adjacent in zip(vector, neighbours):
        neighbour_sum = sum(vector[index] for index in adjacent)
        response.append(survival_weight * value + neighbour_factor * neighbour_sum)
    return response


def _relaxed_steps(lattice, *, steps, survival_weight, birth_weight):
    current = lattice.as_vector()
    neighbours = lattice.neighbours()
    for _ in range(steps):
        current = _linear_response(
            current,
            neighbours,
            survival_weight=survival_weight,
            birth_weight=birth_weight,
        )
    width = lattice.width
    return [current[row_start : row_start + width] for row_start in range(0, len(current), width)]


def test_game_of_life_convex_optimisation_recovers_pattern():
    blinker = [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
    ]

    ground_truth = LifeLattice(height=5, width=5, initial_state=blinker)
    target = ground_truth.relaxed_step(survival_weight=0.6, birth_weight=0.4)

    lattice = LifeLattice(height=5, width=5)
    result = optimise_game_of_life(
        lattice,
        target,
        survival_weight=0.6,
        birth_weight=0.4,
        learning_rate=0.45,
        max_iter=600,
        tolerance=1e-8,
    )

    assert result.converged is True
    optimised = lattice.as_vector()
    expected = _flatten(blinker)
    for value, target_value in zip(optimised, expected):
        assert math.isclose(value, target_value, rel_tol=1e-2, abs_tol=1e-2)

    relaxed = lattice.relaxed_step(survival_weight=0.6, birth_weight=0.4)
    for row_target, row_relaxed in zip(target, relaxed):
        for expected_value, actual_value in zip(row_target, row_relaxed):
            assert math.isclose(expected_value, actual_value, rel_tol=1e-4, abs_tol=1e-4)


def test_game_of_life_optimisation_tracks_progress_via_callback():
    target = [
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0],
    ]

    lattice = LifeLattice(height=3, width=3)
    history = []

    def callback(iteration, board, objective_value):
        history.append((iteration, objective_value, board))

    result = optimise_game_of_life(
        lattice,
        target,
        survival_weight=0.55,
        birth_weight=0.45,
        learning_rate=0.35,
        max_iter=120,
        tolerance=1e-7,
        callback=callback,
    )

    assert history
    assert history[0][0] == 1
    assert history[-1][0] == result.iterations
    assert result.objective_value <= history[0][1]

    state = lattice.as_vector()
    assert all(0.0 <= value <= 1.0 for value in state)


def test_game_of_life_multistep_inference():
    glider = [
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [1.0, 1.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ]

    survival_weight = 0.62
    birth_weight = 0.38

    ground_truth = LifeLattice(height=4, width=4, initial_state=glider)
    target_lattice = LifeLattice(height=4, width=4, initial_state=glider)
    target = _relaxed_steps(
        target_lattice,
        steps=3,
        survival_weight=survival_weight,
        birth_weight=birth_weight,
    )

    lattice = LifeLattice(height=4, width=4)
    result = optimise_game_of_life_multistep(
        lattice,
        target,
        steps=3,
        survival_weight=survival_weight,
        birth_weight=birth_weight,
        learning_rate=0.25,
        max_iter=1500,
        tolerance=1e-6,
    )

    assert result.objective_value < 1e-3

    recovered = LifeLattice(height=4, width=4, initial_state=lattice.as_vector())
    reconstructed = _relaxed_steps(
        recovered,
        steps=3,
        survival_weight=survival_weight,
        birth_weight=birth_weight,
    )

    for row_target, row_reconstructed in zip(target, reconstructed):
        for expected_value, actual_value in zip(row_target, row_reconstructed):
            assert math.isclose(expected_value, actual_value, rel_tol=2e-2, abs_tol=2e-2)
