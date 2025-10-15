# BUIDL in Public

Compute‑God is a long-horizon experiment in meta-computation. We want to cultivate a community that can watch the project unfold, reuse its building blocks, and continuously audit the underlying concepts. This document outlines how we will build in public.

## Guiding Principles

1. **Radical Transparency** – Architecture decisions, research notes, and implementation trade-offs are published as soon as they are legible. Drafts are acceptable; the point is to show the evolution of thought, not only polished releases.
2. **Community Co-Design** – Feedback loops are deliberately short. Prototype rules, observers, or new universes are demonstrated early, with Discord/Matrix/论坛 polls to decide what deserves another iteration.
3. **Traceable Experiments** – Every significant simulation or fixpoint experiment includes reproducible configs and a short narrative about why it matters. We bias toward notebooks and CLI scripts that can run with `make replay-*` commands.
4. **Ethical Meta-Computation** – We actively document potential misuse, computational load, and safety mitigations for higher-order self-referential systems.

## Communication Cadence

| Channel | Frequency | Purpose |
| --- | --- | --- |
| Public Changelog (`CHANGELOG.md`) | Weekly | Summarize merged universes, rule updates, and observer improvements. |
| Build Streams (Twitch/哔哩哔哩) | Bi-weekly | Live debugging of fixpoint engines, concept automata demos, and Q&A. |
| Research Notebooks (Quarto/Jupyter) | Continuous | Publish exploratory derivations, convergence proofs, and visualizations. |
| Community Calls (Discord Stage) | Monthly | Roadmap retrospectives, RFC review, and contributor onboarding. |
| BUIDL Snapshot Blog | Monthly | Narrative recap that ties together experiments, learnings, and upcoming bets. |

## Public Artifacts Checklist

To keep the public build auditable, every notable change should add or update:

- ✅ **Issue or RFC** describing the problem space, constraints, and acceptance tests.
- ✅ **Implementation Notes** that reference the relevant `docs/` primer and link to pull requests.
- ✅ **Trace Logs** or **Notebook Outputs** with reproducible seeds, recorded under `artifacts/` when feasible.
- ✅ **Observer Metrics** exported as JSON/CSV for downstream visualization.
- ✅ **Postmortems** when experiments fail or diverge, including hypotheses for the next attempt.

## Contributor Onboarding Path

1. Start with the [Minimal Universe Axioms](./minimal-universe-axioms.md) and run the `everything-demonstration` fixtures.
2. Explore open issues tagged `good-first-fixpoint` or `concept-automata`.
3. Pair with a maintainer during a live build session; co-streaming is encouraged.
4. Write a short “learning memo” after the first merged PR so the broader community can reuse the insights.

## Metrics We Track in Public

- **Fixpoint Latency Histogram** for the reference universes under canonical workloads.
- **Rule Bank Coverage**: ratio of exercised rewrite rules during integration tests.
- **Observer Signal Quality**: precision/recall for alerting on divergent iterations.
- **Community Health**: number of active contributors, response time on discussions, and retention across three release cycles.

By committing to this public-facing loop, we treat Compute‑God as both a research artifact and a shared playground. The invitation is open: remix the universes, improve the engines, and narrate what you discover.
