from __future__ import annotations

from typing import MutableMapping

from compute_god.panzi import Panzi, explore_origin


def test_panzi_records_origin_and_story() -> None:
    states: list[MutableMapping[str, object]] = [
        {"value": 0},
        {"value": 1},
        {"value": 2},
    ]

    panzi = Panzi(
        predicate=lambda s: s["value"] >= 2,
        metric=lambda a, b: abs(float(b["value"]) - float(a["value"]))
        if a is not b
        else 0.0,
    )

    observations = [panzi.observe(state) for state in states]

    assert [obs.exists for obs in observations] == [False, False, True]
    assert [obs.delta for obs in observations] == [0.0, 1.0, 1.0]
    assert all(obs.is_monotone for obs in observations[1:])

    assert panzi.origin_index == 2
    assert panzi.origin_delta() == 1.0

    story = panzi.origin_story()
    assert story is not None
    assert story.index == 2
    assert story.delta == 1.0
    assert story.state == {"value": 2}
    assert story.is_monotone is True
    assert story.is_stable is False
    assert story.stable_epoch is None


def test_panzi_reset_clears_state() -> None:
    states: list[MutableMapping[str, object]] = [
        {"flag": False},
        {"flag": True},
    ]

    panzi = Panzi(
        predicate=lambda s: bool(s["flag"]),
        metric=lambda a, b: 0.0 if a["flag"] == b["flag"] else 1.0,
    )

    for state in states:
        panzi.observe(state)

    assert panzi.origin_index == 1
    assert panzi.origin_state() == {"flag": True}

    panzi.reset()

    assert panzi.origin_index is None
    assert panzi.origin_state() is None
    assert panzi.existence.history == []
    assert panzi.stability.deltas == []
    assert panzi.stability.is_monotone is True


def test_explore_origin_returns_story() -> None:
    states: list[MutableMapping[str, object]] = [
        {"depth": 0},
        {"depth": 0.5},
        {"depth": 1.0},
    ]

    story = explore_origin(
        states,
        predicate=lambda s: s["depth"] >= 1.0,
        metric=lambda a, b: abs(float(b["depth"]) - float(a["depth"]))
        if a is not b
        else 0.0,
    )

    assert story is not None
    assert story.index == 2
    assert story.state == {"depth": 1.0}


def test_explore_origin_returns_none_when_missing() -> None:
    states: list[MutableMapping[str, object]] = [{"depth": 0.1}, {"depth": 0.2}]

    story = explore_origin(
        states,
        predicate=lambda s: s["depth"] >= 1.0,
        metric=lambda a, b: abs(float(b["depth"]) - float(a["depth"]))
        if a is not b
        else 0.0,
    )

    assert story is None

