from __future__ import annotations

import math

import pytest

from compute_god import ObserverEvent
from compute_god.jiahao import JiahaoMaximumThermalDual
from compute_god.jizi import ThermalDual
from compute_god.miyu import MiyuBond
from compute_god.yihong import (
    YihongMiyuThermalDual,
    yihong_miyu_thermal_dual,
    一弘美羽热对偶,
)


def _bond_with_delta(delta: float | None) -> MiyuBond:
    bond = MiyuBond(target_state={"value": 1.0}, metric=lambda a, b: abs(a["value"] - b["value"]))
    if delta is not None:
        bond(ObserverEvent.STEP, {"value": 1.0 + delta})
    return bond


def _thermal_result(name: str = "aurora") -> JiahaoMaximumThermalDual:
    dual = ThermalDual(machine_heat=120.0, submachine_cold=30.0, gap=90.0, equilibrium=75.0)
    return JiahaoMaximumThermalDual(name=name, dual=dual, happiness=dual.gap)


def test_yihong_miyu_thermal_dual_combines_closeness_and_gap() -> None:
    result = _thermal_result()
    bond = _bond_with_delta(0.2)

    summary = yihong_miyu_thermal_dual(result, bond)

    assert isinstance(summary, YihongMiyuThermalDual)
    assert summary.name == result.name
    assert summary.dual is result.dual
    expected_closeness = math.exp(-0.2)
    assert summary.closeness == pytest.approx(expected_closeness)
    base = result.dual.gap * 0.65 + result.dual.equilibrium * 0.35
    assert summary.harmony == pytest.approx(base * expected_closeness)


def test_yihong_miyu_thermal_dual_defaults_when_bond_has_no_state() -> None:
    result = _thermal_result()
    bond = _bond_with_delta(None)

    summary = yihong_miyu_thermal_dual(result, bond)

    assert summary.closeness is None
    base = result.dual.gap * 0.65 + result.dual.equilibrium * 0.35
    assert summary.harmony == pytest.approx(base)


def test_yihong_miyu_thermal_dual_validates_weight() -> None:
    result = _thermal_result()
    bond = _bond_with_delta(0.1)

    with pytest.raises(ValueError):
        yihong_miyu_thermal_dual(result, bond, equilibrium_weight=1.5)

    with pytest.raises(ValueError):
        yihong_miyu_thermal_dual(result, bond, equilibrium_weight=-0.1)


def test_yihong_miyu_thermal_dual_handles_missing_result() -> None:
    bond = _bond_with_delta(0.1)

    assert yihong_miyu_thermal_dual(None, bond) is None


def test_yihong_miyu_thermal_dual_alias_matches_function() -> None:
    assert 一弘美羽热对偶 is yihong_miyu_thermal_dual


def test_yihong_miyu_thermal_dual_summary_tuple() -> None:
    result = _thermal_result()
    bond = _bond_with_delta(0.0)

    summary = yihong_miyu_thermal_dual(result, bond)
    assert summary is not None
    expected_closeness = 1.0
    expected_harmony = result.dual.gap * 0.65 + result.dual.equilibrium * 0.35
    assert summary.as_tuple() == (
        result.name,
        pytest.approx(result.dual.machine_heat),
        pytest.approx(result.dual.submachine_cold),
        pytest.approx(result.dual.gap),
        pytest.approx(result.dual.equilibrium),
        pytest.approx(expected_closeness),
        pytest.approx(expected_harmony),
    )
