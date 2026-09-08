# ADR-018: CAEGraph domain composition and semantic ownership

- 编号：ADR-018
- 标题：冻结 CAEGraph 的语义组成与归属关系（semantic composition and semantic ownership）；范围排除见正文 scope exclusions
- 日期：2026-09-08
- 状态：**accepted（2026-09-08 经 Architecture review 采纳，语义组成与归属原则冻结）**
- 关联：ADR-015（父决策——本 ADR 归口其「后续设计决策」①②③ 的原则层）、ADR-014（topology subsystem 规范——仅引用，不重复立法）、ADR-016/017（downstream construction and backend adaptation contracts）、Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

ADR-015 冻结 CAEGraph 为 canonical domain representation 并列出组成方向（entities、relations、geometry、fields、regions、conditions，cell-based 方法下含 topology semantics），但将组成细节挂起为「后续设计决策」。本 ADR 回答其中的原则层：**CAEGraph 由哪些语义组件构成、每个组件负责什么、组件之间的归属关系如何。**

## 决策（Decision）

**CAEGraph semantic composition consists of six domain concepts and one referenced topology subsystem.** 这是语义层面的组成声明，不是 class/member 设计——各组件的实现形态保持开放（Geometry 可为 service、Relations 可为 view、Conditions 可为 constraint registry）。

| 组件 | 回答的问题 | 冻结的原则 |
| --- | --- | --- |
| Entities | 有什么物理对象 | Entities require stable identity within their semantic scope.（身份原则；ID schema 不在本 ADR 冻结） |
| Relations | 对象之间如何连接 | Relations are the primary abstraction for connectivity；**some relations may be explicitly provided by the source representation, while others may be derived**。Relations may represent both explicit physical relationships and derived connectivity views（periodic pair、interface relation、cell-face relation、neighborhood relation 均属之）。A connection may require its own domain identity and data representation when it carries domain semantics or independent state. |
| Geometry | 对象在哪里 | 空间位置与几何属性的语义职责；实现形态（含 service）开放 |
| Fields | 对象有什么物理量 | **Fields are associated with entities**, not directly with geometry or topology |
| Regions | 哪些对象属于同一物理区域 | boundary / interface / physical groups 统一为 semantic region；不单独建 BoundaryGraph |
| Conditions | 如何施加物理约束 | Conditions are constraint declarations that **may reference Regions and field data**；initial conditions may reference field data representing an initial state（约束 ≠ 状态；by reference，不与 Fields 融合） |
| Topology subsystem | 离散结构如何定义 | optional semantic provider referenced by CAEGraph；cell-based topology semantics are provided by the topology subsystem defined in ADR-014 |

**Ownership 总则**：Fields **associated with** entities；Conditions may reference Regions and field data；the topology subsystem is **referenced by CAEGraph** rather than modeled as a domain concept owned by CAEGraph——它是 optional semantic provider，不是 CAEGraph 的内部对象，更不是继承体系。

## 不冻结的内容（scope exclusions）

以下均为 implementation / data-model 细节，移交后续 **dedicated ADRs for entity identity and relation/topology modeling**（不预占数量与标题）：

- **ID schema**（多命名空间 / 全局 / 混合——影响 serialization、distributed graph、dataset batching、backend mapping，证据未齐）；
- **storage layout 与 relation 存储形式**（含 edge container）；
- **class hierarchy 与 API**；
- **serialization**；
- **component interaction mechanisms**（Conditions 如何查找 Region、Field 如何绑定 Entity、topology 如何被引用——机制不冻结）。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 语义组件作为内部 class 成员（`CAEGraph.topology = ...` 式） | 否决 | 语义组成 ≠ 类设计；实现形态应保持开放 |
| adjacency-only（连接仅为 node-node 边） | 否决 | 重申 ADR-015 方案 A；丢失 interface / periodic / cell-face 等关系语义 |
| 单独 BoundaryGraph | 否决 | boundary / interface / groups 统一为 semantic region |
| Conditions ⊕ Fields 融合 | 否决 | 约束 ≠ 状态；绑定应为引用 |
| 现在冻结 ID schema（per-kind / global / UUID） | 否决 | 影响 serialization / distributed / batching / backend mapping，证据不足 |

## 影响（Consequences）

- 关闭 ADR-015「后续设计决策」①②③ 的原则层；数据模型细节归后续 dedicated ADRs。
- CAEGraph core 派单的语义依据 = ADR-015 + 本 ADR；API 细节在派单中定稿。
- 不引入新依赖、不改变分层方向。

## Revision history

- 2026-09-08 v1：最小可行草案——冻结语义组成与归属原则；ID schema、存储布局、类层次、交互机制全部出清至后续 dedicated ADRs。
- 2026-09-08：accepted（Architecture review 通过，语义组成与归属原则冻结）。
