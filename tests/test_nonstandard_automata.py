from __future__ import annotations

import pytest

from compute_god.nonstandard_automata import (
    BriansBrainCell,
    WireworldCell,
    brians_brain_step,
    cyclic_automaton_step,
    wireworld_step,
)


def test_cyclic_automaton_step_threshold():
    grid = [
        [0, 1, 1],
        [3, 2, 1],
        [0, 3, 2],
    ]

    assert cyclic_automaton_step(grid, states=4, threshold=2) == [
        [0, 1, 1],
        [0, 3, 2],
        [0, 3, 2],
    ]

    assert cyclic_automaton_step(grid, states=4, threshold=0) == [
        [1, 2, 2],
        [0, 3, 2],
        [1, 0, 3],
    ]


def test_cyclic_automaton_validation():
    with pytest.raises(ValueError):
        cyclic_automaton_step([[0]], states=1)
    with pytest.raises(ValueError):
        cyclic_automaton_step([[0]], states=2, threshold=-1)
    with pytest.raises(ValueError):
        cyclic_automaton_step([[2]], states=2)


def test_brians_brain_step():
    grid = [
        [0, 1, 0],
        [1, 2, 1],
        [0, 1, 0],
    ]

    assert brians_brain_step(grid) == [
        [int(BriansBrainCell.FIRING), int(BriansBrainCell.REFRACTORY), int(BriansBrainCell.FIRING)],
        [int(BriansBrainCell.REFRACTORY), int(BriansBrainCell.DEAD), int(BriansBrainCell.REFRACTORY)],
        [int(BriansBrainCell.FIRING), int(BriansBrainCell.REFRACTORY), int(BriansBrainCell.FIRING)],
    ]


def test_wireworld_step():
    grid = [
        [int(WireworldCell.CONDUCTOR), int(WireworldCell.ELECTRON_HEAD), int(WireworldCell.CONDUCTOR)],
        [int(WireworldCell.EMPTY), int(WireworldCell.CONDUCTOR), int(WireworldCell.EMPTY)],
        [int(WireworldCell.CONDUCTOR), int(WireworldCell.EMPTY), int(WireworldCell.CONDUCTOR)],
    ]

    assert wireworld_step(grid) == [
        [int(WireworldCell.ELECTRON_HEAD), int(WireworldCell.ELECTRON_TAIL), int(WireworldCell.ELECTRON_HEAD)],
        [int(WireworldCell.EMPTY), int(WireworldCell.ELECTRON_HEAD), int(WireworldCell.EMPTY)],
        [int(WireworldCell.CONDUCTOR), int(WireworldCell.EMPTY), int(WireworldCell.CONDUCTOR)],
    ]
