"""Parameterized grid composition for the playful duo of :class:`玉子` and :class:`琦子`.

The module mirrors the narrative style of the ``bingzi`` utilities: tiny,
carefully documented helpers that are pleasant to compose inside experiments.
``Yuzi`` (玉子) focuses on constructing deterministic grids from a small set of
parameters.  ``Qizi`` (琦子) takes the resulting landscape and applies smooth
transformations – scaling, offsets, and exponentiation – returning both the
modulated grid and quick summaries of its extrema.

The helpers lean on :func:`compute_god.landscape_learning.initialise_grid` to
remain consistent with other grid-based universes.  All values are converted to
``float`` to avoid surprising ``Decimal`` / ``Fraction`` interactions when the
helpers are combined with analytical tooling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, MutableMapping, Tuple

from .landscape_learning import initialise_grid

Coordinate = Tuple[int, int]
MutableGrid = MutableMapping[Coordinate, float]
GridKernel = Callable[[int, int, "YuziParameters"], float]


def _bilinear_kernel(x: int, y: int, params: "YuziParameters") -> float:
    return (
        params.base
        + params.x_weight * x
        + params.y_weight * y
        + params.cross_weight * x * y
    )


@dataclass(frozen=True)
class YuziParameters:
    """Configuration describing a small bilinear grid."""

    width: int
    height: int
    base: float = 0.0
    x_weight: float = 1.0
    y_weight: float = 1.0
    cross_weight: float = 0.0

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be strictly positive")

    def iter_coordinates(self) -> Iterable[Coordinate]:
        for x in range(self.width):
            for y in range(self.height):
                yield (x, y)


@dataclass
class Yuzi:
    """Render a deterministic grid from :class:`YuziParameters`."""

    params: YuziParameters
    kernel: GridKernel | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.kernel is None:
            self.kernel = _bilinear_kernel

    def value_at(self, coordinate: Coordinate) -> float:
        x, y = coordinate
        if not (0 <= x < self.params.width and 0 <= y < self.params.height):
            raise ValueError("coordinate lies outside the configured grid")
        assert self.kernel is not None  # for mypy
        return float(self.kernel(x, y, self.params))

    def compute_grid(self) -> MutableGrid:
        assert self.kernel is not None  # for mypy
        grid = initialise_grid(self.params.width, self.params.height, fill=self.params.base)
        for x, y in self.params.iter_coordinates():
            grid[(x, y)] = float(self.kernel(x, y, self.params))
        return grid


@dataclass(frozen=True)
class QiziParameters:
    """Parameters describing how ``Qizi`` modulates a ``Yuzi`` grid."""

    yuzi: YuziParameters
    scale: float = 1.0
    offset: float = 0.0
    exponent: float = 1.0


@dataclass(frozen=True)
class GridSummary:
    """Tiny data structure describing the extrema of a grid."""

    minimum: float
    maximum: float
    mean: float
    min_coordinate: Coordinate
    max_coordinate: Coordinate


@dataclass
class Qizi:
    """Modulate a :class:`Yuzi` grid and report its statistics."""

    params: QiziParameters
    kernel: GridKernel | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.kernel is None:
            self.kernel = _bilinear_kernel

    def compute_grid(self) -> MutableGrid:
        yuzi = Yuzi(self.params.yuzi, kernel=self.kernel)
        base_grid = yuzi.compute_grid()
        scaled_grid = initialise_grid(
            self.params.yuzi.width, self.params.yuzi.height, fill=0.0
        )
        for coord, value in base_grid.items():
            transformed = (value ** self.params.exponent) * self.params.scale + self.params.offset
            scaled_grid[coord] = float(transformed)
        return scaled_grid

    def summary(self) -> GridSummary:
        grid = self.compute_grid()
        items = list(grid.items())
        if not items:
            raise ValueError("grid is empty; cannot compute summary")
        min_coord, min_value = min(items, key=lambda item: item[1])
        max_coord, max_value = max(items, key=lambda item: item[1])
        mean_value = sum(value for _, value in items) / len(items)
        return GridSummary(
            minimum=float(min_value),
            maximum=float(max_value),
            mean=float(mean_value),
            min_coordinate=min_coord,
            max_coordinate=max_coord,
        )


# Playful aliases embracing the narrative surface.
玉子 = Yuzi
琦子 = Qizi

__all__ = [
    "Coordinate",
    "MutableGrid",
    "GridKernel",
    "YuziParameters",
    "Yuzi",
    "QiziParameters",
    "Qizi",
    "GridSummary",
    "玉子",
    "琦子",
]
