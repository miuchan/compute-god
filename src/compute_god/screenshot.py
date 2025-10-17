"""Utility helpers for rendering and verifying guided screenshots.

The project often talks about universe observability and delightful surfaces.
While most modules focus on pure computation, a handful of tests need a
lightweight way to build deterministic screenshots so that higher level
pipelines can validate their rendering stack.  The :class:`ScreenshotEnvironment`
defined here offers that bridge: it assembles a mobile-inspired layout using
`Pillow` primitives and exposes a verification helper that inspects a few key
pixels to ensure the expected colours are present.

The environment purposefully keeps all geometry values explicit which makes the
generated image predictable and friendly to unit tests.  Layout information is
recorded so that callers can sample regions (e.g. card accents, the search bar
or keyboard keys) without duplicating coordinate logic.  Tests can therefore
assert that a screenshot was produced, written to disk and visually consistent
with the design mock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

RGBColour = Tuple[int, int, int]
Bounds = Tuple[int, int, int, int]


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
    """Palette used by :class:`ScreenshotEnvironment`.

    The defaults loosely follow the mock shared in design discussions: muted
    grey backgrounds, colourful project cards and soft keyboard keys.
    """

    background: str = "#F6F6F8"
    card_surface: str = "#FFFFFF"
    search_surface: str = "#F1F2F6"
    search_icon: str = "#9CA0AC"
    text_primary: str = "#171717"
    text_secondary: str = "#5E5E5E"
    keyboard_key: str = "#FFFFFF"
    keyboard_shadow: str = "#D7DAE4"
    keyboard_text: str = "#1D1D1F"
    accent_colours: Tuple[str, str, str] = ("#F16D7A", "#8FDDB3", "#B3A4F8")

    def accent_colour(self, index: int) -> str:
        """Return the accent colour for ``index`` cycling through the palette."""

        if index < 0:
            raise ValueError("Accent colour index must be non-negative")
        return self.accent_colours[index % len(self.accent_colours)]


@dataclass
class ScreenshotEnvironment:
    """Create and validate a guided screenshot layout."""

    width: int = 1170
    height: int = 2532
    horizontal_margin: int = 72
    vertical_margin: int = 140
    theme: ScreenshotTheme = field(default_factory=ScreenshotTheme)
    _palette: Dict[str, RGBColour] = field(init=False, repr=False)
    _layout: Dict[str, Bounds] = field(default_factory=dict, init=False, repr=False)
    _last_image: Optional[Image.Image] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Screenshot dimensions must be positive")

        self._palette = {
            "background": _parse_colour(self.theme.background),
            "card_surface": _parse_colour(self.theme.card_surface),
            "search_surface": _parse_colour(self.theme.search_surface),
            "search_icon": _parse_colour(self.theme.search_icon),
            "text_primary": _parse_colour(self.theme.text_primary),
            "text_secondary": _parse_colour(self.theme.text_secondary),
            "keyboard_key": _parse_colour(self.theme.keyboard_key),
            "keyboard_shadow": _parse_colour(self.theme.keyboard_shadow),
            "keyboard_text": _parse_colour(self.theme.keyboard_text),
            "accent_0": _parse_colour(self.theme.accent_colour(0)),
            "accent_1": _parse_colour(self.theme.accent_colour(1)),
            "accent_2": _parse_colour(self.theme.accent_colour(2)),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render(self) -> Image.Image:
        """Render the screenshot layout and return a Pillow image."""

        self._layout = {}
        image = Image.new("RGB", (self.width, self.height), self._palette["background"])
        draw = ImageDraw.Draw(image)

        header_bottom = self._draw_header(draw)
        cards_bottom = self._draw_cards(draw, header_bottom)
        search_bottom = self._draw_search_bar(draw, cards_bottom)
        self._draw_keyboard(draw, search_bottom)

        self._last_image = image
        return image

    def save(self, path: Path | str, image: Optional[Image.Image] = None) -> Path:
        """Render (if needed) and persist the screenshot to ``path``."""

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
                "search": image.getpixel(self._sample_point("search_bar", 120, 50)),
                "accent_0": image.getpixel(self._sample_point("card:0:accent", 40, 40)),
                "accent_1": image.getpixel(self._sample_point("card:1:accent", 40, 40)),
                "keyboard": image.getpixel(self._sample_point("keyboard:0:0", 30, 30)),
            }
        except KeyError:
            return False

        return (
            samples["background"] == self._palette["background"]
            and samples["search"] == self._palette["search_surface"]
            and samples["accent_0"] == self._palette["accent_0"]
            and samples["accent_1"] == self._palette["accent_1"]
            and samples["keyboard"] == self._palette["keyboard_key"]
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
    def _draw_header(self, draw: ImageDraw.ImageDraw) -> int:
        title_text = "Search"
        title_font = self._load_font(96, bold=True)
        title_pos = (self.horizontal_margin, self.vertical_margin)
        draw.text(title_pos, title_text, fill=self._palette["text_primary"], font=title_font)
        title_width, title_height = self._text_size(draw, title_text, title_font)
        self._register_layout("title", (title_pos[0], title_pos[1], title_pos[0] + title_width, title_pos[1] + title_height))

        subtitle_text = "Recent Projects"
        subtitle_font = self._load_font(48)
        subtitle_y = title_pos[1] + title_height + 48
        subtitle_pos = (self.horizontal_margin, subtitle_y)
        draw.text(subtitle_pos, subtitle_text, fill=self._palette["text_secondary"], font=subtitle_font)
        subtitle_width, subtitle_height = self._text_size(draw, subtitle_text, subtitle_font)
        self._register_layout("subtitle", (subtitle_pos[0], subtitle_pos[1], subtitle_pos[0] + subtitle_width, subtitle_pos[1] + subtitle_height))

        return subtitle_pos[1] + subtitle_height + 64

    def _draw_cards(self, draw: ImageDraw.ImageDraw, top: int) -> int:
        card_width = 420
        card_height = 480
        card_spacing = 48
        accent_height = 260
        radius = 48

        cards = [
            ("card:0", "Chengdu Winter", "Snow memories", self._palette["accent_0"]),
            ("card:1", "Chengdu Autumn", "Warm evenings", self._palette["accent_1"]),
            ("card:2", "2024 Travel", "Dream itinerary", self._palette["accent_2"]),
        ]

        for index, (name, title, subtitle, accent_colour) in enumerate(cards):
            row = index // 2
            column = index % 2
            x0 = self.horizontal_margin + column * (card_width + card_spacing)
            y0 = top + row * (card_height + card_spacing)
            x1 = x0 + card_width
            y1 = y0 + card_height

            shadow_bounds = (x0, y0 + 10, x1, y1 + 10)
            draw.rounded_rectangle(shadow_bounds, radius=radius, fill=self._palette["keyboard_shadow"])

            draw.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=self._palette["card_surface"])
            accent_bounds = (x0 + 2, y0 + 2, x1 - 2, y0 + accent_height)
            draw.rectangle((x0, y0, x1, y0 + accent_height), fill=accent_colour)

            title_font = self._load_font(48, bold=True)
            subtitle_font = self._load_font(36)
            text_x = x0 + 36
            title_y = y0 + accent_height + 32
            subtitle_y = title_y + 64
            draw.text((text_x, title_y), title, fill=self._palette["text_primary"], font=title_font)
            draw.text((text_x, subtitle_y), subtitle, fill=self._palette["text_secondary"], font=subtitle_font)

            self._register_layout(name, (x0, y0, x1, y1))
            self._register_layout(f"{name}:accent", (x0, y0, x1, y0 + accent_height))

        rows = (len(cards) + 1) // 2
        return top + rows * (card_height + card_spacing)

    def _draw_search_bar(self, draw: ImageDraw.ImageDraw, top: int) -> int:
        search_height = 128
        search_radius = 48
        search_left = self.horizontal_margin
        search_right = self.width - self.horizontal_margin
        search_bounds = (search_left, top, search_right, top + search_height)

        draw.rounded_rectangle(search_bounds, radius=search_radius, fill=self._palette["search_surface"])
        self._register_layout("search_bar", search_bounds)

        icon_radius = 28
        icon_center = (search_left + 72, top + search_height // 2)
        icon_bounds = (
            icon_center[0] - icon_radius,
            icon_center[1] - icon_radius,
            icon_center[0] + icon_radius,
            icon_center[1] + icon_radius,
        )
        draw.ellipse(icon_bounds, fill=self._palette["search_icon"])

        placeholder_text = "Pinned searches"
        placeholder_font = self._load_font(44)
        placeholder_x = icon_bounds[2] + 28
        placeholder_y = icon_center[1] - self._text_size(draw, placeholder_text, placeholder_font)[1] // 2
        draw.text((placeholder_x, placeholder_y), placeholder_text, fill=self._palette["text_secondary"], font=placeholder_font)

        button_width = 184
        button_bounds = (
            search_right - button_width - 32,
            top + 28,
            search_right - 32,
            top + search_height - 28,
        )
        draw.rounded_rectangle(button_bounds, radius=36, fill=self._palette["accent_0"])
        button_text = "Search"
        button_font = self._load_font(44, bold=True)
        text_width, text_height = self._text_size(draw, button_text, button_font)
        text_x = button_bounds[0] + (button_width - text_width) / 2
        text_y = button_bounds[1] + (button_bounds[3] - button_bounds[1] - text_height) / 2
        draw.text((text_x, text_y), button_text, fill=self._palette["card_surface"], font=button_font)

        self._register_layout("search_button", button_bounds)
        return search_bounds[3] + 96

    def _draw_keyboard(self, draw: ImageDraw.ImageDraw, top: int) -> None:
        key_width = 96
        key_height = 120
        key_spacing = 16
        row_spacing = 24
        radius = 36

        rows: List[List[str]] = [
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            list("ZXCVBNM"),
            ["space"],
        ]

        for row_index, row in enumerate(rows):
            row_top = top + row_index * (key_height + row_spacing)

            if row == ["space"]:
                space_width = int(self.width * 0.58)
                left = (self.width - space_width) // 2
                bounds = (left, row_top, left + space_width, row_top + key_height)
                self._draw_key(draw, bounds, "space", radius)
                self._register_layout("keyboard:space", bounds)
                continue

            row_width = len(row) * key_width + (len(row) - 1) * key_spacing
            row_left = (self.width - row_width) // 2

            for column, label in enumerate(row):
                x0 = row_left + column * (key_width + key_spacing)
                y0 = row_top
                bounds = (x0, y0, x0 + key_width, y0 + key_height)
                self._draw_key(draw, bounds, label, radius)
                key_name = f"keyboard:{row_index}:{column}"
                self._register_layout(key_name, bounds)

    def _draw_key(self, draw: ImageDraw.ImageDraw, bounds: Bounds, label: str, radius: int) -> None:
        x0, y0, x1, y1 = bounds
        shadow_offset = 8
        draw.rounded_rectangle((x0, y0 + shadow_offset, x1, y1 + shadow_offset), radius=radius, fill=self._palette["keyboard_shadow"])
        draw.rounded_rectangle(bounds, radius=radius, fill=self._palette["keyboard_key"])

        font_size = 52 if len(label) == 1 else 44
        font = self._load_font(font_size, bold=len(label) == 1)
        display = label.upper() if len(label) == 1 else label.title()
        text_width, text_height = self._text_size(draw, display, font)
        text_x = x0 + (x1 - x0 - text_width) / 2
        text_y = y0 + (y1 - y0 - text_height) / 2
        draw.text((text_x, text_y), display, fill=self._palette["keyboard_text"], font=font)

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

