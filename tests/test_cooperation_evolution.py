import pytest

from compute_god.cooperation_evolution import (
    CooperationParameters,
    DEFAULT_COOPERATION_STATE,
    evolve_cooperation,
    run_cooperation_evolution,
)


def test_cooperation_evolution_increases_alignment_over_time():
    history = run_cooperation_evolution(epochs=72)

    assert len(history) == 73

    initial = history[0]
    final = history[-1]

    assert final["cooperation"] > initial["cooperation"]
    assert final["trust"] > initial["trust"]
    assert pytest.approx(final["cooperation"] + final["defection"], abs=1e-9) == 1.0


def test_high_temptation_discourages_cooperation():
    params = CooperationParameters(temptation=1.8, learning_rate=0.35)
    history = run_cooperation_evolution(params=params, epochs=72)

    assert history[-1]["cooperation"] < history[0]["cooperation"]
    assert history[-1]["trust"] <= history[0]["trust"] + 1e-6


def test_evolution_clamps_invalid_inputs():
    state = {
        "cooperation": 1.2,
        "defection": -0.4,
        "trust": 1.7,
        "reputation": -0.8,
        "stability": DEFAULT_COOPERATION_STATE["stability"],
    }

    next_state = evolve_cooperation(state, CooperationParameters(mutation_rate=0.0))

    assert 0.0 <= next_state["cooperation"] <= 1.0
    assert 0.0 <= next_state["trust"] <= 1.0
    assert 0.0 <= next_state["reputation"] <= 1.0
    assert 0.0 <= next_state["defection"] <= 1.0
    assert pytest.approx(next_state["cooperation"] + next_state["defection"], abs=1e-9) == 1.0
