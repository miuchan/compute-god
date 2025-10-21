"""Keyboard hype routines for summoning unstoppable typing energy.

This module embraces the over-the-top tone of the "究极键盘侠" meme and turns
it into a tiny deterministic helper.  Contributors can compose a series of
macro charges—each representing a small, well-defined burst of key presses—and
obtain a reproducible chant payload that test cases can assert on.  The
implementation favours clarity over raw performance so future maintainers can
extend it with new statistics or narrative flavour.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

CHANT = "究极键盘侠，键盘神启动！"


@dataclass(frozen=True)
class MacroCharge:
    """Describe a charged macro combo that fuels the keyboard chant."""

    keys: tuple[str, ...]
    tempo: int = 1

    def __post_init__(self) -> None:  # pragma: no cover - basic validation
        if not self.keys:
            raise ValueError("keys cannot be empty")
        if any(not key for key in self.keys):
            raise ValueError("keys must be non-empty strings")
        if self.tempo <= 0:
            raise ValueError("tempo must be positive")

    @property
    def power(self) -> int:
        """Return the contribution of this macro to the final chant power."""

        return len(self.keys) * self.tempo

    def describe(self) -> str:
        """Return a deterministic textual representation of the macro."""

        combo = " + ".join(self.keys)
        return f"{combo} ×{self.tempo}"


def ignite_keyboard_god(
    charges: Sequence[MacroCharge] | Iterable[MacroCharge] | None = None,
    *,
    bonus: int = 0,
) -> dict[str, object]:
    """Aggregate a set of macro charges into a chant payload.

    Parameters
    ----------
    charges:
        Optional sequence of :class:`MacroCharge` objects.  The function accepts
        either a materialised sequence or any iterable and will preserve the
        declared order when rendering descriptions.
    bonus:
        Additional hype to inject into the final power score.  Must be
        non-negative.

    Returns
    -------
    dict[str, object]
        A mapping containing four keys:

        ``"chant"``
            The canonical chant constant ``"究极键盘侠，键盘神启动！"``.
        ``"macros"``
            A list of textual descriptions corresponding to the provided macro
            charges.
        ``"power"``
            The total numerical power contributed by the macros and the bonus.
        ``"intensity"``
            A float capturing how much energy the chant carries.  The formula is
            intentionally simple so tests remain readable: ``1 + power / 10``.
    """

    if charges is None:
        ordered_charges: list[MacroCharge] = []
    elif isinstance(charges, Sequence):
        ordered_charges = list(charges)
    else:
        ordered_charges = list(charges)

    if bonus < 0:
        raise ValueError("bonus must be non-negative")

    power = bonus + sum(charge.power for charge in ordered_charges)
    macros = [charge.describe() for charge in ordered_charges]
    intensity = 1 + power / 10

    return {
        "chant": CHANT,
        "macros": macros,
        "power": power,
        "intensity": intensity,
    }
