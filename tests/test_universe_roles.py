from compute_god.rule import rule
from compute_god.universe import God


def test_rules_by_role_filters_and_preserves_priority_order() -> None:
    high_priority = rule("high", lambda state: state, priority=10, role="oracle")
    low_priority = rule("low", lambda state: state, priority=1, role="oracle")
    other_role = rule("other", lambda state: state, priority=5, role="observer")

    universe = God.universe(state={}, rules=[high_priority, low_priority, other_role])

    oracle_rules = universe.rules_by_role("oracle")

    assert oracle_rules == [high_priority, low_priority]

    all_rules = universe.rules_by_role(None)
    assert all_rules == [high_priority, other_role, low_priority]
