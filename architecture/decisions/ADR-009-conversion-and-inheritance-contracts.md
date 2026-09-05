# ADR-009: 转换边界与原生继承契约

- 编号：ADR-009
- 标题：Mesh→Graph 由 GraphBuilder 承担；学习层遵循 PyG/PyTorch 原生继承
- 日期：2026-09-05
- 状态：accepted
- 关联：ADR-007、ADR-008、Phase 1–4、Design UML `class_diagram.puml`

## 背景（Context）

ADR-007/008 冻结了“工程真源框架无关、学习图表示 PyG 原生”的定位，但初版
Design UML 与 Phase 规划仍留下两处实现歧义：`Mesh.to_graph()` 会迫使 core
依赖上层 graph；同时让 Graph、Dataset、Model 继承 BaseObject 会与 PyG/PyTorch
的原生基类形成不必要的多继承和方法契约冲突。

## 决策（Decision）

1. Mesh→Graph 的公共转换入口是
   `GraphBuilder.build(mesh, *, view="node" | "cell") -> Graph`。
   `GraphBuilder` 位于 `caegraph.graph`，可以消费 core.Mesh 与 geometry 服务；
   Mesh 不提供 `to_graph()`，core 永不 import graph。
2. BaseObject 只服务于工程真源对象。Phase 2 的 Mesh 与 Field 继承 BaseObject；
   Graph、CAEDataset、Model 不继承 BaseObject。
3. 学习层沿用生态原生继承：Graph 继承 `torch_geometric.data.Data`，
   CAEDataset 继承 `torch_geometric.data.Dataset`，Model 继承
   `torch.nn.Module`。共享元数据和校验通过组合或各原生类的协议实现，不通过
   多继承复用 BaseObject。
4. `CAEDataset` 是公开类名，避免与 PyG 的 Dataset 混淆。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| Mesh.to_graph() + 延迟 import | 否决 | 隐藏而未消除 core→graph 的反向依赖 |
| Mesh 注入转换回调 | 否决 | 为便利方法引入额外协议与生命周期复杂度 |
| GraphBuilder.build(mesh) | 采纳 | 转换逻辑与依赖方向均落在 graph 层 |
| 六类统一继承 BaseObject | 否决 | 与 PyG/PyTorch 基类产生 MRO、validate 与状态管理冲突 |
| 工程真源继承 BaseObject，学习层原生继承 | 采纳 | 域模型纯净且直接兼容既有生态 |

## 影响（Consequences）

- core/geometry/io 可以持续保持 PyG-free，依赖 DAG 可由静态测试直接验证。
- Graph、CAEDataset、Model 分别遵循其生态的序列化、批处理与模块生命周期。
- 共享的 identity/metadata/validation 不能假设来自统一父类；跨层代码必须依赖
  明确协议或对象自身契约。
- ADR-007/008 的产品定位与包分层保持不变；本 ADR 仅消除转换入口和继承语义
  的实现歧义。
