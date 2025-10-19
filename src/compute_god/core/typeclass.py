"""Type class and constraint solving infrastructure for the Compute-God core.

This module distils the requirements outlined in the observational type theory
literature (notably Pujet & Tabareau, López Juan, and Abel & Pientka) into a
practical Python implementation.  The goal is not to emulate the full
meta-theory, but to provide a faithful playground where we can experiment with
type-class-style dictionary passing, observational equality, and constraint
solving driven by higher-order unification.

The design mirrors the specification shared in the project brief:

* **Observational equality** governs casts and proof-irrelevant values.
* **Type classes as records** expose fields that live in the Ω layer.
* **Instance resolution** is implemented via a dynamic pattern unification
  routine inspired by López Juan (2020) and Abel & Pientka (2011).
* **Constraint solving** happens in a recursive loop that guarantees progress
  and keeps track of metavariables representing implicit dictionaries.

The abstractions provided here are intentionally lightweight; they allow other
modules (and test cases) to model type class behaviour without committing to a
full dependent type checker.  Nevertheless, the API enforces many of the
invariants that would exist in a dependently typed core language: law checking
via observational equality, occurs checks during unification, and predictable
metavariable resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union


# ---------------------------------------------------------------------------
# Sorts and observational equality
# ---------------------------------------------------------------------------


class Sort(str, Enum):
    """Universe levels supported by the observational equality model."""

    OMEGA = "Omega"
    UNIVERSE = "U"


class ObservationalEquality:
    """Implements the observational equality fragment.

    The Ω layer is proof-irrelevant – any two witnesses are observationally
    equal.  The 𝒰 layer relies on Python equality by default, but callers may
    provide custom normalisers to extend the comparison.
    """

    def __init__(self, *, normalisers: Optional[Mapping[Sort, Callable[[Any], Any]]] = None) -> None:
        self._normalisers: Dict[Sort, Callable[[Any], Any]] = {
            Sort.UNIVERSE: lambda value: value,
            Sort.OMEGA: lambda value: None,
        }
        if normalisers:
            self._normalisers.update(normalisers)

    def equivalent(self, left: Any, right: Any, *, sort: Sort = Sort.UNIVERSE) -> bool:
        """Return ``True`` when *left* and *right* are observationally equal."""

        normalise = self._normalisers.get(sort)
        if normalise is None:
            raise ValueError(f"No observational normaliser registered for sort {sort}")
        return normalise(left) == normalise(right)


def cast(value: Any, *, source: Any, target: Any, witness: Callable[[Any, Any], bool], equality: ObservationalEquality) -> Any:
    """Cast ``value`` from ``source`` to ``target`` when ``witness`` proves equality.

    The cast is observationally faithful: the *witness* must convince the
    equality oracle that ``source`` and ``target`` coincide.  When the witness
    succeeds the original ``value`` is returned; failures raise ``ValueError``.
    """

    if not witness(source, target):
        raise ValueError("Observational cast witness failed")
    if not equality.equivalent(source, target):
        raise ValueError("Observational equality rejected the cast")
    return value


# ---------------------------------------------------------------------------
# Type expressions and substitutions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypeVar:
    """A type variable used during instance declarations."""

    name: str

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        return self.name


@dataclass(frozen=True)
class TypeExpr:
    """A type constructor applied to zero or more arguments."""

    head: str
    args: Tuple["TypeTerm", ...] = field(default_factory=tuple)

    def map_args(self, fn: Callable[["TypeTerm"], "TypeTerm"]) -> "TypeExpr":
        return TypeExpr(self.head, tuple(fn(arg) for arg in self.args))

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        if not self.args:
            return self.head
        return f"{self.head}({' '.join(map(str, self.args))})"


TypeTerm = Union[TypeExpr, TypeVar]


def occurs_in(var: TypeVar, term: TypeTerm, substitution: "Substitution") -> bool:
    """Return ``True`` if *var* occurs in *term* under *substitution*."""

    term = substitution.apply(term)
    if isinstance(term, TypeVar):
        return term == var
    if isinstance(term, TypeExpr):
        return any(occurs_in(var, arg, substitution) for arg in term.args)
    return False


class UnificationError(Exception):
    """Raised when two type expressions cannot be unified."""


class Substitution:
    """A mutable substitution for type variables."""

    def __init__(self) -> None:
        self._mapping: Dict[TypeVar, TypeTerm] = {}

    def bind(self, var: TypeVar, term: TypeTerm) -> None:
        """Bind ``var`` to ``term`` ensuring the occurs check holds."""

        term = self.apply(term)
        if isinstance(term, TypeVar) and term == var:
            return
        if occurs_in(var, term, self):
            raise UnificationError(f"Occurs check failed for {var} in {term}")
        self._mapping[var] = term

    def apply(self, term: TypeTerm) -> TypeTerm:
        if isinstance(term, TypeVar) and term in self._mapping:
            return self.apply(self._mapping[term])
        if isinstance(term, TypeExpr):
            return term.map_args(self.apply)
        return term

    def merged(self) -> Dict[str, TypeTerm]:  # pragma: no cover - debugging helper
        return {var.name: self.apply(term) for var, term in self._mapping.items()}


def unify(left: TypeTerm, right: TypeTerm, substitution: Optional[Substitution] = None) -> Substitution:
    """Unify ``left`` and ``right`` returning the accumulated substitution."""

    subst = substitution or Substitution()
    left = subst.apply(left)
    right = subst.apply(right)

    if left == right:
        return subst

    if isinstance(left, TypeVar):
        subst.bind(left, right)
        return subst

    if isinstance(right, TypeVar):
        subst.bind(right, left)
        return subst

    if isinstance(left, TypeExpr) and isinstance(right, TypeExpr):
        if left.head != right.head or len(left.args) != len(right.args):
            raise UnificationError(f"Cannot unify {left} with {right}")
        for l_arg, r_arg in zip(left.args, right.args):
            subst = unify(l_arg, r_arg, subst)
        return subst

    raise UnificationError(f"Unsupported terms during unification: {left}, {right}")


# ---------------------------------------------------------------------------
# Type classes and instances
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypeClassField:
    """Metadata describing a field inside a type class dictionary."""

    name: str
    field_type: Any
    sort: Sort = Sort.OMEGA


Law = Callable[[Mapping[str, Any], ObservationalEquality], None]


@dataclass
class TypeClass:
    """A type class represented as an Ω-layer record."""

    name: str
    parameter: TypeVar
    fields: Tuple[TypeClassField, ...]
    laws: Tuple[Law, ...] = ()

    def validate_dictionary(self, dictionary: Mapping[str, Any], equality: ObservationalEquality) -> None:
        missing = {field.name for field in self.fields} - set(dictionary)
        if missing:
            raise ValueError(f"Dictionary for {self.name} is missing fields: {sorted(missing)}")
        for law in self.laws:
            law(dictionary, equality)


@dataclass(frozen=True)
class MetaVar:
    """A metavariable representing an implicit dictionary."""

    name: str


@dataclass(frozen=True)
class ClassConstraint:
    """A pending type class constraint produced during elaboration."""

    type_class: TypeClass
    target: TypeTerm
    metavariable: MetaVar

    def key(self, substitution: Substitution) -> Tuple[str, str]:
        """Canonical key used for memoisation."""

        term = substitution.apply(self.target)
        return (self.type_class.name, repr(term))


@dataclass(frozen=True)
class ConstraintTemplate:
    """Template used to instantiate prerequisite constraints."""

    type_class: TypeClass
    target: TypeTerm
    hint: str

    def instantiate(self, substitution: Substitution, *, index: int) -> Tuple[ClassConstraint, str]:
        target = substitution.apply(self.target)
        metavariable = MetaVar(f"{self.hint}_{index}")
        return ClassConstraint(self.type_class, target, metavariable), self.hint


DictionaryBuilder = Callable[[Mapping[str, Mapping[str, Any]], Substitution, ObservationalEquality], Mapping[str, Any]]


@dataclass
class TypeClassInstance:
    """A concrete inhabitant of a type class."""

    name: str
    head: TypeTerm
    builder: DictionaryBuilder
    prerequisites: Tuple[ConstraintTemplate, ...] = ()

    def instantiate(self, constraint: ClassConstraint) -> Tuple[Substitution, Tuple[Tuple[ClassConstraint, str], ...]]:
        substitution = unify(self.head, constraint.target)
        instantiated = tuple(
            template.instantiate(substitution, index=i)
            for i, template in enumerate(self.prerequisites, start=1)
        )
        return substitution, instantiated


class InstanceResolutionError(Exception):
    """Raised when a class constraint cannot be resolved."""


class TypeClassEnvironment:
    """Registry storing type classes and their instances."""

    def __init__(self, equality: Optional[ObservationalEquality] = None) -> None:
        self._instances: Dict[str, List[TypeClassInstance]] = {}
        self._equality = equality or ObservationalEquality()

    @property
    def equality(self) -> ObservationalEquality:
        return self._equality

    def add_instance(self, type_class: TypeClass, instance: TypeClassInstance) -> None:
        instances = self._instances.setdefault(type_class.name, [])
        instances.append(instance)

    def instances_for(self, type_class: TypeClass) -> Sequence[TypeClassInstance]:
        return tuple(self._instances.get(type_class.name, ()))


class ConstraintSolver:
    """Resolve class constraints through dynamic pattern unification."""

    def __init__(self, environment: TypeClassEnvironment) -> None:
        self._environment = environment
        self._memo: Dict[Tuple[str, str], Mapping[str, Any]] = {}

    def solve_all(self, constraints: Iterable[ClassConstraint]) -> Dict[str, Mapping[str, Any]]:
        solutions: Dict[str, Mapping[str, Any]] = {}
        for constraint in constraints:
            dictionary = self._solve_constraint(constraint, active=())
            solutions[constraint.metavariable.name] = dictionary
        return solutions

    def _solve_constraint(self, constraint: ClassConstraint, *, active: Tuple[Tuple[str, str], ...]) -> Mapping[str, Any]:
        substitution = Substitution()
        key = constraint.key(substitution)
        if key in self._memo:
            return self._memo[key]
        if key in active:
            raise InstanceResolutionError(
                f"Cycle detected while resolving {constraint.type_class.name} for {constraint.target}"
            )

        candidates = self._environment.instances_for(constraint.type_class)
        for instance in candidates:
            try:
                substitution, prerequisites = instance.instantiate(constraint)
            except UnificationError:
                continue

            prereq_solutions: Dict[str, Mapping[str, Any]] = {}
            for prereq_constraint, hint in prerequisites:
                solution = self._solve_constraint(
                    prereq_constraint,
                    active=active + (key,),
                )
                prereq_solutions[hint] = solution

            dictionary = instance.builder(prereq_solutions, substitution, self._environment.equality)
            constraint.type_class.validate_dictionary(dictionary, self._environment.equality)
            self._memo[key] = dictionary
            return dictionary

        raise InstanceResolutionError(
            f"No instance matches constraint {constraint.type_class.name} {constraint.target}"
        )


__all__ = [
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

