"""Tests for the LLM agent taxonomy helper module."""

from __future__ import annotations

from compute_god import (
    AgentTaskRequirement,
    CAPABILITY_KEYS,
    compose_llm_stack,
    iter_llm_type_profiles,
    rank_llm_types,
    score_llm_profile,
)


def test_iter_llm_type_profiles_order_and_capabilities() -> None:
    profiles = iter_llm_type_profiles()
    assert [profile.acronym for profile in profiles] == [
        "GPT",
        "MoE",
        "LRM",
        "VLM",
        "SLM",
        "LAM",
        "HLM",
        "LCM",
    ]
    for profile in profiles:
        assert set(profile.capabilities.keys()) == set(CAPABILITY_KEYS)


def test_rank_llm_types_prefers_multimodal_for_sensory_tasks() -> None:
    requirement = AgentTaskRequirement(multimodal=1.0)
    ranked = rank_llm_types(requirement)
    assert ranked[0].acronym == "VLM"
    assert score_llm_profile(ranked[0], requirement) >= score_llm_profile(ranked[1], requirement)


def test_compose_llm_stack_balanced_mix() -> None:
    requirement = AgentTaskRequirement(multimodal=0.9, tool_use=0.85, collaboration=0.75)
    stack = compose_llm_stack(requirement, max_models=3)
    acronyms = [profile.acronym for profile in stack]
    assert "VLM" in acronyms
    assert "LAM" in acronyms
    assert len(stack) <= 3

    weights = requirement.weights()
    coverage = {key: 0.0 for key in CAPABILITY_KEYS}
    baseline = sum(coverage[key] * weights[key] for key in CAPABILITY_KEYS)

    for profile in stack:
        for key in CAPABILITY_KEYS:
            coverage[key] = max(coverage[key], profile.capability(key))
    improved = sum(coverage[key] * weights[key] for key in CAPABILITY_KEYS)
    assert improved > baseline


def test_requirement_defaults_to_uniform_weights() -> None:
    requirement = AgentTaskRequirement()
    weights = requirement.weights()
    assert all(value == 1.0 for value in weights.values())
    ranked = rank_llm_types(requirement)
    scores = [score_llm_profile(profile, requirement) for profile in ranked]
    assert scores == sorted(scores, reverse=True)
