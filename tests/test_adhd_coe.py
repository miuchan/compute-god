import math

import pytest

from compute_god.adhd import (
    ADHDProfile,
    CoefficientOfEngagement,
    StimulusProfile,
    simulate_coe,
)


def test_stimulus_profile_clamps_values():
    stimulus = StimulusProfile(novelty=1.7, structure=-0.2, reward=0.3, duration=-1)

    assert stimulus.novelty == 1.0
    assert stimulus.structure == 0.0
    assert stimulus.reward == 0.3
    assert stimulus.duration == 0.0


def test_adhd_profile_response_balances_biases():
    profile = ADHDProfile(
        baseline_focus=0.4,
        novelty_bias=0.8,
        structure_bias=0.3,
        reward_bias=0.6,
        variability=0.5,
    )

    first = profile.respond(StimulusProfile(novelty=0.9, structure=0.2, reward=0.8))

    assert first.focus == pytest.approx(0.81, abs=1e-6)
    assert first.regulation == pytest.approx(0.21, abs=1e-6)
    assert first.energy == pytest.approx(1.0, abs=1e-6)
    assert first.engagement == pytest.approx((0.81 + 0.21 + 1.0) / 3, abs=1e-6)
    assert first.duration == pytest.approx(1.0, abs=1e-6)

    second = profile.respond(StimulusProfile(novelty=0.1, structure=0.8, reward=0.3, duration=0.5))

    assert second.focus == pytest.approx(0.43, abs=1e-6)
    assert second.regulation == pytest.approx(0.79, abs=1e-6)
    assert second.energy == pytest.approx(0.06, abs=1e-6)
    assert second.engagement == pytest.approx((0.43 + 0.79 + 0.06) / 3, abs=1e-6)
    assert second.duration == pytest.approx(0.5, abs=1e-6)


def test_coefficient_of_engagement_tracks_trend():
    profile = ADHDProfile(
        baseline_focus=0.45,
        novelty_bias=0.7,
        structure_bias=0.4,
        reward_bias=0.5,
        variability=0.4,
    )

    stimuli = [
        StimulusProfile(0.8, 0.3, 0.9),
        StimulusProfile(0.2, 0.9, 0.4, duration=0.5),
    ]

    responses = [profile.respond(stimulus) for stimulus in stimuli]
    tracker = CoefficientOfEngagement(smoothing=0.4)

    first_value = tracker.observe(responses[0])
    assert first_value == pytest.approx(responses[0].engagement, abs=1e-6)

    second_alpha = min(1.0, 0.4 * responses[1].duration)
    expected_second = (1 - second_alpha) * first_value + second_alpha * responses[1].engagement
    second_value = tracker.observe(responses[1])

    assert second_value == pytest.approx(expected_second, abs=1e-6)
    assert tracker.trend(2) == pytest.approx((first_value + second_value) / 2, abs=1e-6)
    assert tracker.is_stable(epsilon=1.0, window=2)
    assert not tracker.is_stable(epsilon=0.01, window=2)

    with pytest.raises(ValueError):
        tracker.trend(0)

    with pytest.raises(ValueError):
        tracker.trend(3)

    with pytest.raises(ValueError):
        tracker.is_stable(window=1)


def test_simulate_coe_runs_sequence_and_resets():
    profile = ADHDProfile(
        baseline_focus=0.45,
        novelty_bias=0.7,
        structure_bias=0.5,
        reward_bias=0.4,
        variability=0.3,
    )

    stimuli = [
        StimulusProfile(0.7, 0.5, 0.6),
        StimulusProfile(0.3, 0.4, 0.2),
        StimulusProfile(0.6, 0.8, 0.9),
    ]

    tracker, responses = simulate_coe(profile, stimuli, smoothing=0.2)

    assert len(responses) == len(stimuli)
    assert len(tracker.history) == len(stimuli)
    assert tracker.history[0] == pytest.approx(responses[0].engagement, abs=1e-6)
    assert tracker.history[-1] == pytest.approx(tracker.value, abs=1e-6)

    for response in responses:
        assert 0.0 <= response.engagement <= 1.0

    tracker.reset()
    assert tracker.value is None
    assert tracker.history == []
    assert tracker.responses == []

