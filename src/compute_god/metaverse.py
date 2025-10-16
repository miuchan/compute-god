"""Idealised metaverse orchestration primitives.

This module provides a tiny set of helpers that showcase how the Compute-God
runtime can be used to iteratively shape a universe toward the classical Chinese
virtues of ``真`` (truth), ``善`` (goodness) and ``美`` (beauty).  While the
implementation is intentionally lightweight, it demonstrates a practical
blueprint for modelling value aligned feedback loops inside the framework: each
epoch nudges the simulated metaverse closer to clarity, compassion and
creativity while harmonising the three pillars so that none of them dominates at
the expense of the others.

The design is deliberately didactic—intended to act as documentation as much as
code—so the functions expose sensible defaults while still letting callers
experiment with custom starting states and metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule
from .miyu import MiyuBond, bond_miyu

TriadState = MutableMapping[str, float]
LoveMetric = Callable[[State, State], float]


_TRIAD_KEYS: Sequence[str] = ("truth", "goodness", "beauty", "resonance")


def _as_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from None


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _cultivate_truth(state: State, _ctx: object) -> State:
    updated = dict(state)

    knowledge = _towards(_as_float(updated, "knowledge"), 1.0, 0.25)
    clarity = _towards(_as_float(updated, "clarity"), 1.0, 0.2)
    trust = _towards(_as_float(updated, "trust"), 1.0, 0.1)
    transparency = _towards(_as_float(updated, "transparency", knowledge), knowledge, 0.5)

    truth = _as_float(updated, "truth")
    truth += (1.0 - truth) * 0.35
    truth += (knowledge - truth) * 0.2
    truth += (clarity - truth) * 0.15
    truth += (trust - truth) * 0.1

    updated.update(
        {
            "knowledge": _bounded(knowledge),
            "clarity": _bounded(clarity),
            "trust": _bounded(trust),
            "transparency": _bounded(transparency),
            "truth": _bounded(truth),
        }
    )
    return updated


def _cultivate_goodness(state: State, _ctx: object) -> State:
    updated = dict(state)

    empathy = _towards(_as_float(updated, "empathy"), 1.0, 0.3)
    safety = _towards(_as_float(updated, "safety"), 1.0, 0.25)
    stewardship = _towards(_as_float(updated, "stewardship"), 1.0, 0.2)
    care = _towards(_as_float(updated, "care", empathy), empathy, 0.45)

    goodness = _as_float(updated, "goodness")
    goodness += (1.0 - goodness) * 0.3
    goodness += (empathy - goodness) * 0.25
    goodness += (safety - goodness) * 0.2
    goodness += (stewardship - goodness) * 0.1

    updated.update(
        {
            "empathy": _bounded(empathy),
            "safety": _bounded(safety),
            "stewardship": _bounded(stewardship),
            "care": _bounded(care),
            "goodness": _bounded(goodness),
        }
    )
    return updated


def _cultivate_beauty(state: State, _ctx: object) -> State:
    updated = dict(state)

    creativity = _towards(_as_float(updated, "creativity"), 1.0, 0.28)
    awe = _towards(_as_float(updated, "awe"), 1.0, 0.22)
    balance = _towards(_as_float(updated, "balance"), 1.0, 0.18)
    inspiration = _towards(_as_float(updated, "inspiration", creativity), creativity, 0.4)

    beauty = _as_float(updated, "beauty")
    beauty += (1.0 - beauty) * 0.28
    beauty += (creativity - beauty) * 0.25
    beauty += (awe - beauty) * 0.18
    beauty += (balance - beauty) * 0.12

    updated.update(
        {
            "creativity": _bounded(creativity),
            "awe": _bounded(awe),
            "balance": _bounded(balance),
            "inspiration": _bounded(inspiration),
            "beauty": _bounded(beauty),
        }
    )
    return updated


def _harmonise_triad(state: State, _ctx: object) -> State:
    updated = dict(state)

    truth = _as_float(updated, "truth")
    goodness = _as_float(updated, "goodness")
    beauty = _as_float(updated, "beauty")

    triad_avg = (truth + goodness + beauty) / 3.0
    for key in ("truth", "goodness", "beauty"):
        value = _as_float(updated, key)
        if value < triad_avg:
            value = _towards(value, triad_avg, 0.45)
        else:
            value = _towards(value, 1.0, 0.08)
        updated[key] = _bounded(value)

    triad = [updated[k] for k in ("truth", "goodness", "beauty")]
    spread = max(triad) - min(triad)
    resonance_target = _bounded(1.0 - spread * 0.5)
    resonance = _towards(_as_float(updated, "resonance"), resonance_target, 0.4)
    updated["resonance"] = _bounded(resonance)

    return updated


DEFAULT_STATE: TriadState = {
    "truth": 0.45,
    "goodness": 0.48,
    "beauty": 0.46,
    "knowledge": 0.32,
    "clarity": 0.28,
    "trust": 0.30,
    "transparency": 0.30,
    "empathy": 0.34,
    "safety": 0.31,
    "stewardship": 0.33,
    "care": 0.36,
    "creativity": 0.35,
    "awe": 0.29,
    "balance": 0.30,
    "inspiration": 0.33,
    "resonance": 0.27,
}


def _build_rules() -> Sequence[Rule]:
    return (
        rule("cultivate-truth", _cultivate_truth),
        rule("cultivate-goodness", _cultivate_goodness),
        rule("cultivate-beauty", _cultivate_beauty),
        rule("harmonise-triad", _harmonise_triad, priority=-1),
    )


def ideal_metaverse_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Create a universe that iteratively pursues truth, goodness and beauty."""

    state: TriadState = dict(DEFAULT_STATE)
    if initial_state:
        for key, value in initial_state.items():
            state[key] = float(value)

    return God.universe(state=state, rules=_build_rules(), observers=observers)


def metaverse_metric(previous: State, current: State) -> float:
    """Measure change across the three virtues and their resonance."""

    return sum(abs(_as_float(current, key) - _as_float(previous, key)) for key in _TRIAD_KEYS)


def _love_metric(keys: Sequence[str]) -> LoveMetric:
    def metric(state: State, target_state: State) -> float:
        distance = 0.0
        for key in keys:
            distance += abs(_as_float(state, key) - float(target_state.get(key, 0.0)))
        return distance

    return metric


def bond_metaverse_with_love(
    blueprint: Optional[MetaverseBlueprint] = None,
    *,
    keys: Sequence[str] = _TRIAD_KEYS,
) -> MiyuBond:
    """Create a :class:`MiyuBond` that measures love for the triad blueprint."""

    target = (blueprint or MetaverseBlueprint()).as_state()
    target_state = {key: float(target.get(key, 0.0)) for key in keys}
    metric = _love_metric(keys)
    return bond_miyu(target_state=target_state, metric=metric)


@dataclass
class MetaverseBlueprint:
    """Snapshot of the target state for the triad of virtues."""

    truth: float = 1.0
    goodness: float = 1.0
    beauty: float = 1.0
    resonance: float = 1.0

    def as_state(self) -> TriadState:
        return {
            "truth": self.truth,
            "goodness": self.goodness,
            "beauty": self.beauty,
            "resonance": self.resonance,
        }


def run_ideal_metaverse(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    epsilon: float = 1e-3,
    max_epoch: int = 96,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Execute the triad universe until it stabilises near the ideal blueprint."""

    universe = ideal_metaverse_universe(initial_state, observers=observers)
    return fixpoint(universe, metric=metaverse_metric, epsilon=epsilon, max_epoch=max_epoch)

