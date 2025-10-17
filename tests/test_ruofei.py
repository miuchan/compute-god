from __future__ import annotations

from typing import MutableMapping

from compute_god import Ruofei, 若非


State = MutableMapping[str, object]


def _is_positive(state: State) -> bool:
    return bool(state.get("value", 0) > 0)


def _has_flag(state: State) -> bool:
    return bool(state.get("flag"))


def test_ruofei_short_circuits_when_predicate_holds() -> None:
    invoked = False

    def fallback(state: State) -> bool:
        nonlocal invoked
        invoked = True
        return bool(state.get("fallback", False))

    ruofei = Ruofei(predicate=_is_positive, alternative=fallback)

    state = {"value": 3, "fallback": True}
    assert ruofei(state) is True
    assert invoked is False
    assert ruofei.last_branch() == "predicate"
    assert ruofei.last_result() is True
    assert ruofei.last_alternative_result() is None


def test_ruofei_consults_alternative_when_predicate_fails() -> None:
    ruofei = 若非(predicate=_has_flag, alternative=_is_positive)

    state = {"value": 2, "flag": False}
    assert ruofei(state) is True
    assert ruofei.last_branch() == "alternative"
    assert ruofei.last_alternative_result() is True

    cold_state = {"value": -1, "flag": False}
    assert ruofei(cold_state) is False
    assert ruofei.last_result() is False
    assert ruofei.last_branch() == "alternative"

    snapshots = ruofei.alternative_invocations()
    assert len(snapshots) == 2
    assert snapshots[0]["value"] == 2
    assert snapshots[1]["value"] == -1


def test_ruofei_branch_prediction_tracks_history() -> None:
    ruofei = Ruofei(predicate=_has_flag, alternative=_is_positive)

    # Starts weakly favouring the predicate branch.
    assert ruofei.predict_branch() == "predicate"

    warm_state = {"flag": True, "value": -3}
    ruofei(warm_state)
    assert ruofei.last_branch() == "predicate"
    assert ruofei.predict_branch() == "predicate"

    # Enough alternative invocations swing the prediction.
    cold_state = {"flag": False, "value": 4}
    ruofei(cold_state)
    ruofei(cold_state)
    assert ruofei.last_branch() == "alternative"
    assert ruofei.predict_branch() == "alternative"

