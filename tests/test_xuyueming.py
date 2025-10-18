from __future__ import annotations

import pytest

from compute_god import 倒拔垂杨柳, 许月明
from compute_god.xuyueming import WillowBranch, WeepingWillow, WillowUprootPlan, XuYuemingTechnique


def _build_sample_willow() -> WeepingWillow:
    return WeepingWillow(
        root="root",
        branches={
            "root": (
                WillowBranch("north", weight=1.2),
                WillowBranch("south", weight=0.8),
            ),
            "north": (WillowBranch("leaf", weight=0.5),),
            "south": (
                WillowBranch("breeze", weight=0.3),
                WillowBranch("shade", weight=0.9),
            ),
        },
    )


def test_uproot_plan_sequence_and_leverage() -> None:
    willow = _build_sample_willow()
    technique = XuYuemingTechnique(grip_strength=3.2, root_awareness=1.5, footwork=1.1)

    plan = technique.uproot_weeping_willow(willow)

    assert isinstance(plan, WillowUprootPlan)
    assert plan.sequence() == ("breeze", "leaf", "shade", "north", "south", "root")

    leverage_map = dict(plan.leverage_profile())
    assert pytest.approx(leverage_map["root"], rel=1e-9) == 5.17
    assert pytest.approx(leverage_map["south"], rel=1e-12) == 2.7805555555555554
    assert pytest.approx(plan.total_effort, rel=1e-12) == 6.364496785366126


def test_convenience_wrapper_matches_method() -> None:
    willow = _build_sample_willow()
    technique = 许月明(grip_strength=2.4, root_awareness=0.8, footwork=1.25)

    wrapper_plan = 倒拔垂杨柳(technique, willow)
    method_plan = technique.倒拔垂杨柳(willow)

    assert wrapper_plan.sequence() == method_plan.sequence()
    assert pytest.approx(wrapper_plan.total_effort, rel=1e-9) == method_plan.total_effort


def test_willow_helpers_and_validation() -> None:
    willow = _build_sample_willow()

    assert willow.parent("shade") == "south"
    assert willow.path_to_root("shade") == ("shade", "south", "root")
    assert willow.leaves() == ("breeze", "leaf", "shade")

    with pytest.raises(ValueError):
        WeepingWillow(root="origin", branches={"origin": (WillowBranch("loop"),), "loop": (WillowBranch("origin"),)})

    with pytest.raises(ValueError):
        WeepingWillow(root="origin", branches={"origin": (WillowBranch("loop"), WillowBranch("loop"),)})

    with pytest.raises(ValueError):
        WillowBranch(child="", weight=1.0)

