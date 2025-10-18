"""Daily-life toolkit generators for playful self-care rituals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class LifeNeed:
    """Representation of a human need we want to nurture.

    Parameters
    ----------
    name:
        Human-friendly label.  It must not be empty or whitespace.
    description:
        Short explanation of why the need matters.
    priority:
        Positive integer representing how urgent the need feels compared to
        other entries.  Higher values indicate stronger urgency.
    tags:
        Optional thematic markers.  They help downstream tooling cluster
        compatible rituals.
    frequency:
        How often the need should be revisited.  ``"daily"`` by default.
    """

    name: str
    description: str
    priority: int = 1
    tags: tuple[str, ...] = ()
    frequency: str = "daily"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("life needs require a non-empty name")
        if not self.description or not self.description.strip():
            raise ValueError("life needs require a non-empty description")
        if self.priority < 1:
            raise ValueError("priority must be a positive integer")
        if any(not isinstance(tag, str) or not tag.strip() for tag in self.tags):
            raise TypeError("tags must be a sequence of non-empty strings")
        if not isinstance(self.frequency, str) or not self.frequency.strip():
            raise TypeError("frequency must be a non-empty string")


@dataclass(frozen=True)
class ToolRitual:
    """Concrete ritual fulfilling one or more :class:`LifeNeed` instances."""

    title: str
    steps: tuple[str, ...]
    duration_minutes: int
    mood: str = "balanced"

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("tool rituals require a title")
        if not self.steps:
            raise ValueError("tool rituals require at least one step")
        if any(not isinstance(step, str) or not step.strip() for step in self.steps):
            raise TypeError("each ritual step must be a non-empty string")
        if self.duration_minutes <= 0:
            raise ValueError("rituals must take a positive amount of time")
        if not isinstance(self.mood, str) or not self.mood.strip():
            raise TypeError("mood must be a non-empty string")


def _hydrate_steps(glasses: int, *, flavor: str | None, start_warm: bool) -> tuple[str, ...]:
    prefix = "温水" if start_warm else "常温水"
    steps: list[str] = [f"醒来后先喝一杯{prefix}，提醒身体进入白天节奏"]
    if flavor:
        steps.append(f"准备一壶带有{flavor}香气的水，增加饮用仪式感")
    interval = max(2, min(3, glasses // 3 or 1))
    for index in range(1, glasses):
        block = index // interval + 1
        steps.append(
            f"第 {block} 个时间块设置提醒：完成第 {index + 1} 杯水"
        )
    steps.append("睡前 1 小时补最后一杯，温柔收尾")
    return tuple(steps)


def design_hydration_ritual(
    wake_hours: int,
    *,
    flavor: str | None = None,
    start_with_warm: bool = False,
) -> ToolRitual:
    """Design a hydration ritual matching the number of awake hours.

    The ritual balances evenly spaced reminders with a gentle finale before
    sleep.  ``wake_hours`` must be within the typical human waking range (at
    least 8 hours and no more than 18).
    """

    if wake_hours < 8 or wake_hours > 18:
        raise ValueError("wake_hours must be between 8 and 18 hours")
    glasses = max(5, wake_hours // 2)
    steps = _hydrate_steps(glasses, flavor=flavor, start_warm=start_with_warm)
    duration = 3 * glasses  # spread across the day as micro-moments
    mood = "refreshing" if flavor else "grounded"
    return ToolRitual("全天水合规划", steps, duration_minutes=duration, mood=mood)


def design_meal_landscape(
    preferences: Sequence[str],
    budget: float,
    *,
    anchor_meal: str = "午餐",
) -> ToolRitual:
    """Create a vibrant meal-planning ritual that respects flavour cues."""

    if not preferences:
        raise ValueError("at least one food preference is required")
    if budget <= 0:
        raise ValueError("budget must be positive")
    cleaned_preferences = [pref.strip() for pref in preferences if pref.strip()]
    if not cleaned_preferences:
        raise ValueError("preferences must contain non-empty strings")
    featured = "、".join(cleaned_preferences[:3])
    steps = (
        f"以{anchor_meal}为锚点，选择包含 {featured} 的主菜",  # type: ignore[str-bytes-safe]
        "提前腌制或切好食材，放入透明保鲜盒，建立可视化灵感墙",
        f"为 {len(cleaned_preferences)} 个偏好准备互换小菜盒，确保预算控制在 ¥{budget:.0f} 内",
        "用手机记录一张餐桌照片，写下当天味觉心情",
    )
    return ToolRitual("风味餐桌布署", steps, duration_minutes=25, mood="nourishing")


def design_energy_breaks(
    sessions: int,
    focus_minutes: int,
    *,
    break_minutes: int = 6,
) -> ToolRitual:
    """Introduce rhythmic micro-breaks to sustain focus."""

    if sessions < 1:
        raise ValueError("sessions must be a positive integer")
    if focus_minutes < 20:
        raise ValueError("focus_minutes should leave room for deep work")
    if break_minutes <= 0:
        raise ValueError("break_minutes must be positive")

    steps = [
        f"设置 {sessions} 个专注区块，每区块 {focus_minutes} 分钟",
        "区块结束时进行 30 秒伸展 + 深呼吸",
        f"用 {break_minutes} 分钟散步或补水，再进入下一轮",
    ]
    steps.append("最后记录一个亮点与一个放松瞬间")
    return ToolRitual("节奏能量补给", tuple(steps), duration_minutes=(focus_minutes + break_minutes) * sessions, mood="uplifting")


def assemble_life_toolkit(
    needs: Sequence[LifeNeed],
    rituals: Sequence[ToolRitual],
    *,
    available_minutes: int,
    include_gratitude_prompt: bool = True,
) -> Mapping[str, object]:
    """Greedy scheduler pairing rituals with the highest priority needs."""

    if not needs:
        raise ValueError("at least one life need must be provided")
    if not rituals:
        raise ValueError("at least one ritual must be provided")
    if available_minutes <= 0:
        raise ValueError("available_minutes must be positive")

    ordered_needs = sorted(needs, key=lambda need: need.priority, reverse=True)
    available = available_minutes
    assignments: list[dict[str, object]] = []
    need_cycle = list(ordered_needs)
    if not need_cycle:
        raise ValueError("life needs cannot be empty")

    idx = 0
    for ritual in sorted(rituals, key=lambda r: r.duration_minutes):
        if ritual.duration_minutes > available:
            continue
        need = need_cycle[idx % len(need_cycle)]
        assignments.append(
            {
                "need": need.name,
                "title": ritual.title,
                "duration": ritual.duration_minutes,
                "steps": ritual.steps,
                "mood": ritual.mood,
            }
        )
        available -= ritual.duration_minutes
        idx += 1

    if not assignments:
        raise ValueError("no rituals fit within the available minutes")

    plan: dict[str, object] = {
        "needs": tuple(need.name for need in ordered_needs),
        "schedule": tuple(assignments),
        "remaining_minutes": available,
    }
    if include_gratitude_prompt:
        plan["gratitude_prompt"] = "写下今天感谢的一个细节，巩固生活的温度"
    return plan


__all__ = [
    "LifeNeed",
    "ToolRitual",
    "assemble_life_toolkit",
    "design_energy_breaks",
    "design_hydration_ritual",
    "design_meal_landscape",
]
