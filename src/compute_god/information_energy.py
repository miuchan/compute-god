"""Information energy field utilities for stable gradient descent guidance.

The :mod:`information_energy` module weaves a narrative of "information energy"
into the concrete optimisation primitives of the Compute-God runtime.  The
goal is to turn raw gradient descent into a guided ritual – one that balances
stability, delight, and energy efficiency while navigating complex landscapes.

Two core abstractions implement this idea:

``EnergyField``
    Wraps a potential function describing the information energy surface.  The
    field normalises gradients, enforces smoothness, and tracks how much energy
    is available for the descent.

``EnergyDescentNavigator``
    Orchestrates a momentum-informed gradient descent across the field.  The
    navigator adapts the step size to keep the trajectory smooth and natural,
    emitting :class:`DescentStep` records that capture every move.

Together they make it easy to express optimisation problems in the poetic
language used throughout the project while still behaving predictably in unit
tests and when driving universes.  The implementation intentionally avoids
external dependencies and keeps the API functional-programming friendly so it
slots into the existing guidance desk catalogue without friction.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Callable, Sequence

Vector = tuple[float, ...]
PotentialFn = Callable[[Sequence[float]], float]
GradientFn = Callable[[Sequence[float]], Sequence[float]]


def _normalise(vector: Sequence[float], *, epsilon: float = 1e-12) -> Vector:
    norm = sqrt(sum(component * component for component in vector))
    if norm <= epsilon:
        return tuple(0.0 for _ in vector)
    scale = 1.0 / norm
    return tuple(component * scale for component in vector)


def _ensure_tuple(position: Sequence[float]) -> Vector:
    return tuple(float(component) for component in position)


@dataclass(frozen=True)
class DescentStep:
    """Snapshot of a single descent move across the information field."""

    position: Vector
    energy: float
    gradient: Vector
    step_size: float


@dataclass(frozen=True)
class DescentPath:
    """Collection of descent steps plus metadata about the journey."""

    steps: tuple[DescentStep, ...]
    converged: bool
    total_energy_drop: float
    total_distance: float

    def positions(self) -> tuple[Vector, ...]:
        """Return the ordered positions visited during the descent."""

        return tuple(step.position for step in self.steps)


class EnergyField:
    """Energy landscape used for guiding gradient descent paths.

    Parameters
    ----------
    potential:
        Callable returning the scalar energy at a given position.
    gradient:
        Optional analytical gradient.  When not provided the field falls back
        to a central-difference estimate controlled by ``smoothness``.
    smoothness:
        Finite-difference scale used for numerical gradients.
    energy_budget:
        Total amount of energy the navigator is allowed to consume.  The budget
        is represented as the cumulative energy drop along the path.
    """

    def __init__(
        self,
        potential: PotentialFn,
        *,
        gradient: GradientFn | None = None,
        smoothness: float = 1e-4,
        energy_budget: float = float("inf"),
    ) -> None:
        self._potential = potential
        self._gradient = gradient
        self._smoothness = smoothness
        self._energy_budget = energy_budget

    def energy(self, position: Sequence[float]) -> float:
        """Return the energy at ``position``."""

        return float(self._potential(position))

    def gradient(self, position: Sequence[float]) -> Vector:
        """Return the normalised gradient at ``position``."""

        if self._gradient is not None:
            raw_gradient = self._gradient(position)
        else:
            raw_gradient = self._finite_difference_gradient(position)
        return _normalise(raw_gradient)

    def energy_budget(self) -> float:
        """Return the remaining energy budget."""

        return self._energy_budget

    def _finite_difference_gradient(self, position: Sequence[float]) -> Vector:
        baseline = self.energy(position)
        result = []
        for index, component in enumerate(position):
            delta = self._smoothness
            forward = list(position)
            backward = list(position)
            forward[index] = component + delta
            backward[index] = component - delta
            gradient_component = (self.energy(forward) - self.energy(backward)) / (2 * delta)
            result.append(gradient_component)
        return tuple(result)


class EnergyDescentNavigator:
    """Plan an energy-aware gradient descent within an :class:`EnergyField`."""

    def __init__(
        self,
        field: EnergyField,
        *,
        step_size: float = 0.2,
        damping: float = 0.7,
        naturality: float = 0.5,
    ) -> None:
        if not 0.0 <= damping < 1.0:
            raise ValueError("damping must be in [0, 1)")
        if step_size <= 0:
            raise ValueError("step_size must be positive")
        if naturality <= 0:
            raise ValueError("naturality must be positive")
        self._field = field
        self._step_size = step_size
        self._damping = damping
        self._naturality = naturality

    def descend(
        self,
        start: Sequence[float],
        *,
        max_steps: int = 128,
        tolerance: float = 1e-6,
    ) -> DescentPath:
        """Execute a gradient descent and capture the resulting path."""

        position = _ensure_tuple(start)
        steps: list[DescentStep] = []
        momentum = tuple(0.0 for _ in position)
        previous_energy = self._field.energy(position)
        total_drop = 0.0
        total_distance = 0.0

        for _ in range(max_steps):
            gradient = self._field.gradient(position)
            gradient_norm = sqrt(sum(component * component for component in gradient))
            if gradient_norm <= tolerance:
                break

            momentum = tuple(
                self._damping * prev + (1.0 - self._damping) * component
                for prev, component in zip(momentum, gradient)
            )
            step_scale = self._adaptive_step(previous_energy)
            step_vector = tuple(step_scale * value for value in momentum)
            new_position = tuple(coord - self._step_size * step for coord, step in zip(position, step_vector))
            new_energy = self._field.energy(new_position)

            if new_energy > previous_energy:
                fallback_scale = step_scale
                trial_position = new_position
                trial_energy = new_energy
                while trial_energy > previous_energy and fallback_scale > tolerance:
                    fallback_scale *= 0.5
                    trial_position = tuple(
                        coord - self._step_size * fallback_scale * component
                        for coord, component in zip(position, gradient)
                    )
                    trial_energy = self._field.energy(trial_position)
                new_position = trial_position
                new_energy = trial_energy

            energy_drop = max(0.0, previous_energy - new_energy)
            total_drop += energy_drop
            total_distance += sqrt(sum((a - b) ** 2 for a, b in zip(position, new_position)))

            steps.append(
                DescentStep(
                    position=new_position,
                    energy=new_energy,
                    gradient=gradient,
                    step_size=step_scale,
                )
            )

            if total_drop >= self._field.energy_budget():
                break

            if abs(energy_drop) <= tolerance:
                break

            position = new_position
            previous_energy = new_energy

        converged = bool(steps) and (abs(previous_energy - steps[-1].energy) <= tolerance)
        return DescentPath(
            steps=tuple(steps),
            converged=converged,
            total_energy_drop=total_drop,
            total_distance=total_distance,
        )

    def _adaptive_step(self, current_energy: float) -> float:
        modifier = 1.0 / (1.0 + self._naturality * max(0.0, current_energy))
        return self._step_size * modifier


def plan_energy_descent(
    potential: PotentialFn,
    start: Sequence[float],
    *,
    gradient: GradientFn | None = None,
    energy_budget: float = float("inf"),
    max_steps: int = 128,
) -> DescentPath:
    """Helper for running a guided gradient descent in the information field."""

    field = EnergyField(potential, gradient=gradient, energy_budget=energy_budget)
    navigator = EnergyDescentNavigator(field)
    return navigator.descend(start, max_steps=max_steps)


__all__ = [
    "DescentPath",
    "DescentStep",
    "EnergyDescentNavigator",
    "EnergyField",
    "plan_energy_descent",
]

