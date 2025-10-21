"""Planetary rescue dynamics for Compute-God universes.

The "Compute-God saves Earth" story turns climate mitigation, ecological
restoration, and collective cooperation into a compact fixed-point model.  Each
state of the universe tracks three scalar metrics:

``temperature``
    Global heating expressed as the overshoot above pre-industrial baselines.
``pollution``
    Accumulated harmful load such as greenhouse gases or particulate matter.
``cooperation``
    Aggregate willingness of societies and institutions to act together.

Given ``RescueParameters`` the :func:`save_earth` helper builds a universe whose
only rule iteratively nudges the metrics towards declared goals.  The updates are
contractions, hence the fixpoint engine converges exponentially fast while the
state history records each step of the recovery.  This gives playful yet precise
semantics to the meme-worthy prompt "计算神拯救地球" (Compute-God saves the Earth).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping

from compute_god.core import FixpointResult, God, Metric, State, fixpoint, rule


PlanetStateMapping = Mapping[str, float]
MutablePlanetState = MutableMapping[str, float]


@dataclass(frozen=True)
class EarthState:
    """Snapshot of the planet across climate, pollution, and cooperation axes."""

    temperature: float
    pollution: float
    cooperation: float

    def as_mapping(self) -> PlanetStateMapping:
        """Return the state as an immutable mapping."""

        return {
            "temperature": float(self.temperature),
            "pollution": float(self.pollution),
            "cooperation": float(self.cooperation),
        }


@dataclass(frozen=True)
class RescueParameters:
    """Goals and convergence rates for restoring planetary health.

    Parameters
    ----------
    temperature_goal:
        Target overshoot in degrees Celsius.  Values below or equal to ``1.5``
        model alignment with the Paris Agreement.
    pollution_goal:
        Desired steady-state pollution level (dimensionless ratio in ``[0, 1]``).
    cooperation_goal:
        Sustainable cooperation ratio.  ``1`` encodes a fully aligned planet.
    temperature_rate / pollution_rate / cooperation_rate:
        Rates in ``(0, 1]`` dictating how aggressively each metric approaches its
        goal every epoch.  Higher values mean faster convergence but the process
        remains a contraction so long as the rates stay within ``(0, 1]``.
    history_keys:
        Iterable of metric names whose trajectories should be recorded.  Defaults
        to the three canonical metrics.
    """

    temperature_goal: float = 1.5
    pollution_goal: float = 0.2
    cooperation_goal: float = 0.85
    temperature_rate: float = 0.3
    pollution_rate: float = 0.25
    cooperation_rate: float = 0.2
    history_keys: Iterable[str] = ("temperature", "pollution", "cooperation")

    def __post_init__(self) -> None:
        for name, value in (
            ("temperature_rate", self.temperature_rate),
            ("pollution_rate", self.pollution_rate),
            ("cooperation_rate", self.cooperation_rate),
        ):
            if not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must lie in (0, 1], got {value!r}")

    def history_keys_tuple(self) -> tuple[str, ...]:
        keys = tuple(self.history_keys)
        if not keys:
            raise ValueError("history_keys must contain at least one metric name")
        return keys


def _approach(current: float, goal: float, rate: float) -> float:
    """Contract ``current`` towards ``goal`` using ``rate`` in ``(0, 1]``."""

    return current + rate * (goal - current)


def rescue_map(state: PlanetStateMapping, params: RescueParameters) -> MutablePlanetState:
    """Return the next planetary state under ``params``."""

    temperature = _approach(state["temperature"], params.temperature_goal, params.temperature_rate)
    pollution = _approach(state["pollution"], params.pollution_goal, params.pollution_rate)
    cooperation = _approach(state["cooperation"], params.cooperation_goal, params.cooperation_rate)

    next_state: MutablePlanetState = {
        "temperature": float(temperature),
        "pollution": float(pollution),
        "cooperation": float(cooperation),
    }

    keys = params.history_keys_tuple()
    trajectory_entry = {key: next_state[key] for key in keys}
    history = list(state.get("history", ()))
    history.append(trajectory_entry)
    next_state["history"] = history

    return next_state


def _planet_metric(keys: Iterable[str]) -> Metric:
    keys = tuple(keys)

    def metric(previous: State, current: State) -> float:
        return max(abs(previous[key] - current[key]) for key in keys)

    return metric


def save_earth(
    crisis: EarthState,
    plan: RescueParameters | None = None,
    *,
    epsilon: float = 1e-6,
    max_epoch: int = 128,
) -> FixpointResult:
    """Drive a Compute-God universe until the rescue plan stabilises."""

    if plan is None:
        plan = RescueParameters()

    state: MutablePlanetState = {
        "temperature": float(crisis.temperature),
        "pollution": float(crisis.pollution),
        "cooperation": float(crisis.cooperation),
        "history": [],
    }

    keys = plan.history_keys_tuple()
    for key in keys:
        if key not in state:
            raise KeyError(f"history key {key!r} not present in planetary state")

    initial_entry = {key: state[key] for key in keys}
    state["history"].append(initial_entry)

    universe = God.universe(
        state=state,
        rules=[rule("earth-rescue", lambda s, _ctx: rescue_map(s, plan))],
    )

    metric = _planet_metric(keys)
    return fixpoint(universe, metric=metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "EarthState",
    "RescueParameters",
    "rescue_map",
    "save_earth",
]
