"""Dynamical system that nurtures the Miyu–Tiantian shared universe.

The design follows the guiding principles laid out in the project
documentation: the universe is represented as a trio of state, rules and
observers.  ``State`` captures the emotional temperature of the world together
with how well the collaborative rituals between Miyu and Tiantian are
blooming.  ``Rules`` express the rhythm of a day in their Minecraft-inspired
sanctuary—synchronising collective emotion, tending the memory garden, writing
diaries, unlocking floating dream isles and performing the nightly starlake
ballet.  ``Observers`` can be attached to record progress; in particular the
:class:`compute_god.miyu.MiyuBond` helper measures how close the universe is to
a desired blueprint.

The implementation keeps the numeric model intentionally lightweight.  All
state variables are normalised floats, typically constrained to ``[0, 1]`` with
the exception of ``dream_isles`` which grows towards a small upper bound to
represent discrete unlocks.  Each rule gradually pushes the system towards a
steady configuration, making it suitable for the generic
:func:`compute_god.engine.fixpoint` solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .engine import FixpointResult, fixpoint
from .miyu import MiyuBond, bond_miyu
from .observer import Observer
from .rule import Rule, State, rule
from .universe import God, Universe


MiyuTiantianState = MutableMapping[str, float]

_DREAM_ISLE_CAP = 3.0
_STATE_KEYS = (
    "emotion",
    "memory_bloom",
    "collaboration",
    "dream_isles",
    "orbit_rhythm",
    "resonance",
    "diary",
)


def _as_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from exc


def _clamp(value: float, upper: float = 1.0) -> float:
    if value < 0.0:
        return 0.0
    if value > upper:
        return upper
    return value


def _ensure_known_keys(state: Mapping[str, float], who: str) -> None:
    for key in state:
        if key not in DEFAULT_STATE:
            raise KeyError(f"unknown {who} state key: {key!r}")


def _sync_emotion(state: State, _ctx: object) -> State:
    updated = dict(state)

    emotion = _as_float(updated, "emotion")
    memory_bloom = _as_float(updated, "memory_bloom")
    resonance = _as_float(updated, "resonance")
    collaboration = _as_float(updated, "collaboration")

    emotion = (
        emotion * 0.75
        + memory_bloom * 0.15
        + resonance * 0.12
        + collaboration * 0.1
    )
    updated["emotion"] = _clamp(emotion)

    collaboration = collaboration * 0.85 + memory_bloom * 0.1 + resonance * 0.08
    updated["collaboration"] = _clamp(collaboration)

    return updated


def _grow_memory_garden(state: State, _ctx: object) -> State:
    updated = dict(state)

    memory_bloom = _as_float(updated, "memory_bloom")
    diary = _as_float(updated, "diary")
    emotion = _as_float(updated, "emotion")

    growth = 0.18 * emotion + 0.14 * diary + 0.08 * (1.0 - memory_bloom)
    memory_bloom = _clamp(memory_bloom * 0.82 + growth)
    updated["memory_bloom"] = memory_bloom

    diary = _clamp(diary * 0.7 + emotion * 0.2 + memory_bloom * 0.15)
    updated["diary"] = diary

    return updated


def _unlock_dream_isle(state: State, _ctx: object) -> State:
    updated = dict(state)

    emotion = _as_float(updated, "emotion")
    memory_bloom = _as_float(updated, "memory_bloom")
    dream_isles = _as_float(updated, "dream_isles")
    resonance = _as_float(updated, "resonance")

    potential = max(0.0, emotion - 0.6)
    dream_isles = min(
        _DREAM_ISLE_CAP,
        dream_isles * 0.9 + potential * (0.5 + memory_bloom * 0.35),
    )
    updated["dream_isles"] = dream_isles

    resonance = _clamp(resonance * 0.78 + dream_isles * 0.08 + memory_bloom * 0.12)
    updated["resonance"] = resonance

    return updated


def _starlake_ballet(state: State, _ctx: object) -> State:
    updated = dict(state)

    orbit = _as_float(updated, "orbit_rhythm")
    emotion = _as_float(updated, "emotion")
    collaboration = _as_float(updated, "collaboration")
    resonance = _as_float(updated, "resonance")

    orbit = _clamp(orbit * 0.74 + emotion * 0.18 + collaboration * 0.12)
    updated["orbit_rhythm"] = orbit

    resonance = _clamp(resonance * 0.7 + orbit * 0.16 + collaboration * 0.08)
    updated["resonance"] = resonance

    return updated


DEFAULT_STATE: MiyuTiantianState = {
    "emotion": 0.48,
    "memory_bloom": 0.36,
    "collaboration": 0.35,
    "dream_isles": 0.2,
    "orbit_rhythm": 0.4,
    "resonance": 0.33,
    "diary": 0.28,
}


def _build_rules() -> Sequence[Rule]:
    return (
        rule("sync-emotion", _sync_emotion),
        rule("memory-garden", _grow_memory_garden),
        rule("unlock-dream-isle", _unlock_dream_isle),
        rule("starlake-ballet", _starlake_ballet, priority=-1),
    )


def miyu_tiantian_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Return the universe orchestrating Miyu and Tiantian's shared rhythm."""

    state: MiyuTiantianState = dict(DEFAULT_STATE)
    if initial_state:
        for key, value in initial_state.items():
            if key not in DEFAULT_STATE:
                raise KeyError(f"unknown miyu-tiantian state key: {key!r}")
            state[key] = float(value)

    return God.universe(state=state, rules=_build_rules(), observers=observers)


def miyu_tiantian_metric(previous: State, current: State) -> float:
    """Measure the L1 change across the shared universe coordinates."""

    distance = 0.0
    for key in _STATE_KEYS:
        distance += abs(float(previous.get(key, 0.0)) - float(current.get(key, 0.0)))
    return distance


@dataclass
class MiyuTiantianBlueprint:
    """Idealised target for the Miyu–Tiantian universe."""

    emotion: float = 0.9
    memory_bloom: float = 0.85
    collaboration: float = 0.8
    dream_isles: float = 2.5
    orbit_rhythm: float = 0.82
    resonance: float = 0.84
    diary: float = 0.78

    def as_state(self) -> MiyuTiantianState:
        return {
            "emotion": self.emotion,
            "memory_bloom": self.memory_bloom,
            "collaboration": self.collaboration,
            "dream_isles": min(self.dream_isles, _DREAM_ISLE_CAP),
            "orbit_rhythm": self.orbit_rhythm,
            "resonance": self.resonance,
            "diary": self.diary,
        }


def bond_miyu_tiantian(blueprint: Optional[MiyuTiantianBlueprint] = None) -> MiyuBond:
    """Create a :class:`MiyuBond` linked to a Miyu–Tiantian blueprint."""

    target_blueprint = blueprint or MiyuTiantianBlueprint()
    return bond_miyu(target_blueprint.as_state(), miyu_tiantian_metric)


def sweet_encounter(
    tiantian_state: Optional[Mapping[str, float]] = None,
    miyu_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[MiyuTiantianBlueprint] = None,
) -> MiyuTiantianState:
    """Blend Tiantian and Miyu's moods into a shared encounter snapshot.

    Parameters
    ----------
    tiantian_state, miyu_state:
        Optional partial states describing Tiantian或美羽此刻的情绪线索。键名需属于
        :data:`DEFAULT_STATE`，缺失的坐标会自动回落到默认值。
    blueprint:
        甜甜与美羽共同憧憬的目标蓝图。若未提供，则使用
        :class:`MiyuTiantianBlueprint` 的默认设定。

    Returns
    -------
    MiyuTiantianState
        一个在 `[0, 1]`（梦之群岛坐标在 `[0, _DREAM_ISLE_CAP]`）范围内的温柔态，
        用于表示她们甜美相遇时的宇宙温度。

    Notes
    -----
    函数通过对甜甜、美羽、默认宇宙与蓝图目标进行加权平均，并加入“同步亲密度”
    的加成，让两人情绪越接近时，合奏出来的情绪越明亮。
    """

    base_state = dict(DEFAULT_STATE)
    target_blueprint = blueprint or MiyuTiantianBlueprint()
    blueprint_state = target_blueprint.as_state()

    if tiantian_state:
        _ensure_known_keys(tiantian_state, "tiantian")
    if miyu_state:
        _ensure_known_keys(miyu_state, "miyu")

    encounter: MiyuTiantianState = {}

    for key in _STATE_KEYS:
        upper = _DREAM_ISLE_CAP if key == "dream_isles" else 1.0

        tiantian_value = (
            _clamp(float(tiantian_state.get(key, base_state[key])), upper=upper)
            if tiantian_state
            else float(base_state[key])
        )
        miyu_value = (
            _clamp(float(miyu_state.get(key, base_state[key])), upper=upper)
            if miyu_state
            else float(base_state[key])
        )

        base_value = float(base_state[key])
        blueprint_value = float(blueprint_state[key])

        blended = (
            0.3 * tiantian_value
            + 0.3 * miyu_value
            + 0.2 * base_value
            + 0.2 * blueprint_value
        )

        if tiantian_state and miyu_state:
            closeness = 1.0 - min(1.0, abs(tiantian_value - miyu_value))
            blended += 0.05 * closeness

        encounter[key] = _clamp(blended, upper=upper)

    return encounter


def run_miyu_tiantian_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    epsilon: float = 1e-4,
    max_epoch: int = 192,
    observers: Optional[Sequence[Observer]] = None,
) -> FixpointResult:
    """Iterate the universe until it harmonises near the blueprint."""

    universe = miyu_tiantian_universe(initial_state, observers=observers)
    return fixpoint(universe, metric=miyu_tiantian_metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "DEFAULT_STATE",
    "MiyuTiantianBlueprint",
    "MiyuTiantianState",
    "bond_miyu_tiantian",
    "miyu_tiantian_metric",
    "miyu_tiantian_universe",
    "run_miyu_tiantian_universe",
    "sweet_encounter",
]

