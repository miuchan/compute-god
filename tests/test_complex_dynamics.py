from compute_god.complex_dynamics import (
    ComplexDynamicsBlueprint,
    complex_dynamics_metric,
    design_complex_dynamics_universe,
    run_complex_dynamics,
)
from compute_god.observer import ObserverEvent


def test_complex_dynamics_converges_to_blueprint():
    result = run_complex_dynamics(epsilon=1e-4, max_epoch=192)
    assert result.converged is True

    state = result.universe.state
    blueprint = ComplexDynamicsBlueprint().as_state()

    for key, target in blueprint.items():
        if key in {"entropy", "turbulence"}:
            assert state[key] <= target + 5e-3
        else:
            assert abs(state[key] - target) <= 1e-2


def test_complex_dynamics_metric_decreases_monotonically():
    deltas = []

    def observer(event, _state, **metadata):
        if event in (ObserverEvent.EPOCH, ObserverEvent.FIXPOINT_CONVERGED):
            deltas.append(metadata.get("delta", 0.0))

    run_complex_dynamics(epsilon=1e-4, max_epoch=128, observers=(observer,))

    assert deltas, "expected metric deltas to be recorded"
    last = deltas[0]
    for value in deltas[1:]:
        assert value <= last + 1e-6
        last = value


def test_complex_dynamics_metric_matches_coordinate_differences():
    previous = {
        "energy": 0.5,
        "entropy": 0.3,
        "cohesion": 0.48,
        "innovation": 0.46,
        "adaptation": 0.45,
        "stability": 0.47,
        "turbulence": 0.28,
        "resonance": 0.44,
        "feedback": 0.43,
        "memory": 0.42,
        "exploration": 0.45,
        "safety": 0.46,
    }
    current = {
        "energy": 0.7,
        "entropy": 0.12,
        "cohesion": 0.66,
        "innovation": 0.68,
        "adaptation": 0.67,
        "stability": 0.69,
        "turbulence": 0.15,
        "resonance": 0.65,
        "feedback": 0.64,
        "memory": 0.63,
        "exploration": 0.66,
        "safety": 0.67,
    }

    delta = complex_dynamics_metric(previous, current)
    expected = sum(abs(current[key] - previous[key]) for key in previous)
    assert abs(delta - expected) <= 1e-9


def test_design_complex_dynamics_universe_applies_initial_state():
    universe = design_complex_dynamics_universe(
        {"energy": 0.6, "entropy": 0.4},
        blueprint=ComplexDynamicsBlueprint(energy=0.9, entropy=0.05, turbulence=0.07),
    )
    assert universe.state["energy"] == 0.6
    assert universe.state["entropy"] == 0.4
    assert "cohesion" in universe.state
