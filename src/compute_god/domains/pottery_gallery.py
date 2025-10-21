"""Generative pottery display inspired by archaeological museum vitrines."""

from __future__ import annotations

from dataclasses import dataclass, field
import random


@dataclass(frozen=True)
class PotteryVessel:
    """A single vessel on display."""

    shape: str
    height_cm: float
    diameter_cm: float
    era: str
    finish: str
    motif: str
    silhouette: str

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation of the vessel."""

        return {
            "shape": self.shape,
            "height_cm": round(self.height_cm, 2),
            "diameter_cm": round(self.diameter_cm, 2),
            "era": self.era,
            "finish": self.finish,
            "motif": self.motif,
            "silhouette": self.silhouette,
        }


@dataclass(frozen=True)
class PedestalRow:
    """A stepped pedestal row inside the vitrine."""

    level: int
    elevation_cm: float
    vessels: tuple[PotteryVessel, ...]
    spotlight_lux: float

    def width_cm(self, *, spacing_cm: float = 8.0) -> float:
        """Return the combined width of the row, including spacing between vessels."""

        if not self.vessels:
            return 0.0
        total_diameter = sum(v.diameter_cm for v in self.vessels)
        total_spacing = spacing_cm * (len(self.vessels) - 1)
        return round(total_diameter + total_spacing, 2)


@dataclass(frozen=True)
class PotteryDisplay:
    """A complete stepped display with contextual placards."""

    title: str
    rows: tuple[PedestalRow, ...]
    placards: tuple[str, ...] = field(default_factory=tuple)

    def vessel_count(self) -> int:
        return sum(len(row.vessels) for row in self.rows)

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable snapshot of the display."""

        return {
            "title": self.title,
            "rows": [
                {
                    "level": row.level,
                    "elevation_cm": round(row.elevation_cm, 2),
                    "spotlight_lux": round(row.spotlight_lux, 1),
                    "width_cm": row.width_cm(),
                    "vessels": [vessel.as_dict() for vessel in row.vessels],
                }
                for row in self.rows
            ],
            "placards": list(self.placards),
        }


_ShapeProfile = tuple[str, float, float, str]

_SHAPE_LIBRARY: tuple[_ShapeProfile, ...] = (
    ("罐", 38.0, 28.0, "肩部外鼓的储藏罐"),
    ("壶", 34.0, 20.0, "细颈提梁壶"),
    ("瓶", 42.0, 18.0, "高颈赏瓶"),
    ("钵", 18.0, 26.0, "敞口盛食钵"),
    ("碗", 16.0, 22.0, "折沿浅碗"),
    ("尊", 40.0, 24.0, "鼓腹尊"),
    ("豆", 24.0, 18.0, "高足豆"),
)

_ERAS: tuple[str, ...] = (
    "仰韶晚期",
    "龙山文化",
    "夏商交替期",
    "西周初期",
)

_FINISHES: tuple[str, ...] = (
    "灰褐色氧化焙烧",
    "细砂红陶",
    "抛光黑皮",
    "浅褐磨光",
)

_MOTIFS: tuple[str, ...] = (
    "云雷纹",
    "绳纹环带",
    "网格印纹",
    "素面压光",
    "弧线压印",
)


def _row_counts(row_total: int) -> list[int]:
    base = 6
    return [base + 2 * (row_total - level - 1) for level in range(row_total)]


def _spotlight_for_level(level: int) -> float:
    return 220.0 + level * 35.0


def _choose_silhouette(height: float, diameter: float) -> str:
    ratio = height / max(diameter, 1.0)
    if ratio >= 1.7:
        return "高挑轮廓"
    if ratio <= 1.1:
        return "稳重矮身"
    return "匀称中段"


def _generate_vessel(rng: random.Random) -> PotteryVessel:
    shape, base_height, base_diameter, silhouette_hint = rng.choice(_SHAPE_LIBRARY)
    height_variation = rng.uniform(-4.0, 4.0)
    diameter_variation = rng.uniform(-3.0, 3.0)
    height = base_height + height_variation
    diameter = max(12.0, base_diameter + diameter_variation)
    motif = rng.choice(_MOTIFS)
    finish = rng.choice(_FINISHES)
    era = rng.choice(_ERAS)
    silhouette = _choose_silhouette(height, diameter)
    if rng.random() < 0.25:
        silhouette = f"{silhouette_hint}·{silhouette}"
    return PotteryVessel(
        shape=shape,
        height_cm=height,
        diameter_cm=diameter,
        era=era,
        finish=finish,
        motif=motif,
        silhouette=silhouette,
    )


def generate_pottery_display(
    seed: int | None = None,
    *,
    rows: int = 4,
    title: str = "河套陶艺编年展",
    step_height_cm: float = 22.0,
    base_elevation_cm: float = 60.0,
) -> PotteryDisplay:
    """Generate a stepped pottery display reminiscent of a museum vitrine."""

    if rows < 2:
        raise ValueError("rows must be at least 2 to form a stepped display")

    rng = random.Random(seed)
    counts = _row_counts(rows)
    generated_rows: list[PedestalRow] = []
    for level, count in enumerate(counts):
        vessels = tuple(_generate_vessel(rng) for _ in range(count))
        elevation = base_elevation_cm + level * step_height_cm
        spotlight = _spotlight_for_level(level)
        generated_rows.append(
            PedestalRow(
                level=level,
                elevation_cm=elevation,
                vessels=vessels,
                spotlight_lux=spotlight,
            )
        )

    placards = (
        "展柜玻璃采用低反射涂层以保留陶器肌理。",
        "温湿度维持在 20℃ / 55% 以延缓氧化。",
    )

    return PotteryDisplay(title=title, rows=tuple(generated_rows), placards=placards)


def describe_display(display: PotteryDisplay) -> str:
    """Render a human-readable description of the display."""

    lines: list[str] = [f"《{display.title}》展柜，共 {len(display.rows)} 层。"]
    for row in display.rows:
        line = (
            f"- 第 {row.level} 层抬高至 {row.elevation_cm:.0f} cm，"
            f"聚光 {row.spotlight_lux:.0f} lx，陈列 {len(row.vessels)} 件。"
        )
        lines.append(line)
        highlight = sorted(row.vessels, key=lambda v: v.height_cm, reverse=True)[:2]
        for vessel in highlight:
            lines.append(
                "  · "
                f"{vessel.era}{vessel.shape}，高 {vessel.height_cm:.1f} cm，"
                f"腹径 {vessel.diameter_cm:.1f} cm，{vessel.finish}，{vessel.motif}。"
            )
    if display.placards:
        lines.append("说明：")
        lines.extend(f"- {placard}" for placard in display.placards)
    return "\n".join(lines)


__all__ = [
    "PotteryDisplay",
    "PotteryVessel",
    "PedestalRow",
    "describe_display",
    "generate_pottery_display",
]

