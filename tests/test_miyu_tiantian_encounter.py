import pytest

from compute_god.miyu_tiantian import DEFAULT_STATE, sweet_encounter


def test_sweet_encounter_balances_inputs_and_clamps():
    encounter = sweet_encounter(
        tiantian_state={"emotion": 0.62, "dream_isles": 0.8},
        miyu_state={"emotion": 0.74, "dream_isles": 1.2},
    )

    assert set(encounter.keys()) == set(DEFAULT_STATE.keys())
    assert DEFAULT_STATE["emotion"] < encounter["emotion"] <= 1.0
    assert encounter["dream_isles"] <= 3.0


def test_sweet_encounter_rewards_closeness():
    close = sweet_encounter(
        tiantian_state={"emotion": 0.7},
        miyu_state={"emotion": 0.72},
    )
    distant = sweet_encounter(
        tiantian_state={"emotion": 0.25},
        miyu_state={"emotion": 0.9},
    )

    assert close["emotion"] > distant["emotion"]


def test_sweet_encounter_rejects_unknown_keys():
    with pytest.raises(KeyError):
        sweet_encounter(tiantian_state={"unknown": 0.5})
