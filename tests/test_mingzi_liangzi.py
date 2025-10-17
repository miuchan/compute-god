from compute_god import Liangzi, Mingzi, ObserverEvent, 亮子, 明子


def brightness_metric(state):
    return float(state["brightness"])


def _make_state(value: float) -> dict[str, float]:
    return {"brightness": value}


def test_mingzi_tracks_dimmest_state() -> None:
    observer = Mingzi(metric=brightness_metric, dawn_point=-5.0)

    observer(ObserverEvent.STEP, _make_state(1.5))
    observer(ObserverEvent.EPOCH, _make_state(-12.0))
    observer(ObserverEvent.STEP, _make_state(3.0))

    assert observer.dimmest_value == -12.0
    snapshot = observer.dimmest_state()
    assert snapshot == {"brightness": -12.0}

    snapshot["brightness"] = 42.0
    assert observer.dimmest_state() == {"brightness": -12.0}

    assert observer.is_dim is True


def test_mingzi_reset_clears_history() -> None:
    observer = Mingzi(metric=brightness_metric, dawn_point=-1.0)

    observer(ObserverEvent.STEP, _make_state(0.5))

    observer.reset()

    assert observer.history == []
    assert observer.dimmest_value is None
    assert observer.dimmest_state() is None
    assert observer.is_dim is False


def test_liangzi_tracks_brightest_state() -> None:
    observer = Liangzi(metric=brightness_metric, shine_point=80.0)

    observer(ObserverEvent.STEP, _make_state(42.0))
    observer(ObserverEvent.EPOCH, _make_state(120.0))
    observer(ObserverEvent.STEP, _make_state(55.0))

    assert observer.brightest_value == 120.0
    snapshot = observer.brightest_state()
    assert snapshot == {"brightness": 120.0}

    snapshot["brightness"] = 0.0
    assert observer.brightest_state() == {"brightness": 120.0}

    assert observer.is_radiant is True


def test_liangzi_reset_clears_history() -> None:
    observer = Liangzi(metric=brightness_metric, shine_point=50.0)

    observer(ObserverEvent.STEP, _make_state(10.0))

    observer.reset()

    assert observer.history == []
    assert observer.brightest_value is None
    assert observer.brightest_state() is None
    assert observer.is_radiant is False


def test_mingzi_liangzi_have_chinese_aliases() -> None:
    assert 明子 is Mingzi
    assert 亮子 is Liangzi

    ming = 明子(metric=brightness_metric)
    liang = 亮子(metric=brightness_metric)

    assert isinstance(ming, Mingzi)
    assert isinstance(liang, Liangzi)
