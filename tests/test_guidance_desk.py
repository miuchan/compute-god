import pytest

from compute_god import (
    GUIDANCE_DESK,
    DeskStation,
    GuidanceDesk,
    God,
    guidance_desk,
)


@pytest.fixture
def sample_station() -> DeskStation:
    station = DeskStation("triage", "Sample desk")
    station.add("alpha", 1)
    station.extend({"beta": 2})
    return station


def test_desk_station_behaves_like_mapping(sample_station: DeskStation) -> None:
    assert list(sample_station.keys()) == ["alpha", "beta"]
    assert sample_station["alpha"] == 1
    assert sample_station.catalog() == ("alpha", "beta")

    snapshot = sample_station.snapshot()
    assert snapshot["beta"] == 2
    with pytest.raises(TypeError):
        snapshot["gamma"] = 3  # type: ignore[index]


def test_guidance_desk_singleton() -> None:
    desk = guidance_desk()
    assert isinstance(desk, GuidanceDesk)
    assert desk is GUIDANCE_DESK
    assert "core" in desk
    assert desk.resolve("core.God") is God
    assert desk.resolve("core:Universe") is GUIDANCE_DESK["core"]["Universe"]


def test_guidance_desk_catalogue_navigation() -> None:
    catalog = GUIDANCE_DESK.catalog()
    assert "core" in catalog
    assert "bonds" in catalog
    assert catalog["core"][:5] == ("God", "Rule", "rule", "State", "Metric")
    assert "ApplyFn" in catalog["core"]

    assert GUIDANCE_DESK.has_entry("metaverse.run_ideal_metaverse")
    assert GUIDANCE_DESK.resolve("metaverse/run_ideal_metaverse") is GUIDANCE_DESK["metaverse"]["run_ideal_metaverse"]


def test_guidance_desk_summary_is_immutable() -> None:
    summary = GUIDANCE_DESK.summary()
    core = summary["core"]
    assert "God" in core
    with pytest.raises(TypeError):
        core["new"] = object()  # type: ignore[index]
