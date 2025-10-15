import math

import pytest

from compute_god.rule import rule
from compute_god.rule_optimisation import RuleOptimisationResult, optimise_rule_weights


def test_rule_convex_optimisation_recovers_target_state() -> None:
    base_state = {"x": 0.0}

    inc_one = rule("inc_one", lambda state: {"x": state["x"] + 1.0})
    inc_two = rule("inc_two", lambda state: {"x": state["x"] + 2.0})

    result = optimise_rule_weights(
        base_state,
        [inc_one, inc_two],
        target_state={"x": 1.5},
        learning_rate=0.45,
        max_iter=400,
        tolerance=1e-8,
    )

    assert isinstance(result, RuleOptimisationResult)
    assert result.converged is True
    assert math.isclose(result.weights[0], 0.5, rel_tol=1e-4, abs_tol=1e-4)
    assert math.isclose(result.weights[1], 0.5, rel_tol=1e-4, abs_tol=1e-4)
    assert math.isclose(result.state["x"], 1.5, rel_tol=1e-5, abs_tol=1e-5)
    assert result.objective_value <= 1e-6


def test_rule_convex_optimisation_callback_tracks_iterations() -> None:
    base_state = {"x": 0.0, "y": 0.0}

    move_x = rule("move_x", lambda state: {"x": state["x"] + 1.0, "y": state["y"]})
    move_y = rule("move_y", lambda state: {"x": state["x"], "y": state["y"] + 1.0})

    history = []

    def callback(iteration, weights, objective_value):
        history.append((iteration, list(weights), objective_value))

    result = optimise_rule_weights(
        base_state,
        [move_x, move_y],
        target_state={"x": 0.6, "y": 0.4},
        learning_rate=0.35,
        max_iter=200,
        tolerance=1e-9,
        callback=callback,
    )

    assert history
    assert history[0][0] == 1
    assert history[-1][0] == result.iterations
    assert result.converged is True

    final_weights = history[-1][1]
    assert math.isclose(final_weights[0], 0.6, rel_tol=1e-4, abs_tol=1e-4)
    assert math.isclose(final_weights[1], 0.4, rel_tol=1e-4, abs_tol=1e-4)

    assert math.isclose(result.state["x"], 0.6, rel_tol=1e-5, abs_tol=1e-5)
    assert math.isclose(result.state["y"], 0.4, rel_tol=1e-5, abs_tol=1e-5)


def test_rule_convex_optimisation_requires_rules() -> None:
    with pytest.raises(ValueError):
        optimise_rule_weights({"x": 0.0}, [], {"x": 1.0})

