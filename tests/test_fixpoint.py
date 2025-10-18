import functools

from compute_god import God, fixpoint, recursive_descent_fixpoint, rule


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


def test_fixpoint_metric_convergence():
    target = 42.0

    def ease_towards_target(state):
        value = state.get("value", 0.0)
        next_value = value + (target - value) * 0.5
        return {**state, "value": next_value}

    ease_rule = rule("ease", ease_towards_target)
    universe = God.universe(state={"value": 0.0}, rules=[ease_rule])

    result = fixpoint(
        universe,
        metric=lambda a, b: abs(a["value"] - b["value"]),
        epsilon=1e-3,
        max_epoch=50,
    )

    assert result.converged is True
    assert result.epochs < 50
    assert abs(result.universe.state["value"] - target) <= 1e-3


def test_rule_accepts_bound_method():
    class Incrementer:
        def __init__(self) -> None:
            self.calls = 0

        def apply(self, state):
            self.calls += 1
            value = state.get("value", 0)
            return {**state, "value": value + 1}

    inc = Incrementer()
    inc_rule = rule(
        "bound-increment",
        inc.apply,
        guard=lambda state, ctx: state.get("value", 0) < 2,
        until=lambda state, ctx: state.get("value", 0) >= 2,
    )

    universe = God.universe(state={"value": 0}, rules=[inc_rule])
    result = fixpoint(
        universe,
        metric=lambda a, b: abs(a.get("value", 0) - b.get("value", 0)),
        epsilon=0,
        max_epoch=5,
    )

    assert result.converged is True
    assert result.universe.state["value"] == 2
    assert inc.calls >= 1


def test_rule_accepts_partial():
    def set_value(target, state):
        return {**state, "value": target}

    set_to_three = functools.partial(set_value, 3)
    partial_rule = rule("partial-set", set_to_three)

    universe = God.universe(state={"value": 0}, rules=[partial_rule])
    result = fixpoint(
        universe,
        metric=lambda a, b: abs(a.get("value", 0) - b.get("value", 0)),
        epsilon=0,
        max_epoch=2,
    )

    assert result.converged is True
    assert result.universe.state["value"] == 3


def test_recursive_descent_fixpoint_matches_iterative():
    target = 5

    def increment(state):
        value = state.get("counter", 0)
        return {**state, "counter": min(value + 1, target)}

    def universe_factory():
        return God.universe(state={"counter": 0}, rules=[rule("increment", increment)])

    kwargs = dict(
        metric=lambda a, b: abs(a.get("counter", 0) - b.get("counter", 0)),
        epsilon=0,
        max_epoch=10,
    )

    recursive_result = recursive_descent_fixpoint(universe_factory(), **kwargs)
    iterative_result = fixpoint(universe_factory(), **kwargs)

    assert recursive_result.converged is iterative_result.converged is True
    assert recursive_result.universe.state == iterative_result.universe.state == {"counter": target}
    assert recursive_result.epochs == iterative_result.epochs
