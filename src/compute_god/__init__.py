"""Compute-God Python runtime."""

from types import ModuleType
import sys

from .guidance import DeskStation, GuidanceDesk
from .catalogue import build_guidance_desk, iter_export_names

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
    recursive_descent_fixpoint,
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
from .intelligent_driving_lab import (
    DrivingCapability,
    DrivingScenario,
    IntelligentDrivingLab,
    InteractionModule,
    LabSection,
    build_intelligent_driving_lab,
    find_capabilities_with_sensor,
    iter_module_highlights,
    lab_summary_table,
    scenarios_covering_capability,
)
from .dongyun import (
    DongyunBlueprint,
    dongyun_map,
    dongyun_metric,
    dongyun_universe,
    run_dongyun_institute,
    东云研究所,
)
from .momo import (
    MOMO_KEYS,
    MomoResonanceBlueprint,
    momo_resonance_metric,
    momo_time_universe,
    run_momo_time_harmony,
)
from .screenshot import ScreenshotEnvironment, ScreenshotTheme
from .github_feed import GitHubMobileFeed, IssueActivity, RepositoryCard, github_feed
from .github_offline import OfflineGitHub, IssueNotFound, RepositoryNotFound, access_github
from .git_compression import (
    CompressionAlgorithm,
    CompressionPlan,
    GitObjectProfile,
    git_friendly_algorithms,
    known_compression_algorithms,
    plan_repository_compression,
)
from .landscape_learning import (
    LandscapeLearningParameters,
    LandscapeSample,
    initialise_grid,
    landscape_learning_universe,
    learn_landscape,
)
from .factorio import (
    FactoryBalance,
    FactoryBlueprint,
    FactoryStep,
    Recipe,
)
from .gift import (
    GiftCoordinate,
    GiftGrid,
    GiftPlan,
    GiftWish,
    describe_gift_plan,
    prepare_gift_canvas,
    sculpt_gift_landscape,
)
from .pottery_gallery import (
    PedestalRow,
    PotteryDisplay,
    PotteryVessel,
    describe_display,
    generate_pottery_display,
)
from .live_and_let_live import (
    LiveAndLetLiveParameters,
    LiveAndLetLiveState,
    DEFAULT_LIVE_AND_LET_LIVE_STATE,
    live_and_let_live_step,
    run_live_and_let_live,
    让自己活也让别人活,
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
    recursive_descent_fixpoint=recursive_descent_fixpoint,
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
from .bingzi import (
    Bingzi,
    Mingzi,
    Pingzi,
    Liangzi,
    Weiliangzi,
    Weimingzi,
    peculiar_asymmetry,
    qianli_bingfeng,
    冰子,
    千里冰封,
    瓶子,
    明子,
    亮子,
    未亮子,
    未明子,
)
from .panzi import Panzi, PanziObservation, PanziOrigin, explore_origin, 磐子
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
    Mingzi,
    Pingzi,
    PingziRelation,
    Liangzi,
    Weiliangzi,
    Weimingzi,
    peculiar_asymmetry,
    qianli_bingfeng,
    冰子,
    千里冰封,
    瓶子,
    平子,
    明子,
    亮子,
    未亮子,
    未明子,
)
from .yuzi import (
    GridSummary,
    Qizi,
    QiziParameters,
    QuantumThermalDual,
    Yuzi,
    YuziParameters,
    quantum_thermal_dual,
    玉子,
    琦子,
    量子热对偶,
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
from .life_toolbox import (
    LifeNeed,
    ToolRitual,
    assemble_life_toolkit,
    design_energy_breaks,
    design_hydration_ritual,
    design_meal_landscape,
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
from .cooperation_evolution import (
    CooperationParameters,
    CooperationState,
    DEFAULT_COOPERATION_STATE,
    evolve_cooperation,
    run_cooperation_evolution,
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
    validate_proof,
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
from .touhou_project import (
    DEFAULT_BLUEPRINT as TOUHOU_DEFAULT_BLUEPRINT,
    ReimuNextSolution,
    TouhouIncidentBlueprint,
    TouhouIncidentState,
    reimu_next_solution,
    run_touhou_incident,
    touhou_incident_metric,
    touhou_incident_universe,
    博丽灵梦下一解,
)
from .vulkan import (
    DescriptorBinding,
    DescriptorSetLayout,
    RenderAttachment,
    RenderPassBlueprint,
    ShaderStageSpec,
    VulkanDeviceProfile,
    VulkanPipelinePlan,
    VulkanValidationError,
    plan_vulkan_pipeline,
)
from .s_follow_reading import (
    DEFAULT_FOLLOW_READING_STATE,
    FollowReadingBlueprint,
    FollowReadingFriendProfile,
    follow_reading_blueprint_from_friends,
    follow_reading_metric,
    follow_reading_rules,
    follow_reading_universe,
    run_follow_reading_network,
)

_GUIDANCE_SYMBOLS = dict(locals())

GUIDANCE_DESK = build_guidance_desk(_GUIDANCE_SYMBOLS)

def guidance_desk() -> GuidanceDesk:
    """Return the shared guidance desk instance (导诊台)."""

    return GUIDANCE_DESK


__all__ = list(iter_export_names())
__all__.extend(["DeskStation", "GuidanceDesk", "GUIDANCE_DESK", "guidance_desk"])
__all__.extend(["ScreenshotEnvironment", "ScreenshotTheme"])
__all__.extend([
    "GitHubMobileFeed",
    "IssueActivity",
    "RepositoryCard",
    "github_feed",
])
__all__.extend([
    "OfflineGitHub",
    "IssueNotFound",
    "RepositoryNotFound",
    "access_github",
])
__all__.extend([
    "CompressionAlgorithm",
    "CompressionPlan",
    "GitObjectProfile",
    "git_friendly_algorithms",
    "known_compression_algorithms",
    "plan_repository_compression",
])

del _GUIDANCE_SYMBOLS
