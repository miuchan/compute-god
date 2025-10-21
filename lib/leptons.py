"""Standard Model leptons expressed as :class:`~lib.particles.Particle` objects."""

from __future__ import annotations

from typing import Dict

from .particles import Particle, create_particle

#: Mapping from lepton identifier to :class:`~lib.particles.Particle`.
LEPTONS: Dict[str, Particle] = {
    "electron": create_particle(
        name="Electron",
        symbol="e-",
        mass=0.000511,
        charge=-1.0,
        spin=0.5,
        family="lepton",
    ),
    "electron_neutrino": create_particle(
        name="Electron neutrino",
        symbol="nu_e",
        mass=None,
        charge=0.0,
        spin=0.5,
        family="lepton",
    ),
    "muon": create_particle(
        name="Muon",
        symbol="mu-",
        mass=0.10566,
        charge=-1.0,
        spin=0.5,
        family="lepton",
    ),
    "muon_neutrino": create_particle(
        name="Muon neutrino",
        symbol="nu_mu",
        mass=None,
        charge=0.0,
        spin=0.5,
        family="lepton",
    ),
    "tau": create_particle(
        name="Tau",
        symbol="tau-",
        mass=1.77686,
        charge=-1.0,
        spin=0.5,
        family="lepton",
    ),
    "tau_neutrino": create_particle(
        name="Tau neutrino",
        symbol="nu_tau",
        mass=None,
        charge=0.0,
        spin=0.5,
        family="lepton",
    ),
}
