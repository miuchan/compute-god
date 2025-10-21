"""LLM agent taxonomy and stack composition helpers.

The module distils eight common classes of large language models that appear in
agentic systems.  Each profile captures the model archetype's strengths across a
small, shared capability space so orchestration layers can reason about
complementary roles.  The goal is not to prescribe a fixed stack but to provide
lightweight heuristics for pairing the right specialism with the right task.

The taxonomy mirrors the infographic widely circulated in the tooling
community: GPT, MoE, LRM, VLM, SLM, LAM, HLM, and LCM.  For every entry the
module exposes:

``LLMTypeProfile``
    A frozen dataclass describing the archetype, including qualitative
    guidance and a bounded capability vector (values in ``[0.0, 1.0]``).

``AgentTaskRequirement``
    A simple weight specification for the capabilities an agent workflow cares
    about.  Requirements default to zero; callers emphasise dimensions by
    providing numbers in ``[0.0, 1.0]``.

``rank_llm_types`` and ``compose_llm_stack``
    Scoring helpers that recommend individual archetypes or a small stack of
    complementary ones based on a requirement profile.

The helpers purposely avoid heavyweight optimisation to keep them friendly to
interactive notebooks and CLI exploration.  Greedy selection works well for the
small, fixed taxonomy while remaining easy to audit and extend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence, Tuple

__all__ = [
    "CAPABILITY_KEYS",
    "LLMTypeProfile",
    "LLM_TYPE_PROFILES",
    "iter_llm_type_profiles",
    "AgentTaskRequirement",
    "score_llm_profile",
    "rank_llm_types",
    "compose_llm_stack",
]

CAPABILITY_KEYS: Tuple[str, ...] = (
    "general_reasoning",
    "specialisation",
    "long_context",
    "multimodal",
    "efficiency",
    "tool_use",
    "hierarchical_planning",
    "collaboration",
)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class LLMTypeProfile:
    """Describe an LLM archetype used inside agent stacks."""

    name: str
    acronym: str
    description: str
    capabilities: Mapping[str, float] = field(default_factory=dict)
    signature_tools: Tuple[str, ...] = ()
    best_for: Tuple[str, ...] = ()
    caution_notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Normalise the capability mapping so every exported profile remains
        # predictable even if callers pass dictionaries with missing keys.
        normalised: Dict[str, float] = {key: 0.0 for key in CAPABILITY_KEYS}
        for key, value in self.capabilities.items():
            if key not in CAPABILITY_KEYS:
                raise KeyError(f"Unknown capability dimension: {key!r}")
            normalised[key] = _bounded(value)
        object.__setattr__(self, "capabilities", normalised)

    def capability(self, key: str) -> float:
        """Return the archetype strength for the requested capability."""

        if key not in CAPABILITY_KEYS:
            raise KeyError(f"Unknown capability dimension: {key!r}")
        return self.capabilities.get(key, 0.0)


def _profile(
    *,
    name: str,
    acronym: str,
    description: str,
    capabilities: Mapping[str, float],
    signature_tools: Sequence[str],
    best_for: Sequence[str],
    caution_notes: Sequence[str],
) -> LLMTypeProfile:
    return LLMTypeProfile(
        name=name,
        acronym=acronym,
        description=description,
        capabilities=dict(capabilities),
        signature_tools=tuple(signature_tools),
        best_for=tuple(best_for),
        caution_notes=tuple(caution_notes),
    )


LLM_TYPE_PROFILES: Mapping[str, LLMTypeProfile] = {
    "GPT": _profile(
        name="Generative Pretrained Transformer",
        acronym="GPT",
        description=(
            "General-purpose reasoning models that balance scale, instruction"
            " tuning, and tool use support.  They provide dependable coverage"
            " for most agent workflows and act as default planners or"
            " overseers."
        ),
        capabilities={
            "general_reasoning": 0.95,
            "specialisation": 0.70,
            "long_context": 0.62,
            "multimodal": 0.45,
            "efficiency": 0.58,
            "tool_use": 0.88,
            "hierarchical_planning": 0.68,
            "collaboration": 0.66,
        },
        signature_tools=(
            "toolformer-style function calling",
            "retrieval augmented generation",
            "chain-of-thought coaching",
        ),
        best_for=(
            "core planning loops",
            "generalist copilots",
            "alignment-critical conversations",
        ),
        caution_notes=(
            "Watch latency on very long contexts.",
            "Keep an eye on creative saturation when no specialists are present.",
        ),
    ),
    "MoE": _profile(
        name="Mixture of Experts",
        acronym="MoE",
        description=(
            "Routers that dispatch prompts to specialised expert sub-models."
            "  They excel when a fleet needs highly tuned knowledge domains"
            " without sacrificing a shared interface."
        ),
        capabilities={
            "general_reasoning": 0.82,
            "specialisation": 0.96,
            "long_context": 0.54,
            "multimodal": 0.42,
            "efficiency": 0.48,
            "tool_use": 0.72,
            "hierarchical_planning": 0.64,
            "collaboration": 0.78,
        },
        signature_tools=(
            "expert routing",
            "knowledge distillation",
            "domain escalation policies",
        ),
        best_for=(
            "broad knowledge bases",
            "workflow hubs aggregating niche experts",
            "runtime specialisation of prompts",
        ),
        caution_notes=(
            "Routing policies require careful evaluation to avoid expert collapse.",
            "Infrastructure footprint can be significant.",
        ),
    ),
    "LRM": _profile(
        name="Long Reasoning Model",
        acronym="LRM",
        description=(
            "Architectures tuned for deliberate, multi-step reasoning with"
            " expansive context windows and patience for reflective loops."
        ),
        capabilities={
            "general_reasoning": 0.84,
            "specialisation": 0.58,
            "long_context": 0.95,
            "multimodal": 0.36,
            "efficiency": 0.46,
            "tool_use": 0.69,
            "hierarchical_planning": 0.82,
            "collaboration": 0.72,
        },
        signature_tools=(
            "tree-of-thought exploration",
            "self-consistency debates",
            "reflection and critique loops",
        ),
        best_for=(
            "long-form analysis",
            "compliance or audit trails",
            "multi-stage design reasoning",
        ),
        caution_notes=(
            "Deliberate loops increase compute cost and latency.",
            "Pair with alignment checks to avoid overconfident chains.",
        ),
    ),
    "VLM": _profile(
        name="Vision-Language Model",
        acronym="VLM",
        description=(
            "Multimodal models that jointly reason over imagery (and often"
            " audio/video streams) alongside text.  They are the sensory"
            " front-end for embodied or perceptual agents."
        ),
        capabilities={
            "general_reasoning": 0.62,
            "specialisation": 0.57,
            "long_context": 0.52,
            "multimodal": 0.97,
            "efficiency": 0.55,
            "tool_use": 0.66,
            "hierarchical_planning": 0.52,
            "collaboration": 0.58,
        },
        signature_tools=(
            "vision-language alignment",
            "grounded captioning",
            "spatial memory bindings",
        ),
        best_for=(
            "perception stacks",
            "UI automation with screenshot feedback",
            "robotics sensemaking",
        ),
        caution_notes=(
            "Sensitive to dataset biases; continuous evaluation is required.",
            "Ensure privacy controls when ingesting user imagery.",
        ),
    ),
    "SLM": _profile(
        name="Small Language Model",
        acronym="SLM",
        description=(
            "Parameter-efficient models optimised for on-device inference or"
            " ultra low latency responses.  They provide cheap reflexes and"
            " edge deployments."
        ),
        capabilities={
            "general_reasoning": 0.48,
            "specialisation": 0.53,
            "long_context": 0.38,
            "multimodal": 0.34,
            "efficiency": 0.96,
            "tool_use": 0.59,
            "hierarchical_planning": 0.37,
            "collaboration": 0.51,
        },
        signature_tools=(
            "quantisation-aware adapters",
            "distillation from frontier models",
            "specialised device runtimes",
        ),
        best_for=(
            "edge inference",
            "privacy-preserving local agents",
            "fast guardrails and pre-filters",
        ),
        caution_notes=(
            "Pair with oversight for complex reasoning tasks.",
            "Memory limitations require concise prompts.",
        ),
    ),
    "LAM": _profile(
        name="Large Action Model",
        acronym="LAM",
        description=(
            "Controllers that translate high-level goals into precise tool or"
            " API calls.  They shine when automations need structured plans"
            " with verifiable execution traces."
        ),
        capabilities={
            "general_reasoning": 0.66,
            "specialisation": 0.68,
            "long_context": 0.58,
            "multimodal": 0.48,
            "efficiency": 0.61,
            "tool_use": 0.96,
            "hierarchical_planning": 0.83,
            "collaboration": 0.63,
        },
        signature_tools=(
            "function execution sandboxes",
            "workflow graphs",
            "structured logging",
        ),
        best_for=(
            "complex tool orchestration",
            "software automation",
            "back-office operations",
        ),
        caution_notes=(
            "Require consistent schema evolution across toolchains.",
            "Guard against cascading tool errors with simulators.",
        ),
    ),
    "HLM": _profile(
        name="Hierarchical Language Model",
        acronym="HLM",
        description=(
            "Stacks that explicitly separate strategic, tactical, and"
            " operational reasoning.  Useful when coordination spans long"
            " horizons or involves multiple sub-agents."
        ),
        capabilities={
            "general_reasoning": 0.71,
            "specialisation": 0.61,
            "long_context": 0.88,
            "multimodal": 0.47,
            "efficiency": 0.52,
            "tool_use": 0.77,
            "hierarchical_planning": 0.97,
            "collaboration": 0.74,
        },
        signature_tools=(
            "multi-level memory",
            "plan decomposition",
            "cross-agent alignment",
        ),
        best_for=(
            "mission planning",
            "enterprise knowledge management",
            "simulation governance",
        ),
        caution_notes=(
            "Design interfaces carefully so tiers stay in sync.",
            "May require orchestration cost controls on long missions.",
        ),
    ),
    "LCM": _profile(
        name="Large Collaboration Model",
        acronym="LCM",
        description=(
            "Coordination-first models that monitor, negotiate, and optimise"
            " agent teamwork.  They emphasise shared context, feedback loops,"
            " and resilience."
        ),
        capabilities={
            "general_reasoning": 0.68,
            "specialisation": 0.63,
            "long_context": 0.59,
            "multimodal": 0.46,
            "efficiency": 0.57,
            "tool_use": 0.71,
            "hierarchical_planning": 0.69,
            "collaboration": 0.97,
        },
        signature_tools=(
            "cooperation dashboards",
            "feedback analytics",
            "conflict mediation protocols",
        ),
        best_for=(
            "agent networks with shared memory",
            "human-in-the-loop facilitation",
            "resilience and trust monitoring",
        ),
        caution_notes=(
            "Requires high-quality telemetry streams.",
            "Define escalation paths for irreconcilable conflicts.",
        ),
    ),
}


def iter_llm_type_profiles() -> Tuple[LLMTypeProfile, ...]:
    """Return all taxonomy profiles in canonical order."""

    return tuple(LLM_TYPE_PROFILES[key] for key in ("GPT", "MoE", "LRM", "VLM", "SLM", "LAM", "HLM", "LCM"))


@dataclass(frozen=True)
class AgentTaskRequirement:
    """Weights describing how much an agent workflow values each capability."""

    general_reasoning: float = 0.0
    specialisation: float = 0.0
    long_context: float = 0.0
    multimodal: float = 0.0
    efficiency: float = 0.0
    tool_use: float = 0.0
    hierarchical_planning: float = 0.0
    collaboration: float = 0.0

    def weights(self) -> Dict[str, float]:
        mapping = {
            "general_reasoning": _bounded(self.general_reasoning),
            "specialisation": _bounded(self.specialisation),
            "long_context": _bounded(self.long_context),
            "multimodal": _bounded(self.multimodal),
            "efficiency": _bounded(self.efficiency),
            "tool_use": _bounded(self.tool_use),
            "hierarchical_planning": _bounded(self.hierarchical_planning),
            "collaboration": _bounded(self.collaboration),
        }
        if all(value == 0.0 for value in mapping.values()):
            return {key: 1.0 for key in CAPABILITY_KEYS}
        return mapping


def score_llm_profile(profile: LLMTypeProfile, requirement: AgentTaskRequirement) -> float:
    """Return the weighted score of an archetype under the given requirement."""

    weights = requirement.weights()
    return sum(profile.capability(key) * weights[key] for key in CAPABILITY_KEYS)


def rank_llm_types(requirement: AgentTaskRequirement) -> Tuple[LLMTypeProfile, ...]:
    """Return taxonomy profiles sorted by suitability for the requirement."""

    return tuple(
        sorted(
            iter_llm_type_profiles(),
            key=lambda profile: score_llm_profile(profile, requirement),
            reverse=True,
        )
    )


def compose_llm_stack(
    requirement: AgentTaskRequirement,
    *,
    max_models: int = 3,
) -> Tuple[LLMTypeProfile, ...]:
    """Greedily compose a complementary stack of archetypes."""

    if max_models <= 0:
        return ()

    available = list(iter_llm_type_profiles())
    selected: list[LLMTypeProfile] = []
    coverage: Dict[str, float] = {key: 0.0 for key in CAPABILITY_KEYS}
    weights = requirement.weights()

    def coverage_score(candidate: Mapping[str, float]) -> float:
        return sum(candidate[key] * weights[key] for key in CAPABILITY_KEYS)

    baseline = coverage_score(coverage)

    for _ in range(min(max_models, len(available))):
        best_index = -1
        best_gain = 0.0
        best_coverage: MutableMapping[str, float] | None = None

        for index, profile in enumerate(available):
            candidate = dict(coverage)
            for key in CAPABILITY_KEYS:
                candidate[key] = max(candidate[key], profile.capability(key))
            gain = coverage_score(candidate) - baseline
            if gain > best_gain:
                best_gain = gain
                best_index = index
                best_coverage = candidate

        if best_index < 0 or best_gain <= 0.0 or best_coverage is None:
            break

        selected.append(available.pop(best_index))
        coverage = dict(best_coverage)
        baseline += best_gain

    return tuple(selected)
