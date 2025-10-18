from typing import Sequence

import pytest

from compute_god.life_toolbox import (
    LifeNeed,
    ToolRitual,
    assemble_life_toolkit,
    design_energy_breaks,
    design_hydration_ritual,
    design_meal_landscape,
)


def test_life_need_validation() -> None:
    with pytest.raises(ValueError):
        LifeNeed(name="", description="rest")
    with pytest.raises(ValueError):
        LifeNeed(name="Rest", description=" ")
    with pytest.raises(ValueError):
        LifeNeed(name="Rest", description="Recharge", priority=0)
    with pytest.raises(TypeError):
        LifeNeed(name="Rest", description="Recharge", tags=(" ",))


def test_tool_ritual_validation() -> None:
    with pytest.raises(ValueError):
        ToolRitual(title="", steps=("step",), duration_minutes=5)
    with pytest.raises(ValueError):
        ToolRitual(title="Stretch", steps=(), duration_minutes=5)
    with pytest.raises(TypeError):
        ToolRitual(title="Stretch", steps=("",), duration_minutes=5)
    with pytest.raises(ValueError):
        ToolRitual(title="Stretch", steps=("Move",), duration_minutes=0)


def test_design_hydration_ritual_creates_steps() -> None:
    ritual = design_hydration_ritual(12, flavor="柠檬", start_with_warm=True)
    assert ritual.title == "全天水合规划"
    assert any("柠檬" in step for step in ritual.steps)
    assert ritual.duration_minutes > 0
    assert ritual.mood == "refreshing"


@pytest.mark.parametrize("prefs", [["番茄", "牛油果"], ("番茄", "芝士", "罗勒")])
def test_design_meal_landscape_features_preferences(prefs: Sequence[str]) -> None:
    ritual = design_meal_landscape(prefs, budget=88.0)
    joined = "、".join(list(prefs)[:3])
    assert joined in ritual.steps[0]
    assert ritual.mood == "nourishing"


def test_design_energy_breaks_enforces_structure() -> None:
    ritual = design_energy_breaks(sessions=2, focus_minutes=45, break_minutes=7)
    assert ritual.steps[0].startswith("设置 2 个专注区块")
    assert ritual.duration_minutes == (45 + 7) * 2


@pytest.mark.parametrize("available", [60, 90])
def test_assemble_life_toolkit_allocates_time(available: int) -> None:
    needs = [
        LifeNeed(name="补水", description="维持体液平衡", priority=3),
        LifeNeed(name="营养", description="获取能量", priority=2),
    ]
    rituals = [
        design_hydration_ritual(10),
        design_meal_landscape(["燕麦", "菠菜"], budget=50.0),
        design_energy_breaks(1, 30),
    ]
    plan = assemble_life_toolkit(needs, rituals, available_minutes=available)
    assert plan["needs"] == ("补水", "营养")
    assert plan["schedule"]
    assert plan["remaining_minutes"] <= available
    assert "gratitude_prompt" in plan


def test_assemble_life_toolkit_requires_fit() -> None:
    need = LifeNeed(name="放松", description="减压", priority=1)
    ritual = ToolRitual(title="长时间瑜伽", steps=("进行 90 分钟练习",), duration_minutes=90)
    with pytest.raises(ValueError):
        assemble_life_toolkit([need], [ritual], available_minutes=30)
