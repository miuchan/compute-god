from compute_god.complex_network import (
    ComplexNetworkBlueprint,
    complex_network_metric,
    ideal_complex_network_universe,
    run_complex_network,
)
from compute_god.observer import ObserverEvent


def test_complex_network_converges_to_blueprint():
    result = run_complex_network(epsilon=1e-4, max_epoch=192)
    assert result.converged is True

    state = result.universe.state
    blueprint = ComplexNetworkBlueprint().as_state()

    for key, target in blueprint.items():
        if key in {"entropy", "turbulence"}:
            assert state[key] <= 1e-2
        else:
            assert abs(state[key] - target) <= 1e-2


def test_complex_network_metric_decreases_monotonically():
    deltas = []

    def observer(event, _state, **metadata):
        if event in (ObserverEvent.EPOCH, ObserverEvent.FIXPOINT_CONVERGED):
            deltas.append(metadata.get("delta", 0.0))

    run_complex_network(epsilon=1e-4, max_epoch=96, observers=(observer,))

    assert deltas, "expected metric deltas to be recorded"
    last = deltas[0]
    for value in deltas[1:]:
        assert value <= last + 1e-6
        last = value


def test_complex_network_metric_matches_coordinate_differences():
    previous = {
        "structure": 0.5,
        "function": 0.4,
        "cognition": 0.45,
        "ecology": 0.48,
        "resilience": 0.43,
        "adaptation": 0.44,
        "governance": 0.42,
        "trust": 0.41,
        "flow": 0.46,
        "synchrony": 0.4,
        "coherence": 0.45,
        "modularity": 0.44,
        "diversity": 0.47,
        "redundancy": 0.43,
        "turbulence": 0.3,
        "entropy": 0.25,
    }
    current = {
        "structure": 0.7,
        "function": 0.6,
        "cognition": 0.55,
        "ecology": 0.65,
        "resilience": 0.57,
        "adaptation": 0.58,
        "governance": 0.6,
        "trust": 0.59,
        "flow": 0.66,
        "synchrony": 0.61,
        "coherence": 0.63,
        "modularity": 0.62,
        "diversity": 0.64,
        "redundancy": 0.6,
        "turbulence": 0.18,
        "entropy": 0.12,
    }

    delta = complex_network_metric(previous, current)
    expected = sum(abs(current[key] - previous[key]) for key in previous)
    assert abs(delta - expected) <= 1e-9
