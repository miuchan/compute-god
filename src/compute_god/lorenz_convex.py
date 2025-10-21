r"""Convex objectives approximating the Lorenz attractor.

The classic Lorenz system is governed by the non-linear differential equations

``\dot x = \sigma (y - x)``,
``\dot y = x (\rho - z) - y``,
``\dot z = x y - \beta z``.

Even though the full attractor lives inside a chaotic region, its local
structure around the two non-trivial equilibria is well captured by the
*linearised* dynamics.  This module builds a convex quadratic objective
around a chosen equilibrium by squaring the linear residuals of the vector
field.  The resulting objective takes the form ``\tfrac{1}{2} d^T Q d``
with ``d`` the displacement from the equilibrium and ``Q`` positive definite,
making it suitable for standard convex optimisation techniques (gradient
descent, projected solvers, etc.).

Typical usage::

    >>> from compute_god.lorenz_convex import (
    ...     LorenzAttractorParameters,
    ...     build_lorenz_convex_objective,
    ... )
    >>> parameters = LorenzAttractorParameters()
    >>> objective = build_lorenz_convex_objective(parameters, wing=1)
    >>> objective.value(objective.centre)
    0.0

The convex potential exposes both :meth:`value` and :meth:`gradient`
evaluations.  The Hessian (precision matrix) is also available for users who
wish to plug the objective into second-order optimisers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence, Tuple

Vector3 = Tuple[float, float, float]


def _ensure_positive(value: float, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite positive number")
    if value <= 0:
        raise ValueError(f"{name} must be strictly positive")
    return float(value)


def _ensure_state(state: Sequence[float]) -> Vector3:
    if len(state) != 3:
        raise ValueError("state must contain exactly three components (x, y, z)")
    x, y, z = state
    for name, value in zip("xyz", (x, y, z)):
        if not math.isfinite(float(value)):
            raise ValueError(f"state component {name!r} must be finite")
    return (float(x), float(y), float(z))


@dataclass(frozen=True)
class LorenzAttractorParameters:
    """Physical parameters of the Lorenz system."""

    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "sigma", _ensure_positive(self.sigma, "sigma"))
        object.__setattr__(self, "rho", _ensure_positive(self.rho, "rho"))
        object.__setattr__(self, "beta", _ensure_positive(self.beta, "beta"))

    @property
    def wing_amplitude(self) -> float:
        """Return the distance of the non-trivial equilibria from the origin."""

        return math.sqrt(self.beta * max(self.rho - 1.0, 0.0))

    @property
    def wing_altitude(self) -> float:
        """Return the ``z`` coordinate of the non-trivial equilibria."""

        return self.rho - 1.0 if self.rho > 1.0 else 0.0

    def equilibria(self) -> Tuple[Vector3, Vector3, Vector3]:
        """Return the three equilibrium points of the Lorenz system."""

        amplitude = self.wing_amplitude
        altitude = self.wing_altitude
        if amplitude == 0.0:
            origin = (0.0, 0.0, 0.0)
            return origin, origin, origin
        positive = (amplitude, amplitude, altitude)
        negative = (-amplitude, -amplitude, altitude)
        origin = (0.0, 0.0, 0.0)
        return origin, positive, negative


def _build_precision_matrix(
    *,
    alignment_weight: float,
    radial_weight: float,
    vertical_weight: float,
    torsion_weight: float,
    amplitude: float,
    beta: float,
) -> Tuple[Tuple[float, float, float], ...]:
    vectors = (
        (-1.0, 1.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (amplitude, amplitude, -beta),
    )
    weights = (alignment_weight, radial_weight, vertical_weight, torsion_weight)
    matrix = [[0.0, 0.0, 0.0] for _ in range(3)]
    for weight, vector in zip(weights, vectors):
        for row in range(3):
            for col in range(3):
                matrix[row][col] += weight * vector[row] * vector[col]
    return tuple(tuple(value for value in row) for row in matrix)


@dataclass
class LorenzConvexObjective:
    """Quadratic potential centred at a Lorenz equilibrium."""

    parameters: LorenzAttractorParameters
    centre: Vector3
    wing: int
    alignment_weight: float
    radial_weight: float
    vertical_weight: float
    torsion_weight: float
    precision_matrix: Tuple[Tuple[float, float, float], ...] = field(init=False)

    def __post_init__(self) -> None:
        amplitude = abs(self.centre[0])
        self.precision_matrix = _build_precision_matrix(
            alignment_weight=self.alignment_weight,
            radial_weight=self.radial_weight,
            vertical_weight=self.vertical_weight,
            torsion_weight=self.torsion_weight,
            amplitude=amplitude,
            beta=self.parameters.beta,
        )

    def displacement(self, state: Sequence[float]) -> Vector3:
        """Return the displacement of ``state`` from the quadratic centre."""

        x, y, z = _ensure_state(state)
        cx, cy, cz = self.centre
        return (x - cx, y - cy, z - cz)

    def residuals(self, state: Sequence[float]) -> Tuple[float, float, float, float]:
        """Evaluate the linear residuals defining the convex objective."""

        dx, dy, dz = self.displacement(state)
        amplitude = abs(self.centre[0])
        alignment = dy - dx
        radial = dx + dy
        vertical = dz
        torsion = amplitude * radial - self.parameters.beta * dz
        return alignment, radial, vertical, torsion

    def value(self, state: Sequence[float]) -> float:
        """Return ``0.5 * d^T Q d`` for the displacement ``d`` of ``state``."""

        alignment, radial, vertical, torsion = self.residuals(state)
        return 0.5 * (
            self.alignment_weight * alignment * alignment
            + self.radial_weight * radial * radial
            + self.vertical_weight * vertical * vertical
            + self.torsion_weight * torsion * torsion
        )

    def gradient(self, state: Sequence[float]) -> Vector3:
        """Return the gradient of the convex potential at ``state``."""

        alignment, radial, vertical, torsion = self.residuals(state)
        amplitude = abs(self.centre[0])
        grad_x = (
            -self.alignment_weight * alignment
            + self.radial_weight * radial
            + self.torsion_weight * torsion * amplitude
        )
        grad_y = (
            self.alignment_weight * alignment
            + self.radial_weight * radial
            + self.torsion_weight * torsion * amplitude
        )
        grad_z = self.vertical_weight * vertical - self.torsion_weight * torsion * self.parameters.beta
        return grad_x, grad_y, grad_z


def build_lorenz_convex_objective(
    parameters: LorenzAttractorParameters,
    *,
    wing: int = 1,
    alignment_weight: float | None = None,
    radial_weight: float | None = None,
    vertical_weight: float | None = None,
    torsion_weight: float | None = None,
) -> LorenzConvexObjective:
    """Build a convex quadratic objective around a Lorenz equilibrium.

    Parameters
    ----------
    parameters:
        The physical constants of the Lorenz system.
    wing:
        Which equilibrium to linearise around.  ``1`` selects the positive wing,
        ``-1`` the negative wing and ``0`` falls back to the origin.  Any
        positive value maps to the positive wing, any negative value to the
        negative wing.
    alignment_weight, radial_weight, vertical_weight, torsion_weight:
        Optional positive weights scaling the squared residuals.  ``None``
        selects defaults that follow the Lorenz parameters so that the objective
        is well conditioned without user intervention.
    """

    amplitude = parameters.wing_amplitude
    altitude = parameters.wing_altitude

    if wing == 0 or amplitude == 0.0:
        centre = (0.0, 0.0, 0.0)
    else:
        sign = 1 if wing > 0 else -1
        centre = (sign * amplitude, sign * amplitude, altitude)

    default_alignment = parameters.sigma
    scale = amplitude if amplitude > 1.0 else 1.0
    default_radial = parameters.sigma / (2.0 * scale)
    default_vertical = parameters.beta
    default_torsion = max(parameters.beta / scale, 1.0 / scale)

    final_alignment = _ensure_positive(
        default_alignment if alignment_weight is None else alignment_weight,
        "alignment_weight",
    )
    final_radial = _ensure_positive(
        default_radial if radial_weight is None else radial_weight,
        "radial_weight",
    )
    final_vertical = _ensure_positive(
        default_vertical if vertical_weight is None else vertical_weight,
        "vertical_weight",
    )
    final_torsion = _ensure_positive(
        default_torsion if torsion_weight is None else torsion_weight,
        "torsion_weight",
    )

    return LorenzConvexObjective(
        parameters=parameters,
        centre=centre,
        wing=wing,
        alignment_weight=final_alignment,
        radial_weight=final_radial,
        vertical_weight=final_vertical,
        torsion_weight=final_torsion,
    )


__all__ = [
    "LorenzAttractorParameters",
    "LorenzConvexObjective",
    "build_lorenz_convex_objective",
]
