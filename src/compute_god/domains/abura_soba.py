"""Playful yet deterministic helpers to assemble a bowl of 油そば.

The project enjoys sprinkling its computational abstractions with culinary or
poetic references.  This module continues that tradition with a tiny model of
``油そば`` (abura soba / oil noodles).  Rather than attempting to be a
full-fledged food simulator, it provides lightweight dataclasses to describe the
key layers—noodles, tare, aromatic oil, and toppings—and a function that
combines them into a flavour profile that unit tests can reason about.

The goal is to keep things whimsical while remaining completely deterministic.
Every numeric transformation is carefully documented so contributors can tweak
the parameters with confidence.  The resulting :class:`AburaSobaProfile` offers
readable metrics such as ``richness`` or ``balance`` together with a small
human-friendly recommendation on how to finish the bowl.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass(frozen=True)
class NoodleCanvas:
    """Describe the structural qualities of the noodle base.

    Parameters
    ----------
    hydration:
        Hydration level of the dough expressed as a fraction.  Values must lie
        within ``(0, 1]``.
    chewiness:
        Springiness of the noodle.  Must be strictly positive.
    thickness:
        Thickness in millimetres.  Must be strictly positive.
    """

    hydration: float
    chewiness: float
    thickness: float

    def __post_init__(self) -> None:  # pragma: no cover - simple validation
        if not (0.0 < self.hydration <= 1.0):
            raise ValueError("hydration must be within (0, 1]")
        if self.chewiness <= 0:
            raise ValueError("chewiness must be positive")
        if self.thickness <= 0:
            raise ValueError("thickness must be positive")

    @property
    def texture_index(self) -> float:
        """Return a normalised texture score for the noodle base."""

        hydration_penalty = 1.0 + abs(self.hydration - 0.58) * 3.5
        return (self.chewiness * self.thickness) / hydration_penalty


@dataclass(frozen=True)
class TareBlend:
    """Descriptor for the tare (sauce) layer of the bowl."""

    salinity: float
    umami: float
    sweetness: float = 0.0
    acidity: float = 0.0

    def __post_init__(self) -> None:  # pragma: no cover - simple validation
        if self.salinity < 0:
            raise ValueError("salinity cannot be negative")
        if self.umami < 0:
            raise ValueError("umami cannot be negative")
        if self.sweetness < 0:
            raise ValueError("sweetness cannot be negative")
        if self.acidity < 0:
            raise ValueError("acidity cannot be negative")

    @property
    def savoury_depth(self) -> float:
        """Return a weighted measure of how deep the tare tastes."""

        return (
            0.7 * self.umami
            + 0.4 * self.salinity
            + 0.2 * self.sweetness
            - 0.1 * self.acidity
        )


@dataclass(frozen=True)
class OilLayer:
    """Representation of the aromatic oil mixture."""

    aroma: float
    viscosity: float
    spice: float = 0.0

    def __post_init__(self) -> None:  # pragma: no cover - simple validation
        if self.aroma <= 0:
            raise ValueError("aroma must be positive")
        if self.viscosity <= 0:
            raise ValueError("viscosity must be positive")
        if self.spice < 0:
            raise ValueError("spice cannot be negative")

    @property
    def lushness(self) -> float:
        """Return the perceived richness contributed by the oil layer."""

        spice_boost = 1.0 + 0.25 * self.spice
        aromatic_body = 0.6 * self.aroma + 0.4 * self.spice
        return self.viscosity * aromatic_body * spice_boost


@dataclass(frozen=True)
class Topping:
    """Simple descriptor for toppings stirred into the bowl."""

    name: str
    intensity: float
    crunch: float = 0.0

    def __post_init__(self) -> None:  # pragma: no cover - simple validation
        if not self.name:
            raise ValueError("topping name cannot be empty")
        if self.intensity <= 0:
            raise ValueError("intensity must be positive")
        if self.crunch < 0:
            raise ValueError("crunch cannot be negative")


@dataclass
class AburaSobaProfile:
    """Aggregate flavour and texture information for an assembled bowl."""

    richness: float
    brightness: float
    texture: float
    crunch: float
    balance: float
    recommendation: str
    toppings: List[str] = field(default_factory=list)


def assemble_abura_soba(
    noodles: NoodleCanvas,
    tare: TareBlend,
    oil: OilLayer,
    toppings: Sequence[Topping] | None = None,
    /,
    *,
    vinegar: float = 0.0,
    chili_oil: float = 0.0,
) -> AburaSobaProfile:
    """Compose a bowl of abura soba from the provided components.

    The function computes several interpretable metrics:

    ``richness``
        Body contributed by the oil and tare.
    ``brightness``
        Perceived high notes introduced by vinegar and sweetness.
    ``texture``
        Combined noodle bite and structural lift from crunchy toppings.
    ``crunch``
        Raw crunch value contributed by the toppings.
    ``balance``
        How well the bowl balances richness with brightness/texture.
    ``recommendation``
        Small textual hint on how to finish the bowl.
    """

    topping_list: Sequence[Topping] = toppings if toppings is not None else ()

    noodle_texture = noodles.texture_index
    tare_depth = tare.savoury_depth
    oil_richness = oil.lushness

    total_crunch = sum(t.crunch for t in topping_list)
    total_intensity = sum(t.intensity for t in topping_list)

    richness = oil_richness * (1.0 + 0.03 * tare.salinity) + 0.35 * chili_oil
    brightness = tare.acidity + 0.5 * tare.sweetness + vinegar
    texture = noodle_texture + 0.08 * total_crunch
    umami_wave = tare_depth + 0.15 * total_intensity

    balance_drive = richness + umami_wave
    balance_anchor = texture + brightness
    balance = 1.0 / (1.0 + abs(balance_drive - balance_anchor))
    balance = max(0.0, min(1.0, balance))

    if balance >= 0.75:
        recommendation = "Vigorously mix before slurping (豪快に混ぜる)"
    elif brightness > richness:
        recommendation = "Add a touch of chili oil then mix gently."
    else:
        recommendation = "Brighten with vinegar before tossing."

    return AburaSobaProfile(
        richness=richness,
        brightness=brightness,
        texture=texture,
        crunch=total_crunch,
        balance=balance,
        recommendation=recommendation,
        toppings=[t.name for t in topping_list],
    )


def 油そば(*args, **kwargs) -> AburaSobaProfile:
    """Japanese alias so that callers can embrace the playful API surface."""

    return assemble_abura_soba(*args, **kwargs)


__all__ = [
    "AburaSobaProfile",
    "NoodleCanvas",
    "OilLayer",
    "TareBlend",
    "Topping",
    "assemble_abura_soba",
    "油そば",
]

