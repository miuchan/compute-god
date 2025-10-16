"""Thermal duality capturing the tension between eternity and its end.

The helper mirrors the playful style of :mod:`compute_god.jizi` while grounding
it in the narrative of Isaac Asimov's *The End of Eternity*.  In the story the
organisation known as "Eternity" safeguards civilisation by dampening risk,
thereby suppressing the very uncertainty that fuels exploration.  The module
turns that metaphor into a compact structure: the hottest value witnessed by a
"machine" stands in for the stabilising pressure of Eternity, while the coldest
value recorded by a "submachine" represents the liberating chill that ushers in
an end to control.  Their :class:`~compute_god.jizi.ThermalDual` becomes the
bridge between the two forces.

``eternity_end_thermal_dual`` builds on the base dual to extract higher-level
quantities describing how dominant each force is and how much unresolved
tension remains.  Callers can use the resulting dataclass for analytics, quick
assertions or even to craft narrative summaries highlighting whether stability
or freedom is currently prevailing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .jizi import Jizi, ThermalDual, Zijiji, thermal_dual


@dataclass(frozen=True)
class EternityEndThermalDual:
    """Narrative summary balancing Eternity's control with terminal freedom.

    Parameters
    ----------
    dual:
        Base :class:`~compute_god.jizi.ThermalDual` produced by pairing the hot
        ``machine`` with the cold ``submachine``.
    control_pressure:
        Non-negative measure quantifying how forcefully Eternity holds on to
        stability.  It corresponds to the hottest temperature witnessed so far
        but clipped at zero to guard against pathological inputs.
    freedom_pull:
        Non-negative indicator estimating how strongly the end of control pulls
        the system towards exploration.  It uses the magnitude of the coldest
        value, again clipped at zero.
    tension:
        Absolute difference between ``control_pressure`` and ``freedom_pull``.
        Larger values signal a lopsided narrative where one force dominates the
        other.
    resolution:
        Human-friendly tag describing which side currently prevails.  The value
        is one of ``"eternity-prevails"``, ``"end-prevails"`` or ``"balanced"``.
    """

    dual: ThermalDual
    control_pressure: float
    freedom_pull: float
    tension: float
    resolution: str

    def as_tuple(self) -> tuple[float, float, float, float, float, float, float, str]:
        """Return a compact tuple useful for assertions and logs."""

        return (
            float(self.dual.machine_heat),
            float(self.dual.submachine_cold),
            float(self.dual.gap),
            float(self.dual.equilibrium),
            float(self.control_pressure),
            float(self.freedom_pull),
            float(self.tension),
            self.resolution,
        )


def _classify_resolution(balance: float, *, tolerance: float) -> str:
    if balance > tolerance:
        return "eternity-prevails"
    if balance < -tolerance:
        return "end-prevails"
    return "balanced"


def eternity_end_thermal_dual(
    machine: Jizi,
    submachine: Zijiji,
    *,
    tolerance: float = 1e-6,
) -> Optional[EternityEndThermalDual]:
    """Lift :func:`compute_god.jizi.thermal_dual` into an eternal-versus-end view.

    The function first computes the base thermal dual between ``machine`` and
    ``submachine``.  When both observers have recorded at least one state the
    helper measures how far the hottest and coldest values pull in opposite
    directions.  The ``resolution`` tag highlights which side dominates within
    ``tolerance`` while ``tension`` quantifies the magnitude of that imbalance.
    """

    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    dual = thermal_dual(machine, submachine)
    if dual is None:
        return None

    control_pressure = max(0.0, float(dual.machine_heat))
    freedom_pull = max(0.0, float(-dual.submachine_cold))
    balance = control_pressure - freedom_pull
    tension = abs(balance)
    resolution = _classify_resolution(balance, tolerance=tolerance)

    return EternityEndThermalDual(
        dual=dual,
        control_pressure=control_pressure,
        freedom_pull=freedom_pull,
        tension=tension,
        resolution=resolution,
    )


永恒终结热对偶 = eternity_end_thermal_dual


__all__ = [
    "EternityEndThermalDual",
    "eternity_end_thermal_dual",
    "永恒终结热对偶",
]

