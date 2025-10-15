from __future__ import annotations

import math

import pytest

from compute_god import TianheLine, 天和线


def test_blend_endpoints() -> None:
    line = TianheLine(
        heaven={"clarity": 1.0, "harmony": 0.9},
        earth={"clarity": 0.2, "harmony": 0.3},
    )

    assert line.blend(0.0) == pytest.approx({"clarity": 0.2, "harmony": 0.3})
    assert line.blend(1.0) == pytest.approx({"clarity": 1.0, "harmony": 0.9})


def test_project_ratio_for_point_on_line() -> None:
    line = TianheLine(
        heaven={"clarity": 1.0, "harmony": 1.0},
        earth={"clarity": 0.0, "harmony": 0.0},
    )

    point = {"clarity": 0.4, "harmony": 0.4}
    assert math.isclose(line.project_ratio(point), 0.4, abs_tol=1e-9)
    assert line.deviation(point) == pytest.approx(0.0)


def test_project_clamps_outside_points() -> None:
    line = TianheLine(
        heaven={"clarity": 1.0},
        earth={"clarity": 0.0},
    )

    point = {"clarity": 1.8}
    assert math.isclose(line.project_ratio(point), 1.0)
    projection = line.project(point)
    assert projection["clarity"] == pytest.approx(1.0)
    assert line.deviation(point) == pytest.approx(0.8)


def test_unclamped_projection() -> None:
    line = TianheLine(
        heaven={"clarity": 1.0},
        earth={"clarity": 0.0},
        clamp=False,
    )

    point = {"clarity": 1.8}
    ratio = line.project_ratio(point, clamp=False)
    assert math.isclose(ratio, 1.8)
    projection = line.project(point, clamp=False)
    assert projection["clarity"] == pytest.approx(1.8)


def test_requires_non_degenerate_line() -> None:
    with pytest.raises(ValueError):
        TianheLine(heaven={"clarity": 0.5}, earth={"clarity": 0.5})


def test_chinese_alias() -> None:
    assert 天和线 is TianheLine

