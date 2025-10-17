import pytest

from compute_god import (
    InferenceRule,
    Proof,
    ProofStep,
    modus_ponens,
    reconstruct_proof,
    validate_proof,
    run_theorem_prover,
    theorem_metric,
    theorem_proving_universe,
)


def test_theorem_prover_derives_goal_via_modus_ponens():
    result = run_theorem_prover(
        axioms=("P", "P -> Q", "Q -> R"),
        goals=("R",),
        epsilon=0.0,
        max_epoch=10,
    )

    assert result.converged is True
    state = result.universe.state
    assert "R" in state["known"]
    assert state["pending"] == ()
    assert "R" in state["proved"]

    proof = reconstruct_proof(state, "R")
    assert proof is not None
    assert proof.goal == "R"
    assert proof.steps[-1].statement == "R"

    modus_steps = [step for step in proof.steps if step.rule == modus_ponens().name]
    derived_statements = {step.statement for step in modus_steps}
    assert "Q" in derived_statements
    assert "R" in derived_statements

    assert validate_proof(
        proof,
        axioms=("P", "P -> Q", "Q -> R"),
        rules=(modus_ponens(),),
    )


def test_theorem_metric_counts_statement_changes():
    universe = theorem_proving_universe(("A", "A -> B"), goals=("B",))
    base_state = universe.state

    assert theorem_metric(base_state, base_state) == 0.0

    mutated = dict(base_state)
    mutated["known"] = set(base_state["known"]) | {"C"}
    assert theorem_metric(base_state, mutated) == pytest.approx(1.0)

    mutated["proved"] = frozenset({"B"})
    assert theorem_metric(base_state, mutated) == pytest.approx(2.0)


def test_custom_inference_rules_extend_reasoner():
    def infer_chain(known):
        if "seed" in known and "grow" not in known:
            yield "grow", ("seed",)
        if "grow" in known and "bloom" not in known:
            yield "bloom", ("grow",)

    chain_rule = InferenceRule(name="growth", inference=infer_chain)

    result = run_theorem_prover(
        axioms=("seed",),
        goals=("bloom",),
        rules=(chain_rule,),
        epsilon=0.0,
        max_epoch=10,
    )

    assert result.converged is True
    state = result.universe.state
    assert state["pending"] == ()
    assert "bloom" in state["known"]

    proof = reconstruct_proof(state, "bloom")
    assert proof is not None
    assert [step.rule for step in proof.steps if step.rule != "axiom"] == ["growth", "growth"]
    last_step: ProofStep = proof.steps[-1]
    assert last_step.statement == "bloom"
    assert last_step.premises == ("grow",)


def test_validate_proof_rejects_invalid_derivation():
    mp = modus_ponens()
    bogus_proof = Proof(
        goal="R",
        steps=(
            ProofStep(statement="P", rule="axiom", premises=()),
            ProofStep(statement="R", rule=mp.name, premises=("P", "P -> R")),
        ),
    )

    assert validate_proof(bogus_proof, axioms=("P",), rules=(mp,)) is False
