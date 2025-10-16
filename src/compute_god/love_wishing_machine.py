"""A playful yet precise implementation of the "爱情许愿机" (love wishing machine).

The module follows the same pattern as other :mod:`compute_god` helpers: it
captures a poetic narrative – here the ritual of making a love wish – inside a
monotone map hosted by the :class:`~compute_god.universe.Universe`.  Once the
map is monotone on a compact lattice, the Kleene construction guarantees a
minimum fixed-point and the core :func:`~compute_god.engine.fixpoint` routine
constructively finds it.

Conceptually the machine tracks four coupled quantities:

``self_love``
    How much the wisher has tended to their own garden.  Growth is fuelled by
    deliberate cultivation and a gentle reflection of the accumulated blessing.
``openness``
    Willingness to connect.  Patience tempers it while sincerity channels
    self-love outward.
``resonance``
    The shared vibration between the wisher and the world.  It retains part of
    its previous value and rises with the lesser of self-love and openness –
    because resonance demands balance.
``blessing``
    The ambient support perceived after each wishing ritual.  It feeds on
    resonance and slowly dissipates according to the release rate.

All updates use non-negative coefficients which keeps the map monotone under
the component-wise order.  Bounded capacities ensure we stay inside a complete
lattice, therefore the fixed-point exists and can be computed via iteration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping

from .core import FixpointResult, God, Rule, State, Universe, fixpoint, rule


StateMapping = Mapping[str, float]
MutableState = MutableMapping[str, float]


@dataclass(frozen=True)
class WishParameters:
    """Coefficients that shape the dynamics of the love wishing machine.

    The parameters are intentionally compact yet expressive:

    self_cultivation:
        Fraction of the remaining self-love capacity added each epoch.
    openness_gain:
        Share of self-love channelled into openness.
    resonance_rate:
        Portion of the balanced energy ``min(self_love, openness)`` converted
        into resonance.
    blessing_feed:
        Share of resonance that becomes perceived blessing per epoch.
    patience:
        Retention factor for openness' inertia and resonance's memory.
    release_rate:
        Fraction of blessing that gently dissipates every epoch.
    radiance:
        External warm glow injected into the system – defaulting to zero.
    capacities:
        Optional component-wise upper bounds defining the lattice.
    """

    self_cultivation: float
    openness_gain: float
    resonance_rate: float
    blessing_feed: float
    patience: float
    release_rate: float
    radiance: float = 0.0
    capacities: StateMapping | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("self_cultivation", self.self_cultivation),
            ("openness_gain", self.openness_gain),
            ("resonance_rate", self.resonance_rate),
            ("blessing_feed", self.blessing_feed),
            ("patience", self.patience),
            ("release_rate", self.release_rate),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1], got {value!r}")

        if self.radiance < 0.0:
            raise ValueError("radiance must be non-negative")

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


def love_wishing_map(state: StateMapping, params: WishParameters) -> Dict[str, float]:
    """Return the next love wishing state under ``params``."""

    self_capacity = params.capacity("self_love")
    openness_capacity = params.capacity("openness")
    resonance_capacity = params.capacity("resonance")
    blessing_capacity = params.capacity("blessing")

    self_love = _clamp(
        state["self_love"]
        + params.self_cultivation * (1.0 - state["self_love"])
        + params.radiance * state["blessing"],
        self_capacity,
    )

    openness = _clamp(
        state["openness"] * (1.0 - params.patience)
        + params.openness_gain * state["self_love"]
        + params.radiance * state["blessing"],
        openness_capacity,
    )

    resonance = _clamp(
        state["resonance"] * params.patience
        + params.resonance_rate * min(state["self_love"], state["openness"]),
        resonance_capacity,
    )

    blessing = _clamp(
        state["blessing"] * (1.0 - params.release_rate)
        + params.blessing_feed * state["resonance"]
        + params.radiance,
        blessing_capacity,
    )

    return {
        "self_love": self_love,
        "openness": openness,
        "resonance": resonance,
        "blessing": blessing,
    }


def love_wishing_rule(params: WishParameters) -> Rule:
    """Create the monotone rule that updates the love wishing machine."""

    def apply(state: State, _ctx) -> State:
        return love_wishing_map(state, params)

    return rule("love-wishing-machine", apply)


def love_wishing_universe(initial_state: StateMapping, params: WishParameters) -> Universe:
    """Return a :class:`Universe` hosting the love wishing rule."""

    required_keys = {"self_love", "openness", "resonance", "blessing"}
    missing = required_keys.difference(initial_state)
    if missing:
        raise KeyError(f"initial_state missing keys: {sorted(missing)!r}")

    state: MutableState = {
        "self_love": float(initial_state["self_love"]),
        "openness": float(initial_state["openness"]),
        "resonance": float(initial_state["resonance"]),
        "blessing": float(initial_state["blessing"]),
    }

    return God.universe(state=state, rules=[love_wishing_rule(params)])


def love_wishing_metric(a: StateMapping, b: StateMapping) -> float:
    """Return the L1 distance between two love wishing states."""

    return sum(
        abs(a[key] - b[key])
        for key in ("self_love", "openness", "resonance", "blessing")
    )


def love_wishing_fixpoint(
    initial_state: StateMapping,
    params: WishParameters,
    *,
    epsilon: float = 1e-6,
    max_epoch: int = 128,
) -> FixpointResult:
    """Compute the fixed-point of the love wishing machine."""

    universe = love_wishing_universe(initial_state, params)
    return fixpoint(universe, metric=love_wishing_metric, epsilon=epsilon, max_epoch=max_epoch)


def wish_granted(state: StateMapping, threshold: float = 0.85) -> bool:
    """Heuristic indicator that the wish feels fulfilled."""

    if threshold < 0.0:
        raise ValueError("threshold must be non-negative")

    return all(
        state[key] >= threshold for key in ("self_love", "openness", "resonance", "blessing")
    )


__all__ = [
    "WishParameters",
    "love_wishing_fixpoint",
    "love_wishing_map",
    "love_wishing_metric",
    "love_wishing_rule",
    "love_wishing_universe",
    "wish_granted",
]

