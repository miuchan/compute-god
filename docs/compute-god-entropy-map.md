# Compute-God 的源熵与熵源

本文整理 Compute-God 框架中“熵”坐标的来源，区分“源熵”（初始或目标熵值）与“熵源”（驱动熵变化的规则/函数），便于快速定位数值与收缩机制。

## 1. 源熵：默认宇宙给定的熵值

| 模块 | 默认状态中的熵 | 蓝图目标熵 | 说明 |
| --- | --- | --- | --- |
| `everything_demonstration` | `DEFAULT_PHYSICAL_DEMONSTRATION["entropy"] = 0.36`【F:src/compute_god/everything_demonstration.py†L127-L134】 | `EverythingDemonstrationBlueprint.entropy = 0.0`【F:src/compute_god/everything_demonstration.py†L154-L173】 | 物质-能量-信息闭环的初始熵较高，通过演化趋向零熵蓝图。对应的集成测试验证最终熵≈0。【F:tests/test_everything_demonstration.py†L8-L20】 |
| `meta_spacetime` | `DEFAULT_META_SPACETIME["entropy"] = 0.32`【F:src/compute_god/meta_spacetime.py†L135-L142】 | `MetaSpacetimeBlueprint.entropy = 0.0`【F:src/compute_god/meta_spacetime.py†L162-L181】 | 元时空默认带入有限熵，收敛到同步化蓝图时压缩至 0。测试中断言最终熵 ≤ 1e-2。【F:tests/test_meta_spacetime.py†L10-L22】 |

以上初始值即可视作“源熵”——计算神宇宙在迭代前持有的熵量，而蓝图中的目标值提供了熵收缩的终点。

## 2. 熵源：规则中的熵收缩机制

两个宇宙都通过 `_dampen_entropy` 辅助函数在多条规则里衰减熵：

- 物理演示：`_realise_materiality`、`_stabilise_energy_information`、`_close_observer_loop` 依次调用 `_dampen_entropy`，每步最多削减 0.05/0.06/0.04 的熵量，使熵在物质、能量与观察闭环中被逐级“抽走”。【F:src/compute_god/everything_demonstration.py†L55-L124】
- 元时空：`_stabilise_temporal`、`_stabilise_spatial`、`_couple_meta_axes` 使用 `_dampen_entropy`，分别以 0.08、0.05、0.04 的幅度压低熵值，确保时空轴与耦合同步时熵同步减少。【F:src/compute_god/meta_spacetime.py†L56-L132】

这些规则即可理解为“熵源”——它们决定熵如何被消耗或引导至蓝图所需的极限，配合度量（`physical_everything_metric`、`meta_spacetime_metric`）在 `fixpoint` 引擎中监控收敛。【F:src/compute_god/everything_demonstration.py†L145-L205】【F:src/compute_god/meta_spacetime.py†L145-L208】

## 3. 如何验证

运行仓库测试可直接观察两套熵机制的正确性：

```bash
pytest tests/test_everything_demonstration.py tests/test_meta_spacetime.py
```

以上测试分别确认熵坐标按照蓝图收敛与度量逐步减小。如需进一步分析，可在迭代中注册观察者，记录每个 epoch 的 `delta`（熵变化贡献包含在内）。【F:tests/test_meta_spacetime.py†L24-L44】

通过以上定位，可以快速回答“计算神的源熵和熵源在哪里”这一问题：源熵由默认状态和蓝图给定，熵源则是规则中对熵的收缩操作。
