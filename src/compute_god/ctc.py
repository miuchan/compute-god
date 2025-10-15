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


def _project_onto_simplex(values: Sequence[float], total: float) -> Vector:
    """Project ``values`` onto the simplex ``{x >= 0, sum(x) = total}``."""

    if total <= 0:
        raise _ProjectionError("total must be positive when projecting")
    if not values:
        raise _ProjectionError("at least one segment is required to project")

    _ensure_finite(values)

    # Algorithm adapted from "Efficient Projections onto the l1-Ball for
    # Learning in High Dimensions" by Duchi et al.  The values are sorted in
    # descending order to find the appropriate threshold.
    sorted_values = sorted(values, reverse=True)
    cumulative = 0.0
    rho = 0
    theta = 0.0

    for idx, value in enumerate(sorted_values, 1):
        cumulative += value
        candidate = (cumulative - total) / idx
        if value - candidate > 0:
            rho = idx
            theta = candidate

    if rho == 0:
        # All values are effectively zero or negative; fall back to a uniform
        # distribution on the simplex.
        uniform = total / len(values)
        return [uniform for _ in values]

    theta = (sum(sorted_values[:rho]) - total) / rho
    projected = [max(v - theta, 0.0) for v in values]

    # Numerical drift might cause the sum to differ slightly from ``total``.
    projected_sum = sum(projected)
    if projected_sum == 0:
        uniform = total / len(values)
        projected = [uniform for _ in values]
    else:
        scale = total / projected_sum
        projected = [v * scale for v in projected]

    return projected


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
    _vector: Vector = field(init=False, repr=False)

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
        self._renormalise()

    def _renormalise(self) -> None:
        projected = _project_onto_simplex(self._vector, self.period)
        self._vector = projected

    @property
    def dimension(self) -> int:
        """Number of segments describing the curve."""

        return len(self._vector)

    def as_vector(self) -> Vector:
        """Return a defensive copy of the current segment weights."""

        return list(self._vector)

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
            return _project_onto_simplex(values, curve.period)

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

