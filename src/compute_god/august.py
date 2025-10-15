"""Seasonal cycle helpers capturing the feeling of an endless August.

The project loves whimsical metaphors. ``EndlessAugust`` translates the poetic
idea of a month that never ends into a tiny utility class.  It manages a
cyclical sequence of labelled "days" and exposes helpers to walk through the
loop without ever reaching a terminal state.  Users can peek at upcoming days,
advance the cycle while keeping track of how many full laps were completed and
inspect the visited history.  The helper is intentionally deterministic so that
higher level simulations can rely on it for reproducible seasonal patterns.

While the class is lightweight, it aims to be ergonomic: the default cycle
includes the thirty-one days of August, :meth:`peek` offers a non-destructive
preview of what is ahead and :meth:`advance` can take arbitrary step counts.  A
few convenience properties (`current_day`, `turns`, `laps`) make it easy to
query the internal state, enabling expressive tests and playful experiments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence


def _default_august_days() -> List[str]:
    """Return the canonical list of thirty-one day labels for August."""

    return [f"Day {index}" for index in range(1, 32)]


@dataclass
class EndlessAugust:
    """Manage a looping sequence of labelled days with lap tracking.

    Parameters
    ----------
    cycle:
        Ordered labels representing the days in a cycle.  If not provided the
        helper populates it with thirty-one generically named August days.
    start_index:
        Position of the day to start from.  Negative values wrap around the
        provided cycle which mirrors Python's negative indexing semantics.

    Notes
    -----
    ``EndlessAugust`` never mutates the original iterable; an internal list copy
    is stored instead.  The class raises :class:`ValueError` if constructed with
    an empty cycle or if negative steps are requested when advancing.  Laps are
    counted whenever the pointer wraps back to the original starting day.
    """

    cycle: Sequence[str] | Iterable[str] = field(default_factory=_default_august_days)
    start_index: int = 0

    history: List[str] = field(default_factory=list, init=False)
    _index: int = field(init=False, repr=False)
    _origin_index: int = field(init=False, repr=False)
    _turns: int = field(default=0, init=False, repr=False)
    _laps: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        cycle_list = list(self.cycle)
        if not cycle_list:
            raise ValueError("EndlessAugust requires at least one day in the cycle.")

        self.cycle = [str(day) for day in cycle_list]
        cycle_length = len(self.cycle)
        self._origin_index = self.start_index % cycle_length
        self._index = self._origin_index

    @property
    def current_day(self) -> str:
        """Return the label of the day currently pointed at."""

        return self.cycle[self._index]

    @property
    def turns(self) -> int:
        """Return how many individual steps have been taken so far."""

        return self._turns

    @property
    def laps(self) -> int:
        """Return how many complete laps around the cycle were completed."""

        return self._laps

    def peek(self, count: int) -> List[str]:
        """Return the next ``count`` days without mutating internal state."""

        if count < 0:
            raise ValueError("Cannot peek a negative number of days.")

        if count == 0:
            return []

        cycle_length = len(self.cycle)
        index = self._index
        preview: List[str] = []
        for _ in range(count):
            preview.append(self.cycle[index])
            index = (index + 1) % cycle_length
        return preview

    def advance(self, steps: int = 1) -> str:
        """Advance the cycle by ``steps`` positions and return the current day."""

        if steps < 0:
            raise ValueError("Cannot advance a negative number of steps.")

        if steps == 0:
            return self.current_day

        cycle_length = len(self.cycle)
        last_label = self.current_day
        for _ in range(steps):
            self._turns += 1
            self._index = (self._index + 1) % cycle_length
            last_label = self.cycle[self._index]
            self.history.append(last_label)
            if self._index == self._origin_index:
                self._laps += 1
        return last_label

    def timeline(self) -> List[str]:
        """Return a defensive copy of the visited history."""

        return list(self.history)

    def reset(self) -> None:
        """Reset the cycle pointer and clear the recorded history."""

        self._index = self._origin_index
        self._turns = 0
        self._laps = 0
        self.history.clear()
