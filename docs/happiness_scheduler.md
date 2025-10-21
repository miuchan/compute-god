# Happiness Scheduler

This module provides an executable realisation of the "life integral" model
described in the prompt.  It lets you define personal parameters, simulate the
state dynamics, and generate day-to-day schedules using either a greedy
heuristic or a lightweight reinforcement-learning agent.

## Quick start

```python
from compute_god.happiness_scheduler import (
    BlockQLearningScheduler,
    DIMENSIONS,
    GreedyScheduler,
    HappinessSimulator,
    default_parameters,
    default_state,
    sampler_from_ranges,
)

params = default_parameters()
simulator = HappinessSimulator(params, time_budget=1.0)
state = default_state(level=4.5, set_point=4.0)

greedy = GreedyScheduler(simulator)
allocation = greedy.plan_day(state)
results = simulator.simulate(state, [allocation])

sampler = sampler_from_ranges({name: 3.0 for name in DIMENSIONS}, {name: 5.0 for name in DIMENSIONS})
agent = BlockQLearningScheduler(simulator)
agent.train(episodes=200, initial_sampler=sampler, seed=123)
policy_allocation = agent.plan_day(state)
```

## Parameter tuning tips

* ``phi`` boosts the set-point through deliberate habits such as journaling or
  reflection.  Increasing ``phi`` makes those interventions more potent.
* ``psi`` captures how much comparisons or social-media noise pull your
  baseline down.  Reducing ``psi`` corresponds to creating a calmer
  environment.
* ``beta`` controls complementarities.  Assign larger values to pairs of
  dimensions that act as happiness multipliers for you (for example,
  health–relationships or mastery–purpose).

When running weekly or quarterly reviews you can record the observed trajectory
of ``x`` and ``h`` and update the parameters accordingly, mirroring a
calibration workflow.
