"""Core typing helpers for Compute-God.

This module centralises foundational type aliases and protocols used by the
runtime.  Placing them in a dedicated module prevents circular imports between
engine, rule and universe implementations while giving downstream modules a
single source of truth for state annotations.
"""

from __future__ import annotations

from typing import MutableMapping, Protocol

State = MutableMapping[str, object]


class RuleContext(Protocol):
    """Minimal protocol exposed to rules during execution."""

    def steps(self) -> int:
        """Return how many rule applications have been performed."""

    def increment(self) -> None:
        """Record that another rule application has been executed."""
