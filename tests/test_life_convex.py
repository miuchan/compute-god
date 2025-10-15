import math

from compute_god.life import LifeLattice, optimise_game_of_life


def _flatten(matrix):
    return [value for row in matrix for value in row]


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
