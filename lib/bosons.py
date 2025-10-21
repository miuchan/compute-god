"""Gauge bosons represented as :class:`~lib.particles.Particle` instances."""

from __future__ import annotations

from typing import Dict

from .particles import Particle, create_particle

#: Mapping for vector bosons involved in the electroweak interaction.
BOSONS: Dict[str, Particle] = {
    "photon": create_particle(
        name="Photon",
        symbol="gamma",
        mass=None,
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Carrier of electromagnetism",
    ),
    "w_boson": create_particle(
        name="W boson",
        symbol="W",
        mass=80.379,
        charge=1.0,
        spin=1.0,
        family="boson",
        notes="Mediates the charged weak interaction",
    ),
    "z_boson": create_particle(
        name="Z boson",
        symbol="Z",
        mass=91.1876,
        charge=0.0,
        spin=1.0,
        family="boson",
        notes="Mediates the neutral weak interaction",
    ),
}
