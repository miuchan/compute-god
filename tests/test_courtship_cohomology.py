"""Tests for the courtship cohomology helper."""

from fractions import Fraction

import pytest

from compute_god.courtship_cohomology import (
    CochainSpace,
    CourtshipCochainComplex,
    CourtshipDifferential,
    courtship_cohomology_story,
)


def _courtship_complex() -> CourtshipCochainComplex:
    spaces = {
        0: CochainSpace(("confidence", "clarity")),
        1: CochainSpace(("vulnerability", "playfulness", "attunement")),
        2: CochainSpace(("shared_story",)),
    }

    d0 = CourtshipDifferential(
        domain=0,
        codomain=1,
        matrix=(
            (Fraction(1), Fraction(1)),
            (Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(0)),
        ),
    )

    d1 = CourtshipDifferential(
        domain=1,
        codomain=2,
        matrix=((Fraction(0), Fraction(1), Fraction(-1)),),
    )

    return CourtshipCochainComplex(spaces, (d0, d1))


def test_courtship_betti_numbers():
    complex_ = _courtship_complex()
    betti = complex_.betti_numbers()

    assert betti[0] == 1
    assert betti[1] == 1
    assert betti[2] == 0


def test_courtship_story_mentions_basis():
    complex_ = _courtship_complex()
    story = courtship_cohomology_story(complex_)

    assert 0 in story
    assert "confidence" in story[0]
    assert "clarity" in story[0]
    assert 1 in story
    assert "vulnerability" in story[1]


def test_invalid_complex_raises_error():
    spaces = {
        0: CochainSpace(("confidence",)),
        1: CochainSpace(("vulnerability",)),
        2: CochainSpace(("shared_story",)),
    }

    d0 = CourtshipDifferential(domain=0, codomain=1, matrix=((Fraction(1),),))
    # This differential composes with d0 to give a non-zero map, violating d^2 = 0.
    d1 = CourtshipDifferential(domain=1, codomain=2, matrix=((Fraction(1),),))

    with pytest.raises(ValueError):
        CourtshipCochainComplex(spaces, (d0, d1))

