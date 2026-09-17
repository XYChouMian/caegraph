# ADR-019: Phase 2 CAEGraph 实体/关系最小模型与 cell-based 构造语义

- 编号：ADR-019
- 标题：冻结 Phase 2 的 CAEGraph 实体与关系最小数据模型（node graph）、cell-based 构造语义（face 展开去重、region 驱动 NodeCategory）与构造期 field 长度校验；多图构造、几何特征挂载与序列化继续出清
- 日期：2026-09-17
- 状态：accepted（2026-09-17 经 Slice 3a 派单预审采纳，D1–D6 决策冻结）
- 关联：ADR-015（canonical 表示）、ADR-016（构造契约——本 ADR 为其"随派单定稿"的构造语义提供数据模型依据）、ADR-017（后端适配，下游）、ADR-018（领域组成——本 ADR 即其出清的 entity identity 与 relation 存储的 dedicated ADR）、ADR-014（cell-based 拓扑规范）、Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

ADR-018 将实体身份（ID schema）与 relation 存储形式（含 edge container）显式移交后续 dedicated ADR；而 gate 4 的 representation builder 必须落地实体+关系存储——构造无法绕过数据模型决策。本 ADR 即该 dedicated ADR：只冻结 Phase 2 cell-based 构造所需的最小模型，其余继续出清。

## 决策（Decision）

1. **实体模型（Phase 2 cell-based）**：实体 = mesh 节点；实体 ID = canonical 全局节点 ID（即 Mesh 节点存储索引，positional）；身份范围为单 CAEGraph 实例内。多命名空间 ID、跨实例/序列化/分布式身份继续出清（ADR-018 出清项不回收）。
2. **关系模型（node graph）**：无向节点对关系，由全部 canonical cells 的 codim-1 face 模板展开生成——每个 face 的连续节点对（含环回）即一条候选边（TRI3 face → 1 条、QUAD4 face → 4 条）；全局规范化为 `(min, max)`、去重、排序。**1D 特例**：`topo_dim == 1` 时 cell（LINE2）本身即边，贡献其节点对（其 codim-1 faces 为维度 0 的点，不入 canonical topology，ADR-014）。cell-center 图记录为未来扩展，不在 Phase 2 实现。
3. **存储语义**：关系以规范化去重的无序对集合语义存储于 CAEGraph；每实体携带 NodeCategory 注解。容器实现形式（tuple 对列表 vs CSR）为实现细节，不冻结；序列化与 batching 继续出清。
4. **NodeCategory 推导（region 驱动）**：构造期由语义区域推导——节点不属于任何 region → INTERIOR；恰属 1 个 → BOUNDARY；≥2 个 → CORNER。region 成员（canonical facet ID）经 Mesh 展开为节点集；未声明于任何 region 的边界节点保持 INTERIOR（显式语义限制，非缺陷）。
5. **构造签名语义**：输入 = Mesh + 显式传入的 BoundaryManager（region 所有权留在调用方）+ 可选 Fields；输出 = 完整填充的 CAEGraph（引用该 Mesh 为 topology provider）。构造期执行 field 长度校验：`association == "node"` ↔ `len(values) == n_nodes`、`association == "cell"` ↔ `len(values) == n_cells`（ADR-014 组成修订的落点）；其他 association 标签不做长度校验。
6. **出清项**：多图构造并存（node + cell-center）、几何特征挂载（geometry slice 兑现 Design UML 的 `MeshRepresentationBuilder ..> GeometryProcessor`）、增量更新、跨实例 ID、builder registry（单一 builder，第二 source 族出现再议）。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 同时实现 node graph 与 cell-center 图 | 否决 | Phase 2 无消费者；推迟到有 FVM 证据时按 ADR-016 扩展策略 |
| 实体 ID 引入独立命名空间/UUID | 否决 | ADR-018 出清项——影响 serialization/distributed/batching，证据未齐 |
| edge container 冻结为 CSR | 否决 | 过早优化；语义（规范化去重对集合）已足够，容器形式随性能证据定 |
| NodeCategory 由未声明边界 facet 推导（拓扑驱动） | 否决 | 边界语义唯一真源是 region（ADR-010/018）；拓扑面无语义身份，拓扑驱动推导会制造无语义的 BOUNDARY 噪声 |
| field 长度校验留在 CAEGraph.associate_field | 否决 | 校验需要 entity 计数（拓扑事实）；associate_field 不持有 topology 语义，ADR-014 组成修订已将其定位到表示构造层 |

## 影响（Consequences）

- gate 4 Coding（CAEGraph 实体/关系/NodeCategory 存储 + mesh representation builder）获得设计依据；builder API/命名/落位仍随 coding 派单定稿（ADR-016 不冻结项不变）。
- CAEGraph 增加构造期填充的最小图数据与只读访问器；ADR-018"语义组成不定义 class members"的原则不受影响——本 ADR 即授权该存储的 dedicated 立法。
- Backend adapter（gate 4 后半）消费本模型的 edges / node_categories 产出 PyG Data schema。
- 不引入新依赖、不改变依赖分层与 PyG 边界（ADR-007 不变）。

## 修订历史（Revision history）

- 2026-09-17 v1：最小可行决策——D1–D6 冻结，出清项显式记录。
- 2026-09-17 v2：补 1D 构造特例（LINE2 cell 贡献其节点对）——Slice 3a 复核发现 1D 空边集缺陷；accepted。
