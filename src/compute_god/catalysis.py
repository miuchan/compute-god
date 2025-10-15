"""Catalytic reaction primitives for the knotty duo of *纠子* and *缠子*.

The terminology is intentionally poetic.  Within the module a :class:`Jiuzi`
represents a tightly wound knot, whilst :class:`Chanzi` stands for a responsive
entanglement coil.  The :func:`catalyse_jiuzi_and_chanzi` routine combines both
entities under a catalytic drive and reports how strongly the pair resonated
with one another.

Even though the names are whimsical, the implementation is deterministic and
numerically light.  The reaction score is derived from three intuitive factors:

* the **intensity** stored in each participant (loop count × torsion like
  quantities),
* how well their loop/thread counts **align**, and
* the drive created by the external catalyst/agitation parameters.

This simple model is sufficient for the unit tests and showcases how playful
concepts can be translated into small, well documented utilities.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Jiuzi:
    """Representation of a 纠子 (knot-like agent).

    Parameters
    ----------
    loops:
        Discrete windings of the knot.  Must be strictly positive.
    twist:
        Strength contributed by the knot's torsion.  Must be positive.
    coherence:
        Additional multiplicative factor describing how tightly the knot keeps
        itself together.  Must be positive.
    """

    loops: int
    twist: float
    coherence: float = 1.0

    def __post_init__(self) -> None:
        if self.loops <= 0:
            raise ValueError("loops must be positive for a Jiuzi")
        if self.twist <= 0:
            raise ValueError("twist must be positive for a Jiuzi")
        if self.coherence <= 0:
            raise ValueError("coherence must be positive for a Jiuzi")

    @property
    def intensity(self) -> float:
        """Return the energetic intensity stored within the knot."""

        return float(self.loops) * self.twist * self.coherence


@dataclass
class Chanzi:
    """Representation of a 缠子 (entanglement coil).

    Parameters
    ----------
    strands:
        Number of responsive threads.  Must be strictly positive.
    torsion:
        Torsional energy of the coil.  Must be positive.
    resonance:
        Multiplicative factor describing how well the coil can resonate with a
        partner.  Must be positive.
    """

    strands: int
    torsion: float
    resonance: float = 1.0

    def __post_init__(self) -> None:
        if self.strands <= 0:
            raise ValueError("strands must be positive for a Chanzi")
        if self.torsion <= 0:
            raise ValueError("torsion must be positive for a Chanzi")
        if self.resonance <= 0:
            raise ValueError("resonance must be positive for a Chanzi")

    @property
    def intensity(self) -> float:
        """Return the energetic intensity stored within the entanglement coil."""

        return float(self.strands) * self.torsion * self.resonance


@dataclass
class CatalysisOutcome:
    """Summary of the catalytic reaction between :class:`Jiuzi` and :class:`Chanzi`."""

    entanglement: float
    alignment: float
    stability: float
    yield_strength: float


def catalyse_jiuzi_and_chanzi(
    jiuzi: Jiuzi,
    chanzi: Chanzi,
    /,
    *,
    catalyst: float = 1.0,
    agitation: float = 1.0,
) -> CatalysisOutcome:
    """Catalyse the interaction between 纠子与缠子.

    The resulting :class:`CatalysisOutcome` contains four pieces of information:

    ``entanglement``
        Strength of the combined resonance produced by the pair.
    ``alignment``
        Alignment factor derived from their loop/thread counts.  Values lie in
        ``(0, 1]`` with perfectly matched counts reaching one.
    ``stability``
        Coherence attained by the pair under the catalytic drive.
    ``yield_strength``
        Amount of entanglement per total winding.

    Parameters
    ----------
    jiuzi, chanzi:
        Participants of the catalytic reaction.
    catalyst:
        External catalytic multiplier.  Must be positive.
    agitation:
        Environmental agitation supplied to the system.  Must be positive.
    """

    if catalyst <= 0:
        raise ValueError("catalyst must be positive to trigger the reaction")
    if agitation <= 0:
        raise ValueError("agitation must be positive to trigger the reaction")

    base_intensity = math.sqrt(jiuzi.intensity * chanzi.intensity)
    alignment = 1.0 / (1.0 + abs(jiuzi.loops - chanzi.strands))
    coherence = (jiuzi.coherence + chanzi.resonance) / 2.0
    drive = math.log1p(catalyst * agitation)

    entanglement = base_intensity * alignment * drive
    stability = coherence * drive
    total_windings = float(jiuzi.loops + chanzi.strands)
    yield_strength = entanglement / total_windings

    return CatalysisOutcome(
        entanglement=entanglement,
        alignment=alignment,
        stability=stability,
        yield_strength=yield_strength,
    )
