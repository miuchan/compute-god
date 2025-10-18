"""High level sanity tests for the automata catalogue."""

from compute_god.automata_catalogue import (
    AutomatonError,
    DeterministicFiniteAutomaton,
    DeterministicPushdownAutomaton,
    EpsilonNFA,
    LinearBoundedAutomaton,
    LinearBoundedAutomatonError,
    MultiTapeTuringMachine,
    NondeterministicFiniteAutomaton,
    ProbabilisticFiniteAutomaton,
    PushdownAutomaton,
    TuringMachine,
    WeightedFiniteAutomaton,
)


def test_dfa_accepts_even_zero_language() -> None:
    dfa = DeterministicFiniteAutomaton(
        states=frozenset({"even", "odd"}),
        alphabet=frozenset({"0", "1"}),
        transitions={
            ("even", "0"): "odd",
            ("even", "1"): "even",
            ("odd", "0"): "even",
            ("odd", "1"): "odd",
        },
        initial_state="even",
        accepting_states=frozenset({"even"}),
    )
    assert dfa.accepts("0101")
    assert not dfa.accepts("000")


def test_nfa_matches_strings_ending_with_ab() -> None:
    nfa = NondeterministicFiniteAutomaton(
        states=frozenset({"start", "seen_a", "accept"}),
        alphabet=frozenset({"a", "b"}),
        transitions={
            ("start", "a"): frozenset({"start", "seen_a"}),
            ("start", "b"): frozenset({"start"}),
            ("seen_a", "b"): frozenset({"accept"}),
        },
        initial_states=frozenset({"start"}),
        accepting_states=frozenset({"accept"}),
    )
    assert nfa.accepts("aaab")
    assert not nfa.accepts("aba")


def test_epsilon_nfa_handles_empty_string() -> None:
    enfa = EpsilonNFA(
        states=frozenset({"start", "accept"}),
        alphabet=frozenset({"a"}),
        transitions={
            ("start", "a"): frozenset({"accept"}),
        },
        initial_states=frozenset({"start"}),
        accepting_states=frozenset({"accept"}),
        epsilon_transitions={"start": frozenset({"accept"})},
    )
    assert enfa.accepts("")
    assert enfa.accepts("a")
    assert not enfa.accepts("aa")


def test_probabilistic_finite_automaton_returns_acceptance_probability() -> None:
    pfa = ProbabilisticFiniteAutomaton(
        states=frozenset({"start", "accept"}),
        alphabet=frozenset({"0"}),
        transitions={
            ("start", "0"): {"accept": 0.5, "start": 0.5},
            ("accept", "0"): {"accept": 1.0},
        },
        initial_state="start",
        accepting_states=frozenset({"accept"}),
    )
    assert abs(pfa.acceptance_probability("0") - 0.5) < 1e-9
    assert abs(pfa.acceptance_probability("00") - 0.75) < 1e-9


def test_weighted_finite_automaton_combines_path_weights() -> None:
    wfa = WeightedFiniteAutomaton(
        states=frozenset({"start", "mid", "accept"}),
        alphabet=frozenset({"x"}),
        transitions={
            ("start", "x"): {"mid": 0.3, "accept": 0.2},
            ("mid", "x"): {"accept": 2.0},
        },
        initial_states={"start": 1.0},
        accepting_states={"accept": 1.0},
    )
    assert abs(wfa.weight_of("x") - 0.2) < 1e-9
    assert abs(wfa.weight_of("xx") - 0.6) < 1e-9


def test_pushdown_automaton_recognises_an_bn() -> None:
    pda = PushdownAutomaton(
        states=frozenset({"start", "read_b", "accept"}),
        input_alphabet=frozenset({"a", "b"}),
        stack_alphabet=frozenset({"Z", "A"}),
        transitions={
            ("start", "a", "Z"): frozenset({("start", ("Z", "A"))}),
            ("start", "a", "A"): frozenset({("start", ("A", "A"))}),
            ("start", "b", "A"): frozenset({("read_b", ())}),
            ("read_b", "b", "A"): frozenset({("read_b", ())}),
            ("read_b", None, "Z"): frozenset({("accept", ("Z",))}),
        },
        initial_state="start",
        initial_stack_symbol="Z",
        accepting_states=frozenset({"accept"}),
    )
    assert pda.accepts("aabb")
    assert not pda.accepts("aaab")


def test_deterministic_pushdown_detects_duplicate_transitions() -> None:
    try:
        DeterministicPushdownAutomaton(
            states=frozenset({"q0"}),
            input_alphabet=frozenset({"a"}),
            stack_alphabet=frozenset({"Z"}),
            transitions={
                ("q0", "a", "Z"): frozenset({("q0", ("Z",)), ("q0", ("Z", "Z"))}),
            },
            initial_state="q0",
            initial_stack_symbol="Z",
            accepting_states=frozenset({"q0"}),
        )
    except AutomatonError:
        pass
    else:
        assert False, "deterministic PDA should raise if constructed successfully"


def test_turing_machine_accepts_input_with_a_one() -> None:
    tm = TuringMachine(
        states=frozenset({"start", "accept", "reject", "scan"}),
        tape_alphabet=frozenset({"0", "1", "_"}),
        blank_symbol="_",
        transitions={
            ("start", "0"): ("start", "0", "R"),
            ("start", "1"): ("accept", "1", "S"),
            ("start", "_"): ("reject", "_", "S"),
        },
        initial_state="start",
        accepting_states=frozenset({"accept"}),
        rejecting_states=frozenset({"reject"}),
    )
    assert tm.run("0010")
    assert not tm.run("000")


def test_linear_bounded_automaton_rejects_out_of_bounds_move() -> None:
    lba = LinearBoundedAutomaton(
        states=frozenset({"start", "accept", "reject"}),
        tape_alphabet=frozenset({"a", "b", "_"}),
        blank_symbol="_",
        transitions={
            ("start", "a"): ("start", "a", "R"),
            ("start", "b"): ("accept", "b", "S"),
        },
        initial_state="start",
        accepting_states=frozenset({"accept"}),
        rejecting_states=frozenset({"reject"}),
    )
    assert lba.run("ab")
    try:
        lba.run("aa")
    except LinearBoundedAutomatonError:
        pass
    else:
        assert False, "LBA should raise when attempting to move beyond the boundary"


def test_multi_tape_turing_machine_copies_symbol() -> None:
    mttm = MultiTapeTuringMachine(
        states=frozenset({"start", "copy", "accept", "reject"}),
        tape_alphabet=frozenset({"0", "1", "_"}),
        blank_symbol="_",
        transitions={
            ("start", ("1", "_")): ("accept", ("1", "1"), ("S", "S")),
            ("start", ("_", "_")): ("reject", ("_", "_"), ("S", "S")),
        },
        initial_state="start",
        accepting_states=frozenset({"accept"}),
        rejecting_states=frozenset({"reject"}),
        tapes=2,
    )
    assert mttm.run("1")
    assert not mttm.run("")

