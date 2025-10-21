"""Earth Online AI council collaborative simulation.

The module materialises a governance-themed universe where an AI-led council
iteratively harmonises strategic axes such as coordination, sustainability, and
prosperity.  Each member contributes a set of preferred axis levels weighted by
their influence.  The :func:`simulate_ai_council` helper wires these
preferences into the fixed-point engine so the council reaches a consensus that
balances collective mandates with individual visions.

The dynamics are intentionally lightweight: targets stay within ``[0, 1]`` and
convergence is guaranteed because every update contracts the state towards a
stationary consensus target and dissent equilibrium.  History snapshots record
the full trajectory, making it straightforward to generate dashboards or
storytelling artefacts from the resulting trace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, MutableMapping, Sequence

from .core import FixpointResult, God, Metric, State, fixpoint, rule


CouncilSnapshot = Mapping[str, float]
MutableCouncilState = MutableMapping[str, float]


def _clamp(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    """Clamp ``value`` into the inclusive range ``[lower, upper]``."""

    return max(lower, min(upper, value))


@dataclass(frozen=True)
class CouncilMember:
    """Participant of the Earth Online AI council."""

    name: str
    influence: float
    priorities: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.influence <= 0:
            raise ValueError(f"influence must be positive, got {self.influence!r}")

    def preferences_for_axes(self, axes: Iterable[str], baseline: Mapping[str, float]) -> dict[str, float]:
        """Return member preferences for ``axes`` falling back to ``baseline``."""

        preferences: dict[str, float] = {}
        for axis in axes:
            value = self.priorities.get(axis, baseline[axis])
            preferences[axis] = _clamp(float(value))
        return preferences


@dataclass(frozen=True)
class CouncilMandate:
    """Shared configuration guiding the collaborative simulation."""

    axes: tuple[str, ...] = ("coordination", "sustainability", "prosperity")
    base_targets: Mapping[str, float] = field(
        default_factory=lambda: {
            "coordination": 0.88,
            "sustainability": 0.92,
            "prosperity": 0.86,
        }
    )
    consensus_bias: float = 0.7
    adaptation_rate: float = 0.3
    dissent_rate: float = 0.45
    history_keys: Iterable[str] = ("coordination", "sustainability", "prosperity", "dissent")

    def __post_init__(self) -> None:
        if not self.axes:
            raise ValueError("axes must contain at least one strategic dimension")

        for axis in self.axes:
            if axis not in self.base_targets:
                raise KeyError(f"base_targets missing axis {axis!r}")
            base_value = self.base_targets[axis]
            if not 0.0 <= float(base_value) <= 1.0:
                raise ValueError(f"base target for {axis!r} must lie in [0, 1]")

        if not 0.0 <= self.consensus_bias <= 1.0:
            raise ValueError("consensus_bias must lie within [0, 1]")
        if not 0.0 < self.adaptation_rate <= 1.0:
            raise ValueError("adaptation_rate must lie within (0, 1]")
        if not 0.0 < self.dissent_rate <= 1.0:
            raise ValueError("dissent_rate must lie within (0, 1]")

    def axes_tuple(self) -> tuple[str, ...]:
        return tuple(self.axes)

    def history_keys_tuple(self) -> tuple[str, ...]:
        keys = tuple(self.history_keys)
        if not keys:
            raise ValueError("history_keys must contain at least one entry")
        for key in keys:
            if key != "history" and key not in self.axes and key != "dissent":
                raise KeyError(f"history key {key!r} not tracked by council state")
        return keys

    def baseline_targets(self) -> dict[str, float]:
        return {axis: _clamp(float(self.base_targets[axis])) for axis in self.axes}


@dataclass(frozen=True)
class CouncilAgenda:
    """Initial alignment levels for the council axes."""

    axes: Mapping[str, float]
    dissent: float = 0.2

    def __post_init__(self) -> None:
        for value in self.axes.values():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError("agenda axis values must lie within [0, 1]")
        if not 0.0 <= self.dissent <= 1.0:
            raise ValueError("dissent must lie within [0, 1]")

    def as_state(self, axes: Iterable[str]) -> MutableCouncilState:
        state: MutableCouncilState = {}
        for axis in axes:
            if axis not in self.axes:
                raise KeyError(f"agenda missing axis {axis!r}")
            state[axis] = float(self.axes[axis])
        state["dissent"] = float(self.dissent)
        state["history"] = []
        return state


def _weighted_consensus_target(
    members: Sequence[CouncilMember], mandate: CouncilMandate
) -> dict[str, float]:
    axes = mandate.axes_tuple()
    baseline = mandate.baseline_targets()
    total_influence = sum(member.influence for member in members)
    if total_influence <= 0:
        raise ValueError("council requires members with positive influence")

    weighted: dict[str, float] = {axis: 0.0 for axis in axes}

    for member in members:
        preferences = member.preferences_for_axes(axes, baseline)
        for axis in axes:
            weighted[axis] += member.influence * preferences[axis]

    for axis in axes:
        member_target = weighted[axis] / total_influence
        baseline_target = baseline[axis]
        weighted[axis] = _clamp(
            (1.0 - mandate.consensus_bias) * baseline_target
            + mandate.consensus_bias * member_target
        )

    return weighted


def _update_dissent(
    current_dissent: float,
    next_axes: Mapping[str, float],
    members: Sequence[CouncilMember],
    mandate: CouncilMandate,
) -> float:
    axes = mandate.axes_tuple()
    baseline = mandate.baseline_targets()
    total_influence = sum(member.influence for member in members)
    if total_influence <= 0:
        return current_dissent

    aggregate_difference = 0.0
    for member in members:
        preferences = member.preferences_for_axes(axes, baseline)
        deviation = sum(abs(preferences[axis] - next_axes[axis]) for axis in axes) / len(axes)
        aggregate_difference += member.influence * deviation

    equilibrium = aggregate_difference / total_influence
    return (1.0 - mandate.dissent_rate) * current_dissent + mandate.dissent_rate * equilibrium


def council_transition(
    state: Mapping[str, object],
    members: Sequence[CouncilMember],
    mandate: CouncilMandate,
) -> MutableCouncilState:
    """Return the next council state under the collaborative mandate."""

    axes = mandate.axes_tuple()
    history = list(state.get("history", ()))
    consensus_target = _weighted_consensus_target(members, mandate)

    next_state: MutableCouncilState = {axis: float(state[axis]) for axis in axes}
    for axis in axes:
        current_value = float(state[axis])
        target_value = consensus_target[axis]
        updated = current_value + mandate.adaptation_rate * (target_value - current_value)
        next_state[axis] = _clamp(updated)

    current_dissent = float(state["dissent"])
    next_state["dissent"] = _clamp(
        _update_dissent(current_dissent, next_state, members, mandate)
    )

    keys = mandate.history_keys_tuple()
    history.append({key: next_state[key] for key in keys})
    next_state["history"] = history

    return next_state


def _council_metric(keys: Iterable[str]) -> Metric:
    keys = tuple(keys)

    def metric(previous: State, current: State) -> float:
        return max(abs(previous[key] - current[key]) for key in keys)

    return metric


def simulate_ai_council(
    agenda: CouncilAgenda,
    members: Sequence[CouncilMember],
    mandate: CouncilMandate | None = None,
    *,
    epsilon: float = 1e-6,
    max_epoch: int = 128,
) -> FixpointResult:
    """Run the Earth Online AI council until the collaborative plan stabilises."""

    if mandate is None:
        mandate = CouncilMandate()

    member_sequence = tuple(members)
    if not member_sequence:
        raise ValueError("simulate_ai_council requires at least one member")

    axes = mandate.axes_tuple()
    state = agenda.as_state(axes)

    keys = mandate.history_keys_tuple()
    initial_entry = {key: state[key] for key in keys}
    state["history"].append(initial_entry)

    universe = God.universe(
        state=state,
        rules=[rule("ai-council", lambda s, _ctx: council_transition(s, member_sequence, mandate))],
    )

    metric = _council_metric(keys)
    return fixpoint(universe, metric=metric, epsilon=epsilon, max_epoch=max_epoch)


__all__ = [
    "CouncilAgenda",
    "CouncilMandate",
    "CouncilMember",
    "council_transition",
    "simulate_ai_council",
]
