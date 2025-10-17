import pytest

from compute_god.s_follow_reading import (
    DEFAULT_FOLLOW_READING_STATE,
    FollowReadingBlueprint,
    FollowReadingFriendProfile,
    follow_reading_blueprint_from_friends,
    follow_reading_metric,
    follow_reading_rules,
    follow_reading_universe,
    run_follow_reading_network,
)


def test_follow_reading_blueprint_weighted_average() -> None:
    gentle_listener = FollowReadingFriendProfile(
        name="Gentle Listener",
        cohesion=0.4,
        curiosity=0.6,
        rhythm=0.5,
        reflection=0.45,
        encouragement=0.5,
        translation=0.55,
        accountability=0.52,
        playfulness=0.48,
        reliability=1.0,
    )
    energetic_reader = FollowReadingFriendProfile(
        name="Energetic Reader",
        cohesion=0.9,
        curiosity=0.85,
        rhythm=0.88,
        reflection=0.82,
        encouragement=0.86,
        translation=0.8,
        accountability=0.84,
        playfulness=0.83,
        reliability=2.0,
    )

    blueprint = follow_reading_blueprint_from_friends(gentle_listener, energetic_reader)

    assert blueprint.cohesion == pytest.approx((0.4 + 0.9 * 2) / 3)
    assert blueprint.translation == pytest.approx((0.55 + 0.8 * 2) / 3)
    assert blueprint.playfulness == pytest.approx((0.48 + 0.83 * 2) / 3)


def test_follow_reading_metric_tracks_progress() -> None:
    base_state = dict(DEFAULT_FOLLOW_READING_STATE)
    advanced_state = {key: value + 0.1 for key, value in base_state.items()}

    assert follow_reading_metric(base_state, base_state) == pytest.approx(0.0)
    assert follow_reading_metric(base_state, advanced_state) == pytest.approx(0.8)


def test_run_follow_reading_network_converges_to_blueprint() -> None:
    blueprint = FollowReadingBlueprint(
        cohesion=0.92,
        curiosity=0.88,
        rhythm=0.91,
        reflection=0.9,
        encouragement=0.94,
        translation=0.87,
        accountability=0.9,
        playfulness=0.93,
    )

    result = run_follow_reading_network(blueprint, epsilon=1e-4, max_epoch=128)

    assert result.converged is True
    assert result.epochs < 128

    final_state = result.universe.state
    for key, target in blueprint.as_state().items():
        assert key in final_state
        assert final_state[key] == pytest.approx(target, abs=0.05)

    # The rules are accessible for advanced scenarios (smoke test).
    rules = follow_reading_rules(blueprint)
    assert {rule.name for rule in rules} == {
        "follow-reading-cohesion",
        "follow-reading-reflection",
        "follow-reading-joy",
    }

    universe = follow_reading_universe(blueprint)
    assert set(universe.state) >= set(DEFAULT_FOLLOW_READING_STATE)
