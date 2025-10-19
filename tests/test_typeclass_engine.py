"""Regression tests for the type class runtime."""

from __future__ import annotations

import pytest

from compute_god.core import (
    ClassConstraint,
    ConstraintSolver,
    ConstraintTemplate,
    InstanceResolutionError,
    MetaVar,
    ObservationalEquality,
    Sort,
    TypeClass,
    TypeClassEnvironment,
    TypeClassField,
    TypeClassInstance,
    TypeExpr,
    TypeVar,
    cast,
)


def _eq_type_class() -> TypeClass:
    element = TypeVar("A")

    def _eq_field_law(dictionary, _equality):
        if "eq" not in dictionary or not callable(dictionary["eq"]):
            raise ValueError("Eq dictionary must expose a callable 'eq' field")

    return TypeClass(
        name="Eq",
        parameter=element,
        fields=(TypeClassField("eq", "A → A → Bool", sort=Sort.OMEGA),),
        laws=(_eq_field_law,),
    )


def _register_eq_instances(environment: TypeClassEnvironment, eq_class: TypeClass) -> None:
    element = eq_class.parameter

    int_instance = TypeClassInstance(
        name="EqInt",
        head=TypeExpr("Int"),
        builder=lambda prereqs, _subst, _eq: {"eq": lambda x, y: x == y},
    )

    def list_builder(prereqs, _subst, _equality):
        element_dict = prereqs["element"]
        element_eq = element_dict["eq"]

        def eq_list(xs, ys):
            if len(xs) != len(ys):
                return False
            return all(element_eq(x, y) for x, y in zip(xs, ys))

        return {"eq": eq_list}

    list_instance = TypeClassInstance(
        name="EqList",
        head=TypeExpr("List", (element,)),
        builder=list_builder,
        prerequisites=(ConstraintTemplate(eq_class, element, "element"),),
    )

    environment.add_instance(eq_class, int_instance)
    environment.add_instance(eq_class, list_instance)


def test_typeclass_solver_resolves_nested_lists():
    eq_class = _eq_type_class()
    environment = TypeClassEnvironment()
    _register_eq_instances(environment, eq_class)

    solver = ConstraintSolver(environment)
    constraints = [
        ClassConstraint(eq_class, TypeExpr("Int"), MetaVar("eq_int")),
        ClassConstraint(eq_class, TypeExpr("List", (TypeExpr("Int"),)), MetaVar("eq_list_int")),
        ClassConstraint(
            eq_class,
            TypeExpr("List", (TypeExpr("List", (TypeExpr("Int"),)),)),
            MetaVar("eq_list_list_int"),
        ),
    ]

    solutions = solver.solve_all(constraints)

    eq_int = solutions["eq_int"]["eq"]
    assert eq_int(3, 3)
    assert not eq_int(2, 3)

    eq_list_int = solutions["eq_list_int"]["eq"]
    assert eq_list_int([1, 2], [1, 2])
    assert not eq_list_int([1, 2], [1, 3])

    eq_list_list_int = solutions["eq_list_list_int"]["eq"]
    assert eq_list_list_int([[1], [2]], [[1], [2]])
    assert not eq_list_list_int([[1], [3]], [[1], [2]])


def test_solver_raises_on_missing_instance():
    eq_class = _eq_type_class()
    environment = TypeClassEnvironment()
    _register_eq_instances(environment, eq_class)

    solver = ConstraintSolver(environment)
    constraint = ClassConstraint(eq_class, TypeExpr("Unknown"), MetaVar("eq_unknown"))

    with pytest.raises(InstanceResolutionError):
        solver.solve_all([constraint])


def test_observational_cast_respects_witness():
    equality = ObservationalEquality()
    term = TypeExpr("List", (TypeExpr("Int"),))

    value = [1, 2, 3]
    cast_value = cast(
        value,
        source=term,
        target=term,
        witness=lambda s, t: s == t,
        equality=equality,
    )
    assert cast_value is value

    with pytest.raises(ValueError):
        cast(
            value,
            source=term,
            target=TypeExpr("List", (TypeExpr("Bool"),)),
            witness=lambda _s, _t: False,
            equality=equality,
        )
