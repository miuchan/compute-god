"""Marketing funnel dynamics with monotone fixpoint guarantees.

This module offers a tiny but precise model for reasoning about the classical
"marketing concept" found in brand strategy literature.  We encode the funnel as
state transitions inside :mod:`compute_god` so that the convergence behaviour is
not hand-wavy: when the update rule is monotone on a compact lattice we can rely
on Kleene/Tarski style fixed-point theorems for existence and on the provided
``fixpoint`` engine for constructive computation.

The terminology intentionally mirrors the playful tone of the project while
remaining mathematically faithful.  The guarantees boil down to the following
simple facts:

* Each state is a mapping ``{"awareness", "engagement", "customers"}`` whose
  values live in ``[0, capacity]``.
* The update rule combines the previous state with non-negative coefficients,
  hence it is monotone with respect to the component-wise order.
* The state space with that order is a complete lattice; therefore the minimum
  fixed-point exists and can be constructed via Kleene iteration.

The rest of the module merely packages those ingredients so marketing teams can
speak about "ensured brand lift" using precise, inspectable mathematics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping

from .core import FixpointResult, God, Rule, State, Universe, fixpoint, rule


StateMapping = Mapping[str, float]
MutableState = MutableMapping[str, float]


@dataclass(frozen=True)
class FunnelParameters:
    """Coefficients governing a three-stage marketing funnel.

    The parameters are intentionally minimal yet expressive enough to recover
    common marketing levers:

    awareness_budget:
        Fraction of the remaining awareness capacity added at each epoch.  The
        value must lie in ``[0, 1]`` to keep the update monotone.
    engagement_rate:
        Share of awareness that becomes engaged.  Think of it as the combined
        effect of creative resonance and channel fit.
    conversion_rate:
        Fraction of engaged people who convert to customers per epoch.
    retention_rate:
        Share of existing customers that stay loyal during the epoch.
    capacities:
        Component-wise upper bounds for the state.  They define the lattice in
        which the map operates.  Defaults to ``1`` on each component which is
        enough for modelling ratios.
    """

    awareness_budget: float
    engagement_rate: float
    conversion_rate: float
    retention_rate: float
    capacities: StateMapping | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("awareness_budget", self.awareness_budget),
            ("engagement_rate", self.engagement_rate),
            ("conversion_rate", self.conversion_rate),
            ("retention_rate", self.retention_rate),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1], got {value!r}")

        if self.capacities is not None:
            for name, capacity in self.capacities.items():
                if capacity <= 0.0:
                    raise ValueError(f"capacity for {name!r} must be positive")

    def capacity(self, key: str) -> float:
        if self.capacities is None:
            return 1.0
        return self.capacities.get(key, 1.0)


def _clamp(value: float, upper: float) -> float:
    return max(0.0, min(upper, value))


def funnel_map(state: StateMapping, params: FunnelParameters) -> Dict[str, float]:
    """Return the next funnel state under ``params``.

    The map is affine with non-negative coefficients, therefore it is monotone
    under the component-wise order.  The outputs are clamped inside the declared
    capacities to maintain the lattice structure.
    """

    awareness_capacity = params.capacity("awareness")
    engagement_capacity = params.capacity("engagement")
    customer_capacity = params.capacity("customers")

    awareness = _clamp(
        (1.0 - params.awareness_budget) * state["awareness"]
        + params.awareness_budget * awareness_capacity,
        awareness_capacity,
    )
    engagement = _clamp(
        state["engagement"] * (1.0 - params.retention_rate)
        + params.engagement_rate * awareness,
        engagement_capacity,
    )
    customers = _clamp(
        state["customers"] * params.retention_rate
        + params.conversion_rate * engagement,
        customer_capacity,
    )

    return {
        "awareness": awareness,
        "engagement": engagement,
        "customers": customers,
    }


def marketing_rule(params: FunnelParameters) -> Rule:
    """Create the monotone rule that updates the marketing funnel."""

    def apply(state: State, _ctx) -> State:
        return funnel_map(state, params)

    return rule("marketing-funnel", apply)


def marketing_universe(
    initial_state: StateMapping,
    params: FunnelParameters,
) -> Universe:
    """Return a :class:`Universe` hosting the marketing funnel rule."""

    required_keys = {"awareness", "engagement", "customers"}
    missing = required_keys.difference(initial_state)
    if missing:
        raise KeyError(f"initial_state missing keys: {sorted(missing)!r}")

    state: MutableState = {
        "awareness": float(initial_state["awareness"]),
        "engagement": float(initial_state["engagement"]),
        "customers": float(initial_state["customers"]),
    }

    return God.universe(state=state, rules=[marketing_rule(params)])


def l1_metric(a: StateMapping, b: StateMapping) -> float:
    """Return the L1 distance between two funnel states."""

    return sum(abs(a[key] - b[key]) for key in ("awareness", "engagement", "customers"))


def marketing_fixpoint(
    initial_state: StateMapping,
    params: FunnelParameters,
    *,
    epsilon: float = 1e-6,
    max_epoch: int = 128,
) -> FixpointResult:
    """Compute the fixed-point of the marketing funnel map.

    The combination of :func:`marketing_universe` and :func:`fixpoint` turns the
    qualitative marketing narrative into a constructive guarantee: given the
    monotonicity of :func:`funnel_map`, the iteration converges to the minimum
    fixed-point, and the returned :class:`FixpointResult` records whether the
    convergence happened within the allotted epochs.
    """

    universe = marketing_universe(initial_state, params)
    return fixpoint(universe, metric=l1_metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "FunnelParameters",
    "funnel_map",
    "marketing_fixpoint",
    "marketing_rule",
    "marketing_universe",
    "l1_metric",
]
