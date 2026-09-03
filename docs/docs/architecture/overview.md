# 架构总览

本页是架构摘要；具有约束力的规范见
[`architecture/ARCHITECTURE.md`](https://github.com/caegraph/caegraph/blob/main/architecture/ARCHITECTURE.md)。

## 设计哲学

- 模块化设计——每个子包只承担一个职责
- 可复用组件——小而可组合的构建块
- 清晰抽象——只保留有文档、经过评审的抽象
- API 稳定性——已文档化的 API 即为契约
- 文档一致性——文档从代码生成

## 包地图

| 包 | 职责 | 依赖 |
| --- | --- | --- |
| `caegraph.core` | 基础抽象、注册机制、共享类型 | — |
| `caegraph.data` | CAE 数据加载、网格与图表示、数据集 | core |
| `caegraph.models` | GNN 组件、物理信息模型、Trainer | core, data |
| `caegraph.physics` | PDE 残差、物理损失、单位制 | core |
| `caegraph.visualization` | 网格/场/图可视化 | core, data |
| `caegraph.utils` | 日志、IO、可复现性工具 | — |

## UML 双体系

- **Design UML**（`architecture/design/`）——计划中的设计。
- **Generated UML**（`diagrams/generated/`）——代码的真实状态。

详见 [UML 指南](https://github.com/caegraph/caegraph/blob/main/architecture/UML_GUIDE.md)。
