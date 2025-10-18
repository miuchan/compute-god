import pytest

from compute_god.hormone_lab import (
    DEFAULT_STATE,
    hormone_lab_metric,
    hormone_lab_universe,
    run_hormone_lab,
)


def test_hormone_lab_universe_initialises_metrics() -> None:
    universe = hormone_lab_universe()
    state = universe.state

    assert set(DEFAULT_STATE).issubset(state.keys())
    assert 0.0 <= state["synchrony_score"] <= 1.0
    assert 0.0 <= state["metabolic_balance"] <= 1.0
    assert 0.0 <= state["resilience_band"] <= 1.0
    assert 0.0 <= state["bonding_field"] <= 1.0


def test_run_hormone_lab_improves_synchrony() -> None:
    initial_state = {
        "circadian_amplitude": 0.45,
        "cortisol_balance": 0.38,
        "thyroid_flux": 0.42,
        "insulin_resilience": 0.41,
        "oxytocin_wave": 0.44,
    }

    result = run_hormone_lab(initial_state, micro_adjust=0.25, epsilon=1e-6, max_epoch=160)
    final_state = result.state

    assert final_state["synchrony_score"] > 0.6
    assert final_state["gradient_norm"] < 0.05
    assert final_state["descent"] >= 0.0


def test_hormone_lab_metric_is_symmetric() -> None:
    universe = hormone_lab_universe()
    baseline = dict(universe.state)
    perturbed = dict(baseline)
    perturbed["circadian_amplitude"] += 0.05
    perturbed["objective"] = baseline["objective"] + 0.2

    forward = hormone_lab_metric(baseline, perturbed)
    backward = hormone_lab_metric(perturbed, baseline)

    assert forward == pytest.approx(backward, rel=1e-7)
    assert forward > 0.0
