# ADR-015: 提案——Canonical CAEGraph representation（graph-first 范式评估）

- 编号：ADR-015
- 标题：评估是否将最高层领域真源从 Mesh（单元拓扑真源）翻转为 CAEGraph
  （图原生真源）；若采纳，本 ADR 取代 ADR-007 D1/D2/D3、ADR-008 图后端
  冻结条款、ADR-009、并重定义 ADR-012/014 的顶层对象
- 日期：2026-09-07
- 状态：**proposed（草稿待 Architecture review，未生效）**
- 关联：ADR-007（拟取代 D1/D2/D3 相关）、ADR-008（拟取代定位/图后端冻结
  相应条款）、ADR-009（拟取代）、ADR-012/014（拟重定义顶层对象）、
  ADR-011（future-evolution 机制先例）、Phase 2、ROADMAP、Design UML
  `class_diagram.puml`

## 背景（Context）

Phase 2 开工后的架构再评估提出一个**更高一层**的问题：根领域对象应是
「单元拓扑真源（Mesh-first，现状）」还是「图原生表示（graph-first，
本提案候选）」？

本 ADR **不是对 ADR-014 的否定**：ADR-014 解决的是「backend 无关的
canonical topology 如何规范化」，其结论（稳定 global ID、winding-free
facet、facet↔cell 强校验、region 引用拓扑）正确且有独立价值。本 ADR
问的是它是否为最高层：Mesh 是否应作为 cell-based CAE 的一种 topology
view/source specialization，而非 universal domain truth。

候选假设：

```
source formats
    ↓
source normalization
    ↓
CAEGraph canonical representation
    ↓
+-------------+---------------+
|                            |
v                            v
PyG adapter            physics / geometry operations
（torch_geometric）    （若图原生为真源）

Mesh = 一种 source representation / topology view / FEM/FVM 特化，
       不再是 universal domain truth
```

## 动机（Motivation，支持 graph-first 的论据）

1. 真源与最终消费者对齐：CAEGraph 的终点是 GNN/图工作流
   （ADR-008：CAE → GNN → AI），graph 真源直接承载 id/feature/邻接。
2. 范式广度：SPH、粒子、点云、无网格方法天然不含 CellType/facet/element；
   强制其走 Mesh = 人为适配。
3. 各范式可统一为「图构造策略」：FEM elements→topology graph；FVM
   cells→adjacency graph；SPH particles→neighbor graph；point cloud
   →geometric-neighbor graph。
4. 移除「Mesh 是通用网格框架」的越界感，更贴合 ADR-008 工作流定位。

## 冲突与代价（决定前必须正面处理，本 ADR 若采纳须取代）

| 冻结条款 | 冲突内容 |
| --- | --- |
| ADR-007 D2：core/geometry/io 永不 import PyG | 若 canonical CAEGraph 是 `torch_geometric.data.Data` 且置于 core → 破戒 |
| ADR-008：禁止替代图后端层（no alternative graph backend without a new ADR） | 若 core 中的 graph-native 真源**不是** PyG → 正是被冻结的替代图后端；本 ADR 是那纸 "new ADR"，但必须自证必要性 |
| ADR-009：BaseObject 限于 domain truth；Graph/CAEDataset/Model 用原生基类；GraphBuilder 拥有 Mesh→Graph | graph 升格为 domain truth 后，GraphBuilder 的「转换」职责与「原生基类」契约需重写 |
| ADR-014：canonical Mesh 数据模型 | 若 Mesh 降为 view，其 canonical topology 内容须并入 CAEGraph 拓扑子系统（换名不换实风险） |
| ADR-012：source normalization → canonical Mesh | normalization 目标对象改为 CAEGraph |
| Phase 2–4 roadmap（ARCHITECTURE.md §6 / ROADMAP） | 全部 mesh-centric：gmsh→graph、新网格神经仿真、VTK 写回；SPH/点云不在任何 Phase → graph-first 现阶段无外部消费者 |

**信息保真反证（最重）**：FEM/FVM 工作流在真源层需要单元类型、facet、
BC 区域、场关联来支撑 flux/Jacobian、facet↔cell 校验、VTK 拓扑一致性
（Phase 2 validation focus）。若 graph-first 的真源是 lossy 邻接图，
这些校验失去锚点；除非 canonical graph 携带完整 cell/facet 语义——那
等于把 Mesh 塞回图内，属**换名不换实**而非范式演进。

**概念成本**：ADR-007 的哲学是「工程真源与学习后端解耦」。graph-first
若回避 PyG = 再造图抽象（撞 ADR-008）；若拥抱 PyG = 领域真源耦合 ML
后端（撞 ADR-007 D2 精神）。

## 决策范围（本提案一旦采纳须冻结的问题）

1. **主领域对象**：CAEGraph 还是 Mesh？cell-based 场景内是否仍保 Mesh 真源？
2. **身份契约**：node/edge/cell-entity/facet-entity/field-association 的
   编址空间——ADR-014 已有成熟答案（global IDs + facet 表），平移还是重构？
3. **多范式表示**：cell-free 范式（SPH/点云）是否进入当前 contract，还是
   以 Phase 边界限定 cell-based、graph-first 仅作未来演进触发？
4. **关系**：CAEGraph ↔ PyG adapter ↔ Mesh topology ↔ geometry 层的
   依赖方向与真源判定。

## 备选方案（Options considered，待评审裁决）

| 方案 | 状态 | 评估要点 |
| --- | --- | --- |
| A. graph-first（本提案） | 待评 | 需取代 5 份 ADR 相关条款；直面 D2+ADR-008 冲突；roadmap 无 cell-free 消费者；信息保真锚点风险 |
| B. Mesh-first（现状） | 待评 | cell-based 保真完整；泛化缺口（SPH/点云）记入 future-evolution（ADR-011 同构机制），触发条件=非 cell 范式进入 roadmap |
| C. hybrid：Mesh=cell-based 真源 + 独立「entity-free 邻接源」通道（SPH/点云不进 Mesh、直接在 graph 层构造） | 待评 | 满足非 cell 诉求而不降级 Mesh；代价=io/graph 契约面积扩大 |

## 影响（Consequences，无论裁决均适用）

- **CellType 不消失**：local-node conventions、codim-1 face templates、
  显式稳定编码在本提案任何结局下均存活——成为 topology 语义注解层
  （可能从「Mesh 属性」平移为「CAEGraph 拓扑层注解」）。
- **本 ADR 生效前**：暂停 `mesh.py` / io adapter 的前向实现。当前
  `feature/mesh-core` 仅含已过 gate 的 CellType，无停工损失；topology
  primitives / Mesh 数据结构设计等待裁决。
- **ADR-014 保持 accepted 且不被先行修改**——其细节真源价值独立于本
  提案结局；若裁决 A/C，再以本 ADR 为据重定义其顶层对象，不在此前
  污染原决策记录。
- 若裁决 B：本 ADR 的 graph-first 假设与触发条件归档为 future-evolution，
  状态置 superseded（被后续 ADR 取代）或 closed 记录。

## 建议评审路径

1. 先回答「信息保真反证」与「ADR-008 冻结冲突」两项 blocker 是否可解；
2. 再决定范式覆盖（roadmap 内仅 cell-based，还是现即纳入 cell-free）；
3. 最后定 A/B/C；裁决 A/C 需列取代清单并重写 ADR-012/014 顶层对象 +
   Design UML + phase2-cae-data.md 模块树。
