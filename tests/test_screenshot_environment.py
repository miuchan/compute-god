"""Tests for the guided screenshot utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from compute_god.screenshot import ScreenshotEnvironment


def test_component_bounds_requires_render() -> None:
    env = ScreenshotEnvironment()
    with pytest.raises(RuntimeError):
        env.component_bounds("search_bar")

    image = env.render()
    assert env.component_bounds("search_bar")[0] == env.horizontal_margin
    assert env.verify(image)


def test_render_save_and_verify(tmp_path: Path) -> None:
    env = ScreenshotEnvironment()
    image = env.render()

    palette = env.palette
    search_bounds = env.component_bounds("search_bar")
    search_sample = (search_bounds[0] + 120, search_bounds[1] + 50)
    assert image.getpixel(search_sample) == palette["search_surface"]

    first_card = env.component_bounds("card:0:accent")
    first_sample = (first_card[0] + 40, first_card[1] + 40)
    assert image.getpixel(first_sample) == palette["accent_0"]

    second_card = env.component_bounds("card:1:accent")
    second_sample = (second_card[0] + 40, second_card[1] + 40)
    assert image.getpixel(second_sample) == palette["accent_1"]

    saved = env.save(tmp_path / "search.png", image=image)
    assert saved.exists()

    assert env.verify(image)

    tampered = image.copy()
    tampered.putpixel((10, 10), (0, 0, 0))
    assert not env.verify(tampered)
