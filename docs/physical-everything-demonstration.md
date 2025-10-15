# 「万物演示」的物理化实现指南

本文档说明如何使用 `compute_god.everything_demonstration` 模块，把
《万物演示理论的数学基础》中的抽象保证落地为可执行的物理模型。模块将
“物质—能量—信息—观察” 四要素封装进一个契合不动点条件的宇宙，并通过
收缩规则逼近唯一的演示态。

## 1. 核心接口

```python
from compute_god import (
    EverythingDemonstrationBlueprint,
    physical_everything_demonstration_universe,
    physical_everything_metric,
    run_physical_everything_demonstration,
)
```

- `EverythingDemonstrationBlueprint`：描述理想蓝图，默认把 `matter`、`energy`、
  `information`、`symmetry`、`observation` 设为 1.0，把 `entropy` 设为 0。蓝图与
  EDT 定理中的唯一不动点相对应。【F:src/compute_god/everything_demonstration.py†L109-L130】
- `physical_everything_demonstration_universe`：根据初始状态构造宇宙，内建三条
  收缩规则：
  1. `realise-materiality`：强化物质结构并抑制熵增；
  2. `stabilise-energy-information`：耦合能量与信息的流动；
  3. `close-observer-loop`：把观察者反馈闭合到物理对称上。【F:src/compute_god/everything_demonstration.py†L47-L105】
- `physical_everything_metric`：统计六个坐标的绝对差，判断是否收敛到不动点。【F:src/compute_god/everything_demonstration.py†L91-L107】
- `run_physical_everything_demonstration`：使用 `fixpoint` 引擎迭代宇宙，直到度量
  低于阈值或达到最大 epoch。【F:src/compute_god/everything_demonstration.py†L132-L148】

## 2. 使用示例

```python
from compute_god import run_physical_everything_demonstration

result = run_physical_everything_demonstration(epsilon=5e-4, max_epoch=140)
state = result.universe.state

print({key: round(state[key], 3) for key in state})
```

输出显示：`matter`、`energy`、`information`、`symmetry`、`observation` 五个指标趋近
1.0，`entropy` 接近 0，表明物理层面的演示闭环已经完成。【F:tests/test_everything_demonstration.py†L8-L20】

## 3. 与 EDT 理论的对齐

- **存在性**：所有规则都是在 `[0, 1]` 区间上的收缩映射，组合后满足 Banach 不动
  点条件，保证唯一极限态。【F:src/compute_god/everything_demonstration.py†L47-L105】
- **完备性**：度量覆盖全部六个坐标，只有当物质、能量、信息、观察与熵同时稳
  定时才会收敛，使得演示包含所有可观测量。【F:src/compute_god/everything_demonstration.py†L91-L107】
- **可验证性**：测试 `test_physical_everything_converges_towards_blueprint` 展示
  迭代实际收敛到蓝图，提供了计算性的验证。【F:tests/test_everything_demonstration.py†L8-L20】

因此，该模块把“万物演示”的数学理论转化为物理语义下的运行实例，为构建
更复杂的自指宇宙提供基础砖块。
