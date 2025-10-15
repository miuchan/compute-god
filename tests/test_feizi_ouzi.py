from __future__ import annotations

from typing import MutableMapping

from compute_god import Feizi, Ouzi, 非子, 欧子


State = MutableMapping[str, object]


def _positive(state: State) -> bool:
    return bool(state.get("value", 0) > 0)


def _is_even(state: State) -> bool:
    return bool(state.get("value", 0) % 2 == 0)


def _contains_flag(state: State) -> bool:
    return bool(state.get("flag"))


def test_feizi_negates_predicate_and_records_contradictions() -> None:
    feizi = Feizi(predicate=_positive)

    state = {"value": 3}
    assert feizi(state) is False
    assert feizi.last_result() is False

    cold_state = {"value": -1}
    assert feizi(cold_state) is True

    # Mutating the original mapping must not affect stored snapshots.
    cold_state["value"] = 42

    contradictions = feizi.contradictions()
    assert len(contradictions) == 1
    assert contradictions[0]["value"] == -1

    assert 非子 is Feizi


def test_ouzi_disjunction_and_supporting_indices() -> None:
    ouzi = Ouzi(predicates=(_positive, _is_even, _contains_flag))

    state = {"value": -2}
    assert ouzi(state) is True
    assert ouzi.last_result() is True
    assert ouzi.last_truths() == (False, True, False)
    assert ouzi.supporting_indices() == (1,)

    next_state = {"value": -3, "flag": True}
    assert ouzi(next_state) is True
    assert ouzi.last_truths() == (False, False, True)
    assert ouzi.supporting_indices() == (2,)

    empty_state = {"value": -1, "flag": False}
    assert ouzi(empty_state) is False
    assert ouzi.last_truths() == (False, False, False)
    assert ouzi.supporting_indices() == ()

    assert 欧子 is Ouzi

