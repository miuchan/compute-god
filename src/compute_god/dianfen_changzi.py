"""Network game helpers affectionately dubbed ``淀粉肠子网络博弈``.

The module models a playful diffusion game where every vendor (a
``StarchSausagePlayer``) adjusts how many servings of starch sausage to cook
based on their own appetite curve and on influences coming from neighbouring
vendors.  The interaction is intentionally lightweight: no heavy linear algebra
packages are required, yet callers can still approximate a Nash-like
equilibrium by repeatedly applying best responses with a configurable
relaxation factor.

In keeping with the narrative tone of the repository, the API surfaces both
English and Chinese aliases.  ``simulate_starch_sausage_game`` mirrors the
rest of the catalogue by returning a rich ``StarchSausageEquilibrium`` object
capturing the final servings, convergence history, and the largest deviation
encountered along the way.  The convenience function is re-exported under the
iconic name ``淀粉肠子网络博弈`` so that guidance desk stations can reference it
directly when weaving together culinary simulations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, MutableMapping, Tuple

State = MutableMapping[str, float]


@dataclass(frozen=True)
class StarchSausagePlayer:
    """Describe a single vendor participating in the network game.

    Parameters
    ----------
    name:
        Identifier used within state mappings.  The name is preserved in the
        resulting equilibrium so downstream analyses can match servings back to
        their vendors without additional bookkeeping.
    base_appetite:
        Baseline demand for starch sausages before considering neighbouring
        influence.  Larger values lead to higher best responses in the absence
        of competition.
    satiation:
        Positive value controlling how quickly the vendor becomes satisfied.
        The best response divides the adjusted appetite by ``1 + satiation`` so
        higher values tame aggressive production.
    """

    name: str
    base_appetite: float
    satiation: float = 1.0


@dataclass(frozen=True)
class StarchSausageEquilibrium:
    """Summary returned by :func:`simulate_starch_sausage_game`."""

    servings: Mapping[str, float]
    rounds: int
    history: Tuple[Mapping[str, float], ...]
    max_deviation: float

    def as_tuple(self) -> Tuple[Mapping[str, float], int]:
        """Compact representation useful for assertions and quick checks."""

        return self.servings, self.rounds


class StarchSausageNetworkGame:
    """Iterative best-response engine for starch sausage vendors."""

    def __init__(
        self,
        players: Iterable[StarchSausagePlayer],
        influences: Mapping[str, Mapping[str, float]],
        *,
        relaxation: float = 0.5,
    ) -> None:
        self.players: Dict[str, StarchSausagePlayer] = {player.name: player for player in players}
        self.influences: Dict[str, Dict[str, float]] = {
            name: dict(mapping) for name, mapping in influences.items()
        }
        self.relaxation = float(relaxation)
        if not 0.0 < self.relaxation <= 1.0:
            raise ValueError("relaxation must be within (0, 1]")
        missing = set(self.players) - set(self.influences)
        for name in missing:
            self.influences[name] = {}

    def best_response(self, name: str, state: Mapping[str, float]) -> float:
        """Return the servings that maximise the vendor's local utility."""

        player = self.players[name]
        influence = 0.0
        for neighbour, weight in self.influences.get(name, {}).items():
            if neighbour == name:
                continue
            influence += weight * state.get(neighbour, 0.0)
        appetite = player.base_appetite + influence
        response = appetite / (1.0 + player.satiation)
        return max(0.0, response)

    def step(self, state: Mapping[str, float]) -> Dict[str, float]:
        """Compute the next servings applying relaxed best responses."""

        updated: Dict[str, float] = {}
        for name in self.players:
            target = self.best_response(name, state)
            current = state[name]
            updated[name] = current + self.relaxation * (target - current)
        return updated

    def potential(self, state: Mapping[str, float]) -> float:
        """Evaluate a smooth potential function for the current state."""

        total = 0.0
        for name, player in self.players.items():
            servings = state[name]
            total += player.base_appetite * servings
            total -= 0.5 * (1.0 + player.satiation) * servings * servings
            for neighbour, weight in self.influences.get(name, {}).items():
                total += 0.5 * weight * servings * state.get(neighbour, 0.0)
        return total

    def run(
        self,
        initial_state: Mapping[str, float] | None = None,
        *,
        max_rounds: int = 128,
        tolerance: float = 1e-6,
    ) -> StarchSausageEquilibrium:
        """Iterate relaxed best responses until convergence or ``max_rounds``."""

        if max_rounds <= 0:
            raise ValueError("max_rounds must be positive")
        if tolerance <= 0.0:
            raise ValueError("tolerance must be positive")

        state: Dict[str, float]
        if initial_state is None:
            state = {
                name: player.base_appetite / (1.0 + player.satiation)
                for name, player in self.players.items()
            }
        else:
            state = {name: float(initial_state.get(name, 0.0)) for name in self.players}

        history: list[Dict[str, float]] = [dict(state)]
        max_deviation = 0.0

        for round_index in range(1, max_rounds + 1):
            next_state = self.step(state)
            deviation = max(abs(next_state[name] - state[name]) for name in self.players)
            max_deviation = max(max_deviation, deviation)
            state = next_state
            history.append(dict(state))
            if deviation <= tolerance:
                return StarchSausageEquilibrium(
                    servings=state,
                    rounds=round_index,
                    history=tuple(history),
                    max_deviation=max_deviation,
                )

        return StarchSausageEquilibrium(
            servings=state,
            rounds=max_rounds,
            history=tuple(history),
            max_deviation=max_deviation,
        )


def build_starch_sausage_game(
    players: Iterable[StarchSausagePlayer],
    influences: Mapping[str, Mapping[str, float]],
    *,
    relaxation: float = 0.5,
) -> StarchSausageNetworkGame:
    """Convenience wrapper that mirrors other builder helpers in the repo."""

    return StarchSausageNetworkGame(players, influences, relaxation=relaxation)


def simulate_starch_sausage_game(
    players: Iterable[StarchSausagePlayer],
    influences: Mapping[str, Mapping[str, float]],
    initial_state: Mapping[str, float] | None = None,
    *,
    relaxation: float = 0.5,
    max_rounds: int = 128,
    tolerance: float = 1e-6,
) -> StarchSausageEquilibrium:
    """Build and run a starch sausage network game in a single call."""

    game = build_starch_sausage_game(players, influences, relaxation=relaxation)
    return game.run(initial_state=initial_state, max_rounds=max_rounds, tolerance=tolerance)


# Playful aliases embracing the poetic API.
淀粉肠子玩家 = StarchSausagePlayer
淀粉肠子网络 = StarchSausageNetworkGame
淀粉肠子均衡 = StarchSausageEquilibrium
淀粉肠子网络博弈 = simulate_starch_sausage_game


__all__ = [
    "StarchSausagePlayer",
    "StarchSausageNetworkGame",
    "StarchSausageEquilibrium",
    "build_starch_sausage_game",
    "simulate_starch_sausage_game",
    "淀粉肠子玩家",
    "淀粉肠子网络",
    "淀粉肠子均衡",
    "淀粉肠子网络博弈",
]

