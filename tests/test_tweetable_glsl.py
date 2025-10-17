from __future__ import annotations

import math

import pytest

from compute_god.tweetable_glsl import ShaderInput, iterate_shader_field


def test_iterate_shader_field_matches_reference_values() -> None:
    inputs = ShaderInput(time=1.234, fragment_coord=(0.1, -0.2), resolution=(0.75, 1.5))
    output = iterate_shader_field(inputs)

    assert output == pytest.approx(
        (
            0.000592749031084751,
            0.0020335659159909187,
            0.000594557047543801,
            0.000594557047543801,
        ),
        rel=1e-9,
    )


def test_iterate_shader_field_supports_custom_iterations() -> None:
    inputs = ShaderInput(time=0.5, fragment_coord=(0.0, 0.0), resolution=(1.0, 2.0), iterations=5)
    output = iterate_shader_field(inputs)

    assert output == pytest.approx(
        (
            0.00037241456081686544,
            4.373513309657947e-05,
            0.0006993040150373966,
            0.0006993040150373966,
        ),
        rel=1e-9,
    )


def test_shader_input_validates_resolution_and_iterations() -> None:
    with pytest.raises(ValueError):
        ShaderInput(time=0.0, fragment_coord=(0.0, 0.0), resolution=(1.0, 0.0))

    with pytest.raises(ValueError):
        ShaderInput(time=0.0, fragment_coord=(0.0, 0.0), resolution=(1.0, 1.0), iterations=0)
