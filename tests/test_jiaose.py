from __future__ import annotations

import math

import pytest

from compute_god import ChromaticDual, Jiaozi, ObserverEvent, Sezi, chromatic_dual, 角子, 色子, 色角对偶


def angle_metric(state):
    return float(state["angle"])


def colour_metric(state):
    return state["rgb"]


def test_jiaozi_tracks_sharpest_angle() -> None:
    observer = Jiaozi(metric=angle_metric, reference=45.0, period=360.0)

    observer(ObserverEvent.STEP, {"angle": 10.0})
    observer(ObserverEvent.STEP, {"angle": 50.0})
    observer(ObserverEvent.EPOCH, {"angle": 405.0})

    assert observer.sharpest_delta == pytest.approx(0.0)
    sharpest = observer.sharpest_state()
    assert sharpest == {"angle": 405.0}
    sharpest["angle"] = -999.0
    assert observer.sharpest_state() == {"angle": 405.0}
    assert observer.is_pointed(tolerance=5.0) is True


def test_sezi_tracks_most_vibrant_colour() -> None:
    observer = Sezi(metric=colour_metric)

    observer(ObserverEvent.STEP, {"rgb": (0.2, 0.1, 0.3)})
    observer(ObserverEvent.EPOCH, {"rgb": (0.9, 0.1, 0.2)})

    expected_vibrancy = math.sqrt(0.9**2 + 0.1**2 + 0.2**2)
    assert observer.most_vibrant_value == pytest.approx(expected_vibrancy)
    vibrant = observer.most_vibrant_state()
    assert vibrant == {"rgb": (0.9, 0.1, 0.2)}
    assert observer.most_vibrant_vector() == (0.9, 0.1, 0.2)
    vibrant["rgb"] = (0.0, 0.0, 0.0)
    assert observer.most_vibrant_state() == {"rgb": (0.9, 0.1, 0.2)}
    assert observer.is_vibrant(threshold=0.5) is True


def test_chromatic_dual_requires_both_observers() -> None:
    jiao = Jiaozi(metric=angle_metric)
    se = Sezi(metric=colour_metric)

    assert chromatic_dual(jiao, se) is None

    jiao(ObserverEvent.STEP, {"angle": 10.0})
    assert chromatic_dual(jiao, se) is None

    se(ObserverEvent.STEP, {"rgb": (0.1, 0.2, 0.3)})
    dual = chromatic_dual(jiao, se)

    assert isinstance(dual, ChromaticDual)
    assert dual.angle_delta == pytest.approx(jiao.sharpest_delta)
    assert dual.vibrancy == pytest.approx(se.most_vibrant_value)
    assert dual.harmony == pytest.approx(dual.vibrancy - dual.angle_delta)
    assert dual.complementary_angle == pytest.approx(180.0)


def test_chinese_aliases_match_primary_classes() -> None:
    assert 角子 is Jiaozi
    assert 色子 is Sezi
    assert 色角对偶 is chromatic_dual
