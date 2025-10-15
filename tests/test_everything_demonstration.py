import pytest

from compute_god import (
    EverythingDemonstrationBlueprint,
    physical_everything_demonstration_universe,
    physical_everything_metric,
    run_physical_everything_demonstration,
)


def test_physical_everything_converges_towards_blueprint():
    result = run_physical_everything_demonstration(epsilon=5e-4, max_epoch=140)

    assert result.converged is True

    state = result.universe.state
    for key in ("matter", "energy", "information", "symmetry", "observation"):
        assert state[key] == pytest.approx(1.0, rel=0, abs=5e-3)
    assert state["entropy"] == pytest.approx(0.0, rel=0, abs=5e-3)


def test_physical_everything_respects_initial_state():
    universe = physical_everything_demonstration_universe({"entropy": 0.9, "matter": 0.2})

    assert universe.state["entropy"] == 0.9
    assert universe.state["matter"] == 0.2


def test_physical_everything_metric_counts_all_keys():
    blueprint = EverythingDemonstrationBlueprint().as_state()
    perturbed = dict(blueprint)
    perturbed["energy"] -= 0.1
    perturbed["entropy"] += 0.2

    delta = physical_everything_metric(blueprint, perturbed)
    assert delta == pytest.approx(0.30000000000000004)
