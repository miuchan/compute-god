import pytest

from compute_god.earth_online_council import (
    CouncilAgenda,
    CouncilMandate,
    CouncilMember,
    council_transition,
    simulate_ai_council,
)


def _expected_consensus(members: list[CouncilMember], mandate: CouncilMandate) -> dict[str, float]:
    axes = mandate.axes_tuple()
    baseline = mandate.baseline_targets()
    total = sum(member.influence for member in members)
    weighted = {axis: 0.0 for axis in axes}
    for member in members:
        preferences = member.preferences_for_axes(axes, baseline)
        for axis in axes:
            weighted[axis] += member.influence * preferences[axis]
    for axis in axes:
        weighted[axis] = (
            (1.0 - mandate.consensus_bias) * baseline[axis]
            + mandate.consensus_bias * weighted[axis] / total
        )
    return weighted


def test_simulate_ai_council_converges_to_consensus_target():
    members = [
        CouncilMember(
            name="Gaia",
            influence=0.5,
            priorities={
                "coordination": 0.82,
                "sustainability": 0.97,
                "prosperity": 0.78,
            },
        ),
        CouncilMember(
            name="Atlas",
            influence=0.35,
            priorities={
                "coordination": 0.9,
                "sustainability": 0.88,
                "prosperity": 0.83,
            },
        ),
        CouncilMember(
            name="Mimir",
            influence=0.25,
            priorities={
                "coordination": 0.86,
                "sustainability": 0.9,
                "prosperity": 0.92,
            },
        ),
    ]

    mandate = CouncilMandate(consensus_bias=0.75, adaptation_rate=0.4, dissent_rate=0.55)

    agenda = CouncilAgenda(
        axes={"coordination": 0.55, "sustainability": 0.48, "prosperity": 0.51},
        dissent=0.35,
    )

    expected = _expected_consensus(members, mandate)

    result = simulate_ai_council(agenda, members, mandate, epsilon=1e-9, max_epoch=256)

    assert result.converged

    final_state = result.universe.state
    for axis, target in expected.items():
        assert final_state[axis] == pytest.approx(target, rel=1e-6, abs=1e-6)

    history = final_state["history"]
    assert len(history) == result.epochs + 1
    assert history[0]["coordination"] == pytest.approx(0.55)
    assert history[-1]["coordination"] == pytest.approx(expected["coordination"], rel=1e-6, abs=1e-6)


def test_council_mandate_validates_configuration():
    with pytest.raises(ValueError):
        CouncilMandate(consensus_bias=1.2)

    with pytest.raises(KeyError):
        CouncilMandate(axes=("coordination", "prosperity"), base_targets={"coordination": 0.8})


def test_simulate_ai_council_requires_members():
    agenda = CouncilAgenda(axes={"coordination": 0.6, "sustainability": 0.6, "prosperity": 0.6})

    with pytest.raises(ValueError):
        simulate_ai_council(agenda, [])


def test_council_transition_updates_history_and_dissent():
    members = [
        CouncilMember(name="Lumen", influence=1.0, priorities={"coordination": 1.0, "sustainability": 0.9, "prosperity": 0.7})
    ]
    mandate = CouncilMandate(consensus_bias=0.6, adaptation_rate=0.5, dissent_rate=0.6)
    agenda = CouncilAgenda(axes={"coordination": 0.2, "sustainability": 0.4, "prosperity": 0.3})
    state = agenda.as_state(mandate.axes_tuple())
    keys = mandate.history_keys_tuple()
    state["history"].append({key: state[key] for key in keys})

    next_state = council_transition(state, members, mandate)

    assert next_state["coordination"] > state["coordination"]
    assert len(next_state["history"]) == 2
    assert next_state["history"][-1]["coordination"] == next_state["coordination"]
    assert 0.0 <= next_state["dissent"] <= 1.0
