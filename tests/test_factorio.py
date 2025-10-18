import math

from compute_god.factorio import (
    FactoryBalance,
    FactoryBlueprint,
    FactoryStep,
    Recipe,
)


def test_factory_step_rate_and_cycles():
    recipe = Recipe(
        name="iron-plate",
        inputs={"iron-ore": 1},
        outputs={"iron-plate": 1},
        duration=3.2,
    )
    step = FactoryStep(recipe=recipe, machines=4, speed_bonus=0.25)

    cycles = step.cycles_per_second
    assert math.isclose(cycles, 1.5625, rel_tol=1e-6)
    assert math.isclose(step.rate("iron-plate"), cycles, rel_tol=1e-6)
    assert math.isclose(step.rate("iron-ore"), -cycles, rel_tol=1e-6)


def test_factory_blueprint_balance_tracks_surplus_and_base_inputs():
    iron_plate = Recipe(
        "iron-plate",
        inputs={"iron-ore": 1},
        outputs={"iron-plate": 1},
        duration=1.0,
    )
    copper_plate = Recipe(
        "copper-plate",
        inputs={"copper-ore": 1},
        outputs={"copper-plate": 1},
        duration=1.0,
    )
    gear_wheel = Recipe(
        "gear-wheel",
        inputs={"iron-plate": 2},
        outputs={"gear-wheel": 1},
        duration=1.0,
    )
    copper_cable = Recipe(
        "copper-cable",
        inputs={"copper-plate": 1},
        outputs={"copper-cable": 2},
        duration=0.5,
    )
    green_circuit = Recipe(
        "green-circuit",
        inputs={"iron-plate": 1, "copper-cable": 3},
        outputs={"green-circuit": 1},
        duration=0.5,
    )

    blueprint = FactoryBlueprint(
        steps=[
            FactoryStep(recipe=iron_plate, machines=14),
            FactoryStep(recipe=copper_plate, machines=8),
            FactoryStep(recipe=gear_wheel, machines=4),
            FactoryStep(recipe=copper_cable, machines=3),
            FactoryStep(recipe=green_circuit, machines=2),
        ]
    )

    balance = blueprint.balance(base_resources={"iron-ore", "copper-ore"})
    assert isinstance(balance, FactoryBalance)
    assert balance.is_balanced()

    assert math.isclose(balance.throughput["iron-plate"], 2.0, rel_tol=1e-6)
    assert math.isclose(balance.throughput["gear-wheel"], 4.0, rel_tol=1e-6)
    assert math.isclose(balance.throughput["green-circuit"], 4.0, rel_tol=1e-6)
    assert math.isclose(balance.throughput["copper-plate"], 2.0, rel_tol=1e-6)

    assert balance.deficit == {}
    assert math.isclose(balance.surplus["copper-plate"], 2.0, rel_tol=1e-6)
    assert math.isclose(balance.base_consumption["iron-ore"], 14.0, rel_tol=1e-6)
    assert math.isclose(balance.base_consumption["copper-ore"], 8.0, rel_tol=1e-6)

    description = balance.describe()
    assert "Surplus" in description and "Deficit" in description


def test_item_rate_shortcut():
    blueprint = FactoryBlueprint(
        steps=[
            FactoryStep(
                recipe=Recipe(
                    "stone-brick",
                    inputs={"stone": 2},
                    outputs={"stone-brick": 1},
                    duration=3.0,
                ),
                machines=6,
            )
        ]
    )

    rate = blueprint.item_rate("stone-brick")
    assert math.isclose(rate, 2.0, rel_tol=1e-6)

