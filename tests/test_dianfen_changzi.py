import math

import pytest

from compute_god import (
    StarchSausageEquilibrium,
    StarchSausageNetworkGame,
    StarchSausagePlayer,
    build_starch_sausage_game,
    simulate_starch_sausage_game,
    淀粉肠子网络博弈,
)


def test_best_response_respects_satiation() -> None:
    game = build_starch_sausage_game(
        [StarchSausagePlayer("vendor", base_appetite=4.0, satiation=1.0)],
        influences={},
    )
    response = game.best_response("vendor", {"vendor": 0.0})
    assert response == pytest.approx(2.0)

    equilibrium = simulate_starch_sausage_game(
        [StarchSausagePlayer("vendor", base_appetite=4.0, satiation=1.0)],
        influences={},
        relaxation=1.0,
        max_rounds=4,
        tolerance=1e-9,
    )
    assert equilibrium.servings["vendor"] == pytest.approx(2.0)


def test_network_game_converges_to_expected_equilibrium() -> None:
    players = [
        StarchSausagePlayer("alpha", base_appetite=3.0, satiation=1.0),
        StarchSausagePlayer("beta", base_appetite=2.5, satiation=1.5),
    ]
    influences = {
        "alpha": {"beta": 0.4},
        "beta": {"alpha": 0.2},
    }
    game = StarchSausageNetworkGame(players, influences, relaxation=0.75)
    equilibrium = game.run(initial_state={"alpha": 0.0, "beta": 0.0}, tolerance=1e-9)

    assert isinstance(equilibrium, StarchSausageEquilibrium)
    assert equilibrium.rounds < 60
    expected_first_step = 0.75 * (3.0 / (1.0 + 1.0))
    assert equilibrium.max_deviation == pytest.approx(expected_first_step, abs=1e-9)

    expected_beta = 2.8 / 2.46
    expected_alpha = 1.5 + 0.2 * expected_beta
    assert equilibrium.servings["alpha"] == pytest.approx(expected_alpha, abs=1e-6)
    assert equilibrium.servings["beta"] == pytest.approx(expected_beta, abs=1e-6)

    potentials = [game.potential(snapshot) for snapshot in equilibrium.history]
    assert potentials[-1] >= potentials[0]


def test_chinese_alias_runs_full_simulation() -> None:
    players = [
        StarchSausagePlayer("gamma", base_appetite=1.2, satiation=0.8),
        StarchSausagePlayer("delta", base_appetite=1.2, satiation=0.8),
    ]
    influences = {"gamma": {"delta": 0.3}, "delta": {"gamma": 0.3}}
    equilibrium = 淀粉肠子网络博弈(
        players,
        influences,
        initial_state={"gamma": 0.0, "delta": 0.0},
        relaxation=1.0,
        tolerance=1e-9,
        max_rounds=80,
    )

    assert isinstance(equilibrium, StarchSausageEquilibrium)
    assert equilibrium.rounds <= 80
    assert math.isclose(
        equilibrium.servings["gamma"],
        equilibrium.servings["delta"],
        rel_tol=1e-6,
    )
