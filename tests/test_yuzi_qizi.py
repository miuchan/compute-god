from __future__ import annotations

import math

import pytest

from compute_god import (
    GridSummary,
    Qizi,
    QiziParameters,
    Yuzi,
    YuziParameters,
    玉子,
    琦子,
)


def test_yuzi_builds_bilinear_grid() -> None:
    params = YuziParameters(
        width=3,
        height=2,
        base=1.0,
        x_weight=0.5,
        y_weight=-1.0,
        cross_weight=0.25,
    )
    yuzi = Yuzi(params)

    grid = yuzi.compute_grid()

    assert grid[(0, 0)] == pytest.approx(1.0)
    assert grid[(1, 0)] == pytest.approx(1.0 + 0.5)
    assert grid[(0, 1)] == pytest.approx(1.0 - 1.0)
    assert grid[(2, 1)] == pytest.approx(1.0 + 2 * 0.5 - 1.0 + 2 * 1 * 0.25)

    assert yuzi.value_at((2, 1)) == grid[(2, 1)]


def test_yuzi_accepts_custom_kernel() -> None:
    params = YuziParameters(width=2, height=2, base=0.0)

    def quadratic_kernel(x: int, y: int, config: YuziParameters) -> float:
        del config
        return x**2 + y**2

    yuzi = Yuzi(params, kernel=quadratic_kernel)
    grid = yuzi.compute_grid()

    assert grid[(0, 0)] == 0.0
    assert grid[(1, 1)] == 2.0


def test_qizi_modulates_yuzi_grid() -> None:
    yuzi_params = YuziParameters(width=2, height=2, base=0.0, x_weight=1.0, y_weight=0.5)
    params = QiziParameters(yuzi=yuzi_params, scale=2.0, offset=1.0, exponent=2.0)

    qizi = Qizi(params)
    modulated = qizi.compute_grid()

    base = Yuzi(yuzi_params).compute_grid()
    for coord in modulated:
        expected = (base[coord] ** 2.0) * 2.0 + 1.0
        assert modulated[coord] == pytest.approx(expected)


def test_qizi_summary_reports_extrema_and_mean() -> None:
    yuzi_params = YuziParameters(width=2, height=3, base=1.0, x_weight=-0.25, y_weight=0.5)
    params = QiziParameters(yuzi=yuzi_params, scale=1.5, offset=-2.0, exponent=1.0)

    summary = Qizi(params).summary()

    assert isinstance(summary, GridSummary)
    assert summary.min_coordinate == (1, 0)
    assert summary.max_coordinate == (0, 2)
    assert summary.minimum == pytest.approx(-0.875)
    assert summary.maximum == pytest.approx(1.0)
    assert math.isfinite(summary.mean)


def test_aliases_point_to_original_classes() -> None:
    assert 玉子 is Yuzi
    assert 琦子 is Qizi

    yuzi = 玉子(YuziParameters(width=1, height=1))
    qizi = 琦子(QiziParameters(yuzi=YuziParameters(width=1, height=1)))

    assert isinstance(yuzi, Yuzi)
    assert isinstance(qizi, Qizi)
