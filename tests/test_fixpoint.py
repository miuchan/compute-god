from compute_god import God, fixpoint, rule


def edit_distance(a, b):
    return sum(1 for key in set(a) | set(b) if a.get(key) != b.get(key))


def test_fixpoint_converges():
    target = 3

    def increment(state):
        value = state.get("counter", 0)
        return {**state, "counter": min(value + 1, target)}

    inc_rule = rule(
        "increment",
        increment,
        until=lambda state, ctx: state.get("counter", 0) >= target,
    )

    universe = God.universe(state={"counter": 0}, rules=[inc_rule])

    result = fixpoint(
        universe,
        metric=lambda a, b: abs(a.get("counter", 0) - b.get("counter", 0)),
        epsilon=0,
        max_epoch=10,
    )

    assert result.converged is True
    assert result.universe.state["counter"] == target


def test_fixpoint_max_epoch():
    def identity(state):
        return dict(state)

    identity_rule = rule("identity", identity)
    universe = God.universe(state={"value": 1}, rules=[identity_rule])

    result = fixpoint(
        universe,
        metric=lambda a, b: edit_distance(a, b),
        epsilon=0,
        max_epoch=2,
    )

    assert result.converged is True
    assert result.epochs == 1
    assert result.universe.state == {"value": 1}
