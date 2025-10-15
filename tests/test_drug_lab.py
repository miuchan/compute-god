from compute_god import (
    fixpoint,
    drug_lab_metric,
    ideal_drug_lab_universe,
    run_drug_lab,
)


def test_drug_lab_reaches_fixpoint():
    universe = ideal_drug_lab_universe()
    result = fixpoint(universe, metric=drug_lab_metric, epsilon=1e-5, max_epoch=256)

    assert result.converged is True
    state = result.universe.state

    assert state["gradient_norm"] < 1e-3
    assert state["delta_norm"] < 1e-3
    assert state["pipeline_alignment"] > 0.85
    assert state["safety_margin"] > 0.75
    assert state["ethics_harmony"] > 0.75


def test_run_drug_lab_improves_objective():
    initial_state = {
        "infrastructure": 0.2,
        "assay": 0.25,
        "in_vivo": 0.18,
        "safety": 0.4,
        "ethics": 0.5,
        "translation": 0.22,
    }

    baseline_universe = ideal_drug_lab_universe(initial_state, learning_rate=0.2)
    baseline_objective = baseline_universe.state["objective"]
    baseline_gradient = baseline_universe.state["gradient_norm"]

    result = run_drug_lab(initial_state, learning_rate=0.2, epsilon=1e-4, max_epoch=256)
    assert result.result.converged is True

    state = result.state
    assert state["objective"] < baseline_objective
    assert state["gradient_norm"] < baseline_gradient
    assert state["infrastructure"] > initial_state["infrastructure"]
    assert state["ethics"] > 0.75
    assert abs(state["translation"] - 0.87) < 0.1
