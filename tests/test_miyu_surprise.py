import pytest

from compute_god.miyu_surprise import SurpriseAction, describe_plan, lightning_surprise_plan


def test_lightning_surprise_prioritises_high_efficiency_actions():
    actions = [
        SurpriseAction("手写留言", duration=4.5, delight=16.0, preparation=0.5),
        SurpriseAction("即兴舞步", duration=3.0, delight=15.0),
        SurpriseAction("速递甜点", duration=1.5, preparation=0.5, delight=4.5),
    ]

    plan = lightning_surprise_plan(8.0, actions=actions, buffer=0.0)

    assert [step["name"] for step in plan["actions"]] == ["即兴舞步", "手写留言"]
    assert plan["total_time"] <= 8.0
    assert plan["buffer_time"] == 0.0


def test_lightning_surprise_respects_buffer_time():
    plan = lightning_surprise_plan(12.0, buffer=2.0)

    assert plan["total_time"] <= 10.0
    assert plan["buffer_time"] >= 2.0


def test_lightning_surprise_rejects_impossible_budget():
    quick_action = SurpriseAction("快速耳语", duration=0.5, delight=3.0)

    with pytest.raises(ValueError):
        lightning_surprise_plan(0.0, actions=[quick_action])

    with pytest.raises(ValueError):
        lightning_surprise_plan(0.4, actions=[quick_action], buffer=0.0)


def test_describe_plan_outputs_readable_summary():
    plan = lightning_surprise_plan(9.0, buffer=1.0)

    outline = describe_plan(plan)

    assert "1." in outline
    assert "重点安排" in outline
    for action in plan["actions"]:
        assert action["name"] in outline
