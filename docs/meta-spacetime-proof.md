# 元时空的存在性与稳定性证明

本文把「元时空」（meta spacetime）具体化为 Compute-God 运行时中的一个
可计算宇宙：状态由空间（topos）、时间（chronos）与耦合协调量构成，规则
以收缩映射的形式迭代推进。通过构造性的不动点求解，既给出元时空存在的
见证，也展示其在扰动下的稳定性。

## 1. 形式化定义

我们在 `compute_god.meta_spacetime` 中定义元时空宇宙 `U = (S, R, M)`：

- `S`：状态空间为 `MetaSpacetimeState`，每个坐标都位于 `[0, 1]` 内。
- `R`：规则集包含三条收缩变换，分别协调时间轴、空间轴与两者的耦合：
  - `stabilise-temporal`：推动 `chronos`、`causality`、`continuity`
    朝 1.0 与 `chronos` 的中线逼近，同时衰减 `entropy`。
  - `stabilise-spatial`：使 `topos` 与 `continuity` 收敛，并同步提升
    `coherence`。
  - `couple-meta-axes`：把空间与时间的均值反馈给耦合量，进一步压低熵。
- `M`：度量函数为 `meta_spacetime_metric`，即所有核心坐标差值的绝对和。

代码实现如下：

```python
from compute_god import ideal_meta_spacetime_universe, meta_spacetime_metric
```

`ideal_meta_spacetime_universe()` 给出默认初态 `DEFAULT_META_SPACETIME` 与规则
集 `_build_meta_rules()`。【F:src/compute_god/meta_spacetime.py†L89-L118】

## 2. 存在性（不动点）

每条规则都只依赖当前状态的数值并进行线性收缩：

- `_towards(x, t, r) = x + r(t - x)` 满足 `|_towards(x, t, r) - t| = |1 - r|·|x - t|`。
- 在代码中，所有 `r` 取值位于 `(0, 1)`，因此是严格收缩映射。
- `_bounded` 保证状态仍处于 `[0, 1]`，`_dampen_entropy` 进一步收缩熵。

由 Banach 不动点定理可知，复合映射 `F = r₃ ∘ r₂ ∘ r₁` 在完备度量空间
`([0,1]^5 × [0,1], M)` 上存在唯一不动点。Compute-God 的 `fixpoint` 引擎以
迭代方式寻找 `F` 的不动点，从而给出元时空存在性的构造性证明。【F:src/compute_god/meta_spacetime.py†L17-L118】

测试 `test_meta_spacetime_converges_to_blueprint` 运行 `run_meta_spacetime`
并验证终态与蓝图（`MetaSpacetimeBlueprint`）在 `1e-2` 精度内吻合，提供了
计算见证。【F:tests/test_meta_spacetime.py†L6-L23】

## 3. 稳定性（扰动收敛）

稳定性通过度量 `meta_spacetime_metric` 与观察者记录的 `delta` 序列刻画：

- 每次迭代后，`delta = M(s_t, s_{t+1})` 度量状态变化量。
- `test_meta_spacetime_metric_decreases_monotonically` 证明该序列单调下降，
  即任意扰动都会被规则收缩直至满足 `epsilon` 阈值。【F:tests/test_meta_spacetime.py†L25-L43】
- 度量本身等于各坐标差的绝对和，`test_meta_spacetime_metric_matches_coordinate_differences`
  对其进行单元验证，确保收敛准则对应实际物理量。【F:tests/test_meta_spacetime.py†L45-L63】

此外，`run_meta_spacetime` 暴露 `epsilon` 与 `max_epoch` 参数，可在应用中
调节稳定所需的精度与迭代上限。【F:src/compute_god/meta_spacetime.py†L120-L136】

综上，元时空在 Compute-God 框架中被形式化为具备唯一不动点的收缩系统；
其存在性由不动点构造保证，稳定性则由度量单调递减与数值测试验证。
