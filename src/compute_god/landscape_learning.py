"""Landscape learning engine for Compute-God universes.

The "landscape learning" metaphor turns an elevation grid into a canvas that can
be sculpted towards sparse observations.  Each epoch of the engine nudges the
grid to honour new samples while diffusing information across neighbouring
cells.  The behaviour mirrors a minimalist stochastic gradient descent loop with
momentum and Laplacian smoothing, keeping the implementation deliberately
deterministic so that tests can rely on reproducible height maps.

This module exposes two public entry points:

``landscape_learning_universe``
    Build a :class:`~compute_god.core.universe.Universe` containing the learning
    dynamics.  The universe stores the evolving landscape under the ``"grid"``
    key and optionally records snapshots in ``"history"``.

``learn_landscape``
    Convenience wrapper around :func:`compute_god.core.engine.fixpoint` that
    drives the universe until the height map converges.

The API mirrors other high level helpers in the repository (e.g.
``compute_god.earth_rescue`` or ``compute_god.rule_optimisation``) so that the
engine can easily integrate with the catalogue, CLI, and future visualisation
tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping, Sequence, Tuple

from .core import FixpointResult, God, Metric, RuleContext, State, Universe, fixpoint, rule

Coordinate = Tuple[int, int]
GridMapping = Mapping[Coordinate, float]
MutableGrid = MutableMapping[Coordinate, float]


@dataclass(frozen=True)
class LandscapeSample:
    """Observation tying a coordinate to a desired elevation.

    Parameters
    ----------
    coordinate:
        Pair ``(x, y)`` representing the sample position inside the grid.
    elevation:
        Target elevation value associated with ``coordinate``.
    weight:
        Importance weight applied during learning.  Defaults to ``1.0`` and must
        be non-negative.
    """

    coordinate: Coordinate
    elevation: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        x, y = self.coordinate
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("coordinates must be integers")
        if x < 0 or y < 0:
            raise ValueError("coordinates must be non-negative")
        if self.weight < 0:
            raise ValueError("weight must be non-negative")


@dataclass(frozen=True)
class LandscapeLearningParameters:
    """Hyper-parameters steering the learning dynamics."""

    learning_rate: float = 0.25
    smoothing: float = 0.1
    momentum: float = 0.0
    noise_floor: float = 0.0

    def __post_init__(self) -> None:
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be strictly positive")
        if not 0 <= self.smoothing <= 1:
            raise ValueError("smoothing must lie in [0, 1]")
        if not 0 <= self.momentum < 1:
            raise ValueError("momentum must lie in [0, 1)")
        if self.noise_floor < 0:
            raise ValueError("noise_floor must be non-negative")


def initialise_grid(width: int, height: int, *, fill: float = 0.0) -> MutableGrid:
    """Return a dense ``width × height`` grid filled with ``fill``."""

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be strictly positive")

    grid: MutableGrid = {}
    for x in range(width):
        for y in range(height):
            grid[(x, y)] = float(fill)
    return grid


def _infer_dimensions(grid: Mapping[Coordinate, float]) -> tuple[int, int]:
    if not grid:
        raise ValueError("grid must contain at least one cell")

    xs = {x for x, _ in grid}
    ys = {y for _, y in grid}
    width = max(xs) + 1
    height = max(ys) + 1

    if len(xs) != width or len(ys) != height:
        raise ValueError("grid coordinates must form a contiguous rectangle")

    expected_size = width * height
    if len(grid) != expected_size:
        raise ValueError(
            "grid must provide an elevation for every coordinate inside the rectangle"
        )

    for (x, y) in grid:
        if x < 0 or y < 0:
            raise ValueError("grid coordinates must be non-negative")

    return width, height


def _neighbours(coord: Coordinate, width: int, height: int) -> Iterable[Coordinate]:
    x, y = coord
    if x > 0:
        yield (x - 1, y)
    if x + 1 < width:
        yield (x + 1, y)
    if y > 0:
        yield (x, y - 1)
    if y + 1 < height:
        yield (x, y + 1)


def _apply_smoothing(grid: Mapping[Coordinate, float], dims: tuple[int, int], factor: float) -> MutableGrid:
    if factor <= 0:
        return dict(grid)

    width, height = dims
    smoothed: MutableGrid = {}
    for coord, value in grid.items():
        neighbours = list(_neighbours(coord, width, height))
        if not neighbours:
            smoothed[coord] = float(value)
            continue
        average = sum(grid[n] for n in neighbours) / len(neighbours)
        smoothed[coord] = (1 - factor) * float(value) + factor * average
    return smoothed


def _learning_step(
    grid: Mapping[Coordinate, float],
    velocity: Mapping[Coordinate, float],
    samples: Sequence[LandscapeSample],
    params: LandscapeLearningParameters,
    dims: tuple[int, int],
) -> tuple[MutableGrid, MutableGrid]:
    width, height = dims
    new_grid: MutableGrid = dict(grid)
    new_velocity: MutableGrid = {
        coord: params.momentum * velocity.get(coord, 0.0)
        for coord in grid
    }

    for sample in samples:
        if sample.coordinate not in new_grid:
            raise KeyError(f"sample coordinate {sample.coordinate!r} outside landscape bounds")

        baseline = grid[sample.coordinate]
        update = params.learning_rate * sample.weight * (sample.elevation - baseline)
        new_velocity[sample.coordinate] += update
        new_grid[sample.coordinate] = baseline + new_velocity[sample.coordinate]

    if params.noise_floor > 0:
        for coord, value in list(new_grid.items()):
            delta = value - grid[coord]
            if abs(delta) < params.noise_floor:
                new_grid[coord] = grid[coord]
                new_velocity[coord] = 0.0

    smoothed_grid = _apply_smoothing(new_grid, dims, params.smoothing)
    return smoothed_grid, new_velocity


def _landscape_metric(dims: tuple[int, int]) -> Metric:
    coords = [(x, y) for x in range(dims[0]) for y in range(dims[1])]

    def metric(previous: State, current: State) -> float:
        prev_grid = previous["grid"]
        curr_grid = current["grid"]
        return max(abs(prev_grid[coord] - curr_grid[coord]) for coord in coords)

    return metric


def landscape_learning_universe(
    initial_grid: GridMapping,
    samples: Sequence[LandscapeSample],
    params: LandscapeLearningParameters,
    *,
    track_history: bool = True,
) -> Universe:
    """Return a universe encapsulating the landscape learning dynamics."""

    dims = _infer_dimensions(initial_grid)
    frozen_samples = tuple(samples)

    state: State = {
        "grid": {coord: float(value) for coord, value in initial_grid.items()},
        "velocity": {coord: 0.0 for coord in initial_grid},
    }

    if track_history:
        state["history"] = [{coord: float(value) for coord, value in initial_grid.items()}]

    def learning_rule(current_state: State, _ctx: RuleContext) -> State:
        grid = current_state["grid"]
        velocity = current_state["velocity"]
        new_grid, new_velocity = _learning_step(grid, velocity, frozen_samples, params, dims)

        next_state: State = {
            "grid": new_grid,
            "velocity": new_velocity,
        }

        if track_history:
            history = list(current_state.get("history", ()))
            history.append({coord: float(value) for coord, value in new_grid.items()})
            next_state["history"] = history

        return next_state

    universe = God.universe(state=state, rules=[rule("landscape-learning", learning_rule)])
    return universe


def learn_landscape(
    initial_grid: GridMapping,
    samples: Sequence[LandscapeSample],
    params: LandscapeLearningParameters | None = None,
    *,
    epsilon: float = 1e-6,
    max_epoch: int = 128,
    track_history: bool = True,
) -> FixpointResult:
    """Run the landscape learning engine until convergence."""

    if params is None:
        params = LandscapeLearningParameters()

    dims = _infer_dimensions(initial_grid)
    universe = landscape_learning_universe(
        initial_grid,
        samples,
        params,
        track_history=track_history,
    )

    metric = _landscape_metric(dims)
    return fixpoint(universe, metric=metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "Coordinate",
    "GridMapping",
    "LandscapeLearningParameters",
    "LandscapeSample",
    "initialise_grid",
    "landscape_learning_universe",
    "learn_landscape",
]

