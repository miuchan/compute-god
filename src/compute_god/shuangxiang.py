"""Biphasic gradient descent utilities nicknamed ``双相``.

The project enjoys playful terminology when introducing new helpers.  In that
spirit ``shuangxiang`` (双相) models a tiny two-phase system driven by a hot and
cold value.  The module purposefully keeps the representation lightweight so it
can be used in pedagogical examples without pulling in a full optimisation
stack.

At its core the module exposes :class:`BiphasicState` together with a projected
gradient descent routine.  The optimiser mirrors the style of similar helpers in
the code base: callers supply an objective returning both its value and gradient
for the current state.  The solver then performs simple gradient updates,
optionally passing them through a projection to respect custom constraints
before mutating the state in place.  A result dataclass captures the outcome so
callers can inspect whether the run converged, how many iterations it took and
what objective value was achieved.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

Vector = Sequence[float]
Objective = Callable[["BiphasicState"], Tuple[float, Tuple[float, float]]]
Projection = Callable[[Vector], Tuple[float, float]]
Callback = Callable[[int, "BiphasicState", float], None]


@dataclass
class BiphasicState:
    """Represent the hot and cold components of a two-phase system."""

    hot: float
    cold: float

    def as_tuple(self) -> Tuple[float, float]:
        """Return the state as a plain tuple."""

        return (float(self.hot), float(self.cold))

    def copy(self) -> "BiphasicState":
        """Return a defensive copy of the state."""

        return BiphasicState(hot=float(self.hot), cold=float(self.cold))

    def update(self, values: Sequence[float]) -> None:
        """Replace the hot and cold values using ``values``."""

        if len(values) != 2:
            raise ValueError("biphasic state update expects two values")
        hot, cold = float(values[0]), float(values[1])
        if not math.isfinite(hot) or not math.isfinite(cold):
            raise ValueError("biphasic state must remain finite")
        self.hot = hot
        self.cold = cold

    @property
    def gap(self) -> float:
        """Return the temperature gap between the phases."""

        return float(self.hot - self.cold)

    @property
    def equilibrium(self) -> float:
        """Return the midpoint between the hot and cold phases."""

        return float((self.hot + self.cold) / 2.0)


@dataclass(frozen=True)
class BiphasicOptimisationResult:
    """Outcome of optimising a :class:`BiphasicState`."""

    state: BiphasicState
    objective_value: float
    iterations: int
    converged: bool


def optimise_biphasic_state(
    state: BiphasicState,
    objective: Objective,
    *,
    learning_rate: float = 0.1,
    max_iter: int = 256,
    tolerance: float = 1e-6,
    projection: Optional[Projection] = None,
    callback: Optional[Callback] = None,
) -> BiphasicOptimisationResult:
    """Perform projected gradient descent on a biphasic state."""

    if learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if max_iter <= 0:
        raise ValueError("max_iter must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    current = list(state.as_tuple())
    objective_value = math.inf
    converged = False

    for iteration in range(1, max_iter + 1):
        candidate = BiphasicState(hot=current[0], cold=current[1])
        objective_value, gradient = objective(candidate)

        if len(gradient) != 2:
            raise ValueError("objective gradient dimension mismatch")

        grad_norm = math.sqrt(sum(component * component for component in gradient))
        if grad_norm <= tolerance:
            state.update(candidate.as_tuple())
            if callback is not None:
                callback(iteration, state.copy(), objective_value)
            converged = True
            break

        updated = [
            value - learning_rate * grad for value, grad in zip(current, gradient)
        ]

        if projection is None:
            projected = (float(updated[0]), float(updated[1]))
        else:
            projected = projection(updated)
            if len(projected) != 2:
                raise ValueError("projection must return two values")
            projected = (float(projected[0]), float(projected[1]))

        delta = math.sqrt(sum((a - b) ** 2 for a, b in zip(projected, current)))
        current = [projected[0], projected[1]]
        state.update(current)

        if callback is not None:
            callback(iteration, state.copy(), objective_value)

        if delta <= tolerance:
            converged = True
            break

    return BiphasicOptimisationResult(
        state=state.copy(),
        objective_value=float(objective_value),
        iterations=iteration if "iteration" in locals() else 0,
        converged=converged,
    )


# Playful aliases embracing the poetic API surface.
双相 = BiphasicState
双相梯度下降 = optimise_biphasic_state


__all__ = [
    "BiphasicState",
    "BiphasicOptimisationResult",
    "optimise_biphasic_state",
    "双相",
    "双相梯度下降",
]

