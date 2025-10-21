"""Cloud village cooperative built on the ``术力口`` calculus.

The ``术力口云村合作社`` is a narrative wrapper around the numeric scaffold
provided by :mod:`compute_god.shulikou`.  The cooperative describes how a small
village in the clouds aligns its spellcraft through roles, initiatives, and a
shared blueprint.  Each member contributes a :class:`~compute_god.shulikou.ShuliKouGlyph`
whose signature encodes their ritual strengths.  Initiatives remix those glyphs
with lightweight amplification factors so storytellers can reason about
collective projects without re-deriving the arithmetic.

The module stays intentionally small: it exposes dataclasses that structure the
roster and helpers that fold glyphs into :class:`~compute_god.shulikou.ShuliKouReading`
objects.  This keeps the cooperative interoperable with the broader
``术力口`` ecosystem while remaining friendly to automated tests and sister
runtimes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

from .shulikou import (
    ShuliKouBlueprint,
    ShuliKouGlyph,
    ShuliKouReading,
    ShuliKouVector,
    compose_shuli_channels,
)


@dataclass(frozen=True)
class CooperativeMember:
    """Roster entry for the cooperative."""

    name: str
    role: str
    glyph: ShuliKouGlyph
    responsibilities: Tuple[str, ...]


@dataclass(frozen=True)
class CooperativeInitiative:
    """Cooperative project that reuses member glyphs with optional amplification."""

    name: str
    focus: str
    participants: Tuple[str, ...]
    amplification: float = 1.0

    def glyphs_for(self, roster: Mapping[str, CooperativeMember]) -> Tuple[ShuliKouGlyph, ...]:
        """Return glyphs for participants, applying amplification when requested."""

        glyphs: list[ShuliKouGlyph] = []
        for participant in self.participants:
            member = roster[participant]
            if self.amplification == 1.0:
                glyphs.append(member.glyph)
            else:
                glyphs.append(
                    ShuliKouGlyph(
                        name=f"{member.glyph.name}·{self.name}",
                        signature=member.glyph.signature,
                        intensity=member.glyph.intensity * self.amplification,
                        coherence=member.glyph.coherence,
                    )
                )
        return tuple(glyphs)


@dataclass(frozen=True)
class CloudVillageCooperative:
    """Bundle of the cooperative blueprint, roster, and initiatives."""

    name: str
    blueprint: ShuliKouBlueprint
    members: Tuple[CooperativeMember, ...]
    initiatives: Tuple[CooperativeInitiative, ...] = ()

    def roster(self) -> Dict[str, CooperativeMember]:
        """Return a mapping from member name to :class:`CooperativeMember`."""

        return {member.name: member for member in self.members}

    def reading(self) -> ShuliKouReading:
        """Aggregate every member glyph into a cooperative reading."""

        glyphs = (member.glyph for member in self.members)
        return compose_shuli_channels(glyphs, self.blueprint)

    def role_readings(self) -> Dict[str, ShuliKouReading]:
        """Return ``术力口`` readings aggregated by role."""

        grouped: Dict[str, list[ShuliKouGlyph]] = {}
        for member in self.members:
            grouped.setdefault(member.role, []).append(member.glyph)
        return {
            role: compose_shuli_channels(glyphs, self.blueprint)
            for role, glyphs in grouped.items()
        }

    def initiative_readings(self) -> Dict[str, ShuliKouReading]:
        """Return readings for each initiative under the cooperative blueprint."""

        roster = self.roster()
        return {
            initiative.name: compose_shuli_channels(
                initiative.glyphs_for(roster), self.blueprint
            )
            for initiative in self.initiatives
        }


def build_shulikou_cloud_village() -> CloudVillageCooperative:
    """Return a preconfigured ``术力口云村合作社`` instance."""

    blueprint = ShuliKouBlueprint(
        technique_weight=1.0,
        power_weight=1.0,
        voice_weight=1.0,
        resonance_curve=1.3,
        coherence_floor=0.25,
    )

    members = (
        CooperativeMember(
            name="云织守",
            role="weaver",
            glyph=ShuliKouGlyph(
                name="cloud-loom",
                signature=ShuliKouVector(0.8, 0.1, 0.1),
                intensity=1.0,
                coherence=0.9,
            ),
            responsibilities=("loom maintenance", "pattern archive"),
        ),
        CooperativeMember(
            name="雾农",
            role="gardener",
            glyph=ShuliKouGlyph(
                name="mist-allotments",
                signature=ShuliKouVector(0.2, 0.7, 0.3),
                intensity=1.1,
                coherence=0.7,
            ),
            responsibilities=("hydroponic terraces", "wind calibration"),
        ),
        CooperativeMember(
            name="回声歌者",
            role="chorus",
            glyph=ShuliKouGlyph(
                name="echo-choir",
                signature=ShuliKouVector(0.2, 0.2, 0.9),
                intensity=0.9,
                coherence=0.4,
            ),
            responsibilities=("festival cadence", "linguistic bridges"),
        ),
    )

    initiatives = (
        CooperativeInitiative(
            name="云纹织造坊",
            focus="infrastructure",
            participants=(members[0].name, members[1].name),
        ),
        CooperativeInitiative(
            name="回声集市",
            focus="culture",
            participants=(members[1].name, members[2].name),
            amplification=1.2,
        ),
    )

    return CloudVillageCooperative(
        name="术力口云村合作社",
        blueprint=blueprint,
        members=members,
        initiatives=initiatives,
    )


__all__ = [
    "CooperativeInitiative",
    "CooperativeMember",
    "CloudVillageCooperative",
    "build_shulikou_cloud_village",
]
