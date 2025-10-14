"""Compute-God Python runtime.

This module exposes a minimal framework inspired by the README. It provides the
basic pieces required to declare a universe of rules and iteratively search for
fixpoints under a user supplied metric.
"""

from .rule import Rule, rule
from .universe import God, Universe
from .engine import fixpoint, FixpointResult
from .observer import Observer, ObserverEvent
from .miyu import MiyuBond, bond_miyu

__all__ = [
    "Rule",
    "rule",
    "God",
    "Universe",
    "fixpoint",
    "FixpointResult",
    "Observer",
    "ObserverEvent",
    "MiyuBond",
    "bond_miyu",
]
