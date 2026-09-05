# 架构总览

本页是架构摘要；具有约束力的规范见
[`architecture/ARCHITECTURE.md`](https://github.com/XYChouMian/caegraph/blob/main/architecture/ARCHITECTURE.md)。

## 设计哲学

- 模块化设计——每个子包只承担一个职责
- 可复用组件——小而可组合的构建块
- 清晰抽象——只保留有文档、经过评审的抽象
- API 稳定性——已文档化的 API 即为契约
- 文档一致性——文档从代码生成

## 包地图

| 包 | 职责 | 依赖 |
| --- | --- | --- |
| `caegraph.core` | 域抽象：BaseObject、Mesh、Graph、Field；注册机制、共享枚举 | — |
| `caegraph.geometry` | 几何服务：度量、边特征、插值 | core |
| `caegraph.io` | 加载器（gmsh 首发）与写回（VTK）；格式注册表 | core |
| `caegraph.graph` | 图构建（节点图/单元图）与变换 | core, geometry |
| `caegraph.integrations` | 后端适配：PyG `to_pyg()`、PyG 数据集——唯一的 PyG 导入点 | core, graph |
| `caegraph.dataset` | 集合、变换、切分 | core, graph, integrations |
| `caegraph.physics` | PDE 残差、物理损失、约束 | core |
| `caegraph.models` | 可组合 GNN 组件、物理信息模型、Trainer | core, dataset, integrations, physics |
| `caegraph.visualization` | 网格/场/图可视化 | core, io, models |
| `caegraph.utils` | 日志、IO、可复现性工具 | — |

## UML 双体系

- **Design UML**（`architecture/design/`）——计划中的设计。
- **Generated UML**（`diagrams/generated/`）——代码的真实状态。

详见 [UML 指南](https://github.com/XYChouMian/caegraph/blob/main/architecture/UML_GUIDE.md)。
