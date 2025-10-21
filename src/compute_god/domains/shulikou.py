"""Symbolic calculus for orchestrating the spell metric known as ``术力口``.

The term ``术力口`` (shù lì kǒu) is an affectionate shorthand that mixes
``术`` (technique), ``力`` (power), and ``口`` (voice).  Practitioners often use
it to describe whether an incantation feels balanced: precision without power
fizzles out, brute force without articulation misfires, and a resonant chant
needs both.  This module models that intuition with lightweight data
structures so tests and sister runtimes can reason about spell layouts without
resorting to ad-hoc spreadsheets.

Three concepts show up repeatedly:

``ShuliKouVector``
    Three-axis vectors capturing technique, power, and voice contributions.
    They support normalisation and simple arithmetic to keep computations
    explicit.

``ShuliKouGlyph``
    A named channel describing how a particular ritual injects energy into the
    axes.  Glyphs are parameterised by intensity (how much energy they offer)
    and coherence (how disciplined that energy is).

``ShuliKouBlueprint`` and ``compose_shuli_channels``
    The blueprint specifies how sensitive a reading is to each axis and how to
    interpret coherence.  ``compose_shuli_channels`` folds a sequence of glyphs
    into a :class:`ShuliKouReading`, exposing derived metrics such as
    resonance (the headline spell strength) and balance (how evenly the axes
    are distributed).  The helper is also exported under the Hanzi alias
    :data:`术力口` for ergonomics in narrative-heavy modules.

None of the arithmetic aspires to be canonical magic theory; the goal is to
provide a deterministic, well-documented scaffold that captures the flavour of
spell balancing with enough structure for automated checks.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence, Tuple


@dataclass(frozen=True)
class ShuliKouVector:
    """Three-axis vector encoding technique, power, and voice components."""

    technique: float
    power: float
    voice: float

    def __post_init__(self) -> None:
        for name, value in (
            ("technique", self.technique),
            ("power", self.power),
            ("voice", self.voice),
        ):
            if not math.isfinite(value):  # pragma: no cover - defensive guard
                raise ValueError(f"{name} must be a finite number, got {value!r}")

    def __add__(self, other: "ShuliKouVector") -> "ShuliKouVector":
        return ShuliKouVector(
            self.technique + other.technique,
            self.power + other.power,
            self.voice + other.voice,
        )

    def scale(self, factor: float) -> "ShuliKouVector":
        """Return the vector scaled by ``factor``."""

        return ShuliKouVector(
            self.technique * factor,
            self.power * factor,
            self.voice * factor,
        )

    def l1(self) -> float:
        """Return the L1 norm (sum of absolute axis magnitudes)."""

        return abs(self.technique) + abs(self.power) + abs(self.voice)

    def energy(self) -> float:
        """Return the Euclidean energy of the vector."""

        return math.sqrt(self.technique**2 + self.power**2 + self.voice**2)

    def normalised(self) -> "ShuliKouVector":
        """Return a vector whose absolute values add up to one.

        When the vector carries no energy the zero vector is returned to avoid
        division by zero.  The method uses the L1 norm so that the distribution
        can be read as relative shares between the three axes.
        """

        total = self.l1()
        if total == 0.0:
            return ShuliKouVector(0.0, 0.0, 0.0)
        return self.scale(1.0 / total)

    def dot(self, other: "ShuliKouVector") -> float:
        """Return the dot product with another vector."""

        return (
            self.technique * other.technique
            + self.power * other.power
            + self.voice * other.voice
        )

    def dominant_axis(self) -> str:
        """Return the name of the axis with the highest absolute magnitude."""

        values = {
            "technique": abs(self.technique),
            "power": abs(self.power),
            "voice": abs(self.voice),
        }
        dominant = max(values.items(), key=lambda item: item[1])[0]
        return dominant

    def as_tuple(self) -> Tuple[float, float, float]:
        """Return a tuple representation of the vector."""

        return (self.technique, self.power, self.voice)


@dataclass(frozen=True)
class ShuliKouGlyph:
    """Describe how a ritual contributes to the three axes of ``术力口``."""

    name: str
    signature: ShuliKouVector
    intensity: float = 1.0
    coherence: float = 1.0

    def __post_init__(self) -> None:
        if self.intensity < 0.0:
            raise ValueError("intensity must be non-negative")
        if self.coherence < 0.0:
            raise ValueError("coherence must be non-negative")

    def weight(self, blueprint: "ShuliKouBlueprint") -> float:
        """Return the contribution weight under a blueprint."""

        return self.intensity * max(self.coherence, blueprint.coherence_floor)

    def weighted_signature(
        self, blueprint: "ShuliKouBlueprint"
    ) -> Tuple[ShuliKouVector, float]:
        """Return the weighted signature and the applied weight."""

        weight = self.weight(blueprint)
        weighted = ShuliKouVector(
            self.signature.technique * blueprint.technique_weight,
            self.signature.power * blueprint.power_weight,
            self.signature.voice * blueprint.voice_weight,
        ).scale(weight)
        return weighted, weight


@dataclass(frozen=True)
class ShuliKouBlueprint:
    """Parameters guiding how glyphs are interpreted when composed."""

    technique_weight: float = 0.42
    power_weight: float = 0.35
    voice_weight: float = 0.23
    resonance_curve: float = 1.4
    coherence_floor: float = 0.2

    def __post_init__(self) -> None:
        for name, value in (
            ("technique_weight", self.technique_weight),
            ("power_weight", self.power_weight),
            ("voice_weight", self.voice_weight),
        ):
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative")
        if self.resonance_curve <= 0.0:
            raise ValueError("resonance_curve must be positive")
        if self.coherence_floor < 0.0:
            raise ValueError("coherence_floor must be non-negative")

    def weights(self) -> ShuliKouVector:
        """Return the blueprint weights as a vector."""

        return ShuliKouVector(
            self.technique_weight,
            self.power_weight,
            self.voice_weight,
        )


@dataclass(frozen=True)
class ShuliKouReading:
    """Summary produced by :func:`compose_shuli_channels`."""

    technique: float
    power: float
    voice: float
    resonance: float
    alignment: float
    balance: float
    dominant_axis: str
    distribution: Tuple[float, float, float]
    average_coherence: float

    def vector(self) -> ShuliKouVector:
        """Return the reading as a :class:`ShuliKouVector`."""

        return ShuliKouVector(self.technique, self.power, self.voice)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def compose_shuli_channels(
    glyphs: Sequence[ShuliKouGlyph] | Iterable[ShuliKouGlyph],
    blueprint: ShuliKouBlueprint | None = None,
) -> ShuliKouReading:
    """Fold glyphs into a consolidated ``术力口`` reading.

    The helper works with any iterable to keep API friction low.  Each glyph is
    weighted by its intensity, coherence, and the blueprint weights.  Derived
    metrics are calculated as follows:

    ``resonance``
        Product of the vector's Euclidean energy and the alignment raised to
        ``resonance_curve``.  This rewards both raw strength and directional
        agreement with the blueprint.

    ``alignment``
        Similarity between the distribution of the reading and the blueprint's
        weight distribution, expressed as ``1 - L1_distance / 2`` so it sits in
        ``[0, 1]``.

    ``balance``
        How evenly the three axes are distributed once normalised.  It equals
        ``1 - (max_share - min_share)`` and therefore reaches one when all axes
        contribute equally.
    """

    blueprint = blueprint or ShuliKouBlueprint()

    total_vector = ShuliKouVector(0.0, 0.0, 0.0)
    total_weight = 0.0
    coherence_sum = 0.0
    glyph_count = 0

    for glyph in glyphs:
        contribution, weight = glyph.weighted_signature(blueprint)
        total_vector = total_vector + contribution
        total_weight += weight
        coherence_sum += max(glyph.coherence, blueprint.coherence_floor)
        glyph_count += 1

    if total_weight == 0.0:
        averaged = ShuliKouVector(0.0, 0.0, 0.0)
    else:
        averaged = total_vector.scale(1.0 / total_weight)

    distribution_vector = averaged.normalised()
    distribution = distribution_vector.as_tuple()

    target_distribution = blueprint.weights().normalised().as_tuple()
    l1_distance = sum(abs(a - b) for a, b in zip(distribution, target_distribution))
    alignment = _clamp(1.0 - 0.5 * l1_distance)

    resonance = averaged.energy() * (alignment**blueprint.resonance_curve)

    max_share = max(distribution)
    min_share = min(distribution)
    balance = _clamp(1.0 - (max_share - min_share))

    if averaged.l1() == 0.0:
        dominant_axis = "technique"
    else:
        dominant_axis = averaged.dominant_axis()

    average_coherence = (
        coherence_sum / glyph_count if glyph_count else 0.0
    )

    return ShuliKouReading(
        technique=averaged.technique,
        power=averaged.power,
        voice=averaged.voice,
        resonance=resonance,
        alignment=alignment,
        balance=balance,
        dominant_axis=dominant_axis,
        distribution=distribution,
        average_coherence=average_coherence,
    )


# Provide a narrative-friendly alias so call sites can write ``术力口(...)``.
术力口 = compose_shuli_channels

__all__ = [
    "ShuliKouVector",
    "ShuliKouGlyph",
    "ShuliKouBlueprint",
    "ShuliKouReading",
    "compose_shuli_channels",
    "术力口",
]

