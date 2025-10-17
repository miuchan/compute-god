import pytest

from compute_god import (
    ReimuNextSolution,
    TOUHOU_DEFAULT_BLUEPRINT,
    TouhouIncidentBlueprint,
    reimu_next_solution,
    run_touhou_incident,
    touhou_incident_metric,
    touhou_incident_universe,
    博丽灵梦下一解,
)


def test_touhou_incident_converges_to_blueprint() -> None:
    blueprint = TouhouIncidentBlueprint(
        reimu_focus=0.9,
        youkai_pressure=0.28,
        border_resilience=0.85,
    )
    result = run_touhou_incident(blueprint=blueprint, epsilon=1e-6, max_epoch=256)
    assert result.converged

    state = result.universe.state
    assert state["reimu_focus"] == pytest.approx(blueprint.reimu_focus, abs=1e-3)
    assert state["youkai_pressure"] == pytest.approx(blueprint.youkai_pressure, abs=1e-3)
    assert state["border_stability"] == pytest.approx(blueprint.border_resilience, abs=1e-3)
    assert state["incident_intensity"] == pytest.approx(0.0, abs=5e-4)
    assert 0.7 <= state["solution_clarity"] <= 1.0


def test_touhou_metric_accounts_for_all_coordinates() -> None:
    previous = {
        "reimu_focus": 0.2,
        "youkai_pressure": 0.5,
        "border_stability": 0.4,
        "solution_clarity": 0.55,
        "incident_intensity": 0.3,
    }
    current = {
        "reimu_focus": 0.4,
        "youkai_pressure": 0.3,
        "border_stability": 0.6,
        "solution_clarity": 0.7,
        "incident_intensity": 0.1,
    }
    expected = sum(abs(current[key] - previous[key]) for key in current)
    assert touhou_incident_metric(previous, current) == pytest.approx(expected)


def test_reimu_next_solution_classification_variants() -> None:
    result = run_touhou_incident()
    summary = reimu_next_solution(result.universe.state)
    assert isinstance(summary, ReimuNextSolution)
    assert summary.status == "incident-resolved"
    assert summary.solution_clarity >= 0.74

    intense = reimu_next_solution(
        {
            "reimu_focus": 0.58,
            "youkai_pressure": TOUHOU_DEFAULT_BLUEPRINT.youkai_pressure + 0.25,
            "border_stability": 0.42,
        }
    )
    assert intense.status == "heightened-incident"

    focused = reimu_next_solution(
        {
            "reimu_focus": 0.82,
            "youkai_pressure": 0.41,
            "border_stability": 0.72,
            "solution_clarity": 0.76,
            "incident_intensity": 0.12,
        }
    )
    assert focused.status == "focused-intervention"

    support = reimu_next_solution(
        {
            "reimu_focus": 0.6,
            "youkai_pressure": 0.4,
            "border_stability": 0.58,
            "solution_clarity": 0.62,
            "incident_intensity": 0.22,
        }
    )
    assert support.status == "needs-border-support"

    assert 博丽灵梦下一解 is reimu_next_solution


def test_touhou_universe_rejects_unknown_keys() -> None:
    with pytest.raises(KeyError):
        touhou_incident_universe(initial_state={"mystery": 0.5})
