"""Tests for the guided screenshot utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from compute_god.screenshot import ScreenshotEnvironment


def test_component_bounds_requires_render() -> None:
    env = ScreenshotEnvironment()
    with pytest.raises(RuntimeError):
        env.component_bounds("hero:panel")

    image = env.render()
    hero_panel = env.component_bounds("hero:panel")
    assert hero_panel[0] == env.horizontal_margin + 6
    assert env.verify(image)


def test_render_save_and_verify(tmp_path: Path) -> None:
    env = ScreenshotEnvironment()
    image = env.render()

    palette = env.palette
    accent_bounds = env.component_bounds("hero:accent")
    accent_sample = (accent_bounds[0] + 40, accent_bounds[1] + 40)
    assert image.getpixel(accent_sample) == palette["accent_primary"]

    cta_bounds = env.component_bounds("hero:cta")
    cta_sample = (cta_bounds[0] + 20, cta_bounds[1] + 20)
    assert image.getpixel(cta_sample) == palette["accent_secondary"]

    feature_panel = env.component_bounds("feature:0")
    feature_sample = (feature_panel[0] + 100, feature_panel[1] + 60)
    assert image.getpixel(feature_sample) == palette["panel_surface"]

    tertiary_accent = env.component_bounds("feature:2:accent")
    tertiary_sample = (tertiary_accent[0] + 6, tertiary_accent[1] + 40)
    assert image.getpixel(tertiary_sample) == palette["accent_tertiary"]

    saved = env.save(tmp_path / "landing.png", image=image)
    assert saved.exists()

    assert env.verify(image)

    tampered = image.copy()
    tampered.putpixel((10, 10), (0, 0, 0))
    assert not env.verify(tampered)
