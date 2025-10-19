"""Tests for the 乐活与乐佛 thermal dual."""

from __future__ import annotations

import pytest

from compute_god.lehuo_lefo import (
    LehuoLefoThermalDual,
    lehuo_lefo_thermal_dual,
    乐活乐佛热对偶,
)
from compute_god.leshan_buddha import build_leshan_buddha
from compute_god.live_and_let_live import LiveAndLetLiveParameters


def test_lehuo_lefo_default_snapshot() -> None:
    result = lehuo_lefo_thermal_dual()

    assert isinstance(result, LehuoLefoThermalDual)
    assert result.dual.machine_heat == pytest.approx(72.1437647552)
    assert result.dual.submachine_cold == pytest.approx(13.2685496553)
    assert result.dual.gap == pytest.approx(58.8752150999)
    assert result.dual.equilibrium == pytest.approx(42.7061572052)
    assert result.compassion_flux == pytest.approx(0.1965367697)
    assert result.drainage_resilience == pytest.approx(0.9567366441)
    assert result.harmony == pytest.approx(49.2518757071)
    assert result.live_state["live_and_let_live_index"] == pytest.approx(0.7214376476)
    assert result.margin_per_surface == pytest.approx(result.dual.submachine_cold)
    assert result.as_tuple() == pytest.approx(
        (
            72.1437647552,
            13.2685496553,
            58.8752150999,
            42.7061572052,
            0.1965367697,
            0.9567366441,
            49.2518757071,
        )
    )


def test_lehuo_lefo_allows_custom_inputs() -> None:
    params = LiveAndLetLiveParameters(adjustment_rate=0.65, empathy_feedback=0.4)
    initial_state = {"self_support": 0.6, "shared_support": 0.4, "trust": 0.35}
    buddha = build_leshan_buddha(scale=1.1)

    result = lehuo_lefo_thermal_dual(
        initial_state,
        params,
        buddha=buddha,
        rainfall_mm_per_hour=84.0,
    )

    assert result.dual.machine_heat == pytest.approx(69.03089793)
    assert result.dual.submachine_cold == pytest.approx(10.0616112854)
    assert result.dual.gap == pytest.approx(58.9692866446)
    assert result.dual.equilibrium == pytest.approx(39.5462546077)
    assert result.compassion_flux == pytest.approx(0.1795543078)
    assert result.drainage_resilience == pytest.approx(0.8778531251)
    assert result.harmony == pytest.approx(41.8165035633)


def test_lehuo_lefo_rejects_negative_rainfall() -> None:
    with pytest.raises(ValueError):
        lehuo_lefo_thermal_dual(rainfall_mm_per_hour=-1.0)


def test_lehuo_lefo_alias_matches_function() -> None:
    assert 乐活乐佛热对偶 is lehuo_lefo_thermal_dual

