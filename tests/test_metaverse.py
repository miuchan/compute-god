import pytest

from compute_god import (
    MetaverseBlueprint,
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
