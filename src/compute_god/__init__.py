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
from .bingzi import Bingzi, 冰子
from .entangle import (
    Chanzi,
    Entangler,
    EntanglementSnapshot,
    Jiuzi,
    纠子,
    缠子,
    纠缠子,
)
from .existence import ExistenceWitness, StabilityWitness, 存在子, 稳定子
from .ctc import ClosedTimelikeCurve, CTCOptimisationResult, optimise_closed_timelike_curve
from .threshold import (
    ThresholdSpace,
    ThresholdOptimisationResult,
    optimise_threshold_space,
)
from .metaverse import (
    MetaverseBlueprint,
    bond_metaverse_with_love,
    ideal_metaverse_universe,
    metaverse_metric,
    run_ideal_metaverse,
)
from .meta_spacetime import (
    MetaSpacetimeBlueprint,
    ideal_meta_spacetime_universe,
    meta_spacetime_metric,
    run_meta_spacetime,
)
from .catalysis import (
    CatalysisOutcome,
    Chanzi,
    Jiuzi,
    catalyse_jiuzi_and_chanzi,
)
from .theorem import (
    InferenceRule,
    Proof,
    ProofStep,
    modus_ponens,
    reconstruct_proof,
    run_theorem_prover,
    theorem_metric,
    theorem_proving_universe,
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
    "Bingzi",
    "冰子",
    "Jiuzi",
    "Chanzi",
    "Entangler",
    "EntanglementSnapshot",
    "纠子",
    "缠子",
    "纠缠子",
    "ExistenceWitness",
    "StabilityWitness",
    "存在子",
    "稳定子",
    "ClosedTimelikeCurve",
    "CTCOptimisationResult",
    "optimise_closed_timelike_curve",
    "ThresholdSpace",
    "ThresholdOptimisationResult",
    "optimise_threshold_space",
    "MetaverseBlueprint",
    "bond_metaverse_with_love",
    "ideal_metaverse_universe",
    "metaverse_metric",
    "run_ideal_metaverse",
    "MetaSpacetimeBlueprint",
    "ideal_meta_spacetime_universe",
    "meta_spacetime_metric",
    "run_meta_spacetime",
    "Jiuzi",
    "Chanzi",
    "CatalysisOutcome",
    "catalyse_jiuzi_and_chanzi",
    "InferenceRule",
    "Proof",
    "ProofStep",
    "modus_ponens",
    "reconstruct_proof",
    "run_theorem_prover",
    "theorem_metric",
    "theorem_proving_universe",
]
