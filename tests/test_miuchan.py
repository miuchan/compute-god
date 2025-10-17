import pytest

from compute_god.miuchan import (
    DEFAULT_BLUEPRINT,
    MiuchanBlueprint,
    bond_miuchan,
    miuchan_metric,
    miuchan_universe,
    run_miuchan_universe,
)


def _approx_equal(left: float, right: float, *, epsilon: float = 1e-3) -> bool:
    return abs(left - right) <= epsilon


def test_miuchan_universe_converges_to_blueprint():
    blueprint = MiuchanBlueprint(affection=0.94, harmony=0.91, sincerity=0.92)

    result = run_miuchan_universe(blueprint=blueprint, epsilon=1e-4, max_epoch=128)

    assert result.converged is True

    final_state = result.universe.state
    target_state = blueprint.as_state()

    assert final_state["consistency"] >= 0.995
    for key, target_value in target_state.items():
        assert _approx_equal(float(final_state[key]), target_value, epsilon=5e-3)


def test_bond_miuchan_tracks_best_state():
    blueprint = MiuchanBlueprint(affection=0.89, harmony=0.9, sincerity=0.93)
    bond = bond_miuchan(blueprint)

    result = run_miuchan_universe(
        initial_state={"affection": 0.2, "harmony": 0.25, "sincerity": 0.3},
        blueprint=blueprint,
        observers=[bond],
        epsilon=1e-4,
        max_epoch=160,
    )

    assert result.converged is True
    assert bond.best_state is not None
    assert bond.best_delta is not None
    assert bond.is_strong(0.05)

    best = bond.strongest_state()
    assert best is not None
    target_state = blueprint.as_state()
    for key, value in target_state.items():
        assert _approx_equal(float(best[key]), value, epsilon=5e-3)


def test_miuchan_metric_counts_coordinate_changes():
    previous = {"affection": 0.2, "harmony": 0.5, "sincerity": 0.7, "consistency": 0.9}
    current = {"affection": 0.25, "harmony": 0.5, "sincerity": 0.65, "consistency": 0.92}

    assert miuchan_metric(previous, current) == pytest.approx(0.12)


def test_miuchan_universe_rejects_unknown_keys():
    with pytest.raises(KeyError, match="unknown miuchan state key"):
        miuchan_universe(initial_state={"unknown": 0.4})


def test_default_blueprint_integrates_with_metric():
    bond = bond_miuchan()
    result = run_miuchan_universe(observers=[bond])

    assert result.converged is True
    assert bond.best_state is not None
    target = DEFAULT_BLUEPRINT.as_state()
    for key, value in target.items():
        assert _approx_equal(float(result.universe.state[key]), value, epsilon=5e-3)
