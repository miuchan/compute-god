"""Tests for :mod:`compute_god.pottery_gallery`."""

from compute_god.pottery_gallery import (
    PotteryDisplay,
    describe_display,
    generate_pottery_display,
)


def test_generate_default_display_structure() -> None:
    display = generate_pottery_display(seed=42)
    assert isinstance(display, PotteryDisplay)
    assert len(display.rows) == 4
    counts = [len(row.vessels) for row in display.rows]
    assert counts[0] > counts[-1]
    assert display.vessel_count() == sum(counts)
    assert all(v.height_cm > 0 for row in display.rows for v in row.vessels)
    assert all(v.diameter_cm >= 12.0 for row in display.rows for v in row.vessels)


def test_seed_is_deterministic() -> None:
    display_a = generate_pottery_display(seed=7)
    display_b = generate_pottery_display(seed=7)
    assert display_a == display_b


def test_description_mentions_rows() -> None:
    display = generate_pottery_display(seed=3, rows=3)
    narrative = describe_display(display)
    assert "共 3 层" in narrative
    for row in display.rows:
        assert f"第 {row.level} 层" in narrative
        assert str(len(row.vessels)) in narrative
