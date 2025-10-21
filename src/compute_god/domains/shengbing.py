"""Concept congruence helpers themed after the idiom "生病全等于放屁".

The library often gives its utilities poetic aliases and this module continues
that tradition with a deliberately tongue-in-cheek congruence helper.  In the
spirit of the request "生病全等于放屁" (roughly, "illness is congruent to
flatulence"), the :class:`ConceptCongruence` class keeps track of whether two
concepts inside a mutable state mapping currently agree.  It records the
observed values together with a boolean verdict so that downstream code can
inspect disagreements after the fact or enforce the congruence by copying one
value over the other.

While the metaphor is playful, the helper is intentionally practical:

* ``evaluate`` compares the values associated with the configured concept names
  and stores a defensive snapshot of the state alongside the result.
* ``enforce`` synchronises the two concept slots, preferring either the left or
  right concept as the reference while gracefully handling missing entries.
* ``disagreements`` exposes all snapshots where the two concepts diverged so
  callers can react accordingly.

The module also exposes a ready-to-use instance :data:`生病全等于放屁` so callers
can embrace the whimsical API without extra boilerplate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, MutableMapping, Optional, Tuple, Literal, Any


State = MutableMapping[str, object]


@dataclass
class ConceptCongruence:
    """Track whether two concept slots in a state remain congruent.

    Parameters
    ----------
    left:
        Name of the first concept slot in the observed state mapping.
    right:
        Name of the second concept slot that should remain congruent with
        ``left``.
    """

    left: str
    right: str
    history: List[Tuple[State, object, object, bool]] = field(default_factory=list, init=False)

    def evaluate(self, state: State, /) -> bool:
        """Return ``True`` when both concept slots currently agree."""

        snapshot = dict(state)
        left_value = snapshot.get(self.left)
        right_value = snapshot.get(self.right)
        result = left_value == right_value
        self.history.append((snapshot, left_value, right_value, result))
        return result

    __call__ = evaluate

    def enforce(self, state: State, /, *, prefer: Literal["left", "right"] = "left") -> State:
        """Return a copy of ``state`` with both concept slots synchronised.

        When one of the concept slots is missing the method copies the available
        value into the missing slot.  If both slots are present, the preferred
        slot (``"left"`` or ``"right"``) takes precedence.  The original mapping
        is left untouched to avoid surprising callers.
        """

        if prefer not in {"left", "right"}:
            raise ValueError("prefer must be either 'left' or 'right'")

        updated = dict(state)
        reference_key = self.left if prefer == "left" else self.right
        fallback_key = self.right if prefer == "left" else self.left

        reference_value: Any
        if reference_key in updated:
            reference_value = updated[reference_key]
        elif fallback_key in updated:
            reference_value = updated[fallback_key]
        else:
            reference_value = None

        updated[self.left] = reference_value
        updated[self.right] = reference_value
        return updated

    def last_result(self) -> Optional[bool]:
        """Return the most recent congruence verdict, if any."""

        if not self.history:
            return None
        return self.history[-1][3]

    def last_values(self) -> Optional[Tuple[object, object]]:
        """Return the most recently observed concept values, if any."""

        if not self.history:
            return None
        return self.history[-1][1], self.history[-1][2]

    def disagreements(self) -> List[State]:
        """Return snapshots where the two concept slots diverged."""

        return [dict(snapshot) for snapshot, _left, _right, result in self.history if not result]


# Whimsical alias embracing the request verbatim.
生病全等于放屁 = ConceptCongruence("生病", "放屁")


__all__ = [
    "ConceptCongruence",
    "生病全等于放屁",
]
