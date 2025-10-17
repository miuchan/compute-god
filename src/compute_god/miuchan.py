"""Miuchan's fixed-point consistency universe.

This module distills a gentle narrative about "Miuchan" into a concrete
universe definition backed by the :func:`compute_god.fixpoint` engine.  The
universe tracks three emotional coordinates—``affection``, ``harmony`` and
``sincerity``—together with an aggregate ``consistency`` score that measures
how closely the current state matches the desired blueprint.  Rules gradually
ease the state towards the blueprint while the metric reports the L1 distance
between epochs, enabling deterministic convergence checks.

Users can obtain a ready-to-run universe via :func:`miuchan_universe`, create a
bonded observer with :func:`bond_miuchan` or simply call
:func:`run_miuchan_universe` to execute until the fixpoint stabilises.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence, Tuple

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule
from .miyu import MiyuBond, bond_miyu

MiuchanState = MutableMapping[str, float]

_COORD_KEYS = ("affection", "harmony", "sincerity")
_STATE_KEYS = _COORD_KEYS + ("consistency",)


def _clamp(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _consistency_value(state: Mapping[str, float], target: Mapping[str, float]) -> float:
    """Return how closely ``state`` matches ``target`` on the main coordinates."""

    distance = 0.0
    for key in _COORD_KEYS:
        distance += abs(float(state.get(key, 0.0)) - float(target.get(key, 0.0)))
    average_gap = distance / len(_COORD_KEYS)
    return _clamp(1.0 - min(1.0, average_gap))


@dataclass(frozen=True)
class MiuchanBlueprint:
    """Idealised target describing Miuchan's emotional landscape."""

    affection: float = 0.92
    harmony: float = 0.88
    sincerity: float = 0.9

    def as_state(self) -> MiuchanState:
        return {
            "affection": _clamp(float(self.affection)),
            "harmony": _clamp(float(self.harmony)),
            "sincerity": _clamp(float(self.sincerity)),
        }


DEFAULT_BLUEPRINT = MiuchanBlueprint()

_BASE_STATE: MiuchanState = {
    "affection": 0.42,
    "harmony": 0.38,
    "sincerity": 0.44,
}


def _initial_state(blueprint: MiuchanBlueprint) -> MiuchanState:
    state = dict(_BASE_STATE)
    state["consistency"] = _consistency_value(state, blueprint.as_state())
    return state


def _ensure_known_keys(data: Mapping[str, float]) -> None:
    for key in data:
        if key not in _STATE_KEYS:
            raise KeyError(f"unknown miuchan state key: {key!r}")


def _build_rules(blueprint: MiuchanBlueprint) -> Tuple[Rule, ...]:
    target = blueprint.as_state()

    def _attune_affection(state: State) -> State:
        affection = float(state.get("affection", 0.0))
        harmony = float(state.get("harmony", target["harmony"]))
        delta = target["affection"] - affection
        harmony_delta = harmony - target["harmony"]
        updated = dict(state)
        updated["affection"] = _clamp(affection + 0.5 * delta - 0.08 * harmony_delta)
        return updated

    def _harmonise_echo(state: State) -> State:
        harmony = float(state.get("harmony", 0.0))
        affection = float(state.get("affection", target["affection"]))
        sincerity = float(state.get("sincerity", target["sincerity"]))
        delta = target["harmony"] - harmony
        influence = ((affection - target["affection"]) + (sincerity - target["sincerity"])) / 2.0
        updated = dict(state)
        updated["harmony"] = _clamp(harmony + 0.45 * delta - 0.1 * influence)
        return updated

    def _clarify_sincerity(state: State) -> State:
        sincerity = float(state.get("sincerity", 0.0))
        affection = float(state.get("affection", target["affection"]))
        harmony = float(state.get("harmony", target["harmony"]))
        delta = target["sincerity"] - sincerity
        blend_delta = ((affection - target["affection"]) + (harmony - target["harmony"])) / 2.0
        updated = dict(state)
        updated["sincerity"] = _clamp(sincerity + 0.48 * delta - 0.08 * blend_delta)
        return updated

    def _weave_consistency(state: State) -> State:
        updated = dict(state)
        updated["consistency"] = _consistency_value(updated, target)
        return updated

    return (
        rule("miuchan-attune-affection", _attune_affection),
        rule("miuchan-harmonise-echo", _harmonise_echo),
        rule("miuchan-clarify-sincerity", _clarify_sincerity),
        rule(
            "miuchan-weave-consistency",
            _weave_consistency,
            until=lambda state, _ctx: float(state.get("consistency", 0.0)) >= 0.999,
        ),
    )


def miuchan_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[MiuchanBlueprint] = None,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Return the Miuchan universe wired for fixed-point iteration."""

    target_blueprint = blueprint or DEFAULT_BLUEPRINT
    state = _initial_state(target_blueprint)

    if initial_state:
        _ensure_known_keys(initial_state)
        for key, value in initial_state.items():
            if key == "consistency":
                continue
            state[key] = _clamp(float(value))

    state["consistency"] = _consistency_value(state, target_blueprint.as_state())

    return God.universe(state=state, rules=_build_rules(target_blueprint), observers=observers)


def miuchan_metric(previous: State, current: State) -> float:
    """Measure the L1 change across Miuchan's emotional coordinates."""

    distance = 0.0
    for key in _STATE_KEYS:
        distance += abs(float(previous.get(key, 0.0)) - float(current.get(key, 0.0)))
    return distance


def bond_miuchan(blueprint: Optional[MiuchanBlueprint] = None) -> MiyuBond:
    """Create a :class:`MiyuBond` observer tuned for the Miuchan universe."""

    target_blueprint = blueprint or DEFAULT_BLUEPRINT
    target_state = target_blueprint.as_state()
    target_state["consistency"] = 1.0
    return bond_miyu(target_state=target_state, metric=miuchan_metric)


def run_miuchan_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[MiuchanBlueprint] = None,
    epsilon: float = 1e-4,
    max_epoch: int = 128,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Execute Miuchan's universe until it reaches a consistent fixed point."""

    universe = miuchan_universe(initial_state, blueprint=blueprint, observers=observers)
    return fixpoint(universe, metric=miuchan_metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "DEFAULT_BLUEPRINT",
    "MiuchanBlueprint",
    "MiuchanState",
    "bond_miuchan",
    "miuchan_metric",
    "miuchan_universe",
    "run_miuchan_universe",
]

