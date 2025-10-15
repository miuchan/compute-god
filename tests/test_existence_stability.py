from compute_god import ExistenceWitness, StabilityWitness, 存在子, 稳定子


def test_existence_witness_records_first_satisfying_state():
    witness = ExistenceWitness(lambda state: state.get("value", 0) >= 3)

    assert witness.observe({"value": 1}) is False
    assert witness.observe({"value": 2}) is False

    assert witness.exists is False

    assert witness.observe({"value": 3}) is True
    assert witness.exists is True
    assert witness.witness_state() == {"value": 3}

    # Additional observations do not replace the first witness.
    witness.observe({"value": 5})
    assert witness.witness_state() == {"value": 3}


def test_stability_witness_detects_monotone_convergence():
    metric = lambda a, b: abs(a.get("value", 0.0) - b.get("value", 0.0))
    stabiliser = StabilityWitness(metric, epsilon=0.1)

    assert stabiliser.observe({"value": 0.0}) == 0.0
    assert stabiliser.observe({"value": 0.5}) == 0.5
    assert stabiliser.observe({"value": 0.75}) == 0.25
    assert stabiliser.observe({"value": 0.875}) == 0.125

    assert stabiliser.is_monotone is True
    assert stabiliser.is_stable is False

    assert stabiliser.observe({"value": 0.9375}) == 0.0625

    assert stabiliser.is_stable is True
    assert stabiliser.stable_epoch == 4


def test_chinese_aliases_reference_same_classes():
    assert 存在子 is ExistenceWitness
    assert 稳定子 is StabilityWitness
