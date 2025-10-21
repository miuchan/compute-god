"""Tests for the information energy gradient descent utilities."""

from __future__ import annotations

from compute_god import (
    DescentPath,
    DescentStep,
    EnergyDescentNavigator,
    EnergyField,
    plan_energy_descent,
)


def quadratic_potential(position: tuple[float, ...]) -> float:
    x, y = position
    return 0.5 * (x * x + y * y)


def quadratic_gradient(position: tuple[float, ...]) -> tuple[float, ...]:
    x, y = position
    return (x, y)


def test_energy_field_descends_to_origin() -> None:
    field = EnergyField(quadratic_potential, gradient=quadratic_gradient, energy_budget=5.0)
    navigator = EnergyDescentNavigator(field, step_size=0.8, damping=0.5, naturality=0.3)
    path = navigator.descend((2.0, -1.0), max_steps=32, tolerance=1e-5)

    assert isinstance(path, DescentPath)
    assert path.steps, "navigator should take at least one step"
    assert all(isinstance(step, DescentStep) for step in path.steps)

    energies = [quadratic_potential((2.0, -1.0))] + [step.energy for step in path.steps]
    assert energies == sorted(energies, reverse=True), "energy should monotonically decrease"

    final_position = path.steps[-1].position
    assert abs(final_position[0]) < 1e-2
    assert abs(final_position[1]) < 1e-2
    assert path.total_energy_drop > 0
    assert path.total_energy_drop <= 5.0
    assert path.total_distance > 0
    assert len(path.positions()) == len(path.steps)


def test_plan_energy_descent_wrapper() -> None:
    path = plan_energy_descent(
        quadratic_potential,
        (1.0, 1.0),
        gradient=quadratic_gradient,
        energy_budget=2.0,
        max_steps=16,
    )

    assert isinstance(path, DescentPath)
    assert path.total_energy_drop <= 2.0
    assert path.steps[0].energy < quadratic_potential((1.0, 1.0))
