from __future__ import annotations

from compute_god import Bingzi, ObserverEvent, qianli_bingfeng, 冰子, 千里冰封


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


def test_qianli_bingfeng_freezes_when_threshold_reached() -> None:
    observations = [
        (ObserverEvent.STEP, {"temperature": 3.0}),
        (ObserverEvent.EPOCH, {"temperature": -5.0}),
        (ObserverEvent.STEP, {"temperature": -7.5}),
    ]

    frozen = qianli_bingfeng(
        observations,
        metric=lambda state: float(state["temperature"]),
        freeze_point=-1.0,
    )

    assert frozen == {"temperature": -7.5}


def test_qianli_bingfeng_returns_none_when_never_frozen() -> None:
    observations = [
        (ObserverEvent.STEP, {"temperature": 3.0}),
        (ObserverEvent.EPOCH, {"temperature": 1.5}),
    ]

    assert (
        qianli_bingfeng(
            observations,
            metric=lambda state: float(state["temperature"]),
            freeze_point=0.0,
        )
        is None
    )


def test_qianli_bingfeng_has_chinese_alias() -> None:
    assert 千里冰封 is qianli_bingfeng

