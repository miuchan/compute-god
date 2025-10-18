"""Tests for :mod:`compute_god.gift`."""

from __future__ import annotations

import pytest

from compute_god.gift import (
    GiftWish,
    describe_gift_plan,
    prepare_gift_canvas,
    sculpt_gift_landscape,
)
from compute_god.landscape_learning import LandscapeLearningParameters


def test_sculpt_gift_landscape_highlights_primary_wish() -> None:
    canvas = prepare_gift_canvas(3, 3)
    wishes = [
        GiftWish((1, 1), intensity=1.3, label="花瓣灯"),
        GiftWish((0, 2), intensity=0.6, weight=0.5, label="耳语卡片"),
    ]
    params = LandscapeLearningParameters(learning_rate=0.5, smoothing=0.0)

    plan = sculpt_gift_landscape(
        canvas,
        wishes,
        params=params,
        epsilon=1e-6,
        max_epoch=48,
        track_history=True,
    )

    assert plan["converged"] is True
    highlights = plan["highlights"]
    assert highlights[0]["coordinate"] == (1, 1)
    assert pytest.approx(highlights[0]["elevation"], rel=1e-6, abs=1e-6) == 1.3
    assert highlights[0]["label"] == "花瓣灯"
    assert "history" in plan and len(plan["history"]) >= 1

    summary = describe_gift_plan(plan, axis_labels=("灵感", "材质"))
    assert "花瓣灯" in summary
    assert "灵感=1" in summary


def test_sculpt_gift_landscape_without_history() -> None:
    canvas = prepare_gift_canvas(2, 2)
    wishes = [GiftWish((0, 0), intensity=0.4)]
    params = LandscapeLearningParameters(learning_rate=0.5, smoothing=0.0)

    plan = sculpt_gift_landscape(
        canvas,
        wishes,
        params=params,
        track_history=False,
    )

    assert "history" not in plan


def test_sculpt_gift_landscape_requires_wish() -> None:
    canvas = prepare_gift_canvas(1, 1)

    with pytest.raises(ValueError):
        sculpt_gift_landscape(canvas, [])


def test_describe_gift_plan_handles_empty_highlights() -> None:
    plan = {"highlights": []}
    assert describe_gift_plan(plan) == "礼物景观尚未雕刻。"

