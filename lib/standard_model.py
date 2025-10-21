"""Curated catalogue of Standard Model particles for high-level experiments."""

from __future__ import annotations

from typing import Dict

from .bosons import BOSONS
from .gluons import GLUONS
from .leptons import LEPTONS
from .particles import Particle, create_particle
from .quarks import QUARKS

#: Aggregate mapping of all known elementary particles in the Standard Model.
STANDARD_MODEL: Dict[str, Particle] = {
    **QUARKS,
    **LEPTONS,
    **BOSONS,
    **{
        "higgs": create_particle(
            name="Higgs boson",
            symbol="H",
            mass=125.10,
            charge=0.0,
            spin=0.0,
            family="boson",
            notes="Field responsible for electroweak symmetry breaking",
        )
    },
    **GLUONS,
}
