import math

import pytest

from compute_god.catalysis import (
    CatalysisOutcome,
    Chanzi,
    Jiuzi,
    catalyse_jiuzi_and_chanzi,
)


def test_catalysis_balanced_pair() -> None:
    jiuzi = Jiuzi(loops=4, twist=1.2, coherence=0.8)
    chanzi = Chanzi(strands=4, torsion=0.9, resonance=1.1)

    outcome = catalyse_jiuzi_and_chanzi(jiuzi, chanzi, catalyst=1.5, agitation=0.6)

    expected_base = math.sqrt(jiuzi.intensity * chanzi.intensity)
    expected_alignment = 1.0 / (1.0 + abs(jiuzi.loops - chanzi.strands))
    expected_drive = math.log1p(1.5 * 0.6)
    expected_entanglement = expected_base * expected_alignment * expected_drive
    expected_stability = ((jiuzi.coherence + chanzi.resonance) / 2.0) * expected_drive
    expected_yield = expected_entanglement / (jiuzi.loops + chanzi.strands)

    assert isinstance(outcome, CatalysisOutcome)
    assert outcome.entanglement == pytest.approx(expected_entanglement)
    assert outcome.alignment == pytest.approx(expected_alignment)
    assert outcome.stability == pytest.approx(expected_stability)
    assert outcome.yield_strength == pytest.approx(expected_yield)


def test_alignment_penalty_reduces_entanglement() -> None:
    jiuzi = Jiuzi(loops=3, twist=1.4, coherence=1.0)
    aligned = Chanzi(strands=3, torsion=1.1, resonance=1.0)
    misaligned = Chanzi(strands=5, torsion=1.1, resonance=1.0)

    aligned_outcome = catalyse_jiuzi_and_chanzi(jiuzi, aligned, catalyst=1.2, agitation=0.5)
    misaligned_outcome = catalyse_jiuzi_and_chanzi(jiuzi, misaligned, catalyst=1.2, agitation=0.5)

    assert aligned_outcome.alignment > misaligned_outcome.alignment
    assert aligned_outcome.entanglement > misaligned_outcome.entanglement


@pytest.mark.parametrize(
    "factory, kwargs",
    [
        (Jiuzi, dict(loops=0, twist=1.0, coherence=1.0)),
        (Jiuzi, dict(loops=1, twist=0.0, coherence=1.0)),
        (Jiuzi, dict(loops=1, twist=1.0, coherence=0.0)),
        (Chanzi, dict(strands=0, torsion=1.0, resonance=1.0)),
        (Chanzi, dict(strands=1, torsion=0.0, resonance=1.0)),
        (Chanzi, dict(strands=1, torsion=1.0, resonance=0.0)),
    ],
)
def test_participant_validation(factory, kwargs) -> None:
    with pytest.raises(ValueError):
        factory(**kwargs)


@pytest.mark.parametrize(
    "catalyst, agitation",
    [(-1.0, 1.0), (1.0, 0.0)],
)
def test_catalysis_requires_positive_drivers(catalyst: float, agitation: float) -> None:
    jiuzi = Jiuzi(loops=2, twist=1.0, coherence=1.0)
    chanzi = Chanzi(strands=2, torsion=1.0, resonance=1.0)

    with pytest.raises(ValueError):
        catalyse_jiuzi_and_chanzi(jiuzi, chanzi, catalyst=catalyst, agitation=agitation)
