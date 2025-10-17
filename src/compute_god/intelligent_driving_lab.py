"""Interactive blueprint for the Intelligent Driving Lab demo site.

This module rebuilds the public "Intelligent Driving Lab" microsite inside the
Compute‑God universe.  The original page (``miuchan.github.io``) showcases how
an autonomous driving team structures its stack, from perception and data
operations to simulation and deployment.  The code below distils those ideas
into explicit data models that other modules can query or remix.

The focus is on storytelling rather than heavy simulation: a concrete
``IntelligentDrivingLab`` data object provides a hero banner, highlighted
capabilities, representative scenarios and the underlying toolchain modules.
Helper utilities answer common questions—such as "which capabilities require a
LiDAR pipeline?"—while maintaining deterministic, easily testable behaviour.

The module intentionally emphasises readable, declarative structures so that a
future UI renderer can serialise the same information back into HTML blocks or
CLI tables without re-inventing the data layout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple


@dataclass(frozen=True)
class DrivingCapability:
    """A core ability demonstrated inside the lab."""

    name: str
    description: str
    sensors: Tuple[str, ...]
    metrics: Tuple[str, ...]
    maturity: str


@dataclass(frozen=True)
class DrivingScenario:
    """Real-world inspired episodes used to ground discussions."""

    slug: str
    title: str
    environment: str
    challenge: str
    capabilities: Tuple[str, ...]
    evaluation: Tuple[str, ...]


@dataclass(frozen=True)
class InteractionModule:
    """One interactive widget or workflow from the original demo site."""

    name: str
    goal: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    highlight: str


@dataclass(frozen=True)
class LabSection:
    """A themed block that groups multiple interaction modules."""

    title: str
    description: str
    modules: Tuple[InteractionModule, ...]


@dataclass(frozen=True)
class IntelligentDrivingLab:
    """Aggregate representation of the whole lab."""

    hero_title: str
    hero_subtitle: str
    call_to_action: str
    tagline: str
    capabilities: Tuple[DrivingCapability, ...]
    scenarios: Tuple[DrivingScenario, ...]
    sections: Tuple[LabSection, ...]

    def capability_index(self) -> Mapping[str, DrivingCapability]:
        """Return a quick lookup table for capabilities by name."""

        return {capability.name: capability for capability in self.capabilities}


def _default_capabilities() -> Tuple[DrivingCapability, ...]:
    return (
        DrivingCapability(
            name="Perception Fusion",
            description="Fuse LiDAR, radar and camera feeds into a 3D occupancy grid",
            sensors=("LiDAR", "Millimetre-wave radar", "Stereo camera"),
            metrics=("mAP", "BEV IoU", "Latency"),
            maturity="Production",
        ),
        DrivingCapability(
            name="Prediction & Behaviour",
            description="Model agent trajectories and intent-aware interaction fields",
            sensors=("Historical tracks", "Scene semantics"),
            metrics=("ADE", "FDE", "Collision rate"),
            maturity="Beta",
        ),
        DrivingCapability(
            name="Planning & Control",
            description="Optimise comfortable yet assertive paths under uncertainty",
            sensors=("Planner state", "Traffic rules"),
            metrics=("Jerk", "Regret", "Rule violations"),
            maturity="Pilot",
        ),
        DrivingCapability(
            name="Data Engine",
            description="Continuous data mining, labelling and regression triage",
            sensors=("Drive logs", "Edge feedback"),
            metrics=("Hours processed", "Label SLA", "Safety incidents"),
            maturity="Production",
        ),
        DrivingCapability(
            name="Simulation Lab",
            description="Scenario templating, differentiable sensors and digital twins",
            sensors=("HD maps", "Procedural traffic"),
            metrics=("Scenario coverage", "Sim-to-real gap"),
            maturity="Research",
        ),
    )


def _default_scenarios() -> Tuple[DrivingScenario, ...]:
    return (
        DrivingScenario(
            slug="beijing-night-market",
            title="Beijing Night Market",
            environment="Dense urban core",
            challenge="Vulnerable road users weaving across poorly lit junctions",
            capabilities=("Perception Fusion", "Planning & Control", "Prediction & Behaviour"),
            evaluation=("Night-time recall", "Emergency braking response"),
        ),
        DrivingScenario(
            slug="chengdu-ring-road",
            title="Chengdu Ring Road",
            environment="High-speed expressway",
            challenge="Rain-soaked asphalt and aggressive lane changes from human drivers",
            capabilities=("Perception Fusion", "Planning & Control"),
            evaluation=("Lane keeping", "Trajectory smoothness"),
        ),
        DrivingScenario(
            slug="shenzhen-last-mile",
            title="Shenzhen Last Mile",
            environment="Industrial park campus",
            challenge="Coordinating low-speed delivery pods with crosswalk etiquette",
            capabilities=("Prediction & Behaviour", "Data Engine", "Simulation Lab"),
            evaluation=("Right-of-way compliance", "Fleet turnaround time"),
        ),
    )


def _default_sections() -> Tuple[LabSection, ...]:
    return (
        LabSection(
            title="Perception Playground",
            description="Interact with fused sensor timelines and evaluate model deltas",
            modules=(
                InteractionModule(
                    name="Sensor Stacking",
                    goal="Toggle LiDAR, radar and camera layers to inspect occlusions",
                    inputs=("LiDAR point clouds", "Synchronized video"),
                    outputs=("Annotated BEV map", "Occlusion heatmap"),
                    highlight="Mirrors the hero section where users scrub through time",
                ),
                InteractionModule(
                    name="Auto-regress Replayer",
                    goal="Replay perception regressions sourced from the data engine",
                    inputs=("Regression queue", "Label snapshots"),
                    outputs=("Issue timeline", "Suggested fixes"),
                    highlight="Lets visitors triage real production bugs like in the demo",
                ),
            ),
        ),
        LabSection(
            title="Decision Theatre",
            description="Showcase prediction and planning hand-offs with editable intents",
            modules=(
                InteractionModule(
                    name="Interactive Intent Canvas",
                    goal="Drag and stretch predicted intention cones for dynamic agents",
                    inputs=("Agent history", "Scene layers"),
                    outputs=("Updated trajectory bundle", "Risk envelopes"),
                    highlight="Replicates the intent drawing widget from the web demo",
                ),
                InteractionModule(
                    name="Comfort Budget Slider",
                    goal="Tune smoothness versus assertiveness and watch control surfaces",
                    inputs=("Planner knobs", "Vehicle dynamics"),
                    outputs=("Control trace", "Passenger comfort score"),
                    highlight="Demonstrates the page's interactive slider component",
                ),
            ),
        ),
        LabSection(
            title="Ops & Simulation",
            description="Explain how the data engine closes the loop with simulated twins",
            modules=(
                InteractionModule(
                    name="Scenario Composer",
                    goal="Instantiate corner cases from HD maps and traffic templates",
                    inputs=("HD map tiles", "Traffic blueprint"),
                    outputs=("Scenario manifest", "Synthetic sensor feeds"),
                    highlight="Matches the demo's build-your-own-scenario stepper",
                ),
                InteractionModule(
                    name="Continuous Evaluation",
                    goal="Monitor KPI dashboards combining real and simulated drives",
                    inputs=("Fleet metrics", "Simulation sweeps"),
                    outputs=("Unified scorecard", "Regression alarms"),
                    highlight="Complements the final operations dashboard from the site",
                ),
            ),
        ),
    )


def build_intelligent_driving_lab() -> IntelligentDrivingLab:
    """Create the canonical Intelligent Driving Lab structure."""

    return IntelligentDrivingLab(
        hero_title="Intelligent Driving Lab",
        hero_subtitle="Shaping autonomous mobility with simulation-first workflows",
        call_to_action="Explore the stack",
        tagline="Perception · Prediction · Planning · Ops",
        capabilities=_default_capabilities(),
        scenarios=_default_scenarios(),
        sections=_default_sections(),
    )


def find_capabilities_with_sensor(
    lab: IntelligentDrivingLab, sensor_keyword: str
) -> Tuple[DrivingCapability, ...]:
    """Return all capabilities that rely on ``sensor_keyword`` (case-insensitive)."""

    keyword = sensor_keyword.lower()
    return tuple(
        capability
        for capability in lab.capabilities
        if any(keyword in sensor.lower() for sensor in capability.sensors)
    )


def scenarios_covering_capability(
    lab: IntelligentDrivingLab, capability_name: str
) -> Tuple[DrivingScenario, ...]:
    """List the scenarios that highlight ``capability_name``."""

    return tuple(
        scenario
        for scenario in lab.scenarios
        if capability_name in scenario.capabilities
    )


def lab_summary_table(lab: IntelligentDrivingLab) -> Tuple[Mapping[str, str], ...]:
    """Render a compact summary suitable for CLI or Markdown tables."""

    rows = []
    for scenario in lab.scenarios:
        rows.append(
            {
                "Scenario": scenario.title,
                "Environment": scenario.environment,
                "Focus": ", ".join(scenario.capabilities),
                "Evaluation": ", ".join(scenario.evaluation),
            }
        )
    return tuple(rows)


def iter_module_highlights(lab: IntelligentDrivingLab) -> Iterable[str]:
    """Yield descriptive highlight sentences for every interaction module."""

    for section in lab.sections:
        for module in section.modules:
            yield module.highlight


__all__ = [
    "DrivingCapability",
    "DrivingScenario",
    "InteractionModule",
    "IntelligentDrivingLab",
    "LabSection",
    "build_intelligent_driving_lab",
    "find_capabilities_with_sensor",
    "iter_module_highlights",
    "lab_summary_table",
    "scenarios_covering_capability",
]

