from __future__ import annotations

from compute_god import (
    Bingzi,
    ObserverEvent,
    Pingzi,
    peculiar_asymmetry,
    冰子,
    瓶子,
)


def temperature_metric(state):
    return float(state["temperature"])


def test_pingzi_records_hottest_state() -> None:
    observer = Pingzi(metric=temperature_metric, boil_point=42.0)

    observer(ObserverEvent.STEP, {"temperature": 21.0})
    observer(ObserverEvent.EPOCH, {"temperature": 63.5})
    observer(ObserverEvent.STEP, {"temperature": 30.0})

    assert observer.hottest_value == 63.5
    overheated = observer.hottest_state()
    assert overheated == {"temperature": 63.5}

    overheated["temperature"] = 0.0
    assert observer.hottest_state() == {"temperature": 63.5}

    assert observer.is_overheated is True


def test_pingzi_reset_clears_history() -> None:
    observer = Pingzi(metric=temperature_metric, boil_point=10.0)

    observer(ObserverEvent.STEP, {"temperature": 5.0})

    observer.reset()

    assert observer.history == []
    assert observer.hottest_value is None
    assert observer.hottest_state() is None
    assert observer.is_overheated is False


def test_peculiar_asymmetry_between_bingzi_and_pingzi() -> None:
    cold = Bingzi(metric=temperature_metric, freeze_point=-10.0)
    hot = Pingzi(metric=temperature_metric, boil_point=50.0)

    cold(ObserverEvent.STEP, {"temperature": -12.0})
    hot(ObserverEvent.STEP, {"temperature": 75.0})

    assert peculiar_asymmetry(cold, hot) == 87.0


def test_pingzi_has_chinese_alias() -> None:
    assert 冰子 is Bingzi
    assert 瓶子 is Pingzi


def test_peculiar_asymmetry_requires_both_observers() -> None:
    cold = Bingzi(metric=temperature_metric)
    hot = Pingzi(metric=temperature_metric)

    assert peculiar_asymmetry(cold, hot) is None

    cold(ObserverEvent.STEP, {"temperature": -1.0})
    assert peculiar_asymmetry(cold, hot) is None

    hot(ObserverEvent.STEP, {"temperature": 5.0})
    assert peculiar_asymmetry(cold, hot) == 6.0
