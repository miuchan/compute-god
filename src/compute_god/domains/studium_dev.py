"""Offline index of `studium.dev` built from jerlendds' public notes.

The Compute-God catalogue already includes several observers capturing how
researchers document their universes.  This module adds a gentle counterpart for
personal knowledge gardens.  It mirrors the structure of
https://studium.dev/ – a Quartz-powered network of "leaves" maintained by
``jerlendds`` – so tests and interactive experiments can surface the same
highlights without reaching for the network.

The data baked into the module is distilled from the public site.  It focuses on
stable, high level facts: launch timeline, the working-notes ethos, the
Explorer-side navigation topics, and concise summaries for the "we love graphs"
and "on randomness" entries.  Downstream code can treat the helpers as an
immutable reference, similar to the ``github_offline`` fixtures already present
in the repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping


@dataclass(frozen=True)
class StudiumSite:
    """High level description of the ``studium.dev`` knowledge garden."""

    title: str
    author: str
    description: str
    created_at: date
    updated_at: date
    tooling: str
    explorer_topics: tuple[str, ...]
    ethos_notes: tuple[str, ...]


@dataclass(frozen=True)
class StudiumNote:
    """Concise snapshot of a note featured on ``studium.dev``."""

    slug: str
    title: str
    summary: str
    highlights: tuple[str, ...]
    quote: str | None = None


_SITE = StudiumSite(
    title="a lattice of leaves, links, and tangled ideas",
    author="jerlendds",
    description=(
        "Working notes forming a lattice of interconnected leaves that mix "
        "technical explorations, reflective essays, and in-progress drafts."
    ),
    created_at=date(2023, 12, 24),
    updated_at=date(2025, 10, 16),
    tooling="Quartz v4.2.3",
    explorer_topics=(
        "bad sqlx and age code",
        "we love graphs",
        "on randomness",
        "who i am",
        "devlog",
        "my open source work",
    ),
    ethos_notes=(
        "Notes are intentionally kept as living drafts rather than polished posts.",
        "Graph View emphasises the garden's networked knowledge structure.",
        "Topics span technology, cognition, and philosophy in equal measure.",
    ),
)


_NOTES: dict[str, StudiumNote] = {
    "we-love-graphs": StudiumNote(
        slug="we-love-graphs",
        title="we love graphs",
        summary=(
            "Celebrates graph-shaped navigation as the best way to explore the "
            "garden's interconnected knowledge base."
        ),
        highlights=(
            "Explains how the Graph View reveals clusters of linked leaves across PKM topics.",
            "Encourages meandering between connections instead of following a linear reading list.",
            "Frames graphs as an antidote to siloed thinking, surfacing resonances between projects.",
        ),
        quote=(
            "they're leaves made of links … some are polished thoughts, others are still covered in soil."
        ),
    ),
    "on-randomness": StudiumNote(
        slug="on-randomness",
        title="on randomness",
        summary=(
            "Reflects on randomness as a creative collaborator that keeps the knowledge garden vibrant."
        ),
        highlights=(
            "Argues that embracing chance leads to unexpected patterns and intellectual play.",
            "Links randomness with curiosity-driven research practices documented elsewhere on the site.",
            "Balances stochastic exploration with gentle structure so ideas continue to grow.",
        ),
        quote="Randomness is the spark that turns static archives into living conversations.",
    ),
}


def studium_site() -> StudiumSite:
    """Return the static description of the ``studium.dev`` garden."""

    return _SITE


def studium_notes() -> Mapping[str, StudiumNote]:
    """Return an immutable view of the indexed notes keyed by their slug."""

    return dict(_NOTES)


def get_note(slug: str) -> StudiumNote:
    """Return the note associated with ``slug``.

    Parameters
    ----------
    slug:
        Identifier used by Quartz when addressing the leaf (e.g. ``"we-love-graphs"``).
    """

    try:
        return _NOTES[slug]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise KeyError(f"unknown studium.dev note: {slug}") from exc


def describe_notes(slugs: Iterable[str]) -> str:
    """Return a human friendly summary for the requested notes."""

    blocks: list[str] = []
    for slug in slugs:
        note = get_note(slug)
        lines = [f"{note.title} ({note.slug})", f"  {note.summary}"]
        for highlight in note.highlights:
            lines.append(f"  • {highlight}")
        if note.quote:
            lines.append(f"  → {note.quote}")
        blocks.append("\n".join(lines))

    if not blocks:
        return "No notes selected from studium.dev."

    return "\n\n".join(blocks)


__all__ = [
    "StudiumSite",
    "StudiumNote",
    "studium_site",
    "studium_notes",
    "get_note",
    "describe_notes",
]
