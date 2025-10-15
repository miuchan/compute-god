from __future__ import annotations

from typing import MutableMapping

from compute_god import LegendChant, Utawarerumono, UtawarerumonoChant, 传颂之物


State = MutableMapping[str, object]


def verse_name(state: State) -> str:
    return str(state.get("name", ""))


def verse_title(state: State) -> str:
    return str(state.get("title", ""))


def resonance_metric(lines: tuple[str, ...]) -> float:
    return float(sum(len(line) for line in lines))


def test_utawarerumono_records_best_chant_and_copies_state() -> None:
    singer = Utawarerumono((verse_name, verse_title), metric=resonance_metric)

    first_lines = singer.sing({"name": "Haku", "title": "Masked One"})
    assert first_lines == ("Haku", "Masked One")
    assert len(singer.history) == 1

    mutable_state = {"name": "Kuon", "title": "Princess of Tuskur"}
    second_lines = singer.sing(mutable_state)
    assert second_lines == ("Kuon", "Princess of Tuskur")

    # Mutations after singing must not affect stored snapshots.
    mutable_state["title"] = "Changed"

    best = singer.best_chant()
    assert isinstance(best, UtawarerumonoChant)
    assert best.lines == ("Kuon", "Princess of Tuskur")
    assert best.state == {"name": "Kuon", "title": "Princess of Tuskur"}

    # The returned record should be a defensive copy.
    best.state["name"] = "Mutated"
    assert singer.best_state() == {"name": "Kuon", "title": "Princess of Tuskur"}

    assert singer.compose() == "Kuon\nPrincess of Tuskur"
    assert singer.compose(first_lines, delimiter=" • ") == "Haku • Masked One"


def test_utawarerumono_threshold_and_alias() -> None:
    singer = Utawarerumono((verse_name,), metric=resonance_metric, prefer="min")

    singer.sing({"name": "Mikoto"})
    assert singer.is_resonant(5.0) is False

    singer.sing({"name": "Eruruu"})
    assert singer.is_resonant(6.0) is True

    assert UtawarerumonoChant is LegendChant
    assert 传颂之物 is Utawarerumono

