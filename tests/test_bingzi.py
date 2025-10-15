from __future__ import annotations

from compute_god import Bingzi, ObserverEvent, 冰子


def temperature_metric(state):
    return float(state["temperature"])


def test_bingzi_records_coldest_state() -> None:
    observer = Bingzi(metric=temperature_metric, freeze_point=-5.0)

    observer(ObserverEvent.STEP, {"temperature": 3.0})
    observer(ObserverEvent.EPOCH, {"temperature": -7.5})
    observer(ObserverEvent.STEP, {"temperature": -2.0})

    assert observer.coldest_value == -7.5
    frozen = observer.coldest_state()
    assert frozen == {"temperature": -7.5}

    # Ensure defensive copies are returned
    frozen["temperature"] = 0.0
    assert observer.coldest_state() == {"temperature": -7.5}

    assert observer.is_frozen is True


def test_bingzi_reset_clears_history() -> None:
    observer = Bingzi(metric=temperature_metric, freeze_point=-1.0)

    observer(ObserverEvent.STEP, {"temperature": -0.5})

    observer.reset()

    assert observer.history == []
    assert observer.coldest_value is None
    assert observer.coldest_state() is None
    assert observer.is_frozen is False


def test_bingzi_has_chinese_alias() -> None:
    assert 冰子 is Bingzi

