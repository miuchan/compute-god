import pytest

from compute_god import DegreeSpace, tensor_product


def test_dual_evaluates_against_mapping():
    space = DegreeSpace({"alpha": 0.7, "beta": -0.25})
    dual = space.dual()

    value = dual({"alpha": 3.0, "beta": 1.5, "gamma": 42})
    assert value == pytest.approx(0.7 * 3.0 + (-0.25) * 1.5)


def test_negative_dual_flips_orientation():
    space = DegreeSpace({"x": 0.3, "y": 0.9})
    dual = space.dual()
    negative = space.negative_dual()

    vector = {"x": 2.0, "y": -1.0}
    assert negative(vector) == pytest.approx(-dual(vector))


def test_tensor_product_combines_dual_and_negative_dual():
    left_space = DegreeSpace({"u": 0.5, "v": -0.3})
    right_space = DegreeSpace({"x": -0.2, "y": 0.4})

    tensor = tensor_product(left_space.dual(), right_space.negative_dual())

    left_vector = {"u": 1.2, "v": 0.5}
    right_vector = {"x": -0.5, "y": 0.8}

    expected = left_space.dual()(left_vector) * right_space.negative_dual()(right_vector)
    assert tensor(left_vector, right_vector) == pytest.approx(expected)

    # DegreeSpace instances should be accepted directly as well.
    expected_self = left_space.dual()(left_space) * right_space.negative_dual()(right_space)
    assert tensor(left_space, right_space) == pytest.approx(expected_self)

