"""Lightweight command interpreter for Earth Online scripts.

This module implements a very small command interpreter that can execute
scripts composed of whitespace separated tokens.  Each non-empty line is
interpreted as a command invocation where the first token is the command
name, positional arguments follow and keyword arguments are written in the
``key=value`` form.  Values are automatically coerced from strings to
``int``/``float``/``bool``/``None`` when possible.

Example
-------
>>> interpreter = CommandInterpreter()
>>> @interpreter.command()
... def remember(ctx, key, value):
...     ctx[key] = value
...     return f"remembered {key}"
>>> @interpreter.command()
... def recall(ctx, key):
...     return ctx.get(key, "")
>>> script = '''
... # store value
... remember answer 42
... recall answer
... '''
>>> result = interpreter.run(script)
>>> result.outputs[-1]
'42'

The interpreter stores all state in a simple dictionary so callers can
inspect the resulting context after running a script.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional


__all__ = [
    "CommandInterpreter",
    "InterpreterError",
    "UnknownCommandError",
    "InterpreterResult",
]


class InterpreterError(RuntimeError):
    """Base class for interpreter errors."""


class UnknownCommandError(InterpreterError):
    """Raised when a script references an unknown command."""

    def __init__(self, command: str, *, line: int):
        super().__init__(f"Unknown command '{command}' on line {line}")
        self.command = command
        self.line = line


@dataclass(slots=True)
class InterpreterResult:
    """Result produced after executing a script."""

    context: Dict[str, Any] = field(default_factory=dict)
    outputs: List[Any] = field(default_factory=list)


CommandFunc = Callable[..., Any]


class CommandInterpreter:
    """A minimal command interpreter.

    Commands are regular callables that accept a context dictionary as the
    first positional argument.  Positional and keyword arguments from the
    script are forwarded to the command as normal Python values.
    """

    def __init__(self) -> None:
        self._commands: Dict[str, CommandFunc] = {}

    # ------------------------------------------------------------------
    # Command registration helpers
    # ------------------------------------------------------------------
    def register(self, name: str, func: CommandFunc) -> CommandFunc:
        """Register *func* under *name*.

        Parameters
        ----------
        name:
            Identifier used in scripts.
        func:
            Callable that accepts a context dictionary as its first positional
            argument.
        """

        self._commands[name] = func
        return func

    def command(self, name: Optional[str] = None) -> Callable[[CommandFunc], CommandFunc]:
        """Decorator variant of :meth:`register`."""

        def decorator(func: CommandFunc) -> CommandFunc:
            self.register(name or func.__name__, func)
            return func

        return decorator

    # ------------------------------------------------------------------
    # Script execution
    # ------------------------------------------------------------------
    def run(
        self,
        script: Iterable[str] | str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> InterpreterResult:
        """Execute *script* and return the resulting context and outputs."""

        ctx = dict(context or {})
        outputs: List[Any] = []

        for line_no, (command, args, kwargs) in enumerate(
            self._parse(script), start=1
        ):
            func = self._commands.get(command)
            if func is None:
                raise UnknownCommandError(command, line=line_no)

            result = func(ctx, *args, **kwargs)
            if result is not None:
                outputs.append(result)

        return InterpreterResult(context=ctx, outputs=outputs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _parse(self, script: Iterable[str] | str) -> Iterator[tuple[str, list[Any], dict[str, Any]]]:
        lines = script.splitlines() if isinstance(script, str) else list(script)
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            tokens = shlex.split(stripped)
            if not tokens:
                continue

            command = tokens[0]
            args: List[Any] = []
            kwargs: Dict[str, Any] = {}
            for token in tokens[1:]:
                if "=" in token:
                    key, value = token.split("=", 1)
                    kwargs[key] = self._coerce(value)
                else:
                    args.append(self._coerce(token))
            yield command, args, kwargs

    @staticmethod
    def _coerce(value: str) -> Any:
        lowered = value.lower()
        if lowered == "none":
            return None
        if lowered == "true":
            return True
        if lowered == "false":
            return False

        for caster in (int, float):
            try:
                return caster(value)
            except ValueError:
                continue

        return value

