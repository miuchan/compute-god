import math

import pytest

from compute_god import guidance_desk
from compute_god.vulkan import (
    DescriptorBinding,
    DescriptorSetLayout,
    RenderAttachment,
    RenderPassBlueprint,
    ShaderStageSpec,
    VulkanDeviceProfile,
    VulkanValidationError,
    plan_vulkan_pipeline,
)


def _sample_device() -> VulkanDeviceProfile:
    return VulkanDeviceProfile(
        name="Compute-God GPU",
        shader_stage_throughput={
            "vertex": 200_000.0,
            "fragment": 180_000.0,
            "compute": 220_000.0,
            "default": 150_000.0,
        },
        max_descriptors_per_stage=8,
        max_total_descriptors=32,
        max_color_attachments=3,
        supports_depth=True,
    )


def test_plan_vulkan_pipeline_produces_plan_with_metrics() -> None:
    device = _sample_device()
    stages = [
        ShaderStageSpec("vertex", instructions=2_000, texture_reads=2),
        ShaderStageSpec("fragment", instructions=2_500, texture_reads=4, storage_reads=1),
    ]
    descriptor_sets = [
        DescriptorSetLayout(
            "frame-data",
            (
                DescriptorBinding(0, "uniform-buffer", stages=("vertex", "fragment")),
                DescriptorBinding(1, "sampled-image", count=2, stages=("fragment",)),
            ),
        ),
        DescriptorSetLayout(
            "material",
            (
                DescriptorBinding(0, "sampler", stages=("fragment",)),
            ),
        ),
    ]
    render_pass = RenderPassBlueprint(
        color_attachments=(RenderAttachment("swapchain", "bgra8", samples=1),),
        depth_attachment=RenderAttachment("depth", "d32", usage="depth"),
        subpasses=2,
    )

    plan = plan_vulkan_pipeline(device, stages, descriptor_sets, render_pass)

    assert plan.device is device
    assert plan.render_pass.subpasses == 2
    assert plan.descriptor_pressure["fragment"] > plan.descriptor_pressure["vertex"]
    assert plan.latency_budget > 0

    # Estimate frame time for a HD frame; the estimate should scale with resolution.
    frame_time_hd = plan.estimate_frame_time((1280, 720))
    frame_time_uhd = plan.estimate_frame_time((3840, 2160))

    assert frame_time_hd > 0
    assert frame_time_uhd > frame_time_hd
    assert math.isfinite(frame_time_uhd)


def test_plan_vulkan_pipeline_validates_descriptor_pressure() -> None:
    device = _sample_device()
    tight_device = VulkanDeviceProfile(
        name="Tiny Vulkan Device",
        shader_stage_throughput=device.shader_stage_throughput,
        max_descriptors_per_stage=1,
        max_total_descriptors=4,
        max_color_attachments=2,
        supports_depth=True,
    )

    stages = [ShaderStageSpec("fragment", instructions=1_000)]
    descriptor_sets = [
        DescriptorSetLayout(
            "over-subscribed",
            (
                DescriptorBinding(0, "uniform-buffer", count=2, stages=("fragment",)),
            ),
        )
    ]
    render_pass = RenderPassBlueprint(
        color_attachments=(RenderAttachment("swapchain", "bgra8"),),
    )

    with pytest.raises(VulkanValidationError):
        plan_vulkan_pipeline(tight_device, stages, descriptor_sets, render_pass)


def test_guidance_desk_lists_vulkan_entries() -> None:
    desk = guidance_desk()
    assert desk.has_entry("vulkan.plan_vulkan_pipeline")
