# ADR-011: 边界词汇重估——Phase 2 维持单一 BoundaryType

- 编号：ADR-011
- 标题：执行 ADR-010「未来演进」预定的 Phase 2 重估：两个触发条件均未命中，维持单一七值 `BoundaryType`；以 `BoundarySpec` 槽位一致性校验加固，并细化 Phase 3 重触发条件
- 日期：2026-09-06
- 状态：accepted
- 关联：ADR-010（重估对象，保持 accepted 不被取代）、ADR-007（D4 共享词汇）、ADR-008（跨软件抽象定位）、Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

`phase2-cae-data.md` 将 ADR-010「未来演进」列为 Phase 2 开工前置：在实现 `BoundarySpec` / `BoundaryManager` 之前，必须对照 ADR-010 记录的触发条件重估 `BoundaryConditionType` × `BoundaryRegionType` 拆分候选，并以 ADR 记录结论（"decide by ADR, not silently"）。本 ADR 即该重估的结论记录。

触发条件（ADR-010 原文归纳）：

- T1：physics / transforms 层需要以不同方式处理「施加约束」与「接口配对」（如 INTERFACE 需要携带跨域配对元数据而非约束值）；
- T2：Phase 2 的 region 元数据无法自然表达角色信息。

## 重估分析（Evaluation）

**T1 未命中（证据不足）。** Phase 2 的 BC 编码（`transforms/physics.py` 规划）是 mask + 特征赋值模式：值驱动类型（DIRICHLET / NEUMANN / ROBIN）写入值或参数特征，配对驱动类型（PERIODIC / SYMMETRY / INTERFACE）只携带标识与配对信息。二者确实分叉，但分叉的**调度依据是 `BoundarySpec` 的槽位形状**（`paired_region` / `parameters` 是否存在，ADR-010 已设计）而非枚举分类学；且 Phase 2 的 GraphBuilder 只做 node / cell 视图构建，不实现周期边合成或跨域接口点匹配——配对数据在本 Phase 仅被**承载**，真正的消费方是 Phase 3 的 physics 损失层。

**T2 未命中（结构无阻塞）。** BoundaryRegion 元数据是开放的 str→Any 映射，external / interface / internal 等角色信息可以作为**数据**自然存放；gmsh 物理组 → region 的映射不因词汇单复而受阻。

**候选拆分本身分类不纯（决定性论据）。** PERIODIC / SYMMETRY 横跨两个轴：既近似约束，本质上又是区域间几何关系；而 DIRICHLET 型条件完全可以施加在 INTERFACE 区域上（CHT 界面连续性）。真正正确的模型（若需要）是 **正交双轴**：region role × constraint type，而非把一个枚举重新划成两个互斥枚举。设计该模型所需的证据——界面连续性算子、周期配对损失、观测约束训练的实际形态——要到 Phase 3 才出现。

**拆分时机成本不对称。** 项目未发布（0.x，无序列化消费者），任何时候拆分都没有兼容负担；现在拆分是投机，Phase 3 拆分是有据。ADR-010 当初的顾虑（gmsh 映射被迫同时面向两套词汇）依然成立。

## 决策（Decision）

1. Phase 2 维持单一 `BoundaryType` 七值枚举不变（ADR-010 决策继续有效）；`BoundarySpec` / `BoundaryManager` / Graph 输入编码均以七类为准。
2. **加固措施（Phase 2 实现约束）**：`BoundarySpec` 必须实现按类型的 **槽位一致性校验**（fail-fast，符合 BaseObject 校验契约）：
   - `PERIODIC` ⇒ `paired_region` 必填；
   - 值槽（value / `FieldFunction`）仅对约束值类型（DIRICHLET / NEUMANN / ROBIN）有意义，非法组合直接报错而非静默忽略；
   - `INTERFACE` 的跨域配对信息优先存放在 `paired_region`，角色提示作为 region 元数据（数据而非词汇）表达。该校验使单枚举的语义混杂无害化，并让未来可能的拆分成为机械操作。
3. **Phase 3 重触发条件（细化并接替 ADR-010 的原始表述）**：
   - physics 损失实现界面连续性 / 周期配对算子时，单枚举分发变得广泛且语义浑浊（如「约束损失累加器」需要反复排除 INTERFACE / NONE）；
   - `BoundarySpec` 校验矩阵长出大量按类型特例，表明枚举混合了两个正交轴；
   - dataset 持久化 / GNN 输入编码需要按「角色 × 约束类型」正交查询。触发时的正确形态是正交双轴（role × constraint），经新 ADR 取代 ADR-010 / 011 的相应部分；既有七值按 ADR-010 记录的分组机械迁移。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 按 ADR-010 候选拆分为 BoundaryConditionType × BoundaryRegionType | 否决 | 候选分类不纯（PERIODIC / SYMMETRY 横跨两轴；DIRICHLET 可施加于 INTERFACE 区域）；触发条件未命中；Phase 3 前缺乏设计正交双轴的证据 |
| 立即升级为正交双轴模型（role × constraint） | 否决 | 投机性过强；gmsh 映射被迫同时面向两套词汇（ADR-010 原顾虑）；无消费者压力 |
| 维持单一枚举 + 槽位一致性校验（本决策） | 采纳 | 触发条件未命中；加固后语义混杂无害；未发布状态下推迟拆分零成本，Phase 3 有据后再议 |

## 影响（Consequences）

- Phase 2 可直接开工 `core/boundary/` 三件套：词汇无变化，无迁移成本。
- `BoundarySpec` 实现多一项按类型的校验矩阵；Testing Agent 须为非法组合编写失败用例（如 `PERIODIC` 缺 `paired_region`、`INTERFACE` 携带 value）。
- ADR-010 保持 accepted、不被取代；其「未来演进」节的候选方案由本 ADR 的重估结论与细化触发条件接替。
- 序列化面不变：七值小写字符串，「仅增不改」原则继续有效。
- 本 ADR 不引入新包、不改变依赖方向与 PyG 边界（ADR-007 不变）。
