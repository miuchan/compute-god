"""Simplified Factorio-style factory planning primitives.

The real game ships with a deep optimisation problem that mixes discrete
crafting recipes, production bonuses, and sprawling dependency graphs.
For the purposes of the Compute-God playground we model a light-weight
subset that is deterministic and easy to reason about in tests:

* ``Recipe`` captures the inputs, outputs, and base crafting time for one
  production cycle.
* ``FactoryStep`` binds a recipe to a number of machines (with optional
  speed bonuses) and provides helpers to calculate the effective crafting
  rate for that step.
* ``FactoryBlueprint`` aggregates steps and exposes a :meth:`balance`
  method that computes the overall throughput of every item alongside
  surplus/deficit reports.

The tiny abstraction is expressive enough to model common blueprints –
such as an early-game electronic circuit build – while keeping the API
approachable for educational simulations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, MutableMapping


Number = float


@dataclass(frozen=True, slots=True)
class Recipe:
    """A Factorio crafting recipe.

    Parameters
    ----------
    name:
        Human readable recipe name.
    inputs:
        Mapping of item names to the amount consumed per crafting cycle.
    outputs:
        Mapping of item names to the amount produced per crafting cycle.
    duration:
        Duration (in seconds) required to complete one crafting cycle.
    """

    name: str
    inputs: Mapping[str, Number]
    outputs: Mapping[str, Number]
    duration: Number

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError("recipe duration must be positive")
        if not self.outputs:
            raise ValueError("recipe must produce at least one item")


@dataclass(frozen=True, slots=True)
class FactoryStep:
    """Bind a :class:`Recipe` to a number of machines.

    The ``speed_bonus`` models beacon or module bonuses as a fractional
    increase where ``0.2`` corresponds to a +20% crafting speed.
    """

    recipe: Recipe
    machines: Number
    speed_bonus: Number = 0.0

    def __post_init__(self) -> None:
        if self.machines <= 0:
            raise ValueError("machines must be positive")
        if self.speed_bonus < -1:
            raise ValueError("speed bonus cannot reduce speed below zero")

    @property
    def cycles_per_second(self) -> Number:
        """Number of crafting cycles executed per second."""

        return (self.machines * (1.0 + self.speed_bonus)) / self.recipe.duration

    def rate(self, item: str) -> Number:
        """Net production rate for ``item`` in items/second."""

        output = self.recipe.outputs.get(item, 0.0) * self.cycles_per_second
        input_ = self.recipe.inputs.get(item, 0.0) * self.cycles_per_second
        return output - input_


@dataclass(slots=True)
class FactoryBalance:
    """Summary of a blueprint balance calculation."""

    throughput: Dict[str, Number]
    surplus: Dict[str, Number]
    deficit: Dict[str, Number]
    base_consumption: Dict[str, Number]

    def is_balanced(self) -> bool:
        """Return ``True`` when the blueprint has no internal deficits."""

        return not self.deficit

    def describe(self) -> str:
        """Human readable description of the balance."""

        surplus_lines = ", ".join(
            f"{item}: +{amount:.2f}/s" for item, amount in sorted(self.surplus.items())
        ) or "None"
        deficit_lines = ", ".join(
            f"{item}: -{amount:.2f}/s" for item, amount in sorted(self.deficit.items())
        ) or "None"
        base_lines = ", ".join(
            f"{item}: {amount:.2f}/s" for item, amount in sorted(self.base_consumption.items())
        ) or "None"
        return (
            "Surplus -> "
            + surplus_lines
            + " | Deficit -> "
            + deficit_lines
            + " | Base Inputs -> "
            + base_lines
        )


@dataclass(slots=True)
class FactoryBlueprint:
    """A collection of :class:`FactoryStep` objects that form a factory."""

    steps: Iterable[FactoryStep] = field(default_factory=list)

    def balance(self, base_resources: Iterable[str] | None = None) -> FactoryBalance:
        """Return production balance across the blueprint.

        Parameters
        ----------
        base_resources:
            Items that are considered free inputs (ore, water, etc.).
            Deficits for these resources are excluded from the ``deficit``
            report but their consumption rates are still tracked under
            ``base_consumption``.
        """

        base_set = frozenset(base_resources or ())
        throughput: MutableMapping[str, Number] = {}
        base_consumption: MutableMapping[str, Number] = {}

        for step in self.steps:
            cps = step.cycles_per_second
            if cps == 0:
                continue
            for item, amount in step.recipe.outputs.items():
                throughput[item] = throughput.get(item, 0.0) + amount * cps
            for item, amount in step.recipe.inputs.items():
                rate = amount * cps
                throughput[item] = throughput.get(item, 0.0) - rate
                if item in base_set:
                    base_consumption[item] = base_consumption.get(item, 0.0) + rate

        surplus = {
            item: rate
            for item, rate in throughput.items()
            if rate > 0 and item not in base_set
        }
        deficit = {
            item: -rate
            for item, rate in throughput.items()
            if rate < 0 and item not in base_set
        }

        return FactoryBalance(
            throughput=dict(sorted(throughput.items())),
            surplus=dict(sorted(surplus.items())),
            deficit=dict(sorted(deficit.items())),
            base_consumption=dict(sorted(base_consumption.items())),
        )

    def item_rate(self, item: str) -> Number:
        """Convenience helper to read a single item's net throughput."""

        balance = self.balance()
        return balance.throughput.get(item, 0.0)


__all__ = [
    "FactoryBalance",
    "FactoryBlueprint",
    "FactoryStep",
    "Recipe",
]

