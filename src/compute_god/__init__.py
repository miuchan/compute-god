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
from .bingzi import Bingzi, Pingzi, peculiar_asymmetry, 冰子, 瓶子
from .jizi import Jizi, ThermalDual, Zijiji, thermal_dual, 机子, 子机机, 热对偶
from .abura_soba import (
    AburaSobaProfile,
    NoodleCanvas,
    OilLayer,
    TareBlend,
    Topping,
    assemble_abura_soba,
    油そば,
)
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
from .degree_space import DegreeDual, DegreeSpace, DegreeTensor, tensor_product
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
from .everything_demonstration import (
    EverythingDemonstrationBlueprint,
    physical_everything_demonstration_universe,
    physical_everything_metric,
    run_physical_everything_demonstration,
)
from .tianhe import TianheLine, 天和线
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
    "Pingzi",
    "peculiar_asymmetry",
    "冰子",
    "瓶子",
    "Jizi",
    "Zijiji",
    "ThermalDual",
    "thermal_dual",
    "机子",
    "子机机",
    "热对偶",
    "AburaSobaProfile",
    "NoodleCanvas",
    "OilLayer",
    "TareBlend",
    "Topping",
    "assemble_abura_soba",
    "油そば",
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
    "DegreeSpace",
    "DegreeDual",
    "DegreeTensor",
    "tensor_product",
    "MetaverseBlueprint",
    "bond_metaverse_with_love",
    "ideal_metaverse_universe",
    "metaverse_metric",
    "run_ideal_metaverse",
    "MetaSpacetimeBlueprint",
    "ideal_meta_spacetime_universe",
    "meta_spacetime_metric",
    "run_meta_spacetime",
    "EverythingDemonstrationBlueprint",
    "physical_everything_demonstration_universe",
    "physical_everything_metric",
    "run_physical_everything_demonstration",
    "TianheLine",
    "天和线",
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
