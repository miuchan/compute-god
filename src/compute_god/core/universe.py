"""Universe definitions for Compute-God."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, MutableMapping, Optional, Sequence

from .observer import NoopObserver, Observer
from .rules import Rule
from .types import RuleContext, State


@dataclass(frozen=True)
class Universe:
    """Container for the state, rules and observers."""

    state: State
    rules: Sequence[Rule]
    observers: Sequence[Observer] = field(default_factory=lambda: (NoopObserver(),))

    def sorted_rules(self) -> List[Rule]:
        return sorted(self.rules, key=lambda r: r.priority, reverse=True)

    def rules_by_role(self, role: Optional[str]) -> List[Rule]:
        if role is None:
            return self.sorted_rules()
        return [rule for rule in self.sorted_rules() if rule.role == role]


class _RuleContextImpl:
    def __init__(self) -> None:
        self._steps = 0

    def increment(self) -> None:
        self._steps += 1

    def steps(self) -> int:
        return self._steps


class God:
    @staticmethod
    def universe(
        *,
        state: Optional[MutableMapping[str, object]] = None,
        rules: Optional[Iterable[Rule]] = None,
        observers: Optional[Iterable[Observer]] = None,
    ) -> Universe:
        if state is None:
            state = {}
        if rules is None:
            rules = []
        if observers is None:
            observers = (NoopObserver(),)
        return Universe(state=state, rules=tuple(rules), observers=tuple(observers))

    @staticmethod
    def rule_context() -> RuleContext:
        return _RuleContextImpl()


__all__ = ["God", "Universe"]
