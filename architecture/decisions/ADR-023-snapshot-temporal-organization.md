# ADR-023: Snapshot temporal organization over realizations

- 编号：ADR-023
- 标题：冻结 canonical temporal organization over realizations——Snapshot（graph-level instantaneous-state organization construct）以显式 membership 定义瞬时状态、三时间坐标分离（snapshot identity / physical_time / solver_step）、scope 显式二分（global/static ‖ snapshot-scoped）、`(Snapshot, Field) ≤ 1 FieldData`、`FieldData.timestep` 去 canonical temporal authority（solver_step 一致性守卫）、显式 selection 产出满足 ADR-022 现有 input contract 的 single-state projection（adapter 零修改）；不冻结存储 / 容器 / 写入口 / API / 视图实现形态
- 日期：2026-10-05
- 状态：**proposed（2026-10-05 草案；本 ADR 止于 proposed 报 PM 裁决，不进入合入）**
- 关联：ADR-018（六领域概念组成——Snapshot 不新增概念计数，见 D-01 原文引用）、ADR-007（D6 六抽象清单——Snapshot 不新增计数）、ADR-020（1:0..* 语义基数不变、D4 canonical data flow、ownership / container / storage 不冻结、D6 显式选择纪律）、ADR-021（realization families——Snapshot 成员仍是 FieldData，family 语义不变）、ADR-022（D-05 zero-selector 与 D-06 declaration-only 零足迹零修改；其不覆盖项 temporal view microdecision 由本 ADR 承接）、Phase 2、Design UML `class_diagram.puml`（随未来 temporal coding dispatch 具体化）

## Mental Model

```mermaid
flowchart TB
    F["Field (declaration)"] --> FD["FieldData (one realization)"]
    FD -->|"snapshot-scoped membership"| SN["Snapshot (instantaneous physical state)"]
    FD -->|"global / static scope"| PR["single-state projection"]
    SN -->|"explicit selection (ordered by physical_time)"| PR
    PR --> AD["PyG adapter (ADR-022, zero change)"]
    classDef nowrap white-space:nowrap
    class F,FD,SN,PR,AD nowrap
```

## 背景（Context）

- **FACT-01**：ADR-022 不覆盖项明文将 temporal view（realization 排序 / 窗口 / 选择）列为另立 microdecision，并记录三触发条件（首个合法消费 >1 realization 的 consumer 出现；首次需要 temporal ordering / window / selection；gate 6 引入 temporal dataset / window——满足其一即立项）。transient CAE 数据需求已使触发条件满足，本 ADR 即该 microdecision 的立项与裁决（PM 2026-10-05 派单）。
- **FACT-02**：现行实现 `FieldData.timestep: float | None`（`core/field.py`——int / float、bool 拒绝；`None` = 未声明时间）；canonical representation 中**无任何瞬时状态结构**——`CAEGraph._field_data` 为扁平 append-only list（`core/caegraph.py`），builder 明文多 realization 存储不静默选择（ADR-020 D6），构造期零时间校验。
- **FACT-03**：跨 Field 同一时刻的 realization 仅能靠消费端 timestep 数值相等推导——瞬时状态是消费约定而非 canonical 结构关系；且「无 timestep」语义歧义（steady 还是漏注册不可判定）。
- **FACT-04**：ADR-020 冻结 Field : FieldData = **1:0..\*** 语义基数（Field 为 name / unit / association / component semantics 唯一真源）、realization data 位于 canonical data flow 且 ownership / container / storage 不冻结；ADR-018 冻结 CAEGraph 语义组成 = **六领域概念** + referenced topology subsystem，其澄清注记（2026-10-01，ADR-020）明确「Fields 仍为一个领域概念（由 Field 与 FieldData 共同承载），FieldData 不构成第七领域概念」；ADR-007 D6 六抽象清单经 ADR-020 局部取代后明文「FieldData 为 Field 概念的 realization 成员，不新增计数」。
- **FACT-05**：ADR-022 D-05 冻结 adapter 多 realization 一律 fail-fast、零 selector、无 timestep 豁免；D-06 冻结 declaration-only 零足迹；二者零修改保留（见「兼容性核实」）。
- **FACT-06**：`dataset/` 与 `transforms/` 当前为空包（仅 `__init__.py`）——temporal Dataset / window 实现全部未建。

## 范围（Scope）

本 ADR 冻结 canonical temporal organization 的**语义层**：Snapshot membership、scope、时间坐标、global ordering、显式 selection 的义务与产物契约；不冻结任何存储结构、容器形态、写入口、API 与视图实现（见不覆盖项）。本 ADR 只处理 realization 的**时间维度组织**：不将 multiple realization 整体重定义为 multiple timestep，不打开 mesh / mesh-free representation form 议题，不处理第二 realization axis（ensemble / multi-source / multi-fidelity）。

## 问题（Issues）

- **ISSUE-01**：瞬时状态无 canonical 结构表达——跨 Field 同刻 realization 的归属关系只能由消费端数值推导（FACT-03）。
- **ISSUE-02**：时间概念被压缩——snapshot identity、physical time、solver step 三种语义混于单一 float `timestep`；无时间信息时语义不可判定。
- **ISSUE-03**：steady / transient 共存无 scope 语义——为逐帧完整而复制 steady realization，或以缺失时间信息隐式推断 steady，两者均无契约依据。
- **ISSUE-04**：temporal selection 职责未定——选择若入 adapter 即违 ADR-022 D-05；需在 adapter 之前完成显式选择，且产物须满足既有 adapter input contract 以避免修改 ADR-022。

## 决策（Decision）

### D-01 Snapshot = canonical realization organization construct

**一句话结论**：Snapshot 是 **graph-level 的 canonical realization organization construct**——以显式 membership 组织既有 FieldData、表达「这些 realization 属于同一瞬时物理状态」；**不构成新的领域概念**。

**展开解释**：定位依据为既有 ADR 原文：ADR-018 冻结「CAEGraph 的语义组成由六个领域概念和一个被引用的 topology subsystem 构成」，其澄清注记（2026-10-01，随 ADR-020 采纳生效）明确「Fields 仍为一个领域概念（由 Field 与 FieldData 共同承载），FieldData 不构成第七领域概念」；ADR-007 D6 六抽象清单经 ADR-020 局部取代后明文 realization 成员「不新增计数」。Snapshot 沿同一纪律：它是 realization 的**组织构造**，不引入新物理量 / 实体 / 状态语义，不增加 ADR-018 领域概念计数，不进入 ADR-007 D6 六抽象清单——temporal organization 语义由 Snapshot 承载，realization 语义仍由 Field / FieldData 承载。temporal organization 为**可选结构**：无 Snapshot 的 canonical representation 合法（steady-only / declaration-only 现状不变）；引入 Snapshot 组织时受本 ADR 约束。

### D-02 三时间坐标分离

**一句话结论**：snapshot identity、physical_time、solver_step 是**三个语义不同的时间坐标**，不得相互替代；Phase 2 temporal organization 中每个 Snapshot 必须携带 **physical_time**，且同一 temporal organization 内 **physical_time 值唯一**；solver_step 可选，不承担 Snapshot identity。

**展开解释**：identity 回答「这是哪个瞬时状态」——由 Snapshot 的结构身份承载，不由 float 值或步号承担；physical_time 回答「该状态对应什么物理时间」——是 global ordering 的唯一坐标（D-08）；solver_step 回答「数据源 / 求解器中的步号」——纯来源标注。非等间隔 physical_time 合法（无等差假设）。三坐标的具体成员形态不冻结（不覆盖项）。

### D-03 membership 定义瞬时状态

**一句话结论**：**「属于同一瞬时物理状态」的唯一判据是 Snapshot membership**——snapshot-scoped FieldData 经显式归属进入某 Snapshot；**`(Snapshot, Field) ≤ 1 FieldData`**（一致性校验 fail-fast）；membership 单值（每个 snapshot-scoped FieldData 恰属一个 Snapshot）。

**展开解释**：membership 是定义性结构关系，**不引入时间数值参与判定**——同一 Snapshot 的成员即同一瞬时状态，无论其时间标注如何；本 ADR 不使用也不引入 `(Field, t)` 类时间值判据。`(Snapshot, Field) ≤ 1 FieldData` 意味着同一 Snapshot 内同一 Field 至多一个 realization；同一 Snapshot 内同一 Field 的多 realization（solution / experiment / prediction 并存等）属于**第二 realization axis**（ensemble / multi-source / multi-fidelity），本 ADR 显式 deferred（不覆盖项）。Snapshot 成员数无下限（部分乃至全部 Field 缺席合法，见 D-06）。

### D-04 scope 显式二分

**一句话结论**：每个 FieldData **恰属一个 scope**——**global / static realization**（不属于任何 Snapshot）或 **snapshot-scoped realization**（恰属一个 Snapshot）；scope 是显式声明的结构属性，**禁止以「缺失时间信息」推断 steady**；**Phase 2 temporal profile 中，同一 Field 不得同时拥有 global 与 snapshot-scoped realizations**（一致性校验 fail-fast）。

**展开解释**：scope 二分消除「无 Snapshot membership」的歧义——一个 FieldData 要么显式 global、要么显式 snapshot-scoped，不存在「本来 transient 但尚未被正确注册」的中间态。**披露：本条的 per-Field scope 禁混是 ADR-023 在 Phase 2 temporal profile 中新增的合法性收窄**——ADR-020 D6 只冻结「多 realization 可存于 representation、要求唯一 realization 的消费须显式选择或失败」，未裁决 temporal scope 混存；本 ADR 为消除 override / precedence 问题将其收窄，未来若需混存须显式新决策。本 ADR 冻结的是 **scope / membership / consistency validation 义务**：无论写入口是什么，上述约束必须被构造期或一致性校验强制；**不冻结任何特定对象为永久唯一 temporal 写入口**（含 MeshRepresentationBuilder——承袭 ADR-020 ownership / container / storage 不冻结立场）。

### D-05 global realization 上限（Phase 2 temporal profile）

**一句话结论**：**Phase 2 temporal profile 中，global-scoped Field 至多一个 FieldData**（0 合法 = declaration-only）。

**展开解释**：这是「当前暂不支持第二 realization axis（ensemble / multi-source / multi-fidelity 等）」的 **Phase 2 限制，不是普适领域定律**——global realization 的多实例与同刻多实例同属该 deferred axis；未来开放该 axis 属独立架构问题，须显式新决策。跨时间的多 realization 由 Snapshot 组织承载（与 ADR-020 D6 的多 realization 存储合法性一致，见兼容性核实）。

### D-06 Snapshot 缺 Field 合法

**一句话结论**：Snapshot 内某 Field 无 realization 合法；**single-state projection 中该 Field 保持 declaration-only**，由 ADR-022 D-06 零足迹语义接管；**不要求不同 Snapshot 字段同构**。

**展开解释**：canonical temporal state 的完整性要求归下游 consumer（Dataset / transforms 层自定充分性判定）；不得为 batching 或训练便利要求字段完全同构。

### D-07 `FieldData.timestep` 去 canonical temporal authority

**一句话结论**：`FieldData.timestep` 保留现有成员，但**不再具有 canonical temporal authority**——不参与 Snapshot membership、global ordering、跨 Field 对齐或 selection；**不得被重新定义为 physical_time 或一般性 provenance 真源**；防错帧守卫：**Snapshot 的 solver_step 与其成员 FieldData 的 timestep 二者同时存在时必须一致，否则 fail-fast**；不要求 timestep 与 physical_time 做一致性比较；长期删除或迁移 deferred。

**展开解释**：timestep 的 canonical temporal 职能由 Snapshot（membership + physical_time，D-02 / D-03 / D-08）唯一接管——时间组织语义只有一个权威来源。防错帧守卫利用 timestep 与 solver_step 同为「来源步号」语义的重叠做一致性校验（错帧注册的主要检测面），但不因此恢复 timestep 的权威地位。Phase 2 现有构造签名与成员集零变化（ADR-020 D2 本不冻结成员形态）。

### D-08 global ordering 与显式 selection

**一句话结论**：canonical global ordering = **同一 temporal organization 内按 physical_time 升序**（唯一性由 D-02 支撑；下标、注册顺序、solver_step 均不构成时间序）；显式 Snapshot selection 的结果是 **single-state canonical CAEGraph projection——必须满足 ADR-022 现有 input contract**；**adapter 零修改、zero-selector**；projection 的实现形态（copy / lazy view / 其他）不冻结。

**展开解释**：single-state projection 的组成 = 所选 Snapshot 的全部成员 + **全部** global realizations（global 不复制、各状态共享）。projection 满足 ADR-022 D-01 profile（CAEGraph canonical representation、`validate()` 通过、cell-based topology provider、`n_entities ≥ 1`）与 D-05 前提（每 Field 恰一 realization——由 D-03 / D-05 保证），因此**无需修改 ADR-022 任何条款**；多 realization 原图直接进入 adapter 仍 fail-fast（ADR-022 D-05 原样）。选择发生在 adapter 之前；adapter 不知道也不需要知道「为什么这一帧被选择」。selection / ordering 的具体 API 与视图类型 defer Design UML / implementation（不覆盖项）。

## 义务分界（canonical temporal organization 与 Dataset / transforms）

- **canonical temporal layer（本 ADR，representation 侧）**：Snapshot organization（membership / scope）、global ordering、explicit single-state selection、snapshot iteration（可访问的时间顺序）。
- **Dataset 层**：window size / stride / history length / prediction horizon / target construction / sequence sampling strategy——ML window semantics 不得进入 FieldData 或 Snapshot 定义。
- **transforms 层**：窗口内派生编码。
- **adapter**：忠实物化，零修改（ADR-022）。

## 兼容性核实（对既有契约逐条核对）

| 既有契约 | 原文要点 | 本 ADR 影响 |
| --- | --- | --- |
| Field : FieldData = 1:0..*（ADR-020 标题行冻结语义基数） | 「1:0..* 关系……Field 为 name/unit/association/component semantics 唯一真源」 | **不变**——Snapshot 对 FieldData 是**非拥有型 organization / membership relation**，只组织既有 realization，不改变 Field → FieldData 的语义基数与真源关系 |
| ADR-020 D4 canonical data flow | 「realization data 位于 CAEGraph canonical data flow……ownership / container / storage 不冻结」 | **承袭**——Snapshot membership 属 canonical organization 语义；存储 / 容器形态本 ADR 同样不冻结（D-04） |
| ADR-020 D6 | 「representation construction 可合法保存多个 realization；要求唯一 realization 的消费须显式选择或显式失败」 | **保持**——跨 Snapshot 每 Field 各一 realization 即 D6 的多 realization；显式选择纪律由 Snapshot selection 承接（D6 明文「eligible 判定与显式选择机制不冻结」，本 ADR 即其 temporal 轴裁决） |
| ADR-018 六领域概念 / ADR-007 D6 六抽象 | 「Fields 仍为一个领域概念……FieldData 不构成第七领域概念」（ADR-018 注记）；「不新增计数」（ADR-007 D6） | **不变**——Snapshot 沿同一纪律，为 organization construct，不增两处计数（D-01 引用原文） |
| ADR-022 D-05 / D-06 | 多 realization 一律 fail-fast、零 selector、无 timestep 豁免；declaration-only 零足迹 | **零修改**——selection 前置（D-08），原图直入 adapter 行为不变；缺 Field 由 D-06 零足迹接管 |
| ADR-022 不覆盖项 temporal view | 「另立 microdecision，立项触发：①②③满足其一即立项」 | **承接**——本 ADR 即该 microdecision 立项；ADR-022 正文零修改 |
| **两处 Phase 2 收窄（显式披露，非既有冻结事实）** | — | D-04 per-Field scope 禁混、D-05 global realization 上限——均为 ADR-023 新增 profile 限制（D-04 / D-05 正文已披露） |

## 本 ADR 不覆盖项（scope exclusions）

- Snapshot / scope / membership 的存储结构与容器形态（list / dict / 其他）、HDF5 layout、lazy loading、内存策略；
- temporal 写入口机制（含 builder 是否参与、以何种方式参与）——本 ADR 只冻结结构义务（D-04）；
- 具体 API（`add_snapshot()` / `assign_snapshot()` / `snapshot()` / `iter_snapshots()` 等）与 `SnapshotView` 等视图类型；整帧注册 vs 逐 FieldData 归属的实现方式；
- projection 实现形态（copy / lazy view / 其他）与 selection API 形态（D-08）；
- snapshot identity / physical_time / solver_step 的具体成员形态（D-02）；
- Dataset window 语义（window size / stride / history / horizon / target / sampling）与 Dataset 实现；
- 第二 realization axis（ensemble / multi-source / multi-fidelity；同一 Snapshot 内同一 Field 的多 realization）；
- `FieldData.timestep` 的长期删除或迁移（D-07）；
- PyG 单帧时间标注的键呈现（仍 defer——ADR-022 D-02 键集封闭，本 ADR 不改其正文）；
- mesh / mesh-free representation form（独立议题，明确不打开）。

以上各项禁止提前实现接口等待未来确认；纳入决策范围须专门架构决策。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| A. `FieldData.timestep` 作时间真源，按时间数值派生 frame（前案） | 否决 | 瞬时状态沦为消费端推导约定，非 canonical 结构关系；float 相等脆弱且「无 timestep」语义不可判定（steady 还是漏注册）；三个时间概念被压缩进一个 float |
| B. graph-level Snapshot membership（本案） | 采纳 | membership 是定义性结构关系——canonical representation 显式表达「同一瞬时状态」；三时间坐标各归其位；steady / transient scope 显式；selection 产物满足既有 adapter input contract，ADR-022 零修改 |
| B'. 时间容器复制时间值（TemporalFrame 持有 t，成员各自保留时间） | 否决 | 物理时间双份存储 → 第二时间真源 |
| C. adapter 内扩展时间选择 / 排序 | 否决 | 直接违反 ADR-022 D-05 冻结 |
| D. 继续 defer 至 Dataset 实现期 | 否决 | 立项触发条件已满足（FACT-01）；无契约则 gate 6 temporal dataset 无验收对照物 |

## 影响（Consequences）

- 新能力：transient 数据的 canonical 组织——同一瞬时状态显式结构化、global ordering、显式 selection；steady / global realization 单份存在、各状态共享，无逐帧复制。
- 成本：一个未来 temporal organization coding dispatch（Snapshot membership / scope 校验 / selection projection 的实现与守卫测试——`ADR-023-invariants.yaml` TEST_MISSING 条目的证据落点）；Design UML 随该 dispatch 具体化。
- `FieldData.timestep` 语义降级为非权威（现有签名零变化；长期迁移 deferred）。
- ADR-020 / ADR-021 / ADR-022 正文零修改；两处 Phase 2 收窄显式披露（D-04 / D-05）。
- Dataset / transforms 层获得明确上游契约（义务分界）；window 语义归 gate 6 及以后。
- 不改变依赖分层与 PyG 边界（ADR-007 D2）。

## Invariant 登记策略

- **eligibility 判断（本 ADR 独立作出）**：仅登记当前已可判定、且不引用任何 deferred API 形态的约束，TEST_MISSING 初版与本文档同 commit 创建；守卫测试随未来 temporal organization coding dispatch 经 PM 授权回填，证据同步永不与 feat 同 commit：D-02 physical_time 必在与同组织内唯一（D02-01）；D-03 `(Snapshot, Field) ≤ 1 FieldData`（D03-01）；D-04 scope 二分（D04-01）与 per-Field scope 禁混 fail-fast（D04-02）；D-05 global realization 上限（D05-01）；D-07 solver_step / timestep 同在一致性 fail-fast（D07-01）。
- **不登记**（eligibility 排除）：ordering / selection / projection 条目——其可执行形态依赖 deferred 的视图与选择 API；snapshot identity 成员形态、迭代 API 等同理由不登记。
- Markdown ADR 仍是唯一决策真源；YAML 只作机器可读核验索引，禁止反向冻结本 ADR 的不冻结项。

## 修订历史（Revision history）

- 2026-10-05 v1：草案（proposed）——方向比较后采纳 Snapshot membership 方案；前案（timestep 数值分组派生 frame）经 PM 中断否决，理由存档于备选方案表 A 行。九项起草修正随 v1 落盘：D-03 唯一性统一为 `(Snapshot, Field) ≤ 1 FieldData`（时间值不入判据）；D-04 scope 禁混显式披露为 Phase 2 收窄、解除写入口冻结（只冻结构义务）；D-05 定位为 Phase 2 限制（非普适定律、非 adapter 兜底理由）；D-07 timestep 去权威 + solver_step 一致性守卫 + 不与 physical_time 比较；D-02 / D-08 时间坐标契约补强（physical_time 必在且同组织内唯一、solver_step 可选）；projection 实现形态不冻结；兼容性核实逐条引用原文；YAML 依 eligibility 判断登记。
