"""Follow-reading learning friend cooperation network utilities.

The playful title ``S跟读学习朋友合作网络`` refers to a circle of study
companions who practise shadow reading together.  The helper functions in this
module provide a concrete blueprint for modelling such a learning network inside
Compute-God.  Each epoch the simulated friends align their reading rhythm,
reflect on insights gathered from the text and maintain a joyful environment so
that mutual encouragement never fades.  While whimsical, the rules are designed
as contractions—repeated iteration quickly converges toward the desired
blueprint which callers can tweak to match their community.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

FollowReadingState = MutableMapping[str, float]

_FOLLOW_READING_KEYS: Sequence[str] = (
    "cohesion",
    "curiosity",
    "rhythm",
    "reflection",
    "encouragement",
    "translation",
    "accountability",
    "playfulness",
)


def _ensure_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive programming
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from None


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _blend(*values: float) -> float:
    return sum(values) / float(len(values)) if values else 0.0


@dataclass(frozen=True)
class FollowReadingFriendProfile:
    """Describe how a learning friend contributes to the cooperation network."""

    name: str
    cohesion: float = 0.5
    curiosity: float = 0.5
    rhythm: float = 0.5
    reflection: float = 0.5
    encouragement: float = 0.5
    translation: float = 0.5
    accountability: float = 0.5
    playfulness: float = 0.5
    reliability: float = 1.0

    def weight(self) -> float:
        return max(0.0, float(self.reliability))

    def metric(self, key: str) -> float:
        return _bounded(float(getattr(self, key)))


def _weighted_average(friends: Sequence[FollowReadingFriendProfile], key: str) -> float:
    weights = [friend.weight() for friend in friends]
    total = sum(weights)
    if total <= 0:
        weights = [1.0 for _ in friends]
        total = float(len(friends)) if friends else 1.0

    accumulator = 0.0
    for friend, weight in zip(friends, weights):
        accumulator += friend.metric(key) * weight
    if total == 0:  # pragma: no cover - defensive but unreachable after guard
        return 0.0
    return accumulator / total


@dataclass
class FollowReadingBlueprint:
    """Target configuration for the follow-reading cooperation network."""

    cohesion: float = 1.0
    curiosity: float = 1.0
    rhythm: float = 1.0
    reflection: float = 1.0
    encouragement: float = 1.0
    translation: float = 1.0
    accountability: float = 1.0
    playfulness: float = 1.0

    def as_state(self) -> Mapping[str, float]:
        return {
            "cohesion": _bounded(self.cohesion),
            "curiosity": _bounded(self.curiosity),
            "rhythm": _bounded(self.rhythm),
            "reflection": _bounded(self.reflection),
            "encouragement": _bounded(self.encouragement),
            "translation": _bounded(self.translation),
            "accountability": _bounded(self.accountability),
            "playfulness": _bounded(self.playfulness),
        }


DEFAULT_FOLLOW_READING_STATE: FollowReadingState = {
    "cohesion": 0.44,
    "curiosity": 0.46,
    "rhythm": 0.42,
    "reflection": 0.43,
    "encouragement": 0.45,
    "translation": 0.4,
    "accountability": 0.41,
    "playfulness": 0.43,
}


def follow_reading_blueprint_from_friends(
    *friends: FollowReadingFriendProfile,
) -> "FollowReadingBlueprint":
    """Create a blueprint that honours the strengths of the provided friends."""

    if not friends:
        return FollowReadingBlueprint()

    mapping = {key: _weighted_average(friends, key) for key in _FOLLOW_READING_KEYS}
    return FollowReadingBlueprint(**mapping)


def _cultivate_cohesion_and_rhythm(target: Mapping[str, float]) -> Rule:
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        cohesion = _towards(_ensure_float(updated, "cohesion"), target["cohesion"], 0.33)
        rhythm_target = _bounded(_blend(target["rhythm"], cohesion))
        rhythm = _towards(_ensure_float(updated, "rhythm"), rhythm_target, 0.34)
        accountability_target = _bounded(_blend(cohesion, rhythm, target["accountability"]))
        accountability = _towards(
            _ensure_float(updated, "accountability"), accountability_target, 0.32
        )

        updated.update(
            {
                "cohesion": _bounded(cohesion),
                "rhythm": _bounded(rhythm),
                "accountability": _bounded(accountability),
            }
        )
        return updated

    return rule("follow-reading-cohesion", apply, role="coordination")


def _nurture_curiosity_and_reflection(target: Mapping[str, float]) -> Rule:
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        translation = _towards(
            _ensure_float(updated, "translation"), target["translation"], 0.31
        )
        curiosity = _towards(_ensure_float(updated, "curiosity"), target["curiosity"], 0.29)
        reflection_target = _bounded(_blend(curiosity, translation, target["reflection"]))
        reflection = _towards(
            _ensure_float(updated, "reflection"), reflection_target, 0.3
        )

        updated.update(
            {
                "translation": _bounded(translation),
                "curiosity": _bounded(curiosity),
                "reflection": _bounded(reflection),
            }
        )
        return updated

    return rule("follow-reading-reflection", apply, role="insight")


def _spark_encouragement_and_playfulness(target: Mapping[str, float]) -> Rule:
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        encouragement = _towards(
            _ensure_float(updated, "encouragement"), target["encouragement"], 0.35
        )
        playfulness_target = _bounded(
            target["playfulness"] + 0.2 * (encouragement - target["encouragement"])
        )
        playfulness = _towards(
            _ensure_float(updated, "playfulness"), playfulness_target, 0.33
        )
        cohesion = _towards(
            _ensure_float(updated, "cohesion"), _blend(encouragement, playfulness), 0.18
        )

        updated.update(
            {
                "encouragement": _bounded(encouragement),
                "playfulness": _bounded(playfulness),
                "cohesion": _bounded(cohesion),
            }
        )
        return updated

    return rule("follow-reading-joy", apply, role="care", priority=-1)


def follow_reading_rules(blueprint: Optional[FollowReadingBlueprint] = None) -> Sequence[Rule]:
    """Return the canonical set of rules steering the cooperation network."""

    target = (blueprint or FollowReadingBlueprint()).as_state()
    return (
        _cultivate_cohesion_and_rhythm(target),
        _nurture_curiosity_and_reflection(target),
        _spark_encouragement_and_playfulness(target),
    )


def follow_reading_metric(previous: State, current: State) -> float:
    """Measure change across the cooperation pillars."""

    distance = 0.0
    for key in _FOLLOW_READING_KEYS:
        previous_value = float(previous.get(key, 0.0))
        current_value = float(current.get(key, 0.0))
        distance += abs(current_value - previous_value)
    return distance


def follow_reading_universe(
    blueprint: Optional[FollowReadingBlueprint] = None,
    *,
    initial_state: Optional[Mapping[str, float]] = None,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Build a universe that simulates the follow-reading cooperation network."""

    state: FollowReadingState = dict(DEFAULT_FOLLOW_READING_STATE)
    if initial_state:
        for key, value in initial_state.items():
            state[key] = float(value)

    return God.universe(state=state, rules=follow_reading_rules(blueprint), observers=observers)


def run_follow_reading_network(
    blueprint: Optional[FollowReadingBlueprint] = None,
    *,
    initial_state: Optional[Mapping[str, float]] = None,
    epsilon: float = 1e-3,
    max_epoch: int = 96,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Execute the follow-reading universe until it harmonises with the blueprint."""

    universe = follow_reading_universe(
        blueprint, initial_state=initial_state, observers=observers
    )
    return fixpoint(universe, metric=follow_reading_metric, epsilon=epsilon, max_epoch=max_epoch)
