# ADR-014: Mesh canonical 数据模型

- 编号：ADR-014
- 标题：定义 CAEGraph Mesh canonical representation——canonical cell 存储与显式 facet 拓扑双 CSR、身份契约、connectivity 语义（facet winding-free / cell 有向局部拓扑且不含 backend 编号）、CellType 词汇与显式稳定编码、校验分层（拓扑合法性 / 条件 coverage-partition）
- 日期：2026-09-06
- 状态：accepted
- 关联：ADR-007（D3 反 god-object / D6 Field）、ADR-008（跨软件定位）、ADR-009（BaseObject 限于 domain-truth）、ADR-010（三层职责链）、ADR-011（槽位一致性）、ADR-012（读取管线，本 ADR 修订其决策 2/5）、ADR-013（IO 引擎 provisional）、Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

Phase 2 开工纠偏（先设计 Mesh、后写 IO）后经七轮架构评审收敛。要解决的核心问题：CAEGraph Mesh 必须是**面向 CAE→Graph/Physics AI 的 canonical representation**，而非 meshio/Gmsh 内部结构的包装。外部世界的数据（block 布局、physical tag 表示、cell 局部编号、facet 源绕向）必须在进入 `core.Mesh` 之前被 IO normalization 完全消化。

## 决策（Decision）

### 1. Canonical cell storage + derived type views

全局布局是唯一真源：

```
cells:  cell_types（显式整数编码 ndarray） + 扁平 connectivity + offsets
```

- 全局索引即存储索引（CSR 风格 ragged array）；
- 按类型分组的二维矩阵块只能是**派生视图/缓存**（如 cells_of_type 风格），不具独立身份，永不构成第二套编址体系；
- 复杂度表述（严谨版）：**O(1) 定位**某 cell/facet 的 connectivity **切片**；读取为 O(k)，k 为该单元节点数（小常数）。

**不变量（原句冻结）**：

> CAEGraph entity IDs refer to canonical Mesh storage — nodes, cells, facets — never to loader/backend block-local indices.

### 2. Canonical explicit facet topology（平行 canonical 表）

facet（dim == topo_dim − 1 的边界/界面实体：2D 网格为 edge，3D 为 face）拥有与 cell 平行的 canonical 表与**独立稳定的全局索引空间**：

```
facets: facet_types + fconn + foffsets + facet_cells(ragged 邻接)
```

- **收录范围**：仅收录**由 IO adapter 或用户显式声明、且需要保留独立语义/稳定引用**的 boundary/interface facets；未命名内部 facet 不入表，由 geometry 层按需推导（最小真源）。
- **facet_cells**：每个 facet 邻接的全局 cell id 列表（ragged/CSR，不硬编码上限以容忍非流形：len==1 外边界候选、==2 内部/界面、≥3 非流形）。由加载/规范化管线 build 阶段计算一次并存为 canonical——它不是可随时重算的普通 geometry cache：cell-relative 法向、interface 检测、Neumann/Robin、surface graph 都依赖这套邻接。
- **维度边界**：canonical topology 只容纳 dim == topo_dim 的 canonical cells 与 dim == topo_dim − 1 的 canonical facets；dim < topo_dim − 1 的 source entities（角点/曲线标记等）当前版本**不进入** canonical topology。本 contract 面向**单一拓扑维度网格**；真正的 mixed-dimensional mesh（3D solid + 2D shell + 1D beam）留待未来 ADR 扩展。
- interface 能力注记：邻接 + 域分组 → 界面 facet 检测（如 fluid|solid 共享 facet），为未来 INTERFACE/PERIODIC 供数据基础。

### 3. Connectivity 语义（双语冻结）

```
facet：winding-free——canonicalization 同时考虑原序与反序的全部
       cyclic rotations，选择唯一确定性表示（如字典序最小者）；
       不承诺 intrinsic normal；法向始终相对于指定 adjacent cell
       定义；signed cell-facet incidence 作为未来性能演进。
cell ：保留有向局部拓扑语义，但不保留 backend-specific 节点编号——
       IO normalization 必须将各来源的单元局部编号映射为 CAEGraph
       CellType 的 local-node convention。
```

> Facet connectivity is winding-free. Cell connectivity retains oriented local-topology semantics, but backend-specific local node ordering must not leak into core.

**CAEGraph local-node convention**：具体 per-type 局部编号表不进本 ADR，**随 CellType 实现冻结**（docstring 表 + 测试，一经发布即稳定），列为 Coding gate 的具名交付物。

### 4. CellType 词汇与编码

```
LINE2 / TRI3 / QUAD4 / TET4 / PYR5 / WEDGE6 / HEX8
（POINT 与高阶单元 TRI6/TET10… = 记录在案的未来扩展）
```

- str-Enum 序列化面（"tri3" 等，与 BoundaryType 同风格）；
- **显式稳定整数内部编码**（概念上 LINE2↔1、TRI3↔2…），映射由 CAEGraph 显式定义并测试：

> Integer encoding is explicit and stable; it must not derive implicitly from enum declaration order.

- 每类型携带：`dim`、`node_count`、local-node convention、**codim-1 face templates**（topology 校验与 geometry 推导的共用依据）。

### 5. 身份契约（canonical identity contract）

```
Nodes        → stable global node IDs
Cells        → stable global cell IDs + canonical CellType +
               CAEGraph local-node convention + oriented connectivity
Explicit Facets → stable global facet IDs + winding-free
               connectivity + validated ragged cell adjacency
Domain groups（计算域/材料分组）      → global cell IDs
Boundary / Interface groups          → global facet IDs
Field(node) → node IDs；Field(cell) → cell IDs
```

### 6. 职责切分（anti-god-object）

- **Mesh 拥有拓扑事实**（nodes / cells / facets / facet_cells）；
- **BoundaryManager 只做语义引用**：name → BoundaryRegion 的命名分组、spec 按名绑定解析、corner（多区域交集）查询——不同时承担拓扑存储与边界语义；
- **BoundaryRegion 引用 topology，不拥有 topology**：canonical 成员 = 全局 facet 索引；节点集是派生视图，永不作为真源（节点集不能唯一重建 facet connectivity，反向才成立）。

### 7. Mesh 组合与生命周期

```
nodes: ndarray (n_nodes, 3) float64（规范 3D 存储，见 8a 强制不变量） + topo_dim（= canonical cells 的共同拓扑维度，与 domain_groups 无关）
cells: canonical CSR（决策 1）
facets: canonical CSR + facet_cells（决策 2）
BoundaryManager: name → BoundaryRegion
domain_groups: dict[str, ndarray]（全局 cell 索引，朴素数据，无类）
fields: dict[str, Field]；经 add_field 追加并校验关联长度
metadata: BaseObject 槽位
```

**结构冻结、场可追加**：nodes/cells/facets/分组在构造 + validate 后冻结；Field 可经显式方法追加。坐标固定 `(n, 3)` 规范存储。

### 8. 校验分层

**8a 拓扑合法性（validate 无条件强制）**：

- offsets 单调（cells 与 facets 两表）；
- 单元/facet 节点数 == CellType 规定数；
- 节点/cell/facet 索引界内；
- **nodes 形状与 dtype**：nodes 必须为二维数组，shape == (n_nodes, 3)，dtype == float64；topo_dim 独立于坐标列数——2D Mesh 仍采用三分量坐标存储，禁止以列数携带拓扑维度；
- **维度层级（blocker 修正）**：所有 canonical cells 的 dim == topo_dim；所有 canonical facets 的 dim == topo_dim − 1；dim < topo_dim − 1 的 source entities 不得进入 canonical topology（决策 2 维度边界）；
- **facet 邻接完整性**：每 facet ≥1 个 adjacent cell；facet_cells 中 cell id 界内且不重复；**每个 facet 必须匹配其每个 adjacent cell 的合法 codim-1 face**（依据 CellType face templates）——facet_cells 是经过验证的 canonical topology，不是未经验证的附加数组；
- 场值长度与关联（node/cell）匹配。

**8b 条件检查（非 universal invariant；语义写准，暂不加 API）**：

```
complete_coverage  ：组并集 == 全体目标 cells
complete_partition ：coverage + 组间两两不交

二者不是 Mesh 的 universal invariant；
由调用方/加载管线根据数据语义显式声明并校验。

Gmsh physical domain groups：
- 不默认视为 complete partition；
- adapter 根据实际 physical-group 映射判断 coverage / overlap；
- 只有明确满足且调用路径要求 partition 时，才执行
  complete_partition 检查。
```

无分组网格（拓扑合法）不被迫制造 "default" 组。

### 9. 对 ADR-012 的修订

- **决策 2**：「域分组存在时并集 == [0, n_cells)」不再是 universal invariant——改为 8b 的 complete_coverage / complete_partition 条件检查；「边界分组节点集 ⊆ 全体节点」随成员表示演进而被 8a 的 facet 强一致校验取代。
- **决策 5**：BoundaryRegion 的 canonical 成员改为**全局 facet 索引**；节点集降级为派生视图。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| meshio 风格分块存储 + 全局映射表 | 否决 | dual source of truth；所有 API 被迫区分 global id 与 block-local id |
| 边界仅存节点集（B 路线） | 否决 | 节点集不能唯一重建 facet connectivity；读取时丢弃权威信息、使用时启发式重建，违反 canonical 设计目标 |
| 区域内自存 connectivity（C 路线） | 否决 | 无共同 facet 身份，跨区域比较退化为节点集合比对；Region 拥有而非引用 topology |
| 全量 facets 入表（F2） | 否决 | 与最小真源冲突；3D 存储约 3–4× cells；大量 facet 永无消费者 |
| facet 归一化仅旋转最小节点在前 | 否决 | 不消除 winding 差异：[5,8,3]→[3,5,8] 与 [5,3,8]→[3,8,5] 仍不同，源绕向泄漏进 canonical 表示 |
| cell connectivity 保留源文件顺序 | 否决 | backend 局部编号约定不同（QUAD4/HEX8 等不止顺逆时针），源序入 core 使 CellType 无统一局部拓扑语义，污染 Jacobian/face 推导/匹配/插值/法向 |
| CellType 整数编码取 Enum 声明顺序 | 否决 | 隐式编码随声明顺序漂移，历史 Mesh/缓存全错 |
| 域分组并集覆盖作为 universal invariant | 否决 | 无材料分组的合法拓扑网格被判非法，被迫制造 "default" 组（语义污染） |
| gmsh 有体分组 ⇒ 视为 complete partition | 否决 | gmsh 实体可参与多个物理分组，外部语义不能固化进 canonical Mesh |
| canonical cells 允许 dim ≤ topo_dim（旧 8a 表述） | 否决（评审 blocker） | 2D Mesh 会同时把 TRI3 与 LINE2 放入 canonical cells，而 LINE2 又可能作为 canonical facet，重新产生双真源；cells/facets 的维度角色必须互斥 |

## 影响（Consequences）

- **Coding gate 具名交付物**：CellType 实现——局部编号表、codim-1 face templates、显式整数编码映射，docstring + 测试（一经发布即稳定）。
- loader 义务（ADR-012/013 落地时执行）：消化 block 布局、物理 tag、**源局部编号映射**、**facet 源绕向消除**、build 阶段计算并验证 facet_cells；meshio 类型与 block-local id 死在 io 层。
- Testing 需覆盖：全局重编号（多 block）、归一化确定性（同 facet 不同源序/绕向 → 同一 canonical 表示）、facet↔cell 强一致（含伪造邻接的失败用例）、coverage/partition 条件检查、无分组网格合法、结构冻结语义、add_field 校验。
- 未来格式加载器（Fluent/Abaqus/ICEM/Pointwise）继承本合同的全部 normalization 义务。
- 本 ADR 不引入依赖（meshio 见 ADR-013 provisional）、不改变依赖方向与 PyG 边界（ADR-007 不变）。
