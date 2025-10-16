"""Complex dynamical system design and evolution helpers.

The module packages a small-yet-expressive model of a complex dynamical
system.  The state keeps track of energy, cohesion, innovation and other
macroscopic qualities that frequently appear in socio-technical systems.  The
rules are written as gentle contractions around a configurable blueprint.  By
tracking the deviation to the target at every step the rules orchestrate
stability seeking feedback loops without ever diverging from the declared
design.

``run_complex_dynamics`` can therefore be used to iterate any initial
configuration towards the supplied blueprint.  The default blueprint reflects
an almost perfectly tuned system (high energy/adaptation with tiny entropy and
low turbulence) but users may provide their own equilibrium description.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .engine import FixpointResult, fixpoint
from .observer import Observer
from .rule import Rule, State, rule
from .universe import God, Universe

ComplexDynamicsState = MutableMapping[str, float]

_DYNAMICS_KEYS: Sequence[str] = (
    "energy",
    "entropy",
    "cohesion",
    "innovation",
    "adaptation",
    "stability",
    "turbulence",
    "resonance",
    "feedback",
    "memory",
    "exploration",
    "safety",
)


def _ensure_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive branch
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from None


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


DEFAULT_COMPLEX_DYNAMICS: ComplexDynamicsState = {
    "energy": 0.42,
    "entropy": 0.24,
    "cohesion": 0.4,
    "innovation": 0.41,
    "adaptation": 0.39,
    "stability": 0.43,
    "turbulence": 0.27,
    "resonance": 0.38,
    "feedback": 0.37,
    "memory": 0.36,
    "exploration": 0.4,
    "safety": 0.41,
}


@dataclass
class ComplexDynamicsBlueprint:
    """Blueprint describing the desired equilibrium of the dynamical system."""

    energy: float = 0.975
    entropy: float = 0.02
    cohesion: float = 0.975
    innovation: float = 0.975
    adaptation: float = 0.975
    stability: float = 0.975
    turbulence: float = 0.03
    resonance: float = 0.975
    feedback: float = 0.975
    memory: float = 0.975
    exploration: float = 0.975
    safety: float = 0.975

    def as_state(self) -> Mapping[str, float]:
        return {
            "energy": self.energy,
            "entropy": self.entropy,
            "cohesion": self.cohesion,
            "innovation": self.innovation,
            "adaptation": self.adaptation,
            "stability": self.stability,
            "turbulence": self.turbulence,
            "resonance": self.resonance,
            "feedback": self.feedback,
            "memory": self.memory,
            "exploration": self.exploration,
            "safety": self.safety,
        }


def _stabilise_energy_flow(target: Mapping[str, float]):
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        energy = _towards(_ensure_float(updated, "energy"), target["energy"], 0.33)
        entropy = _towards(_ensure_float(updated, "entropy"), target["entropy"], 0.38)
        turbulence = _towards(_ensure_float(updated, "turbulence"), target["turbulence"], 0.35)

        stability_delta = 0.5 * (
            (energy - target["energy"]) - (entropy - target["entropy"]) - (turbulence - target["turbulence"])
        )
        stability_target = target["stability"] + stability_delta
        stability = _towards(_ensure_float(updated, "stability"), stability_target, 0.3)

        updated.update(
            {
                "energy": _bounded(energy),
                "entropy": _bounded(entropy),
                "turbulence": _bounded(turbulence),
                "stability": _bounded(stability),
            }
        )
        return updated

    return apply


def _harmonise_feedback_loops(target: Mapping[str, float]):
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        cohesion = _towards(_ensure_float(updated, "cohesion"), target["cohesion"], 0.3)
        energy = _ensure_float(updated, "energy")
        stability = _ensure_float(updated, "stability")

        resonance_delta = (
            (energy - target["energy"]) + (cohesion - target["cohesion"]) + (stability - target["stability"])
        ) / 3.0
        resonance_target = target["resonance"] + 0.6 * resonance_delta
        resonance = _towards(_ensure_float(updated, "resonance"), resonance_target, 0.28)

        memory = _towards(_ensure_float(updated, "memory"), target["memory"], 0.27)

        feedback_delta = (
            (resonance - target["resonance"]) + (cohesion - target["cohesion"]) + (memory - target["memory"])
        ) / 3.0
        feedback_target = target["feedback"] + 0.55 * feedback_delta
        feedback = _towards(_ensure_float(updated, "feedback"), feedback_target, 0.3)

        entropy = _towards(_ensure_float(updated, "entropy"), target["entropy"], 0.12)

        updated.update(
            {
                "cohesion": _bounded(cohesion),
                "resonance": _bounded(resonance),
                "memory": _bounded(memory),
                "feedback": _bounded(feedback),
                "entropy": _bounded(entropy),
            }
        )
        return updated

    return apply


def _diffuse_innovation_cycles(target: Mapping[str, float]):
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        innovation = _towards(_ensure_float(updated, "innovation"), target["innovation"], 0.31)
        cohesion = _ensure_float(updated, "cohesion")
        feedback = _ensure_float(updated, "feedback")

        adaptation_delta = (
            (innovation - target["innovation"]) + (feedback - target["feedback"]) + (cohesion - target["cohesion"])
        ) / 3.0
        adaptation_target = target["adaptation"] + 0.58 * adaptation_delta
        adaptation = _towards(_ensure_float(updated, "adaptation"), adaptation_target, 0.3)

        exploration = _towards(_ensure_float(updated, "exploration"), target["exploration"], 0.29)

        stability = _ensure_float(updated, "stability")
        memory = _ensure_float(updated, "memory")
        safety_delta = (
            (stability - target["stability"]) + (memory - target["memory"]) + (adaptation - target["adaptation"])
        ) / 3.0
        safety_target = target["safety"] + 0.54 * safety_delta
        safety = _towards(_ensure_float(updated, "safety"), safety_target, 0.28)

        turbulence = _towards(_ensure_float(updated, "turbulence"), target["turbulence"], 0.17)

        updated.update(
            {
                "innovation": _bounded(innovation),
                "adaptation": _bounded(adaptation),
                "exploration": _bounded(exploration),
                "safety": _bounded(safety),
                "turbulence": _bounded(turbulence),
            }
        )
        return updated

    return apply


def _synchronise_temporal_layers(target: Mapping[str, float]):
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        energy = _ensure_float(updated, "energy")
        innovation = _ensure_float(updated, "innovation")
        exploration = _ensure_float(updated, "exploration")
        stability = _ensure_float(updated, "stability")
        safety = _ensure_float(updated, "safety")
        feedback = _ensure_float(updated, "feedback")

        horizon_delta = (
            (energy - target["energy"]) + (innovation - target["innovation"]) + (exploration - target["exploration"])
        ) / 3.0
        anchor_delta = (
            (stability - target["stability"]) + (safety - target["safety"]) + (feedback - target["feedback"])
        ) / 3.0
        equilibrium_delta = 0.5 * (horizon_delta + anchor_delta)

        energy_target = target["energy"] + 0.6 * equilibrium_delta
        stability_target = target["stability"] + 0.6 * equilibrium_delta
        resonance_target = target["resonance"] + 0.55 * equilibrium_delta
        adaptation_target = target["adaptation"] + 0.55 * equilibrium_delta
        memory_target = target["memory"] + 0.5 * equilibrium_delta

        energy = _towards(energy, energy_target, 0.24)
        stability = _towards(stability, stability_target, 0.24)
        resonance = _towards(_ensure_float(updated, "resonance"), resonance_target, 0.24)
        adaptation = _towards(_ensure_float(updated, "adaptation"), adaptation_target, 0.24)
        memory = _towards(_ensure_float(updated, "memory"), memory_target, 0.22)

        entropy = _towards(_ensure_float(updated, "entropy"), target["entropy"], 0.18)
        turbulence = _towards(_ensure_float(updated, "turbulence"), target["turbulence"], 0.18)

        updated.update(
            {
                "energy": _bounded(energy),
                "stability": _bounded(stability),
                "resonance": _bounded(resonance),
                "adaptation": _bounded(adaptation),
                "memory": _bounded(memory),
                "entropy": _bounded(entropy),
                "turbulence": _bounded(turbulence),
            }
        )
        return updated

    return apply


def _build_dynamics_rules(target: Mapping[str, float]) -> Sequence[Rule]:
    return (
        rule("stabilise-energy-flow", _stabilise_energy_flow(target)),
        rule("harmonise-feedback-loops", _harmonise_feedback_loops(target)),
        rule("diffuse-innovation-cycles", _diffuse_innovation_cycles(target)),
        rule("synchronise-temporal-layers", _synchronise_temporal_layers(target), priority=-1),
    )


def complex_dynamics_metric(previous: State, current: State) -> float:
    """Sum of coordinate-wise distances across the dynamical state."""

    delta = 0.0
    for key in _DYNAMICS_KEYS:
        delta += abs(_ensure_float(current, key) - _ensure_float(previous, key))
    return delta


def design_complex_dynamics_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[ComplexDynamicsBlueprint] = None,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Instantiate a universe that realises the supplied complex dynamics blueprint."""

    if blueprint is None:
        blueprint = ComplexDynamicsBlueprint()
    target = {key: _bounded(float(value)) for key, value in blueprint.as_state().items()}

    if initial_state is None:
        state = dict(DEFAULT_COMPLEX_DYNAMICS)
    else:
        state = dict(DEFAULT_COMPLEX_DYNAMICS)
        for key, value in initial_state.items():
            state[key] = float(value)

    for key, target_value in target.items():
        state.setdefault(key, float(target_value))
        state[key] = _bounded(float(state[key]))

    return God.universe(state=state, rules=_build_dynamics_rules(target), observers=observers)


def run_complex_dynamics(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[ComplexDynamicsBlueprint] = None,
    epsilon: float = 1e-4,
    max_epoch: int = 192,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Run the complex dynamical system until it matches the blueprint."""

    universe = design_complex_dynamics_universe(
        initial_state,
        blueprint=blueprint,
        observers=observers,
    )
    return fixpoint(universe, metric=complex_dynamics_metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "ComplexDynamicsBlueprint",
    "ComplexDynamicsState",
    "DEFAULT_COMPLEX_DYNAMICS",
    "complex_dynamics_metric",
    "design_complex_dynamics_universe",
    "run_complex_dynamics",
]

