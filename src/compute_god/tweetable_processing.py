"""Numerically emulate a tweet-length Processing sketch.

The original tweet-sized Processing snippet compresses an entire animation into
just over one hundred characters::

    f=0,d=200,draw=c=>{for(f||createCanvas(W=400,W),noStroke(background(0,20)),
    i=0;i<PI;i+=PI/256)r=99*cos(i+f/2),x=sin(i)*r+d,y=99*cos(i)+d,fill(W,150),
    circle(x,y,3),circle(W-x,y,3),fill(W,22),circle(W-x,W-y,3),circle(y,x,3),
    circle(y,W-x,3);f-=.05}

It sketches a pair of mirrored rings that slowly tumble by manipulating a
single phase accumulator ``f``.  Rendering the effect normally requires a full
Processing runtime.  The :mod:`compute_god` project prefers testable, data-first
representations instead, so this module translates the sketch into pure Python
structures.  We simulate the geometry produced by each frame and leave actual
rasterisation to downstream consumers.

Two tiny dataclasses model the output: :class:`ProcessingCircle` captures the
position, diameter and greyscale fill of a single ``circle`` call; and
:class:`ProcessingFrame` aggregates the full set of circles together with the
background wash used at the beginning of ``draw``.  The
:class:`TweetableProcessingSketch` class mirrors the behaviour of the JavaScript
snippet—each call to :meth:`generate_frame` advances the phase by ``0.05`` and
returns the circles needed to paint the new state.  Consumers can feed those
instructions into their own renderer (matplotlib, PIL, SVG, …) while tests assert
against the deterministic numeric output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, pi, sin
from typing import Tuple


GreyscaleFill = Tuple[float, float]


@dataclass(frozen=True)
class ProcessingCircle:
    """Descriptor of a ``circle`` invocation from the original sketch.

    Attributes
    ----------
    x, y:
        Centre of the circle in pixels.
    diameter:
        The circle diameter.  The sketch always used ``3`` but the field keeps
        the data explicit for downstream renderers.
    fill:
        Two-channel greyscale colour corresponding to ``fill(W, alpha)`` in
        Processing.  The first component is the grey level, the second the
        alpha.
    """

    x: float
    y: float
    diameter: float
    fill: GreyscaleFill


@dataclass(frozen=True)
class ProcessingFrame:
    """All drawing instructions required for a single frame."""

    width: float
    background: GreyscaleFill
    circles: Tuple[ProcessingCircle, ...]


@dataclass
class TweetableProcessingSketch:
    """Faithfully reproduce the tweet-length Processing sketch numerically."""

    width: float = 400.0
    radius: float = 99.0
    circle_diameter: float = 3.0
    angle_steps: int = 256
    phase: float = 0.0
    _centre: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.angle_steps <= 0:
            raise ValueError("angle_steps must be positive")
        if self.radius <= 0.0:
            raise ValueError("radius must be positive")
        if self.circle_diameter <= 0.0:
            raise ValueError("circle_diameter must be positive")

        # ``d`` in the snippet always sat halfway across the canvas.  Keeping it
        # derived from the width means callers only need to tweak a single
        # parameter when experimenting with larger canvases.
        self._centre = self.width / 2.0

    @property
    def centre(self) -> float:
        """Return the centre offset corresponding to ``d`` in the original code."""

        return self._centre

    def generate_frame(self) -> ProcessingFrame:
        """Return the drawing instructions for the next animation frame."""

        highlight_fill: GreyscaleFill = (self.width, 150.0)
        shadow_fill: GreyscaleFill = (self.width, 22.0)
        background: GreyscaleFill = (0.0, 20.0)

        circles: list[ProcessingCircle] = []
        for step in range(self.angle_steps):
            angle = step * pi / self.angle_steps
            radius = self.radius * cos(angle + self.phase / 2.0)
            x = sin(angle) * radius + self.centre
            y = self.radius * cos(angle) + self.centre

            circles.append(
                ProcessingCircle(x=x, y=y, diameter=self.circle_diameter, fill=highlight_fill)
            )
            circles.append(
                ProcessingCircle(
                    x=self.width - x, y=y, diameter=self.circle_diameter, fill=highlight_fill
                )
            )
            circles.append(
                ProcessingCircle(
                    x=self.width - x,
                    y=self.width - y,
                    diameter=self.circle_diameter,
                    fill=shadow_fill,
                )
            )
            circles.append(
                ProcessingCircle(
                    x=y,
                    y=x,
                    diameter=self.circle_diameter,
                    fill=shadow_fill,
                )
            )
            circles.append(
                ProcessingCircle(
                    x=y,
                    y=self.width - x,
                    diameter=self.circle_diameter,
                    fill=shadow_fill,
                )
            )

        frame = ProcessingFrame(
            width=self.width,
            background=background,
            circles=tuple(circles),
        )
        self.phase -= 0.05
        return frame


__all__ = [
    "GreyscaleFill",
    "ProcessingCircle",
    "ProcessingFrame",
    "TweetableProcessingSketch",
]
