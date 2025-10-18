# 自应用与 ER=EPR 的统一实现

本文档记录 ``compute_god.self_application_er_epr`` 模块中提供的三个
具体构造，展示如何把 λ 演算中的自应用与 ER=EPR 桥接在同一张串图
上理解。

## 1. Y 组合子：语义回路的固定点

* **函数**：``compute_god.self_application_er_epr.y_combinator``
* **示例**：``compute_god.self_application_er_epr.factorial_via_y``

递归体并不显式引用自身，而是把潜在的递归调用当作参数传递。通过
自应用 ``(λx.g (x x)) (λx.g (x x))``，我们把输出端重新插回输入端，得
到满足 ``F = g(F)`` 的不动点。在模块里 ``factorial_via_y`` 证明了这一
点：阶乘的递归完全由 Y 组合子的回路支撑。

## 2. TFD 态：纠缠桥的几何纯化

* **函数**：``compute_god.self_application_er_epr.thermofield_double``
* **衡量**：``compute_god.self_application_er_epr.entanglement_entropy``

给定哈密顿量的本征能谱和温度参数 ``β``，``thermofield_double`` 会生
成标准的 TFD 向量：把热态纯化到左右两个 Hilbert 空间，使其自然纠缠。
``entanglement_entropy`` 计算其冯诺依曼熵，数值上验证“几何桥”确实携带
量子纠缠信息。

## 3. Choi–Jamiołkowski：过程≙态的桥接

* **函数**：``compute_god.self_application_er_epr.choi_state_from_kraus``
* **基态**：``compute_god.self_application_er_epr.bell_state``

通过 Kraus 算符集合描述的量子信道 ``Φ``，可以映射为一个双体系态
``J_Φ``，这正是 Choi–Jamiołkowski 同构。该函数把每个基算符
``|i⟩⟨j|`` 送入 ``Φ``，再把输出粘接到另一个副本上，最终得到
``dim_out × dim_in`` 维的 Choi 态矩阵。``bell_state`` 则提供
``|Φ^+⟩`` 作为参考，使“过程=纠缠态”的图像具象化。

## 4. 如何一起使用

```python
from compute_god.self_application_er_epr import (
    factorial_via_y,
    thermofield_double,
    entanglement_entropy,
    choi_state_from_kraus,
    bell_state,
)
import numpy as np

# 语义回路：Y 组合子
assert factorial_via_y(5) == 120

# 几何桥：TFD 态及纠缠熵
energies = [0.0, 1.0]
beta = 1.0
tfd = thermofield_double(energies, beta)
entropy_bits = entanglement_entropy(tfd, (2, 2))

# 过程=态：恒等信道的 Choi 态就是 Bell 慢线
identity = np.eye(2)
choi_identity = choi_state_from_kraus([identity])
bell = bell_state(2)
bell_projector = np.outer(bell, bell.conj())

assert np.allclose(choi_identity, bell_projector)
```

这段代码把“自应用回路”“ER 桥”“过程=态”同时摆在手边，形成互相映
射的三重粘接：语义、量子与几何。

