"""Meta spacetime stabilisation primitives.

This module formalises a tiny ``meta spacetime`` inside the Compute-God
framework.  A meta spacetime is modelled as a universe whose state tracks the
coherence between spatial structure (``topos``), temporal flow (``chronos``) and
the coupling that keeps them aligned (``coherence`` and ``causality``).  The
rules act as contractive updates, ensuring that every epoch nudges the state
closer to a blueprint where space and time are synchronised.

The primary purpose of the module is pedagogical: it turns the abstract
"existence" of a meta spacetime into a constructive fixed-point computation.
Because each rule is monotone and contractive on ``[0, 1]``-valued coordinates,
the composite transition function admits a unique fixed point.  Running the
``fixpoint`` engine therefore produces not only a witness of existence but also
an explicit notion of stability (convergence under perturbations measured by the
provided metric).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

MetaSpacetimeState = MutableMapping[str, float]


_META_KEYS = ("chronos", "topos", "causality", "continuity", "coherence", "entropy")


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
    value -= reduction
    return max(0.0, value)


def _stabilise_temporal(state: State, _ctx: object) -> State:
    updated = dict(state)

    chronos = _ensure_float(updated, "chronos")
    causality = _ensure_float(updated, "causality", chronos)
    continuity = _ensure_float(updated, "continuity", chronos)

    chronos = _towards(chronos, 1.0, 0.35)
    causality = _towards(causality, chronos, 0.4)
    continuity = _towards(continuity, chronos, 0.25)

    entropy = _ensure_float(updated, "entropy")
    entropy = _dampen_entropy(entropy, 0.08)

    updated.update(
        {
            "chronos": _bounded(chronos),
            "causality": _bounded(causality),
            "continuity": _bounded(continuity),
            "entropy": _bounded(entropy),
        }
    )
    return updated


def _stabilise_spatial(state: State, _ctx: object) -> State:
    updated = dict(state)

    topos = _ensure_float(updated, "topos")
    continuity = _ensure_float(updated, "continuity")
    coherence = _ensure_float(updated, "coherence", (topos + continuity) / 2.0)

    topos = _towards(topos, 1.0, 0.3)
    continuity = _towards(continuity, topos, 0.3)
    coherence = _towards(coherence, (topos + continuity) / 2.0, 0.35)

    entropy = _ensure_float(updated, "entropy")
    entropy = _dampen_entropy(entropy, 0.05)

    updated.update(
        {
            "topos": _bounded(topos),
            "continuity": _bounded(continuity),
            "coherence": _bounded(coherence),
            "entropy": _bounded(entropy),
        }
    )
    return updated


def _couple_meta_axes(state: State, _ctx: object) -> State:
    updated = dict(state)

    chronos = _ensure_float(updated, "chronos")
    topos = _ensure_float(updated, "topos")
    causality = _ensure_float(updated, "causality")
    continuity = _ensure_float(updated, "continuity")
    coherence = _ensure_float(updated, "coherence")

    average = (chronos + topos + causality + continuity) / 4.0

    coherence = _towards(coherence, average, 0.5)
    causality = _towards(causality, (chronos + average) / 2.0, 0.35)
    continuity = _towards(continuity, (topos + average) / 2.0, 0.35)

    entropy = _ensure_float(updated, "entropy")
    entropy = _dampen_entropy(entropy, 0.04)

    updated.update(
        {
            "coherence": _bounded(coherence),
            "causality": _bounded(causality),
            "continuity": _bounded(continuity),
            "entropy": _bounded(entropy),
        }
    )
    return updated


DEFAULT_META_SPACETIME: MetaSpacetimeState = {
    "chronos": 0.46,
    "topos": 0.44,
    "causality": 0.42,
    "continuity": 0.41,
    "coherence": 0.43,
    "entropy": 0.32,
}


def _build_meta_rules() -> Sequence[Rule]:
    return (
        rule("stabilise-temporal", _stabilise_temporal),
        rule("stabilise-spatial", _stabilise_spatial),
        rule("couple-meta-axes", _couple_meta_axes, priority=-1),
    )


def meta_spacetime_metric(previous: State, current: State) -> float:
    """Measure change across the fundamental meta spacetime coordinates."""

    delta = 0.0
    for key in _META_KEYS:
        delta += abs(_ensure_float(current, key) - _ensure_float(previous, key))
    return delta


@dataclass
class MetaSpacetimeBlueprint:
    """Target synchronisation point for the meta spacetime coordinates."""

    chronos: float = 1.0
    topos: float = 1.0
    causality: float = 1.0
    continuity: float = 1.0
    coherence: float = 1.0
    entropy: float = 0.0

    def as_state(self) -> MetaSpacetimeState:
        return {
            "chronos": self.chronos,
            "topos": self.topos,
            "causality": self.causality,
            "continuity": self.continuity,
            "coherence": self.coherence,
            "entropy": self.entropy,
        }


def ideal_meta_spacetime_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Create a universe that contracts toward a coherent meta spacetime."""

    state: MetaSpacetimeState = dict(DEFAULT_META_SPACETIME)
    if initial_state:
        for key, value in initial_state.items():
            state[key] = float(value)
    return God.universe(state=state, rules=_build_meta_rules(), observers=observers)


def run_meta_spacetime(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    epsilon: float = 1e-3,
    max_epoch: int = 96,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Run the meta spacetime universe until it stabilises."""

    universe = ideal_meta_spacetime_universe(initial_state, observers=observers)
    return fixpoint(universe, metric=meta_spacetime_metric, epsilon=epsilon, max_epoch=max_epoch)
