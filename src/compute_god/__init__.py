"""Compute-God Python runtime."""

from __future__ import annotations

from importlib import metadata as _importlib_metadata
from pathlib import Path
from types import ModuleType
import sys
import tomllib
from typing import Any

# Extend the package search path so legacy ``compute_god.<module>`` imports keep
# working after reorganising the code base into dedicated sub-packages.
package_dir = Path(__file__).resolve().parent
_DOMAINS_DIR = package_dir / "domains"
if _DOMAINS_DIR.is_dir():  # pragma: no branch - guarded import path mutation
    __path__.append(str(_DOMAINS_DIR))

from .guidance import DeskStation, GuidanceDesk
from .catalogue import build_guidance_desk, iter_export_names
from .information_energy import (
    DescentPath,
    DescentStep,
    EnergyDescentNavigator,
    EnergyField,
    plan_energy_descent,
)
from .happiness_scheduler import (
    BlockQLearningScheduler,
    DIMENSIONS,
    GreedyScheduler,
    HappinessSimulator,
    LifeState,
    ModelParameters,
    StepResult,
    default_parameters,
    default_state,
    sampler_from_ranges,
)

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
from .domains.miyu import MiyuBond, bond_miyu
from .domains.miuchan import (
    MiuchanBlueprint,
    bond_miuchan,
    miuchan_metric,
    miuchan_universe,
    run_miuchan_universe,
)
from .domains.intelligent_driving_lab import (
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
from .domains.dongyun import (
    DongyunBlueprint,
    dongyun_map,
    dongyun_metric,
    dongyun_universe,
    run_dongyun_institute,
    东云研究所,
)
from .domains.momo import (
    MOMO_KEYS,
    MomoResonanceBlueprint,
    momo_resonance_metric,
    momo_time_universe,
    run_momo_time_harmony,
)
from .domains.screenshot import ScreenshotEnvironment, ScreenshotTheme
from .domains.github_feed import GitHubMobileFeed, IssueActivity, RepositoryCard, github_feed
from .domains.github_offline import OfflineGitHub, IssueNotFound, RepositoryNotFound, access_github
from .domains.git_compression import (
    CompressionAlgorithm,
    CompressionPlan,
    GitObjectProfile,
    git_friendly_algorithms,
    known_compression_algorithms,
    plan_repository_compression,
)
from .domains.landscape_learning import (
    LandscapeLearningParameters,
    LandscapeSample,
    initialise_grid,
    landscape_learning_universe,
    learn_landscape,
)
from .domains.limit_language import (
    ComputableFunction,
    DomainSpec,
    LimitApproach,
    LimitProgram,
    LimitResult,
    LimitStatement,
    parse_limit_language,
)
from .domains.factorio import (
    FactoryBalance,
    FactoryBlueprint,
    FactoryStep,
    Recipe,
)
from .domains.gift import (
    GiftCoordinate,
    GiftGrid,
    GiftPlan,
    GiftWish,
    describe_gift_plan,
    prepare_gift_canvas,
    sculpt_gift_landscape,
)
from .domains.earth_online_council import (
    CouncilAgenda,
    CouncilMandate,
    CouncilMember,
    council_transition,
    simulate_ai_council,
)
from .domains.leshan_buddha import (
    BuddhaSegment,
    DrainageChannel,
    LeshanBuddhaModel,
    ObservationPlatform,
    build_leshan_buddha,
    iter_segment_features,
)
from .domains.lehuo_lefo import (
    LehuoLefoThermalDual,
    lehuo_lefo_thermal_dual,
    乐活乐佛热对偶,
)
try:  # pragma: no cover - optional dependency during import
    from .domains.self_application_er_epr import (
        bell_state,
        choi_state_from_kraus,
        entanglement_entropy,
        factorial_via_y,
        thermofield_double,
        y_combinator,
    )
except ImportError:  # pragma: no cover - numpy may be unavailable in minimal installs
    pass
from .domains.pottery_gallery import (
    PedestalRow,
    PotteryDisplay,
    PotteryVessel,
    describe_display,
    generate_pottery_display,
)
from .domains.live_and_let_live import (
    LiveAndLetLiveParameters,
    LiveAndLetLiveState,
    DEFAULT_LIVE_AND_LET_LIVE_STATE,
    live_and_let_live_step,
    run_live_and_let_live,
    让自己活也让别人活,
)
from .domains.shulikou import (
    ShuliKouBlueprint,
    ShuliKouGlyph,
    ShuliKouReading,
    ShuliKouVector,
    compose_shuli_channels,
    术力口,
)
from .domains.shulikou_cloud_village import (
    CloudVillageCooperative,
    CooperativeInitiative,
    CooperativeMember,
    build_shulikou_cloud_village,
)
from .domains.yin_yang_wu_xing import (
    Element,
    Polarity,
    Trigram,
    arrange_bagua,
    generation_cycle,
    overcoming_cycle,
    trigram,
    trigram_from_lines,
)


def _find_pyproject_file() -> Path | None:
    """Return the nearest ``pyproject.toml`` file, if available."""

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def _load_local_version(pyproject: Path) -> str | None:
    """Load the package version from a local ``pyproject.toml`` file."""

    try:
        with pyproject.open("rb") as stream:
            data: dict[str, Any] = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError):  # pragma: no cover - defensive guard
        return None

    project = data.get("project")
    if isinstance(project, dict):
        version = project.get("version")
        if isinstance(version, str):
            return version
    return None


def _load_version() -> str:
    """Best-effort loader for the distribution version string."""

    try:
        return _importlib_metadata.version("compute-god")
    except _importlib_metadata.PackageNotFoundError:
        pyproject = _find_pyproject_file()
        if pyproject is not None:
            version = _load_local_version(pyproject)
            if version is not None:
                return version
    return "0.0.0"


__version__ = _load_version()


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
from .domains.bingzi import (
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
from .domains.panzi import Panzi, PanziObservation, PanziOrigin, explore_origin, 磐子
from .domains.jizi import (
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
from .domains.eternity_end import EternityEndThermalDual, eternity_end_thermal_dual, 永恒终结热对偶
from .domains.bingzi import (
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
from .domains.yuzi import (
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
from .domains.sanzi import Sanzi, SanziOverview, Weizi, 三子, 维子
from .domains.siqianzi import (
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
from .domains.dianfen_changzi import (
    StarchSausageEquilibrium,
    StarchSausageNetworkGame,
    StarchSausagePlayer,
    build_starch_sausage_game,
    simulate_starch_sausage_game,
    淀粉肠子均衡,
    淀粉肠子网络,
    淀粉肠子玩家,
    淀粉肠子网络博弈,
)
from .domains.jiahao import (
    JiahaoMaximumThermalDual,
    jiahao_max_thermal_dual,
    jiahao_max_thermal_dual_from_network,
    嘉豪最大热对偶,
)
from .domains.yihong import YihongMiyuThermalDual, yihong_miyu_thermal_dual, 一弘美羽热对偶
from .domains.jiaose import ChromaticDual, Jiaozi, Sezi, chromatic_dual, 角子, 色子, 色角对偶
from .domains.august import EndlessAugust
from .domains.abura_soba import (
    AburaSobaProfile,
    NoodleCanvas,
    OilLayer,
    TareBlend,
    Topping,
    assemble_abura_soba,
    油そば,
)
from .domains.entangle import (
    Chanzi,
    Entangler,
    EntanglementSnapshot,
    Jiuzi,
    纠子,
    缠子,
    纠缠子,
)
from .domains.quantum_decoherence import (
    KNOWN_QUANTUM_MECHANISMS,
    DecoherenceEnvironment,
    DecoherenceLedger,
    DecoherenceResult,
    QuantumMechanism,
    decohere_all_known_quantum_mechanisms,
    decoherence_for_mechanism,
    退相干所有量子机制,
)
from .domains.anti_quantum import (
    AntiQuantumAlgorithm,
    AntiQuantumDual,
    QuantumAttackSurface,
    anti_quantum_dual,
    抗量子算法,
    抗量子对偶,
    量子攻击面,
)
from .domains.existence import ExistenceWitness, StabilityWitness, 存在子, 稳定子
from .domains.ctc import ClosedTimelikeCurve, CTCOptimisationResult, optimise_closed_timelike_curve
from .domains.threshold import ThresholdSpace, ThresholdOptimisationResult, optimise_threshold_space
from .domains.life import (
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
from .domains.rule_optimisation import RuleOptimisationResult, optimise_rule_weights
from .domains.degree_space import DegreeDual, DegreeSpace, DegreeTensor, tensor_product
from .domains.metaverse import (
    MetaverseBlueprint,
    bond_metaverse_with_love,
    ideal_metaverse_universe,
    metaverse_metric,
    run_ideal_metaverse,
)
from .domains.mihoyo import (
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
from .domains.meta_spacetime import (
    MetaSpacetimeBlueprint,
    ideal_meta_spacetime_universe,
    meta_spacetime_metric,
    run_meta_spacetime,
)
from .domains.complex_dynamics import (
    ComplexDynamicsBlueprint,
    complex_dynamics_metric,
    design_complex_dynamics_universe,
    run_complex_dynamics,
)
from .domains.complex_network import (
    ComplexNetworkBlueprint,
    complex_network_metric,
    ideal_complex_network_universe,
    run_complex_network,
)
from .domains.cooperation_evolution import (
    CooperationParameters,
    CooperationState,
    DEFAULT_COOPERATION_STATE,
    evolve_cooperation,
    run_cooperation_evolution,
)
from .domains.llm_cooperation import (
    DEFAULT_LLM_COOPERATION,
    LLMAgentContribution,
    LLMCooperationBlueprint,
    ideal_llm_cooperation_universe,
    llm_cooperation_blueprint_from_agents,
    llm_cooperation_metric,
    run_llm_cooperation,
)
from .domains.llm_agent_taxonomy import (
    CAPABILITY_KEYS,
    AgentTaskRequirement,
    LLMTypeProfile,
    LLM_TYPE_PROFILES,
    compose_llm_stack,
    iter_llm_type_profiles,
    rank_llm_types,
    score_llm_profile,
)
from .domains.everything_demonstration import (
    EverythingDemonstrationBlueprint,
    physical_everything_demonstration_universe,
    physical_everything_metric,
    run_physical_everything_demonstration,
)
from .domains.drug_lab import (
    DrugLabOptimisationResult,
    drug_lab_metric,
    ideal_drug_lab_universe,
    run_drug_lab,
)
from .domains.tianhe import TianheLine, 天和线
from .domains.catalysis import (
    CatalysisOutcome,
    Chanzi,
    Jiuzi,
    catalyse_jiuzi_and_chanzi,
)
from .domains.theorem import (
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
from .domains.elf_usdt import (
    ELFUSDTMarket,
    SwapDirection,
    SwapEvent,
    ELF,
    USDT,
    精灵,
    泰达,
)
from .domains.adhd import (
    ADHDProfile,
    ADHDResponse,
    CoefficientOfEngagement,
    StimulusProfile,
    simulate_coe,
)
from .domains.logic import Feizi, Ouzi, Ruofei, 非子, 欧子, 若非
from .domains.xuyueming import (
    UprootStep,
    WillowBranch,
    WeepingWillow,
    WillowUprootPlan,
    XuYuemingTechnique,
    倒拔垂杨柳,
    许月明,
)
from .domains.shengbing import ConceptCongruence, 生病全等于放屁
from .domains.utawarerumono import LegendChant, Utawarerumono, UtawarerumonoChant, 传颂之物
from .domains.love_wishing_machine import (
    WishParameters,
    love_wishing_fixpoint,
    love_wishing_map,
    love_wishing_metric,
    love_wishing_rule,
    love_wishing_universe,
    wish_granted,
)
from .domains.courtship_cohomology import (
    CochainSpace,
    CourtshipCochainComplex,
    CourtshipDifferential,
    courtship_cohomology_story,
)
from .domains.world import WorldExecutionRequest, world_execute
from .domains.earth_rescue import EarthState, RescueParameters, rescue_map, save_earth
from .domains.shuangxiang import (
    BiphasicOptimisationResult,
    BiphasicState,
    continue_biphasic_descent,
    optimise_biphasic_state,
    双相,
    双相梯度下降,
    继续梯度下降,
)
from .domains.touhou_project import (
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
from .domains.vulkan import (
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
from .domains.s_follow_reading import (
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

# Maintain backwards compatibility by aliasing restructured modules to their
# historical ``compute_god.<module>`` import paths.  Without this step Python
# would load two distinct module objects (``compute_god.<name>`` and
# ``compute_god.domains.<name>``) leading to isinstance checks failing across
# boundaries such as the Miyu ecosystem.
if _DOMAINS_DIR.is_dir():
    for _module_file in _DOMAINS_DIR.glob("*.py"):
        if _module_file.name == "__init__.py":
            continue
        _module_name = _module_file.stem
        _domain_qualname = f"{__name__}.domains.{_module_name}"
        _legacy_qualname = f"{__name__}.{_module_name}"
        _module = sys.modules.get(_domain_qualname)
        if _module is not None:
            sys.modules[_legacy_qualname] = _module
    del _module_file, _module_name, _domain_qualname, _legacy_qualname, _module

GUIDANCE_DESK = build_guidance_desk(_GUIDANCE_SYMBOLS)

def guidance_desk() -> GuidanceDesk:
    """Return the shared guidance desk instance (导诊台)."""

    return GUIDANCE_DESK


__all__ = list(iter_export_names())
__all__.extend(["DeskStation", "GuidanceDesk", "GUIDANCE_DESK", "guidance_desk"])
__all__.extend(["ScreenshotEnvironment", "ScreenshotTheme"])
__all__.extend([
    "DescentPath",
    "DescentStep",
    "EnergyDescentNavigator",
    "EnergyField",
    "plan_energy_descent",
])
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
__all__.append("__version__")

del _GUIDANCE_SYMBOLS
