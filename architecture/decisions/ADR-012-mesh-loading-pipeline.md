# ADR-012: 跨格式加载的 source normalization → canonical Mesh 管线与源分组语义契约

- 编号：ADR-012
- 标题：定义跨格式 Mesh 加载管线（`__call__` 稳定、protected hook 不冻结）：source → format-specific normalization → canonical Mesh build（ADR-014）→ validate；源分组（source-group）按维度分类为 domain / boundary|interface / unsupported；normalization 义务；IO 永不推断 BoundaryType
- 日期：2026-09-06
- 状态：accepted
- 关联：ADR-007（分层与共享词汇）、ADR-008（跨软件定位）、ADR-010（三层职责链）、ADR-011（Spec 槽位一致性）、ADR-013（IO 引擎 provisional）、**ADR-014（canonical Mesh 数据模型——Mesh 结构的权威定义）**、Phase 2、Design UML `class_diagram.puml`

## 职责边界（Scope）

本 ADR 只回答一个问题：**外部数据如何被规范化并进入 canonical Mesh**。「Mesh 必须长什么样」一律由 ADR-014 立法；本 ADR 不重复定义任何存储布局、索引契约或校验规则，避免两处立法漂移。

```
ADR-012 = 怎么进入 Mesh（source normalization → canonical build）
ADR-014 = Mesh 到底是什么（canonical 结构、身份、校验）
```

## 背景（Context）

不同输入（Gmsh、Fluent、Abaqus、ICEM、Pointwise…）数据结构各异，读取后须转为同一框架对象 `caegraph.core.Mesh`。转换流程跨格式共享且确定，因此抽象预算投向 **source-normalization 管线**（统一入口），而非领域对象分类学（初版 Region 继承树提案经评审否决，见 Options）。同时需冻结源分组语义边界（维度分类、命名实体 ≠ 数学类别）与 normalization 义务。

## 决策（Decision）

### 1. 加载管线契约（Pipeline contract）

统一入口稳定；格式差异经 source-specific 阶段消化，不预演未来格式形态：

```
AbstractMeshLoader.__call__(path) -> Mesh
  1. obtain source representation
  2. perform source-specific normalization
  3. build canonical Mesh according to ADR-014
  4. validate canonical Mesh
  5. return Mesh
```

> `__call__` pipeline is stable; the number and naming of protected format-specific hooks are implementation details and are not frozen by this ADR.

分类、构造、校验规则不按格式复制（步骤 2 之后共享 ADR-014 的 build 语义）。IO 引擎（meshio，ADR-013 provisional）只存在于步骤 1–2 的实现细节，可整体替换。

### 2. 源分组（source-group）语义分类契约

以 ADR-014 的 `topo_dim`（canonical cells 的共同拓扑维度）为基准，对所有 **source named group** 分类。术语跨格式中立：Gmsh physical group、Abaqus element set / surface、Fluent zone 都是 source named group 的实例，不得被强制冠以 "physical group"。

**topo_dim 确定顺序**：加载过程中 Mesh 尚未正式构造，`topo_dim` 必须由 normalized canonical-cell candidates 依 ADR-014 确定，**绝不从 source-group 维度反推**：

```
source cells → CellType normalization → 确定 top-dimensional canonical cells → topo_dim → 再分类 source groups
```

（禁止反向：先看有哪些 source groups 再反推 topo_dim——避免循环定义。）

```
source_group_dim == topo_dim      → domain group → 成员 = canonical global cell IDs
source_group_dim == topo_dim − 1  → explicit boundary/interface facet group → 成员 = canonical global facet IDs
source_group_dim < topo_dim − 1   → 不入 canonical topology → warning / diagnostics
```

- 写 **boundary/interface** 而非仅 boundary：codim-1 组既可是外部边界，也可是域间 interface（如 fluid|solid 共享 facet）。两者的承载对象统一为 `BoundaryRegion`（ADR-014 决策 6：命名 codim-1 facet-region 抽象，名称不意味必然位于外边界），禁止再造 InterfaceRegion。
- complete_coverage / complete_partition 是否成立由调用方按数据语义显式声明并校验（ADR-014 8b）；本 ADR 不默认 source named group 构成 partition（gmsh 实体可参与多个物理组）。

### 3. Normalization 义务

进入 `core.Mesh` 前，io adapter 必须消化以下全部 source 特定表示，使其不得渗入 canonical topology（身份契约见 ADR-014 决策 5）：

- backend block-local indices → global node/cell/facet IDs；
- source local-node ordering → ADR-014 CellType local-node convention；
- source facet winding → winding-free canonical connectivity；
- source group/tag representation → domain groups 与 boundary/interface BoundaryRegion 成员（global facet IDs）及元数据。

### 4. 物理语义边界（Physics semantic boundary）

加载管线的职责终点是产出 canonical Mesh、domain groups 以及命名 boundary/interface regions；数学 BoundaryType 只能来自用户声明的 BoundarySpec。禁止任何 `名称 → 数学类别` 映射表进入 io 层——同名在不同问题中可为不同数学类别（ADR-010 背景论据；Spec 槽位一致性见 ADR-011）。

### Revision history

- 2026-09-06 初版：Region 抽象继承树提案 → 评审否决（见 Options）。
- 2026-09-06 返工：改为转换管线 + 物理组维度分类（当时含 block 存储、node-set 边界成员、唯一 `_read` 钩子等过渡表述）。
- 2026-09-06 重写：ADR-014 冻结 Mesh contract 后，清退所有与 ADR-014 重复或已被其取代的立法（存储布局、全局索引契约、node-set 成员、域并覆盖不变量），只保留「进入」契约；术语统一为 source named group；protected hook 数量不再冻结。
- 2026-09-07 评审收口：明确 BoundaryRegion 为统一 codim-1 facet-region 抽象（含 internal interface）；补 topo_dim 确定顺序（不循环定义）；不要求每种新格式自建 ADR。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| Region 抽象基类 + DomainRegion / BoundaryRegion 继承树（初版提案） | 否决（评审） | 分类学非真问题；抽象预算投向转换管线 |
| 域分组轻量记录类（frozen dataclass） | 否决（评审） | 与「Region 不必要」裁决边缘相近；dict + 校验已足 |
| 冻结唯一 protected 钩子 `_read`（未来格式只实现一个钩子） | 否决（评审） | 各格式 source semantics 不统一，「组提取」本身可能是格式特定 normalization；过早锁死 future loader 形态 |
| 本 ADR 继续立法 block 存储 / node-set 边界 / 域并 universal invariant | 否决（评审） | 与 ADR-014 双立法漂移；规范文字必须保持单一当前世界 |
| "physical group" 作为跨格式核心术语 | 否决（评审） | Gmsh 专属术语；Abaqus set / Fluent zone 不应伪装成 physical group |
| IO 层内置名称→数学类别推断表 | 否决 | 物理语义僭越；同名不同义（ADR-010） |
| 源组全量映射为边界 | 否决 | 计算域误注册为边界；Spec 可绑定域、corner 查询污染 |
| 各格式 loader 自行实现分类与构造 | 否决 | 契约复制漂移；各格式各自发明规则 |

## 影响（Consequences）

- Phase 2 模块清单：`io/` 增加管线基类（AbstractMeshLoader）与 `gmsh.py` 首个实现；`core/boundary/region.py`（BoundaryRegion）；domain groups 为 Mesh 朴素数据（phase2-cae-data.md 模块树待评审通过后另行同步）。
- Testing 需覆盖：domain-group global-ID 映射；dim 分类（topo-dim 组不入 boundary/interface 注册表）；低维组 warning/diagnostics；可选 complete_coverage / complete_partition（**重叠组在未要求 partition 时合法；无分组网格合法**）；Spec 绑定 domain 组被拒（该跨层约束属 BoundaryManager/BoundarySpec 的 core contract，测试可置于 core 测试而非 io 测试）；io 层无 BoundaryType 推断；normalization 义务逐项（block-local / 局部编号 / 绕向 / 组表示消除）。
- 未来格式加载器（Fluent/Abaqus/ICEM/Pointwise）必须遵循本 ADR 与 ADR-014 的既有契约；**仅当**引入新的架构决策、偏离既有 normalization contract，或现有合同无法表达该格式时，才通过新 ADR 裁决——不是每种新格式都需要自己的 ADR。
- 不改变依赖方向与 PyG 边界（ADR-007 不变）；不冻结 IO 引擎（ADR-013 provisional）。
