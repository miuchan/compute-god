"""Compute-God Python runtime."""

from types import ModuleType
import sys

from .guidance import DeskStation, GuidanceDesk

from .core import (
    ApplyFn,
    FixpointEngine,
    FixpointResult,
    God,
    Observer,
    ObserverEvent,
    NoopObserver,
    Rule,
    PredicateFn,
    RuleContext,
    State,
    Universe,
    Metric,
    combine_observers,
    fixpoint,
    rule,
)
from .miyu import MiyuBond, bond_miyu
from .miuchan import (
    MiuchanBlueprint,
    bond_miuchan,
    miuchan_metric,
    miuchan_universe,
    run_miuchan_universe,
)


def _register_compat_module(name: str, **attrs: object) -> ModuleType:
    module = ModuleType(f"{__name__}.{name}")
    module.__dict__.update(attrs)
    module.__all__ = tuple(attrs.keys())  # type: ignore[attr-defined]
    sys.modules[f"{__name__}.{name}"] = module
    return module


_register_compat_module(
    "rule",
    Rule=Rule,
    rule=rule,
    ApplyFn=ApplyFn,
    PredicateFn=PredicateFn,
    RuleContext=RuleContext,
    State=State,
)
_register_compat_module(
    "engine",
    FixpointEngine=FixpointEngine,
    FixpointResult=FixpointResult,
    Metric=Metric,
    fixpoint=fixpoint,
)
_register_compat_module(
    "observer",
    Observer=Observer,
    ObserverEvent=ObserverEvent,
    NoopObserver=NoopObserver,
    combine_observers=combine_observers,
)
_register_compat_module(
    "universe",
    God=God,
    Universe=Universe,
)
from .bingzi import Bingzi, Pingzi, peculiar_asymmetry, qianli_bingfeng, 冰子, 千里冰封, 瓶子
from .jizi import (
    Jizi,
    ThermalDual,
    Zijiji,
    thermal_dual,
    机子,
    日子,
    子机机,
    月子,
    热对偶,
    自机子对偶,
)
from .eternity_end import EternityEndThermalDual, eternity_end_thermal_dual, 永恒终结热对偶
from .bingzi import (
    Bingzi,
    Pingzi,
    PingziRelation,
    peculiar_asymmetry,
    qianli_bingfeng,
    冰子,
    千里冰封,
    瓶子,
    平子,
)
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
from .jiahao import (
    JiahaoMaximumThermalDual,
    jiahao_max_thermal_dual,
    jiahao_max_thermal_dual_from_network,
    嘉豪最大热对偶,
)
from .yihong import YihongMiyuThermalDual, yihong_miyu_thermal_dual, 一弘美羽热对偶
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
from .anti_quantum import (
    AntiQuantumAlgorithm,
    AntiQuantumDual,
    QuantumAttackSurface,
    anti_quantum_dual,
    抗量子算法,
    抗量子对偶,
    量子攻击面,
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
from .mihoyo import (
    MihoyoStudioBlueprint,
    MiyuCreativeProfile,
    MiyuJoinsMihoyoResult,
    bond_miyu_with_mihoyo,
    mihoyo_alignment_metric,
    measure_mihoyo_fengshui,
    mihoyo_progress_metric,
    miyu_join_mihoyo_universe,
    run_miyu_join_mihoyo,
)
from .meta_spacetime import (
    MetaSpacetimeBlueprint,
    ideal_meta_spacetime_universe,
    meta_spacetime_metric,
    run_meta_spacetime,
)
from .complex_dynamics import (
    ComplexDynamicsBlueprint,
    complex_dynamics_metric,
    design_complex_dynamics_universe,
    run_complex_dynamics,
)
from .complex_network import (
    ComplexNetworkBlueprint,
    complex_network_metric,
    ideal_complex_network_universe,
    run_complex_network,
)
from .llm_cooperation import (
    DEFAULT_LLM_COOPERATION,
    LLMAgentContribution,
    LLMCooperationBlueprint,
    ideal_llm_cooperation_universe,
    llm_cooperation_blueprint_from_agents,
    llm_cooperation_metric,
    run_llm_cooperation,
)
from .everything_demonstration import (
    EverythingDemonstrationBlueprint,
    physical_everything_demonstration_universe,
    physical_everything_metric,
    run_physical_everything_demonstration,
)
from .drug_lab import (
    DrugLabOptimisationResult,
    drug_lab_metric,
    ideal_drug_lab_universe,
    run_drug_lab,
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
from .shengbing import ConceptCongruence, 生病全等于放屁
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
from .earth_rescue import EarthState, RescueParameters, rescue_map, save_earth
from .shuangxiang import (
    BiphasicOptimisationResult,
    BiphasicState,
    continue_biphasic_descent,
    optimise_biphasic_state,
    双相,
    双相梯度下降,
    继续梯度下降,
)


_SYMBOLS = dict(locals())

_STATION_LAYOUT = (
    (
        "core",
        "Core runtime primitives for building universes and solving fixed points.",
        (
            "ApplyFn",
            "PredicateFn",
            "Metric",
            "State",
            "RuleContext",
            "Rule",
            "rule",
            "God",
            "Universe",
            "combine_observers",
            "fixpoint",
            "FixpointEngine",
            "FixpointResult",
            "Observer",
            "ObserverEvent",
            "NoopObserver",
        ),
    ),
    (
        "bonds",
        "Bond-building blueprints connecting Miyu and companions across universes.",
        (
            "MiyuBond",
            "bond_miyu",
            "MiuchanBlueprint",
            "bond_miuchan",
            "miuchan_metric",
            "miuchan_universe",
            "run_miuchan_universe",
        ),
    ),
    (
        "august",
        "Narrative constructs capturing endless August loops and moods.",
        (
            "EndlessAugust",
        ),
    ),
    (
        "bingzi",
        "Thermal dual phenomena of the 冰子 universe and its asymmetries.",
        (
            "Bingzi",
            "Pingzi",
            "PingziRelation",
            "peculiar_asymmetry",
            "qianli_bingfeng",
            "冰子",
            "千里冰封",
            "瓶子",
            "平子",
        ),
    ),
    (
        "sanzi",
        "三子与维子的策略总览。",
        (
            "Sanzi",
            "SanziOverview",
            "Weizi",
            "三子",
            "维子",
        ),
    ),
    (
        "siqianzi",
        "死前子网络与热对偶变换。",
        (
            "Siqianzi",
            "SiqianziDualNode",
            "SiqianziDualEdge",
            "SiqianziThermalNetwork",
            "thermal_dual_network",
            "死前子",
            "死前子节点",
            "死前子连线",
            "死前子网络",
            "死前子热对偶网络",
        ),
    ),
    (
        "jizi",
        "自机子热对偶与其伙伴体系。",
        (
            "Jizi",
            "Zijiji",
            "ThermalDual",
            "thermal_dual",
            "机子",
            "日子",
            "子机机",
            "月子",
            "热对偶",
            "自机子对偶",
        ),
    ),
    (
        "eternity_end",
        "永恒终结热对偶研究。",
        (
            "EternityEndThermalDual",
            "eternity_end_thermal_dual",
            "永恒终结热对偶",
        ),
    ),
    (
        "jiahao",
        "嘉豪最大热对偶网络的变体与构造。",
        (
            "JiahaoMaximumThermalDual",
            "jiahao_max_thermal_dual",
            "jiahao_max_thermal_dual_from_network",
            "嘉豪最大热对偶",
        ),
    ),
    (
        "yihong",
        "一弘与美羽之间的热对偶。",
        (
            "YihongMiyuThermalDual",
            "yihong_miyu_thermal_dual",
            "一弘美羽热对偶",
        ),
    ),
    (
        "jiaose",
        "角子与色子的色角对偶关系。",
        (
            "Jiaozi",
            "Sezi",
            "ChromaticDual",
            "chromatic_dual",
            "角子",
            "色子",
            "色角对偶",
        ),
    ),
    (
        "culinary",
        "风味油そば宇宙的配方与画布。",
        (
            "AburaSobaProfile",
            "NoodleCanvas",
            "OilLayer",
            "TareBlend",
            "Topping",
            "assemble_abura_soba",
            "油そば",
        ),
    ),
    (
        "entanglement",
        "纠子、缠子与纠缠子的关联度量。",
        (
            "Entangler",
            "EntanglementSnapshot",
            "纠子",
            "缠子",
            "纠缠子",
        ),
    ),
    (
        "anti_quantum",
        "抗量子算法与对偶建模。",
        (
            "AntiQuantumAlgorithm",
            "AntiQuantumDual",
            "QuantumAttackSurface",
            "anti_quantum_dual",
            "抗量子算法",
            "抗量子对偶",
            "量子攻击面",
        ),
    ),
    (
        "existence",
        "存在性与稳定性的见证构造。",
        (
            "ExistenceWitness",
            "StabilityWitness",
            "存在子",
            "稳定子",
        ),
    ),
    (
        "love_wishing",
        "愿望机宇宙与其不动点推演。",
        (
            "WishParameters",
            "love_wishing_fixpoint",
            "love_wishing_map",
            "love_wishing_metric",
            "love_wishing_rule",
            "love_wishing_universe",
            "wish_granted",
        ),
    ),
    (
        "courtship",
        "求爱上同调的链复形。",
        (
            "CochainSpace",
            "CourtshipCochainComplex",
            "CourtshipDifferential",
            "courtship_cohomology_story",
        ),
    ),
    (
        "ctc",
        "闭合类时曲线的优化求解。",
        (
            "ClosedTimelikeCurve",
            "CTCOptimisationResult",
            "optimise_closed_timelike_curve",
        ),
    ),
    (
        "threshold",
        "门限空间的布局与最优化。",
        (
            "ThresholdSpace",
            "ThresholdOptimisationResult",
            "optimise_threshold_space",
        ),
    ),
    (
        "life",
        "生命游戏格点的演化调优。",
        (
            "LifeLattice",
            "LifeOptimisationResult",
            "optimise_game_of_life",
            "optimise_game_of_life_multistep",
        ),
    ),
    (
        "rule_optimisation",
        "规则权重的梯度化调节。",
        (
            "RuleOptimisationResult",
            "optimise_rule_weights",
        ),
    ),
    (
        "degree_space",
        "度空间的张量结构与对偶。",
        (
            "DegreeSpace",
            "DegreeDual",
            "DegreeTensor",
            "tensor_product",
        ),
    ),
    (
        "metaverse",
        "元宇宙蓝图与爱的绑定策略。",
        (
            "MetaverseBlueprint",
            "bond_metaverse_with_love",
            "ideal_metaverse_universe",
            "metaverse_metric",
            "run_ideal_metaverse",
        ),
    ),
    (
        "mihoyo",
        "米哈游工作室与美羽的结盟轨迹。",
        (
            "MihoyoStudioBlueprint",
            "MiyuCreativeProfile",
            "MiyuJoinsMihoyoResult",
            "bond_miyu_with_mihoyo",
            "mihoyo_alignment_metric",
            "measure_mihoyo_fengshui",
            "mihoyo_progress_metric",
            "miyu_join_mihoyo_universe",
            "run_miyu_join_mihoyo",
        ),
    ),
    (
        "meta_spacetime",
        "元时空蓝图与理想化运行。",
        (
            "MetaSpacetimeBlueprint",
            "ideal_meta_spacetime_universe",
            "meta_spacetime_metric",
            "run_meta_spacetime",
        ),
    ),
    (
        "complex_dynamics",
        "复杂动力系统的迭代设计。",
        (
            "ComplexDynamicsBlueprint",
            "complex_dynamics_metric",
            "design_complex_dynamics_universe",
            "run_complex_dynamics",
        ),
    ),
    (
        "complex_network",
        "复杂网络宇宙与指标体系。",
        (
            "ComplexNetworkBlueprint",
            "complex_network_metric",
            "ideal_complex_network_universe",
            "run_complex_network",
        ),
    ),
    (
        "llm_cooperation",
        "多智能体协作蓝图与指标。",
        (
            "LLMAgentContribution",
            "LLMCooperationBlueprint",
            "DEFAULT_LLM_COOPERATION",
            "ideal_llm_cooperation_universe",
            "llm_cooperation_blueprint_from_agents",
            "llm_cooperation_metric",
            "run_llm_cooperation",
        ),
    ),
    (
        "everything_demonstration",
        "万物演示计划的物理化执行。",
        (
            "EverythingDemonstrationBlueprint",
            "physical_everything_demonstration_universe",
            "physical_everything_metric",
            "run_physical_everything_demonstration",
        ),
    ),
    (
        "drug_lab",
        "药物实验室宇宙的调参策略。",
        (
            "DrugLabOptimisationResult",
            "drug_lab_metric",
            "ideal_drug_lab_universe",
            "run_drug_lab",
        ),
    ),
    (
        "tianhe",
        "天和线的轨迹建模。",
        (
            "TianheLine",
            "天和线",
        ),
    ),
    (
        "catalysis",
        "缠子与纠子在催化场景中的协同。",
        (
            "CatalysisOutcome",
            "Chanzi",
            "Jiuzi",
            "catalyse_jiuzi_and_chanzi",
        ),
    ),
    (
        "theorem",
        "定理证明器与推理规则。",
        (
            "InferenceRule",
            "Proof",
            "ProofStep",
            "modus_ponens",
            "reconstruct_proof",
            "run_theorem_prover",
            "theorem_metric",
            "theorem_proving_universe",
        ),
    ),
    (
        "elf_usdt",
        "ELF/USDT 市场的交换模型。",
        (
            "ELFUSDTMarket",
            "SwapDirection",
            "SwapEvent",
            "ELF",
            "USDT",
            "精灵",
            "泰达",
        ),
    ),
    (
        "adhd",
        "注意力缺陷情境下的参与度模拟。",
        (
            "StimulusProfile",
            "ADHDResponse",
            "ADHDProfile",
            "CoefficientOfEngagement",
            "simulate_coe",
        ),
    ),
    (
        "logic",
        "非子与若非的逻辑演算。",
        (
            "Feizi",
            "Ouzi",
            "Ruofei",
            "非子",
            "欧子",
            "若非",
        ),
    ),
    (
        "shengbing",
        "生病等价放屁的幽默同构。",
        (
            "ConceptCongruence",
            "生病全等于放屁",
        ),
    ),
    (
        "utawarerumono",
        "传颂之物的吟唱结构。",
        (
            "Utawarerumono",
            "UtawarerumonoChant",
            "LegendChant",
            "传颂之物",
        ),
    ),
    (
        "world",
        "世界执行请求的编排器。",
        (
            "WorldExecutionRequest",
            "world_execute",
        ),
    ),
    (
        "earth_rescue",
        "地球拯救计划的策略映射。",
        (
            "EarthState",
            "RescueParameters",
            "rescue_map",
            "save_earth",
        ),
    ),
    (
        "shuangxiang",
        "双相梯度下降与相关优化。",
        (
            "BiphasicState",
            "BiphasicOptimisationResult",
            "continue_biphasic_descent",
            "optimise_biphasic_state",
            "双相",
            "双相梯度下降",
            "继续梯度下降",
        ),
    ),
)


GUIDANCE_DESK = GuidanceDesk(
    DeskStation(name, description, {symbol: _SYMBOLS[symbol] for symbol in symbols})
    for name, description, symbols in _STATION_LAYOUT
)


def guidance_desk() -> GuidanceDesk:
    """Return the shared guidance desk instance (导诊台)."""

    return GUIDANCE_DESK


__all__ = []
for _, _, symbols in _STATION_LAYOUT:
    for symbol in symbols:
        if symbol not in __all__:
            __all__.append(symbol)
__all__.extend(["DeskStation", "GuidanceDesk", "GUIDANCE_DESK", "guidance_desk"])
