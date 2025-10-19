import pytest

from compute_god import parse_limit_language


def test_limit_language_supports_uniform_convergence():
    source = """
    # simple contraction
    function f(n, x) = x / (n + 1)
    limit n -> infinity of f(n, x) = 0; uniform on [0, 1]; samples=6; tolerance=1e-4; steps=15
    """

    program = parse_limit_language(source)
    assert tuple(program.functions) == ("f",)
    result = program.verify()[0]

    assert result.converged is True
    assert result.statement.mode == "uniform"
    assert result.samples_evaluated == 6
    assert result.max_error <= result.statement.tolerance + 1e-12

    evaluated = program.evaluate_function("f", n=9, x=0.5)
    assert evaluated == pytest.approx(0.5 / 10)


def test_limit_language_accepts_chinese_keywords():
    source = """
    函数 g(x) = sin(x) / x
    极限 x -> 0 的 g(x) = 1; 容差=1e-3; 步数=18
    """

    program = parse_limit_language(source)
    result = program.verify()[0]

    assert result.converged is True
    assert result.statement.mode == "pointwise"
    assert result.max_error <= 1e-3
    assert result.steps_used >= 1


def test_limit_language_detects_incorrect_limit():
    source = """
    function h(n) = 1 / (n + 1)
    limit n -> infinity of h(n) = 1; tolerance=1e-6; steps=5
    """

    program = parse_limit_language(source)
    result = program.verify()[0]

    assert result.converged is False
    assert result.steps_used == result.statement.max_steps
    assert result.max_error > result.statement.tolerance
