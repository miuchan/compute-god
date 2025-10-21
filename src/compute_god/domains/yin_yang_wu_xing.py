"""Symbolic helpers modelling 阴阳 (Yin–Yang), 五行 (Wu Xing) and 八卦 (Ba Gua).

The project often embraces poetic mathematical metaphors.  This module keeps
that tradition alive by providing small, well documented data structures for
working with the most recognisable triad in classical Chinese cosmology:

``阴阳`` represents complementary polarities, ``五行`` describes the cycle of
five transformative elements, while ``八卦`` arranges trigrams that encode
relationships between the elements.  The implementation is intentionally light
weight – it focuses on modelling the canonical relationships so that other
modules (and the tests) can reason about them without having to memorise the
myriad correspondences by heart.

The helpers are pure Python objects that keep the semantics easily inspectable.
Enumerations are used for the discrete sets (polarity and elements) whereas the
``Trigram`` dataclass captures the descriptive attributes that tend to be cited
in literature.  Utility functions expose the classical 生 (generating) and 克
(conquering) cycles together with standard arrangements of the 八卦 diagram.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Iterator, List, Tuple


class Polarity(Enum):
    """Enumeration of the two primordial polarities in the Yin–Yang system."""

    YIN = "yin"
    YANG = "yang"

    def flip(self) -> "Polarity":
        """Return the complementary polarity."""

        return Polarity.YANG if self is Polarity.YIN else Polarity.YIN

    def to_symbol(self) -> str:
        """Return the traditional Unicode symbol for the polarity."""

        return "⚫" if self is Polarity.YIN else "⚪"


class Element(Enum):
    """The five elements participating in the Wu Xing cycle."""

    WOOD = ("wood", "木")
    FIRE = ("fire", "火")
    EARTH = ("earth", "土")
    METAL = ("metal", "金")
    WATER = ("water", "水")

    def __init__(self, english: str, hanzi: str) -> None:
        self.english = english
        self.hanzi = hanzi

    def generates(self) -> "Element":
        """Return the element nourished by the current one (生 cycle)."""

        generation_order = {
            Element.WOOD: Element.FIRE,
            Element.FIRE: Element.EARTH,
            Element.EARTH: Element.METAL,
            Element.METAL: Element.WATER,
            Element.WATER: Element.WOOD,
        }
        return generation_order[self]

    def generated_by(self) -> "Element":
        """Return the element that nourishes the current one (inverse 生)."""

        for element, child in _GENERATION_PAIRS:
            if child is self:
                return element
        raise RuntimeError("Generation cycle corrupted")  # pragma: no cover

    def overcomes(self) -> "Element":
        """Return the element weakened by the current one (克 cycle)."""

        overcoming_order = {
            Element.WOOD: Element.EARTH,
            Element.EARTH: Element.WATER,
            Element.WATER: Element.FIRE,
            Element.FIRE: Element.METAL,
            Element.METAL: Element.WOOD,
        }
        return overcoming_order[self]

    def overcome_by(self) -> "Element":
        """Return the element that controls the current one (inverse 克)."""

        for element, target in _OVERCOMING_PAIRS:
            if target is self:
                return element
        raise RuntimeError("Overcoming cycle corrupted")  # pragma: no cover


_GENERATION_PAIRS: List[Tuple[Element, Element]] = [
    (Element.WOOD, Element.FIRE),
    (Element.FIRE, Element.EARTH),
    (Element.EARTH, Element.METAL),
    (Element.METAL, Element.WATER),
    (Element.WATER, Element.WOOD),
]

_OVERCOMING_PAIRS: List[Tuple[Element, Element]] = [
    (Element.WOOD, Element.EARTH),
    (Element.EARTH, Element.WATER),
    (Element.WATER, Element.FIRE),
    (Element.FIRE, Element.METAL),
    (Element.METAL, Element.WOOD),
]


@dataclass(frozen=True)
class Trigram:
    """Representation of a single Ba Gua trigram."""

    name: str
    pinyin: str
    meaning: str
    element: Element
    direction: str
    family_role: str
    lines: Tuple[Polarity, Polarity, Polarity]

    def yin_count(self) -> int:
        """Return the number of Yin lines in the trigram."""

        return sum(1 for line in self.lines if line is Polarity.YIN)

    def yang_count(self) -> int:
        """Return the number of Yang lines in the trigram."""

        return 3 - self.yin_count()

    def inverted(self) -> "Trigram":
        """Return the trigram obtained by flipping each line's polarity."""

        flipped_lines = tuple(line.flip() for line in self.lines)  # type: ignore[arg-type]
        return trigram_from_lines(flipped_lines)


_TRIGRAMS: Dict[str, Trigram] = {
    "乾": Trigram(
        name="乾",
        pinyin="qián",
        meaning="heaven",
        element=Element.METAL,
        direction="northwest",
        family_role="father",
        lines=(Polarity.YANG, Polarity.YANG, Polarity.YANG),
    ),
    "坤": Trigram(
        name="坤",
        pinyin="kūn",
        meaning="earth",
        element=Element.EARTH,
        direction="southwest",
        family_role="mother",
        lines=(Polarity.YIN, Polarity.YIN, Polarity.YIN),
    ),
    "震": Trigram(
        name="震",
        pinyin="zhèn",
        meaning="thunder",
        element=Element.WOOD,
        direction="east",
        family_role="eldest son",
        lines=(Polarity.YANG, Polarity.YIN, Polarity.YIN),
    ),
    "巽": Trigram(
        name="巽",
        pinyin="xùn",
        meaning="wind",
        element=Element.WOOD,
        direction="southeast",
        family_role="eldest daughter",
        lines=(Polarity.YIN, Polarity.YIN, Polarity.YANG),
    ),
    "坎": Trigram(
        name="坎",
        pinyin="kǎn",
        meaning="water",
        element=Element.WATER,
        direction="north",
        family_role="middle son",
        lines=(Polarity.YANG, Polarity.YIN, Polarity.YANG),
    ),
    "离": Trigram(
        name="离",
        pinyin="lí",
        meaning="fire",
        element=Element.FIRE,
        direction="south",
        family_role="middle daughter",
        lines=(Polarity.YIN, Polarity.YANG, Polarity.YIN),
    ),
    "艮": Trigram(
        name="艮",
        pinyin="gèn",
        meaning="mountain",
        element=Element.EARTH,
        direction="northeast",
        family_role="youngest son",
        lines=(Polarity.YANG, Polarity.YANG, Polarity.YIN),
    ),
    "兑": Trigram(
        name="兑",
        pinyin="duì",
        meaning="lake",
        element=Element.METAL,
        direction="west",
        family_role="youngest daughter",
        lines=(Polarity.YIN, Polarity.YANG, Polarity.YANG),
    ),
}

_TRIGRAMS_BY_LINES: Dict[Tuple[Polarity, Polarity, Polarity], Trigram] = {
    trigram.lines: trigram for trigram in _TRIGRAMS.values()
}


def trigram(name: str) -> Trigram:
    """Return the trigram with the given Chinese name."""

    return _TRIGRAMS[name]


def trigram_from_lines(lines: Iterable[Polarity]) -> Trigram:
    """Return the trigram that matches the given sequence of lines."""

    triple = tuple(lines)
    if triple not in _TRIGRAMS_BY_LINES:
        raise KeyError(f"Unknown trigram lines: {triple!r}")
    return _TRIGRAMS_BY_LINES[triple]


def generation_cycle(start: Element) -> Iterator[Element]:
    """Yield the Wu Xing generation sequence starting from ``start``."""

    current = start
    while True:
        yield current
        current = current.generates()


def overcoming_cycle(start: Element) -> Iterator[Element]:
    """Yield the Wu Xing overcoming sequence starting from ``start``."""

    current = start
    while True:
        yield current
        current = current.overcomes()


def arrange_bagua(arrangement: str = "later_heaven") -> Tuple[Trigram, ...]:
    """Return an ordered tuple of trigrams for the requested arrangement.

    Parameters
    ----------
    arrangement:
        Either ``"pre_heaven"`` (先天八卦) or ``"later_heaven"`` (后天八卦).
        The default picks the King Wen arrangement that is commonly used when
        mapping the trigrams onto geographic directions.
    """

    if arrangement == "pre_heaven":
        order = ("乾", "兑", "离", "震", "巽", "坎", "艮", "坤")
    elif arrangement == "later_heaven":
        order = ("坎", "艮", "震", "巽", "离", "坤", "兑", "乾")
    else:  # pragma: no cover - defensive guard
        raise ValueError(f"Unknown arrangement: {arrangement!r}")
    return tuple(trigram(name) for name in order)


__all__ = [
    "Polarity",
    "Element",
    "Trigram",
    "arrange_bagua",
    "generation_cycle",
    "overcoming_cycle",
    "trigram",
    "trigram_from_lines",
]

