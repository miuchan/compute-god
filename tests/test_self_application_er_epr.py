from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from compute_god.self_application_er_epr import (
    bell_state,
    choi_state_from_kraus,
    entanglement_entropy,
    factorial_via_y,
    thermofield_double,
    y_combinator,
)


def test_y_combinator_produces_factorial() -> None:
    assert factorial_via_y(0) == 1
    assert factorial_via_y(5) == 120


def test_y_combinator_allows_custom_recursion() -> None:
    def make_sum(recursive):
        def inner(pair):
            left, right = pair
            if right == 0:
                return left
            return recursive((left + 1, right - 1))

        return inner

    add = y_combinator(make_sum)
    assert add((2, 3)) == 5


def test_thermofield_double_entropy_matches_two_level_system() -> None:
    state = thermofield_double([0.0, 1.0], beta=1.0)
    entropy = entanglement_entropy(state, (2, 2))
    assert entropy == pytest.approx(0.8723, rel=1e-3)


def test_choi_state_matches_bell_projector_for_identity() -> None:
    identity = np.eye(2)
    choi = choi_state_from_kraus([identity])
    bell = bell_state(2)
    projector = np.outer(bell, bell.conj())
    assert np.allclose(choi, projector)

