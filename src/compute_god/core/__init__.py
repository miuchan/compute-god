"""Compute-God core runtime package."""

from .engine import FixpointEngine, FixpointResult, Metric, fixpoint, recursive_descent_fixpoint
from .observer import Observer, ObserverEvent, NoopObserver, combine_observers
from .rules import ApplyFn, PredicateFn, Rule, rule
from .typeclass import (
    ClassConstraint,
    ConstraintSolver,
    ConstraintTemplate,
    InstanceResolutionError,
    Law,
    MetaVar,
    ObservationalEquality,
    Sort,
    Substitution,
    TypeClass,
    TypeClassEnvironment,
    TypeClassField,
    TypeClassInstance,
    TypeExpr,
    TypeTerm,
    TypeVar,
    UnificationError,
    cast,
    unify,
)
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
    "recursive_descent_fixpoint",
    "rule",

    # Type class exports
    "ClassConstraint",
    "ConstraintSolver",
    "ConstraintTemplate",
    "InstanceResolutionError",
    "Law",
    "MetaVar",
    "ObservationalEquality",
    "Sort",
    "Substitution",
    "TypeClass",
    "TypeClassEnvironment",
    "TypeClassField",
    "TypeClassInstance",
    "TypeExpr",
    "TypeTerm",
    "TypeVar",
    "UnificationError",
    "cast",
    "unify",
]
