from __future__ import annotations

import pytest

from compute_god.shulikou_cloud_village import build_shulikou_cloud_village


def test_cloud_village_reading_alignment_and_balance():
    cooperative = build_shulikou_cloud_village()
    reading = cooperative.reading()

    assert reading.dominant_axis == "technique"
    assert reading.technique == pytest.approx(0.4660098522167489)
    assert reading.power == pytest.approx(0.3453201970443349)
    assert reading.voice == pytest.approx(0.3177339901477833)
    assert reading.resonance == pytest.approx(0.5938964896358961)
    assert reading.alignment == pytest.approx(0.9205933682373473)
    assert reading.balance == pytest.approx(0.868673647469459)
    assert reading.distribution == pytest.approx(
        (0.4127399650959861, 0.30584642233856885, 0.28141361256544506)
    )
    assert reading.average_coherence == pytest.approx(2 / 3)


def test_role_readings_follow_member_focus():
    cooperative = build_shulikou_cloud_village()
    role_readings = cooperative.role_readings()

    assert set(role_readings) == {"weaver", "gardener", "chorus"}

    weaver = role_readings["weaver"]
    assert weaver.dominant_axis == "technique"
    assert weaver.distribution == pytest.approx((0.8, 0.1, 0.1))

    gardener = role_readings["gardener"]
    assert gardener.dominant_axis == "power"
    assert gardener.distribution == pytest.approx((0.1666666666666667, 0.5833333333333333, 0.25))

    chorus = role_readings["chorus"]
    assert chorus.dominant_axis == "voice"
    assert chorus.distribution == pytest.approx(
        (0.15384615384615383, 0.15384615384615383, 0.6923076923076923)
    )


def test_initiatives_apply_amplification_to_participants():
    cooperative = build_shulikou_cloud_village()
    initiatives = cooperative.initiative_readings()

    assert set(initiatives) == {"云纹织造坊", "回声集市"}

    weaving = initiatives["云纹织造坊"]
    assert weaving.dominant_axis == "technique"
    assert weaving.distribution == pytest.approx(
        (0.47916666666666674, 0.34484649122807015, 0.1759868421052632)
    )

    market = initiatives["回声集市"]
    assert market.dominant_axis == "power"
    assert market.distribution == pytest.approx(
        (0.16235632183908044, 0.4389367816091954, 0.3987068965517241)
    )
    assert market.resonance > weaving.resonance
