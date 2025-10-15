"""Convex optimisation for a relaxed variant of Conway's Game of Life.

The classic Game of Life evolves a binary lattice using non-linear birth and
survival rules.  This module provides a *convex* relaxation of that dynamics:
cells are allowed to take values in ``[0, 1]`` and the discrete update is
approximated by a linear response operator that mixes each cell with the
average activity of its Moore neighbourhood.  The relaxation admits an
objective of the form ``\frac{1}{2}‖A x - b‖²`` which is convex in the state
vector ``x``.  We can therefore recover latent configurations by running
projected gradient descent inside the hypercube ``[0, 1]^{HW}``.

The ergonomics mirror the rest of the convex optimisation utilities in
``compute_god``: the lattice is represented by :class:`LifeLattice`, the solver
returns a :class:`LifeOptimisationResult`, and the main entry point
(:func:`optimise_game_of_life`) accepts an optional callback for diagnostics.

The relaxation is intentionally simple yet expressive enough for experiments:

* ``survival_weight`` controls how much the current cell value influences the
  relaxed update (preserving existing life).
* ``birth_weight`` scales the contribution of neighbours (encouraging new
  births when three neighbours are active).

Together they form the affine operator ``response = s · x + b · (N x / 3)``
where ``N`` is the neighbour-incidence matrix of the lattice.  Setting
``survival_weight + birth_weight = 1`` yields an intuitive interpolation between
pure survival and pure birth dynamics, though the optimiser does not enforce
that restriction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence

Vector = List[float]
Matrix = List[List[float]]

Callback = Callable[[int, Matrix, float], None]


def _ensure_dimension(value: int, name: str) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _ensure_probability(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("lattice values must be finite")
    if value < 0.0 or value > 1.0:
        raise ValueError("lattice values must lie within [0, 1]")
    return float(value)


def _to_vector(height: int, width: int, state: Optional[Sequence[Sequence[float]] | Sequence[float]]) -> Vector:
    size = height * width
    if state is None:
        return [0.0 for _ in range(size)]

    if len(state) == size and not any(isinstance(value, Sequence) for value in state):
        return [_ensure_probability(float(value)) for value in state]  # type: ignore[arg-type]

    if len(state) != height:
        raise ValueError("two-dimensional initial state must match lattice height")

    vector: Vector = []
    for row in state:  # type: ignore[assignment]
        if len(row) != width:  # type: ignore[arg-type]
            raise ValueError("two-dimensional initial state must match lattice width")
        vector.extend(_ensure_probability(float(value)) for value in row)  # type: ignore[arg-type]
    return vector


def _reshape(vector: Sequence[float], width: int) -> Matrix:
    return [list(vector[row_start : row_start + width]) for row_start in range(0, len(vector), width)]


def _build_neighbourhood(height: int, width: int) -> List[List[int]]:
    neighbours: List[List[int]] = []
    for row in range(height):
        for col in range(width):
            indices: List[int] = []
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr = row + dr
                    cc = col + dc
                    if 0 <= rr < height and 0 <= cc < width:
                        indices.append(rr * width + cc)
            neighbours.append(indices)
    return neighbours


def _life_linear_response(
    vector: Sequence[float],
    neighbours: Sequence[Sequence[int]],
    *,
    survival_weight: float,
    birth_weight: float,
) -> Vector:
    neighbour_factor = birth_weight / 3.0
    response: Vector = []
    for value, adjacent in zip(vector, neighbours):
        neighbour_sum = sum(vector[index] for index in adjacent)
        response.append(survival_weight * value + neighbour_factor * neighbour_sum)
    return response


def _life_objective(
    vector: Sequence[float],
    target: Sequence[float],
    neighbours: Sequence[Sequence[int]],
    *,
    survival_weight: float,
    birth_weight: float,
) -> tuple[float, Vector]:
    response = _life_linear_response(
        vector, neighbours, survival_weight=survival_weight, birth_weight=birth_weight
    )
    residual = [current - target_value for current, target_value in zip(response, target)]

    value = 0.5 * sum(res * res for res in residual)

    gradient = [survival_weight * res for res in residual]
    neighbour_factor = birth_weight / 3.0
    for cell_index, adjacent in enumerate(neighbours):
        contribution = neighbour_factor * residual[cell_index]
        for neighbour_index in adjacent:
            gradient[neighbour_index] += contribution
    return value, gradient


@dataclass
class LifeLattice:
    """Representation of a relaxed Game of Life lattice."""

    height: int
    width: int
    initial_state: Optional[Sequence[Sequence[float]] | Sequence[float]] = None
    _state: Vector = field(init=False, repr=False)
    _neighbours: List[List[int]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.height = _ensure_dimension(self.height, "height")
        self.width = _ensure_dimension(self.width, "width")
        self._state = _to_vector(self.height, self.width, self.initial_state)
        self._neighbours = _build_neighbourhood(self.height, self.width)

    @property
    def dimension(self) -> int:
        return self.height * self.width

    def as_vector(self) -> Vector:
        return list(self._state)

    def as_matrix(self) -> Matrix:
        return _reshape(self._state, self.width)

    def neighbours(self) -> Sequence[Sequence[int]]:
        return self._neighbours

    def update(self, values: Sequence[float]) -> None:
        if len(values) != self.dimension:
            raise ValueError("dimension mismatch when updating lattice state")
        self._state = [_ensure_probability(float(value)) for value in values]

    def relaxed_step(self, *, survival_weight: float, birth_weight: float) -> Matrix:
        response = _life_linear_response(
            self._state, self._neighbours, survival_weight=survival_weight, birth_weight=birth_weight
        )
        return _reshape(response, self.width)


@dataclass
class LifeOptimisationResult:
    """Outcome of the convex optimisation on a Life lattice."""

    lattice: LifeLattice
    objective_value: float
    iterations: int
    converged: bool


def optimise_game_of_life(
    lattice: LifeLattice,
    target_state: Sequence[Sequence[float]] | Sequence[float],
    *,
    survival_weight: float = 0.6,
    birth_weight: float = 0.4,
    learning_rate: float = 0.2,
    max_iter: int = 512,
    tolerance: float = 1e-6,
    callback: Optional[Callback] = None,
) -> LifeOptimisationResult:
    """Perform projected gradient descent on the relaxed Life lattice."""

    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if max_iter <= 0:
        raise ValueError("max_iter must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    target = _to_vector(lattice.height, lattice.width, target_state)

    current = lattice.as_vector()
    neighbours = lattice.neighbours()

    converged = False
    objective_value = math.inf

    for iteration in range(1, max_iter + 1):
        objective_value, gradient = _life_objective(
            current,
            target,
            neighbours,
            survival_weight=survival_weight,
            birth_weight=birth_weight,
        )

        grad_norm = math.sqrt(sum(component * component for component in gradient))
        if grad_norm <= tolerance:
            converged = True
            if callback:
                callback(iteration, _reshape(current, lattice.width), objective_value)
            break

        updated = [value - learning_rate * grad for value, grad in zip(current, gradient)]
        projected = [min(max(value, 0.0), 1.0) for value in updated]

        delta = math.sqrt(sum((a - b) ** 2 for a, b in zip(projected, current)))
        current = projected
        lattice.update(current)

        if callback:
            callback(iteration, lattice.as_matrix(), objective_value)

        if delta <= tolerance:
            converged = True
            break

    final_vector = lattice.as_vector()
    objective_value, _ = _life_objective(
        final_vector,
        target,
        neighbours,
        survival_weight=survival_weight,
        birth_weight=birth_weight,
    )

    iterations = iteration if converged else max_iter

    return LifeOptimisationResult(
        lattice=lattice,
        objective_value=objective_value,
        iterations=iterations,
        converged=converged,
    )


__all__ = [
    "LifeLattice",
    "LifeOptimisationResult",
    "optimise_game_of_life",
]

