"""Vulkan pipeline planning helpers for the Compute-God laboratory.

The goal of this module is not to reimplement the entire Vulkan API – that
would be an endless endeavour – but rather to provide a composable, declarative
model of a rendering pipeline that fits the Compute-God ethos.  The
abstractions are intentionally lightweight and focus on the ingredients that
matter when *planning* a pipeline: shader workloads, descriptor pressure and
render pass structure.

Three small data layers are modelled:

``ShaderStageSpec``
    Describes the instruction and resource footprint of an individual shader
    stage.  The specification is agnostic of how the shader was written; it only
    captures the characteristics that influence scheduling and device
    selection.

``DescriptorSetLayout``
    Simplified descriptor bookkeeping where each binding tracks its descriptor
    type, multiplicity and the shader stages that consume it.

``RenderPassBlueprint``
    Captures the shape of a render pass including colour/depth attachments and
    the desired number of subpasses.

Given those ingredients, :func:`plan_vulkan_pipeline` validates the blueprint
against a :class:`VulkanDeviceProfile` and returns a
:class:`VulkanPipelinePlan`.  The resulting plan exposes convenience metrics
such as descriptor pressure and an estimated latency budget which can then be
fed into higher-level orchestration scripts or optimisation loops.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Tuple

__all__ = [
    "DescriptorBinding",
    "DescriptorSetLayout",
    "RenderAttachment",
    "RenderPassBlueprint",
    "ShaderStageSpec",
    "VulkanDeviceProfile",
    "VulkanPipelinePlan",
    "VulkanValidationError",
    "plan_vulkan_pipeline",
]


class VulkanValidationError(ValueError):
    """Raised when a Vulkan blueprint violates device constraints."""


_VALID_SHADER_STAGES = {
    "vertex",
    "fragment",
    "compute",
    "geometry",
    "tess_control",
    "tess_eval",
}

_VALID_DESCRIPTOR_TYPES = {
    "uniform-buffer",
    "storage-buffer",
    "sampled-image",
    "storage-image",
    "sampler",
}


@dataclass
class ShaderStageSpec:
    """Declarative description of a shader stage workload."""

    stage: str
    instructions: int
    texture_reads: int = 0
    storage_reads: int = 0
    workgroup_size: Tuple[int, int, int] = (1, 1, 1)

    def __post_init__(self) -> None:
        self.stage = self.stage.lower()
        if self.stage not in _VALID_SHADER_STAGES:
            raise VulkanValidationError(f"unknown shader stage: {self.stage!r}")
        if self.instructions <= 0:
            raise VulkanValidationError("instructions must be positive")
        if self.texture_reads < 0 or self.storage_reads < 0:
            raise VulkanValidationError("resource reads must not be negative")
        if len(self.workgroup_size) != 3:
            raise VulkanValidationError("workgroup_size must be a 3-tuple")
        normalised: Tuple[int, int, int] = tuple(int(max(1, dim)) for dim in self.workgroup_size)  # type: ignore[assignment]
        self.workgroup_size = normalised


@dataclass(frozen=True)
class DescriptorBinding:
    """Representation of a descriptor binding inside a set layout."""

    binding: int
    descriptor_type: str
    count: int = 1
    stages: Tuple[str, ...] = ("vertex", "fragment")

    def __post_init__(self) -> None:
        if self.binding < 0:
            raise VulkanValidationError("binding index must be non-negative")
        if self.count <= 0:
            raise VulkanValidationError("descriptor count must be positive")
        descriptor_type = self.descriptor_type.lower()
        if descriptor_type not in _VALID_DESCRIPTOR_TYPES:
            raise VulkanValidationError(f"unsupported descriptor type: {self.descriptor_type!r}")
        object.__setattr__(self, "descriptor_type", descriptor_type)

        if not self.stages:
            raise VulkanValidationError("descriptor binding must target at least one stage")
        normalised_stages = tuple(sorted({stage.lower() for stage in self.stages}))
        for stage in normalised_stages:
            if stage not in _VALID_SHADER_STAGES:
                raise VulkanValidationError(f"descriptor binding references unknown stage: {stage!r}")
        object.__setattr__(self, "stages", normalised_stages)


@dataclass
class DescriptorSetLayout:
    """Descriptor set layout made of :class:`DescriptorBinding` entries."""

    name: str
    bindings: Sequence[DescriptorBinding] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise VulkanValidationError("descriptor set layout name must not be empty")
        self.bindings = tuple(self.bindings)
        seen_bindings = set()
        for binding in self.bindings:
            if binding.binding in seen_bindings:
                raise VulkanValidationError(
                    f"duplicate descriptor binding index {binding.binding} in set {self.name!r}"
                )
            seen_bindings.add(binding.binding)

    def descriptor_count(self) -> int:
        return sum(binding.count for binding in self.bindings)

    def descriptor_usage_by_stage(self) -> Mapping[str, int]:
        usage: Dict[str, int] = {}
        for binding in self.bindings:
            for stage in binding.stages:
                usage[stage] = usage.get(stage, 0) + binding.count
        return usage


@dataclass(frozen=True)
class RenderAttachment:
    """Simple representation of a render attachment."""

    name: str
    format: str
    samples: int = 1
    usage: str = "color"

    def __post_init__(self) -> None:
        if not self.name:
            raise VulkanValidationError("render attachment name must not be empty")
        if self.samples <= 0:
            raise VulkanValidationError("sample count must be positive")
        usage = self.usage.lower()
        if usage not in {"color", "depth"}:
            raise VulkanValidationError("attachment usage must be 'color' or 'depth'")
        object.__setattr__(self, "usage", usage)


@dataclass
class RenderPassBlueprint:
    """Declarative structure of a render pass."""

    color_attachments: Sequence[RenderAttachment] = ()
    depth_attachment: RenderAttachment | None = None
    subpasses: int = 1

    def __post_init__(self) -> None:
        if self.subpasses <= 0:
            raise VulkanValidationError("render pass must declare at least one subpass")
        self.color_attachments = tuple(self.color_attachments)
        for attachment in self.color_attachments:
            if attachment.usage != "color":
                raise VulkanValidationError("colour attachments must have usage='color'")
        if self.depth_attachment is not None and self.depth_attachment.usage != "depth":
            raise VulkanValidationError("depth attachment must have usage='depth'")


@dataclass(frozen=True)
class VulkanDeviceProfile:
    """Minimal device profile capturing relevant Vulkan limits."""

    name: str
    shader_stage_throughput: Mapping[str, float]
    max_descriptors_per_stage: int = 32
    max_total_descriptors: int = 128
    max_color_attachments: int = 4
    supports_depth: bool = True

    def throughput_for(self, stage: str) -> float:
        stage = stage.lower()
        throughput = self.shader_stage_throughput.get(stage)
        if throughput is None:
            throughput = self.shader_stage_throughput.get("default")
        if throughput is None or throughput <= 0:
            raise VulkanValidationError(
                f"device {self.name!r} does not provide throughput for stage {stage!r}"
            )
        return throughput


@dataclass
class VulkanPipelinePlan:
    """Result of :func:`plan_vulkan_pipeline` containing derived metrics."""

    device: VulkanDeviceProfile
    stages: Tuple[ShaderStageSpec, ...]
    descriptor_sets: Tuple[DescriptorSetLayout, ...]
    render_pass: RenderPassBlueprint
    descriptor_usage: Mapping[str, int]
    descriptor_pressure: Mapping[str, float]
    complexity: float
    latency_budget: float

    def estimate_frame_time(
        self,
        resolution: Tuple[int, int] = (1920, 1080),
        *,
        frame_overlap: float = 0.0,
    ) -> float:
        """Estimate the frame time (in arbitrary milliseconds) for the plan.

        The estimation scales the latency budget by the render resolution, the
        number of attachments and an overlap factor.  ``frame_overlap`` allows
        modelling scenarios where compute/graphics work overlaps between frames
        (values in ``[0, 1)`` reduce the final estimate).
        """

        width, height = resolution
        if width <= 0 or height <= 0:
            raise VulkanValidationError("resolution dimensions must be positive")
        overlap = max(0.0, min(frame_overlap, 0.9))

        pixel_count = float(width * height)
        shading_factor = 1.0 + 0.1 * len(self.render_pass.color_attachments)
        if self.render_pass.depth_attachment is not None:
            shading_factor += 0.05

        density = max(1.0, pixel_count / 1_000_000.0)
        return self.latency_budget * shading_factor * density * (1.0 - 0.5 * overlap)


def _normalise_stages(stages: Sequence[ShaderStageSpec]) -> Tuple[ShaderStageSpec, ...]:
    if not stages:
        raise VulkanValidationError("at least one shader stage is required to plan a pipeline")
    ordered: list[ShaderStageSpec] = []
    seen = set()
    for stage in stages:
        if stage.stage in seen:
            raise VulkanValidationError(f"duplicate shader stage {stage.stage!r} provided")
        seen.add(stage.stage)
        ordered.append(stage)
    return tuple(ordered)


def _aggregate_descriptor_usage(
    descriptor_sets: Sequence[DescriptorSetLayout],
) -> tuple[Tuple[DescriptorSetLayout, ...], Dict[str, int], int]:
    ordered_sets = tuple(descriptor_sets)
    usage: Dict[str, int] = {}
    total = 0
    for layout in ordered_sets:
        total += layout.descriptor_count()
        for stage, count in layout.descriptor_usage_by_stage().items():
            usage[stage] = usage.get(stage, 0) + count
    return ordered_sets, usage, total


def _compute_stage_latency(stage: ShaderStageSpec, device: VulkanDeviceProfile) -> float:
    throughput = device.throughput_for(stage.stage)
    stage_latency = stage.instructions / throughput
    stage_latency += 0.02 * stage.texture_reads
    stage_latency += 0.03 * stage.storage_reads
    if stage.stage == "compute":
        group_size = stage.workgroup_size[0] * stage.workgroup_size[1] * stage.workgroup_size[2]
        stage_latency *= min(group_size / 64.0, 4.0)
    return stage_latency


def plan_vulkan_pipeline(
    device: VulkanDeviceProfile,
    stages: Sequence[ShaderStageSpec],
    descriptor_sets: Sequence[DescriptorSetLayout],
    render_pass: RenderPassBlueprint,
) -> VulkanPipelinePlan:
    """Validate ``stages``/``descriptor_sets`` against ``device`` and build a plan."""

    ordered_stages = _normalise_stages(stages)
    ordered_sets, descriptor_usage, total_descriptors = _aggregate_descriptor_usage(descriptor_sets)

    if total_descriptors > device.max_total_descriptors:
        raise VulkanValidationError(
            f"descriptor usage {total_descriptors} exceeds device limit {device.max_total_descriptors}"
        )

    for stage in ordered_stages:
        count = descriptor_usage.get(stage.stage, 0)
        if count > device.max_descriptors_per_stage:
            raise VulkanValidationError(
                f"stage {stage.stage} uses {count} descriptors (limit {device.max_descriptors_per_stage})"
            )
        # Ensure the stage is supported by querying throughput.
        device.throughput_for(stage.stage)

    if len(render_pass.color_attachments) > device.max_color_attachments:
        raise VulkanValidationError(
            f"render pass requests {len(render_pass.color_attachments)} colour attachments "
            f"(limit {device.max_color_attachments})"
        )
    if render_pass.depth_attachment is not None and not device.supports_depth:
        raise VulkanValidationError("device does not support depth attachments")

    stage_latency = 0.0
    complexity = 0.0
    descriptor_pressure: Dict[str, float] = {}

    for stage in ordered_stages:
        stage_latency += _compute_stage_latency(stage, device)
        complexity += stage.instructions + 8.0 * stage.texture_reads + 12.0 * stage.storage_reads
        usage = descriptor_usage.get(stage.stage, 0)
        descriptor_pressure[stage.stage] = usage / float(device.max_descriptors_per_stage)

    attachment_complexity = sum(att.samples for att in render_pass.color_attachments)
    if render_pass.depth_attachment is not None:
        attachment_complexity += 1.5 * render_pass.depth_attachment.samples
    complexity += 42.0 * attachment_complexity

    latency_budget = stage_latency * (1.0 + 0.05 * max(0, render_pass.subpasses - 1))
    latency_budget += 0.1 * len(render_pass.color_attachments)

    return VulkanPipelinePlan(
        device=device,
        stages=ordered_stages,
        descriptor_sets=ordered_sets,
        render_pass=render_pass,
        descriptor_usage=dict(descriptor_usage),
        descriptor_pressure=descriptor_pressure,
        complexity=complexity,
        latency_budget=latency_budget,
    )

