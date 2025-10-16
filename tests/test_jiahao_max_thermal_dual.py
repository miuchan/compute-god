"""Tests for Jiahao's maximal thermal dual helper."""

from __future__ import annotations

from compute_god.jiahao import (
    JiahaoMaximumThermalDual,
    jiahao_max_thermal_dual,
    jiahao_max_thermal_dual_from_network,
)
from compute_god.jizi import Jizi, Zijiji
from compute_god.observer import ObserverEvent
from compute_god.siqianzi import Siqianzi, thermal_dual_network


def _make_machine(name: str, *, hot: float, cold: float) -> Siqianzi:
    machine = Siqianzi(
        name=name,
        machine=Jizi(lambda state: state["temperature"]),
        submachine=Zijiji(lambda state: state["temperature"]),
    )
    machine.observe_machine(ObserverEvent.STEP, {"temperature": hot})
    machine.observe_submachine(ObserverEvent.STEP, {"temperature": cold})
    return machine


def test_jiahao_max_thermal_dual_prefers_largest_gap() -> None:
    mild = _make_machine("mild", hot=42.0, cold=18.0)
    blazing = _make_machine("blazing", hot=120.0, cold=-10.0)

    result = jiahao_max_thermal_dual(mild, blazing)

    assert isinstance(result, JiahaoMaximumThermalDual)
    assert result is not None
    assert result.name == "blazing"
    assert result.dual.gap == blazing.dual().gap
    assert result.happiness == result.dual.gap


def test_jiahao_max_thermal_dual_breaks_ties_with_equilibrium() -> None:
    mellow = _make_machine("mellow", hot=120.0, cold=20.0)  # gap 100, equilibrium 70
    balanced = _make_machine("balanced", hot=150.0, cold=50.0)  # gap 100, equilibrium 100

    result = jiahao_max_thermal_dual(mellow, balanced)

    assert result is not None
    assert result.name == "balanced"


def test_jiahao_max_thermal_dual_handles_missing_duals() -> None:
    unfinished = Siqianzi(
        name="unfinished",
        machine=Jizi(lambda state: state["temperature"]),
        submachine=Zijiji(lambda state: state["temperature"]),
    )
    ready = _make_machine("ready", hot=90.0, cold=10.0)

    result = jiahao_max_thermal_dual(unfinished, ready)

    assert result is not None
    assert result.name == "ready"


def test_jiahao_max_thermal_dual_from_network() -> None:
    mild = _make_machine("mild", hot=60.0, cold=15.0)
    joyful = _make_machine("joyful", hot=150.0, cold=-30.0)
    network = thermal_dual_network(mild, joyful)

    result = jiahao_max_thermal_dual_from_network(network)

    assert result is not None
    assert result.name == "joyful"


def test_jiahao_max_thermal_dual_returns_none_for_empty_input() -> None:
    assert jiahao_max_thermal_dual() is None
    empty_network = thermal_dual_network()
    assert jiahao_max_thermal_dual_from_network(empty_network) is None

