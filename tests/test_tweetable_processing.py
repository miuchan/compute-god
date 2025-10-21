"""Tests for :mod:`compute_god.tweetable_processing`."""

from __future__ import annotations

import math

import pytest

from compute_god.tweetable_processing import (
    ProcessingCircle,
    ProcessingFrame,
    TweetableProcessingSketch,
)


def test_generate_frame_matches_first_iteration() -> None:
    sketch = TweetableProcessingSketch()

    frame = sketch.generate_frame()

    assert isinstance(frame, ProcessingFrame)
    assert frame.width == pytest.approx(400.0)
    assert frame.background == (0.0, 20.0)
    assert len(frame.circles) == 256 * 5

    first_circle = frame.circles[0]
    assert isinstance(first_circle, ProcessingCircle)
    assert first_circle.fill == (400.0, 150.0)
    assert first_circle.diameter == pytest.approx(3.0)
    assert first_circle.x == pytest.approx(200.0)
    assert first_circle.y == pytest.approx(299.0)

    mirror_circle = frame.circles[1]
    assert mirror_circle.x == pytest.approx(200.0)
    assert mirror_circle.y == pytest.approx(299.0)

    shadow_circle = frame.circles[2]
    assert shadow_circle.fill == (400.0, 22.0)
    assert shadow_circle.x == pytest.approx(200.0)
    assert shadow_circle.y == pytest.approx(101.0)

    assert sketch.phase == pytest.approx(-0.05)


def test_phase_affects_subsequent_frame_geometry() -> None:
    sketch = TweetableProcessingSketch()
    first_frame = sketch.generate_frame()

    second_frame = sketch.generate_frame()
    phase_used = sketch.phase + 0.05
    angle = math.pi / sketch.angle_steps
    expected_radius = sketch.radius * math.cos(angle + phase_used / 2.0)
    expected_x = math.sin(angle) * expected_radius + sketch.centre
    expected_y = sketch.radius * math.cos(angle) + sketch.centre

    highlight_second_step = second_frame.circles[5]
    assert highlight_second_step.x == pytest.approx(expected_x)
    assert highlight_second_step.y == pytest.approx(expected_y)

    first_highlight = first_frame.circles[5]
    assert highlight_second_step.x != first_highlight.x
    assert sketch.phase == pytest.approx(-0.10)


def test_custom_width_updates_centre() -> None:
    sketch = TweetableProcessingSketch(width=640.0)
    assert sketch.centre == pytest.approx(320.0)

    frame = sketch.generate_frame()
    assert frame.width == pytest.approx(640.0)
    assert frame.circles[0].x == pytest.approx(320.0)
