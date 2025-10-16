import pytest

from compute_god import (
    EternityEndThermalDual,
    Jizi,
    ObserverEvent,
    Zijiji,
    eternity_end_thermal_dual,
    永恒终结热对偶,
)


def temperature_metric(state):
    return float(state["temperature"])


def test_eternity_end_requires_complete_dual() -> None:
    machine = Jizi(metric=temperature_metric)
    submachine = Zijiji(metric=temperature_metric)

    assert eternity_end_thermal_dual(machine, submachine) is None

    machine(ObserverEvent.STEP, {"temperature": 10.0})
    assert eternity_end_thermal_dual(machine, submachine) is None

    submachine(ObserverEvent.STEP, {"temperature": -5.0})
    assert eternity_end_thermal_dual(machine, submachine) is not None


def test_eternity_end_quantifies_balance() -> None:
    machine = Jizi(metric=temperature_metric)
    submachine = Zijiji(metric=temperature_metric)

    machine(ObserverEvent.STEP, {"temperature": 42.0})
    machine(ObserverEvent.STEP, {"temperature": 90.0})
    submachine(ObserverEvent.STEP, {"temperature": 18.0})
    submachine(ObserverEvent.STEP, {"temperature": -25.0})

    result = eternity_end_thermal_dual(machine, submachine)
    assert isinstance(result, EternityEndThermalDual)

    assert result.dual.gap == pytest.approx(115.0)
    assert result.dual.equilibrium == pytest.approx(32.5)
    assert result.control_pressure == pytest.approx(90.0)
    assert result.freedom_pull == pytest.approx(25.0)
    assert result.tension == pytest.approx(65.0)
    assert result.resolution == "eternity-prevails"

    as_tuple = result.as_tuple()
    assert as_tuple[:4] == pytest.approx((90.0, -25.0, 115.0, 32.5))
    assert as_tuple[4:7] == pytest.approx((90.0, 25.0, 65.0))
    assert as_tuple[7] == "eternity-prevails"


def test_eternity_end_supports_terminal_dominance() -> None:
    machine = Jizi(metric=temperature_metric)
    submachine = Zijiji(metric=temperature_metric)

    machine(ObserverEvent.STEP, {"temperature": 20.0})
    machine(ObserverEvent.STEP, {"temperature": 35.0})
    submachine(ObserverEvent.STEP, {"temperature": -80.0})

    result = eternity_end_thermal_dual(machine, submachine)
    assert result is not None
    assert result.resolution == "end-prevails"
    assert result.freedom_pull == pytest.approx(80.0)
    assert result.tension == pytest.approx(45.0)


def test_eternity_end_rejects_non_positive_tolerance() -> None:
    machine = Jizi(metric=temperature_metric)
    submachine = Zijiji(metric=temperature_metric)

    with pytest.raises(ValueError):
        eternity_end_thermal_dual(machine, submachine, tolerance=0.0)


def test_chinese_alias_matches_primary_function() -> None:
    assert 永恒终结热对偶 is eternity_end_thermal_dual

