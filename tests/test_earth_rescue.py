import pytest

from compute_god.earth_rescue import EarthState, RescueParameters, save_earth


def test_save_earth_converges_to_plan_goals():
    crisis = EarthState(temperature=3.2, pollution=0.7, cooperation=0.25)
    plan = RescueParameters(
        temperature_goal=1.4,
        pollution_goal=0.15,
        cooperation_goal=0.92,
        temperature_rate=0.35,
        pollution_rate=0.4,
        cooperation_rate=0.25,
    )

    result = save_earth(crisis, plan, epsilon=1e-8, max_epoch=256)

    assert result.converged

    final_state = result.universe.state

    assert final_state["temperature"] == pytest.approx(plan.temperature_goal, rel=1e-6, abs=1e-6)
    assert final_state["pollution"] == pytest.approx(plan.pollution_goal, rel=1e-6, abs=1e-6)
    assert final_state["cooperation"] == pytest.approx(plan.cooperation_goal, rel=1e-6, abs=1e-6)

    history = final_state["history"]
    assert len(history) == result.epochs + 1
    assert history[0]["temperature"] == pytest.approx(crisis.temperature)
    assert history[-1]["temperature"] == pytest.approx(plan.temperature_goal, rel=1e-6, abs=1e-6)


def test_rescue_parameters_validate_rates():
    with pytest.raises(ValueError):
        RescueParameters(temperature_rate=0.0)


def test_save_earth_rejects_unknown_history_key():
    crisis = EarthState(temperature=2.5, pollution=0.6, cooperation=0.4)
    plan = RescueParameters(history_keys=("temperature", "biodiversity"))

    with pytest.raises(KeyError):
        save_earth(crisis, plan)
