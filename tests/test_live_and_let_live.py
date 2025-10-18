from compute_god import (
    DEFAULT_LIVE_AND_LET_LIVE_STATE,
    LiveAndLetLiveParameters,
    live_and_let_live_step,
    run_live_and_let_live,
    让自己活也让别人活,
)


def test_live_and_let_live_step_increases_fairness_and_vitality():
    params = LiveAndLetLiveParameters(balance_sensitivity=0.4)
    next_state = live_and_let_live_step(
        {
            "self_support": 0.2,
            "shared_support": 0.7,
            "trust": 0.3,
            "commons_health": 0.25,
            "resilience": 0.2,
        },
        params=params,
    )

    assert 0.0 <= next_state["fairness"] <= 1.0
    assert 0.0 <= next_state["vitality"] <= 1.0
    assert next_state["fairness"] > 0.4
    assert next_state["live_and_let_live_index"] >= next_state["vitality"]


def test_run_live_and_let_live_returns_full_history():
    params = LiveAndLetLiveParameters(adjustment_rate=0.5)
    history = run_live_and_let_live(params=params, epochs=12)

    assert len(history) == 13

    first = history[0]
    last = history[-1]

    assert last["trust"] >= first["trust"]
    assert last["commons_health"] >= first["commons_health"]


def test_alias_points_to_same_runner():
    assert 让自己活也让别人活 is run_live_and_let_live

    history = 让自己活也让别人活(epochs=0)
    assert history and history[0].keys() == DEFAULT_LIVE_AND_LET_LIVE_STATE.keys()
