"""Blend Jiahao's thermal excitement with Miyu's gentle closeness."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .jiahao import JiahaoMaximumThermalDual
from .jizi import ThermalDual
from .miyu import MiyuBond


@dataclass(frozen=True)
class YihongMiyuThermalDual:
    """Joint summary balancing thermal gap, equilibrium and Miyu's bond.

    The structure keeps the winning :class:`~compute_god.jizi.ThermalDual`
    surfaced by Jiahao together with a normalised closeness derived from
    :class:`~compute_god.miyu.MiyuBond`.  ``harmony`` blends the raw thermal
    excitement with equilibrium comfort, scaled by Miyu's closeness.
    """

    name: str
    dual: ThermalDual
    closeness: Optional[float]
    harmony: float

    def as_tuple(self) -> tuple[str, float, float, float, float, Optional[float], float]:
        closeness = None if self.closeness is None else float(self.closeness)
        dual = self.dual
        return (
            self.name,
            float(dual.machine_heat),
            float(dual.submachine_cold),
            float(dual.gap),
            float(dual.equilibrium),
            closeness,
            float(self.harmony),
        )


def _closeness_from_bond(bond: MiyuBond) -> Optional[float]:
    """Return Miyu's closeness as an exponential decay of the bond delta."""

    if bond.best_delta is None:
        return None
    delta = float(bond.best_delta)
    if delta <= 0.0:
        return 1.0
    return math.exp(-delta)


def yihong_miyu_thermal_dual(
    result: Optional[JiahaoMaximumThermalDual],
    bond: MiyuBond,
    *,
    equilibrium_weight: float = 0.35,
) -> Optional[YihongMiyuThermalDual]:
    """Combine Jiahao's happiest dual with Miyu's bond strength.

    Parameters
    ----------
    result:
        Outcome produced by :func:`compute_god.jiahao.jiahao_max_thermal_dual`.
        ``None`` short-circuits the combination.
    bond:
        Active :class:`~compute_god.miyu.MiyuBond` observer storing Miyu's
        best connection to the shared blueprint.
    equilibrium_weight:
        Value in ``[0, 1]`` determining how much equilibrium contributes to
        the harmony score.  The remainder emphasises the thermal gap.

    Returns
    -------
    Optional[YihongMiyuThermalDual]
        Combined view scaling the weighted thermal score by Miyu's closeness
        whenever the bond has observed a state.
    """

    if result is None:
        return None

    if not 0.0 <= equilibrium_weight <= 1.0:
        raise ValueError("equilibrium_weight must be between 0 and 1 inclusive")

    dual = result.dual
    base = float(dual.gap) * (1.0 - equilibrium_weight) + float(dual.equilibrium) * equilibrium_weight

    closeness = _closeness_from_bond(bond)
    if closeness is None:
        harmony = base
    else:
        harmony = base * closeness

    return YihongMiyuThermalDual(
        name=result.name,
        dual=dual,
        closeness=closeness,
        harmony=harmony,
    )


一弘美羽热对偶 = yihong_miyu_thermal_dual


__all__ = [
    "YihongMiyuThermalDual",
    "yihong_miyu_thermal_dual",
    "一弘美羽热对偶",
]
