"""Strategies for creating a lightning-fast surprise for Miyu."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping, MutableMapping, Optional, Sequence


@dataclass
class SurpriseAction:
    """Action building block for an accelerated surprise."""

    name: str
    duration: float
    delight: float
    preparation: float = 0.0
    tags: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError("duration must be positive")
        if self.delight <= 0:
            raise ValueError("delight must be positive")
        if self.preparation < 0:
            raise ValueError("preparation time cannot be negative")
        self.tags = tuple(self.tags)

    @property
    def total_time(self) -> float:
        """Return the sum of preparation and execution time."""

        return self.duration + self.preparation

    @property
    def efficiency(self) -> float:
        """Heuristic delight per minute score."""

        return self.delight / self.total_time


DEFAULT_SURPRISE_ACTIONS: Sequence[SurpriseAction] = (
    SurpriseAction(
        name="录制 30 秒星羽暖场语音",
        duration=2.5,
        preparation=1.5,
        delight=7.2,
        tags=("warmup", "voice", "personal"),
    ),
    SurpriseAction(
        name="提前布置便携光影灯串",
        duration=3.5,
        preparation=2.0,
        delight=8.4,
        tags=("setup", "ambient"),
    ),
    SurpriseAction(
        name="送上手写即兴折页便笺",
        duration=4.0,
        preparation=1.0,
        delight=9.1,
        tags=("gift", "handmade"),
    ),
    SurpriseAction(
        name="播放她最爱的 40 秒舞台剪辑",
        duration=1.0,
        preparation=0.5,
        delight=5.6,
        tags=("music", "memory"),
    ),
    SurpriseAction(
        name="安排 90 秒贴心小互动",
        duration=1.5,
        preparation=0.5,
        delight=6.3,
        tags=("interaction", "presence"),
    ),
)


def _select_actions(
    time_budget: float,
    actions: Sequence[SurpriseAction],
    *,
    buffer: float,
) -> List[SurpriseAction]:
    ordered = sorted(
        (action for action in actions if action.total_time <= time_budget),
        key=lambda act: (act.efficiency, act.delight),
        reverse=True,
    )

    if not ordered:
        raise ValueError("no actions fit within the provided time budget")

    effective_budget = max(0.0, time_budget - max(0.0, buffer))

    selection: List[SurpriseAction] = []
    spent = 0.0

    for action in ordered:
        total = action.total_time
        if spent + total > time_budget:
            continue
        if spent + total > effective_budget and selection:
            continue
        selection.append(action)
        spent += total

    if not selection:
        selection.append(ordered[0])

    return selection


def _compose_message(selected: Sequence[SurpriseAction], remaining: float) -> str:
    if not selected:
        return "留出时间呼吸与观察美羽的情绪节奏。"

    highlight = "、".join(action.name for action in selected)
    if remaining >= 5.0:
        tail = f"最后预留 {remaining:.1f} 分钟用于沉淀与微调舞步。"
    elif remaining >= 1.0:
        tail = f"仍有 {remaining:.1f} 分钟机动时间随时呼应美羽的反馈。"
    else:
        tail = "几乎所有时间都投向惊喜本身，请保持全程陪伴。"
    return f"重点安排：{highlight}。{tail}"


def lightning_surprise_plan(
    time_budget: float,
    actions: Optional[Sequence[SurpriseAction]] = None,
    *,
    buffer: float = 4.0,
) -> MutableMapping[str, object]:
    """Return the highest-impact surprise plan within a time budget."""

    if time_budget <= 0:
        raise ValueError("time_budget must be positive")

    catalog = actions or DEFAULT_SURPRISE_ACTIONS
    selected = _select_actions(time_budget, catalog, buffer=buffer)

    total_time = sum(action.total_time for action in selected)
    total_delight = sum(action.delight for action in selected)
    remaining = max(time_budget - total_time, 0.0)

    plan_actions: List[Mapping[str, object]] = [
        {
            "name": action.name,
            "duration": action.duration,
            "preparation": action.preparation,
            "total_time": action.total_time,
            "delight": action.delight,
            "tags": list(action.tags),
        }
        for action in selected
    ]

    return {
        "actions": plan_actions,
        "total_time": total_time,
        "total_delight": total_delight,
        "buffer_time": remaining,
        "efficiency": total_delight / total_time if total_time else 0.0,
        "message": _compose_message(selected, remaining),
    }


def describe_plan(plan: Mapping[str, object]) -> str:
    """Convert a plan dictionary to a short human-friendly outline."""

    actions = plan.get("actions", [])
    if not isinstance(actions, Sequence):
        raise TypeError("plan['actions'] must be a sequence")

    lines: List[str] = []
    for index, raw in enumerate(actions, start=1):
        if not isinstance(raw, Mapping):
            raise TypeError("every action entry must be a mapping")
        name = raw.get("name", "(unknown)")
        total_time = float(raw.get("total_time", 0.0))
        delight = float(raw.get("delight", 0.0))
        lines.append(
            f"{index}. {name} —— {total_time:.1f} 分钟完成，惊喜值 {delight:.1f}",
        )

    message = plan.get("message")
    if isinstance(message, str) and message:
        lines.append("")
        lines.append(message)

    return "\n".join(lines)


__all__ = [
    "DEFAULT_SURPRISE_ACTIONS",
    "SurpriseAction",
    "describe_plan",
    "lightning_surprise_plan",
]
