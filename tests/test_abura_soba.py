import pytest

from compute_god.abura_soba import (
    AburaSobaProfile,
    NoodleCanvas,
    OilLayer,
    TareBlend,
    Topping,
    assemble_abura_soba,
    油そば,
)


def test_abura_soba_profile_metrics() -> None:
    noodles = NoodleCanvas(hydration=0.58, chewiness=1.1, thickness=1.9)
    tare = TareBlend(salinity=1.5, umami=2.2, sweetness=0.4, acidity=0.7)
    oil = OilLayer(aroma=1.6, viscosity=1.3, spice=0.5)
    toppings = [
        Topping("menma", intensity=0.8, crunch=0.6),
        Topping("scallion", intensity=0.3, crunch=0.4),
    ]

    profile = assemble_abura_soba(
        noodles,
        tare,
        oil,
        toppings,
        vinegar=0.2,
        chili_oil=0.1,
    )

    assert isinstance(profile, AburaSobaProfile)
    assert profile.toppings == ["menma", "scallion"]
    assert profile.richness == pytest.approx(1.8078, abs=1e-4)
    assert profile.brightness == pytest.approx(1.1, abs=1e-6)
    assert profile.texture == pytest.approx(2.17, abs=1e-2)
    assert 0.0 <= profile.balance <= 1.0
    assert profile.balance == pytest.approx(0.5397, abs=1e-4)
    assert "toss" in profile.recommendation.lower()

    alias_profile = 油そば(
        noodles,
        tare,
        oil,
        toppings,
        vinegar=0.2,
        chili_oil=0.1,
    )
    assert alias_profile == profile


def test_abura_soba_validations() -> None:
    with pytest.raises(ValueError):
        NoodleCanvas(hydration=1.2, chewiness=1.0, thickness=1.5)

    with pytest.raises(ValueError):
        TareBlend(salinity=-0.2, umami=1.0)

    with pytest.raises(ValueError):
        OilLayer(aroma=0.0, viscosity=1.0)

    with pytest.raises(ValueError):
        Topping("", intensity=0.3)

