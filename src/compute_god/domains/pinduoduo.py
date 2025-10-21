"""Pinduoduo bargain automaton.

The real-world “砍一刀” (“cut a slice”) feature that popularised the Chinese
e-commerce platform Pinduoduo follows a recognisable automaton-like pattern.
Participants invite helpers who each remove a tiny portion of the remaining
price, but the contribution decays sharply once the bargain campaign is close to
completion.  This module provides a tiny deterministic simulator that mirrors
that behaviour so experiments can be carried out without calling the actual
service.

The :class:`PinduoduoBargainAutomaton` keeps track of the amount that still
needs to be shaved off and exposes two helpers:

``step``
    Apply a single helper action.  The automaton validates the helper type,
    derives the cut produced by that helper given the current stage of the
    bargain, and returns a :class:`BargainStep` snapshot.

``simulate``
    Drive the automaton through a sequence of helper activations until the
    bargain completes or the input sequence is exhausted.

The implementation is intentionally modest: instead of modelling every quirk of
the proprietary system it captures its signature traits (declining cuts and the
importance of new users) in a deterministic and well-documented manner.  This
makes it ideal for algorithmic prototyping, probability-free Monte Carlo
experiments, or teaching exercises about finite-state machines in modern
commerce.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Tuple


@dataclass(frozen=True)
class HelperProfile:
    """Describe how much a helper can cut from the bargain price.

    Parameters
    ----------
    min_cut:
        The minimum amount (in the same units as the target price) removed by a
        helper of this type at full enthusiasm.  Must be non-negative.
    max_cut:
        The maximum amount removed by a helper of this type at full enthusiasm.
        Must satisfy ``max_cut >= min_cut``.
    stage_multipliers:
        Optional scaling factors applied in the ``early``, ``middle``, and
        ``final`` phases of the bargain respectively.  When omitted the helper
        keeps its full strength during the entire run.
    """

    min_cut: float
    max_cut: float
    stage_multipliers: Tuple[float, float, float] | None = None

    def __post_init__(self) -> None:
        if self.min_cut < 0.0:
            raise ValueError("min_cut must be non-negative")
        if self.max_cut < self.min_cut:
            raise ValueError("max_cut must be greater than or equal to min_cut")
        if self.stage_multipliers is not None:
            if len(self.stage_multipliers) != 3:
                raise ValueError("stage_multipliers must contain three entries")
            for value in self.stage_multipliers:
                if value < 0.0:
                    raise ValueError("stage multipliers must be non-negative")

    def multiplier_for_stage(self, stage: str) -> float:
        """Return the scaling multiplier for a bargain stage."""

        if self.stage_multipliers is None:
            return 1.0
        index = {"early": 0, "middle": 1, "final": 2}[stage]
        return self.stage_multipliers[index]


@dataclass(frozen=True)
class BargainStep:
    """Snapshot produced after each helper activation."""

    helper_type: str
    cut_applied: float
    remaining: float
    stage: str


class PinduoduoBargainAutomaton:
    """Deterministic simulator of a Pinduoduo style bargain campaign."""

    #: Mapping from stage names to the ratio thresholds that delimit them.
    _STAGE_THRESHOLDS: Mapping[str, float] = {
        "early": 0.7,
        "middle": 0.3,
        "final": 0.0,
    }

    def __init__(
        self,
        target_amount: float,
        helper_profiles: Mapping[str, HelperProfile],
        *,
        enthusiasm_decay: float = 0.4,
    ) -> None:
        if target_amount <= 0.0:
            raise ValueError("target_amount must be positive")
        if not helper_profiles:
            raise ValueError("helper_profiles must not be empty")
        self._target = float(target_amount)
        self._remaining = float(target_amount)
        self._helper_profiles: Dict[str, HelperProfile] = dict(helper_profiles)
        self._enthusiasm_decay = float(enthusiasm_decay)
        if not 0.0 <= self._enthusiasm_decay <= 1.0:
            raise ValueError("enthusiasm_decay must lie in [0, 1]")

    @property
    def target_amount(self) -> float:
        """Total amount that needs to be cut to complete the bargain."""

        return self._target

    @property
    def remaining(self) -> float:
        """Current amount left to cut."""

        return self._remaining

    def reset(self) -> None:
        """Reset the automaton to its initial state."""

        self._remaining = self._target

    def stage(self) -> str:
        """Return the current stage of the bargain."""

        if self._remaining <= 0.0:
            return "complete"
        ratio = self._remaining / self._target
        for stage, threshold in self._STAGE_THRESHOLDS.items():
            if ratio >= threshold:
                return stage
        return "final"

    def _apply_helper(self, helper_type: str, *, enthusiasm: float) -> BargainStep:
        if self._remaining <= 0.0:
            raise RuntimeError("bargain already completed")
        if not 0.0 <= enthusiasm <= 1.0:
            raise ValueError("enthusiasm must lie in [0, 1]")
        try:
            profile = self._helper_profiles[helper_type]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise KeyError(f"unknown helper type: {helper_type!r}") from exc

        stage = self.stage()
        if stage == "complete":
            raise RuntimeError("bargain already completed")

        base_cut = profile.min_cut + enthusiasm * (profile.max_cut - profile.min_cut)
        cut = base_cut * profile.multiplier_for_stage(stage)

        # Cuts become less efficient as enthusiasm dissipates across helpers.
        cut *= 1.0 - (1.0 - enthusiasm) * self._enthusiasm_decay

        cut = min(cut, self._remaining)
        self._remaining -= cut

        next_stage = self.stage()
        return BargainStep(helper_type=helper_type, cut_applied=cut, remaining=self._remaining, stage=next_stage)

    def step(self, helper_type: str, *, enthusiasm: float = 1.0) -> BargainStep:
        """Apply a helper activation and return the resulting state."""

        return self._apply_helper(helper_type, enthusiasm=enthusiasm)

    def simulate(self, helpers: Iterable[str | Tuple[str, float]]) -> List[BargainStep]:
        """Run the automaton through a sequence of helpers.

        Each entry in ``helpers`` can either be a helper type string or a
        ``(helper_type, enthusiasm)`` tuple.  The sequence is truncated as soon as
        the bargain completes.
        """

        steps: List[BargainStep] = []
        for item in helpers:
            if isinstance(item, tuple):
                helper_type, enthusiasm = item
            else:
                helper_type, enthusiasm = item, 1.0
            step = self.step(helper_type, enthusiasm=enthusiasm)
            steps.append(step)
            if step.stage == "complete":
                break
        return steps


__all__ = [
    "BargainStep",
    "HelperProfile",
    "PinduoduoBargainAutomaton",
]

