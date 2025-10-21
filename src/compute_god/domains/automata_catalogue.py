"""A small catalogue of classic automata implementations.

The project receives frequent questions about *how* one could experiment with
different flavours of automata without diving into domain-specific reference
implementations.  This module provides compact, well documented Python
implementations of the most approachable machines from the user's extensive
list: deterministic and non-deterministic finite automata, ε-automata,
probabilistic and weighted automata, several pushdown variants, and a handful
of Turing-machine style models including a linear bounded automaton and a
multi-tape machine.

The goal is to offer batteries-included simulation helpers that trade raw
performance for clarity and strong validation.  Each class exposes a dedicated
``accepts`` (or ``acceptance_probability`` / ``weight_of``) method so that
callers can run quick experiments without pulling in third-party packages.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, MutableMapping, Optional, Sequence, Tuple


Symbol = Optional[str]


class AutomatonError(ValueError):
    """Raised when an automaton is constructed with inconsistent data."""


@dataclass(frozen=True)
class DeterministicFiniteAutomaton:
    """Minimal DFA simulator for educational experiments."""

    states: frozenset[str]
    alphabet: frozenset[str]
    transitions: Mapping[Tuple[str, str], str]
    initial_state: str
    accepting_states: frozenset[str]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if self.initial_state not in self.states:
            raise AutomatonError("initial state must belong to states")
        if not self.accepting_states <= self.states:
            raise AutomatonError("accepting states must be subset of states")
        for (state, symbol), target in self.transitions.items():
            if state not in self.states or target not in self.states:
                raise AutomatonError("transition references unknown state")
            if symbol not in self.alphabet:
                raise AutomatonError("transition references unknown symbol")

    def accepts(self, word: Sequence[str]) -> bool:
        state = self.initial_state
        for symbol in word:
            if symbol not in self.alphabet:
                raise AutomatonError(f"symbol {symbol!r} not in alphabet")
            try:
                state = self.transitions[(state, symbol)]
            except KeyError:  # pragma: no cover - guard rail
                raise AutomatonError("missing deterministic transition") from None
        return state in self.accepting_states


@dataclass(frozen=True)
class NondeterministicFiniteAutomaton:
    """Small-step simulator for an NFA without ε-transitions."""

    states: frozenset[str]
    alphabet: frozenset[str]
    transitions: Mapping[Tuple[str, str], frozenset[str]]
    initial_states: frozenset[str]
    accepting_states: frozenset[str]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if not self.initial_states <= self.states:
            raise AutomatonError("initial states must be subset of states")
        if not self.accepting_states <= self.states:
            raise AutomatonError("accepting states must be subset of states")
        for (state, symbol), targets in self.transitions.items():
            if state not in self.states or not targets <= self.states:
                raise AutomatonError("transition references unknown state")
            if symbol not in self.alphabet:
                raise AutomatonError("transition references unknown symbol")

    def accepts(self, word: Sequence[str]) -> bool:
        current_states = set(self.initial_states)
        for symbol in word:
            if symbol not in self.alphabet:
                raise AutomatonError(f"symbol {symbol!r} not in alphabet")
            next_states: set[str] = set()
            for state in current_states:
                next_states.update(self.transitions.get((state, symbol), ()))
            current_states = next_states
            if not current_states:
                return False
        return any(state in self.accepting_states for state in current_states)


@dataclass(frozen=True)
class EpsilonNFA(NondeterministicFiniteAutomaton):
    """NFA variant that supports ε-transitions via ``None`` symbols."""

    epsilon_transitions: Mapping[str, frozenset[str]]

    def __post_init__(self) -> None:  # pragma: no cover - validation guard
        super().__post_init__()
        if not set(self.epsilon_transitions).issubset(self.states):
            raise AutomatonError("ε-transition references unknown state")
        for targets in self.epsilon_transitions.values():
            if not targets <= self.states:
                raise AutomatonError("ε-transition targets must be known states")

    def _epsilon_closure(self, states: Iterable[str]) -> frozenset[str]:
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for target in self.epsilon_transitions.get(state, ()):  # type: ignore[arg-type]
                if target not in closure:
                    closure.add(target)
                    stack.append(target)
        return frozenset(closure)

    def accepts(self, word: Sequence[str]) -> bool:
        current_states = set(self._epsilon_closure(self.initial_states))
        for symbol in word:
            if symbol not in self.alphabet:
                raise AutomatonError(f"symbol {symbol!r} not in alphabet")
            next_states: set[str] = set()
            for state in current_states:
                targets = self.transitions.get((state, symbol), ())
                if targets:
                    next_states.update(self._epsilon_closure(targets))
            current_states = next_states
            if not current_states:
                return False
        return any(state in self.accepting_states for state in current_states)


@dataclass(frozen=True)
class ProbabilisticFiniteAutomaton:
    """Return acceptance probability by summing over weighted paths."""

    states: frozenset[str]
    alphabet: frozenset[str]
    transitions: Mapping[Tuple[str, str], Mapping[str, float]]
    initial_state: str
    accepting_states: frozenset[str]

    def __post_init__(self) -> None:  # pragma: no cover - validation guard
        if self.initial_state not in self.states:
            raise AutomatonError("initial state must belong to states")
        if not self.accepting_states <= self.states:
            raise AutomatonError("accepting states must be subset of states")
        for (state, symbol), mapping in self.transitions.items():
            if state not in self.states:
                raise AutomatonError("transition references unknown state")
            if symbol not in self.alphabet:
                raise AutomatonError("transition references unknown symbol")
            for target, probability in mapping.items():
                if target not in self.states:
                    raise AutomatonError("transition targets unknown state")
                if probability < 0:
                    raise AutomatonError("probabilities must be non-negative")

    def acceptance_probability(self, word: Sequence[str]) -> float:
        distribution: Dict[str, float] = {self.initial_state: 1.0}
        for symbol in word:
            if symbol not in self.alphabet:
                raise AutomatonError(f"symbol {symbol!r} not in alphabet")
            next_distribution: Dict[str, float] = {}
            for state, prob in distribution.items():
                for target, weight in self.transitions.get((state, symbol), {}).items():
                    next_distribution[target] = next_distribution.get(target, 0.0) + prob * weight
            distribution = next_distribution
            if not distribution:
                return 0.0
        return sum(prob for state, prob in distribution.items() if state in self.accepting_states)


@dataclass(frozen=True)
class WeightedFiniteAutomaton:
    """Compute the total weight of all accepting paths over a semiring."""

    states: frozenset[str]
    alphabet: frozenset[str]
    transitions: Mapping[Tuple[str, str], Mapping[str, float]]
    initial_states: Mapping[str, float]
    accepting_states: Mapping[str, float]

    def __post_init__(self) -> None:  # pragma: no cover - validation guard
        if not set(self.initial_states).issubset(self.states):
            raise AutomatonError("initial states must be subset of states")
        if not set(self.accepting_states).issubset(self.states):
            raise AutomatonError("accepting states must be subset of states")
        for (state, symbol), mapping in self.transitions.items():
            if state not in self.states:
                raise AutomatonError("transition references unknown state")
            if symbol not in self.alphabet:
                raise AutomatonError("transition references unknown symbol")
            if not set(mapping).issubset(self.states):
                raise AutomatonError("transition targets must be known states")

    def weight_of(self, word: Sequence[str]) -> float:
        weights: Dict[str, float] = dict(self.initial_states)
        for symbol in word:
            if symbol not in self.alphabet:
                raise AutomatonError(f"symbol {symbol!r} not in alphabet")
            next_weights: Dict[str, float] = {}
            for state, weight in weights.items():
                for target, transition_weight in self.transitions.get((state, symbol), {}).items():
                    next_weights[target] = next_weights.get(target, 0.0) + weight * transition_weight
            weights = next_weights
            if not weights:
                return 0.0
        return sum(weight * self.accepting_states[state] for state, weight in weights.items() if state in self.accepting_states)


StackSymbol = str


@dataclass
class PushdownAutomaton:
    """General-purpose PDA that supports ε-transitions."""

    states: frozenset[str]
    input_alphabet: frozenset[str]
    stack_alphabet: frozenset[StackSymbol]
    transitions: Mapping[Tuple[str, Optional[str], StackSymbol], frozenset[Tuple[str, Tuple[StackSymbol, ...]]]]
    initial_state: str
    initial_stack_symbol: StackSymbol
    accepting_states: frozenset[str]

    def __post_init__(self) -> None:  # pragma: no cover - validation guard
        if self.initial_state not in self.states:
            raise AutomatonError("initial state must belong to states")
        if self.initial_stack_symbol not in self.stack_alphabet:
            raise AutomatonError("initial stack symbol must belong to stack alphabet")
        if not self.accepting_states <= self.states:
            raise AutomatonError("accepting states must be subset of states")
        for (state, symbol, stack_symbol), targets in self.transitions.items():
            if state not in self.states:
                raise AutomatonError("transition references unknown state")
            if symbol is not None and symbol not in self.input_alphabet:
                raise AutomatonError("transition references unknown input symbol")
            if stack_symbol not in self.stack_alphabet:
                raise AutomatonError("transition references unknown stack symbol")
            for target_state, push_symbols in targets:
                if target_state not in self.states:
                    raise AutomatonError("transition target must be known state")
                if not set(push_symbols).issubset(self.stack_alphabet):
                    raise AutomatonError("push string must use stack alphabet symbols")

    def accepts(self, word: Sequence[str], *, max_steps: int = 1024) -> bool:
        queue: deque[Tuple[str, int, Tuple[StackSymbol, ...]]] = deque()
        queue.append((self.initial_state, 0, (self.initial_stack_symbol,)))
        visited: set[Tuple[str, int, Tuple[StackSymbol, ...]]] = set()
        steps = 0

        while queue and steps < max_steps:
            state, index, stack = queue.popleft()
            steps += 1
            configuration = (state, index, stack)
            if configuration in visited:
                continue
            visited.add(configuration)

            if index == len(word) and state in self.accepting_states:
                return True

            stack_top = stack[-1] if stack else None
            if stack_top is None:
                continue

            for input_symbol in (None, word[index] if index < len(word) else None):
                if input_symbol is None:
                    next_index = index
                else:
                    if input_symbol not in self.input_alphabet or index >= len(word):
                        continue
                    if word[index] != input_symbol:
                        continue
                    next_index = index + 1
                for next_state, push_symbols in self.transitions.get((state, input_symbol, stack_top), ()):  # type: ignore[arg-type]
                    next_stack = list(stack[:-1])
                    next_stack.extend(push_symbols)
                    queue.append((next_state, next_index, tuple(next_stack)))
        return False


class DeterministicPushdownAutomaton(PushdownAutomaton):
    """Pushdown automaton that ensures determinism at construction time."""

    def __post_init__(self) -> None:  # pragma: no cover - validation guard
        super().__post_init__()
        seen: set[Tuple[str, Optional[str], StackSymbol]] = set()
        for key, targets in self.transitions.items():
            if len(targets) > 1:
                raise AutomatonError("deterministic PDA cannot branch")
            if key in seen:
                raise AutomatonError("duplicate transition in deterministic PDA")
            seen.add(key)


class LinearBoundedAutomatonError(RuntimeError):
    """Raised when an LBA attempts to move beyond its fixed tape bounds."""


Move = str  # 'L', 'R', or 'S'


@dataclass
class TuringMachine:
    """Deterministic, single-tape Turing machine simulator."""

    states: frozenset[str]
    tape_alphabet: frozenset[str]
    blank_symbol: str
    transitions: Mapping[Tuple[str, str], Tuple[str, str, Move]]
    initial_state: str
    accepting_states: frozenset[str]
    rejecting_states: frozenset[str]

    def __post_init__(self) -> None:  # pragma: no cover - validation guard
        if self.blank_symbol not in self.tape_alphabet:
            raise AutomatonError("blank symbol must belong to tape alphabet")
        if self.initial_state not in self.states:
            raise AutomatonError("initial state must belong to states")
        if not self.accepting_states <= self.states:
            raise AutomatonError("accepting states must be subset of states")
        if not self.rejecting_states <= self.states:
            raise AutomatonError("rejecting states must be subset of states")
        for (state, symbol), result in self.transitions.items():
            if state not in self.states or result[0] not in self.states:
                raise AutomatonError("transition references unknown state")
            if symbol not in self.tape_alphabet or result[1] not in self.tape_alphabet:
                raise AutomatonError("transition uses unknown tape symbol")
            if result[2] not in {"L", "R", "S"}:
                raise AutomatonError("move must be 'L', 'R', or 'S'")

    def _initial_tape(self, word: Sequence[str]) -> MutableMapping[int, str]:
        tape: MutableMapping[int, str] = {}
        for index, symbol in enumerate(word):
            if symbol not in self.tape_alphabet:
                raise AutomatonError(f"symbol {symbol!r} not on tape alphabet")
            tape[index] = symbol
        return tape

    def run(self, word: Sequence[str], *, max_steps: int = 2048) -> bool:
        tape = self._initial_tape(word)
        head = 0
        state = self.initial_state
        steps = 0

        while steps < max_steps:
            if state in self.accepting_states:
                return True
            if state in self.rejecting_states:
                return False

            symbol = tape.get(head, self.blank_symbol)
            try:
                next_state, write_symbol, move = self.transitions[(state, symbol)]
            except KeyError:
                return False

            tape[head] = write_symbol
            if move == "L":
                head -= 1
            elif move == "R":
                head += 1
            state = next_state
            steps += 1
        raise RuntimeError("maximum number of steps exceeded")


@dataclass
class LinearBoundedAutomaton(TuringMachine):
    """Turing machine constrained to the input's length."""

    def run(self, word: Sequence[str], *, max_steps: int = 2048) -> bool:
        tape = self._initial_tape(word)
        head = 0
        state = self.initial_state
        left_boundary = 0
        right_boundary = len(word) - 1 if word else -1
        steps = 0

        while steps < max_steps:
            if state in self.accepting_states:
                return True
            if state in self.rejecting_states:
                return False

            symbol = tape.get(head, self.blank_symbol)
            try:
                next_state, write_symbol, move = self.transitions[(state, symbol)]
            except KeyError:
                return False

            tape[head] = write_symbol
            if move == "L":
                if head == left_boundary:
                    raise LinearBoundedAutomatonError("attempted to move beyond left boundary")
                head -= 1
            elif move == "R":
                if head == right_boundary:
                    raise LinearBoundedAutomatonError("attempted to move beyond right boundary")
                head += 1
            state = next_state
            steps += 1
        raise RuntimeError("maximum number of steps exceeded")


@dataclass
class MultiTapeTuringMachine:
    """Deterministic Turing machine with an arbitrary number of tapes."""

    states: frozenset[str]
    tape_alphabet: frozenset[str]
    blank_symbol: str
    transitions: Mapping[Tuple[str, Tuple[str, ...]], Tuple[str, Tuple[str, ...], Tuple[Move, ...]]]
    initial_state: str
    accepting_states: frozenset[str]
    rejecting_states: frozenset[str]
    tapes: int

    def __post_init__(self) -> None:  # pragma: no cover - validation guard
        if self.tapes < 1:
            raise AutomatonError("multi-tape machine must have at least one tape")
        if self.blank_symbol not in self.tape_alphabet:
            raise AutomatonError("blank symbol must belong to tape alphabet")
        if self.initial_state not in self.states:
            raise AutomatonError("initial state must belong to states")
        if not self.accepting_states <= self.states:
            raise AutomatonError("accepting states must be subset of states")
        if not self.rejecting_states <= self.states:
            raise AutomatonError("rejecting states must be subset of states")
        for (state, symbols), result in self.transitions.items():
            if state not in self.states or result[0] not in self.states:
                raise AutomatonError("transition references unknown state")
            if len(symbols) != self.tapes or len(result[1]) != self.tapes or len(result[2]) != self.tapes:
                raise AutomatonError("transition arity must match number of tapes")
            if not set(symbols).issubset(self.tape_alphabet) or not set(result[1]).issubset(self.tape_alphabet):
                raise AutomatonError("transition uses unknown tape symbol")
            for move in result[2]:
                if move not in {"L", "R", "S"}:
                    raise AutomatonError("move must be 'L', 'R', or 'S'")

    def run(self, word: Sequence[str], *, max_steps: int = 2048) -> bool:
        tapes: list[MutableMapping[int, str]] = [{} for _ in range(self.tapes)]
        for index, symbol in enumerate(word):
            if symbol not in self.tape_alphabet:
                raise AutomatonError(f"symbol {symbol!r} not on tape alphabet")
            tapes[0][index] = symbol
        heads = [0 for _ in range(self.tapes)]
        state = self.initial_state
        steps = 0

        while steps < max_steps:
            if state in self.accepting_states:
                return True
            if state in self.rejecting_states:
                return False

            symbols = tuple(tape.get(head, self.blank_symbol) for tape, head in zip(tapes, heads))
            try:
                next_state, write_symbols, moves = self.transitions[(state, symbols)]
            except KeyError:
                return False

            for tape, head, symbol in zip(tapes, heads, write_symbols):
                tape[head] = symbol
            for index, move in enumerate(moves):
                if move == "L":
                    heads[index] -= 1
                elif move == "R":
                    heads[index] += 1
            state = next_state
            steps += 1
        raise RuntimeError("maximum number of steps exceeded")


__all__ = [
    "AutomatonError",
    "DeterministicFiniteAutomaton",
    "NondeterministicFiniteAutomaton",
    "EpsilonNFA",
    "ProbabilisticFiniteAutomaton",
    "WeightedFiniteAutomaton",
    "PushdownAutomaton",
    "DeterministicPushdownAutomaton",
    "LinearBoundedAutomaton",
    "LinearBoundedAutomatonError",
    "TuringMachine",
    "MultiTapeTuringMachine",
]
