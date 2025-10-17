from compute_god import (
    MOMO_KEYS,
    MomoResonanceBlueprint,
    momo_resonance_metric,
    momo_time_universe,
    run_momo_time_harmony,
)
from compute_god.core import fixpoint


def test_momo_universe_reduces_gray_influence():
    universe = momo_time_universe(initial_state={"gray_influence": 0.8})
    result = fixpoint(universe, metric=momo_resonance_metric, epsilon=1e-4, max_epoch=32)

    final_state = result.universe.state
    assert final_state["gray_influence"] < 0.2
    assert final_state["time_harmony"] > 0.6


def test_momo_run_helper_uses_blueprint_customisation():
    blueprint = MomoResonanceBlueprint(gray_dissipation=0.5)
    result = run_momo_time_harmony(
        initial_state={"gray_influence": 0.9, "time_harmony": 0.2},
        blueprint=blueprint,
        epsilon=1e-4,
        max_epoch=24,
    )

    final_state = result.universe.state
    assert final_state["gray_influence"] < 0.05
    assert final_state["time_harmony"] > 0.65


def test_momo_metric_tracks_core_keys():
    previous = {key: 0.1 for key in MOMO_KEYS}
    current = dict(previous)
    current["time_harmony"] = 0.5
    current["gray_influence"] = 0.0

    delta = momo_resonance_metric(previous, current)
    assert delta == 0.5

