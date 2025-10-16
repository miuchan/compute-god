"""Compute-God core runtime package."""

from .engine import FixpointEngine, FixpointResult, Metric, fixpoint
from .observer import Observer, ObserverEvent, NoopObserver, combine_observers
from .rules import ApplyFn, PredicateFn, Rule, rule
from .types import RuleContext, State
from .universe import God, Universe

__all__ = [
    "ApplyFn",
    "FixpointEngine",
    "FixpointResult",
    "God",
    "Metric",
    "NoopObserver",
    "Observer",
    "ObserverEvent",
    "PredicateFn",
    "Rule",
    "RuleContext",
    "State",
    "Universe",
    "combine_observers",
    "fixpoint",
    "rule",
]
