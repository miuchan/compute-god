from __future__ import annotations

import pytest

from compute_god.interpreter import (
    CommandInterpreter,
    InterpreterResult,
    UnknownCommandError,
)


@pytest.fixture()
def interpreter() -> CommandInterpreter:
    interp = CommandInterpreter()

    @interp.command()
    def store(ctx, key, value):
        ctx[key] = value

    @interp.command()
    def emit(ctx, key):
        return ctx[key]

    @interp.command()
    def combine(ctx, left, right, sep=" "):
        return f"{left}{sep}{right}"

    return interp


def test_run_script_returns_context_and_outputs(interpreter: CommandInterpreter) -> None:
    script = """
    # store something
    store answer 42
    emit answer
    combine hello world sep=,
    """

    result = interpreter.run(script)

    assert isinstance(result, InterpreterResult)
    assert result.context == {"answer": 42}
    assert result.outputs == [42, "hello,world"]


def test_unknown_command_raises(interpreter: CommandInterpreter) -> None:
    with pytest.raises(UnknownCommandError) as excinfo:
        interpreter.run("missing_command")

    assert excinfo.value.command == "missing_command"


def test_context_can_be_seeded(interpreter: CommandInterpreter) -> None:
    result = interpreter.run("emit seed", context={"seed": "value"})

    assert result.outputs == ["value"]
    assert result.context["seed"] == "value"


def test_literal_coercion_handles_bool_and_none(interpreter: CommandInterpreter) -> None:
    result = interpreter.run(
        """
        store truth true
        store lie false
        store empty none
        """
    )

    assert result.context["truth"] is True
    assert result.context["lie"] is False
    assert result.context["empty"] is None


