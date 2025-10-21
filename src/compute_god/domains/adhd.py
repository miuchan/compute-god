"""Attention dynamics helpers and a Coefficient of Engagement tracker.

This module introduces a light‑weight model that embraces the playful tone of
the project while still providing deterministic, well behaved utilities that
are straightforward to test.  ``ADHDProfile`` encodes how a hypothetical mind
reacts to structured stimuli, balancing a baseline focus with biases toward
novelty, structure and reward.  ``StimulusProfile`` instances describe the
environmental input and are automatically clamped to the ``[0, 1]`` interval so
callers can provide rough sketches without worrying about accidental
out-of-range values.

Each call to :meth:`ADHDProfile.respond` yields an :class:`ADHDResponse` that
captures focus, regulation and energy levels.  The averages of these metrics
form the *engagement* score which can be fed into
``CoefficientOfEngagement``—a small exponential moving average tracker able to
report short term trends and stability checks.

The goal is not to simulate neurology with fidelity but to offer ergonomic
building blocks for higher level experiments in the Compute-God universe.  The
implementation favours clarity, determinism and pleasant defaults so it can be
used in both tests and playful exploratory notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

__all__ = [
    "StimulusProfile",
    "ADHDResponse",
    "ADHDProfile",
    "CoefficientOfEngagement",
    "simulate_coe",
]


def _clamp(value: float, /, lower: float = 0.0, upper: float = 1.0) -> float:
    """Return ``value`` forced to lie inside ``[lower, upper]``."""

    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


@dataclass(frozen=True)
class StimulusProfile:
    """Description of environmental input received by an :class:`ADHDProfile`.

    Parameters
    ----------
    novelty:
        How surprising or stimulating the input is.  Values are clamped to the
        ``[0, 1]`` interval.
    structure:
        Degree of scaffolding or predictability offered by the input.  Also
        clamped to ``[0, 1]``.
    reward:
        Proxy for motivational value, such as immediate feedback or a tangible
        payoff.  Likewise clamped to ``[0, 1]``.
    duration:
        Relative exposure time.  Only non-negative values are accepted—the
        duration is forced to be at least zero so it can modulate the moving
        average weighting without introducing sign inversions.
    """

    novelty: float
    structure: float
    reward: float
    duration: float = 1.0

    def __post_init__(self) -> None:  # pragma: no cover - exercised indirectly
        object.__setattr__(self, "novelty", _clamp(float(self.novelty)))
        object.__setattr__(self, "structure", _clamp(float(self.structure)))
        object.__setattr__(self, "reward", _clamp(float(self.reward)))
        duration = float(self.duration)
        if duration < 0:
            duration = 0.0
        object.__setattr__(self, "duration", duration)


@dataclass
class ADHDResponse:
    """Outcome of a single :meth:`ADHDProfile.respond` invocation."""

    focus: float
    regulation: float
    energy: float
    engagement: float
    duration: float

    def as_tuple(self) -> Tuple[float, float, float, float, float]:
        """Return a convenient tuple representation."""

        return self.focus, self.regulation, self.energy, self.engagement, self.duration


@dataclass
class ADHDProfile:
    """Simple attention profile reacting deterministically to stimuli.

    The profile maintains a notion of the last computed focus level so it can
    exhibit inertia across successive calls to :meth:`respond`.  Each stimulus
    nudges the target focus based on the configured biases, and the
    ``variability`` parameter controls how quickly the internal state moves
    toward that target.
    """

    baseline_focus: float = 0.5
    novelty_bias: float = 0.6
    structure_bias: float = 0.4
    reward_bias: float = 0.5
    variability: float = 0.5
    _last_focus: Optional[float] = field(default=None, init=False, repr=False)

    def respond(self, stimulus: StimulusProfile, /) -> ADHDResponse:
        """Process ``stimulus`` and return the resulting attention metrics."""

        novelty_delta = stimulus.novelty - 0.5
        structure_delta = stimulus.structure - 0.5
        reward_delta = stimulus.reward - 0.5

        target_focus = _clamp(
            self.baseline_focus
            + self.novelty_bias * novelty_delta
            + self.structure_bias * structure_delta
            + self.reward_bias * reward_delta
        )

        if self._last_focus is None:
            focus = target_focus
        else:
            focus = _clamp(
                self._last_focus + self.variability * (target_focus - self._last_focus)
            )

        self._last_focus = focus

        regulation = _clamp(
            0.5
            + self.structure_bias * structure_delta
            - self.variability * novelty_delta
        )
        energy = _clamp(
            0.5
            + self.novelty_bias * novelty_delta
            + self.reward_bias * reward_delta
        )
        engagement = _clamp((focus + regulation + energy) / 3)

        return ADHDResponse(
            focus=focus,
            regulation=regulation,
            energy=energy,
            engagement=engagement,
            duration=stimulus.duration,
        )

    def reset(self) -> None:
        """Forget the stored focus level so the next response starts fresh."""

        self._last_focus = None


@dataclass
class CoefficientOfEngagement:
    """Track a smoothed engagement score over successive responses."""

    smoothing: float = 0.25
    value: Optional[float] = field(default=None, init=False)
    history: List[float] = field(default_factory=list, init=False)
    responses: List[ADHDResponse] = field(default_factory=list, init=False)

    def observe(self, response: ADHDResponse, /) -> float:
        """Ingest ``response`` and update the coefficient value."""

        alpha = _clamp(self.smoothing * max(response.duration, 0.0))

        if self.value is None:
            self.value = response.engagement
        else:
            self.value = (1 - alpha) * self.value + alpha * response.engagement

        self.history.append(self.value)
        self.responses.append(response)
        return self.value

    def trend(self, window: int = 3) -> float:
        """Return the average of the last ``window`` observations."""

        if window <= 0:
            raise ValueError("window must be positive")
        if len(self.history) < window:
            raise ValueError("not enough observations to compute trend")
        recent = self.history[-window:]
        return sum(recent) / len(recent)

    def is_stable(self, *, epsilon: float = 0.05, window: int = 3) -> bool:
        """Check if the coefficient has stabilised within ``epsilon``."""

        if window <= 1:
            raise ValueError("window must be greater than one")
        if len(self.history) < window:
            return False
        segment = self.history[-window:]
        return max(segment) - min(segment) <= epsilon

    def reset(self) -> None:
        """Clear stored observations and the current value."""

        self.value = None
        self.history.clear()
        self.responses.clear()


def simulate_coe(
    profile: ADHDProfile,
    stimuli: Iterable[StimulusProfile],
    *,
    smoothing: float = 0.25,
) -> Tuple[CoefficientOfEngagement, List[ADHDResponse]]:
    """Convenience helper to run ``profile`` over ``stimuli``.

    Parameters
    ----------
    profile:
        The attention profile used to respond to each stimulus.
    stimuli:
        Iterable of :class:`StimulusProfile` instances.  The iterable is
        consumed in order and each response is fed to the coefficient tracker.
    smoothing:
        Initial smoothing factor for the created
        :class:`CoefficientOfEngagement`.

    Returns
    -------
    tuple
        The created coefficient tracker alongside the list of produced
        responses.
    """

    tracker = CoefficientOfEngagement(smoothing=smoothing)
    responses: List[ADHDResponse] = []

    for stimulus in stimuli:
        response = profile.respond(stimulus)
        responses.append(response)
        tracker.observe(response)

    return tracker, responses

