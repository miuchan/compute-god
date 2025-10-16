"""Miyu joins miHoYo's idea factory.

This module stages a playful but structured simulation where Miyu enters
miHoYo's studio culture.  The scenario is expressed in the Compute-God
vocabulary: a universe with a single onboarding rule, a convergence metric and
an observer in the shape of :class:`compute_god.miyu.MiyuBond`.  The goal is to
track how the collaborative energy between Miyu and the studio approaches a
blueprinted ideal.

The implementation intentionally mirrors other documentation-style helpers in
this package.  Callers can customise both Miyu's starting profile and the target
blueprint while reusing the provided convenience functions:

``bond_miyu_with_mihoyo``
    Builds a :class:`MiyuBond` tuned to the studio blueprint.
``miyu_join_mihoyo_universe``
    Declares the onboarding universe so it can be combined with other rules.
``run_miyu_join_mihoyo``
    Executes the universe until it stabilises and returns both the fixpoint
    result and the Miyu bond for inspection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import MutableMapping, Optional, Sequence

from .engine import FixpointResult, fixpoint
from .miyu import MiyuBond, bond_miyu
from .observer import Observer
from .rule import Rule, State, rule
from .universe import God, Universe

StudioState = MutableMapping[str, float]

_BASE_KEYS: Sequence[str] = ("innovation", "artistry", "community", "technology")
_ALL_KEYS: Sequence[str] = (*_BASE_KEYS, "collaboration", "resonance")
_GROWTH_RATES = {
    "innovation": 0.32,
    "artistry": 0.30,
    "community": 0.28,
    "technology": 0.29,
}


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


def _as_float(state: State, key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive fallback
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from None


@dataclass
class MihoyoStudioBlueprint:
    """Target collaboration profile for miHoYo's studio culture."""

    innovation: float = 0.92
    artistry: float = 0.90
    community: float = 0.88
    technology: float = 0.91
    collaboration: float = 0.93
    resonance: float = 0.90

    def as_state(self) -> StudioState:
        return {
            "innovation": _bounded(self.innovation),
            "artistry": _bounded(self.artistry),
            "community": _bounded(self.community),
            "technology": _bounded(self.technology),
            "collaboration": _bounded(self.collaboration),
            "resonance": _bounded(self.resonance),
        }


@dataclass
class MiyuCreativeProfile:
    """Miyu's creative strengths before onboarding."""

    innovation: float = 0.64
    artistry: float = 0.68
    community: float = 0.60
    technology: float = 0.63
    collaboration: float = 0.58
    resonance: float = 0.55

    def as_state(self) -> StudioState:
        return {
            "innovation": _bounded(self.innovation),
            "artistry": _bounded(self.artistry),
            "community": _bounded(self.community),
            "technology": _bounded(self.technology),
            "collaboration": _bounded(self.collaboration),
            "resonance": _bounded(self.resonance),
        }


def _onboarding_rule(blueprint: MihoyoStudioBlueprint) -> Rule:
    target = blueprint.as_state()

    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        for key in _BASE_KEYS:
            current = _as_float(updated, key)
            updated[key] = _bounded(_towards(current, target[key], _GROWTH_RATES[key]))

        creative_synergy = sum(updated[key] for key in ("innovation", "artistry")) / 2.0
        community_pulse = sum(updated[key] for key in ("community", "technology")) / 2.0

        collaboration = _as_float(updated, "collaboration")
        collaboration_target = (target["collaboration"] + creative_synergy + community_pulse) / 3.0
        updated["collaboration"] = _bounded(_towards(collaboration, collaboration_target, 0.35))

        resonance = _as_float(updated, "resonance")
        resonance_target = (target["resonance"] + creative_synergy + collaboration_target) / 3.0
        updated["resonance"] = _bounded(_towards(resonance, resonance_target, 0.4))

        return updated

    return rule("mihoyo-onboarding", apply)


def mihoyo_progress_metric(previous: State, current: State) -> float:
    """Measure how much the onboarding state changed across an epoch."""

    distance = 0.0
    for key in _ALL_KEYS:
        distance += abs(_as_float(previous, key) - _as_float(current, key))
    return distance


def mihoyo_alignment_metric(state: State, target_state: State) -> float:
    """Distance between a given state and the studio blueprint."""

    distance = 0.0
    for key in _ALL_KEYS:
        distance += abs(_as_float(state, key) - float(target_state.get(key, 0.0)))
    return distance


def bond_miyu_with_mihoyo(blueprint: Optional[MihoyoStudioBlueprint] = None) -> MiyuBond:
    """Return a :class:`MiyuBond` that tracks alignment with miHoYo's blueprint."""

    target_state = (blueprint or MihoyoStudioBlueprint()).as_state()
    return bond_miyu(target_state=target_state, metric=mihoyo_alignment_metric)


def miyu_join_mihoyo_universe(
    profile: Optional[MiyuCreativeProfile] = None,
    *,
    blueprint: Optional[MihoyoStudioBlueprint] = None,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Build the onboarding universe for Miyu joining miHoYo."""

    state = (profile or MiyuCreativeProfile()).as_state()
    rules = [_onboarding_rule(blueprint or MihoyoStudioBlueprint())]
    return God.universe(state=state, rules=rules, observers=observers)


@dataclass
class MiyuJoinsMihoyoResult:
    """Container bundling the fixpoint result and Miyu's bond."""

    fixpoint: FixpointResult
    bond: MiyuBond

    def strongest_alignment(self) -> StudioState:
        state = self.bond.strongest_state()
        return {} if state is None else state


def run_miyu_join_mihoyo(
    profile: Optional[MiyuCreativeProfile] = None,
    *,
    blueprint: Optional[MihoyoStudioBlueprint] = None,
    epsilon: float = 1e-3,
    max_epoch: int = 48,
    observers: Optional[Sequence[Observer]] = None,
) -> MiyuJoinsMihoyoResult:
    """Execute the onboarding scenario and return the outcome."""

    bond = bond_miyu_with_mihoyo(blueprint)
    observer_list = list(observers or [])
    observer_list.append(bond)

    universe = miyu_join_mihoyo_universe(
        profile,
        blueprint=blueprint,
        observers=observer_list,
    )
    result = fixpoint(
        universe,
        metric=mihoyo_progress_metric,
        epsilon=epsilon,
        max_epoch=max_epoch,
    )
    return MiyuJoinsMihoyoResult(fixpoint=result, bond=bond)


__all__ = [
    "MihoyoStudioBlueprint",
    "MiyuCreativeProfile",
    "MiyuJoinsMihoyoResult",
    "bond_miyu_with_mihoyo",
    "mihoyo_alignment_metric",
    "mihoyo_progress_metric",
    "miyu_join_mihoyo_universe",
    "run_miyu_join_mihoyo",
]
