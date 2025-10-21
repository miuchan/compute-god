"""Discrete life-integral simulator with greedy and RL schedulers.

The implementation avoids hard dependencies on external numerical packages so
that it can run in constrained environments.  All vector operations are
implemented using plain Python lists and ``math`` helpers.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, MutableMapping, Optional, Sequence


DIMENSIONS: Sequence[str] = ("H", "W", "R", "M", "P", "A", "E", "S")


def _vector(values: Sequence[float]) -> list[float]:
    return [float(v) for v in values]


def _matrix(values: Sequence[Sequence[float]]) -> list[list[float]]:
    return [_vector(row) for row in values]


@dataclass(frozen=True)
class ModelParameters:
    """Numerical parameters for the life integral model."""

    alpha0: float
    alpha: Sequence[float]
    beta: Sequence[Sequence[float]]
    gamma: float
    delta: Sequence[float]
    k: Sequence[float]
    phi: Sequence[float]
    psi: Sequence[float]
    productivity_base: Sequence[float]
    productivity_matrix: Sequence[Sequence[float]]
    stress_baseline: float = 0.0
    stress_sensitivity: Sequence[float] | None = None
    sigma: Sequence[float] | None = None
    discount: float = 0.97

    def __post_init__(self) -> None:
        n = len(DIMENSIONS)
        for name, seq in (
            ("alpha", self.alpha),
            ("delta", self.delta),
            ("k", self.k),
            ("phi", self.phi),
            ("psi", self.psi),
            ("productivity_base", self.productivity_base),
        ):
            if len(seq) != n:
                raise ValueError(f"{name} must contain {n} entries")
        for name, mat in ("beta", self.beta), ("productivity_matrix", self.productivity_matrix):
            if len(mat) != n or any(len(row) != n for row in mat):
                raise ValueError(f"{name} must be an {n}x{n} matrix")
        if self.stress_sensitivity is not None and len(self.stress_sensitivity) != n:
            raise ValueError("stress_sensitivity must contain one entry per dimension")
        if self.sigma is not None and len(self.sigma) != n:
            raise ValueError("sigma must contain one entry per dimension")

    @property
    def alpha_vec(self) -> list[float]:
        return _vector(self.alpha)

    @property
    def beta_mat(self) -> list[list[float]]:
        return _matrix(self.beta)

    @property
    def delta_vec(self) -> list[float]:
        return _vector(self.delta)

    @property
    def k_vec(self) -> list[float]:
        return _vector(self.k)

    @property
    def phi_vec(self) -> list[float]:
        return _vector(self.phi)

    @property
    def psi_vec(self) -> list[float]:
        return _vector(self.psi)

    @property
    def productivity_base_vec(self) -> list[float]:
        return _vector(self.productivity_base)

    @property
    def productivity_matrix_mat(self) -> list[list[float]]:
        return _matrix(self.productivity_matrix)

    @property
    def stress_sensitivity_vec(self) -> list[float]:
        if self.stress_sensitivity is None:
            return [0.0] * len(DIMENSIONS)
        return _vector(self.stress_sensitivity)

    @property
    def sigma_vec(self) -> list[float] | None:
        return None if self.sigma is None else _vector(self.sigma)


@dataclass
class LifeState:
    x: list[float]
    s: list[float]
    time: int = 0

    def copy(self) -> "LifeState":
        return LifeState(x=self.x.copy(), s=self.s.copy(), time=self.time)


@dataclass(frozen=True)
class StepResult:
    happiness: float
    stress: float
    allocation: list[float]
    new_state: LifeState


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class HappinessSimulator:
    """Simulate the life integral dynamics in discrete time."""

    def __init__(self, params: ModelParameters, time_budget: float = 1.0) -> None:
        self.params = params
        self.time_budget = float(time_budget)
        self._alpha = params.alpha_vec
        self._beta = params.beta_mat
        self._delta = params.delta_vec
        self._k = params.k_vec
        self._phi = params.phi_vec
        self._psi = params.psi_vec
        self._productivity_base = params.productivity_base_vec
        self._productivity_matrix = params.productivity_matrix_mat
        self._stress_sensitivity = params.stress_sensitivity_vec
        self._sigma = params.sigma_vec

    def productivity(self, state: LifeState) -> list[float]:
        prod = []
        for i in range(len(DIMENSIONS)):
            value = self._productivity_base[i]
            row = self._productivity_matrix[i]
            value += sum(row[j] * state.x[j] for j in range(len(DIMENSIONS)))
            prod.append(value)
        return prod

    def marginal_happiness(self, state: LifeState) -> list[float]:
        marginal: list[float] = []
        for i in range(len(DIMENSIONS)):
            x_i = max(state.x[i], 1e-8)
            term = self._alpha[i] / (1.0 + x_i)
            complement = 0.0
            for j in range(len(DIMENSIONS)):
                if i == j:
                    continue
                beta = self._beta[i][j]
                if beta == 0.0:
                    continue
                complement += 0.5 * beta * math.sqrt(max(state.x[j], 0.0) / x_i)
            marginal.append(term + complement)
        return marginal

    def stress(self, allocation: Sequence[float]) -> float:
        return self.params.stress_baseline + _dot(self._stress_sensitivity, allocation)

    def instantaneous_happiness(self, state: LifeState, stress: float) -> float:
        value = self.params.alpha0
        value += sum(self._alpha[i] * math.log1p(max(state.x[i], 0.0)) for i in range(len(DIMENSIONS)))
        for i in range(len(DIMENSIONS)):
            for j in range(i + 1, len(DIMENSIONS)):
                beta = self._beta[i][j]
                if beta == 0.0:
                    continue
                value += beta * math.sqrt(max(state.x[i], 0.0) * max(state.x[j], 0.0))
        return value - self.params.gamma * stress

    def step(
        self,
        state: LifeState,
        allocation: Sequence[float],
        habit_signal: Optional[Sequence[float]] = None,
        comparison_signal: Optional[Sequence[float]] = None,
        shock: Optional[Sequence[float]] = None,
        stress_override: Optional[float] = None,
        rng: Optional[random.Random] = None,
    ) -> StepResult:
        if len(allocation) != len(DIMENSIONS):
            raise ValueError("allocation must match the number of dimensions")
        if any(a < -1e-9 for a in allocation):
            raise ValueError("allocation entries must be non-negative")
        if sum(allocation) > self.time_budget + 1e-8:
            raise ValueError("allocation exceeds the available time budget")

        habit = _vector(habit_signal or [0.0] * len(DIMENSIONS))
        comparison = _vector(comparison_signal or [0.0] * len(DIMENSIONS))

        if shock is not None:
            noise = _vector(shock)
        elif self._sigma is not None:
            rng = rng or random.Random()
            noise = [rng.gauss(0.0, sigma) for sigma in self._sigma]
        else:
            noise = [0.0] * len(DIMENSIONS)

        stress = stress_override if stress_override is not None else self.stress(allocation)
        happiness = self.instantaneous_happiness(state, stress)

        prod = self.productivity(state)
        next_x: list[float] = []
        for i in range(len(DIMENSIONS)):
            value = (1.0 - self._delta[i]) * state.x[i]
            value += prod[i] * allocation[i]
            value -= self._k[i] * (state.x[i] - state.s[i])
            value += noise[i]
            next_x.append(value)

        next_s = [state.s[i] + self._phi[i] * habit[i] - self._psi[i] * comparison[i] for i in range(len(DIMENSIONS))]
        next_state = LifeState(x=next_x, s=next_s, time=state.time + 1)
        return StepResult(happiness=happiness, stress=stress, allocation=list(allocation), new_state=next_state)

    def simulate(
        self,
        initial_state: LifeState,
        allocations: Iterable[Sequence[float]],
        habit_signals: Optional[Iterable[Sequence[float]]] = None,
        comparison_signals: Optional[Iterable[Sequence[float]]] = None,
        shocks: Optional[Iterable[Sequence[float]]] = None,
    ) -> list[StepResult]:
        results: list[StepResult] = []
        state = initial_state.copy()
        habit_iter = iter(habit_signals) if habit_signals is not None else None
        comparison_iter = iter(comparison_signals) if comparison_signals is not None else None
        shock_iter = iter(shocks) if shocks is not None else None

        for allocation in allocations:
            habit_signal = next(habit_iter) if habit_iter is not None else None
            comparison_signal = next(comparison_iter) if comparison_iter is not None else None
            shock = next(shock_iter) if shock_iter is not None else None
            step = self.step(
                state,
                allocation,
                habit_signal=habit_signal,
                comparison_signal=comparison_signal,
                shock=shock,
            )
            results.append(step)
            state = step.new_state
        return results


class GreedyScheduler:
    """Daily allocation heuristic based on marginal returns."""

    def __init__(self, simulator: HappinessSimulator, top_k: int = 4, epsilon: float = 1e-9) -> None:
        self.simulator = simulator
        self.top_k = max(1, top_k)
        self.epsilon = epsilon

    def marginal_returns(self, state: LifeState) -> list[float]:
        productivity = self.simulator.productivity(state)
        marginal = self.simulator.marginal_happiness(state)
        return [m * p for m, p in zip(marginal, productivity)]

    def plan_day(self, state: LifeState) -> list[float]:
        mr = self.marginal_returns(state)
        ranked = sorted(range(len(DIMENSIONS)), key=lambda i: mr[i], reverse=True)
        chosen = ranked[: self.top_k]
        weights = [max(mr[i], self.epsilon) for i in chosen]
        total = sum(weights)
        allocation = [0.0] * len(DIMENSIONS)
        for idx, weight in zip(chosen, weights):
            allocation[idx] = weight / total * self.simulator.time_budget
        return allocation


class BlockQLearningScheduler:
    """Tabular Q-learning agent operating on daily time blocks."""

    def __init__(
        self,
        simulator: HappinessSimulator,
        blocks: int = 4,
        num_bins: int = 5,
        learning_rate: float = 0.1,
        discount: Optional[float] = None,
        epsilon: float = 0.1,
        value_range: float = 12.0,
    ) -> None:
        self.simulator = simulator
        self.blocks = max(1, blocks)
        self.num_bins = max(2, num_bins)
        self.learning_rate = learning_rate
        self.discount = discount if discount is not None else simulator.params.discount
        self.epsilon = epsilon
        self.value_range = value_range
        self.block_allocation = simulator.time_budget / float(self.blocks)
        self.q_table: MutableMapping[tuple[int, ...], list[float]] = defaultdict(
            lambda: [0.0] * len(DIMENSIONS),
        )

    def _discretise(self, x: Sequence[float]) -> tuple[int, ...]:
        bin_width = self.value_range / float(self.num_bins)
        return tuple(
            min(int(max(value, 0.0) // bin_width), self.num_bins - 1)
            for value in x
        )

    def _choose_action(self, obs: tuple[int, ...], rng: random.Random) -> int:
        if rng.random() < self.epsilon:
            return rng.randrange(len(DIMENSIONS))
        q_values = self.q_table[obs]
        best_value = max(q_values)
        best_actions = [i for i, value in enumerate(q_values) if value == best_value]
        return rng.choice(best_actions)

    def train(
        self,
        episodes: int,
        initial_sampler: Callable[[random.Random], LifeState],
        habit_signal: Optional[Sequence[float]] = None,
        comparison_signal: Optional[Sequence[float]] = None,
        seed: Optional[int] = None,
    ) -> None:
        rng = random.Random(seed)
        for _ in range(episodes):
            state = initial_sampler(rng).copy()
            for _ in range(self.blocks):
                obs = self._discretise(state.x)
                action = self._choose_action(obs, rng)
                allocation = [0.0] * len(DIMENSIONS)
                allocation[action] = self.block_allocation
                step = self.simulator.step(
                    state,
                    allocation,
                    habit_signal=habit_signal,
                    comparison_signal=comparison_signal,
                    rng=rng,
                )
                next_obs = self._discretise(step.new_state.x)
                reward = step.happiness
                best_next = max(self.q_table[next_obs])
                current = self.q_table[obs][action]
                td_error = reward + self.discount * best_next - current
                self.q_table[obs][action] = current + self.learning_rate * td_error
                state = step.new_state

    def plan_day(self, state: LifeState) -> list[float]:
        schedule = [0.0] * len(DIMENSIONS)
        scratch = state.copy()
        for _ in range(self.blocks):
            obs = self._discretise(scratch.x)
            q_values = self.q_table.get(obs)
            if q_values is None:
                mr = self.simulator.marginal_happiness(scratch)
                action = max(range(len(DIMENSIONS)), key=lambda i: mr[i])
            else:
                best_value = max(q_values)
                best_actions = [i for i, value in enumerate(q_values) if value == best_value]
                action = best_actions[0]
            allocation = [0.0] * len(DIMENSIONS)
            allocation[action] = self.block_allocation
            schedule[action] += self.block_allocation
            step = self.simulator.step(scratch, allocation)
            scratch = step.new_state
        total = sum(schedule)
        if total > 0:
            scale = self.simulator.time_budget / total
            schedule = [value * scale for value in schedule]
        return schedule


def default_parameters() -> ModelParameters:
    n = len(DIMENSIONS)
    beta = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        if DIMENSIONS[i] in {"H", "S"}:
            for j in range(n):
                beta[i][j] = beta[j][i] = 0.18
    mastery = DIMENSIONS.index("M")
    purpose = DIMENSIONS.index("P")
    beta[mastery][purpose] = beta[purpose][mastery] = 0.25

    productivity_matrix = [[0.01 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        productivity_matrix[i][i] += 0.05

    return ModelParameters(
        alpha0=0.5,
        alpha=[0.9, 0.6, 0.7, 0.8, 0.75, 0.6, 0.55, 0.85],
        beta=beta,
        gamma=0.8,
        delta=[0.08, 0.05, 0.06, 0.04, 0.035, 0.04, 0.05, 0.09],
        k=[0.12, 0.1, 0.09, 0.06, 0.05, 0.07, 0.08, 0.11],
        phi=[0.05, 0.02, 0.04, 0.05, 0.06, 0.03, 0.02, 0.04],
        psi=[0.03, 0.05, 0.04, 0.03, 0.02, 0.04, 0.05, 0.03],
        productivity_base=[0.35, 0.28, 0.25, 0.3, 0.27, 0.24, 0.22, 0.33],
        productivity_matrix=productivity_matrix,
        stress_baseline=0.2,
        stress_sensitivity=[0.1, 0.15, 0.08, 0.07, 0.06, 0.09, 0.05, 0.04],
        sigma=[0.05] * n,
        discount=0.96,
    )


def default_state(level: float = 4.0, set_point: float = 3.5) -> LifeState:
    x = [float(level)] * len(DIMENSIONS)
    s = [float(set_point)] * len(DIMENSIONS)
    return LifeState(x=x, s=s, time=0)


def sampler_from_ranges(
    low: Mapping[str, float] | Sequence[float],
    high: Mapping[str, float] | Sequence[float],
) -> Callable[[random.Random], LifeState]:
    if isinstance(low, Mapping):
        low_vec = [float(low[name]) for name in DIMENSIONS]
    else:
        low_vec = [float(value) for value in low]
    if isinstance(high, Mapping):
        high_vec = [float(high[name]) for name in DIMENSIONS]
    else:
        high_vec = [float(value) for value in high]
    if len(low_vec) != len(DIMENSIONS) or len(high_vec) != len(DIMENSIONS):
        raise ValueError("low/high must specify one value per dimension")

    def sampler(rng: random.Random) -> LifeState:
        x = [rng.uniform(low_vec[i], high_vec[i]) for i in range(len(DIMENSIONS))]
        s = [rng.uniform(low_vec[i] - 0.5, high_vec[i] - 0.5) for i in range(len(DIMENSIONS))]
        return LifeState(x=x, s=s)

    return sampler


__all__ = [
    "BlockQLearningScheduler",
    "DIMENSIONS",
    "GreedyScheduler",
    "HappinessSimulator",
    "LifeState",
    "ModelParameters",
    "StepResult",
    "default_parameters",
    "default_state",
    "sampler_from_ranges",
]

