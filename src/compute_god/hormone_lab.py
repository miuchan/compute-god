"""Hormone kinetics fine-tuning laboratory.

This module models a simplified endocrine regulation lab that can tune
multiple hormonal axes through gentle gradient descent.  Each coordinate in
the state represents an interpretable physiological quantity—circadian
amplitude, cortisol balance, thyroid flux, insulin resilience and the
oxytocin bonding wave.  The goal is to nudge every coordinate towards an
evidence-backed target while preserving their mutual entrainment.

Three coupling principles drive the optimisation:

* **Circadian alignment** – cortisol should peak shortly after the circadian
  amplitude crest.
* **Metabolic harmony** – thyroid flux and insulin resilience must remain
  synchronised to avoid metabolic whiplash.
* **Bonding coherence** – the oxytocin field mirrors the mean state of the
  other axes, acting as an integrator of overall endocrine safety.

The :func:`run_hormone_lab` helper executes projected gradient descent under
the shared fixed-point engine so that other universes can import the tuned
state as a stabilising prior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

HormoneLabState = MutableMapping[str, float]

_HORMONE_KEYS: Sequence[str] = (
    "circadian_amplitude",
    "cortisol_balance",
    "thyroid_flux",
    "insulin_resilience",
    "oxytocin_wave",
)

_TARGETS: Mapping[str, float] = {
    "circadian_amplitude": 0.82,
    "cortisol_balance": 0.70,
    "thyroid_flux": 0.74,
    "insulin_resilience": 0.75,
    "oxytocin_wave": 0.80,
}

_BASE_WEIGHTS: Mapping[str, float] = {
    "circadian_amplitude": 0.32,
    "cortisol_balance": 0.28,
    "thyroid_flux": 0.30,
    "insulin_resilience": 0.30,
    "oxytocin_wave": 0.26,
}

_CIRCADIAN_WEIGHT = 0.20
_METABOLIC_WEIGHT = 0.18
_BONDING_WEIGHT = 0.16


def _ensure_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        raise TypeError(f"state[{key!r}] must be numeric, received {value!r}") from None


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _hormone_objective(state: MutableMapping[str, object]) -> tuple[float, dict[str, float]]:
    """Return the objective value and gradient for ``state``."""

    values = {key: _ensure_float(state, key, float(_TARGETS.get(key, 0.0))) for key in _HORMONE_KEYS}

    objective = 0.0
    gradient = {key: 0.0 for key in _HORMONE_KEYS}

    for key, weight in _BASE_WEIGHTS.items():
        diff = values[key] - _TARGETS[key]
        objective += weight * diff * diff
        gradient[key] += 2.0 * weight * diff

    cortisol_reference = values["circadian_amplitude"] - 0.12
    circadian_gap = values["cortisol_balance"] - cortisol_reference
    objective += _CIRCADIAN_WEIGHT * circadian_gap * circadian_gap
    grad_circadian = 2.0 * _CIRCADIAN_WEIGHT * circadian_gap
    gradient["cortisol_balance"] += grad_circadian
    gradient["circadian_amplitude"] -= grad_circadian

    metabolic_gap = values["insulin_resilience"] - values["thyroid_flux"]
    objective += _METABOLIC_WEIGHT * metabolic_gap * metabolic_gap
    grad_metabolic = 2.0 * _METABOLIC_WEIGHT * metabolic_gap
    gradient["insulin_resilience"] += grad_metabolic
    gradient["thyroid_flux"] -= grad_metabolic

    bonding_reference = (
        values["circadian_amplitude"] + values["insulin_resilience"] + values["thyroid_flux"]
    ) / 3.0
    bonding_gap = values["oxytocin_wave"] - bonding_reference
    objective += _BONDING_WEIGHT * bonding_gap * bonding_gap
    grad_bonding = 2.0 * _BONDING_WEIGHT * bonding_gap
    gradient["oxytocin_wave"] += grad_bonding
    shared_grad = grad_bonding / 3.0
    gradient["circadian_amplitude"] -= shared_grad
    gradient["insulin_resilience"] -= shared_grad
    gradient["thyroid_flux"] -= shared_grad

    return objective, gradient


def _synchrony_score(state: MutableMapping[str, object]) -> float:
    circadian = _ensure_float(state, "circadian_amplitude")
    cortisol = _ensure_float(state, "cortisol_balance")
    thyroid = _ensure_float(state, "thyroid_flux")
    insulin = _ensure_float(state, "insulin_resilience")
    oxytocin = _ensure_float(state, "oxytocin_wave")

    circadian_match = 1.0 - min(1.0, abs(cortisol - (circadian - 0.12)) * 2.6)
    metabolic_coherence = 1.0 - min(1.0, abs(insulin - thyroid) * 2.2)
    bonding_alignment = 1.0 - min(1.0, abs(oxytocin - (circadian + insulin + thyroid) / 3.0) * 2.0)

    score = 0.35 * circadian_match + 0.33 * metabolic_coherence + 0.32 * bonding_alignment
    return _bounded(score)


def _metabolic_balance(state: MutableMapping[str, object]) -> float:
    insulin = _ensure_float(state, "insulin_resilience")
    thyroid = _ensure_float(state, "thyroid_flux")
    balance = 1.0 - min(1.0, abs(insulin - thyroid) * 1.8)
    return _bounded(balance)


def _resilience_band(state: MutableMapping[str, object]) -> float:
    circadian = _ensure_float(state, "circadian_amplitude")
    cortisol = _ensure_float(state, "cortisol_balance")
    band = 1.0 - min(1.0, abs(cortisol - (circadian - 0.12)) * 2.0)
    return _bounded(band)


def _bonding_field(state: MutableMapping[str, object]) -> float:
    oxytocin = _ensure_float(state, "oxytocin_wave")
    circadian = _ensure_float(state, "circadian_amplitude")
    insulin = _ensure_float(state, "insulin_resilience")
    thyroid = _ensure_float(state, "thyroid_flux")
    desired = (circadian * 0.4 + insulin * 0.3 + thyroid * 0.3)
    field = 1.0 - min(1.0, abs(oxytocin - desired) * 1.7)
    return _bounded(field)


def _hormone_lab_step(state: State, _ctx: object) -> State:
    updated = dict(state)
    learning_rate = max(0.0, float(updated.get("micro_adjust", 0.22)))
    if learning_rate == 0.0:
        learning_rate = 0.22
    learning_rate = min(learning_rate, 1.0)

    current_objective, gradient = _hormone_objective(updated)

    delta = 0.0
    for key, grad in gradient.items():
        current_value = _ensure_float(updated, key)
        new_value = _bounded(current_value - learning_rate * grad)
        delta += (new_value - current_value) ** 2
        updated[key] = new_value

    next_objective, next_gradient = _hormone_objective(updated)
    gradient_norm = math.sqrt(sum(component * component for component in next_gradient.values()))

    updated["objective"] = next_objective
    updated["gradient_norm"] = gradient_norm
    updated["delta_norm"] = math.sqrt(delta)
    updated["descent"] = current_objective - next_objective
    updated["synchrony_score"] = _synchrony_score(updated)
    updated["metabolic_balance"] = _metabolic_balance(updated)
    updated["resilience_band"] = _resilience_band(updated)
    updated["bonding_field"] = _bonding_field(updated)
    updated["micro_adjust"] = learning_rate

    return updated


def _build_rules() -> Sequence[Rule]:
    return (rule("hormone-lab-step", _hormone_lab_step),)


DEFAULT_STATE: HormoneLabState = {
    "circadian_amplitude": 0.58,
    "cortisol_balance": 0.52,
    "thyroid_flux": 0.50,
    "insulin_resilience": 0.48,
    "oxytocin_wave": 0.55,
    "micro_adjust": 0.22,
    "objective": 0.0,
    "gradient_norm": 0.0,
    "delta_norm": 0.0,
    "descent": 0.0,
    "synchrony_score": 0.0,
    "metabolic_balance": 0.0,
    "resilience_band": 0.0,
    "bonding_field": 0.0,
}


def hormone_lab_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    micro_adjust: float = 0.22,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Instantiate the coupled hormone kinetics universes."""

    if micro_adjust <= 0:
        raise ValueError("micro_adjust must be positive")

    state: HormoneLabState = dict(DEFAULT_STATE)
    state["micro_adjust"] = float(micro_adjust)

    if initial_state:
        for key, value in initial_state.items():
            if key in _HORMONE_KEYS:
                state[key] = float(value)

    objective, gradient = _hormone_objective(state)
    state["objective"] = objective
    state["gradient_norm"] = math.sqrt(sum(component * component for component in gradient.values()))
    state["delta_norm"] = 0.0
    state["descent"] = 0.0
    state["synchrony_score"] = _synchrony_score(state)
    state["metabolic_balance"] = _metabolic_balance(state)
    state["resilience_band"] = _resilience_band(state)
    state["bonding_field"] = _bonding_field(state)

    return God.universe(state=state, rules=_build_rules(), observers=observers)


def hormone_lab_metric(previous: State, current: State) -> float:
    """Compute the Euclidean distance across hormone readiness coordinates."""

    total = 0.0
    for key in _HORMONE_KEYS:
        prev_value = _ensure_float(dict(previous), key)
        curr_value = _ensure_float(dict(current), key)
        total += (curr_value - prev_value) ** 2

    objective_gap = _ensure_float(dict(previous), "objective") - _ensure_float(dict(current), "objective")
    total += 0.25 * objective_gap * objective_gap
    return math.sqrt(total)


@dataclass(frozen=True)
class HormoneLabOptimisationResult:
    """Wrapper around the fixpoint result for convenience."""

    result: FixpointResult

    @property
    def state(self) -> State:
        return self.result.universe.state


def run_hormone_lab(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    micro_adjust: float = 0.22,
    epsilon: float = 1e-4,
    max_epoch: int = 256,
    observers: Optional[Sequence[Observer]] = None,
) -> HormoneLabOptimisationResult:
    """Evolve the hormone lab until a fixed point is reached."""

    universe = hormone_lab_universe(initial_state, micro_adjust=micro_adjust, observers=observers)
    result = fixpoint(universe, metric=hormone_lab_metric, epsilon=epsilon, max_epoch=max_epoch)
    return HormoneLabOptimisationResult(result)
