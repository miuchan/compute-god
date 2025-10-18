from __future__ import annotations

import pytest

from compute_god.pinduoduo import (
    BargainStep,
    HelperProfile,
    PinduoduoBargainAutomaton,
)


def test_basic_bargain_progression() -> None:
    profiles = {
        "new_user": HelperProfile(min_cut=4.0, max_cut=6.0, stage_multipliers=(1.0, 0.8, 0.5)),
        "regular": HelperProfile(min_cut=1.5, max_cut=2.5, stage_multipliers=(0.9, 0.7, 0.4)),
    }
    automaton = PinduoduoBargainAutomaton(target_amount=20.0, helper_profiles=profiles)

    steps = automaton.simulate([
        ("new_user", 1.0),
        ("regular", 0.8),
        ("regular", 0.6),
        ("new_user", 0.7),
        "regular",
        ("regular", 0.4),
        ("new_user", 0.6),
        ("regular", 0.9),
        ("new_user", 0.5),
        "regular",
    ])

    assert steps[-1].stage == "complete"
    assert pytest.approx(sum(step.cut_applied for step in steps), rel=1e-9) == 20.0
    assert automaton.remaining == 0.0
    # The extra helper after completion should be ignored because the simulation stops.
    assert len(steps) == 9


def test_step_reports_remaining_amount() -> None:
    profiles = {"friend": HelperProfile(min_cut=3.0, max_cut=5.0)}
    automaton = PinduoduoBargainAutomaton(target_amount=9.0, helper_profiles=profiles)

    first = automaton.step("friend", enthusiasm=0.5)
    assert isinstance(first, BargainStep)
    assert first.helper_type == "friend"
    assert first.remaining == pytest.approx(automaton.remaining)
    assert first.stage in {"early", "middle", "final", "complete"}


def test_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        HelperProfile(min_cut=-1.0, max_cut=2.0)

    with pytest.raises(ValueError):
        PinduoduoBargainAutomaton(target_amount=0, helper_profiles={})

    profile = HelperProfile(min_cut=1.0, max_cut=2.0)
    automaton = PinduoduoBargainAutomaton(target_amount=5.0, helper_profiles={"x": profile})
    with pytest.raises(ValueError):
        automaton.step("x", enthusiasm=-0.1)
    with pytest.raises(KeyError):
        automaton.step("unknown")


def test_reset_restores_target() -> None:
    profile = HelperProfile(min_cut=1.0, max_cut=1.5)
    automaton = PinduoduoBargainAutomaton(target_amount=3.0, helper_profiles={"x": profile})
    automaton.step("x", enthusiasm=0.5)
    automaton.reset()
    assert automaton.remaining == pytest.approx(automaton.target_amount)

