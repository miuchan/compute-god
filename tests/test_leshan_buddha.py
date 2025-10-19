"""Tests for the Leshan Giant Buddha model."""

from __future__ import annotations

import math

import pytest

from compute_god.leshan_buddha import (
    build_leshan_buddha,
    iter_segment_features,
)


def test_total_height_scales_linearly() -> None:
    base = build_leshan_buddha()
    enlarged = build_leshan_buddha(scale=1.2)

    assert math.isclose(
        enlarged.total_height(),
        base.total_height() * 1.2,
        rel_tol=1e-9,
    )


def test_drainage_margin_balances_capacity() -> None:
    model = build_leshan_buddha()
    capacity = model.drainage_capacity()

    rainfall = capacity * 60.0 / model.total_surface_area()
    margin = model.drainage_margin(rainfall_mm_per_hour=rainfall)
    assert math.isclose(margin, 0.0, abs_tol=1e-6)


def test_iter_segment_features_orders_features() -> None:
    model = build_leshan_buddha()
    features = list(iter_segment_features(model))
    assert ("head", "螺髻") in features
    assert features[0][0] == "lotus_pedestal"


def test_invalid_scale_rejected() -> None:
    with pytest.raises(ValueError):
        build_leshan_buddha(scale=0.0)


def test_negative_rainfall_rejected() -> None:
    model = build_leshan_buddha()
    with pytest.raises(ValueError):
        model.drainage_margin(rainfall_mm_per_hour=-1.0)
