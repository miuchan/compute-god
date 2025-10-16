"""Multilayer complex network stabilisation utilities.

The module instantiates what is arguably the "most complex network" inside the
Compute-God framework.  It treats a civilisation-scale network as a
multilayered system where structure, function, cognition and ecology interact
through dense feedback loops.  Each coordinate is normalised to ``[0, 1]`` and
the rules are designed to be contractive so that repeated application converges
to a coherent fixed point.  The fixed point witnesses a network that is
structurally sound, dynamically resilient, socially trustworthy and
entropically quiet.

To keep the implementation approachable the rules focus on smooth
interpolations (``_towards``) coupled with entropy/turbulence damping.  The
resulting dynamics remain expressive yet provably converge because every rule
shrinks distances under the provided metric.  ``run_complex_network`` offers a
one-liner to evolve an initial state until the layers lock into synchrony.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

ComplexNetworkState = MutableMapping[str, float]

_COMPLEX_KEYS: Sequence[str] = (
    "structure",
    "function",
    "cognition",
    "ecology",
    "resilience",
    "adaptation",
    "governance",
    "trust",
    "flow",
    "synchrony",
    "coherence",
    "modularity",
    "diversity",
    "redundancy",
    "turbulence",
    "entropy",
)


def _ensure_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive programming
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from None


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _dampen(value: float, reduction: float) -> float:
    value -= reduction
    return max(0.0, value)


def _stitch_structural_layers(state: State, _ctx: object) -> State:
    updated = dict(state)

    structure = _towards(_ensure_float(updated, "structure"), 1.0, 0.32)
    modularity = _towards(_ensure_float(updated, "modularity", structure), structure, 0.35)
    redundancy = _towards(_ensure_float(updated, "redundancy", modularity), (structure + modularity) / 2.0, 0.3)
    coherence = _towards(
        _ensure_float(updated, "coherence", (structure + modularity) / 2.0),
        (structure + modularity + redundancy) / 3.0,
        0.34,
    )

    turbulence = _dampen(_ensure_float(updated, "turbulence", 0.2), 0.06)
    entropy = _dampen(_ensure_float(updated, "entropy", 0.18), 0.04)

    updated.update(
        {
            "structure": _bounded(structure),
            "modularity": _bounded(modularity),
            "redundancy": _bounded(redundancy),
            "coherence": _bounded(coherence),
            "turbulence": _bounded(turbulence),
            "entropy": _bounded(entropy),
        }
    )
    return updated


def _evolve_ecological_dynamics(state: State, _ctx: object) -> State:
    updated = dict(state)

    structure = _ensure_float(updated, "structure")
    function = _towards(_ensure_float(updated, "function"), 1.0, 0.28)
    diversity = _towards(_ensure_float(updated, "diversity"), 1.0, 0.26)
    flow = _towards(_ensure_float(updated, "flow", function), (structure + function + diversity) / 3.0, 0.33)
    ecology = _towards(
        _ensure_float(updated, "ecology", flow),
        (function + diversity + flow) / 3.0,
        0.3,
    )
    adaptation = _towards(
        _ensure_float(updated, "adaptation"),
        (diversity + flow + ecology) / 3.0,
        0.32,
    )
    redundancy = _ensure_float(updated, "redundancy")
    resilience = _towards(
        _ensure_float(updated, "resilience"),
        (redundancy + adaptation + ecology) / 3.0,
        0.31,
    )

    turbulence = _dampen(_ensure_float(updated, "turbulence"), 0.05)
    entropy = _dampen(_ensure_float(updated, "entropy"), 0.03)

    updated.update(
        {
            "function": _bounded(function),
            "diversity": _bounded(diversity),
            "flow": _bounded(flow),
            "ecology": _bounded(ecology),
            "adaptation": _bounded(adaptation),
            "resilience": _bounded(resilience),
            "turbulence": _bounded(turbulence),
            "entropy": _bounded(entropy),
        }
    )
    return updated


def _align_cognitive_social(state: State, _ctx: object) -> State:
    updated = dict(state)

    cognition = _towards(_ensure_float(updated, "cognition"), 1.0, 0.29)
    governance = _towards(_ensure_float(updated, "governance"), 1.0, 0.27)
    trust = _towards(
        _ensure_float(updated, "trust", (cognition + governance) / 2.0),
        (cognition + governance) / 2.0,
        0.34,
    )

    flow = _ensure_float(updated, "flow")
    ecology = _ensure_float(updated, "ecology")
    synchrony = _towards(
        _ensure_float(updated, "synchrony", (flow + trust) / 2.0),
        (flow + trust + cognition + governance + ecology) / 5.0,
        0.36,
    )
    coherence = _towards(
        _ensure_float(updated, "coherence"),
        (cognition + trust + governance + synchrony) / 4.0,
        0.33,
    )

    entropy = _dampen(_ensure_float(updated, "entropy"), 0.02)

    updated.update(
        {
            "cognition": _bounded(cognition),
            "governance": _bounded(governance),
            "trust": _bounded(trust),
            "synchrony": _bounded(synchrony),
            "coherence": _bounded(coherence),
            "entropy": _bounded(entropy),
        }
    )
    return updated


def _close_feedback_loops(state: State, _ctx: object) -> State:
    updated = dict(state)

    positive_keys = [
        "structure",
        "function",
        "cognition",
        "ecology",
        "resilience",
        "adaptation",
        "governance",
        "trust",
        "flow",
        "synchrony",
        "coherence",
        "modularity",
        "diversity",
        "redundancy",
    ]
    average = sum(_ensure_float(updated, key) for key in positive_keys) / len(positive_keys)

    for key in positive_keys:
        value = _towards(_ensure_float(updated, key), (average + 1.0) / 2.0, 0.24)
        updated[key] = _bounded(value)

    turbulence = _dampen(_ensure_float(updated, "turbulence"), 0.07)
    entropy = _dampen(_ensure_float(updated, "entropy"), 0.05)

    updated.update({"turbulence": _bounded(turbulence), "entropy": _bounded(entropy)})
    return updated


DEFAULT_COMPLEX_NETWORK: ComplexNetworkState = {
    "structure": 0.48,
    "function": 0.46,
    "cognition": 0.44,
    "ecology": 0.45,
    "resilience": 0.42,
    "adaptation": 0.43,
    "governance": 0.41,
    "trust": 0.4,
    "flow": 0.47,
    "synchrony": 0.39,
    "coherence": 0.43,
    "modularity": 0.45,
    "diversity": 0.44,
    "redundancy": 0.42,
    "turbulence": 0.28,
    "entropy": 0.24,
}


def _build_complex_rules() -> Sequence[Rule]:
    return (
        rule("stitch-structural-layers", _stitch_structural_layers),
        rule("evolve-ecological-dynamics", _evolve_ecological_dynamics),
        rule("align-cognitive-social", _align_cognitive_social),
        rule("close-feedback-loops", _close_feedback_loops, priority=-1),
    )


def complex_network_metric(previous: State, current: State) -> float:
    """Measure coordinate-wise differences across the complex network state."""

    delta = 0.0
    for key in _COMPLEX_KEYS:
        delta += abs(_ensure_float(current, key) - _ensure_float(previous, key))
    return delta


@dataclass
class ComplexNetworkBlueprint:
    """Target configuration for the multilayer complex network."""

    structure: float = 1.0
    function: float = 1.0
    cognition: float = 1.0
    ecology: float = 1.0
    resilience: float = 1.0
    adaptation: float = 1.0
    governance: float = 1.0
    trust: float = 1.0
    flow: float = 1.0
    synchrony: float = 1.0
    coherence: float = 1.0
    modularity: float = 1.0
    diversity: float = 1.0
    redundancy: float = 1.0
    turbulence: float = 0.0
    entropy: float = 0.0

    def as_state(self) -> Mapping[str, float]:
        return {
            "structure": self.structure,
            "function": self.function,
            "cognition": self.cognition,
            "ecology": self.ecology,
            "resilience": self.resilience,
            "adaptation": self.adaptation,
            "governance": self.governance,
            "trust": self.trust,
            "flow": self.flow,
            "synchrony": self.synchrony,
            "coherence": self.coherence,
            "modularity": self.modularity,
            "diversity": self.diversity,
            "redundancy": self.redundancy,
            "turbulence": self.turbulence,
            "entropy": self.entropy,
        }


def ideal_complex_network_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Build the canonical complex network universe."""

    state: ComplexNetworkState
    if initial_state is None:
        state = dict(DEFAULT_COMPLEX_NETWORK)
    else:
        state = {key: float(value) for key, value in initial_state.items()}
    return God.universe(state=state, rules=_build_complex_rules(), observers=observers)


def run_complex_network(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    epsilon: float = 1e-3,
    max_epoch: int = 128,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Run the complex network universe until the layers synchronise."""

    universe = ideal_complex_network_universe(initial_state, observers=observers)
    return fixpoint(universe, metric=complex_network_metric, epsilon=epsilon, max_epoch=max_epoch)
