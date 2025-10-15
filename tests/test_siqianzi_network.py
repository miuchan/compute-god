from __future__ import annotations

from compute_god import Jizi, Zijiji
from compute_god.observer import ObserverEvent
from compute_god.siqianzi import (
    Siqianzi,
    SiqianziDualEdge,
    SiqianziThermalNetwork,
    thermal_dual_network,
)


def _temperature(state):
    return float(state["temperature"])


def _build_machine(name: str) -> Siqianzi:
    return Siqianzi(name=name, machine=Jizi(metric=_temperature), submachine=Zijiji(metric=_temperature))


def test_thermal_dual_network_only_includes_complete_nodes() -> None:
    alpha = _build_machine("alpha")
    beta = _build_machine("beta")

    alpha.observe_machine(ObserverEvent.STEP, {"temperature": 120.0})
    alpha.observe_submachine(ObserverEvent.STEP, {"temperature": -10.0})

    beta.observe_machine(ObserverEvent.STEP, {"temperature": 80.0})
    # ``beta`` never observes the submachine and should therefore be skipped.

    network = thermal_dual_network(alpha, beta)

    assert isinstance(network, SiqianziThermalNetwork)
    assert len(network.nodes) == 1
    assert network.nodes[0].name == "alpha"
    assert len(network.edges) == 0


def test_thermal_dual_network_edges_capture_differences() -> None:
    alpha = _build_machine("alpha")
    beta = _build_machine("beta")

    alpha.observe_machine(ObserverEvent.STEP, {"temperature": 100.0})
    alpha.observe_machine(ObserverEvent.STEP, {"temperature": 110.0})
    alpha.observe_submachine(ObserverEvent.STEP, {"temperature": 10.0})
    alpha.observe_submachine(ObserverEvent.STEP, {"temperature": 5.0})

    beta.observe_machine(ObserverEvent.STEP, {"temperature": 95.0})
    beta.observe_submachine(ObserverEvent.STEP, {"temperature": 15.0})

    network = thermal_dual_network(alpha, beta)
    assert len(network.nodes) == 2
    assert {node.name for node in network.nodes} == {"alpha", "beta"}

    edge = network.find_edge("alpha", "beta")
    assert isinstance(edge, SiqianziDualEdge)
    # ``alpha`` gap is 105.0 (110 - 5), ``beta`` gap is 80.0 (95 - 15)
    assert edge.gap_difference == 80.0 - 105.0
    # ``alpha`` equilibrium is 57.5, ``beta`` equilibrium is 55.0
    assert edge.equilibrium_difference == 55.0 - 57.5
    assert edge.average_gap == (105.0 + 80.0) / 2.0
    assert edge.average_equilibrium == (57.5 + 55.0) / 2.0

    adjacency = network.adjacency()
    assert set(adjacency) == {"alpha", "beta"}
    assert adjacency["alpha"] == adjacency["beta"] == (edge,)

