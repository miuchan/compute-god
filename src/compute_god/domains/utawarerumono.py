"""Legend weaving utilities for the so called "One Being Sung".

The playful module name references *Utawarerumono* (传颂之物), a story about
how deeds echo through songs.  Within the Compute‑God ecosystem we interpret
this as a helper that records how a sequence of ``verses`` describe the states
encountered during a computation.  Each time :class:`Utawarerumono` is asked to
``sing`` it evaluates the configured verses, stores the resulting lines together
with a copy of the inspected state and keeps track of the strongest chant seen
so far according to a user supplied ``metric``.

The implementation intentionally mirrors the ergonomics of other observability
helpers such as :class:`compute_god.miyu.MiyuBond` and
:class:`compute_god.entangle.Entangler`.  All snapshots are defensive copies so
that the recorded history remains stable even if the caller mutates their input
mappings after the fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Literal, MutableMapping, Optional, Sequence, Tuple

State = MutableMapping[str, object]
Verse = Callable[[State], str]
ResonanceMetric = Callable[[Tuple[str, ...]], float]
Preference = Literal["max", "min"]


@dataclass
class UtawarerumonoChant:
    """Snapshot of a single chant emitted by :class:`Utawarerumono`.

    Parameters
    ----------
    state:
        Defensive copy of the state that was sung about.
    lines:
        Tuple containing the individual outputs of each verse.
    resonance:
        Numeric score returned by the configured metric.  Larger values usually
        denote a stronger legend, but the exact interpretation depends on the
        ``prefer`` mode selected by :class:`Utawarerumono`.
    """

    state: State
    lines: Tuple[str, ...]
    resonance: float

    def compose(self, delimiter: str = "\n") -> str:
        """Join the verses of the chant into a single legend string."""

        return delimiter.join(self.lines)


LegendChant = UtawarerumonoChant


@dataclass
class Utawarerumono:
    """Record and evaluate chants describing computation states.

    Parameters
    ----------
    verses:
        Ordered collection of callables that each accept a state and return a
        string describing one aspect of it.
    metric:
        Callable used to score the tuple of lines returned by ``verses``.  When
        omitted the default metric computes the total length of the concatenated
        lines.
    prefer:
        Indicates whether higher (``"max"``) or lower (``"min"``) scores are
        considered better.  The default favours higher resonance as that mirrors
        the idea of a louder, more celebrated legend.
    """

    verses: Sequence[Verse]
    metric: Optional[ResonanceMetric] = None
    prefer: Preference = "max"
    history: List[UtawarerumonoChant] = field(default_factory=list, init=False)
    _best: Optional[UtawarerumonoChant] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.verses = tuple(self.verses)
        if not self.verses:
            raise ValueError("Utawarerumono requires at least one verse to sing.")

        if self.prefer not in ("max", "min"):
            raise ValueError("prefer must be either 'max' or 'min'.")

    @staticmethod
    def _default_metric(lines: Tuple[str, ...]) -> float:
        """Length based default resonance metric."""

        return float(sum(len(line) for line in lines))

    def _evaluate(self, lines: Tuple[str, ...]) -> float:
        metric = self.metric or self._default_metric
        return float(metric(lines))

    def _is_better(self, candidate: float, current: float) -> bool:
        if self.prefer == "max":
            return candidate > current
        return candidate < current

    def sing(self, state: State, /) -> Tuple[str, ...]:
        """Evaluate the verses for ``state`` and store the resulting chant."""

        lines = tuple(verse(state) for verse in self.verses)
        resonance = self._evaluate(lines)

        snapshot = UtawarerumonoChant(state=dict(state), lines=lines, resonance=resonance)
        self.history.append(snapshot)

        if self._best is None or self._is_better(snapshot.resonance, self._best.resonance):
            self._best = snapshot

        return lines

    def best_chant(self) -> Optional[UtawarerumonoChant]:
        """Return a defensive copy of the strongest chant observed so far."""

        if self._best is None:
            return None
        return UtawarerumonoChant(
            state=dict(self._best.state),
            lines=self._best.lines,
            resonance=self._best.resonance,
        )

    def best_state(self) -> Optional[State]:
        """Return the state that produced the strongest chant."""

        if self._best is None:
            return None
        return dict(self._best.state)

    def best_lines(self) -> Optional[Tuple[str, ...]]:
        """Return the tuple of verse outputs that formed the best chant."""

        if self._best is None:
            return None
        return self._best.lines

    def compose(self, lines: Optional[Tuple[str, ...]] = None, *, delimiter: str = "\n") -> str:
        """Compose a legend string either from ``lines`` or the best chant."""

        if lines is None:
            best = self.best_lines()
            if best is None:
                return ""
            lines = best
        return delimiter.join(lines)

    def is_resonant(self, threshold: float) -> bool:
        """Check whether the best chant satisfies the desired threshold."""

        if self._best is None:
            return False
        if self.prefer == "max":
            return self._best.resonance >= threshold
        return self._best.resonance <= threshold

    def clear(self) -> None:
        """Remove the recorded history and forget the best chant."""

        self.history.clear()
        self._best = None


传颂之物 = Utawarerumono


__all__ = [
    "Utawarerumono",
    "UtawarerumonoChant",
    "LegendChant",
    "传颂之物",
]

