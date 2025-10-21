# Compute-God · Earth Online Experience Lab

> A cross-language meta-computation playground for prototyping universes, rules, and observers that converge on resilient futures.

The Compute-God project treats "Earth Online" as a living laboratory.  Every module in this repository is a self-contained universe, simulation, or storytelling device that can be composed through a shared fixed-point engine.  The Python runtime doubles as the reference implementation for sister codebases – including the TypeScript toolkit and the long-form documentation vault – so researchers and storytellers can remix ideas across repositories without friction.

![Earth Online Experience Lab banner](https://dummyimage.com/1200x320/001b2a/7df9ff.png&text=Earth+Online+Experience+Lab)

## Table of Contents
- [Project Overview](#project-overview)
- [Interoperability](#interoperability)
- [Architecture](#architecture)
  - [Core Engine](#core-engine)
  - [Universe Libraries](#universe-libraries)
  - [Observers & Telemetry](#observers--telemetry)
  - [Guidance & Tooling](#guidance--tooling)
- [Repository Layout](#repository-layout)
- [Getting Started](#getting-started)
- [Universe Catalogue & CLI](#universe-catalogue--cli)
- [Development Workflow](#development-workflow)
- [Publishing to PyPI](#publishing-to-pypi)
- [Roadmap](#roadmap)

## Project Overview
Compute-God reframes meta-computation as a playable, observable universe builder.  Each universe combines:

* **State** – arbitrary structures describing the current slice of reality.
* **Rules** – composable transformations that reshape the state.
* **Observers** – telemetry hooks capturing how the universe evolves.
* **Oracles** – optional heuristics guiding expensive or undecidable moves.

By iterating these components through a fixed-point engine the lab can explore social simulations, mathematical constructs, speculative fiction, and personal rituals under a single conceptual umbrella.

## Interoperability
The project is intentionally multi-repo and multi-runtime:

* **Python runtime (this repository)** – home of the canonical execution engine, CLI, and the most complete catalogue of universes.
* **TypeScript/Node.js runtime** – mirrors the Python surface so web experiments, editors, and bots can drive the same universes.
* **Documentation & storytelling vault** – deep dives, field notes, and world-building artefacts that reference the shared catalogue.

All runtimes consume the same catalogue blueprint, ensuring that a universe registered here is instantly discoverable everywhere.  The new `compute_god.catalogue` module materialises that blueprint and is now the single source of truth consumed by documentation generators and CLI tooling alike.

## Architecture
### Core Engine
The `compute_god.core` package is the heartbeat of the lab.  It exposes:

* `Universe` and `God` constructors to wrap states, rules, and observers.
* `Rule`, `rule()`, and guard utilities for declarative rewrites.
* `FixpointEngine` and `fixpoint()` to iterate universes until convergence under a chosen metric.
* Observer helpers (`Observer`, `ObserverEvent`, `combine_observers`) to wire telemetry streams.

### Universe Libraries
Dozens of universes live in `src/compute_god/`, each capturing a distinct narrative or research theme: `drug_lab` for molecular discovery, `earth_rescue` for planetary strategy, `touhou_project` for folklore-inspired optimisation, and many more.  They all follow the same pattern – a blueprint, a metric, and a `run_*` helper – so explorers can remix them with minimal ceremony.

### Observers & Telemetry
Modules such as `screenshot`, `github_feed`, and `github_offline` translate universe events into tangible artefacts: rendered mockups, mobile-friendly feeds, or offline knowledge bases.  Observers plug directly into the core engine, giving experiments a rich exhaust of data for analysis or storytelling.

### Guidance & Tooling
`guidance.py` and the CLI (`compute_god/cli.py`) surface the entire catalogue via a "guidance desk" metaphor.  Stations group related universes, thermal duals, culinary rituals, and more.  The freshly refactored catalogue blueprint ensures these groupings remain consistent across documentation, tests, and sibling runtimes.

The new `information_energy.py` module extends the desk with a companion for
"information energy" exploration.  It packages a momentum-aware gradient
descent navigator that tunes each step for stability, delight, and low energy
consumption so researchers can script smooth descents through their favourite
landscapes.

## Repository Layout
```
compute-god/
├── README.md                # Project narrative and onboarding guide
├── docs/                    # Field notes, world-building essays, and roadmap
├── src/compute_god/         # Python runtime, universes, observers, and tooling
│   ├── core/                # Fixed-point engine, rules, observers, universe types
│   ├── catalogue.py         # Shared blueprint powering the guidance desk
│   ├── guidance.py          # Station abstractions for catalogue navigation
│   ├── cli.py               # `compute-god` command line entry points
│   └── *.py                 # Universe modules and experimental toolkits
├── tests/                   # Behavioural and regression tests for every universe
├── pyproject.toml           # Build configuration (Python + CLI entry points)
└── uv.lock                  # Reproducible dependency lock for `uv`
```

## Getting Started
### Install the Python runtime
```bash
uv pip install compute-god
# or, when developing locally
uv venv
uv pip install -e .
```

### Install the TypeScript runtime
```bash
pnpm add compute-god
# or
npm install compute-god
```

### Spin up a quick experiment
```python
from compute_god import God, rule, fixpoint

universe = God.universe(
    state={"term": "(Y f)"},
    rules=[
        rule(
            "beta-reduce",
            lambda state: {"term": beta(state["term"])},
            until=lambda state: is_value(state["term"]) or steps() > 256,
        )
    ],
)

result = fixpoint(
    universe,
    metric=lambda prev, nxt: edit_distance(prev["term"], nxt["term"]),
    epsilon=0,
    max_epoch=64,
)
print(result.state["term"])
```

## Universe Catalogue & CLI
Explore every station programmatically or from the terminal:

```python
from compute_god import guidance_desk

desk = guidance_desk()
print(sorted(desk.keys())[:5])
print(desk["core"].catalog())
```

```bash
$ compute-god stations
core
  Core runtime primitives for building universes and solving fixed points.
  - ApplyFn
  - PredicateFn
  - Rule
  ...

$ compute-god station marketing --format json
{
    "description": "营销漏斗动力学。",
    "entries": [
      "FunnelParameters",
      "marketing_universe",
      ...
    ]
}

$ compute-god search god
Search results for 'god':
  - core.God
```

The CLI output is deterministic, making it perfect for generating documentation snippets or powering editor integrations.

## Development Workflow
1. **Set up tooling** – `uv venv && source .venv/bin/activate`.
2. **Install editable dependencies** – `uv pip install -e .[dev]` (see `pyproject.toml` for extras).
3. **Run tests** – `uv run pytest` or target a single module (`uv run pytest tests/test_guidance_desk.py`).
4. **Keep docs in sync** – update `README.md` and [`docs/TODO.md`](docs/TODO.md) whenever you add or reclassify a universe.

CI scripts in sister repositories consume the shared catalogue blueprint, so every change to `catalogue.py` propagates automatically to documentation and TypeScript typings.

## Publishing to PyPI
Releases of the Python runtime are published to [PyPI](https://pypi.org/project/compute-god/).  A step-by-step guide covering
version bumps, pre-flight checks, TestPyPI verification, and the trusted publishing workflow that powers
GitHub Releases lives in [`docs/publish_to_pypi.md`](docs/publish_to_pypi.md).

## Roadmap
The living checklist in [`docs/TODO.md`](docs/TODO.md) translates this README into actionable work – from codifying new universes to improving cross-repo automation.  Tick items as they ship, and propose new experiments via pull requests to keep the Earth Online Experience Lab evolving.
