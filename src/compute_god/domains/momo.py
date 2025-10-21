"""Time harmony universes inspired by *Momo*."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from compute_god.core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

StateMapping = MutableMapping[str, float]


def _as_float(state: MutableMapping[str, object], key: str, default: float = 0.0) -> float:
    value = state.get(key, default)
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # pragma: no cover - defensive
        raise TypeError(f"state[{key!r}] must be numeric, got {value!r}") from None


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _towards(value: float, target: float, rate: float) -> float:
    return value + (target - value) * rate


@dataclass(frozen=True)
class MomoResonanceBlueprint:
    listening_rate: float = 0.32
    garden_growth: float = 0.28
    cosmic_guidance: float = 0.26
    gray_dissipation: float = 0.3
    harmony_rate: float = 0.35


def _nurture_listening(state: State, blueprint: MomoResonanceBlueprint) -> State:
    updated = dict(state)

    listening = _towards(_as_float(updated, "listening"), 1.0, blueprint.listening_rate)
    empathy = _towards(_as_float(updated, "empathy"), listening, blueprint.listening_rate * 0.6)
    presence = _towards(_as_float(updated, "presence"), listening, blueprint.listening_rate * 0.5)

    time_flow = _as_float(updated, "time_flow")
    time_flow = _towards(time_flow, (listening + empathy + presence) / 3.0, 0.4)

    updated.update(
        {
            "listening": _bounded(listening),
            "empathy": _bounded(empathy),
            "presence": _bounded(presence),
            "time_flow": _bounded(time_flow),
        }
    )
    return updated


def _tend_time_garden(state: State, blueprint: MomoResonanceBlueprint) -> State:
    updated = dict(state)

    garden_vitality = _towards(_as_float(updated, "garden_vitality"), 1.0, blueprint.garden_growth)
    reclaimed_time = _towards(_as_float(updated, "reclaimed_time"), garden_vitality, blueprint.garden_growth * 0.7)
    creativity = _towards(_as_float(updated, "creativity"), garden_vitality, blueprint.garden_growth * 0.6)

    time_harmony = _as_float(updated, "time_harmony")
    time_harmony = _towards(time_harmony, (garden_vitality + reclaimed_time + creativity) / 3.0, 0.45)

    updated.update(
        {
            "garden_vitality": _bounded(garden_vitality),
            "reclaimed_time": _bounded(reclaimed_time),
            "creativity": _bounded(creativity),
            "time_harmony": _bounded(time_harmony),
        }
    )
    return updated


def _consult_hora_master(state: State, blueprint: MomoResonanceBlueprint) -> State:
    updated = dict(state)

    wisdom = _towards(_as_float(updated, "wisdom"), 1.0, blueprint.cosmic_guidance)
    trust = _towards(_as_float(updated, "trust"), wisdom, blueprint.cosmic_guidance * 0.8)
    patience = _towards(_as_float(updated, "patience"), wisdom, blueprint.cosmic_guidance * 0.5)

    cosmic_resonance = _as_float(updated, "cosmic_resonance")
    cosmic_resonance = _towards(cosmic_resonance, (wisdom + trust + patience) / 3.0, 0.5)

    updated.update(
        {
            "wisdom": _bounded(wisdom),
            "trust": _bounded(trust),
            "patience": _bounded(patience),
            "cosmic_resonance": _bounded(cosmic_resonance),
        }
    )
    return updated


def _dispel_gray_men(state: State, blueprint: MomoResonanceBlueprint) -> State:
    updated = dict(state)

    gray_influence = _as_float(updated, "gray_influence")
    gray_influence = _towards(gray_influence, 0.0, blueprint.gray_dissipation)
    reclaimed_time = _towards(_as_float(updated, "reclaimed_time"), 1.0, blueprint.gray_dissipation * 0.5)
    community = _towards(_as_float(updated, "community"), 1.0, blueprint.gray_dissipation * 0.4)

    updated.update(
        {
            "gray_influence": _bounded(gray_influence),
            "reclaimed_time": _bounded(reclaimed_time),
            "community": _bounded(community),
        }
    )
    return updated


def _restore_harmony(state: State, blueprint: MomoResonanceBlueprint) -> State:
    updated = dict(state)

    time_harmony = _as_float(updated, "time_harmony")
    cosmic_resonance = _as_float(updated, "cosmic_resonance")
    listening = _as_float(updated, "listening")
    gray_influence = _as_float(updated, "gray_influence")

    desired_harmony = max(time_harmony, cosmic_resonance)
    desired_harmony = desired_harmony * (1.0 - gray_influence * 0.5)
    desired_harmony = (desired_harmony + listening) / 2.0

    harmony = _towards(_as_float(updated, "harmony"), desired_harmony, blueprint.harmony_rate)
    serenity = _towards(_as_float(updated, "serenity"), harmony, blueprint.harmony_rate * 0.7)

    updated.update(
        {
            "harmony": _bounded(harmony),
            "serenity": _bounded(serenity),
        }
    )
    return updated


DEFAULT_STATE: StateMapping = {
    "listening": 0.38,
    "empathy": 0.33,
    "presence": 0.35,
    "time_flow": 0.3,
    "garden_vitality": 0.32,
    "reclaimed_time": 0.28,
    "creativity": 0.31,
    "time_harmony": 0.29,
    "wisdom": 0.34,
    "trust": 0.3,
    "patience": 0.33,
    "cosmic_resonance": 0.27,
    "gray_influence": 0.52,
    "community": 0.36,
    "harmony": 0.31,
    "serenity": 0.28,
}


def _build_rules(blueprint: MomoResonanceBlueprint) -> Sequence[Rule]:
    return (
        rule("nurture-listening", lambda s, _ctx=None: _nurture_listening(s, blueprint)),
        rule("tend-time-garden", lambda s, _ctx=None: _tend_time_garden(s, blueprint)),
        rule("consult-hora-master", lambda s, _ctx=None: _consult_hora_master(s, blueprint)),
        rule("dispel-gray-men", lambda s, _ctx=None: _dispel_gray_men(s, blueprint)),
        rule("restore-harmony", lambda s, _ctx=None: _restore_harmony(s, blueprint), priority=-1),
    )


def momo_time_universe(
    *,
    initial_state: Optional[Mapping[str, float]] = None,
    observers: Optional[Sequence[Observer]] = None,
    blueprint: Optional[MomoResonanceBlueprint] = None,
) -> Universe:
    blueprint = blueprint or MomoResonanceBlueprint()

    state: StateMapping = dict(DEFAULT_STATE)
    if initial_state:
        for key, value in initial_state.items():
            state[key] = float(value)

    return God.universe(state=state, rules=_build_rules(blueprint), observers=observers)


MOMO_KEYS: Sequence[str] = (
    "listening",
    "time_harmony",
    "cosmic_resonance",
    "harmony",
    "gray_influence",
)


def momo_resonance_metric(previous: State, current: State) -> float:
    total = 0.0
    for key in MOMO_KEYS:
        total += abs(_as_float(current, key) - _as_float(previous, key))
    return total


def run_momo_time_harmony(
    *,
    initial_state: Optional[Mapping[str, float]] = None,
    observers: Optional[Sequence[Observer]] = None,
    blueprint: Optional[MomoResonanceBlueprint] = None,
    epsilon: float = 1e-3,
    max_epoch: int = 48,
) -> FixpointResult:
    universe = momo_time_universe(
        initial_state=initial_state,
        observers=observers,
        blueprint=blueprint,
    )
    return fixpoint(universe, metric=momo_resonance_metric, epsilon=epsilon, max_epoch=max_epoch)

