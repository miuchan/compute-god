"""LLM cooperation network orchestration utilities.

The module treats a fleet of large language models as a cooperative network. It
captures how alignment, coverage, safety, creativity and operations interact
when multiple agents collaborate on a shared mission.  Much like the complex
network helpers available in the codebase, every value is normalised to
``[0.0, 1.0]`` and the provided rules are contractive: repeated application
quickly leads to a harmonious fixed point where all participating models pull in
the same direction.

Two main entry points are exposed:

``llm_cooperation_blueprint_from_agents``
    Synthesise a blueprint directly from a collection of agent contribution
    profiles.  The helper performs reliability-weighted averaging so that highly
    reliable agents influence the target configuration more strongly.

``run_llm_cooperation``
    Construct the canonical cooperation universe and iterate it until the
    network stabilises.  The returned :class:`compute_god.engine.FixpointResult`
    describes whether convergence was achieved alongside the terminal state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional, Sequence

from .core import FixpointResult, God, Observer, Rule, State, Universe, fixpoint, rule

LLMCooperationState = MutableMapping[str, float]

_LLM_KEYS: Sequence[str] = (
    "alignment",
    "coverage",
    "creativity",
    "safety",
    "feedback",
    "memory",
    "tooling",
    "responsiveness",
    "autonomy",
    "trust",
    "evaluation",
    "resilience",
    "ethics",
    "cohesion",
    "experimentation",
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


def _blend(left: float, right: float) -> float:
    return (left + right) / 2.0


@dataclass(frozen=True)
class LLMAgentContribution:
    """Describe the cooperation strengths contributed by an LLM agent."""

    name: str
    alignment: float = 0.5
    coverage: float = 0.5
    creativity: float = 0.5
    safety: float = 0.5
    feedback: float = 0.5
    memory: float = 0.5
    tooling: float = 0.5
    responsiveness: float = 0.5
    autonomy: float = 0.5
    trust: float = 0.5
    evaluation: float = 0.5
    resilience: float = 0.5
    ethics: float = 0.5
    cohesion: float = 0.5
    experimentation: float = 0.5
    reliability: float = 1.0

    def weight(self) -> float:
        return max(0.0, float(self.reliability))

    def metric(self, key: str) -> float:
        return _bounded(float(getattr(self, key)))


def _weighted_average(agents: Sequence[LLMAgentContribution], key: str) -> float:
    weights = [agent.weight() for agent in agents]
    total = sum(weights)
    if total <= 0:
        weights = [1.0 for _ in agents]
        total = float(len(agents)) if agents else 1.0

    accumulator = 0.0
    for agent, weight in zip(agents, weights):
        accumulator += agent.metric(key) * weight
    if total == 0:  # pragma: no cover - defensive but unreachable after guard
        return 0.0
    return accumulator / total


def llm_cooperation_blueprint_from_agents(*agents: LLMAgentContribution) -> "LLMCooperationBlueprint":
    """Return a blueprint generated from the provided agent contributions."""

    if not agents:
        return LLMCooperationBlueprint()

    mapping = {key: _weighted_average(agents, key) for key in _LLM_KEYS}
    return LLMCooperationBlueprint(**mapping)


@dataclass
class LLMCooperationBlueprint:
    """Target configuration for the LLM cooperation network."""

    alignment: float = 1.0
    coverage: float = 1.0
    creativity: float = 1.0
    safety: float = 1.0
    feedback: float = 1.0
    memory: float = 1.0
    tooling: float = 1.0
    responsiveness: float = 1.0
    autonomy: float = 1.0
    trust: float = 1.0
    evaluation: float = 1.0
    resilience: float = 1.0
    ethics: float = 1.0
    cohesion: float = 1.0
    experimentation: float = 1.0

    def as_state(self) -> Mapping[str, float]:
        return {
            "alignment": _bounded(self.alignment),
            "coverage": _bounded(self.coverage),
            "creativity": _bounded(self.creativity),
            "safety": _bounded(self.safety),
            "feedback": _bounded(self.feedback),
            "memory": _bounded(self.memory),
            "tooling": _bounded(self.tooling),
            "responsiveness": _bounded(self.responsiveness),
            "autonomy": _bounded(self.autonomy),
            "trust": _bounded(self.trust),
            "evaluation": _bounded(self.evaluation),
            "resilience": _bounded(self.resilience),
            "ethics": _bounded(self.ethics),
            "cohesion": _bounded(self.cohesion),
            "experimentation": _bounded(self.experimentation),
        }


DEFAULT_LLM_COOPERATION: LLMCooperationState = {
    "alignment": 0.58,
    "coverage": 0.55,
    "creativity": 0.57,
    "safety": 0.6,
    "feedback": 0.52,
    "memory": 0.53,
    "tooling": 0.5,
    "responsiveness": 0.54,
    "autonomy": 0.48,
    "trust": 0.51,
    "evaluation": 0.49,
    "resilience": 0.5,
    "ethics": 0.62,
    "cohesion": 0.47,
    "experimentation": 0.56,
}


def _align_objectives(target: Mapping[str, float]) -> Rule:
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        alignment = _towards(_ensure_float(updated, "alignment"), target["alignment"], 0.34)
        ethics = _towards(_ensure_float(updated, "ethics"), target["ethics"], 0.33)

        safety_target = _bounded(
            target["safety"]
            + 0.2 * (ethics - target["ethics"])
        )
        safety = _towards(_ensure_float(updated, "safety"), safety_target, 0.32)

        trust_target = _bounded(
            target["trust"]
            + 0.25 * (alignment - target["alignment"])
            + 0.25 * (safety - target["safety"])
        )
        trust = _towards(_ensure_float(updated, "trust"), trust_target, 0.31)

        evaluation_target = _bounded(
            target["evaluation"] + 0.2 * (trust - target["trust"])
        )
        evaluation = _towards(_ensure_float(updated, "evaluation"), evaluation_target, 0.3)

        updated.update(
            {
                "alignment": _bounded(alignment),
                "safety": _bounded(safety),
                "ethics": _bounded(ethics),
                "trust": _bounded(trust),
                "evaluation": _bounded(evaluation),
            }
        )
        return updated

    return rule("align-objectives", apply, annotations={"target": dict(target)})


def _harmonise_capabilities(target: Mapping[str, float]) -> Rule:
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        alignment = _ensure_float(updated, "alignment")
        trust = _ensure_float(updated, "trust")
        safety = _ensure_float(updated, "safety")

        coverage_target = _bounded(
            target["coverage"]
            + 0.2 * (alignment - target["alignment"])
            + 0.2 * (trust - target["trust"])
        )
        coverage = _towards(_ensure_float(updated, "coverage"), coverage_target, 0.29)

        creativity_target = _bounded(
            target["creativity"] + 0.25 * (alignment - target["alignment"])
        )
        creativity = _towards(_ensure_float(updated, "creativity"), creativity_target, 0.31)

        experimentation_target = _bounded(
            target["experimentation"] + 0.2 * (creativity - target["creativity"])
        )
        experimentation = _towards(
            _ensure_float(updated, "experimentation"), experimentation_target, 0.3
        )

        feedback_target = _bounded(
            target["feedback"] + 0.25 * (trust - target["trust"])
        )
        feedback = _towards(_ensure_float(updated, "feedback"), feedback_target, 0.3)

        memory_target = _bounded(
            target["memory"] + 0.25 * (safety - target["safety"])
        )
        memory = _towards(_ensure_float(updated, "memory"), memory_target, 0.28)

        tooling_target = _bounded(
            target["tooling"] + 0.2 * (coverage - target["coverage"])
        )
        tooling = _towards(_ensure_float(updated, "tooling"), tooling_target, 0.27)

        cohesion_target = _bounded(
            target["cohesion"]
            + 0.2 * (alignment - target["alignment"])
            + 0.2 * (coverage - target["coverage"])
        )
        cohesion = _towards(_ensure_float(updated, "cohesion"), cohesion_target, 0.3)

        updated.update(
            {
                "coverage": _bounded(coverage),
                "creativity": _bounded(creativity),
                "experimentation": _bounded(experimentation),
                "feedback": _bounded(feedback),
                "memory": _bounded(memory),
                "tooling": _bounded(tooling),
                "cohesion": _bounded(cohesion),
            }
        )
        return updated

    return rule("harmonise-capabilities", apply)


def _stabilise_operations(target: Mapping[str, float]) -> Rule:
    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)

        evaluation = _ensure_float(updated, "evaluation")
        feedback = _ensure_float(updated, "feedback")

        responsiveness_target = _bounded(
            target["responsiveness"]
            + 0.2 * (evaluation - target["evaluation"])
            + 0.2 * (feedback - target["feedback"])
        )
        responsiveness = _towards(
            _ensure_float(updated, "responsiveness"), responsiveness_target, 0.33
        )

        autonomy_target = _bounded(
            target["autonomy"] + 0.2 * (evaluation - target["evaluation"])
        )
        autonomy = _towards(_ensure_float(updated, "autonomy"), autonomy_target, 0.3)

        resilience_target = _bounded(
            target["resilience"]
            + 0.2 * (autonomy - target["autonomy"])
            + 0.2 * (responsiveness - target["responsiveness"])
        )
        resilience = _towards(_ensure_float(updated, "resilience"), resilience_target, 0.31)

        updated.update(
            {
                "responsiveness": _bounded(responsiveness),
                "autonomy": _bounded(autonomy),
                "resilience": _bounded(resilience),
            }
        )
        return updated

    return rule("stabilise-operations", apply)


def _close_feedback_cycles(target: Mapping[str, float]) -> Rule:
    positive_keys = [key for key in _LLM_KEYS]
    average_target = sum(target[key] for key in positive_keys) / len(positive_keys)

    def apply(state: State, _ctx: object) -> State:
        updated = dict(state)
        average = sum(_ensure_float(updated, key) for key in positive_keys) / len(positive_keys)

        for key in positive_keys:
            target_adjusted = _bounded(
                target[key] + 0.15 * (average - average_target)
            )
            updated[key] = _bounded(
                _towards(_ensure_float(updated, key), target_adjusted, 0.18)
            )
        return updated

    return rule("close-feedback-cycles", apply, priority=-1)


def _build_llm_cooperation_rules(target: Mapping[str, float]) -> Sequence[Rule]:
    return (
        _align_objectives(target),
        _harmonise_capabilities(target),
        _stabilise_operations(target),
        _close_feedback_cycles(target),
    )


def llm_cooperation_metric(previous: State, current: State) -> float:
    """Measure coordinate-wise differences across the cooperation state."""

    delta = 0.0
    for key in _LLM_KEYS:
        delta += abs(_ensure_float(current, key) - _ensure_float(previous, key))
    return delta


def ideal_llm_cooperation_universe(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[LLMCooperationBlueprint] = None,
    observers: Optional[Sequence[Observer]] = None,
) -> Universe:
    """Build the canonical LLM cooperation universe."""

    if blueprint is None:
        blueprint = LLMCooperationBlueprint()
    target = dict(blueprint.as_state())

    if initial_state is None:
        state: LLMCooperationState = dict(DEFAULT_LLM_COOPERATION)
    else:
        state = {key: float(value) for key, value in initial_state.items()}

    return God.universe(state=state, rules=_build_llm_cooperation_rules(target), observers=observers)


def run_llm_cooperation(
    initial_state: Optional[Mapping[str, float]] = None,
    *,
    blueprint: Optional[LLMCooperationBlueprint] = None,
    observers: Optional[Sequence[Observer]] = None,
    epsilon: float = 1e-3,
    max_epoch: int = 128,
) -> FixpointResult:
    """Run the LLM cooperation universe until the network stabilises."""

    universe = ideal_llm_cooperation_universe(
        initial_state,
        blueprint=blueprint,
        observers=observers,
    )
    return fixpoint(universe, metric=llm_cooperation_metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "LLMAgentContribution",
    "LLMCooperationBlueprint",
    "DEFAULT_LLM_COOPERATION",
    "ideal_llm_cooperation_universe",
    "llm_cooperation_blueprint_from_agents",
    "llm_cooperation_metric",
    "run_llm_cooperation",
]

