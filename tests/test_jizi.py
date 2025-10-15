from __future__ import annotations

import pytest

from compute_god import Jizi, ObserverEvent, ThermalDual, Zijiji, 热对偶, 机子, 子机机, 自机子对偶


def temperature_metric(state):
    return float(state["temperature"])


def test_jizi_tracks_hottest_state() -> None:
    machine = Jizi(metric=temperature_metric, boil_point=50.0)

    machine(ObserverEvent.STEP, {"temperature": 10.0})
    machine(ObserverEvent.EPOCH, {"temperature": 80.0})
    machine(ObserverEvent.STEP, {"temperature": 20.0})

    assert machine.hottest_value == 80.0
    hottest = machine.hottest_state()
    assert hottest == {"temperature": 80.0}

    hottest["temperature"] = -273.0
    assert machine.hottest_state() == {"temperature": 80.0}
    assert machine.is_overheated is True


def test_zijiji_tracks_coldest_state() -> None:
    submachine = Zijiji(metric=temperature_metric, freeze_point=-5.0)

    submachine(ObserverEvent.EPOCH, {"temperature": 4.0})
    submachine(ObserverEvent.STEP, {"temperature": -7.5})
    submachine(ObserverEvent.STEP, {"temperature": 0.0})

    assert submachine.coldest_value == -7.5
    coldest = submachine.coldest_state()
    assert coldest == {"temperature": -7.5}

    coldest["temperature"] = 999.0
    assert submachine.coldest_state() == {"temperature": -7.5}
    assert submachine.is_frozen is True


def test_thermal_dual_produces_gap_and_equilibrium() -> None:
    machine = Jizi(metric=temperature_metric)
    submachine = Zijiji(metric=temperature_metric)

    machine(ObserverEvent.STEP, {"temperature": 12.0})
    machine(ObserverEvent.STEP, {"temperature": 30.0})
    submachine(ObserverEvent.STEP, {"temperature": 18.0})
    submachine(ObserverEvent.STEP, {"temperature": -6.0})

    dual = 热对偶(machine, submachine)
    assert isinstance(dual, ThermalDual)
    assert dual.machine_heat == pytest.approx(30.0)
    assert dual.submachine_cold == pytest.approx(-6.0)
    assert dual.gap == pytest.approx(36.0)
    assert dual.equilibrium == pytest.approx(12.0)


def test_thermal_dual_requires_both_observers() -> None:
    machine = Jizi(metric=temperature_metric)
    submachine = Zijiji(metric=temperature_metric)

    assert 热对偶(machine, submachine) is None

    machine(ObserverEvent.STEP, {"temperature": 1.0})
    assert 热对偶(machine, submachine) is None

    submachine(ObserverEvent.STEP, {"temperature": -2.0})
    assert 热对偶(machine, submachine) is not None


def test_chinese_aliases_match_primary_classes() -> None:
    assert 机子 is Jizi
    assert 子机机 is Zijiji
    assert 自机子对偶 is 热对偶

