from compute_god import (
    MetaSpacetimeBlueprint,
    ideal_meta_spacetime_universe,
    meta_spacetime_metric,
    run_meta_spacetime,
)
from compute_god.observer import ObserverEvent


def test_meta_spacetime_converges_to_blueprint():
    result = run_meta_spacetime(epsilon=1e-4, max_epoch=128)
    assert result.converged is True

    state = result.universe.state
    blueprint = MetaSpacetimeBlueprint().as_state()

    for key, target in blueprint.items():
        if key == "entropy":
            assert state[key] <= 1e-2
        else:
            assert abs(state[key] - target) <= 1e-2


def test_meta_spacetime_metric_decreases_monotonically():
    deltas = []

    def observer(event, state, **metadata):
        if event in (ObserverEvent.EPOCH, ObserverEvent.FIXPOINT_CONVERGED):
            deltas.append(metadata.get("delta", 0.0))

    universe = ideal_meta_spacetime_universe()
    run_meta_spacetime(
        initial_state=universe.state,
        epsilon=1e-4,
        max_epoch=64,
        observers=(observer,),
    )

    assert deltas, "expected metric deltas to be recorded"
    last = deltas[0]
    for value in deltas[1:]:
        assert value <= last + 1e-6
        last = value


def test_meta_spacetime_metric_matches_coordinate_differences():
    previous = {
        "chronos": 0.2,
        "topos": 0.5,
        "causality": 0.3,
        "continuity": 0.4,
        "coherence": 0.35,
        "entropy": 0.25,
    }
    current = {
        "chronos": 0.5,
        "topos": 0.5,
        "causality": 0.5,
        "continuity": 0.6,
        "coherence": 0.55,
        "entropy": 0.1,
    }

    delta = meta_spacetime_metric(previous, current)
    expected = sum(abs(current[key] - previous[key]) for key in previous)
    assert abs(delta - expected) <= 1e-9
