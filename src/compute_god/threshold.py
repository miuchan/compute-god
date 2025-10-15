"""Convex optimisation primitives for liminal (threshold) spaces.

This module complements :mod:`compute_god.ctc` by providing a sibling data
structure that models **threshold spaces**—convex polytopes defined by
per-dimension lower/upper bounds together with an affine ``sum`` constraint.

The optimiser mirrors the ergonomics of
``optimise_closed_timelike_curve`` while swapping the projection step with a
bounded simplex projection.  The projection is implemented via the KKT
conditions of the quadratic programme resulting in a simple bisection on the
Lagrange multiplier.  No external dependencies are required and the
implementation remains numerically stable for typical machine precision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Sequence

Vector = List[float]


class _ProjectionError(ValueError):
    """Internal helper used to signal invalid projection parameters."""


def _ensure_finite(values: Iterable[float]) -> None:
    for value in values:
        if not math.isfinite(value):  # pragma: no cover - defensive
            raise ValueError("threshold values must be finite")


def _project_onto_threshold_simplex(
    values: Sequence[float],
    lower_bounds: Sequence[float],
    upper_bounds: Sequence[float],
    total: float,
    *,
    tolerance: float = 1e-9,
    max_iter: int = 128,
) -> Vector:
    """Project ``values`` onto ``{x | lower <= x <= upper, sum(x) = total}``."""

    if total <= 0:
        raise _ProjectionError("total must be positive when projecting")

    if not values:
        raise _ProjectionError("at least one dimension is required to project")

    if not (len(values) == len(lower_bounds) == len(upper_bounds)):
        raise _ProjectionError("dimension mismatch in threshold projection")

    _ensure_finite(values)
    _ensure_finite(lower_bounds)
    _ensure_finite(upper_bounds)

    lower_sum = sum(lower_bounds)
    upper_sum = sum(upper_bounds)

    if lower_sum > total + tolerance or upper_sum < total - tolerance:
        raise _ProjectionError("total is incompatible with provided bounds")

    # Degenerate case: the feasible set is a singleton.
    if math.isclose(lower_sum, upper_sum, rel_tol=0.0, abs_tol=tolerance):
        return [float(value) for value in lower_bounds]

    def clip_with_lambda(lagrange: float) -> Vector:
        clipped: Vector = []
        for value, low, high in zip(values, lower_bounds, upper_bounds):
            projected = value - lagrange
            if projected < low:
                projected = low
            elif projected > high:
                projected = high
            clipped.append(projected)
        return clipped

    lambda_low = min(value - high for value, high in zip(values, upper_bounds))
    lambda_high = max(value - low for value, low in zip(values, lower_bounds))

    projected = clip_with_lambda(0.5 * (lambda_low + lambda_high))
    for _ in range(max_iter):
        lambda_mid = 0.5 * (lambda_low + lambda_high)
        projected = clip_with_lambda(lambda_mid)
        current_sum = sum(projected)

        if abs(current_sum - total) <= tolerance:
            break

        if current_sum > total:
            lambda_low = lambda_mid
        else:
            lambda_high = lambda_mid
    else:  # pragma: no cover - defensive path
        projected = clip_with_lambda(lambda_high)

    # Normalise potential numerical drift to ensure the affine constraint holds.
    current_sum = sum(projected)
    if current_sum == 0:
        raise _ProjectionError("projection collapsed to zero vector")

    correction = total - current_sum
    if abs(correction) > tolerance:
        free_indices = [
            idx
            for idx, (value, low, high) in enumerate(
                zip(projected, lower_bounds, upper_bounds)
            )
            if low < value < high
        ]

        if not free_indices:
            # No interior points available; distribute to nearest feasible bounds.
            for idx in range(len(projected)):
                if correction == 0:
                    break
                capacity = upper_bounds[idx] - projected[idx] if correction > 0 else projected[idx] - lower_bounds[idx]
                delta = max(min(correction, capacity), -capacity)
                projected[idx] += delta
                correction -= delta
        else:
            adjustment = correction / len(free_indices)
            for idx in free_indices:
                projected[idx] += adjustment

    # Final clipping to guarantee compliance with bounds.
    final_vector = [
        min(max(value, low), high)
        for value, low, high in zip(projected, lower_bounds, upper_bounds)
    ]

    final_sum = sum(final_vector)
    if abs(final_sum - total) > 1e-6:  # pragma: no cover - defensive
        raise _ProjectionError("failed to project within tolerance")

    return final_vector


Objective = Callable[[Sequence[float]], tuple[float, Sequence[float]]]
Projection = Callable[[Sequence[float]], Vector]


@dataclass
class ThresholdSpace:
    """Representation of a convex threshold space."""

    lower_bounds: Sequence[float]
    upper_bounds: Sequence[float]
    total: float
    initial: Optional[Sequence[float]] = None
    _vector: Vector = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.total <= 0:
            raise ValueError("total must be strictly positive")

        if not self.lower_bounds or not self.upper_bounds:
            raise ValueError("threshold space requires at least one dimension")

        if len(self.lower_bounds) != len(self.upper_bounds):
            raise ValueError("lower and upper bounds must share the same dimension")

        for low, high in zip(self.lower_bounds, self.upper_bounds):
            if low > high:
                raise ValueError("lower bound cannot exceed upper bound")

        _ensure_finite(self.lower_bounds)
        _ensure_finite(self.upper_bounds)

        lower_sum = sum(self.lower_bounds)
        upper_sum = sum(self.upper_bounds)

        if not (lower_sum <= self.total <= upper_sum):
            raise ValueError("total must lie between the sum of bounds")

        initial = (
            list(self.initial)
            if self.initial is not None
            else [0.5 * (low + high) for low, high in zip(self.lower_bounds, self.upper_bounds)]
        )

        if len(initial) != len(self.lower_bounds):
            raise ValueError("initial vector dimension mismatch")

        _ensure_finite(initial)

        self._vector = _project_onto_threshold_simplex(
            initial, self.lower_bounds, self.upper_bounds, self.total
        )

    @property
    def dimension(self) -> int:
        return len(self._vector)

    def as_vector(self) -> Vector:
        return list(self._vector)

    def update(self, values: Sequence[float]) -> None:
        if len(values) != self.dimension:
            raise ValueError("dimension mismatch when updating threshold space")
        _ensure_finite(values)
        self._vector = _project_onto_threshold_simplex(
            values, self.lower_bounds, self.upper_bounds, self.total
        )


@dataclass
class ThresholdOptimisationResult:
    """Outcome of the convex optimisation on a threshold space."""

    space: ThresholdSpace
    objective_value: float
    iterations: int
    converged: bool


def optimise_threshold_space(
    space: ThresholdSpace,
    objective: Objective,
    *,
    learning_rate: float = 0.1,
    max_iter: int = 256,
    tolerance: float = 1e-6,
    projection: Optional[Projection] = None,
    callback: Optional[Callable[[int, Sequence[float], float], None]] = None,
) -> ThresholdOptimisationResult:
    """Perform projected gradient descent within a threshold space."""

    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if max_iter <= 0:
        raise ValueError("max_iter must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    current = space.as_vector()

    if projection is None:

        def projection(values: Sequence[float]) -> Vector:  # type: ignore[redefinition]
            return _project_onto_threshold_simplex(
                values, space.lower_bounds, space.upper_bounds, space.total
            )

    converged = False
    objective_value = math.inf

    for iteration in range(1, max_iter + 1):
        objective_value, gradient = objective(current)
        if len(gradient) != len(current):
            raise ValueError("objective gradient dimension mismatch")

        grad_norm = math.sqrt(sum(g * g for g in gradient))
        if grad_norm <= tolerance:
            converged = True
            if callback:
                callback(iteration, current, objective_value)
            break

        updated = [value - learning_rate * grad for value, grad in zip(current, gradient)]
        projected = projection(updated)

        delta = math.sqrt(sum((a - b) ** 2 for a, b in zip(projected, current)))
        current = projected
        space.update(current)

        if callback:
            callback(iteration, current, objective_value)

        if delta <= tolerance:
            converged = True
            break

    objective_value, _ = objective(space.as_vector())
    iterations = iteration if converged else max_iter

    return ThresholdOptimisationResult(
        space=space,
        objective_value=objective_value,
        iterations=iterations,
        converged=converged,
    )


__all__ = [
    "ThresholdSpace",
    "ThresholdOptimisationResult",
    "optimise_threshold_space",
]

