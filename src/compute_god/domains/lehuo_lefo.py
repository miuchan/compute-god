"""Thermal duality weaving together 乐活 (live-and-let-live) and 乐佛.

This module braids the socio-ecological dynamics from
:mod:`compute_god.live_and_let_live` with the hydrological steadiness of the
Leshan Giant Buddha model (:mod:`compute_god.leshan_buddha`).  It interprets the
``live_and_let_live_index`` as a source of communal warmth while the Buddha's
drainage network supplies a reservoir of cooling margin.  The two signals are
combined into a :class:`~compute_god.jizi.ThermalDual` accompanied by a handful
of harmony metrics so that other catalogues can reference the liaison without
having to repeat the arithmetic."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .jizi import ThermalDual
from .leshan_buddha import LeshanBuddhaModel, build_leshan_buddha
from .live_and_let_live import LiveAndLetLiveParameters, live_and_let_live_step


def _freeze_state(state: Mapping[str, float]) -> Mapping[str, float]:
    """Return an immutable snapshot of ``state`` with float values."""

    return MappingProxyType({key: float(value) for key, value in state.items()})


@dataclass(frozen=True)
class LehuoLefoThermalDual:
    """Summary of the 乐活 and 乐佛 thermal resonance."""

    live_state: Mapping[str, float]
    rainfall_mm_per_hour: float
    margin_per_surface: float
    dual: ThermalDual
    compassion_flux: float
    drainage_resilience: float
    harmony: float

    def as_tuple(self) -> tuple[float, float, float, float, float, float, float]:
        """Return a serialisable view combining the thermal and harmony metrics."""

        dual = self.dual
        return (
            float(dual.machine_heat),
            float(dual.submachine_cold),
            float(dual.gap),
            float(dual.equilibrium),
            float(self.compassion_flux),
            float(self.drainage_resilience),
            float(self.harmony),
        )


def lehuo_lefo_thermal_dual(
    state: Mapping[str, float] | None = None,
    params: LiveAndLetLiveParameters | None = None,
    *,
    buddha: LeshanBuddhaModel | None = None,
    rainfall_mm_per_hour: float = 36.0,
) -> LehuoLefoThermalDual:
    """Combine 乐活 dynamics with 乐佛 hydrology into a thermal dual."""

    if rainfall_mm_per_hour < 0:
        raise ValueError("rainfall_mm_per_hour must be non-negative")

    model = buddha or build_leshan_buddha()
    live_state = _freeze_state(live_and_let_live_step(state, params))

    machine_heat = live_state["live_and_let_live_index"] * 100.0
    margin = model.drainage_margin(rainfall_mm_per_hour)
    surface_area = model.total_surface_area()
    submachine_cold = margin / surface_area
    gap = machine_heat - submachine_cold
    equilibrium = (machine_heat + submachine_cold) / 2.0
    dual = ThermalDual(
        machine_heat=machine_heat,
        submachine_cold=submachine_cold,
        gap=gap,
        equilibrium=equilibrium,
    )

    compassion_flux = live_state["shared_support"] * live_state["trust"]
    drainage_resilience = margin / model.drainage_capacity()
    harmony = equilibrium * (compassion_flux + max(0.0, drainage_resilience))

    return LehuoLefoThermalDual(
        live_state=live_state,
        rainfall_mm_per_hour=float(rainfall_mm_per_hour),
        margin_per_surface=submachine_cold,
        dual=dual,
        compassion_flux=compassion_flux,
        drainage_resilience=drainage_resilience,
        harmony=harmony,
    )


乐活乐佛热对偶 = lehuo_lefo_thermal_dual


__all__ = [
    "LehuoLefoThermalDual",
    "lehuo_lefo_thermal_dual",
    "乐活乐佛热对偶",
]

