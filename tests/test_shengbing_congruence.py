from __future__ import annotations

from compute_god import ConceptCongruence, 生病全等于放屁


def test_concept_congruence_records_agreement() -> None:
    congruence = ConceptCongruence("left", "right")
    state = {"left": 1, "right": 1}
    assert congruence(state) is True
    assert congruence.last_result() is True
    assert congruence.last_values() == (1, 1)


def test_concept_congruence_detects_disagreement() -> None:
    congruence = ConceptCongruence("x", "y")
    state = {"x": "foo", "y": "bar"}
    assert congruence(state) is False
    assert congruence.last_result() is False
    disagreements = congruence.disagreements()
    assert len(disagreements) == 1
    assert disagreements[0]["x"] == "foo"
    assert disagreements[0]["y"] == "bar"


def test_shengbing_quandeng_fangpi_enforces_sync() -> None:
    mismatched = {"生病": "痛苦", "放屁": "解脱"}
    assert 生病全等于放屁(mismatched) is False
    repaired = 生病全等于放屁.enforce(mismatched, prefer="right")
    assert repaired["生病"] == "解脱"
    assert repaired["放屁"] == "解脱"

    missing = {"生病": "康复"}
    synchronised = 生病全等于放屁.enforce(missing)
    assert synchronised["生病"] == "康复"
    assert synchronised["放屁"] == "康复"
