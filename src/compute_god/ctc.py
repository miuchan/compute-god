"""Convex optimisation helpers for closed timelike curves.

This module introduces a tiny utility for modelling **closed timelike curves**
as convex optimisation problems.  While the physical terminology is playful,
the implementation is intentionally pragmatic: a curve is represented by a set
of positive segment weights whose total equals the period of the loop.  The
optimiser performs projected gradient descent on those weights whilst keeping
the curve closed (i.e. the weights remain on the probability simplex scaled by
the desired period).

The interface is deliberately lightweight so it can be plugged into the rest of
the Compute-God ecosystem.  Users define a convex objective function that
returns both its value and gradient.  The optimiser takes care of the projection
step, guaranteeing that the iterates remain within the convex set describing
the closed timelike curve.
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
            raise ValueError("segment values must be finite")


def _project_onto_bounded_simplex(
    values: Sequence[float],
    total: float,
    lower_bounds: Sequence[float],
    upper_bounds: Sequence[float],
    *,
    tolerance: float = 1e-9,
    max_iter: int = 128,
) -> Vector:
    """Project ``values`` onto ``{x | lower <= x <= upper, sum(x) = total}``."""

    if total <= 0:
        raise _ProjectionError("total must be positive when projecting")
    if not values:
        raise _ProjectionError("at least one segment is required to project")

    if not (len(values) == len(lower_bounds) == len(upper_bounds)):
        raise _ProjectionError("dimension mismatch in projection")

    _ensure_finite(values)
    _ensure_finite(lower_bounds)

    # ``upper_bounds`` may contain infinities; filter them lazily when needed.
    for low, high in zip(lower_bounds, upper_bounds):
        if high < low:
            raise _ProjectionError("upper bound must be at least as large as lower bound")

    lower_sum = sum(lower_bounds)
    if lower_sum > total + tolerance:
        raise _ProjectionError("total is incompatible with lower bounds")

    finite_upper = [high for high in upper_bounds if math.isfinite(high)]
    if finite_upper and sum(finite_upper) < total - tolerance:
        raise _ProjectionError("total exceeds the sum of finite upper bounds")

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

    def sum_with_lambda(lagrange: float) -> tuple[float, Vector]:
        clipped = clip_with_lambda(lagrange)
        return sum(clipped), clipped

    lambda_low_candidates = [
        value - high
        for value, high in zip(values, upper_bounds)
        if math.isfinite(high)
    ]
    if lambda_low_candidates:
        lambda_low = min(lambda_low_candidates)
    else:
        lambda_low = min(values) - total

    lambda_high = max(value - low for value, low in zip(values, lower_bounds))

    sum_low, projected_low = sum_with_lambda(lambda_low)
    adjust_iter = 0
    while sum_low < total and adjust_iter < max_iter:
        step = max(1.0, abs(lambda_low))
        lambda_low -= step
        sum_low, projected_low = sum_with_lambda(lambda_low)
        adjust_iter += 1
    if sum_low < total - tolerance:
        raise _ProjectionError("failed to bracket projection from below")

    sum_high, projected_high = sum_with_lambda(lambda_high)
    adjust_iter = 0
    while sum_high > total and adjust_iter < max_iter:
        step = max(1.0, abs(lambda_high))
        lambda_high += step
        sum_high, projected_high = sum_with_lambda(lambda_high)
        adjust_iter += 1
    if sum_high > total + tolerance:
        raise _ProjectionError("failed to bracket projection from above")

    projected = projected_low
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

    current_sum = sum(projected)
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
            for idx in range(len(projected)):
                if abs(correction) <= tolerance:
                    break
                low, high = lower_bounds[idx], upper_bounds[idx]
                capacity = (high - projected[idx]) if correction > 0 else (projected[idx] - low)
                capacity = max(capacity, 0.0)
                delta = max(min(correction, capacity), -capacity)
                projected[idx] += delta
                correction -= delta
        else:
            adjustment = correction / len(free_indices)
            for idx in free_indices:
                projected[idx] += adjustment

    final_vector = [
        min(max(value, low), high)
        for value, low, high in zip(projected, lower_bounds, upper_bounds)
    ]

    final_sum = sum(final_vector)
    if abs(final_sum - total) > 1e-6:  # pragma: no cover - defensive
        raise _ProjectionError("projection failed to satisfy affine constraint")

    return final_vector


def _project_onto_simplex(values: Sequence[float], total: float) -> Vector:
    lower = [0.0 for _ in values]
    upper = [math.inf for _ in values]
    return _project_onto_bounded_simplex(values, total, lower, upper)


Objective = Callable[[Sequence[float]], tuple[float, Sequence[float]]]
Projection = Callable[[Sequence[float]], Vector]


@dataclass
class ClosedTimelikeCurve:
    """Representation of a discretised closed timelike curve.

    Parameters
    ----------
    segments:
        Positive weights associated with each segment of the curve.  The values
        are normalised so that their sum matches ``period``.
    period:
        Total proper time of the curve.  Must be strictly positive.
    """

    segments: Sequence[float]
    period: float
    lower_bounds: Optional[Sequence[float]] = None
    upper_bounds: Optional[Sequence[float]] = None
    _vector: Vector = field(init=False, repr=False)
    _lower_bounds: Vector = field(init=False, repr=False)
    _upper_bounds: List[float] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("period must be strictly positive")
        if not self.segments:
            raise ValueError("a closed timelike curve requires at least one segment")
        _ensure_finite(self.segments)

        total = sum(self.segments)
        if total <= 0:
            raise ValueError("segment weights must sum to a positive value")

        scale = self.period / total
        self._vector = [max(value * scale, 0.0) for value in self.segments]

        dimension = len(self.segments)
        lower = (
            list(self.lower_bounds)
            if self.lower_bounds is not None
            else [0.0 for _ in range(dimension)]
        )
        upper = (
            list(self.upper_bounds)
            if self.upper_bounds is not None
            else [math.inf for _ in range(dimension)]
        )

        if len(lower) != dimension or len(upper) != dimension:
            raise ValueError("bounds must match the number of segments")

        _ensure_finite(lower)
        for value in upper:
            if not math.isfinite(value) and not math.isinf(value):
                raise ValueError("upper bounds must be finite or infinity")

        for low, high in zip(lower, upper):
            if high < low:
                raise ValueError("upper bound must exceed lower bound")

        lower_sum = sum(lower)
        if lower_sum > self.period + 1e-9:
            raise ValueError("period is incompatible with provided lower bounds")

        finite_upper = [value for value in upper if math.isfinite(value)]
        if finite_upper and sum(finite_upper) < self.period - 1e-9:
            raise ValueError("period exceeds the sum of finite upper bounds")

        self._lower_bounds = lower
        self._upper_bounds = upper
        self._renormalise()

    def _renormalise(self) -> None:
        self._vector = self._project(self._vector)

    def _project(self, values: Sequence[float]) -> Vector:
        return _project_onto_bounded_simplex(
            values, self.period, self._lower_bounds, self._upper_bounds
        )

    @property
    def dimension(self) -> int:
        """Number of segments describing the curve."""

        return len(self._vector)

    def as_vector(self) -> Vector:
        """Return a defensive copy of the current segment weights."""

        return list(self._vector)

    @property
    def lower(self) -> Vector:
        """Return defensive copy of the lower bounds."""

        return list(self._lower_bounds)

    @property
    def upper(self) -> List[float]:
        """Return defensive copy of the upper bounds."""

        return list(self._upper_bounds)

    def update(self, values: Sequence[float]) -> None:
        """Replace the segment weights and renormalise onto the simplex."""

        if len(values) != self.dimension:
            raise ValueError("dimension mismatch when updating curve")
        _ensure_finite(values)
        self._vector = list(values)
        self._renormalise()


@dataclass
class CTCOptimisationResult:
    """Outcome of the convex optimisation on a closed timelike curve."""

    curve: ClosedTimelikeCurve
    objective_value: float
    iterations: int
    converged: bool


def optimise_closed_timelike_curve(
    curve: ClosedTimelikeCurve,
    objective: Objective,
    *,
    learning_rate: float = 0.1,
    max_iter: int = 256,
    tolerance: float = 1e-6,
    projection: Optional[Projection] = None,
    callback: Optional[Callable[[int, Sequence[float], float], None]] = None,
) -> CTCOptimisationResult:
    """Perform projected gradient descent on a closed timelike curve.

    Parameters
    ----------
    curve:
        Closed timelike curve to optimise.  The curve is updated in-place.
    objective:
        Callable returning both the objective value and its gradient for a given
        vector of segment weights.
    learning_rate:
        Step size used by the gradient descent updates.  Must be positive.
    max_iter:
        Maximum number of iterations to perform.
    tolerance:
        Threshold for both the gradient norm and the update magnitude used to
        determine convergence.
    projection:
        Optional projection callable.  When omitted, the optimiser projects onto
        the simplex implied by the curve's period.
    callback:
        Optional callable invoked after each iteration.  Receives the iteration
        number (starting at one), the current segment vector and the objective
        value.
    """

    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if max_iter <= 0:
        raise ValueError("max_iter must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    current = curve.as_vector()

    if projection is None:

        def projection(values: Sequence[float]) -> Vector:  # type: ignore[redefinition]
            return curve._project(values)

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
        curve.update(current)

        if callback:
            callback(iteration, current, objective_value)

        if delta <= tolerance:
            converged = True
            break

    # Ensure the objective value reflects the final iterate.
    objective_value, _ = objective(curve.as_vector())
    iterations = iteration if converged else max_iter

    return CTCOptimisationResult(
        curve=curve,
        objective_value=objective_value,
        iterations=iterations,
        converged=converged,
    )


__all__ = [
    "ClosedTimelikeCurve",
    "CTCOptimisationResult",
    "optimise_closed_timelike_curve",
]

