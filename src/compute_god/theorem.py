from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Iterator, List, MutableMapping, Optional, Sequence, Set, Tuple

from .core import FixpointResult, God, Observer, RuleContext, State, Universe, fixpoint, rule

Statement = str
Premises = Tuple[Statement, ...]
InferenceFn = Callable[[Set[Statement]], Iterable[Tuple[Statement, Premises]]]


@dataclass(frozen=True)
class ProofTrace:
    """Internal bookkeeping structure capturing how a statement was derived."""

    rule: str
    premises: Premises


@dataclass(frozen=True)
class ProofStep:
    """A single step in a reconstructed proof."""

    statement: Statement
    rule: str
    premises: Premises


@dataclass(frozen=True)
class Proof:
    """A structured proof for a particular goal statement."""

    goal: Statement
    steps: Tuple[ProofStep, ...]


@dataclass(frozen=True)
class InferenceRule:
    """Declarative description of how new statements may be inferred."""

    name: str
    inference: InferenceFn

    def infer(self, known: Set[Statement]) -> Iterable[Tuple[Statement, Premises]]:
        return self.inference(known)


def _parse_implication(statement: Statement) -> Optional[Tuple[Statement, Statement]]:
    if "->" not in statement:
        return None

    antecedent, consequent = statement.split("->", 1)
    antecedent = antecedent.strip()
    consequent = consequent.strip()
    if not antecedent or not consequent:
        return None
    return antecedent, consequent


def modus_ponens(name: str = "modus-ponens") -> InferenceRule:
    """Construct a standard modus ponens inference rule."""

    def infer(known: Set[Statement]) -> Iterator[Tuple[Statement, Premises]]:
        implications: List[Tuple[Statement, Statement, Statement]] = []
        for stmt in known:
            parsed = _parse_implication(stmt)
            if parsed is None:
                continue
            antecedent, consequent = parsed
            implications.append((stmt, antecedent, consequent))

        for implication_stmt, antecedent, consequent in implications:
            if antecedent in known and consequent not in known:
                yield consequent, (implication_stmt, antecedent)

    return InferenceRule(name=name, inference=infer)


def theorem_proving_universe(
    axioms: Sequence[Statement],
    *,
    goals: Sequence[Statement] | None = None,
    rules: Sequence[InferenceRule] | None = None,
    observers: Sequence[Observer] = (),
) -> Universe:
    """Build a universe that performs automated theorem proving over statements."""

    if goals is None:
        goals = ()
    if rules is None:
        rules = (modus_ponens(),)

    known: Set[Statement] = set(axioms)
    proofs: Dict[Statement, ProofTrace] = {
        statement: ProofTrace(rule="axiom", premises=()) for statement in known
    }
    proved = frozenset(statement for statement in goals if statement in known)
    pending = tuple(sorted(statement for statement in goals if statement not in known))

    initial_state: State = {
        "known": known,
        "proofs": proofs,
        "goals": tuple(goals),
        "proved": proved,
        "pending": pending,
    }

    inference_rules = tuple(rules)

    def apply(state: State, _ctx: RuleContext) -> State:
        known_statements = set(state.get("known", ()))
        proof_traces = dict(state.get("proofs", {}))
        proved_goals = set(state.get("proved", ()))
        goals_tuple = tuple(state.get("goals", ()))

        produced = False
        for inference_rule in inference_rules:
            for conclusion, premises in inference_rule.infer(known_statements):
                if conclusion in known_statements:
                    continue
                known_statements.add(conclusion)
                proof_traces[conclusion] = ProofTrace(
                    rule=inference_rule.name, premises=premises
                )
                produced = True

        if not produced:
            return state

        if goals_tuple:
            proved_goals.update(goal for goal in goals_tuple if goal in known_statements)

        new_state = dict(state)
        new_state["known"] = known_statements
        new_state["proofs"] = proof_traces
        new_state["proved"] = frozenset(proved_goals)
        new_state["pending"] = tuple(
            sorted(goal for goal in goals_tuple if goal not in known_statements)
        )
        return new_state

    theorem_rule = rule("theorem-closure", apply)
    return God.universe(
        state=initial_state,
        rules=(theorem_rule,),
        observers=tuple(observers),
    )


def theorem_metric(previous: State, current: State) -> float:
    """Metric for theorem proving universes.

    The metric counts how many known statements or proved goals changed between
    two epochs. Once the set of known statements stabilises the metric evaluates
    to zero, allowing the fixpoint engine to detect convergence.
    """

    prev_known = set(previous.get("known", ()))
    curr_known = set(current.get("known", ()))
    prev_proved = set(previous.get("proved", ()))
    curr_proved = set(current.get("proved", ()))

    delta_known = len(prev_known.symmetric_difference(curr_known))
    delta_proved = len(prev_proved.symmetric_difference(curr_proved))
    return float(delta_known + delta_proved)


def run_theorem_prover(
    *,
    axioms: Sequence[Statement],
    goals: Sequence[Statement],
    rules: Sequence[InferenceRule] | None = None,
    observers: Sequence[Observer] = (),
    epsilon: float,
    max_epoch: int,
) -> FixpointResult:
    """Execute the theorem proving universe until it converges."""

    universe = theorem_proving_universe(
        axioms,
        goals=goals,
        rules=rules,
        observers=observers,
    )
    return fixpoint(
        universe,
        metric=theorem_metric,
        epsilon=epsilon,
        max_epoch=max_epoch,
    )


def reconstruct_proof(state: MutableMapping[str, object], goal: Statement) -> Optional[Proof]:
    """Reconstruct a proof for ``goal`` from the theorem proving state."""

    proofs = state.get("proofs")
    if not isinstance(proofs, dict) or goal not in proofs:
        return None

    proof_traces: Dict[Statement, ProofTrace] = proofs  # type: ignore[assignment]
    seen: Set[Statement] = set()
    steps: List[ProofStep] = []

    def build(statement: Statement) -> None:
        if statement in seen:
            return
        seen.add(statement)
        trace = proof_traces.get(statement)
        if trace is None:
            return
        for premise in trace.premises:
            build(premise)
        steps.append(
            ProofStep(statement=statement, rule=trace.rule, premises=trace.premises)
        )

    build(goal)
    if not steps or steps[-1].statement != goal:
        return None
    return Proof(goal=goal, steps=tuple(steps))
