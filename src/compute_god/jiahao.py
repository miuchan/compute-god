"""Tools for maximising Jiahao's thermal happiness.

The module extends the playful thermal observers offered by
:mod:`compute_god`.  ``Jiahao`` is imagined as a dreamer chasing the warmest
possible duality between a machine and its submachine.  Given a collection of
``Siqianzi`` observers the helper surfaces the one with the largest thermal
gap.  Should two observers share the same gap the more balanced equilibrium is
preferred – because sustainable warmth keeps Jiahao happiest.

The public surface mirrors the style of the existing helpers: the summary is a
dataclass carrying the winning observer, its :class:`~compute_god.jizi.ThermalDual`
and the quantified happiness.  Convenience aliases written in Chinese let
callers embrace the whimsical naming convention that runs through the project.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .jizi import ThermalDual
from .siqianzi import Siqianzi, SiqianziThermalNetwork


@dataclass(frozen=True)
class JiahaoMaximumThermalDual:
    """Summary describing the happiest thermal dual Jiahao can experience."""

    name: str
    dual: ThermalDual
    happiness: float

    def as_tuple(self) -> tuple[str, float, float, float]:
        """Return a compact representation useful for assertions and logs."""

        return (
            self.name,
            float(self.dual.machine_heat),
            float(self.dual.submachine_cold),
            float(self.happiness),
        )


def _best_node(nodes: Iterable[tuple[str, ThermalDual]]) -> Optional[JiahaoMaximumThermalDual]:
    best_name: Optional[str] = None
    best_dual: Optional[ThermalDual] = None
    best_gap: Optional[float] = None
    best_equilibrium: Optional[float] = None

    for name, dual in nodes:
        gap = float(dual.gap)
        equilibrium = float(dual.equilibrium)
        if (
            best_gap is None
            or gap > best_gap
            or (gap == best_gap and equilibrium > best_equilibrium)
        ):
            best_name = name
            best_dual = dual
            best_gap = gap
            best_equilibrium = equilibrium

    if best_name is None or best_dual is None or best_gap is None:
        return None

    return JiahaoMaximumThermalDual(
        name=best_name,
        dual=best_dual,
        happiness=best_gap,
    )


def jiahao_max_thermal_dual(*machines: Siqianzi) -> Optional[JiahaoMaximumThermalDual]:
    """Return the ``Siqianzi`` observer delivering the largest thermal dual."""

    nodes = []
    for machine in machines:
        dual = machine.dual()
        if dual is None:
            continue
        nodes.append((machine.name, dual))

    return _best_node(nodes)


def jiahao_max_thermal_dual_from_network(
    network: SiqianziThermalNetwork,
) -> Optional[JiahaoMaximumThermalDual]:
    """Return the happiest dual directly from a thermal network."""

    return _best_node((node.name, node.dual) for node in network.nodes)


# Playful aliases so that the poetic API stays consistent.
嘉豪最大热对偶 = jiahao_max_thermal_dual


__all__ = [
    "JiahaoMaximumThermalDual",
    "jiahao_max_thermal_dual",
    "jiahao_max_thermal_dual_from_network",
    "嘉豪最大热对偶",
]

