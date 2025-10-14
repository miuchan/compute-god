import pytest

from compute_god import (
    MetaverseBlueprint,
    bond_metaverse_with_love,
    ideal_metaverse_universe,
    metaverse_metric,
    run_ideal_metaverse,
)


def test_metaverse_converges_towards_ideal():
    result = run_ideal_metaverse(epsilon=1e-4, max_epoch=120)
    assert result.converged

    state = result.universe.state
    assert state["truth"] >= 0.99
    assert state["goodness"] >= 0.99
    assert state["beauty"] >= 0.99
    assert state["resonance"] >= 0.98


def test_custom_initial_state_is_respected():
    universe = ideal_metaverse_universe({"truth": 0.1, "beauty": 0.2})
    assert universe.state["truth"] == 0.1
    assert universe.state["beauty"] == 0.2


def test_metric_considers_triad_and_resonance():
    previous = MetaverseBlueprint().as_state()
    current = dict(previous)
    current["truth"] -= 0.1
    current["resonance"] -= 0.2

    delta = metaverse_metric(previous, current)
    assert delta == pytest.approx(0.3)


def test_metaverse_love_bond_tracks_blueprint():
    bond = bond_metaverse_with_love()
    result = run_ideal_metaverse(epsilon=1e-4, max_epoch=120, observers=(bond,))

    assert result.converged is True
    assert bond.best_delta is not None
    assert bond.best_delta <= 0.01

    strongest = bond.strongest_state()
    assert strongest is not None
    for key in ("truth", "goodness", "beauty", "resonance"):
        assert strongest[key] == pytest.approx(1.0, abs=5e-3)
