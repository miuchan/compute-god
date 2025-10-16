"""Drug laboratory optimisation via gradient descent.

This module instantiates a simplified version of the "DrugLab" universe
introduced in the documentation.  The state tracks the readiness of six
subsystems—laboratory infrastructure, assay automation, in vivo orchestration,
safety governance, ethics oversight and translation planning.  Every subsystem
is modelled as a value in ``[0, 1]`` where larger numbers indicate tighter
control, better calibration or higher trust.

The implementation focuses on the feedback loop between the infrastructure and
project universes.  We expose a differentiable objective encoding three
principles:

* Each subsystem should approach a desired target competency.
* Adjacent stages (e.g. assay -> in vivo -> translation) must remain aligned so
  that throughput does not collapse at hand-off points.
* Safety and ethics must remain tightly coupled with execution so that toxic or
  non-compliant plans are discouraged automatically.

The ``drug_lab_gradient_step`` rule performs projected gradient descent on this
objective, keeping every coordinate within ``[0, 1]``.  The helper
:func:`run_drug_lab` wraps the fixpoint engine so callers can iterate until the
laboratory reaches a stable configuration (gradient norm below the tolerance).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

DrugLabState = MutableMapping[str, float]

_DRUG_LAB_KEYS: Sequence[str] = (
    "infrastructure",
    "assay",
    "in_vivo",
    "safety",
    "ethics",
    "translation",
)

_TARGETS: Mapping[str, float] = {
    "infrastructure": 0.92,
    "assay": 0.88,
    "in_vivo": 0.85,
    "safety": 0.90,
    "ethics": 0.93,
    "translation": 0.87,
}

_BASE_WEIGHTS: Mapping[str, float] = {
    "infrastructure": 0.35,
    "assay": 0.30,
    "in_vivo": 0.28,
    "safety": 0.32,
    "ethics": 0.34,
    "translation": 0.26,
}

_PIPELINE_WEIGHT = 0.18
_SAFETY_WEIGHT = 0.22
_TRANSLATION_WEIGHT = 0.16
_ETHICS_WEIGHT = 0.14


def _ensure_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        raise TypeError(f"state[{key!r}] must be numeric, received {value!r}") from None


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _drug_lab_objective(state: MutableMapping[str, object]) -> tuple[float, dict[str, float]]:
    """Return the objective value and its gradient for ``state``."""

    values = {key: _ensure_float(state, key, float(_TARGETS.get(key, 0.0))) for key in _DRUG_LAB_KEYS}

    objective = 0.0
    gradient = {key: 0.0 for key in _DRUG_LAB_KEYS}

    for key, weight in _BASE_WEIGHTS.items():
        diff = values[key] - _TARGETS[key]
        objective += weight * diff * diff
        gradient[key] += 2.0 * weight * diff

    pipeline_delta = (values["infrastructure"] + values["assay"]) / 2.0 - values["in_vivo"]
    objective += _PIPELINE_WEIGHT * pipeline_delta * pipeline_delta
    grad_pipeline = 2.0 * _PIPELINE_WEIGHT * pipeline_delta
    gradient["infrastructure"] += grad_pipeline * 0.5
    gradient["assay"] += grad_pipeline * 0.5
    gradient["in_vivo"] += grad_pipeline * -1.0

    safety_gap = values["in_vivo"] - values["safety"]
    objective += _SAFETY_WEIGHT * safety_gap * safety_gap
    grad_safety = 2.0 * _SAFETY_WEIGHT * safety_gap
    gradient["in_vivo"] += grad_safety
    gradient["safety"] -= grad_safety

    translation_gap = values["translation"] - (values["assay"] + values["in_vivo"]) / 2.0
    objective += _TRANSLATION_WEIGHT * translation_gap * translation_gap
    grad_translation = 2.0 * _TRANSLATION_WEIGHT * translation_gap
    gradient["translation"] += grad_translation
    gradient["assay"] -= grad_translation * 0.5
    gradient["in_vivo"] -= grad_translation * 0.5

    ethics_gap = values["ethics"] - (values["safety"] + values["translation"]) / 2.0
    objective += _ETHICS_WEIGHT * ethics_gap * ethics_gap
    grad_ethics = 2.0 * _ETHICS_WEIGHT * ethics_gap
    gradient["ethics"] += grad_ethics
    gradient["safety"] -= grad_ethics * 0.5
    gradient["translation"] -= grad_ethics * 0.5

    return objective, gradient


def _alignment_score(state: MutableMapping[str, object]) -> float:
    infrastructure = _ensure_float(state, "infrastructure")
    assay = _ensure_float(state, "assay")
    in_vivo = _ensure_float(state, "in_vivo")
    translation = _ensure_float(state, "translation")

    pipeline_delta = abs((infrastructure + assay) / 2.0 - in_vivo)
    translation_delta = abs(translation - (assay + in_vivo) / 2.0)
    score = 1.0 - min(1.0, pipeline_delta * 0.6 + translation_delta * 0.4)
    return _bounded(score)


def _safety_margin(state: MutableMapping[str, object]) -> float:
    in_vivo = _ensure_float(state, "in_vivo")
    safety = _ensure_float(state, "safety")
    margin = 1.0 - min(1.0, abs(in_vivo - safety))
    return _bounded(margin)


def _ethics_harmony(state: MutableMapping[str, object]) -> float:
    ethics = _ensure_float(state, "ethics")
    safety = _ensure_float(state, "safety")
    translation = _ensure_float(state, "translation")
    harmony = 1.0 - min(1.0, abs(ethics - (safety + translation) / 2.0))
    return _bounded(harmony)


def _drug_lab_gradient_step(state: State, _ctx: object) -> State:
    updated = dict(state)
    learning_rate = max(0.0, float(updated.get("learning_rate", 0.18)))
    if learning_rate == 0.0:
        learning_rate = 0.18
    learning_rate = min(learning_rate, 1.0)

    current_objective, gradient = _drug_lab_objective(updated)

    delta = 0.0
    for key, grad in gradient.items():
        current_value = _ensure_float(updated, key)
        new_value = _bounded(current_value - learning_rate * grad)
        delta += (new_value - current_value) ** 2
        updated[key] = new_value

    next_objective, next_gradient = _drug_lab_objective(updated)
    gradient_norm = math.sqrt(sum(component * component for component in next_gradient.values()))

    updated["objective"] = next_objective
    updated["gradient_norm"] = gradient_norm
    updated["delta_norm"] = math.sqrt(delta)
    updated["descent"] = current_objective - next_objective
    updated["pipeline_alignment"] = _alignment_score(updated)
    updated["safety_margin"] = _safety_margin(updated)
    updated["ethics_harmony"] = _ethics_harmony(updated)
    updated["learning_rate"] = learning_rate

    return updated


def _build_rules() -> Sequence[Rule]:
    return (rule("drug-lab-gradient-step", _drug_lab_gradient_step),)


DEFAULT_STATE: DrugLabState = {
    "infrastructure": 0.52,
    "assay": 0.48,
    "in_vivo": 0.42,
    "safety": 0.65,
    "ethics": 0.70,
    "translation": 0.40,
    "learning_rate": 0.18,
    "objective": 0.0,
    "gradient_norm": 0.0,
    "delta_norm": 0.0,
    "descent": 0.0,
    "pipeline_alignment": 0.0,
    "safety_margin": 0.0,
    "ethics_harmony": 0.0,
}


def ideal_drug_lab_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    learning_rate: float = 0.18,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Instantiate the coupled drug laboratory universes."""

    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")

    state: DrugLabState = dict(DEFAULT_STATE)
    state["learning_rate"] = float(learning_rate)

    if initial_state:
        for key, value in initial_state.items():
            if key in _DRUG_LAB_KEYS:
                state[key] = float(value)

    objective, gradient = _drug_lab_objective(state)
    state["objective"] = objective
    state["gradient_norm"] = math.sqrt(sum(component * component for component in gradient.values()))
    state["delta_norm"] = 0.0
    state["descent"] = 0.0
    state["pipeline_alignment"] = _alignment_score(state)
    state["safety_margin"] = _safety_margin(state)
    state["ethics_harmony"] = _ethics_harmony(state)

    return God.universe(state=state, rules=_build_rules(), observers=observers)


def drug_lab_metric(previous: State, current: State) -> float:
    """Euclidean distance across the laboratory readiness coordinates."""

    total = 0.0
    for key in _DRUG_LAB_KEYS:
        prev_value = _ensure_float(dict(previous), key)
        curr_value = _ensure_float(dict(current), key)
        total += (curr_value - prev_value) ** 2
    total += (
        (_ensure_float(dict(previous), "objective") - _ensure_float(dict(current), "objective")) ** 2
    ) * 0.25
    return math.sqrt(total)


@dataclass(frozen=True)
class DrugLabOptimisationResult:
    """Convenience wrapper around the fixpoint result."""

    result: FixpointResult

    @property
    def state(self) -> State:
        return self.result.universe.state


def run_drug_lab(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    learning_rate: float = 0.18,
    epsilon: float = 1e-4,
    max_epoch: int = 256,
    observers: Optional[Sequence[Observer]] = None,
) -> DrugLabOptimisationResult:
    """Evolve the drug laboratory until it reaches a fixed point."""

    universe = ideal_drug_lab_universe(initial_state, learning_rate=learning_rate, observers=observers)
    result = fixpoint(universe, metric=drug_lab_metric, epsilon=epsilon, max_epoch=max_epoch)
    return DrugLabOptimisationResult(result)
