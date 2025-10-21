"""Colour combinations for gluons in the Standard Model."""

from __future__ import annotations

from typing import Dict

from .particles import Particle, create_particle

#: Eight gluon colour states represented as :class:`~lib.particles.Particle` instances.
GLUONS: Dict[str, Particle] = {
    "rg": create_particle(
        name="Red-green gluon",
        symbol="g_rg",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Carries colour between red and green",
    ),
    "rb": create_particle(
        name="Red-blue gluon",
        symbol="g_rb",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Carries colour between red and blue",
    ),
    "gr": create_particle(
        name="Green-red gluon",
        symbol="g_gr",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Carries colour between green and red",
    ),
    "gb": create_particle(
        name="Green-blue gluon",
        symbol="g_gb",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Carries colour between green and blue",
    ),
    "br": create_particle(
        name="Blue-red gluon",
        symbol="g_br",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Carries colour between blue and red",
    ),
    "bg": create_particle(
        name="Blue-green gluon",
        symbol="g_bg",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Carries colour between blue and green",
    ),
    "rr_minus_bb": create_particle(
        name="Red-red minus blue-blue gluon",
        symbol="g_rr_bb",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Linear combination distinguishing red and blue",
    ),
    "rgb": create_particle(
        name="Red+green-2 blue gluon",
        symbol="g_rgb",
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Linear combination completing the octet",
    ),
}
