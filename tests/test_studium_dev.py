"""Tests for the offline studium.dev knowledge helpers."""

from __future__ import annotations

import pytest

from compute_god.studium_dev import (
    describe_notes,
    get_note,
    studium_notes,
    studium_site,
)


def test_site_metadata_is_consistent() -> None:
    site = studium_site()

    assert site.title == "a lattice of leaves, links, and tangled ideas"
    assert site.author == "jerlendds"
    assert "working notes" in site.description.lower()
    assert site.tooling == "Quartz v4.2.3"
    assert "we love graphs" in site.explorer_topics
    assert any("graph view" in note.lower() for note in site.ethos_notes)


def test_note_lookup_and_description() -> None:
    notes = studium_notes()
    assert {"we-love-graphs", "on-randomness"}.issubset(notes)

    graph_note = get_note("we-love-graphs")
    assert "interconnected" in graph_note.summary
    assert graph_note.quote and "leaves made of links" in graph_note.quote

    summary = describe_notes(["we-love-graphs", "on-randomness"])
    summary_lower = summary.lower()
    assert "graph view" in summary_lower
    assert "randomness" in summary_lower
    assert summary.count("•") >= 4


def test_unknown_note_raises() -> None:
    with pytest.raises(KeyError):
        get_note("unknown-note")

    with pytest.raises(KeyError):
        describe_notes(["unknown-note"])

    assert describe_notes([]) == "No notes selected from studium.dev."
