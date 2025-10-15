from __future__ import annotations

from compute_god import (
    Bingzi,
    Jizi,
    ObserverEvent,
    Pingzi,
    Sanzi,
    SanziOverview,
    Weizi,
    Zijiji,
    peculiar_asymmetry,
    thermal_dual,
    三子,
    维子,
)


def temperature_metric(state):
    return float(state["temperature"])


def make_observers():
    cold = Bingzi(metric=temperature_metric, freeze_point=-10.0)
    hot = Pingzi(metric=temperature_metric, boil_point=50.0)
    machine = Jizi(metric=temperature_metric, boil_point=60.0)
    submachine = Zijiji(metric=temperature_metric, freeze_point=-20.0)
    return cold, hot, machine, submachine


def record_samples(cold: Bingzi, hot: Pingzi, machine: Jizi, submachine: Zijiji) -> None:
    cold(ObserverEvent.STEP, {"temperature": -12.0})
    cold(ObserverEvent.EPOCH, {"temperature": -3.0})
    hot(ObserverEvent.EPOCH, {"temperature": 75.0})
    hot(ObserverEvent.STEP, {"temperature": 63.0})
    machine(ObserverEvent.STEP, {"temperature": 70.0})
    machine(ObserverEvent.EPOCH, {"temperature": 65.0})
    submachine(ObserverEvent.STEP, {"temperature": -21.0})
    submachine(ObserverEvent.EPOCH, {"temperature": -10.0})


def test_sanzi_reports_span_equilibrium_and_overview() -> None:
    cold, hot, machine, submachine = make_observers()
    triad = Sanzi(bingzi=cold, pingzi=hot, jizi=machine)

    assert triad.temperature_span() is None
    assert triad.equilibrium() is None
    assert triad.machine_heat() is None
    assert triad.overview() is None

    record_samples(cold, hot, machine, submachine)

    expected_span = peculiar_asymmetry(cold, hot)
    assert expected_span is not None
    assert triad.temperature_span() == expected_span

    expected_equilibrium = (float(cold.coldest_value) + float(hot.hottest_value)) / 2.0
    assert triad.equilibrium() == expected_equilibrium
    assert triad.machine_heat() == float(machine.hottest_value)

    overview = triad.overview()
    assert isinstance(overview, SanziOverview)
    assert overview == SanziOverview(
        coldest=float(cold.coldest_value),
        hottest=float(hot.hottest_value),
        span=expected_span,
        equilibrium=expected_equilibrium,
        machine_heat=float(machine.hottest_value),
    )


def test_weizi_bridges_sanzi_and_zijiji() -> None:
    cold, hot, machine, submachine = make_observers()
    triad = Sanzi(bingzi=cold, pingzi=hot, jizi=machine)
    bridge = Weizi(sanzi=triad, zijiji=submachine)

    assert bridge.dual() is None
    assert bridge.equilibrium() is None
    assert bridge.is_balanced(tolerance=1.0) is False

    record_samples(cold, hot, machine, submachine)

    expected_dual = thermal_dual(machine, submachine)
    assert expected_dual is not None
    assert bridge.dual() == expected_dual
    assert bridge.equilibrium() == expected_dual.equilibrium
    assert bridge.is_balanced(tolerance=expected_dual.gap + 1.0) is True
    assert bridge.is_balanced(tolerance=expected_dual.gap - 1.0) is False


def test_sanzi_and_weizi_have_chinese_aliases() -> None:
    cold, hot, machine, submachine = make_observers()

    assert 三子 is Sanzi
    assert 维子 is Weizi

    assert 三子(bingzi=cold, pingzi=hot, jizi=machine) == Sanzi(
        bingzi=cold, pingzi=hot, jizi=machine
    )

    triad = Sanzi(bingzi=cold, pingzi=hot, jizi=machine)
    assert 维子(sanzi=triad, zijiji=submachine) == Weizi(sanzi=triad, zijiji=submachine)

