from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, MutableMapping, Optional, Protocol

State = MutableMapping[str, object]


class RuleContext(Protocol):
    """Protocol capturing the runtime context exposed to rules."""

    def steps(self) -> int:
        ...


ApplyFn = Callable[[State, RuleContext], State]
PredicateFn = Callable[[State, RuleContext], bool]


@dataclass(frozen=True)
class Rule:
    """A declarative state transition."""

    name: str
    apply: ApplyFn
    guard: Optional[PredicateFn] = None
    until: Optional[PredicateFn] = None
    priority: int = 0
    role: Optional[str] = None
    annotations: Dict[str, object] = field(default_factory=dict)

    def should_fire(self, state: State, ctx: RuleContext) -> bool:
        if self.guard is None:
            return True
        return bool(self.guard(state, ctx))

    def should_stop(self, state: State, ctx: RuleContext) -> bool:
        if self.until is None:
            return False
        return bool(self.until(state, ctx))


def rule(
    name: str,
    apply: Callable[[State], State] | ApplyFn,
    *,
    guard: Optional[PredicateFn] = None,
    until: Optional[PredicateFn] = None,
    priority: int = 0,
    role: Optional[str] = None,
    annotations: Optional[Dict[str, object]] = None,
) -> Rule:
    """Helper to lift a simple state transformer into a :class:`Rule`.

    The helper accepts an ``apply`` callable that may either take the raw state or
    the pair ``(state, ctx)``. When only ``state`` is expected a thin adapter is
    inserted.
    """

    if annotations is None:
        annotations = {}

    argcount = getattr(getattr(apply, "__code__", None), "co_argcount", None)
    if argcount == 1:
        simple_apply = apply  # type: ignore[assignment]

        def wrapped(state: State, _ctx: RuleContext) -> State:
            return simple_apply(state)

        apply_fn: ApplyFn = wrapped
    else:
        apply_fn = apply  # type: ignore[assignment]

    return Rule(
        name=name,
        apply=apply_fn,
        guard=guard,
        until=until,
        priority=priority,
        role=role,
        annotations=annotations,
    )
