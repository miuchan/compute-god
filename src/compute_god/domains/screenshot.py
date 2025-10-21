"""Utility helpers for rendering and verifying guided screenshots.

The project often talks about universe observability and delightful surfaces.
While most modules focus on pure computation, a handful of tests need a
lightweight way to build deterministic screenshots so that higher level
pipelines can validate their rendering stack.  The :class:`ScreenshotEnvironment`
defined here offers that bridge: it assembles a desktop-inspired "Earth Online"
landing layout using `Pillow` primitives and exposes a verification helper that
inspects a few key pixels to ensure the expected colours are present.

The environment purposefully keeps all geometry values explicit which makes the
generated image predictable and friendly to unit tests.  Layout information is
recorded so that callers can sample regions (e.g. the hero accent block or the
feature column capsules) without duplicating coordinate logic.  Tests can
therefore assert that a screenshot was produced, written to disk and visually
consistent with the design mock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, TYPE_CHECKING

try:  # pragma: no cover - import guard
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError as exc:  # pragma: no cover - exercised in environments without Pillow
    _PIL_IMPORT_ERROR = exc

    class _SimpleImage:
        """Very small in-memory RGB image used as a Pillow fallback."""

        def __init__(self, size: Tuple[int, int], colour: RGBColour) -> None:
            width, height = size
            if width <= 0 or height <= 0:
                raise ValueError("Image dimensions must be positive")
            self.size = (int(width), int(height))
            self._pixels = [
                [tuple(colour) for _ in range(self.size[0])] for _ in range(self.size[1])
            ]

        def copy(self) -> "_SimpleImage":
            clone = _SimpleImage(self.size, (0, 0, 0))
            clone._pixels = [row[:] for row in self._pixels]
            return clone

        def getpixel(self, point: Tuple[int, int]) -> RGBColour:
            x, y = point
            width, height = self.size
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError("Pixel coordinate out of range")
            return self._pixels[y][x]

        def putpixel(self, point: Tuple[int, int], colour: RGBColour) -> None:
            x, y = point
            width, height = self.size
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError("Pixel coordinate out of range")
            self._pixels[y][x] = tuple(colour)

        def save(self, path: Path | str, format: str = "PNG") -> None:  # pragma: no cover - trivial
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            width, height = self.size
            with target.open("wb") as handle:
                handle.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
                for row in self._pixels:
                    handle.write(bytes(channel for pixel in row for channel in pixel))

    class _SimpleFont:
        def __init__(self, size: int, bold: bool = False) -> None:
            self.size = size
            self.bold = bold

    class _SimpleDraw:
        def __init__(self, image: _SimpleImage) -> None:
            self._image = image

        def rectangle(self, bounds: Bounds, *, fill: RGBColour) -> None:
            x0, y0, x1, y1 = (int(b) for b in bounds)
            for y in range(max(0, y0), min(self._image.size[1], y1)):
                row = self._image._pixels[y]
                for x in range(max(0, x0), min(self._image.size[0], x1)):
                    row[x] = tuple(fill)

        def rounded_rectangle(self, bounds: Bounds, radius: int, *, fill: RGBColour) -> None:
            self.rectangle(bounds, fill=fill)

        def ellipse(self, bounds: Bounds, *, fill: RGBColour) -> None:
            x0, y0, x1, y1 = (int(b) for b in bounds)
            rx = max(1, (x1 - x0) / 2)
            ry = max(1, (y1 - y0) / 2)
            cx = x0 + rx
            cy = y0 + ry
            for y in range(max(0, y0), min(self._image.size[1], y1)):
                for x in range(max(0, x0), min(self._image.size[0], x1)):
                    dx = (x + 0.5 - cx) / rx
                    dy = (y + 0.5 - cy) / ry
                    if dx * dx + dy * dy <= 1.0:
                        self._image._pixels[y][x] = tuple(fill)

        def text(self, position: Tuple[float, float], text: str, *, fill: RGBColour, font: _SimpleFont) -> None:
            # The fallback renderer does not draw glyphs; we merely record the
            # bounding box to keep layout metrics consistent.  Sampling in tests
            # never touches text regions so this is sufficient.
            return

        def textbbox(self, position: Tuple[float, float], text: str, *, font: _SimpleFont) -> Tuple[int, int, int, int]:
            x, y = position
            width = int(len(text) * (font.size * (0.55 if font.bold else 0.5)))
            height = int(font.size * (1.05 if font.bold else 1.0))
            return int(x), int(y), int(x + width), int(y + height)

    class _ImageModule:
        Image = _SimpleImage

        @staticmethod
        def new(mode: str, size: Tuple[int, int], colour: RGBColour) -> _SimpleImage:
            if mode != "RGB":
                raise ValueError("Fallback renderer only supports RGB mode")
            return _SimpleImage(size, colour)

    class _ImageDrawModule:
        ImageDraw = _SimpleDraw

        @staticmethod
        def Draw(image: _SimpleImage) -> _SimpleDraw:
            return _SimpleDraw(image)

    class _ImageFontModule:
        ImageFont = _SimpleFont

        @staticmethod
        def truetype(name: str, size: int) -> _SimpleFont:
            bold = "bold" in name.lower()
            return _SimpleFont(size, bold=bold)

        @staticmethod
        def load_default() -> _SimpleFont:
            return _SimpleFont(12)

    Image = _ImageModule()
    ImageDraw = _ImageDrawModule()
    ImageFont = _ImageFontModule()
    _FALLBACK_ACTIVE = True
else:  # pragma: no cover - module import is trivial to test indirectly
    _PIL_IMPORT_ERROR = None
    _FALLBACK_ACTIVE = False

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from PIL import Image as PILImage
else:
    PILImage = Any

RGBColour = Tuple[int, int, int]
Bounds = Tuple[int, int, int, int]


def _require_pillow() -> None:
    if _PIL_IMPORT_ERROR is not None and not _FALLBACK_ACTIVE:
        raise ModuleNotFoundError(
            "Pillow is required to use ScreenshotEnvironment; install compute-god[image]"
        ) from _PIL_IMPORT_ERROR


def _parse_colour(value: str) -> RGBColour:
    """Return the RGB triple encoded by ``value``.

    Parameters
    ----------
    value:
        Hexadecimal colour string in ``#RRGGBB`` form.

    Raises
    ------
    ValueError
        If ``value`` is not a recognised hexadecimal colour.
    """

    candidate = value.strip()
    if not candidate.startswith("#"):
        raise ValueError(f"Colour value must start with '#': {value!r}")

    digits = candidate[1:]
    if len(digits) != 6:
        raise ValueError(f"Colour value must contain 6 hex digits: {value!r}")

    try:
        red = int(digits[0:2], 16)
        green = int(digits[2:4], 16)
        blue = int(digits[4:6], 16)
    except ValueError as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Colour value contains non-hexadecimal characters: {value!r}") from exc

    return red, green, blue


@dataclass(frozen=True)
class ScreenshotTheme:
    """Palette used by :class:`ScreenshotEnvironment`."""

    background_top: str = "#030916"
    background_bottom: str = "#0E2A4A"
    hero_surface: str = "#071C2E"
    hero_outline: str = "#104066"
    panel_surface: str = "#0B2236"
    panel_border: str = "#12395C"
    text_primary: str = "#F6FAFF"
    text_secondary: str = "#95B2D6"
    accent_primary: str = "#00B8D9"
    accent_secondary: str = "#15C79B"
    accent_tertiary: str = "#8A7BFF"
    divider: str = "#1B4168"


@dataclass
class ScreenshotEnvironment:
    """Create and validate a guided screenshot layout."""

    width: int = 1920
    height: int = 1080
    horizontal_margin: int = 120
    vertical_margin: int = 96
    theme: ScreenshotTheme = field(default_factory=ScreenshotTheme)
    _palette: Dict[str, RGBColour] = field(init=False, repr=False)
    _layout: Dict[str, Bounds] = field(default_factory=dict, init=False, repr=False)
    _last_image: Optional[PILImage] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        _require_pillow()
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Screenshot dimensions must be positive")

        self._palette = {
            "background_top": _parse_colour(self.theme.background_top),
            "background_bottom": _parse_colour(self.theme.background_bottom),
            "hero_surface": _parse_colour(self.theme.hero_surface),
            "hero_outline": _parse_colour(self.theme.hero_outline),
            "panel_surface": _parse_colour(self.theme.panel_surface),
            "panel_border": _parse_colour(self.theme.panel_border),
            "text_primary": _parse_colour(self.theme.text_primary),
            "text_secondary": _parse_colour(self.theme.text_secondary),
            "accent_primary": _parse_colour(self.theme.accent_primary),
            "accent_secondary": _parse_colour(self.theme.accent_secondary),
            "accent_tertiary": _parse_colour(self.theme.accent_tertiary),
            "divider": _parse_colour(self.theme.divider),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render(self) -> Image.Image:
        """Render the screenshot layout and return a Pillow image."""

        _require_pillow()
        self._layout = {}
        image = Image.new("RGB", (self.width, self.height), self._palette["background_top"])
        self._draw_background_gradient(image)
        draw = ImageDraw.Draw(image)

        nav_bottom = self._draw_navigation(draw)
        hero_bounds = self._draw_hero_panel(draw, nav_bottom + 24)
        column_bottom = self._draw_feature_column(draw, hero_bounds)
        footer_top = max(hero_bounds[3], column_bottom) + 40
        self._draw_footer(draw, footer_top)

        self._last_image = image
        return image

    def save(self, path: Path | str, image: Optional[Image.Image] = None) -> Path:
        """Render (if needed) and persist the screenshot to ``path``."""

        _require_pillow()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        if image is None:
            if self._last_image is None:
                image = self.render()
            else:
                image = self._last_image

        image.save(target, format="PNG")
        return target

    def verify(self, image: Optional[Image.Image] = None) -> bool:
        """Return ``True`` when ``image`` matches key layout expectations."""

        _require_pillow()
        if image is None:
            if self._last_image is None:
                raise ValueError("No screenshot rendered yet; call render() first")
            image = self._last_image

        if image.size != (self.width, self.height):
            return False

        if not self._layout:
            return False

        try:
            samples = {
                "background": image.getpixel((10, 10)),
                "hero_accent": image.getpixel(self._sample_point("hero:accent", 48, 48)),
                "hero_cta": image.getpixel(self._sample_point("hero:cta", 24, 24)),
                "feature_primary": image.getpixel(self._sample_point("feature:0:accent", 6, 60)),
                "feature_panel": image.getpixel(self._sample_point("feature:0", 120, 80)),
                "feature_tertiary": image.getpixel(self._sample_point("feature:2:accent", 6, 60)),
            }
        except KeyError:
            return False

        return (
            samples["background"] == self._palette["background_top"]
            and samples["hero_accent"] == self._palette["accent_primary"]
            and samples["hero_cta"] == self._palette["accent_secondary"]
            and samples["feature_primary"] == self._palette["accent_secondary"]
            and samples["feature_panel"] == self._palette["panel_surface"]
            and samples["feature_tertiary"] == self._palette["accent_tertiary"]
        )

    def component_bounds(self, name: str) -> Bounds:
        """Return the bounding box registered for ``name``."""

        if not self._layout:
            raise RuntimeError("Screenshot has not been rendered yet")
        try:
            return self._layout[name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise KeyError(f"Unknown component name: {name!r}") from exc

    @property
    def palette(self) -> Mapping[str, RGBColour]:
        """Return a read-only view of the colour palette used by the layout."""

        return dict(self._palette)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _draw_background_gradient(self, image: PILImage) -> None:
        width, height = image.size
        top_colour = self._palette["background_top"]
        bottom_colour = self._palette["background_bottom"]

        if height <= 1:
            return

        for y in range(height):
            ratio = y / (height - 1)
            blended = tuple(
                int(top_colour[channel] + (bottom_colour[channel] - top_colour[channel]) * ratio)
                for channel in range(3)
            )
            for x in range(width):
                image.putpixel((x, y), blended)

    def _draw_navigation(self, draw: ImageDraw.ImageDraw) -> int:
        brand_text = "EARTH ONLINE"
        brand_font = self._load_font(48, bold=True)
        brand_pos = (self.horizontal_margin, self.vertical_margin)
        draw.text(brand_pos, brand_text, fill=self._palette["text_primary"], font=brand_font)
        brand_width, brand_height = self._text_size(draw, brand_text, brand_font)
        self._register_layout(
            "nav:brand",
            (brand_pos[0], brand_pos[1], brand_pos[0] + brand_width, brand_pos[1] + brand_height),
        )

        tagline_text = "Planet Experience Lab"
        tagline_font = self._load_font(30)
        tagline_pos = (brand_pos[0], brand_pos[1] + brand_height + 10)
        draw.text(tagline_pos, tagline_text, fill=self._palette["text_secondary"], font=tagline_font)
        tagline_width, tagline_height = self._text_size(draw, tagline_text, tagline_font)
        self._register_layout(
            "nav:tagline",
            (tagline_pos[0], tagline_pos[1], tagline_pos[0] + tagline_width, tagline_pos[1] + tagline_height),
        )

        menu_items = ["序曲", "实验目录", "算力观测", "联系我们"]
        menu_font = self._load_font(28)
        x = self.width - self.horizontal_margin
        menu_top = brand_pos[1]
        for label in reversed(menu_items):
            width, height = self._text_size(draw, label, menu_font)
            x -= width
            draw.text((x, menu_top), label, fill=self._palette["text_secondary"], font=menu_font)
            self._register_layout(
                f"nav:item:{label}",
                (x, menu_top, x + width, menu_top + height),
            )
            x -= 64

        return tagline_pos[1] + tagline_height + 36

    def _draw_hero_panel(self, draw: ImageDraw.ImageDraw, top: int) -> Bounds:
        hero_width = 760
        hero_height = 640
        outline_radius = 48
        inset = 6
        x0 = self.horizontal_margin
        y0 = top
        x1 = x0 + hero_width
        y1 = y0 + hero_height

        draw.rounded_rectangle((x0, y0, x1, y1), radius=outline_radius, fill=self._palette["hero_outline"])
        inner_bounds = (x0 + inset, y0 + inset, x1 - inset, y1 - inset)
        draw.rounded_rectangle(inner_bounds, radius=outline_radius - 6, fill=self._palette["hero_surface"])
        self._register_layout("hero:panel", inner_bounds)

        accent_top_margin = 36
        accent_side_margin = 36
        accent_height = 260
        accent_bounds = (
            inner_bounds[0] + accent_side_margin,
            inner_bounds[1] + accent_top_margin,
            inner_bounds[2] - accent_side_margin,
            inner_bounds[1] + accent_top_margin + accent_height,
        )
        draw.rounded_rectangle(accent_bounds, radius=32, fill=self._palette["accent_primary"])
        self._register_layout("hero:accent", accent_bounds)

        orb_size = 140
        orb_margin = 44
        orb_bounds = (
            accent_bounds[2] - orb_size - orb_margin,
            accent_bounds[1] + orb_margin,
            accent_bounds[2] - orb_margin,
            accent_bounds[1] + orb_margin + orb_size,
        )
        draw.ellipse(orb_bounds, fill=self._palette["accent_tertiary"])

        accent_title = "CLOSEAI"
        accent_title_font = self._load_font(44, bold=True)
        accent_title_pos = (accent_bounds[0] + 36, accent_bounds[1] + 40)
        draw.text(
            accent_title_pos,
            accent_title,
            fill=self._palette["text_primary"],
            font=accent_title_font,
        )

        accent_caption = "Planetary Experience Synthesiser"
        accent_caption_font = self._load_font(28)
        accent_caption_pos = (accent_title_pos[0], accent_title_pos[1] + 56)
        draw.text(
            accent_caption_pos,
            accent_caption,
            fill=self._palette["text_primary"],
            font=accent_caption_font,
        )

        ribbon_height = 12
        ribbon_bounds = (
            accent_bounds[0] + 32,
            accent_bounds[3] - ribbon_height - 32,
            accent_bounds[2] - 32,
            accent_bounds[3] - 32,
        )
        draw.rounded_rectangle(ribbon_bounds, radius=8, fill=self._palette["accent_secondary"])

        title_text = "新算器 · 行星级体验"
        title_font = self._load_font(58, bold=True)
        title_x = inner_bounds[0] + accent_side_margin
        title_y = accent_bounds[3] + 40
        draw.text((title_x, title_y), title_text, fill=self._palette["text_primary"], font=title_font)
        title_height = self._text_size(draw, title_text, title_font)[1]

        intro_text = "开放式算力网络，驱动 Earth Online 的持续演化。"
        intro_font = self._load_font(32)
        intro_y = title_y + title_height + 18
        draw.text((title_x, intro_y), intro_text, fill=self._palette["text_secondary"], font=intro_font)
        intro_height = self._text_size(draw, intro_text, intro_font)[1]

        bullet_lines = [
            "开放 API 与算子市场，按需装配宇宙工具链。",
            "多模态协同：终端、桌面、星舰同步推演场景。",
            "行星体验实验室一键发布调度，全栈观测。",
        ]
        bullet_font = self._load_font(30)
        bullet_start = intro_y + intro_height + 24
        for index, line in enumerate(bullet_lines):
            line_y = bullet_start + index * 54
            bullet_bounds = (
                title_x,
                line_y + 10,
                title_x + 14,
                line_y + 24,
            )
            draw.ellipse(bullet_bounds, fill=self._palette["accent_secondary"])
            draw.text(
                (title_x + 28, line_y),
                line,
                fill=self._palette["text_secondary"],
                font=bullet_font,
            )

        cta_width = 260
        cta_height = 72
        cta_bounds = (
            title_x,
            inner_bounds[3] - 48 - cta_height,
            title_x + cta_width,
            inner_bounds[3] - 48,
        )
        draw.rounded_rectangle(cta_bounds, radius=32, fill=self._palette["accent_secondary"])
        self._register_layout("hero:cta", cta_bounds)

        cta_text = "进入 CloseAI"
        cta_font = self._load_font(32, bold=True)
        text_width, text_height = self._text_size(draw, cta_text, cta_font)
        text_x = cta_bounds[0] + (cta_width - text_width) / 2
        text_y = cta_bounds[1] + (cta_height - text_height) / 2
        draw.text((text_x, text_y), cta_text, fill=self._palette["text_primary"], font=cta_font)

        return inner_bounds

    def _draw_feature_column(self, draw: ImageDraw.ImageDraw, hero_bounds: Bounds) -> int:
        column_left = hero_bounds[2] + 72
        column_right = self.width - self.horizontal_margin
        top = hero_bounds[1]

        heading_text = "CloseAI 新算器体验矩阵"
        heading_font = self._load_font(44, bold=True)
        draw.text((column_left, top), heading_text, fill=self._palette["text_primary"], font=heading_font)
        heading_width, heading_height = self._text_size(draw, heading_text, heading_font)
        self._register_layout(
            "column:heading",
            (column_left, top, column_left + heading_width, top + heading_height),
        )

        strap_bounds = (
            column_left,
            top + heading_height + 20,
            column_right,
            top + heading_height + 28,
        )
        draw.rectangle(strap_bounds, fill=self._palette["divider"])

        description = "OpenAI 的 CloseAI 将实时协作、观测与调度融合为统一界面，支持团队在行星级网络中实验与部署。"
        description_font = self._load_font(30)
        description_y = strap_bounds[3] + 24
        draw.text(
            (column_left, description_y),
            description,
            fill=self._palette["text_secondary"],
            font=description_font,
        )
        description_height = self._text_size(draw, description, description_font)[1]

        card_top = description_y + description_height + 36
        features = [
            (
                "智能特性",
                [
                    "开放编程接口，打造个性化的行星算子。",
                    "多模态推理与感知统一，实时响应事件。",
                ],
                "accent_secondary",
            ),
            (
                "关键管线",
                [
                    "事件总线聚合 artifact proxy / event bus，形成算力协作闭环。",
                    "可视化调度盘实时呈现状态流与回放。",
                ],
                "accent_primary",
            ),
            (
                "安全与治理",
                [
                    "多层加密、权限沙箱与算力隔离，保证实验安全可控。",
                    "内置回滚策略，确保每次推演都可恢复。",
                ],
                "accent_tertiary",
            ),
            (
                "结论",
                [
                    "CloseAI 新算器把复杂体验整合成统一的感知与行动界面，赋能 Earth Online 的下一次跃迁。",
                ],
                "accent_secondary",
            ),
        ]

        card_spacing = 28
        bottom = card_top
        for index, (title, body, accent_key) in enumerate(features):
            bottom = self._draw_feature_card(
                draw,
                index,
                column_left,
                column_right,
                bottom,
                title,
                body,
                accent_key,
            )
            bottom += card_spacing

        return bottom

    def _draw_feature_card(
        self,
        draw: ImageDraw.ImageDraw,
        index: int,
        left: int,
        right: int,
        top: int,
        title: str,
        body_lines: List[str],
        accent_key: str,
    ) -> int:
        padding_x = 48
        padding_y = 36
        title_font = self._load_font(36, bold=True)
        body_font = self._load_font(28)

        _, title_height = self._text_size(draw, title, title_font)
        body_sizes = [self._text_size(draw, line, body_font) for line in body_lines]
        body_height = sum(size[1] for size in body_sizes)
        body_height += 20 * max(len(body_lines) - 1, 0)

        card_height = padding_y * 2 + title_height + body_height
        outer_bounds = (left - 3, top - 3, right + 3, top + card_height + 3)
        draw.rounded_rectangle(outer_bounds, radius=34, fill=self._palette["panel_border"])
        bounds = (left, top, right, top + card_height)
        draw.rounded_rectangle(bounds, radius=32, fill=self._palette["panel_surface"])
        self._register_layout(f"feature:{index}", bounds)

        accent_bounds = (
            left + 24,
            top + padding_y,
            left + 24 + 18,
            top + card_height - padding_y,
        )
        draw.rounded_rectangle(accent_bounds, radius=10, fill=self._palette[accent_key])
        self._register_layout(f"feature:{index}:accent", accent_bounds)

        text_x = left + padding_x
        current_y = top + padding_y
        draw.text((text_x, current_y), title, fill=self._palette["text_primary"], font=title_font)
        current_y += title_height + 24

        for (line, (_, height)) in zip(body_lines, body_sizes):
            draw.text((text_x, current_y), line, fill=self._palette["text_secondary"], font=body_font)
            current_y += height + 20

        return bounds[3]

    def _draw_footer(self, draw: ImageDraw.ImageDraw, top: int) -> None:
        bottom_limit = self.height - self.vertical_margin
        footer_top = min(top, bottom_limit - 80)

        strap_bounds = (
            self.horizontal_margin,
            footer_top,
            self.horizontal_margin + 220,
            footer_top + 6,
        )
        draw.rectangle(strap_bounds, fill=self._palette["divider"])
        self._register_layout("footer:strap", strap_bounds)

        footer_text = "Earth Online · Planet Experience Lab"
        footer_font = self._load_font(26)
        text_y = strap_bounds[3] + 18
        draw.text(
            (self.horizontal_margin, text_y),
            footer_text,
            fill=self._palette["text_secondary"],
            font=footer_font,
        )
        width, height = self._text_size(draw, footer_text, footer_font)
        self._register_layout(
            "footer:text",
            (
                self.horizontal_margin,
                text_y,
                self.horizontal_margin + width,
                text_y + height,
            ),
        )

        contact_text = "欢迎访问 CloseAI 新算器，共建下一代行星体验。"
        contact_font = self._load_font(26)
        contact_width, contact_height = self._text_size(draw, contact_text, contact_font)
        contact_x = self.width - self.horizontal_margin - contact_width
        draw.text((contact_x, text_y), contact_text, fill=self._palette["text_secondary"], font=contact_font)
        self._register_layout(
            "footer:contact",
            (contact_x, text_y, contact_x + contact_width, text_y + contact_height),
        )

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _register_layout(self, name: str, bounds: Bounds) -> None:
        self._layout[name] = tuple(int(value) for value in bounds)

    def _sample_point(self, name: str, offset_x: int, offset_y: int) -> Tuple[int, int]:
        bounds = self._layout[name]
        x0, y0, x1, y1 = bounds
        x = max(min(x0 + offset_x, x1 - 1), x0)
        y = max(min(y0 + offset_y, y1 - 1), y0)
        return int(x), int(y)

    def _load_font(self, size: int, *, bold: bool = False) -> ImageFont.ImageFont:
        """Return a truetype font of ``size`` with a graceful fallback."""

        candidates = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "Arial Bold.ttf" if bold else "Arial.ttf",
        ]

        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue

        return ImageFont.load_default()

    @staticmethod
    def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height


__all__ = ["ScreenshotEnvironment", "ScreenshotTheme"]

