"""Physical realisation of the Everything Demonstration Theory.

The module turns the conceptual guarantees outlined in
``docs/everything-demonstration-foundations.md`` into an executable
universe.  The state tracks how well physical quantities (matter and
energy), informational order and observational fidelity align.  Each
rule acts as a contractive map on ``[0, 1]``-valued coordinates, which
means the composite transition admits a unique fixed point.  Running the
``fixpoint`` engine therefore produces a concrete witness that "all
things" have been demonstrated in a physically consistent way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from compute_god.core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

PhysicalDemonstrationState = MutableMapping[str, float]

_PHYSICAL_KEYS = (
    "matter",
    "energy",
    "information",
    "symmetry",
    "observation",
    "entropy",
)


def _ensure_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from None


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _dampen_entropy(value: float, reduction: float) -> float:
    return max(0.0, value - reduction)


def _realise_materiality(state: State, _ctx: object) -> State:
    updated = dict(state)

    matter = _ensure_float(updated, "matter")
    symmetry = _ensure_float(updated, "symmetry", matter)
    observation = _ensure_float(updated, "observation", (matter + symmetry) / 2.0)
    entropy = _ensure_float(updated, "entropy", 0.35)

    matter = _towards(matter, 1.0, 0.33)
    symmetry = _towards(symmetry, matter, 0.28)
    observation = _towards(observation, (matter + symmetry) / 2.0, 0.24)
    entropy = _dampen_entropy(entropy, 0.05)

    updated.update(
        {
            "matter": _bounded(matter),
            "symmetry": _bounded(symmetry),
            "observation": _bounded(observation),
            "entropy": _bounded(entropy),
        }
    )
    return updated


def _stabilise_energy_information(state: State, _ctx: object) -> State:
    updated = dict(state)

    matter = _ensure_float(updated, "matter")
    energy = _ensure_float(updated, "energy", matter)
    information = _ensure_float(updated, "information", (energy + matter) / 2.0)
    entropy = _ensure_float(updated, "entropy", 0.3)

    energy = _towards(energy, (matter + 1.0) / 2.0, 0.32)
    information = _towards(information, (energy + matter) / 2.0, 0.35)
    entropy = _dampen_entropy(entropy, 0.06)

    updated.update(
        {
            "energy": _bounded(energy),
            "information": _bounded(information),
            "entropy": _bounded(entropy),
        }
    )
    return updated


def _close_observer_loop(state: State, _ctx: object) -> State:
    updated = dict(state)

    matter = _ensure_float(updated, "matter")
    energy = _ensure_float(updated, "energy")
    information = _ensure_float(updated, "information")
    symmetry = _ensure_float(updated, "symmetry")
    observation = _ensure_float(updated, "observation")
    entropy = _ensure_float(updated, "entropy", 0.2)

    centroid = (matter + energy + information + symmetry) / 4.0

    observation = _towards(observation, centroid, 0.4)
    symmetry = _towards(symmetry, centroid, 0.3)
    entropy = _dampen_entropy(entropy, 0.04)

    updated.update(
        {
            "observation": _bounded(observation),
            "symmetry": _bounded(symmetry),
            "entropy": _bounded(entropy),
        }
    )
    return updated


DEFAULT_PHYSICAL_DEMONSTRATION: PhysicalDemonstrationState = {
    "matter": 0.45,
    "energy": 0.43,
    "information": 0.44,
    "symmetry": 0.42,
    "observation": 0.4,
    "entropy": 0.36,
}


def _build_physical_rules() -> Sequence[Rule]:
    return (
        rule("realise-materiality", _realise_materiality),
        rule("stabilise-energy-information", _stabilise_energy_information),
        rule("close-observer-loop", _close_observer_loop, priority=-1),
    )


def physical_everything_metric(previous: State, current: State) -> float:
    """Measure the distance between two physical demonstration states."""

    delta = 0.0
    for key in _PHYSICAL_KEYS:
        delta += abs(_ensure_float(current, key) - _ensure_float(previous, key))
    return delta


@dataclass
class EverythingDemonstrationBlueprint:
    """Target configuration for the physical everything demonstration."""

    matter: float = 1.0
    energy: float = 1.0
    information: float = 1.0
    symmetry: float = 1.0
    observation: float = 1.0
    entropy: float = 0.0

    def as_state(self) -> PhysicalDemonstrationState:
        return {
            "matter": self.matter,
            "energy": self.energy,
            "information": self.information,
            "symmetry": self.symmetry,
            "observation": self.observation,
            "entropy": self.entropy,
        }


def physical_everything_demonstration_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Create a universe that contracts towards the physical demonstration blueprint."""

    state: PhysicalDemonstrationState = dict(DEFAULT_PHYSICAL_DEMONSTRATION)
    if initial_state:
        for key, value in initial_state.items():
            state[key] = float(value)
    return God.universe(state=state, rules=_build_physical_rules(), observers=observers)


def run_physical_everything_demonstration(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    epsilon: float = 1e-3,
    max_epoch: int = 120,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Execute the universe until the physical demonstration converges."""

    universe = physical_everything_demonstration_universe(initial_state, observers=observers)
    return fixpoint(
        universe,
        metric=physical_everything_metric,
        epsilon=epsilon,
        max_epoch=max_epoch,
    )

