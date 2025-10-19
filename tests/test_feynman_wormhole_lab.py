from __future__ import annotations

import math

import pytest

np = pytest.importorskip("numpy")

from compute_god.feynman_wormhole_lab import (
    BridgeSummary,
    DiagramLeg,
    Propagator,
    run_feynman_wormhole_lab,
)


def test_feynman_wormhole_lab_generates_expected_bridge() -> None:
    legs = [
        DiagramLeg("L0", "left"),
        DiagramLeg("L1", "left"),
        DiagramLeg("R0", "right"),
        DiagramLeg("R1", "right"),
    ]
    propagators = [
        Propagator("L0", "R0", amplitude=1.0, proper_time=0.5),
        Propagator("L0", "R1", amplitude=0.5, proper_time=1.0),
        Propagator("R0", "L1", amplitude=0.7, proper_time=1.5),
        Propagator("L1", "R1", amplitude=1.2, proper_time=0.75),
    ]

    summary = run_feynman_wormhole_lab(legs, propagators, temperature=1.0)

    expected_matrix = np.array(
        [
            [math.exp(-0.5), 0.5 * math.exp(-1.0)],
            [0.7 * math.exp(-1.5), 1.2 * math.exp(-0.75)],
        ],
        dtype=float,
    )

    assert isinstance(summary, BridgeSummary)
    assert summary.left_labels == ("L0", "L1")
    assert summary.right_labels == ("R0", "R1")
    assert summary.temperature == pytest.approx(1.0)
    assert np.allclose(summary.propagator_matrix, expected_matrix)
    assert summary.bridge_strength == pytest.approx(float(np.sum(np.abs(expected_matrix))), rel=1e-6)
    assert len(summary.state_vector) == 4
    assert summary.entanglement_bits == pytest.approx(0.7799709844469482, rel=1e-6)
    assert summary.schmidt_coefficients == pytest.approx(
        (0.8768539587115665, 0.48075683572036104),
        rel=1e-6,
    )


def test_feynman_wormhole_lab_rejects_invalid_wiring() -> None:
    legs = [DiagramLeg("L0", "left"), DiagramLeg("R0", "right")]

    with pytest.raises(KeyError):
        run_feynman_wormhole_lab(legs, [Propagator("L0", "R1")])

    with pytest.raises(ValueError):
        run_feynman_wormhole_lab(legs, [Propagator("L0", "L0")])

    with pytest.raises(ValueError):
        run_feynman_wormhole_lab(legs, [Propagator("L0", "R0", amplitude=0.0)], temperature=-0.1)
