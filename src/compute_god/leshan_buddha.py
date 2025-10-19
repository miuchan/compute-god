"""Leshan Giant Buddha landscape model for the Compute-God catalogue.

The Leshan Giant Buddha sits at the confluence of three rivers in Sichuan
province.  Beyond being an awe-inspiring piece of stone sculpture it is also a
carefully engineered hydrological system: internal drainage channels, carved
sluices, and the broad lotus pedestal protect the statue from relentless
weathering.  This module captures a lightweight, deterministic snapshot of that
engineering so other universes in the repository can reference the Buddha as a
guardian node, a drainage benchmark, or a meditative ritual sequence.

The model splits the statue into sculptural segments, lists the hidden drainage
channels, and registers the observation platforms that pilgrims traverse.  The
data structures are intentionally small but expressive enough to power tests and
scenario builders.

Typical usage::

    from compute_god.leshan_buddha import build_leshan_buddha

    buddha = build_leshan_buddha(scale=1.1)
    print(buddha.total_height())
    print(buddha.drainage_margin(rainfall_mm_per_hour=45))

The helper functions keep floating point math reproducible to support the unit
tests shipped with the project.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class BuddhaSegment:
    """Representation of a single sculpted region of the Buddha.

    Parameters
    ----------
    name:
        Identifier used by other parts of the repository.  A small inventory of
        canonical names keeps scenarios deterministic.
    height_m:
        The vertical span of the segment in metres.
    width_m:
        Approximate frontal width of the segment in metres.
    slope_deg:
        Inclination of the sculpted plane in degrees.  A zero degree slope means
        the segment faces the observer directly while higher values indicate
        greater curvature towards the river.
    relief_factor:
        Multiplier applied when computing the surface area of the segment.  The
        lotus pedestal is flatter than the intricately carved head, so the
        factor encodes that nuance without resorting to detailed meshes.
    features:
        Narrative descriptors and engineering notes associated with the segment.
    """

    name: str
    height_m: float
    width_m: float
    slope_deg: float
    relief_factor: float
    features: tuple[str, ...]

    def surface_area(self) -> float:
        """Return an approximate surface area in square metres."""

        return self.height_m * self.width_m * self.relief_factor


@dataclass(frozen=True)
class DrainageChannel:
    """Internal drainage channel carved inside the statue."""

    name: str
    capacity_l_per_min: float
    connected_segments: tuple[str, ...]

    def covers_segment(self, segment_name: str) -> bool:
        """Return ``True`` if the channel protects the given segment."""

        return segment_name in self.connected_segments


@dataclass(frozen=True)
class ObservationPlatform:
    """Viewpoint or pathway that visitors follow."""

    name: str
    elevation_m: float
    distance_from_face_m: float
    focus_segment: str


@dataclass(frozen=True)
class LeshanBuddhaModel:
    """Complete structural snapshot of the Leshan Giant Buddha."""

    scale: float
    segments: tuple[BuddhaSegment, ...]
    drainage_channels: tuple[DrainageChannel, ...]
    platforms: tuple[ObservationPlatform, ...]

    def segment_map(self) -> Mapping[str, BuddhaSegment]:
        """Return a mapping from segment name to the corresponding object."""

        return {segment.name: segment for segment in self.segments}

    def total_height(self) -> float:
        """Return the combined height of all segments in metres."""

        return sum(segment.height_m for segment in self.segments)

    def total_surface_area(self) -> float:
        """Return the estimated surface area exposed to rainfall."""

        return sum(segment.surface_area() for segment in self.segments)

    def drainage_capacity(self) -> float:
        """Return the combined drainage capacity in litres per minute."""

        return sum(channel.capacity_l_per_min for channel in self.drainage_channels)

    def drainage_margin(self, rainfall_mm_per_hour: float) -> float:
        """Return the spare drainage capacity under a rainfall scenario.

        The rainfall is first converted to litres per minute using the exposed
        surface area of the statue (assuming one millimetre of rainfall over one
        square metre yields one litre of water).  The difference between the
        drainage capacity and the incoming volume indicates whether the system
        keeps the stone dry (positive margin) or is overwhelmed (negative
        margin).
        """

        if rainfall_mm_per_hour < 0:
            raise ValueError("rainfall_mm_per_hour must be non-negative")

        rainfall_l_per_hour = rainfall_mm_per_hour * self.total_surface_area()
        rainfall_l_per_minute = rainfall_l_per_hour / 60.0
        return self.drainage_capacity() - rainfall_l_per_minute

    def pilgrim_sequence(self) -> tuple[str, ...]:
        """Return platform names ordered by elevation then proximity."""

        ordered = sorted(
            self.platforms,
            key=lambda platform: (platform.elevation_m, platform.distance_from_face_m),
        )
        return tuple(platform.name for platform in ordered)

    def describe(self) -> dict[str, object]:
        """Return a serialisable snapshot of the statue."""

        return {
            "scale": self.scale,
            "total_height": round(self.total_height(), 2),
            "segments": [
                {
                    "name": segment.name,
                    "height_m": round(segment.height_m, 2),
                    "width_m": round(segment.width_m, 2),
                    "slope_deg": round(segment.slope_deg, 1),
                    "features": list(segment.features),
                }
                for segment in self.segments
            ],
            "drainage_channels": [
                {
                    "name": channel.name,
                    "capacity_l_per_min": round(channel.capacity_l_per_min, 1),
                    "connected_segments": list(channel.connected_segments),
                }
                for channel in self.drainage_channels
            ],
            "platform_sequence": list(self.pilgrim_sequence()),
        }


_BASE_SEGMENTS: tuple[tuple[str, float, float, float, float, tuple[str, ...]], ...] = (
    (
        "lotus_pedestal",
        8.6,
        28.0,
        6.0,
        0.95,
        ("莲花台瓣", "岷江洪水缓冲"),
    ),
    (
        "feet",
        6.7,
        8.5,
        12.0,
        1.05,
        ("十趾并列", "脚背排水孔"),
    ),
    (
        "knees",
        12.8,
        18.0,
        14.0,
        1.1,
        ("盘腿坐姿", "膝上凹槽"),
    ),
    (
        "torso",
        24.5,
        17.5,
        10.5,
        1.15,
        ("袈裟褶皱", "胸前暗渠"),
    ),
    (
        "hands",
        8.3,
        6.0,
        18.0,
        1.08,
        ("掌心向上", "掌心导流"),
    ),
    (
        "head",
        14.7,
        10.2,
        22.0,
        1.25,
        ("螺髻", "耳洞隐渠"),
    ),
)

_BASE_DRAINAGE: tuple[tuple[str, float, tuple[str, ...]], ...] = (
    ("耳洞暗渠", 4200.0, ("head", "torso")),
    ("胸前泄水", 5100.0, ("torso", "hands")),
    ("膝后瀑口", 4800.0, ("knees", "feet")),
    ("莲花暗沟", 3600.0, ("lotus_pedestal", "feet")),
)

_BASE_PLATFORMS: tuple[tuple[str, float, float, str], ...] = (
    ("凌云栈道", 12.0, 4.5, "head"),
    ("胸口观景台", 31.0, 7.0, "torso"),
    ("膝前栈桥", 22.0, 5.8, "knees"),
    ("大佛脚下", 3.5, 2.2, "feet"),
)


def _build_segments(scale: float) -> tuple[BuddhaSegment, ...]:
    segments: list[BuddhaSegment] = []
    for name, height, width, slope, relief_factor, features in _BASE_SEGMENTS:
        segments.append(
            BuddhaSegment(
                name=name,
                height_m=height * scale,
                width_m=width * scale,
                slope_deg=slope,
                relief_factor=relief_factor,
                features=features,
            )
        )
    return tuple(segments)


def _build_channels() -> tuple[DrainageChannel, ...]:
    return tuple(
        DrainageChannel(name=name, capacity_l_per_min=capacity, connected_segments=segments)
        for name, capacity, segments in _BASE_DRAINAGE
    )


def _build_platforms(scale: float) -> tuple[ObservationPlatform, ...]:
    # Elevations scale with the statue while horizontal distance remains fixed
    # because the cliff wall and river have stable spacing.
    return tuple(
        ObservationPlatform(
            name=name,
            elevation_m=elevation * scale,
            distance_from_face_m=distance,
            focus_segment=focus,
        )
        for name, elevation, distance, focus in _BASE_PLATFORMS
    )


def build_leshan_buddha(*, scale: float = 1.0) -> LeshanBuddhaModel:
    """Construct a :class:`LeshanBuddhaModel`.

    Parameters
    ----------
    scale:
        Uniform scaling factor applied to the statue dimensions.  ``1.0`` matches
        the canonical measurements (roughly seventy-one metres tall).  Values
        must be strictly positive.
    """

    if scale <= 0:
        raise ValueError("scale must be strictly positive")

    segments = _build_segments(scale)
    channels = _build_channels()
    platforms = _build_platforms(scale)
    return LeshanBuddhaModel(
        scale=scale,
        segments=segments,
        drainage_channels=channels,
        platforms=platforms,
    )


def iter_segment_features(model: LeshanBuddhaModel) -> Iterable[tuple[str, str]]:
    """Yield ``(segment_name, feature)`` pairs for catalogue indexing."""

    for segment in model.segments:
        for feature in segment.features:
            yield segment.name, feature

