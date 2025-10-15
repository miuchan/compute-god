from __future__ import annotations

from compute_god import Bingzi, ObserverEvent, Pingzi, PingziRelation, peculiar_asymmetry, 平子


def temperature_metric(state):
    return float(state["temperature"])


def test_pingzi_relation_reports_span_and_equilibrium() -> None:
    cold = Bingzi(metric=temperature_metric, freeze_point=-10.0)
    hot = Pingzi(metric=temperature_metric, boil_point=50.0)

    relation = PingziRelation(bingzi=cold, pingzi=hot)

    assert relation.temperature_span() is None
    assert relation.equilibrium() is None
    assert relation.is_balanced(tolerance=1.0) is False

    cold(ObserverEvent.STEP, {"temperature": -12.0})
    hot(ObserverEvent.STEP, {"temperature": 84.0})

    assert relation.temperature_span() == peculiar_asymmetry(cold, hot)
    assert relation.equilibrium() == 36.0
    assert relation.is_balanced(tolerance=40.0) is True
    assert relation.is_balanced(tolerance=10.0) is False


def test_pingzi_relation_has_chinese_alias() -> None:
    cold = Bingzi(metric=temperature_metric)
    hot = Pingzi(metric=temperature_metric)

    relation = PingziRelation(bingzi=cold, pingzi=hot)

    assert 平子 is PingziRelation
    assert 平子(bingzi=cold, pingzi=hot) == relation
