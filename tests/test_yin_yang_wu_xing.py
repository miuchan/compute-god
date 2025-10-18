"""Tests for the Yin–Yang, Wu Xing and Ba Gua helpers."""

from __future__ import annotations

from itertools import islice

from compute_god.yin_yang_wu_xing import (
    Element,
    Polarity,
    arrange_bagua,
    generation_cycle,
    overcoming_cycle,
    trigram,
    trigram_from_lines,
)


def test_polarity_flip_and_symbol() -> None:
    assert Polarity.YIN.flip() is Polarity.YANG
    assert Polarity.YANG.flip() is Polarity.YIN
    assert Polarity.YIN.to_symbol() == "⚫"
    assert Polarity.YANG.to_symbol() == "⚪"


def test_wu_xing_generation_and_overcoming_cycles() -> None:
    generation = list(islice(generation_cycle(Element.WOOD), 6))
    assert generation == [
        Element.WOOD,
        Element.FIRE,
        Element.EARTH,
        Element.METAL,
        Element.WATER,
        Element.WOOD,
    ]

    overcoming = list(islice(overcoming_cycle(Element.WOOD), 5))
    assert overcoming == [
        Element.WOOD,
        Element.EARTH,
        Element.WATER,
        Element.FIRE,
        Element.METAL,
    ]

    assert Element.FIRE.generated_by() is Element.WOOD
    assert Element.WOOD.overcome_by() is Element.METAL


def test_trigram_lookup_and_counts() -> None:
    qian = trigram("乾")
    assert qian.pinyin == "qián"
    assert qian.element is Element.METAL
    assert qian.direction == "northwest"
    assert qian.family_role == "father"
    assert qian.yang_count() == 3
    assert qian.yin_count() == 0

    kun = trigram_from_lines((Polarity.YIN, Polarity.YIN, Polarity.YIN))
    assert kun.name == "坤"
    assert kun.inverted() is qian


def test_arrange_bagua_orders() -> None:
    pre_heaven = tuple(tri.name for tri in arrange_bagua("pre_heaven"))
    assert pre_heaven == ("乾", "兑", "离", "震", "巽", "坎", "艮", "坤")

    later_heaven = tuple(tri.name for tri in arrange_bagua("later_heaven"))
    assert later_heaven == ("坎", "艮", "震", "巽", "离", "坤", "兑", "乾")
