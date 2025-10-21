"""Gift sculpting helpers built on top of :mod:`compute_god.landscape_learning`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping, Sequence

from .landscape_learning import (
    LandscapeLearningParameters,
    LandscapeSample,
    initialise_grid,
    learn_landscape,
)

GiftCoordinate = tuple[int, int]
GiftGrid = MutableMapping[GiftCoordinate, float]
GiftPlan = MutableMapping[str, object]


@dataclass(frozen=True)
class GiftWish:
    """Desired highlight inside the gift landscape."""

    coordinate: GiftCoordinate
    intensity: float
    weight: float = 1.0
    label: str | None = None

    def __post_init__(self) -> None:
        if self.label is not None and not isinstance(self.label, str):
            raise TypeError("label must be a string or ``None``")

    def as_sample(self) -> LandscapeSample:
        """Convert the wish to a :class:`LandscapeSample`."""

        return LandscapeSample(self.coordinate, float(self.intensity), float(self.weight))


def prepare_gift_canvas(width: int, height: int, *, baseline: float = 0.0) -> GiftGrid:
    """Return an empty gift canvas backed by :func:`initialise_grid`."""

    return initialise_grid(width, height, fill=baseline)


def _default_parameters() -> LandscapeLearningParameters:
    return LandscapeLearningParameters(learning_rate=0.35, smoothing=0.18, momentum=0.25)


def _sorted_highlights(
    grid: Mapping[GiftCoordinate, float],
    wishes: Sequence[GiftWish],
    *,
    limit: int = 3,
) -> list[dict[str, object]]:
    label_lookup: dict[GiftCoordinate, str] = {}
    for wish in wishes:
        if wish.label:
            label_lookup[wish.coordinate] = wish.label

    ordered = sorted(grid.items(), key=lambda item: item[1], reverse=True)
    highlights: list[dict[str, object]] = []
    for coord, value in ordered[:limit]:
        entry: dict[str, object] = {
            "coordinate": coord,
            "elevation": float(value),
        }
        label = label_lookup.get(coord)
        if label:
            entry["label"] = label
        highlights.append(entry)
    return highlights


def sculpt_gift_landscape(
    canvas: Mapping[GiftCoordinate, float],
    wishes: Sequence[GiftWish],
    *,
    params: LandscapeLearningParameters | None = None,
    epsilon: float = 1e-6,
    max_epoch: int = 96,
    track_history: bool = True,
) -> GiftPlan:
    """Diffuse wishes across the canvas and return a structured gift plan."""

    if not wishes:
        raise ValueError("at least one wish is required to sculpt the gift landscape")

    parameters = params or _default_parameters()
    samples = [wish.as_sample() for wish in wishes]

    result = learn_landscape(
        canvas,
        samples,
        parameters,
        epsilon=epsilon,
        max_epoch=max_epoch,
        track_history=track_history,
    )

    grid = result.universe.state["grid"]
    plan: GiftPlan = {
        "grid": {coord: float(value) for coord, value in grid.items()},
        "highlights": _sorted_highlights(grid, wishes),
        "converged": result.converged,
        "epochs": result.epochs,
    }

    history = result.universe.state.get("history")
    if track_history and isinstance(history, Iterable):
        plan["history"] = [
            {coord: float(value) for coord, value in snapshot.items()}
            for snapshot in history
        ]

    return plan


def describe_gift_plan(
    plan: Mapping[str, object],
    *,
    axis_labels: tuple[str, str] = ("x", "y"),
) -> str:
    """Render the plan highlights as a small narrative snippet."""

    if len(axis_labels) != 2:
        raise ValueError("axis_labels must contain exactly two entries")

    highlights = plan.get("highlights", [])
    if not isinstance(highlights, Sequence):
        raise TypeError("plan['highlights'] must be a sequence")

    if not highlights:
        return "礼物景观尚未雕刻。"

    lines: list[str] = []
    x_axis, y_axis = axis_labels

    for highlight in highlights:
        if not isinstance(highlight, Mapping):
            raise TypeError("each highlight must be a mapping")

        coordinate = highlight.get("coordinate")
        if (
            not isinstance(coordinate, tuple)
            or len(coordinate) != 2
            or not all(isinstance(value, int) for value in coordinate)
        ):
            raise TypeError("highlight coordinate must be a pair of integers")

        value = float(highlight.get("elevation", 0.0))
        label = highlight.get("label")
        position = f"{x_axis}={coordinate[0]}, {y_axis}={coordinate[1]}"

        if isinstance(label, str) and label:
            lines.append(f"- {label} @ {position} -> 高度 {value:.2f}")
        else:
            lines.append(f"- 亮点坐标 {position} -> 高度 {value:.2f}")

    if bool(plan.get("converged")):
        epochs = int(plan.get("epochs", 0))
        lines.append("")
        lines.append(f"景观在 {epochs} 轮学习内稳定下来。")

    return "\n".join(lines)


__all__ = [
    "GiftCoordinate",
    "GiftGrid",
    "GiftPlan",
    "GiftWish",
    "describe_gift_plan",
    "prepare_gift_canvas",
    "sculpt_gift_landscape",
]

