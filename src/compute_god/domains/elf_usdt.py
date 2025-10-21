"""A playful constant product market maker for the ``ELF/USDT`` pair.

The project frequently models whimsical concepts as small, focused utility
modules.  ``ELF/USDT`` continues the tradition by providing a light-weight
market simulation that mirrors the behaviour of a constant product automated
market maker (AMM).  The implementation is deliberately dependency free while
still exposing rich diagnostics—each swap returns an :class:`SwapEvent`
containing the realised price, paid fees, and resulting invariant.

The module does *not* attempt to be financially authoritative; instead it
offers enough structure for educational experiments, automated tests, or
high-level reasoning about liquidity and slippage.  Users can preview swaps
without mutating the pool, execute trades in either direction, and inspect the
recorded history to replay activity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Tuple

SwapDirection = Literal["ELF->USDT", "USDT->ELF"]


@dataclass(frozen=True)
class SwapEvent:
    """Snapshot of a single trade executed against the ``ELF/USDT`` pool."""

    direction: SwapDirection
    amount_in: float
    amount_out: float
    fee_paid: float
    mid_price: float
    effective_price: float
    slippage: float
    invariant: float


@dataclass
class ELFUSDTMarket:
    """Simple constant-product AMM specialised for the ``ELF/USDT`` pair."""

    elf_reserve: float
    usdt_reserve: float
    fee_rate: float = 0.003
    history: List[SwapEvent] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.elf_reserve <= 0 or self.usdt_reserve <= 0:
            raise ValueError("reserves must be strictly positive")
        if not (0.0 <= self.fee_rate < 1.0):
            raise ValueError("fee_rate must be within [0, 1)")

    @property
    def invariant(self) -> float:
        """Return the constant product invariant of the pool."""

        return self.elf_reserve * self.usdt_reserve

    @property
    def mid_price(self) -> float:
        """Return the instantaneous price of ``ELF`` expressed in ``USDT``."""

        return self.usdt_reserve / self.elf_reserve

    def _apply_swap(self, direction: SwapDirection, amount_in: float) -> Tuple[SwapEvent, float, float]:
        if amount_in <= 0:
            raise ValueError("amount_in must be strictly positive")

        invariant = self.invariant
        mid_price = self.mid_price
        fee_paid = amount_in * self.fee_rate
        net_amount = amount_in - fee_paid

        if direction == "ELF->USDT":
            new_elf = self.elf_reserve + net_amount
            new_usdt = invariant / new_elf
            amount_out = self.usdt_reserve - new_usdt
            effective_price = amount_out / amount_in
        else:  # direction == "USDT->ELF"
            new_usdt = self.usdt_reserve + net_amount
            new_elf = invariant / new_usdt
            amount_out = self.elf_reserve - new_elf
            effective_price = amount_in / amount_out

        slippage = (effective_price / mid_price) - 1.0

        event = SwapEvent(
            direction=direction,
            amount_in=amount_in,
            amount_out=amount_out,
            fee_paid=fee_paid,
            mid_price=mid_price,
            effective_price=effective_price,
            slippage=slippage,
            invariant=invariant,
        )

        return event, new_elf, new_usdt

    def preview_swap(self, direction: SwapDirection, amount_in: float) -> SwapEvent:
        """Return the swap outcome without mutating internal reserves."""

        event, _, _ = self._apply_swap(direction, amount_in)
        return event

    def swap(self, direction: SwapDirection, amount_in: float) -> SwapEvent:
        """Execute a swap and record it in the internal history."""

        event, new_elf, new_usdt = self._apply_swap(direction, amount_in)
        self.elf_reserve = new_elf
        self.usdt_reserve = new_usdt
        self.history.append(event)
        return event

    def swap_elf_for_usdt(self, amount_in: float) -> SwapEvent:
        """Convenience wrapper around :meth:`swap` for ``ELF -> USDT`` trades."""

        return self.swap("ELF->USDT", amount_in)

    def swap_usdt_for_elf(self, amount_in: float) -> SwapEvent:
        """Convenience wrapper around :meth:`swap` for ``USDT -> ELF`` trades."""

        return self.swap("USDT->ELF", amount_in)


# Symbolic helpers mirroring the style of other modules.
ELF = "ELF"
USDT = "USDT"
精灵 = ELF
泰达 = USDT


__all__ = [
    "ELFUSDTMarket",
    "SwapDirection",
    "SwapEvent",
    "ELF",
    "USDT",
    "精灵",
    "泰达",
]

