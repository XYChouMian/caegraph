# ADR-019: Phase 2 CAEGraph 实体族/关系最小模型与 cell-based 构造语义

- 编号：ADR-019
- 标题：冻结 Phase 2 的 CAEGraph 实体族（node/cell entities）与关系最小数据模型（node graph）、cell-based 构造语义（face 展开去重、region 驱动 NodeCategory 的适用边界）与构造期 field 基数校验；region 分类机制与多图构造、几何特征挂载、序列化继续出清或待裁
- 日期：2026-09-18（v3）
- 状态：proposed（v3 修订起草：D1/D4 决策级修订待报批重新采纳，获批前本 ADR 不标 accepted；v2 的 accepted 状态自本修订起草起挂起）
- 关联：ADR-015（canonical 表示）、ADR-016（构造契约——本 ADR 为其"随派单定稿"的构造语义提供数据模型依据）、ADR-017（后端适配，下游）、ADR-018（领域组成——本 ADR 即其出清的 entity identity 与 relation 存储的 dedicated ADR）、ADR-014（cell-based 拓扑规范）、Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

ADR-018 将实体身份（ID schema）与 relation 存储形式（含 edge container）显式移交后续 dedicated ADR；而 gate 4 的 representation builder 必须落地实体+关系存储——构造无法绕过数据模型决策。本 ADR 即该 dedicated ADR：只冻结 Phase 2 cell-based 构造所需的最小模型，其余继续出清。

v3 修订动因（三方审查结论）：v2 的 D1 将 domain entity 与 GNN vertex 混同（以 mesh 节点直接定义实体的表述与 ADR-018 "Fields are associated with entities" 及 `association == "cell"` 的事实矛盾）；D4 的 region-count 机械映射对 internal interface 与 physical group 语义失效；D2 的示例计数以偏概全；D5 的 Python 容器措辞过紧。Slice 3a 代码已通过终审，代码方向不变，本修订仅做文档级矫正与最小代码对齐。

## 决策（Decision）

1. **实体族（【架构决策】，v3 待重新采纳）**：Phase 2 cell-based CAEGraph 支持两个 entity family——**node entities**（ID = canonical Mesh node ID，单实例内 positional）与 **cell entities**（ID = canonical Mesh cell ID，单实例内 positional）。Phase 2 的 message-passing node graph 以 node entities 作为 graph vertices——这是 **representation choice**，不是 domain entity 的定义。多命名空间 ID、跨实例/序列化/分布式身份继续出清（ADR-018 出清项不回收）。
2. **关系模型（node graph）（【架构决策】，v2 冻结 + v3 errata 修正）**：无向节点对关系，由全部 canonical cells 的 codim-1 face 模板展开——每个 face template 的连续节点对（含环回）构成候选无向关系：2-node face → 1 对，k ≥ 3 face → k 对。候选对规范化为 `(min, max)`，全局去重，按 `(min, max)` 字典序排序；**同端点候选对 `(a, a)`（退化单元）丢弃**。**1D 特例**（v2 维持）：`topo_dim == 1` 时 cell（LINE2）本身即边，贡献其节点对（其 codim-1 faces 为维度 0 的点，不入 canonical topology，ADR-014）。cell-center 图记录为未来扩展，不在 Phase 2 实现。单 cell 唯一边参考（候选 ≠ 唯一）见下方参考表。
3. **存储语义（语义 = 【架构决策】；容器 = 【实现细节】）**：关系以规范化去重的无序对集合语义存储于 CAEGraph；**每 node 实体携带 NodeCategory 注解；Phase 2 中 cell 实体不参与 NodeCategory**。容器实现形式（tuple 对列表 vs CSR）为实现细节，不冻结；序列化与 batching 继续出清。
4. **NodeCategory 推导（【架构决策】，v3 待重新采纳）**：NodeCategory 语义需要显式的 region 分类规则。当前 Phase 2 推导（节点不属于任何 region → INTERIOR；恰属 1 个 → BOUNDARY；≥2 个 → CORNER）**仅适用于代表 boundary participation 的 region 类别**；internal interface 及其他语义 region 需另行规则。分类机制是 architecture decision，不由 region membership count 单独隐式定义——一般化分类规则留待后续裁定。显式限制：① 1D 无 canonical facet，NodeCategory 恒为 INTERIOR（继承 ADR-014——POINT facets 为已记录的未来扩展）；② 同壁面两个 region 共享节点会被标注 CORNER（显式语义限制，非缺陷）。boundary-class 判定细节不在本 ADR 立法；可用旁证：ADR-014 `facet_cells` 邻接数（`len == 1` 为 exterior 候选）。
5. **构造签名语义（语义 = 【架构决策】；基数检查机制 = 【实现细节】）**：输入 = Mesh + 显式传入的 BoundaryManager（region 所有权留在调用方）+ 可选 Fields；输出 = **满足 Phase 2 最小表示契约的 CAEGraph**（引用该 Mesh 为 topology provider）。构造期校验清单：**field 基数（leading entity axis cardinality，不冻结 Python 容器语义）**——`association == "node"` 的 field 其首轴长度 == `n_nodes`、`association == "cell"` 的 field 其首轴长度 == `n_cells`（ADR-014 组成修订的落点），其他 association 标签不做基数校验；**region membership 越界**——region 成员 ID 必须落于所供 Mesh 的 facet namespace，越界即构造失败（Region 不拥有 topology，校验责任在 representation construction；已实现并测试）。**BoundaryManager 最小冻结语义**：NodeCategory 为构造期结果，manager 事后 mutation 不追溯修改已构造的 CAEGraph；引用 vs 整体快照列为待裁定项，实现方案不冻结。
6. **出清项**：多图构造并存（node + cell-center）、几何特征挂载（geometry slice 兑现 Design UML 的 `MeshRepresentationBuilder ..> GeometryProcessor`）、增量更新、跨实例 ID、builder registry（单一 builder，第二 source 族出现再议）。

### 唯一边参考表（单 cell，候选 ≠ 唯一）

| Cell | 候选 | 唯一 |
| --- | --- | --- |
| LINE2 | 1 | 1 |
| TRI3 | 3 | 3 |
| QUAD4 | 4 | 4 |
| TET4 | 12 | 6 |
| PYR5 | 16 | 8 |
| WEDGE6 | 18 | 9 |
| HEX8 | 24 | 12 |

## associate_field 的 Phase 2 状态声明

`CAEGraph.associate_field()` 在 Phase 2 为 **lightweight association API**：不做 topology-cardinality 校验（基数校验仅在构造期执行）；其长期去留记入 backlog，不改 API。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 同时实现 node graph 与 cell-center 图 | 否决 | Phase 2 无消费者；推迟到有 FVM 证据时按 ADR-016 扩展策略 |
| 实体 ID 引入独立命名空间/UUID | 否决 | ADR-018 出清项——影响 serialization/distributed/batching，证据未齐 |
| edge container 冻结为 CSR | 否决 | 过早优化；语义（规范化去重对集合）已足够，容器形式随性能证据定 |
| NodeCategory 由未声明边界 facet 推导（拓扑驱动） | 否决 | 边界语义唯一真源是 region（ADR-010/018）；拓扑面无语义身份，拓扑驱动推导会制造无语义的 BOUNDARY 噪声 |
| field 长度校验留在 CAEGraph.associate_field | 否决 | 校验需要 entity 计数（拓扑事实）；associate_field 不持有 topology 语义，ADR-014 组成修订已将其定位到表示构造层 |
| NodeCategory 推导改为 region-membership-count 注解并改名 | 记录在案（v3） | 如实反映机械计数语义、消除 BOUNDARY/CORNER 误读；待分类机制裁定时一并评估 |
| NodeCategory 降级为 boolean node mask | 记录在案（v3） | 消除类别语义负担；损失三值信息，待分类机制裁定时一并评估 |

## 影响（Consequences）

- gate 4 Coding（CAEGraph 实体/关系/NodeCategory 存储 + mesh representation builder）获得设计依据；builder API/命名/落位仍随 coding 派单定稿（ADR-016 不冻结项不变）。
- CAEGraph 增加构造期填充的最小图数据与只读访问器；ADR-018"语义组成不定义 class members"的原则不受影响——本 ADR 即授权该存储的 dedicated 立法。
- Backend adapter（gate 4 后半）消费本模型的 edges / node_categories 产出 PyG Data schema；**adapter 可将无向关系集 materialize 为对称有向边 `(u, v)` / `(v, u)`——该转换属 backend adaptation，不属 CAEGraph storage（供 ADR-017 消费）**。
- 不引入新依赖、不改变依赖分层与 PyG 边界（ADR-007 不变）。

## 修订历史（Revision history）

- 2026-09-17 v1：最小可行决策——D1–D6 冻结，出清项显式记录。
- 2026-09-17 v2：补 1D 构造特例（LINE2 cell 贡献其节点对）——Slice 3a 复核发现 1D 空边集缺陷；accepted。
- 2026-09-18 v3：三方审查修订——D1 重写为双 entity family（node/cell，graph vertices 为 representation choice）；D2 errata（k-node face → k 候选对、退化对丢弃、唯一边参考表）；D4 重构为显式 region 分类规则问题（Phase 2 机械映射限定 boundary-participation 类别，一般化分类待裁）；D5 措辞与校验扩展（leading entity axis、membership 越界拦截、BoundaryManager 最小语义、"最小表示契约"表述）；新增 associate_field 状态声明与对称边 materialization 归属。**D1/D4 决策级修订待报批重新采纳，获批前状态为 proposed。**
