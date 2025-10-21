"""Collections of quark particles defined for the Standard Model helpers."""

from __future__ import annotations

from typing import Dict

from .particles import Particle, create_particle

#: Canonical mapping from identifier to :class:`~lib.particles.Particle` for quarks.
QUARKS: Dict[str, Particle] = {
    "up": create_particle(
        name="Up quark",
        symbol="u",
        mass=0.0022,
        charge=2.0 / 3.0,
        spin=0.5,
        family="quark",
    ),
    "down": create_particle(
        name="Down quark",
        symbol="d",
        mass=0.0047,
        charge=-1.0 / 3.0,
        spin=0.5,
        family="quark",
    ),
    "charm": create_particle(
        name="Charm quark",
        symbol="c",
        mass=1.27,
        charge=2.0 / 3.0,
        spin=0.5,
        family="quark",
    ),
    "strange": create_particle(
        name="Strange quark",
        symbol="s",
        mass=0.095,
        charge=-1.0 / 3.0,
        spin=0.5,
        family="quark",
    ),
    "top": create_particle(
        name="Top quark",
        symbol="t",
        mass=172.76,
        charge=2.0 / 3.0,
        spin=0.5,
        family="quark",
    ),
    "bottom": create_particle(
        name="Bottom quark",
        symbol="b",
        mass=4.18,
        charge=-1.0 / 3.0,
        spin=0.5,
        family="quark",
    ),
}
