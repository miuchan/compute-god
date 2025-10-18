"""Non-mainstream cellular automata implementations.

This module collects a few two-dimensional cellular automata that sit outside
the standard Conway ``Life`` canon.  The automata are intentionally small and
pure so they can be embedded inside larger simulations or combined with the
project's fixed-point engine.  Each helper validates the input grid, applies
a single synchronous update step, and returns a brand new lattice without
mutating the original data.

The following automata are provided:

* :func:`cyclic_automaton_step` – a colour-cycling automaton where a cell
  advances to the next colour when enough neighbours already display it.
* :func:`brians_brain_step` – Brian's Brain with the standard firing/refractory
  dynamics.
* :func:`wireworld_step` – Wireworld, commonly used for logic circuit
  experiments.

All automata use a Moore neighbourhood (eight surrounding cells) and expect a
rectangular grid represented as a sequence of integer sequences.  The helpers
return ``list[list[int]]`` instances to make it easy to feed the result back
into the next iteration or serialise the lattice for observers.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Iterable, List, Sequence, Tuple

Grid = Sequence[Sequence[int]]


def _ensure_rectangular(grid: Grid) -> Tuple[int, int]:
    """Validate that the grid is non-jagged and return its dimensions."""

    if not grid:
        raise ValueError("grid must contain at least one row")

    width = len(grid[0])
    if width == 0:
        raise ValueError("grid rows must contain at least one cell")

    for row in grid:
        if len(row) != width:
            raise ValueError("grid must be rectangular")
    return len(grid), width


def _iter_moore_neighbours(row: int, col: int, height: int, width: int) -> Iterable[Tuple[int, int]]:
    """Yield coordinates of the Moore neighbourhood for a given cell."""

    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr = row + dr
            cc = col + dc
            if 0 <= rr < height and 0 <= cc < width:
                yield rr, cc


def cyclic_automaton_step(grid: Grid, *, states: int, threshold: int = 1) -> List[List[int]]:
    """Return the next step of a cyclic cellular automaton.

    Parameters
    ----------
    grid:
        A rectangular lattice of integers in ``[0, states)``.
    states:
        Number of colours in the cycle.  Must be at least ``2``.
    threshold:
        Minimum number of neighbours in the successor colour required for a
        cell to advance.  Defaults to ``1``.
    """

    if states < 2:
        raise ValueError("states must be at least 2")
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    height, width = _ensure_rectangular(grid)

    next_grid: List[List[int]] = []
    for row_index, row in enumerate(grid):
        next_row: List[int] = []
        for col_index, value in enumerate(row):
            if value < 0 or value >= states:
                raise ValueError("grid values must lie within [0, states)")

            successor = (value + 1) % states
            neighbour_count = 0
            for nr, nc in _iter_moore_neighbours(row_index, col_index, height, width):
                if grid[nr][nc] == successor:
                    neighbour_count += 1
                    if neighbour_count >= threshold:
                        break

            next_row.append(successor if neighbour_count >= threshold else value)
        next_grid.append(next_row)
    return next_grid


class BriansBrainCell(IntEnum):
    """Cell states for Brian's Brain."""

    DEAD = 0
    FIRING = 1
    REFRACTORY = 2


def brians_brain_step(grid: Grid) -> List[List[int]]:
    """Return the next step of Brian's Brain cellular automaton."""

    height, width = _ensure_rectangular(grid)

    next_grid: List[List[int]] = []
    for row_index, row in enumerate(grid):
        next_row: List[int] = []
        for col_index, value in enumerate(row):
            try:
                state = BriansBrainCell(value)
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise ValueError("invalid Brian's Brain state") from exc

            if state is BriansBrainCell.FIRING:
                next_row.append(int(BriansBrainCell.REFRACTORY))
                continue
            if state is BriansBrainCell.REFRACTORY:
                next_row.append(int(BriansBrainCell.DEAD))
                continue

            # Dead cell: count firing neighbours.
            firing_neighbours = sum(
                1
                for nr, nc in _iter_moore_neighbours(row_index, col_index, height, width)
                if grid[nr][nc] == BriansBrainCell.FIRING
            )
            next_row.append(
                int(BriansBrainCell.FIRING if firing_neighbours == 2 else BriansBrainCell.DEAD)
            )
        next_grid.append(next_row)
    return next_grid


class WireworldCell(IntEnum):
    """Cell states for Wireworld."""

    EMPTY = 0
    ELECTRON_HEAD = 1
    ELECTRON_TAIL = 2
    CONDUCTOR = 3


def wireworld_step(grid: Grid) -> List[List[int]]:
    """Return the next step of the Wireworld cellular automaton."""

    height, width = _ensure_rectangular(grid)

    next_grid: List[List[int]] = []
    for row_index, row in enumerate(grid):
        next_row: List[int] = []
        for col_index, value in enumerate(row):
            try:
                state = WireworldCell(value)
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise ValueError("invalid Wireworld state") from exc

            if state is WireworldCell.EMPTY:
                next_row.append(int(WireworldCell.EMPTY))
                continue
            if state is WireworldCell.ELECTRON_HEAD:
                next_row.append(int(WireworldCell.ELECTRON_TAIL))
                continue
            if state is WireworldCell.ELECTRON_TAIL:
                next_row.append(int(WireworldCell.CONDUCTOR))
                continue

            # Conductor
            head_neighbours = sum(
                1
                for nr, nc in _iter_moore_neighbours(row_index, col_index, height, width)
                if grid[nr][nc] == WireworldCell.ELECTRON_HEAD
            )
            next_row.append(
                int(
                    WireworldCell.ELECTRON_HEAD
                    if 1 <= head_neighbours <= 2
                    else WireworldCell.CONDUCTOR
                )
            )
        next_grid.append(next_row)
    return next_grid


__all__ = [
    "Grid",
    "cyclic_automaton_step",
    "brians_brain_step",
    "BriansBrainCell",
    "wireworld_step",
    "WireworldCell",
]
