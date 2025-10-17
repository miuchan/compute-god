# Intelligent Driving Lab 微交互复刻

`compute_god.intelligent_driving_lab` 把 [miuchan.github.io](http://miuchan.github.io/public/demo/intelligent-driving-lab/index.html)
上的演示页转译为结构化的 Python 数据模型：

* **Hero 区块**：`build_intelligent_driving_lab()` 返回的对象包含标题、标语与 CTA。
* **核心能力**：`DrivingCapability` 描述传感器、衡量指标与成熟度，用于生成展示卡片。
* **场景剧场**：`DrivingScenario` 收录北京夜市、成都绕城等代表性场景，方便快速对比。
* **交互模块**：`InteractionModule` 对应网页上的滑块、时间轴、场景编排器，`LabSection` 负责分组。

示例：

```python
from compute_god import build_intelligent_driving_lab, lab_summary_table

lab = build_intelligent_driving_lab()

for row in lab_summary_table(lab):
    print(f"{row['Scenario']}: {row['Focus']}")
```

输出一张可直接贴到 Wiki / CLI 的精简表格，实现“看得见的智能驾驶故事板”。

