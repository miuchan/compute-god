from __future__ import annotations

import math

from compute_god import ELFUSDTMarket


def test_mid_price_and_invariant() -> None:
    market = ELFUSDTMarket(elf_reserve=1_200.0, usdt_reserve=3_600.0)

    assert math.isclose(market.mid_price, 3.0)
    assert math.isclose(market.invariant, 4_320_000.0)


def test_preview_does_not_mutate_state() -> None:
    market = ELFUSDTMarket(elf_reserve=1_000.0, usdt_reserve=2_000.0)

    preview = market.preview_swap("ELF->USDT", 10.0)

    assert market.history == []
    assert math.isclose(market.elf_reserve, 1_000.0)
    assert math.isclose(market.usdt_reserve, 2_000.0)

    executed = market.swap_elf_for_usdt(10.0)

    assert executed == preview
    assert len(market.history) == 1


def test_swap_updates_reserves_and_tracks_slippage() -> None:
    market = ELFUSDTMarket(elf_reserve=1_000.0, usdt_reserve=2_000.0)

    event = market.swap_elf_for_usdt(15.0)

    assert event.direction == "ELF->USDT"
    assert event.fee_paid == 15.0 * market.fee_rate
    assert event.slippage < 0.0
    assert math.isclose(event.invariant, market.invariant, rel_tol=1e-9)


def test_swap_usdt_for_elf_records_positive_slippage() -> None:
    market = ELFUSDTMarket(elf_reserve=500.0, usdt_reserve=1_500.0)

    event = market.swap_usdt_for_elf(120.0)

    assert event.direction == "USDT->ELF"
    assert event.slippage > 0.0
    assert math.isclose(event.invariant, market.invariant, rel_tol=1e-9)

