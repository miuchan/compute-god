from compute_god.happiness_scheduler import (
    BlockQLearningScheduler,
    DIMENSIONS,
    GreedyScheduler,
    HappinessSimulator,
    ModelParameters,
    default_parameters,
    default_state,
    sampler_from_ranges,
)


def build_parameters() -> ModelParameters:
    params = default_parameters()
    return ModelParameters(
        alpha0=params.alpha0,
        alpha=params.alpha,
        beta=params.beta,
        gamma=params.gamma,
        delta=params.delta,
        k=params.k,
        phi=params.phi,
        psi=params.psi,
        productivity_base=params.productivity_base,
        productivity_matrix=params.productivity_matrix,
        stress_baseline=params.stress_baseline,
        stress_sensitivity=params.stress_sensitivity,
        sigma=[0.0 for _ in params.sigma],
        discount=params.discount,
    )


def test_simulator_step_updates_state_and_happiness() -> None:
    params = build_parameters()
    simulator = HappinessSimulator(params)
    state = default_state(level=5.0, set_point=4.5)
    allocation = [0.0] * len(DIMENSIONS)
    allocation[0] = 0.6
    result = simulator.step(state, allocation)

    assert result.happiness > 0
    assert result.stress > 0
    assert result.new_state.x[0] > state.x[0]
    assert all(abs(a - b) < 1e-9 for a, b in zip(result.new_state.s, state.s))


def test_greedy_scheduler_allocates_budget() -> None:
    params = build_parameters()
    simulator = HappinessSimulator(params)
    scheduler = GreedyScheduler(simulator, top_k=3)
    state = default_state(level=4.2, set_point=3.9)
    allocation = scheduler.plan_day(state)

    assert abs(sum(allocation) - simulator.time_budget) < 1e-9
    assert allocation.count(0.0) == len(DIMENSIONS) - 3


def test_block_q_learning_scheduler_trains_and_allocates() -> None:
    params = build_parameters()
    simulator = HappinessSimulator(params)
    scheduler = BlockQLearningScheduler(simulator, blocks=4, num_bins=4, learning_rate=0.2)

    low = {name: 3.0 for name in DIMENSIONS}
    high = {name: 5.0 for name in DIMENSIONS}
    sampler = sampler_from_ranges(low, high)
    scheduler.train(episodes=50, initial_sampler=sampler, seed=7)

    state = default_state(level=4.0, set_point=3.5)
    allocation = scheduler.plan_day(state)

    assert abs(sum(allocation) - simulator.time_budget) < 1e-9
    assert any(value > 0 for value in allocation)
