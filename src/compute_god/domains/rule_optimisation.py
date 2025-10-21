"""Convex optimisation utilities operating directly on rule ensembles.

This module complements :mod:`compute_god.rule` by providing a lightweight
quadratic programme that tunes the *mixture weights* associated with a set of
rules.  The idea is to treat the effect of each rule as a basis vector in the
space of numeric state variables.  Given a desired target state we solve the
convex problem

``minimise ½‖∑ᵢ wᵢ · Δᵢ - (target - state)‖²`` subject to ``w ∈ Δ``

where ``Δᵢ`` denotes the displacement induced by rule ``i`` and ``Δ`` is the
probability simplex with total mass ``total_weight``.  The resulting weights can
be fed back into higher level orchestration (e.g. to prioritise rules or to
schedule their application).

The implementation mirrors the ergonomics of other convex helpers in the
package.  Users call :func:`optimise_rule_weights` with the current numeric state
and a collection of rules.  The solver performs projected gradient descent on
the simplex, returning both the optimised weights and the synthesised state
obtained by blending the rule effects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Mapping, MutableMapping, Optional, Sequence

from compute_god.core import Rule

NumericState = Mapping[str, object]
Vector = List[float]

Callback = Callable[[int, Sequence[float], float], None]


class _StaticRuleContext:
    """Minimal context exposing the ``steps`` method expected by rules."""

    __slots__ = ()

    def steps(self) -> int:
        return 0


def _ensure_numeric_mapping(mapping: NumericState, name: str) -> MutableMapping[str, float]:
    numeric_state: MutableMapping[str, float] = {}
    for key, value in mapping.items():
        if not isinstance(key, str):
            raise TypeError(f"{name} keys must be strings; received {type(key)!r}")
        if isinstance(value, bool):
            numeric_state[key] = float(value)
        elif isinstance(value, (int, float)):
            numeric_state[key] = float(value)
        else:
            raise TypeError(
                f"{name} values must be numeric; key {key!r} has unsupported value {value!r}"
            )
    return numeric_state


def _vector_from_mapping(keys: Sequence[str], mapping: Mapping[str, float]) -> Vector:
    return [mapping.get(key, 0.0) for key in keys]


def _project_onto_simplex(values: Sequence[float], total: float) -> Vector:
    """Project ``values`` onto the simplex ``{w | w ≥ 0, ∑w = total}``."""

    if total <= 0:
        raise ValueError("total_weight must be strictly positive")
    if not values:
        raise ValueError("at least one weight is required for optimisation")

    sorted_values = sorted(values, reverse=True)
    cumulative = 0.0
    rho = -1
    theta = 0.0

    for idx, value in enumerate(sorted_values):
        cumulative += value
        candidate = (cumulative - total) / (idx + 1)
        if value - candidate > 0:
            rho = idx
            theta = candidate

    if rho == -1:
        theta = (sum(sorted_values) - total) / len(values)
    else:
        theta = (sum(sorted_values[: rho + 1]) - total) / (rho + 1)

    projected = [max(value - theta, 0.0) for value in values]
    current_sum = sum(projected)

    if not math.isclose(current_sum, total, rel_tol=1e-9, abs_tol=1e-9):
        if current_sum == 0:
            equal_weight = total / len(values)
            projected = [equal_weight for _ in values]
        else:
            scale = total / current_sum
            projected = [max(value * scale, 0.0) for value in projected]

    return projected


def _synthesise_state(
    base_vector: Sequence[float],
    deltas: Sequence[Sequence[float]],
    weights: Sequence[float],
) -> Vector:
    combined = list(base_vector)
    for weight, delta in zip(weights, deltas):
        for idx, component in enumerate(delta):
            combined[idx] += weight * component
    return combined


def _objective(
    deltas: Sequence[Sequence[float]],
    target_delta: Sequence[float],
    weights: Sequence[float],
) -> tuple[float, Vector]:
    residual = [
        sum(delta[idx] * weights[col] for col, delta in enumerate(deltas)) - target_value
        for idx, target_value in enumerate(target_delta)
    ]

    value = 0.5 * sum(component * component for component in residual)

    gradient: Vector = []
    for delta in deltas:
        gradient.append(sum(component * residual_value for component, residual_value in zip(delta, residual)))

    return value, gradient


@dataclass
class RuleOptimisationResult:
    """Outcome of the convex optimisation over rule mixtures."""

    weights: Vector
    state: Mapping[str, float]
    objective_value: float
    iterations: int
    converged: bool


def optimise_rule_weights(
    state: NumericState,
    rules: Sequence[Rule],
    target_state: NumericState,
    *,
    total_weight: float = 1.0,
    learning_rate: float = 0.2,
    max_iter: int = 512,
    tolerance: float = 1e-6,
    callback: Optional[Callback] = None,
) -> RuleOptimisationResult:
    """Optimise a convex combination of rule effects to match ``target_state``.

    Parameters
    ----------
    state:
        The current numeric state.  Only entries with numeric values are
        considered during optimisation.
    rules:
        Sequence of rules whose effects will be blended.  Each rule is evaluated
        once against ``state`` to extract its displacement vector.
    target_state:
        Desired numeric state.  Entries absent from ``state`` are assumed to be
        zero.
    total_weight:
        Total mass of the simplex the optimiser projects onto.  Defaults to
        ``1.0`` producing convex combinations of rule effects.
    learning_rate:
        Step size of the projected gradient descent.
    max_iter:
        Maximum number of gradient iterations.
    tolerance:
        Convergence tolerance applied both to the gradient norm and to the
        iterate displacement.
    callback:
        Optional callable receiving ``(iteration, weights, objective_value)`` at
        each iteration.
    """

    if not rules:
        raise ValueError("at least one rule is required to perform optimisation")
    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if max_iter <= 0:
        raise ValueError("max_iter must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    base_state = _ensure_numeric_mapping(state, "state")
    target_numeric = _ensure_numeric_mapping(target_state, "target_state")

    rule_states: List[MutableMapping[str, float]] = []
    keys = set(base_state.keys()) | set(target_numeric.keys())

    for rule in rules:
        context = _StaticRuleContext()
        rule_state = rule.apply(dict(base_state), context)
        if not isinstance(rule_state, MutableMapping):
            raise TypeError(
                f"rule {rule.name!r} must return a mutable mapping, received {type(rule_state)!r}"
            )
        numeric_rule_state = _ensure_numeric_mapping(rule_state, f"rule {rule.name!r} state")
        keys.update(numeric_rule_state.keys())
        rule_states.append(numeric_rule_state)

    ordered_keys = sorted(keys)
    base_vector = _vector_from_mapping(ordered_keys, base_state)
    target_vector = _vector_from_mapping(ordered_keys, target_numeric)
    target_delta = [target - base for target, base in zip(target_vector, base_vector)]

    deltas: List[Vector] = []
    for rule_state in rule_states:
        rule_vector = _vector_from_mapping(ordered_keys, rule_state)
        deltas.append([component - base for component, base in zip(rule_vector, base_vector)])

    weights = [total_weight / len(rules) for _ in rules]
    converged = False
    objective_value = math.inf

    for iteration in range(1, max_iter + 1):
        objective_value, gradient = _objective(deltas, target_delta, weights)
        grad_norm = math.sqrt(sum(component * component for component in gradient))

        if grad_norm <= tolerance:
            converged = True
            if callback:
                callback(iteration, list(weights), objective_value)
            break

        updated = [weight - learning_rate * grad for weight, grad in zip(weights, gradient)]
        projected = _project_onto_simplex(updated, total_weight)

        delta = math.sqrt(sum((new - old) ** 2 for new, old in zip(projected, weights)))
        weights = projected

        if callback:
            callback(iteration, list(weights), objective_value)

        if delta <= tolerance:
            converged = True
            break

    else:
        iteration = max_iter

    final_vector = _synthesise_state(base_vector, deltas, weights)
    objective_value, _ = _objective(deltas, target_delta, weights)

    result_state = {key: value for key, value in zip(ordered_keys, final_vector)}

    return RuleOptimisationResult(
        weights=list(weights),
        state=result_state,
        objective_value=objective_value,
        iterations=iteration if converged else max_iter,
        converged=converged,
    )


__all__ = ["RuleOptimisationResult", "optimise_rule_weights"]

