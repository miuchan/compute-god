"""Triadic thermal observers nicknamed ``三子`` and ``维子``.

``Sanzi`` (三子) acts as a gentle coordinator around the existing observers in
the project.  The module already offers :class:`compute_god.bingzi.Bingzi`,
:class:`compute_god.bingzi.Pingzi` and :class:`compute_god.jizi.Jizi` which each
focus on one aspect of the thermal story.  ``Sanzi`` simply weaves the trio
into a convenient façade so callers can ask for combined summaries without
having to manually juggle the individual helpers every time.

``Weizi`` (维子) extends this idea by pairing a ``Sanzi`` instance with
``Zijiji`` (子机机), the cold-observing counterpart to ``Jizi``.  The pairing is
able to surface the underlying :class:`compute_god.jizi.ThermalDual` and answer
basic questions about whether the recorded history appears balanced around a
target tolerance.

While whimsical, both classes are intentionally tiny.  They avoid keeping any
additional state, instead delegating to the wrapped observers on demand.  This
makes them straightforward to test and pleasant to re-use in pedagogical
examples, mirroring the rest of the code base.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .bingzi import Bingzi, Pingzi, peculiar_asymmetry
from .jizi import Jizi, ThermalDual, Zijiji, thermal_dual


@dataclass(frozen=True)
class SanziOverview:
    """Summary describing the combined behaviour of the triad."""

    coldest: float
    hottest: float
    span: float
    equilibrium: float
    machine_heat: float


@dataclass
class Sanzi:
    """Façade combining ``Bingzi``, ``Pingzi`` and ``Jizi``.

    The helper never stores additional history.  Instead each method checks
    whether the underlying observers have recorded enough information before
    returning derived values such as the observed span or equilibrium.
    """

    bingzi: Bingzi
    pingzi: Pingzi
    jizi: Jizi

    def temperature_span(self) -> Optional[float]:
        """Return the temperature span between ``Bingzi`` and ``Pingzi``."""

        return peculiar_asymmetry(self.bingzi, self.pingzi)

    def equilibrium(self) -> Optional[float]:
        """Return the midpoint between the coldest and hottest observations."""

        if self.bingzi.coldest_value is None or self.pingzi.hottest_value is None:
            return None
        coldest = float(self.bingzi.coldest_value)
        hottest = float(self.pingzi.hottest_value)
        return (coldest + hottest) / 2.0

    def machine_heat(self) -> Optional[float]:
        """Return the hottest temperature recorded by ``Jizi``."""

        if self.jizi.hottest_value is None:
            return None
        return float(self.jizi.hottest_value)

    def overview(self) -> Optional[SanziOverview]:
        """Return a combined snapshot of the triad.

        ``None`` is returned until the underlying observers have all recorded at
        least one value.  Once available the result contains the coldest and
        hottest temperatures, the span between them, their equilibrium and the
        hottest value measured by ``Jizi``.
        """

        span = self.temperature_span()
        equilibrium = self.equilibrium()
        machine_heat = self.machine_heat()

        if (
            span is None
            or equilibrium is None
            or machine_heat is None
            or self.bingzi.coldest_value is None
            or self.pingzi.hottest_value is None
        ):
            return None

        return SanziOverview(
            coldest=float(self.bingzi.coldest_value),
            hottest=float(self.pingzi.hottest_value),
            span=span,
            equilibrium=equilibrium,
            machine_heat=machine_heat,
        )


@dataclass
class Weizi:
    """Bridge combining ``Sanzi`` with ``Zijiji``.

    The class offers a tiny façade above :func:`thermal_dual` while mirroring
    the ergonomic helpers available on :class:`Sanzi`.  This keeps the public
    API playful without hiding the underlying primitives from advanced users.
    """

    sanzi: Sanzi
    zijiji: Zijiji

    def dual(self) -> Optional[ThermalDual]:
        """Return the thermal dual between the machine and submachine."""

        return thermal_dual(self.sanzi.jizi, self.zijiji)

    def equilibrium(self) -> Optional[float]:
        """Return the equilibrium temperature of the dual if available."""

        dual = self.dual()
        if dual is None:
            return None
        return float(dual.equilibrium)

    def is_balanced(self, tolerance: float) -> bool:
        """Return ``True`` if the thermal gap is within ``tolerance``.

        The method returns ``False`` until both observers have recorded at least
        one value, mirroring the behaviour of the wrapped helpers.
        """

        dual = self.dual()
        if dual is None:
            return False
        return abs(float(dual.gap)) <= float(tolerance)


# Playful aliases embracing the poetic API.
三子 = Sanzi
维子 = Weizi


__all__ = ["SanziOverview", "Sanzi", "Weizi", "三子", "维子"]

