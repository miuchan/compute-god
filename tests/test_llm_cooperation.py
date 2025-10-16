from compute_god.llm_cooperation import (
    LLMAgentContribution,
    LLMCooperationBlueprint,
    llm_cooperation_blueprint_from_agents,
    llm_cooperation_metric,
    run_llm_cooperation,
)


def test_llm_cooperation_converges_to_blueprint():
    blueprint = LLMCooperationBlueprint().as_state()

    result = run_llm_cooperation(epsilon=1e-4, max_epoch=192)
    assert result.converged is True

    state = result.universe.state
    for key, target in blueprint.items():
        assert abs(state[key] - target) <= 1e-2


def test_llm_cooperation_metric_matches_absolute_difference():
    previous = {
        "alignment": 0.5,
        "coverage": 0.45,
        "creativity": 0.48,
        "safety": 0.5,
        "feedback": 0.42,
        "memory": 0.44,
        "tooling": 0.46,
        "responsiveness": 0.47,
        "autonomy": 0.4,
        "trust": 0.43,
        "evaluation": 0.41,
        "resilience": 0.45,
        "ethics": 0.52,
        "cohesion": 0.38,
        "experimentation": 0.49,
    }
    current = {
        "alignment": 0.8,
        "coverage": 0.76,
        "creativity": 0.74,
        "safety": 0.79,
        "feedback": 0.72,
        "memory": 0.71,
        "tooling": 0.73,
        "responsiveness": 0.75,
        "autonomy": 0.7,
        "trust": 0.77,
        "evaluation": 0.69,
        "resilience": 0.74,
        "ethics": 0.81,
        "cohesion": 0.73,
        "experimentation": 0.76,
    }

    delta = llm_cooperation_metric(previous, current)
    expected = sum(abs(current[key] - previous[key]) for key in previous)
    assert abs(delta - expected) <= 1e-9


def test_blueprint_from_agents_respects_reliability_weights():
    planner = LLMAgentContribution(
        "planner",
        alignment=0.9,
        coverage=0.85,
        creativity=0.6,
        safety=0.82,
        feedback=0.88,
        memory=0.8,
        tooling=0.76,
        responsiveness=0.7,
        autonomy=0.65,
        trust=0.84,
        evaluation=0.78,
        resilience=0.81,
        ethics=0.9,
        cohesion=0.79,
        experimentation=0.68,
        reliability=1.2,
    )
    artist = LLMAgentContribution(
        "artist",
        alignment=0.6,
        coverage=0.55,
        creativity=0.92,
        safety=0.58,
        feedback=0.62,
        memory=0.57,
        tooling=0.6,
        responsiveness=0.68,
        autonomy=0.7,
        trust=0.61,
        evaluation=0.59,
        resilience=0.6,
        ethics=0.63,
        cohesion=0.66,
        experimentation=0.91,
        reliability=0.8,
    )

    blueprint = llm_cooperation_blueprint_from_agents(planner, artist)
    state = blueprint.as_state()

    total_weight = planner.reliability + artist.reliability
    expected_alignment = (
        planner.alignment * planner.reliability + artist.alignment * artist.reliability
    ) / total_weight
    expected_creativity = (
        planner.creativity * planner.reliability + artist.creativity * artist.reliability
    ) / total_weight

    assert abs(state["alignment"] - expected_alignment) <= 1e-9
    assert abs(state["creativity"] - expected_creativity) <= 1e-9
