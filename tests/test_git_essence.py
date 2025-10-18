"""Tests for the Git essence structural model."""

from compute_god.git_essence import (
    GitEssence,
    git_essence_model,
)


def test_git_essence_common_and_differentiators() -> None:
    model = git_essence_model()
    assert isinstance(model, GitEssence)

    common = model.common_names()
    differentiators = model.differentiator_names()

    assert common == (
        "Snapshot storage",
        "Content addressed objects",
        "Immutable history graph",
    )
    assert differentiators[0] == "Branch pointers"
    assert "Distributed synchronisation" in differentiators


def test_git_essence_summary_structure() -> None:
    summary = git_essence_model().summary()

    assert {"common", "differentiators"} == set(summary.keys())
    assert all(entry["invariants"] for entry in summary["common"])
    assert all("capabilities" in entry for entry in summary["differentiators"])
