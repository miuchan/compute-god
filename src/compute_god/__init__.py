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
from .metaverse import (
    MetaverseBlueprint,
    ideal_metaverse_universe,
    metaverse_metric,
    run_ideal_metaverse,
)

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
    "MetaverseBlueprint",
    "ideal_metaverse_universe",
    "metaverse_metric",
    "run_ideal_metaverse",
]
