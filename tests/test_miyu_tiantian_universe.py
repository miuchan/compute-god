from compute_god import fixpoint
from compute_god.miyu_tiantian import (
    DEFAULT_STATE,
    MiyuTiantianBlueprint,
    bond_miyu_tiantian,
    miyu_tiantian_metric,
    miyu_tiantian_universe,
    run_miyu_tiantian_universe,
)


def test_miyu_tiantian_universe_converges_and_blooms():
    result = run_miyu_tiantian_universe()

    assert result.converged is True
    assert result.epochs > 0

    final_state = result.universe.state
    assert final_state["memory_bloom"] >= DEFAULT_STATE["memory_bloom"]
    assert final_state["dream_isles"] >= DEFAULT_STATE["dream_isles"]
    assert 0.0 <= final_state["emotion"] <= 1.0


def test_miyu_tiantian_bond_tracks_progress_towards_blueprint():
    blueprint = MiyuTiantianBlueprint(
        emotion=0.88,
        memory_bloom=0.82,
        collaboration=0.78,
        dream_isles=2.4,
        orbit_rhythm=0.8,
        resonance=0.81,
        diary=0.75,
    )

    bond = bond_miyu_tiantian(blueprint)

    initial_state = dict(DEFAULT_STATE)
    initial_delta = bond.metric(initial_state, blueprint.as_state())

    universe = miyu_tiantian_universe(initial_state=initial_state, observers=[bond])
    outcome = fixpoint(
        universe,
        metric=miyu_tiantian_metric,
        epsilon=1e-5,
        max_epoch=256,
    )

    assert outcome.converged is True
    assert bond.best_delta is not None
    assert bond.best_delta <= initial_delta
    assert bond.strongest_state() is not None
