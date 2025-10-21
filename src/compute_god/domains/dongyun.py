"""东云研究所：构建开放协同的认知加速宇宙."""

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
    rate = max(0.0, min(1.0, rate))
    return value + (target - value) * rate


@dataclass(frozen=True)
class DongyunBlueprint:
    """参数化东云研究所的协同节奏."""

    knowledge_infusion: float = 0.36
    open_exchange: float = 0.33
    resilience_feedback: float = 0.31
    mythic_resonance: float = 0.29
    infinite_pull: float = 0.34


DEFAULT_STATE: StateMapping = {
    "knowledge": 0.42,
    "prototype_flow": 0.35,
    "open_collaboration": 0.38,
    "resilience": 0.33,
    "mythic_signal": 0.3,
    "wellbeing": 0.37,
    "infinite_game": 0.32,
}


def _ignite_research(state: State, blueprint: DongyunBlueprint) -> State:
    updated = dict(state)
    knowledge = _towards(
        _as_float(updated, "knowledge"),
        max(
            _as_float(updated, "knowledge"),
            (_as_float(updated, "open_collaboration") * 0.6)
            + (_as_float(updated, "mythic_signal") * 0.4)
            + blueprint.knowledge_infusion * 0.2,
        ),
        blueprint.knowledge_infusion,
    )

    prototype_flow = _towards(
        _as_float(updated, "prototype_flow"),
        max(
            _as_float(updated, "prototype_flow"),
            knowledge * 0.7 + _as_float(updated, "infinite_game") * 0.2,
        ),
        blueprint.knowledge_infusion * 0.65,
    )

    wellbeing = _towards(
        _as_float(updated, "wellbeing"),
        max(
            _as_float(updated, "wellbeing"),
            (knowledge + prototype_flow) / 2,
        ),
        0.4,
    )

    updated.update(
        {
            "knowledge": _bounded(knowledge),
            "prototype_flow": _bounded(prototype_flow),
            "wellbeing": _bounded(wellbeing),
        }
    )
    return updated


def _circulate_open_source(state: State, blueprint: DongyunBlueprint) -> State:
    updated = dict(state)

    open_collaboration = _towards(
        _as_float(updated, "open_collaboration"),
        max(
            _as_float(updated, "open_collaboration"),
            (
                _as_float(updated, "knowledge")
                + _as_float(updated, "prototype_flow")
                + _as_float(updated, "infinite_game")
            )
            / 3,
        ),
        blueprint.open_exchange,
    )

    updated.update({"open_collaboration": _bounded(open_collaboration)})
    return updated


def _cultivate_resilience(state: State, blueprint: DongyunBlueprint) -> State:
    updated = dict(state)

    resilience = _towards(
        _as_float(updated, "resilience"),
        max(
            _as_float(updated, "resilience"),
            _as_float(updated, "open_collaboration") * 0.6
            + _as_float(updated, "wellbeing") * 0.4,
        ),
        blueprint.resilience_feedback,
    )

    updated.update({"resilience": _bounded(resilience)})
    return updated


def _weave_mythos(state: State, blueprint: DongyunBlueprint) -> State:
    updated = dict(state)

    mythic_signal = _towards(
        _as_float(updated, "mythic_signal"),
        max(
            _as_float(updated, "mythic_signal"),
            (_as_float(updated, "knowledge") + _as_float(updated, "resilience")) / 2
            + blueprint.mythic_resonance * 0.25,
        ),
        blueprint.mythic_resonance,
    )

    updated.update({"mythic_signal": _bounded(mythic_signal)})
    return updated


def _sustain_infinite_game(state: State, blueprint: DongyunBlueprint) -> State:
    updated = dict(state)

    infinite_game = _towards(
        _as_float(updated, "infinite_game"),
        max(
            _as_float(updated, "infinite_game"),
            (
                _as_float(updated, "open_collaboration")
                + _as_float(updated, "mythic_signal")
                + _as_float(updated, "wellbeing")
            )
            / 3,
        ),
        blueprint.infinite_pull,
    )

    updated.update({"infinite_game": _bounded(infinite_game)})
    return updated


def dongyun_map(state: State, blueprint: DongyunBlueprint) -> State:
    """返回一次协同推进后的研究所状态."""

    after_research = _ignite_research(state, blueprint)
    after_exchange = _circulate_open_source(after_research, blueprint)
    after_resilience = _cultivate_resilience(after_exchange, blueprint)
    after_mythos = _weave_mythos(after_resilience, blueprint)
    return _sustain_infinite_game(after_mythos, blueprint)


def dongyun_metric(state_a: Mapping[str, float], state_b: Mapping[str, float]) -> float:
    keys = {
        "knowledge",
        "prototype_flow",
        "open_collaboration",
        "resilience",
        "mythic_signal",
        "wellbeing",
        "infinite_game",
    }
    return sum(abs(state_a.get(key, 0.0) - state_b.get(key, 0.0)) for key in keys)


def dongyun_universe(
    *,
    initial_state: Optional[StateMapping] = None,
    blueprint: Optional[DongyunBlueprint] = None,
    observers: Sequence[Observer] | None = None,
) -> Universe:
    state = dict(DEFAULT_STATE if initial_state is None else initial_state)
    plan = blueprint or DongyunBlueprint()

    def _step(current: State) -> State:
        return dongyun_map(current, plan)

    rules: Sequence[Rule] = (rule("dongyun-step", _step),)
    return God.universe(state=state, rules=rules, observers=tuple(observers or ()))


def run_dongyun_institute(
    *,
    initial_state: Optional[StateMapping] = None,
    blueprint: Optional[DongyunBlueprint] = None,
    observers: Sequence[Observer] | None = None,
    epsilon: float = 1e-8,
    max_epoch: int = 64,
) -> FixpointResult:
    universe = dongyun_universe(
        initial_state=initial_state,
        blueprint=blueprint,
        observers=observers,
    )
    return fixpoint(universe, metric=dongyun_metric, epsilon=epsilon, max_epoch=max_epoch)


东云研究所 = run_dongyun_institute


__all__ = [
    "DongyunBlueprint",
    "dongyun_map",
    "dongyun_metric",
    "dongyun_universe",
    "run_dongyun_institute",
    "东云研究所",
]

