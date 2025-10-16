from compute_god import MiyuBond
from compute_god.mihoyo import (
    MihoyoStudioBlueprint,
    MiyuCreativeProfile,
    bond_miyu_with_mihoyo,
    mihoyo_alignment_metric,
    measure_mihoyo_fengshui,
    run_miyu_join_mihoyo,
)


def test_miyu_join_mihoyo_strengthens_alignment():
    blueprint = MihoyoStudioBlueprint()
    profile = MiyuCreativeProfile()
    initial_delta = mihoyo_alignment_metric(profile.as_state(), blueprint.as_state())
    standalone_bond = bond_miyu_with_mihoyo()
    assert isinstance(standalone_bond, MiyuBond)
    assert standalone_bond.metric(profile.as_state(), blueprint.as_state()) == initial_delta

    outcome = run_miyu_join_mihoyo()

    assert outcome.fixpoint.converged is True
    assert outcome.fixpoint.epochs > 0
    assert isinstance(outcome.bond, MiyuBond)
    assert outcome.bond.best_delta is not None
    assert outcome.bond.best_delta < initial_delta

    strongest = outcome.bond.strongest_state()
    assert strongest is not None
    for key, target_value in blueprint.as_state().items():
        assert abs(strongest[key] - target_value) < 0.15


def test_custom_blueprint_and_profile_improve_alignment():
    blueprint = MihoyoStudioBlueprint(
        innovation=0.95,
        artistry=0.93,
        community=0.90,
        technology=0.94,
        collaboration=0.96,
        resonance=0.94,
    )
    profile = MiyuCreativeProfile(
        innovation=0.52,
        artistry=0.57,
        community=0.50,
        technology=0.55,
        collaboration=0.49,
        resonance=0.46,
    )

    before = mihoyo_alignment_metric(profile.as_state(), blueprint.as_state())
    outcome = run_miyu_join_mihoyo(profile=profile, blueprint=blueprint)

    assert outcome.fixpoint.converged is True
    strongest = outcome.bond.strongest_state()
    assert strongest is not None
    after = mihoyo_alignment_metric(strongest, blueprint.as_state())
    assert after < before


def test_measure_mihoyo_fengshui_tracks_harmony():
    blueprint = MihoyoStudioBlueprint()
    empty_state = {key: 0.0 for key in blueprint.as_state()}

    baseline = measure_mihoyo_fengshui(empty_state, blueprint)
    assert 0.0 <= baseline < 1.0

    perfect = measure_mihoyo_fengshui(blueprint.as_state(), blueprint)
    assert perfect == 1.0

    outcome = run_miyu_join_mihoyo(blueprint=blueprint)
    strongest = outcome.bond.strongest_state()
    assert strongest is not None
    assert measure_mihoyo_fengshui(strongest, blueprint) > baseline
