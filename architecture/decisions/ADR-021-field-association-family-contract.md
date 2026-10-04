# ADR-021: Field association entity-family contract

- 编号：ADR-021
- 标题：冻结 Field.association 为 entity-family identifier——声明必须携带 entity family（`None` 非法）、supported realization families = node / cell、unsupported-family FieldData 构造期拒绝、representation 维持 `str` 类型化 deferred、gate 4b 关联保真原则（node 对齐 / cell 保留 association / 禁隐式插值）
- 日期：2026-10-04
- 状态：**proposed（草案——待人工裁决采纳；采纳后 ADR-020 D5 pending 项收口随本 ADR 生效）**
- 关联：ADR-020（D5 pending association microdecision 由本 ADR 收口）、ADR-019（D5 基数契约——node/cell family 键控，本 ADR 不改其 statements）、ADR-018（fields↔entities 关联原则 + 开放词汇——本 ADR 语义上游）、ADR-007（D6 Field 六抽象）、Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

- **FACT-01**：ADR-018 冻结 fields↔entities 关联原则——"Fields 与 entities 关联，而不直接与 geometry 或 topology 关联"。
- **FACT-02**：Field 既有表述——association 为 "entity scope label identifying the entity family the quantity attaches to… Labels denote entity families, never topology positions or semantic regions"，词汇开放（for example `node` / `cell` / `particle`）。
- **FACT-03**：builder 现行 known-set {node, cell} 基数校验；其余标签跳过——无基数语义的数据可进入 canonical representation。
- **FACT-04**：ADR-019 D5 基数契约以 family 键控（node → `n_nodes` / cell → `n_cells`；不变式 D5-01/02 以 "node-associated FieldData values" 表述）。
- **FACT-05**：ADR-020 v3 D5 将标签 representation、匹配方式与 `None` 语义显式移交本 microdecision（gate 4b 前裁决）。
- **FACT-06**：`None` 现为声明级合法；因 Field 构造后冻结（无 mutation 路径），`None` 声明永久不可路由。
- **FACT-07**：unknown/typo 标签构造期静默跳过基数校验。
- **FACT-08**：gate 4b adapter 按 family 路由；node → node-aligned；cell 保真未决（先期"拒 cell"草案与保真要求冲突）。
- **FACT-09**：cell realizations 是一等构造产物（ADR-019 "cell 字段经构造期基数校验与 cell ID 关联"），并有下游语义消费者（ADR-018 Conditions 行）。
- **FACT-10**：DoD 条款——"field association…must survive every conversion boundary without unintended loss or alteration"。

## 问题（Issues）

- **ISSUE-01**：`None` 声明永久不可路由——合法但不可用的契约歧义。
- **ISSUE-02**：unknown/typo 标签构造期静默绕过基数校验——无法验证的数据进入 canonical representation。
- **ISSUE-03**：cell-family backend 保真未决——先期"拒 cell"草案与 FACT-09/10 的保真要求冲突。
- **ISSUE-04**：representation 选择与 contract 变化耦合——须按"是否改变 runtime/canonical contract"分流。

## 决策（Decision）

**裁决形式说明**：DECISION-03 / DECISION-05 改变 construction/runtime validity，构成独立 contract 变更——本 ADR 按 **Outcome B** 立案；代码迁移另立窄 dispatch（见影响）。

### DECISION-01 association = entity-family identifier

**一句话结论**：`Field.association` 的领域含义冻结为 **entity-family identifier**——标识量所附着的 entity family；具体 representation 不冻结。

**展开解释**：family 语义与 FACT-01/02 一脉相承，本次显式立法；标签→family 的映射与匹配方式 = implementation detail。

### DECISION-02 开放词汇 + supported realization families

**一句话结论**：vocabulary 保持开放（声明级任意非空字符串合法）；Phase 2 **supported realization families = {node, cell}**——仅其上存在基数契约与 backend 挂载语义。

**展开解释**：supported 集合来源 = ADR-019 D5 基数契约；扩展流程见 DECISION-06。

### DECISION-03 `None` 非法——声明必须携带 entity family

**一句话结论**：`association=None` 不作为合法 canonical Field 状态——Field declaration 构造期必须携带非空 entity family 标签（fail-fast）。

**展开解释**：废除 optional `None`（FACT-06 的永久不可路由后果自本 ADR 起不再可产生）。Breaking signature change：`association` 成为必填关键字参数，随窄 code dispatch 迁移全部构造调用面。

### DECISION-04 representation 维持 `str`

**一句话结论**：association 的 representation 维持 `str`；Enum / EntityFamily 类型化 deferred。

**展开解释**：类型化升级触发条件——① Phase 3 dataset 类型化路由需求；② io band 落地第二个真实 family；③ 跨 IO-backend 契约需要。触发前禁止为可测试性或类型美学提前引入。

### DECISION-05 unsupported-family：声明可表达、realization 构造期拒绝

**一句话结论**：unsupported family 的 Field declaration 可表达（DECISION-02 开放词汇），但在尚无对应 cardinality contract 时**不得创建/挂载其 FieldData realization**——construction fail-fast，避免无法验证的数据进入 canonical representation。

**展开解释**：FieldData 构造期校验 `field.association` ∈ supported families；builder canonical 门复验（纵深防御）。已知后果（有意，非缺陷）：unsupported 声明在其 family 经 DECISION-06 获得基数契约前无法携带任何 realization。

### DECISION-06 supported family 准入流程

**一句话结论**：新 supported family 必须经后续 dispatch 明确其 cardinality semantics、construction validation 与 backend behavior。

**展开解释**：每 family 一派单；仅依赖/边界变化时 architecture review。particle（mesh-free）前置 = mesh-free 构造策略（ADR-016 future）——其基数语义来源与 mesh 不同。

### DECISION-07 gate 4b association 保真原则

**一句话结论**：gate 4b 对 node / cell FieldData 均必须保持 association 语义——node 形成 node-aligned backend data；**cell 必须保留 cell association，禁止隐式 cell→node interpolation**；具体 PyG key / schema / layout 不在本 microdecision 冻结，由 gate 4b 派单决定。

**展开解释**：取代先期 M5/Q4 "拒 cell" 草案（ISSUE-03 收口）；cell realizations 经构造期基数校验后为一等数据，其 backend 呈现以保真为原则（family 标记等形态细节归 gate 4b 派单）。declaration-only Field → DECISION-08。

### DECISION-08 declaration-only backend 呈现不冻结

**一句话结论**：declaration-only Field 的 backend 具体呈现不在本决策冻结——仅维持 ADR-020 D4 "不凭空产生 realization values"。

## 本 ADR 不覆盖项（scope exclusions）

- Enum / EntityFamily 类型化（deferred + 触发条件，DECISION-04）；
- 新 supported family 的具体基数语义与验证规则（per-family dispatch，DECISION-06）；
- PyG key / schema / layout 与 family 标记形态（gate 4b 派单，DECISION-07）；
- declaration-only backend 呈现（DECISION-08）；
- selection API（ADR-020 D6 治理）；
- `associate_field` 长期去留（ADR-019 backlog）。

以上各项禁止提前实现接口等待未来确认；纳入决策范围须专门架构决策。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| `None` 维持合法（现状） | 否决 | ISSUE-01 永久不可路由 + 合法但不可用的契约歧义；canonical 状态必须可路由 |
| unsupported-family FieldData 容忍（跳过基数，现状） | 否决 | ISSUE-02 无法验证的数据进入 canonical representation |
| Enum / EntityFamily 立即类型化 | 否决（deferred） | 过早冻结词汇；io band 证据未齐（FACT-02 开放性）；改动面无消费者对价 |
| gate 4b 拒 cell（先期 M5 草案） | 否决 | 违 FACT-09/10 保真要求（ISSUE-03）；DoF "no unintended loss" 条款不支持 |
| 本决策（family contract + 两级处置） | 采纳 | 语义立法、不可验证数据阻断、cell 保真原则、表示自由度保留 |

## 影响（Consequences）

- **Breaking**：Field 签名（association 必填）+ FieldData supported-family 构造守卫——独立窄 code dispatch（边界：`core/field.py`、`graph/builder.py`、测试面、docstrings、CHANGELOG；不含 gate 4b adapter 本体）。
- **迁移测试清单**（dispatch 内执行）：Field 缺 association → `TypeError`（signature）；空串 → `ValueError`；FieldData unsupported family（如 `particle`）→ 构造即 `ValueError`；node/cell 基数行为不变；旧 "other association labels skip" 测试退役。
- **gate 4b 解锁条件**：本 ADR 采纳 + 上述 dispatch 落地 → adapter family-routing 契约 = DECISION-07（实际可达 family 仅 node/cell——unsupported/None 已被构造期阻断；declaration-only 零足迹）。
- **YAML/registry**：本 ADR 属 implementation ADR；不变式登记延迟至 code dispatch 与证据同步创建（eligibility review 适用；候选：association 必填的结构事实——签名级可执行、DECISION-05 构造守卫）。
- **不改变**：ADR-019 D5 statements（family 措辞已兼容）、ADR-020 D1–D4/D6、依赖分层与 PyG 边界（ADR-007）。

## Invariant 登记策略

- 登记**延迟至 code dispatch**，与测试证据同步创建（eligibility review 适用）；候选：DECISION-03 结构事实（Field 构造必须携带非空 association——签名级可执行，非缺席型）、DECISION-05 构造守卫（unsupported-family FieldData 创建即拒）。
- 本 Markdown 为唯一决策真源；YAML 只作机器可读核验索引。

## 修订历史（Revision history）

- 2026-10-04 v1：草案（proposed）——Step A Planning Report（事实链 FACT-01..10、触点清单、Q1–Q7 方案矩阵、风险/兼容性分析、推荐结论压力测试）经人工裁决后成文；DECISION-01..08 按人工裁决撰写。
