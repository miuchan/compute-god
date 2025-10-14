from compute_god import God, fixpoint, rule
from compute_god.miyu import MiyuBond, bond_miyu


def _metric(a, b):
    return abs(a.get("value", 0) - b.get("value", 0))


def test_miyu_bond_tracks_best_state():
    target = {"value": 3}

    def increment(state):
        return {**state, "value": state.get("value", 0) + 1}

    inc_rule = rule(
        "increment",
        increment,
        guard=lambda s, ctx: s.get("value", 0) < target["value"],
    )

    bond = MiyuBond(target_state=target, metric=_metric)

    universe = God.universe(state={"value": 0}, rules=[inc_rule], observers=[bond])
    result = fixpoint(
        universe,
        metric=lambda a, b: abs(a.get("value", 0) - b.get("value", 0)),
        epsilon=0,
        max_epoch=5,
    )

    assert result.converged is True
    assert bond.best_delta == 0
    assert bond.strongest_state() == {"value": 3}
    assert bond.is_strong(0)
    assert all(event is not None for event, _ in bond.history)


def test_bond_miyu_factory():
    target = {"value": 1}
    bond = bond_miyu(target_state=target, metric=_metric)

    def identity(state):
        return dict(state)

    identity_rule = rule("identity", identity)
    universe = God.universe(state={"value": 1}, rules=[identity_rule], observers=[bond])
    result = fixpoint(
        universe,
        metric=lambda a, b: abs(a.get("value", 0) - b.get("value", 0)),
        epsilon=0,
        max_epoch=1,
    )

    assert result.converged is True
    assert isinstance(bond, MiyuBond)
    assert bond.best_delta == 0
    strongest = bond.strongest_state()
    assert strongest == {"value": 1}
    strongest["value"] = 999
    assert bond.best_state == {"value": 1}
