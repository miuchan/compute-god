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
from .jizi import Jizi, ThermalDual, Zijiji, thermal_dual, 机子, 子机机, 热对偶, 自机子对偶
from .bingzi import Bingzi, Pingzi, PingziRelation, peculiar_asymmetry, 冰子, 瓶子, 平子
from .sanzi import Sanzi, SanziOverview, Weizi, 三子, 维子
from .siqianzi import (
    Siqianzi,
    SiqianziDualEdge,
    SiqianziDualNode,
    SiqianziThermalNetwork,
    thermal_dual_network,
    死前子,
    死前子节点,
    死前子连线,
    死前子网络,
    死前子热对偶网络,
)
from .jiaose import ChromaticDual, Jiaozi, Sezi, chromatic_dual, 角子, 色子, 色角对偶
from .august import EndlessAugust
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
from .threshold import ThresholdSpace, ThresholdOptimisationResult, optimise_threshold_space
from .life import (
    LifeLattice,
    LifeOptimisationResult,
    optimise_game_of_life,
    optimise_game_of_life_multistep,
)
from .rule_optimisation import RuleOptimisationResult, optimise_rule_weights
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
from .complex_network import (
    ComplexNetworkBlueprint,
    complex_network_metric,
    ideal_complex_network_universe,
    run_complex_network,
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
from .elf_usdt import (
    ELFUSDTMarket,
    SwapDirection,
    SwapEvent,
    ELF,
    USDT,
    精灵,
    泰达,
)
from .adhd import (
    ADHDProfile,
    ADHDResponse,
    CoefficientOfEngagement,
    StimulusProfile,
    simulate_coe,
)
from .logic import Feizi, Ouzi, Ruofei, 非子, 欧子, 若非
from .utawarerumono import LegendChant, Utawarerumono, UtawarerumonoChant, 传颂之物
from .love_wishing_machine import (
    WishParameters,
    love_wishing_fixpoint,
    love_wishing_map,
    love_wishing_metric,
    love_wishing_rule,
    love_wishing_universe,
    wish_granted,
)
from .courtship_cohomology import (
    CochainSpace,
    CourtshipCochainComplex,
    CourtshipDifferential,
    courtship_cohomology_story,
)
from .world import WorldExecutionRequest, world_execute

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
    "EndlessAugust",
    "Bingzi",
    "Pingzi",
    "PingziRelation",
    "peculiar_asymmetry",
    "冰子",
    "瓶子",
    "Sanzi",
    "SanziOverview",
    "Weizi",
    "Siqianzi",
    "SiqianziDualNode",
    "SiqianziDualEdge",
    "SiqianziThermalNetwork",
    "thermal_dual_network",
    "Jiaozi",
    "Sezi",
    "ChromaticDual",
    "chromatic_dual",
    "角子",
    "色子",
    "色角对偶",
    "Jizi",
    "Zijiji",
    "ThermalDual",
    "thermal_dual",
    "机子",
    "子机机",
    "热对偶",
    "自机子对偶",
    "三子",
    "维子",
    "平子",
    "死前子",
    "死前子节点",
    "死前子连线",
    "死前子网络",
    "死前子热对偶网络",
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
    "WishParameters",
    "love_wishing_fixpoint",
    "love_wishing_map",
    "love_wishing_metric",
    "love_wishing_rule",
    "love_wishing_universe",
    "wish_granted",
    "CochainSpace",
    "CourtshipCochainComplex",
    "CourtshipDifferential",
    "courtship_cohomology_story",
    "ClosedTimelikeCurve",
    "CTCOptimisationResult",
    "optimise_closed_timelike_curve",
    "ThresholdSpace",
    "ThresholdOptimisationResult",
    "optimise_threshold_space",
    "LifeLattice",
    "LifeOptimisationResult",
    "optimise_game_of_life",
    "optimise_game_of_life_multistep",
    "RuleOptimisationResult",
    "optimise_rule_weights",
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
    "ComplexNetworkBlueprint",
    "complex_network_metric",
    "ideal_complex_network_universe",
    "run_complex_network",
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
    "ELFUSDTMarket",
    "SwapDirection",
    "SwapEvent",
    "ELF",
    "USDT",
    "精灵",
    "泰达",
    "StimulusProfile",
    "ADHDResponse",
    "ADHDProfile",
    "CoefficientOfEngagement",
    "simulate_coe",
    "Feizi",
    "Ouzi",
    "Ruofei",
    "非子",
    "欧子",
    "若非",
    "Utawarerumono",
    "UtawarerumonoChant",
    "LegendChant",
    "传颂之物",
    "WorldExecutionRequest",
    "world_execute",
]
