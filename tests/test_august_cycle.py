from __future__ import annotations

import pytest

from compute_god.august import EndlessAugust


def test_endless_august_peek_does_not_advance() -> None:
    august = EndlessAugust()

    preview = august.peek(3)

    assert preview == ["Day 1", "Day 2", "Day 3"]
    assert august.current_day == "Day 1"
    assert august.turns == 0
    assert august.laps == 0


def test_endless_august_wraps_and_counts_laps() -> None:
    august = EndlessAugust()

    visited = [august.current_day]
    for _ in range(31):
        visited.append(august.advance())

    assert visited[:5] == ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"]
    assert august.current_day == "Day 1"
    assert august.turns == 31
    assert august.laps == 1
    assert august.timeline()[-3:] == ["Day 30", "Day 31", "Day 1"]


def test_endless_august_custom_cycle_and_multi_step() -> None:
    august = EndlessAugust(["dawn", "noon", "dusk"], start_index=1)

    assert august.current_day == "noon"

    final_label = august.advance(2)

    assert final_label == "dawn"
    assert august.current_day == "dawn"
    assert august.turns == 2
    assert august.laps == 0

    assert august.advance() == "noon"
    assert august.laps == 1


@pytest.mark.parametrize("method, value", [("peek", -1), ("advance", -2)])
def test_endless_august_rejects_negative_values(method: str, value: int) -> None:
    august = EndlessAugust(["warm", "cold"])

    with pytest.raises(ValueError):
        getattr(august, method)(value)
