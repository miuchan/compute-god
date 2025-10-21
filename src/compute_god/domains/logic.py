"""Logical helpers affectionately referred to as :class:`非子` and :class:`欧子`.

The project enjoys giving its utilities whimsical nicknames and the logical
operators introduced here continue that tradition.  ``Feizi`` encapsulates the
idea of logical negation applied to an arbitrary predicate over universe
states.  ``Ouzi`` complements it by modelling a disjunction across multiple
predicates.  Both helpers keep lightweight histories so that downstream code
can inspect how the evaluations evolved over time without having to juggle
additional bookkeeping.

The goal is not to provide a fully fledged propositional calculus but rather a
pair of ergonomic building blocks that can be composed with the existing
observers and fixpoint machinery.  They are particularly handy when callers
need to express simple guards or convergence criteria that mix negated
conditions and disjunctive checks while still wanting insight into which
branch fired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, log
from typing import Callable, List, MutableMapping, Optional, Sequence, Tuple

State = MutableMapping[str, object]
Predicate = Callable[[State], bool]


@dataclass
class Feizi:
    """Negate a predicate over universe states while keeping evaluation history.

    Parameters
    ----------
    predicate:
        Callable receiving a state and returning ``True`` when the condition it
        represents holds.  ``Feizi`` will negate that result so callers can work
        with the logical complement without having to wrap the predicate
        themselves.
    """

    predicate: Predicate
    history: List[Tuple[State, bool]] = field(default_factory=list, init=False)

    def evaluate(self, state: State, /) -> bool:
        """Return the negated value of ``predicate`` for ``state``.

        A defensive copy of ``state`` is stored alongside the result so that the
        history remains stable even if the caller mutates the original mapping
        after evaluation.
        """

        snapshot = dict(state)
        result = not bool(self.predicate(snapshot))
        self.history.append((snapshot, result))
        return result

    __call__ = evaluate

    def last_result(self) -> Optional[bool]:
        """Return the most recent negated result, if any."""

        if not self.history:
            return None
        return self.history[-1][1]

    def contradictions(self) -> List[State]:
        """Return snapshots where the underlying predicate evaluated to ``False``."""

        return [dict(snapshot) for snapshot, negated in self.history if negated]


@dataclass
class Ouzi:
    """Disjunction helper that reports how multiple predicates evaluated.

    Parameters
    ----------
    predicates:
        Sequence of callables to evaluate for each observed state.  The
        instance records the boolean value of every predicate together with the
        resulting disjunction so callers can later reason about which branch
        provided support.
    """

    predicates: Sequence[Predicate]
    history: List[Tuple[State, Tuple[bool, ...], bool]] = field(
        default_factory=list, init=False
    )

    def __post_init__(self) -> None:
        self.predicates = tuple(self.predicates)
        if not self.predicates:
            raise ValueError("Ouzi requires at least one predicate")

    def evaluate(self, state: State, /) -> bool:
        """Return whether any predicate holds for ``state``."""

        snapshot = dict(state)
        evaluations = tuple(bool(predicate(snapshot)) for predicate in self.predicates)
        result = any(evaluations)
        self.history.append((snapshot, evaluations, result))
        return result

    __call__ = evaluate

    def last_result(self) -> Optional[bool]:
        """Return the boolean value of the most recent disjunction."""

        if not self.history:
            return None
        return self.history[-1][2]

    def last_truths(self) -> Optional[Tuple[bool, ...]]:
        """Return the individual predicate values from the latest evaluation."""

        if not self.history:
            return None
        return self.history[-1][1]

    def supporting_indices(self) -> Optional[Tuple[int, ...]]:
        """Return indices of predicates that evaluated to ``True`` most recently."""

        truths = self.last_truths()
        if truths is None:
            return None
        return tuple(index for index, value in enumerate(truths) if value)


@dataclass
class Ruofei:
    """Branching helper expressing the idiom "若非" (roughly "if not").

    ``Ruofei`` pairs a *predicate* with an optional *alternative* predicate.  When
    evaluated it first checks the primary predicate; if it holds the result is
    ``True`` and the alternative is skipped.  Otherwise the alternative is
    consulted (if supplied) and its boolean value becomes the result.  Every
    evaluation is recorded so callers can inspect which branch executed.
    """

    predicate: Predicate
    alternative: Optional[Predicate] = None
    history: List[Tuple[State, bool, Optional[bool], bool, str]] = field(
        default_factory=list, init=False
    )
    _branch_counter: int = field(default=2, init=False, repr=False)
    _branch_weight: float = field(
        default=log(0.7 / 0.3), init=False, repr=False
    )  # weakly favour predicate
    _learning_rate: float = field(default=1.0, init=False, repr=False)

    def evaluate(self, state: State, /) -> bool:
        """Evaluate the predicate and optional alternative for ``state``.

        The method stores a defensive copy of ``state`` alongside the boolean
        results so that callers can safely introspect past evaluations even if
        the original mapping is mutated later.
        """

        snapshot = dict(state)
        predicate_value = bool(self.predicate(snapshot))
        alternative_value: Optional[bool] = None
        if predicate_value:
            result = True
            branch = "predicate"
        else:
            if self.alternative is None:
                result = False
                branch = "predicate"
            else:
                alternative_value = bool(self.alternative(snapshot))
                result = alternative_value
                branch = "alternative"
        self.history.append(
            (snapshot, predicate_value, alternative_value, result, branch)
        )
        self._update_branch_counter(branch)
        return result

    __call__ = evaluate

    def last_result(self) -> Optional[bool]:
        """Return the most recent boolean result, if any."""

        if not self.history:
            return None
        return self.history[-1][3]

    def last_branch(self) -> Optional[str]:
        """Return the branch (``"predicate"`` or ``"alternative"``) used last."""

        if not self.history:
            return None
        return self.history[-1][4]

    def last_alternative_result(self) -> Optional[bool]:
        """Return the alternative predicate result from the latest evaluation."""

        if not self.history:
            return None
        return self.history[-1][2]

    def alternative_invocations(self) -> List[State]:
        """Return snapshots where the alternative predicate was evaluated."""

        return [
            dict(snapshot)
            for snapshot, _pred, alt, _result, branch in self.history
            if branch == "alternative" and alt is not None
        ]

    def predict_branch(self) -> str:
        """Predict which branch is likely to execute next.

        ``Ruofei`` models its branch predictor as a single-parameter logistic
        regression that is trained online using convex optimisation.  Each
        branch evaluation produces a binary label (``1`` for the predicate
        branch, ``0`` for the alternative).  The logistic loss is convex with
        respect to the weight, so a simple gradient descent step refines the
        predictor after every evaluation.  The predicted branch corresponds to
        whichever side currently has probability at least 50 percent.
        """

        return "predicate" if self._branch_probability() >= 0.5 else "alternative"

    def branch_probability(self) -> float:
        """Return the logistic probability of the predicate branch.

        Values above ``0.5`` indicate that the predictor currently favours the
        predicate branch.  The probability is derived from the internal weight
        trained via convex optimisation and therefore reflects the entire
        evaluation history in a smooth manner.
        """

        return self._branch_probability()

    def _update_branch_counter(self, branch: str) -> None:
        outcome = 1.0 if branch == "predicate" else 0.0
        probability = self._branch_probability()
        gradient = probability - outcome
        self._branch_weight -= self._learning_rate * gradient

        # Project the probabilistic predictor onto the historical two-bit
        # counter so existing introspection behaviour remains stable.
        updated_probability = self._branch_probability()
        scaled = int(round(updated_probability * 3))
        self._branch_counter = min(3, max(0, scaled))

    def _branch_probability(self) -> float:
        return 1.0 / (1.0 + exp(-self._branch_weight))


# Chinese aliases embracing the playful API surface.
非子 = Feizi
欧子 = Ouzi
若非 = Ruofei


__all__ = [
    "Feizi",
    "Ouzi",
    "Ruofei",
    "非子",
    "欧子",
    "若非",
]

