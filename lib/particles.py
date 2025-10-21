"""Primitives and helpers for representing elementary particles."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Particle:
    """Describe a particle in the Standard Model.

    Parameters
    ----------
    name:
        Human readable name of the particle.
    symbol:
        Short symbol used in equations.
    mass:
        Rest mass in gigaelectronvolts. The default ``None`` indicates that the
        value is unknown or not yet measured.
    charge:
        Electric charge in units of the elementary charge.
    spin:
        Intrinsic spin quantum number.
    family:
        Optional grouping such as "lepton" or "boson".
    notes:
        Free-form string with supplementary information.
    """

    name: str
    symbol: str
    mass: Optional[float] = None
    charge: Optional[float] = None
    spin: Optional[float] = None
    family: Optional[str] = None
    notes: str = ""


def create_particle(**kwargs: Any) -> Particle:
    """Create a :class:`Particle` while normalising optional fields."""

    if "mass" in kwargs and kwargs["mass"] is not None:
        kwargs["mass"] = float(kwargs["mass"])
    return Particle(**kwargs)


def asdict(particle: Particle) -> Dict[str, Any]:
    """Return a serialisable dictionary representation of *particle*."""

    return {
        "name": particle.name,
        "symbol": particle.symbol,
        "mass": particle.mass,
        "charge": particle.charge,
        "spin": particle.spin,
        "family": particle.family,
        "notes": particle.notes,
    }


def with_notes(particle: Particle, notes: str) -> Particle:
    """Return a copy of *particle* with ``notes`` appended."""

    combined = f"{particle.notes} {notes}".strip()
    return replace(particle, notes=combined)
