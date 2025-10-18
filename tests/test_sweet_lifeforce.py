from compute_god.miyu_tiantian import (
    DEFAULT_STATE,
    MiyuTiantianBlueprint,
    sweet_lifeforce,
)


def test_sweet_lifeforce_increases_with_closeness():
    blueprint = MiyuTiantianBlueprint()
    close_state = blueprint.as_state()

    close_pulse = sweet_lifeforce(
        tiantian_state=close_state,
        miyu_state=close_state,
        blueprint=blueprint,
    )

    muted_state = dict(close_state)
    muted_state["hormone_glow"] = 0.2
    muted_pulse = sweet_lifeforce(
        tiantian_state=muted_state,
        miyu_state=muted_state,
        blueprint=blueprint,
    )

    distant_state = {key: 0.0 for key in DEFAULT_STATE}
    far_pulse = sweet_lifeforce(
        tiantian_state=distant_state,
        miyu_state=distant_state,
        blueprint=blueprint,
    )

    assert 0.0 <= close_pulse.lifeforce <= 1.0
    assert close_pulse.lifeforce > far_pulse.lifeforce
    assert close_pulse.lifeforce > muted_pulse.lifeforce
    assert any("心跳" in reason for reason in close_pulse.reasons)
    assert any("激素" in reason for reason in close_pulse.reasons)


def test_sweet_lifeforce_offers_reason_even_when_dim():
    blueprint = MiyuTiantianBlueprint()
    tiantian_state = {
        "emotion": 0.08,
        "memory_bloom": 0.1,
        "collaboration": 0.05,
        "dream_isles": 0.0,
        "orbit_rhythm": 0.04,
        "resonance": 0.1,
        "diary": 0.12,
    }

    pulse = sweet_lifeforce(
        tiantian_state=tiantian_state,
        miyu_state={"emotion": 0.1},
        blueprint=blueprint,
    )

    assert 0.0 <= pulse.lifeforce <= 1.0
    assert pulse.encounter.keys() == DEFAULT_STATE.keys()
    assert any("理由" in reason or "微光" in reason for reason in pulse.reasons)
