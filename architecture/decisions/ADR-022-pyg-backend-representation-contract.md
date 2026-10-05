# ADR-022: PyG backend representation contract

- 编号：ADR-022
- 标题：冻结 Phase 2 PyG backend representation 契约——node-graph backend profile、schema 键集与保留键、`field_families` 保真映射与 gate 6 可判定验收义务、`node_category` 显式映射（append-only）、多 realization 一律拒绝、declaration-only 零足迹、义务分界判据（canonical 忠实呈现 vs transforms 派生编码）；接口形态不冻结；仅覆盖 Phase 2 / PyG，不构成通用 backend 契约
- 日期：2026-10-04
- 状态：**proposed（草案——待 PM 裁决采纳；采纳后 gate 4b 进入 Design UML 具体化）**
- 关联：ADR-017（适配链冻结——schema/mapping/batching 委托由本 ADR 在 PyG/Phase 2 范围内定稿，正文不改）、ADR-019（C-01 对称展开属 backend adaptation）、ADR-020（D4 领域输入唯一、D6 唯一-realization 纪律）、ADR-021（DECISION-07 family 保真原则——本 ADR 为其 gate 4b 必答项的回答）、ADR-007（D2 PyG 边界）、Phase 2、Design UML `class_diagram.puml`（Stage 2 具体化）

## 背景（Context）

- **FACT-01**：ADR-017 将「DataGraph 字段与 tensor schema；CAEGraph → PyG 的字段 mapping；batching 策略」委托 adapter 派单定稿（L33-38），适配链与依赖方向已冻结。
- **FACT-02**：ADR-021 DECISION-07 要求 gate 4b 派单必须回答 transforms 如何按 family 安全处理 node/cell data——禁止 association 丢失或隐式重解释；具体 PyG key / schema / layout 由 gate 4b 派单决定。
- **FACT-03**：ADR-020 D4 冻结 adapter 领域输入唯一 = CAEGraph canonical representation；D6 冻结多 realization 下要求唯一输入的消费路径必须显式选择或失败。
- **FACT-04**：ADR-019 C-01 冻结对称有向展开（`(u,v)`/`(v,u)`）属 backend adaptation、永不入 CAEGraph storage。
- **FACT-05**：field-split 与 ADR-021 association contract migration 已落地——**经 Git 祖先关系核实**：merge commit `6153268` 包含 field-split（`4351c9e`）、facet-cells bool 修复（`d887765`）、ADR-021 采纳（`8e5213b`）及 association contract migration 全部 commits（含第 4 修正 `3829b9f` 与 UML 同步 `bc61e34`）。Field 声明必带 entity family，FieldData 仅支持 `{node, cell}`，adapter 实际可见的 family 只有 node/cell。
- **FACT-06**：gate 4b adapter 尚未实现（`caegraph.graph.pyg` 未建）；本 ADR 为其 Architecture 前置。

## 范围（Scope）

**本 ADR 仅覆盖 Phase 2 的 PyG backend representation，不构成通用 backend 契约**；未来 backend 仍按 ADR-017 门槛处理（改变 domain/boundary 或依赖方向才需 review）。ADR-017 本身只冻结适配边界（`CAEGraph → backend adapter → framework-specific representation`），并明确把 schema / mapping / batching 留给后续具体化——本 ADR 即该委托在 PyG / Phase 2 范围内的具体化，不改变 ADR-017 正文。

## 问题（Issues）

- **ISSUE-01**：schema 键集与键空间治理未定——backend Data 上哪些键由 adapter 写入、哪些保留不可占用，无契约则 transforms/dataset 消费无稳定面。
- **ISSUE-02**：backend↔transforms 跨层 family 保真契约未裁决——ADR-021 D7 只立原则，未定 PyG 侧的保真载体与验收形态。
- **ISSUE-03**：多 realization 与 temporal 组织的边界未划——adapter 是否选择、timestep 是否豁免，未定。
- **ISSUE-04**：adapter 与 transforms 的义务分界缺判据——「忠实呈现」与「派生编码」无分界句，gate 4b/6 范围易互窜。

## 决策（Decision）

### D-01 适配入口与 node-graph backend profile

**一句话结论**：adapter 唯一领域输入为 CAEGraph；仅接受满足本 ADR 所定义 **node-graph backend profile** 的 canonical state，不满足则 fail-fast。

**展开解释**：profile 为可判定条件组，**全部满足方可适配，否则 `ValueError`**（按 canonical state 判定，不按 source provenance 判断）：① 输入为 `CAEGraph` canonical representation（类型检查先于一切）；② 通过 `graph.validate()`；③ 携带满足 ADR-019/020 的 cell-based `Mesh` topology provider；④ 携带构造期图数据（`n_entities >= 1`）。不满足本 profile 的 canonical state（含未来 mesh-free 表示）不在本 ADR 覆盖范围（见不覆盖项）。

### D-02 schema 键集

**一句话结论**：adapter 产出的 `torch_geometric.data.Data` 键集为——`edge_index`（对称有向 `[2, 2E]`，long）、`num_nodes`（= `n_entities`；node-graph profile 下成立，见 D-01）、`pos`（float64 `[n, 3]`，本 profile 冻结）、`node_category`（long，编码见 D-07）、field data 键（按 Field 名挂载，见 D-03/D-05/D-06）与 `field_families`（见 D-03）。**`field_families` 恒在于产出的 Data 上（可为空）**。

**展开解释**：对称有向展开属 backend adaptation（ADR-019 C-01）；`edge_index` 为 `(min, max)` 规范对的双向物化，无向存储不重复。`pos` 取 topology provider 节点坐标，dtype 保留 float64（canonical 存储），cast 属 transforms。`field_families` 的空态语义见 D-06（declaration-only → 映射存在但无条目）。

### D-03 `field_families` 保真映射（ADR-021 D7 必答）

**一句话结论**：**`Field.association` 是领域 authoritative source；`field_families` 是其在 PyG backend representation 中的保真映射**——`field_families: dict[str, str]` 将每个已挂载 field data 键映射到其 `"node"` / `"cell"` family；不改写 Field 名、不设双列表、不做前缀命名空间。

**展开解释**：cell-family field data 以**原形**挂载（首轴 `n_cells`，零变换，禁隐式 cell→node interpolation）；node-family 保持 node 对齐。`field_families` 是**保真映射与统一查询面，不是领域真源**——association 等语义的 authoritative source 仍是 Field（ADR-020 D3）。每个已物化 field 的 family 必须可恢复、且与适配前的 association 一致。no-loss 为 **gate 6 可判定验收义务**（本 ADR 不宣称已证）：batching / transforms 之后 `field_families` 必须仍然存在、键集一致、值语义不变；**是否要求不同样本具有相同字段集合，本 ADR 不冻结**（留 dataset 层裁决）。

### D-04 保留键 fail-fast

**一句话结论**：保留键集 = `edge_index` / `num_nodes` / `pos` / `node_category` / `field_families` + PyG 常用属性 `x` / `y` / `edge_attr` / `batch` / `ptr`；Field 名与任一保留键冲突 → 适配期 `ValueError`。

**展开解释**：该 fail-fast **仅发生在 backend adaptation（adapter）**——不得将 PyG 保留键规则泄漏回 `MeshRepresentationBuilder` 或其他 construction 层；声明层词汇开放不受影响（ADR-021 D2）。`train_mask` / `val_mask` / `test_mask` 等 dataset 惯例键**不在本集**——掩码语义属 gate 6 dataset 层，本 ADR 不越界禁占。

### D-05 多 realization 一律拒绝

**一句话结论**：同一 Field 存在多于一个 FieldData 时，adapter 一律 fail-fast（`ValueError`）；**无 timestep 豁免**；adapter 零 selector。

**展开解释**：无选择机制即无可判定的「正确一帧」，任何隐式选取（first/latest/按 timestep）都违反 ADR-020 D6。ADR-020 已明确：多 realization **可以存在于 representation**，但要求唯一 realization 的消费路径必须显式选择或失败——本条是该纪律在 adapter 的落地。单帧 FieldData 的 timestep 之 PyG 呈现方式本 ADR 不冻结，留 temporal view microdecision（见不覆盖项触发条件）。

### D-06 declaration-only 零足迹

**一句话结论**：只有声明而无 FieldData 的 Field 在 backend representation 上产生**零足迹**（无键、无 `field_families` 条目、不生成任何 values）——本 ADR 新增的 backend presentation decision。

**展开解释**：与 ADR-020 D4 的 problem-before-solving 合法态相衔接；但「零足迹呈现」这一 backend 侧决策由本 ADR 独立作出并冻结。

### D-07 `node_category` 显式映射（append-only）

**一句话结论**：`node_category` 编码冻结为显式映射 `INTERIOR→0`、`BOUNDARY→1`、`CORNER→2`；该映射 **append-only**——只许追加新类别（追加于现有值之后），禁止重排或改值；数值稳定性依据本句，而非枚举声明序。

**展开解释**：Phase 2 `NodeCategory` 本身为字符串枚举——显式 backend 数值映射因此比「依赖枚举声明序」更可靠（此即对原声明序方案的修正理由）。field data 与 `node_category` 均**不得无依据改变 dtype**（保留 canonical dtype；转换属 transforms）；未来新增类别（若有）只能追加新整数值，既有映射不变。

### D-08 适配器形态不冻结

**一句话结论**：Phase 2 实现为具体适配器（命名与调用接口随 Design UML 具体化与 coding 派单定稿）；本 ADR 不冻结接口形态（遵 ADR-017「concrete interface not frozen」）。

## 义务分界判据（本 ADR 与 transforms 的边界）

**ADR-022 义务止于 canonical 属性的忠实呈现（materialization）；从语义派生新数据的编码属 transforms（gate 6）。**既有 canonical `pos`、`node_category`（ADR-019 将 `NodeCategory` 定义为 CAEGraph node annotation）属 adapter **忠实物化**；依据 geometry / boundary / region 再计算 feature、mask、constraint、physics encoding 才属 gate 6 transforms。

## 本 ADR 不覆盖项（scope exclusions）

- PyG batching 实现策略（gate 6；`field_families` 的 batching 后保真为 gate 6 验收义务，D-03）；
- transforms 消费 API 与读取方式（gate 6；本 ADR 只立禁止性义务：不得丢失、不得隐式重解释）；
- 几何 / boundary / region / mask 编码（transforms，gate 6——按上文义务分界判据）；
- temporal view（realization 排序 / 窗口 / 选择）——另立 microdecision，立项触发：① 首个合法消费 >1 realization 的 consumer 出现；② 首次需要 temporal ordering / window / selection；③ gate 6 引入 temporal dataset / window。满足其一即立项；
- selection API（ADR-020 D6 治理）；
- mesh-free canonical state（node-graph profile 之外；未来表示，触发时另行架构决策）；
- 非 PyG backend（ADR-017 门槛：改变 domain/boundary 或依赖方向才需 review）；
- 性能优化。

以上各项禁止提前实现接口等待未来确认；纳入决策范围须专门架构决策。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| `field_families` 统一映射 | 采纳 | backend association 保真载体与统一查询面；不改名、无命名空间污染 |
| 前缀命名空间（`cell__vol`） | 否决 | 名称污染、与用户命名冲突 |
| node/cell 双列表属性 | 否决 | 两处维护、易失同步 |
| `node_category` 按声明序编码（原案） | 否决，改为显式映射 + append-only | 注记：数值稳定性不应依赖枚举声明序这一实现细节；终为显式映射句，防复审误读 |
| gate 4b 拒绝 cell field data（更早草案） | 否决 | ADR-021 DECISION-07 已翻案：cell 必须保真携带，禁隐式插值 |
| adapter 内置 selector（first/latest/timestep） | 否决 | 违 ADR-020 D6；temporal 组织归上层视图（另立 microdecision） |
| YAML 不变式延迟登记 | 否决 | 前瞻性契约 D-02..D-07 可判真伪；不登记使 Stage 3 测试失去验收对照物——本 ADR 采纳即创建 TEST_MISSING 初版，与 Markdown 同 commit |

## 影响（Consequences）

- gate 4b 序列：本 ADR 采纳 → Stage 2 Design UML 具体化（`BackendAdapter` → Phase 2 具体适配器）→ Stage 3 coding（含 **授权制** evidence 回填：YAML 编辑永不与 feat 同 commit）→ Stage 4 docs（含 ADR-019 C-01 追加落点、phase2 措辞澄清）。
- transforms 层义务（gate 6 兑现）：`field_families` no-loss 可判定验收（存在性、键集一致、值语义不变）；读取 API 由 gate 6 设计。
- temporal view microdecision 依三触发条件立项（不覆盖项）。
- 不改变依赖分层与 PyG 边界（ADR-007 D2）；不改 ADR-017/019/020/021 正文（关联引用即可）。

## Invariant 登记策略

- **采纳即创建** `ADR-022-invariants.yaml`（TEST_MISSING 初版，与本文档同 commit）——理由见备选方案末行。
- 三条件约束：① statement 用可判定断言；② YAML 治理三件套（字段 schema / 规则注释 / eligibility 纪律）与既定格式一致；③ Stage 3 回填仍走 PM 授权（证据同步永不与 feat 同 commit）。
- 候选登记范围：D-02 schema 键集存在性、D-03 `field_families` 映射与 family 一致、D-04 保留键 fail-fast、D-05 多 realization 拒绝、D-06 declaration-only 零足迹、D-07 显式映射与 append-only；eligibility review 适用（凡引用 deferred 机制形态缺席者不登记）。
- C-01 adapter 侧守卫**归 ADR-019** test_mapping（Stage 4 落点），本 ADR 不重复登记。

## 修订历史（Revision history）

- 2026-10-04 v1：草案（proposed）——契约内容经两轮裁决后成文；备选方案记录四组裁决及其排除理由。
- 2026-10-04 v1.1：contract cleanup（12 项审阅修正，契约语义按裁决精化，方向零变化）——新增范围声明（仅 Phase 2 / PyG，非通用 backend 契约）；FACT-05 改为经核实的 Git 祖先事实；D-01 改 profile 可判定条件表述（不按 source provenance 判断）；明确 `field_families` 恒在可空、其为保真映射而非领域真源；D-04 fail-fast 限定于 backend adaptation；D-05 补 ADR-020 交叉引用；D-07 去 implementation primitive、补 NodeCategory 字符串枚举理由；义务分界精化（忠实物化 vs 派生编码）；修订历史与同 commit registry 的内部标号清理。
