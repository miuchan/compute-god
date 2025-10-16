"""Thermal dual network utilities affectionately nicknamed ``死前子``.

The module builds on the existing hot and cold observers offered by
``compute_god``.  ``Siqianzi`` (死前子) combines :class:`compute_god.jizi.Jizi`
with :class:`compute_god.jizi.Zijiji` so that callers can drive both observers
under a single façade.  Once both sides have recorded at least one temperature
the helper can surface their :class:`compute_god.jizi.ThermalDual` summary.

To reason about multiple "pre-mortem" machines at once the module exposes
``thermal_dual_network``.  The function gathers all available thermal duals and
connects them into a tiny undirected network.  Each edge captures how the gap
and equilibrium differ between two machines, enabling coarse-grained analysis
without resorting to heavy graph libraries.  The resulting
:class:`SiqianziThermalNetwork` also offers a convenience ``adjacency`` view so
experiments can quickly inspect the neighbourhood of each node.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, MutableMapping, Optional, Tuple

from .jizi import Jizi, ThermalDual, Zijiji, thermal_dual
from .core import ObserverEvent

State = MutableMapping[str, object]


@dataclass
class Siqianzi:
    """Convenience façade combining ``Jizi`` and ``Zijiji``.

    Parameters
    ----------
    name:
        Identifier used when building networks.  The name is preserved on the
        resulting nodes so downstream code can keep track of the original
        machines without additional bookkeeping.
    machine:
        Hot-observing instance of :class:`Jizi`.
    submachine:
        Cold-observing instance of :class:`Zijiji`.
    """

    name: str
    machine: Jizi
    submachine: Zijiji

    def observe_machine(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Forward ``state`` to the hot observer."""

        self.machine(event, state, **metadata)

    def observe_submachine(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Forward ``state`` to the cold observer."""

        self.submachine(event, state, **metadata)

    def observe(self, event: ObserverEvent, state: State, /, **metadata: object) -> None:
        """Send ``state`` to both observers in lockstep."""

        self.observe_machine(event, state, **metadata)
        self.observe_submachine(event, state, **metadata)

    def reset(self) -> None:
        """Clear the history of both observers."""

        self.machine.reset()
        self.submachine.reset()

    def dual(self) -> Optional[ThermalDual]:
        """Return the thermal dual for the combined observers if available."""

        return thermal_dual(self.machine, self.submachine)


@dataclass(frozen=True)
class SiqianziDualNode:
    """Node describing a ``Siqianzi`` instance together with its thermal dual."""

    name: str
    dual: ThermalDual


@dataclass(frozen=True)
class SiqianziDualEdge:
    """Edge capturing the thermal delta between two ``Siqianzi`` nodes."""

    source: str
    target: str
    gap_difference: float
    equilibrium_difference: float
    average_gap: float
    average_equilibrium: float

    def as_tuple(self) -> Tuple[str, str, float, float]:
        """Return a compact representation useful for quick assertions."""

        return (self.source, self.target, self.gap_difference, self.equilibrium_difference)


@dataclass(frozen=True)
class SiqianziThermalNetwork:
    """Tiny undirected network formed by ``Siqianzi`` thermal duals."""

    nodes: Tuple[SiqianziDualNode, ...]
    edges: Tuple[SiqianziDualEdge, ...]

    def adjacency(self) -> Dict[str, Tuple[SiqianziDualEdge, ...]]:
        """Return the adjacency mapping keyed by node name."""

        mapping: Dict[str, List[SiqianziDualEdge]] = {node.name: [] for node in self.nodes}
        for edge in self.edges:
            mapping[edge.source].append(edge)
            mapping[edge.target].append(edge)
        return {name: tuple(edges) for name, edges in mapping.items()}

    def find_edge(self, left: str, right: str) -> Optional[SiqianziDualEdge]:
        """Return the edge connecting ``left`` and ``right`` if it exists."""

        for edge in self.edges:
            if {edge.source, edge.target} == {left, right}:
                return edge
        return None


def thermal_dual_network(*machines: Siqianzi) -> SiqianziThermalNetwork:
    """Generate the thermal dual network for the provided ``Siqianzi`` instances.

    Only machines that have recorded a complete thermal dual participate in the
    resulting network.  The graph is treated as undirected: each pair of nodes
    contributes a single edge describing how their gaps and equilibria differ.
    """

    nodes: List[SiqianziDualNode] = []
    for machine in machines:
        dual = machine.dual()
        if dual is None:
            continue
        nodes.append(SiqianziDualNode(name=machine.name, dual=dual))

    edges: List[SiqianziDualEdge] = []
    for left, right in combinations(nodes, 2):
        gap_difference = float(right.dual.gap - left.dual.gap)
        equilibrium_difference = float(right.dual.equilibrium - left.dual.equilibrium)
        average_gap = float((right.dual.gap + left.dual.gap) / 2.0)
        average_equilibrium = float((right.dual.equilibrium + left.dual.equilibrium) / 2.0)
        edges.append(
            SiqianziDualEdge(
                source=left.name,
                target=right.name,
                gap_difference=gap_difference,
                equilibrium_difference=equilibrium_difference,
                average_gap=average_gap,
                average_equilibrium=average_equilibrium,
            )
        )

    return SiqianziThermalNetwork(nodes=tuple(nodes), edges=tuple(edges))


# Playful aliases embracing the poetic API.
死前子 = Siqianzi
死前子节点 = SiqianziDualNode
死前子连线 = SiqianziDualEdge
死前子网络 = SiqianziThermalNetwork
死前子热对偶网络 = thermal_dual_network


__all__ = [
    "Siqianzi",
    "SiqianziDualNode",
    "SiqianziDualEdge",
    "SiqianziThermalNetwork",
    "thermal_dual_network",
    "死前子",
    "死前子节点",
    "死前子连线",
    "死前子网络",
    "死前子热对偶网络",
]

