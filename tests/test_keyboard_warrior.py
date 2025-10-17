from __future__ import annotations

import pytest

from compute_god.keyboard_warrior import CHANT, MacroCharge, ignite_keyboard_god


def test_ignite_keyboard_god_builds_payload() -> None:
    charges = [
        MacroCharge(("Ctrl", "Alt", "Delete"), tempo=2),
        MacroCharge(("W", "A", "S", "D"), tempo=1),
    ]

    payload = ignite_keyboard_god(charges, bonus=3)

    assert payload["chant"] == CHANT
    assert payload["macros"] == [
        "Ctrl + Alt + Delete ×2",
        "W + A + S + D ×1",
    ]
    assert payload["power"] == (3 * 2) + (4 * 1) + 3
    assert payload["intensity"] == pytest.approx(1 + payload["power"] / 10)


def test_macro_charge_validation() -> None:
    with pytest.raises(ValueError):
        MacroCharge(())
    with pytest.raises(ValueError):
        MacroCharge(("",))
    with pytest.raises(ValueError):
        MacroCharge(("Shift",), tempo=0)


@pytest.mark.parametrize("bonus", [0, 5])
def test_bonus_validation(bonus: int) -> None:
    payload = ignite_keyboard_god([MacroCharge(("F",), tempo=1)], bonus=bonus)
    assert payload["power"] == 1 + bonus


def test_negative_bonus_rejected() -> None:
    with pytest.raises(ValueError):
        ignite_keyboard_god([MacroCharge(("F",), tempo=1)], bonus=-1)
