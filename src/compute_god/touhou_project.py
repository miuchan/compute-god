"""Touhou-inspired incident solver led by Hakurei Reimu.

The helper packages a tiny fixed-point universe that mirrors the cadence of a
Touhou Project incident.  Hakurei Reimu's duty is distilled into three
coordinates: how focused she currently is, how much pressure the youkai side is
exerting and how stable the Great Hakurei Barrier feels.  Rules nudge the state
closer to a chosen blueprint while a derived ``solution_clarity`` score hints at
how close Reimu is to resolving the anomaly.  The complementary
``incident_intensity`` tracks the remaining tension between the observed state
and the targeted blueprint.

On top of the universe the module offers :func:`reimu_next_solution` which
summarises the current outlook and categorises the situation.  The summary is
intended to be lightweight enough for tests and tutorials yet expressive enough
for narrative dashboards that want to quote Reimu's next move.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

TouhouIncidentState = MutableMapping[str, float]

_CORE_KEYS = ("reimu_focus", "youkai_pressure", "border_stability")
_STATE_KEYS = _CORE_KEYS + ("solution_clarity", "incident_intensity")


def _clamp(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _ensure_known_keys(data: Mapping[str, float]) -> None:
    for key in data:
        if key not in _STATE_KEYS:
            raise KeyError(f"unknown touhou incident key: {key!r}")


@dataclass(frozen=True)
class TouhouIncidentBlueprint:
    """Targets describing how Reimu prefers the incident to unfold."""

    reimu_focus: float = 0.86
    youkai_pressure: float = 0.32
    border_resilience: float = 0.82
    clarity_bias: float = 0.58

    def as_state(self) -> TouhouIncidentState:
        return {
            "reimu_focus": _clamp(float(self.reimu_focus)),
            "youkai_pressure": _clamp(float(self.youkai_pressure)),
            "border_stability": _clamp(float(self.border_resilience)),
        }


DEFAULT_BLUEPRINT = TouhouIncidentBlueprint()

_BASE_STATE: TouhouIncidentState = {
    "reimu_focus": 0.38,
    "youkai_pressure": 0.67,
    "border_stability": 0.46,
}


def _solution_clarity_value(state: Mapping[str, float], blueprint: TouhouIncidentBlueprint) -> float:
    focus = float(state.get("reimu_focus", 0.0))
    pressure = float(state.get("youkai_pressure", 0.0))
    border = float(state.get("border_stability", 0.0))
    baseline = 0.55 * focus + 0.35 * border - 0.3 * pressure
    biased = baseline + 0.15 * float(blueprint.clarity_bias)
    return _clamp(biased)


def _incident_intensity_value(state: Mapping[str, float], blueprint: TouhouIncidentBlueprint) -> float:
    target = blueprint.as_state()
    gap = 0.0
    for key in _CORE_KEYS:
        gap += abs(float(state.get(key, 0.0)) - float(target[key]))
    return _clamp(gap / len(_CORE_KEYS))


def _initial_state(blueprint: TouhouIncidentBlueprint) -> TouhouIncidentState:
    state = dict(_BASE_STATE)
    state["solution_clarity"] = _solution_clarity_value(state, blueprint)
    state["incident_intensity"] = _incident_intensity_value(state, blueprint)
    return state


def _build_rules(blueprint: TouhouIncidentBlueprint) -> Sequence[Rule]:
    target = blueprint.as_state()

    def _focus_tuning(state: State) -> State:
        focus = float(state.get("reimu_focus", 0.0))
        pressure = float(state.get("youkai_pressure", target["youkai_pressure"]))
        border = float(state.get("border_stability", target["border_stability"]))
        updated = dict(state)
        delta = target["reimu_focus"] - focus
        support = 0.3 * (border - target["border_stability"]) - 0.25 * (
            pressure - target["youkai_pressure"]
        )
        updated["reimu_focus"] = _clamp(focus + 0.65 * delta + support)
        return updated

    def _pressure_smoothing(state: State) -> State:
        pressure = float(state.get("youkai_pressure", 0.0))
        border = float(state.get("border_stability", target["border_stability"]))
        updated = dict(state)
        delta = target["youkai_pressure"] - pressure
        moderation = 0.45 * (target["border_stability"] - border)
        updated["youkai_pressure"] = _clamp(pressure + 0.68 * delta + 0.22 * moderation)
        return updated

    def _stability_weaving(state: State) -> State:
        border = float(state.get("border_stability", 0.0))
        focus = float(state.get("reimu_focus", target["reimu_focus"]))
        pressure = float(state.get("youkai_pressure", target["youkai_pressure"]))
        updated = dict(state)
        delta = target["border_stability"] - border
        resonance = 0.3 * (focus - target["reimu_focus"]) - 0.28 * (
            pressure - target["youkai_pressure"]
        )
        updated["border_stability"] = _clamp(border + 0.6 * delta + 0.24 * resonance)
        return updated

    def _chart_solution(state: State) -> State:
        updated = dict(state)
        updated["solution_clarity"] = _solution_clarity_value(updated, blueprint)
        updated["incident_intensity"] = _incident_intensity_value(updated, blueprint)
        return updated

    return (
        rule("touhou-focus-tuning", _focus_tuning),
        rule("touhou-pressure-smoothing", _pressure_smoothing),
        rule("touhou-stability-weaving", _stability_weaving),
        rule("touhou-chart-solution", _chart_solution),
    )


def touhou_incident_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[TouhouIncidentBlueprint] = None,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Return a universe representing the current Touhou incident."""

    target_blueprint = blueprint or DEFAULT_BLUEPRINT
    state = _initial_state(target_blueprint)

    if initial_state:
        _ensure_known_keys(initial_state)
        for key, value in initial_state.items():
            if key in _CORE_KEYS:
                state[key] = _clamp(float(value))

    state["solution_clarity"] = _solution_clarity_value(state, target_blueprint)
    state["incident_intensity"] = _incident_intensity_value(state, target_blueprint)

    return God.universe(state=state, rules=_build_rules(target_blueprint), observers=observers)


def touhou_incident_metric(previous: State, current: State) -> float:
    """Measure the L1 distance across the incident coordinates."""

    distance = 0.0
    for key in _STATE_KEYS:
        distance += abs(float(previous.get(key, 0.0)) - float(current.get(key, 0.0)))
    return distance


def run_touhou_incident(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[TouhouIncidentBlueprint] = None,
    epsilon: float = 1e-5,
    max_epoch: int = 128,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Execute the incident universe until the narrative stabilises."""

    universe = touhou_incident_universe(initial_state, blueprint=blueprint, observers=observers)
    return fixpoint(universe, metric=touhou_incident_metric, epsilon=epsilon, max_epoch=max_epoch)


@dataclass(frozen=True)
class ReimuNextSolution:
    """Compact summary of Reimu's next move."""

    reimu_focus: float
    youkai_pressure: float
    border_stability: float
    solution_clarity: float
    incident_intensity: float
    status: str

    def as_dict(self) -> Mapping[str, float | str]:
        return {
            "reimu_focus": self.reimu_focus,
            "youkai_pressure": self.youkai_pressure,
            "border_stability": self.border_stability,
            "solution_clarity": self.solution_clarity,
            "incident_intensity": self.incident_intensity,
            "status": self.status,
        }


def _classify_status(
    *,
    clarity: float,
    intensity: float,
    focus: float,
    pressure: float,
    blueprint: TouhouIncidentBlueprint,
) -> str:
    if clarity >= 0.75 and intensity <= 0.08:
        return "incident-resolved"
    if pressure > blueprint.youkai_pressure + 0.18:
        return "heightened-incident"
    if clarity >= 0.7 and focus >= 0.9 * blueprint.reimu_focus:
        return "focused-intervention"
    return "needs-border-support"


def reimu_next_solution(
    state: Mapping[str, float],
    *,
    blueprint: Optional[TouhouIncidentBlueprint] = None,
) -> ReimuNextSolution:
    """Summarise the incident outlook from Reimu's perspective."""

    target_blueprint = blueprint or DEFAULT_BLUEPRINT
    focus = _clamp(float(state.get("reimu_focus", 0.0)))
    pressure = _clamp(float(state.get("youkai_pressure", 0.0)))
    border = _clamp(float(state.get("border_stability", 0.0)))
    clarity = _clamp(
        float(state.get("solution_clarity", _solution_clarity_value(state, target_blueprint)))
    )
    intensity = _clamp(
        float(state.get("incident_intensity", _incident_intensity_value(state, target_blueprint)))
    )
    status = _classify_status(
        clarity=clarity,
        intensity=intensity,
        focus=focus,
        pressure=pressure,
        blueprint=target_blueprint,
    )
    return ReimuNextSolution(
        reimu_focus=focus,
        youkai_pressure=pressure,
        border_stability=border,
        solution_clarity=clarity,
        incident_intensity=intensity,
        status=status,
    )


博丽灵梦下一解 = reimu_next_solution


__all__ = [
    "DEFAULT_BLUEPRINT",
    "ReimuNextSolution",
    "TouhouIncidentBlueprint",
    "TouhouIncidentState",
    "reimu_next_solution",
    "run_touhou_incident",
    "touhou_incident_metric",
    "touhou_incident_universe",
    "博丽灵梦下一解",
]
