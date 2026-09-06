# ADR-012: Mesh 读取转换管线与物理组语义契约

- 编号：ADR-012
- 标题：以 AbstractMeshLoader 模板方法定义跨格式统一转换管线（唯一
  格式钩子 `_read`）；冻结物理组维度分类契约、全局索引契约与
  「IO 永不推断 BoundaryType」边界；域分组为 Mesh 朴素数据，边界分组
  物化为 BoundaryRegion
- 日期：2026-09-06（同日返工：初版 Region 继承树提案经评审否决，本版
  为重写，否决理由见备选方案表）
- 状态：accepted
- 关联：ADR-007（D3 反 god-object / D4 共享词汇）、ADR-008（跨软件
  定位）、ADR-009（BaseObject 限于 domain-truth）、ADR-010（三层职责
  链与区域元数据）、ADR-011（槽位一致性校验）、ADR-013（IO 引擎，
  provisional）、Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

CAEGraph 的 io 层要解决的真实问题：不同输入（gmsh、Fluent、ICEM、
Pointwise…）**数据结构各异**，读取后必须转为相同的框架对象
（`caegraph.core.Mesh`）。这个转换**流程是相同且确定的**——因此抽象
预算应当投向**转换管线**（用抽象类定义一次），而非领域对象的分类学
（初版提案的 Region 继承树经评审否决）。

开工前暴露并需一并冻结的问题：

1. **单元编址语义**：Mesh 同时持有 triangle/quad 等多类型 cell 块时，
   分组索引是全局编号还是块内编号必须冻结——否则 block 一重组
   （triangle block 0 + triangle block 1 + quad block），region 就可能
   指错单元。
2. **物理组语义分类**：physical group 不全是边界（二维 `fluid_domain`
   dim 2 是计算域，`inlet/wall` dim 1 才是边界）。
3. **物理语义职责边界**：`inlet → DIRICHLET` 之类的名称→类别推断
   是否允许出现在 IO 层（ADR-010 已裁定软件命名≠数学类别）。

## 决策（Decision）

1. **AbstractMeshLoader 转换管线（模板方法，落于 `caegraph.io`）**：

   ```
   __call__(path) -> Mesh            # 固定流程（final）
     1. raw = self._read(path)       # 唯一的格式钩子（抽象方法）
     2. 组提取：name / (tag, dim) / 成员
     3. dim 分类（本 ADR 第 3 条契约）
     4. 构造：域组 → Mesh 域分组数据（第 4 条）；
              边界组 → BoundaryRegion → BoundaryManager（第 5 条）
     5. mesh.validate() fail-fast    # 不变量统一执行
   ```

   分类、构造、校验**只写一次**，位于基类；具体格式 loader（gmsh 首发）
   只实现 `_read` 钩子。未来 Fluent/ICEM/Pointwise loader 同样只写钩子，
   永不复制管线。IO 引擎（meshio，ADR-013）只在钩子后面，可整体替换。

2. **全局索引契约（编址唯一真相）**：
   - **全局 cell 索引**：0-based 连续，跨类型、跨 block 统一编址；
     域分组、单元场（Field 的 cell association）、未来 Graph 的 cell
     视图共享同一全局索引空间。
   - triangle/quad 分块仅为**内部存储结构**，禁止渗入任何编址语义。
   - Loader 在管线固定阶段**一次性**完成 block-local → global 重编号。
   - **全局 node 索引**：单一节点索引空间（.msh/meshio 天然全局，
     显式声明以防未来格式破坏）。
   - 校验不变量（validate 强制）：域分组存在时各组并集 == [0, n_cells)；
     分组索引界内；边界分组节点集 ⊆ 全体节点。

3. **物理组维度分类契约**（格式无关，管线固定阶段）：以
   `topo_dim = 网格最高单元维度`（加载时推断）为基准：
   - `group_dim == topo_dim` → 计算域/子域/材料块（cell 成员）；
   - `group_dim == topo_dim − 1` → 边界（节点成员，由边界单元归纳）；
   - `group_dim < topo_dim − 1` → 跳过并输出 warning（确定性留痕）。

4. **域分组 = Mesh 朴素数据**：`Mesh` 持有 `name → 全局 cell 索引数组`
   映射（`dict[str, ndarray]`），纳入 validate；**不设类、不设继承**——
   语义区分仅体现在数据与校验规则。域分组不可被 BoundarySpec 绑定。

5. **边界分组物化为 `BoundaryRegion`**（BaseObject domain-truth 家族）：
   槽位 = 唯一名 / dim / 节点成员集（全局 node 索引）/ 开放元数据
   （软件命名 wall/inlet…，ADR-010；角色提示，ADR-011）。BoundaryManager
   保存 `name → BoundaryRegion 对象`并承担 spec 按名绑定解析与
   corner（多区域交集）查询；`BoundarySpec` 以名字符串引用目标区域，
   bind 时校验存在性并拒绝域分组名。诞生地：`core/boundary/region.py`；
   io 层只消费、只构造。

6. **IO 永不推断 BoundaryType**：加载器的职责终点是产出命名 Region
   与朴素域分组；数学类别只能来自用户声明的 BoundarySpec。禁止任何
   `名称 → 数学类别` 映射表进入 IO 层（同名在不同问题中可为三种数学
   类别，ADR-010 背景论据）。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| Region 抽象基类 + DomainRegion / BoundaryRegion 继承树（初版提案） | 否决（评审） | 分类学非真问题；抽象预算应投向转换管线；真问题是异构输入经统一管线转为同一框架 |
| 域分组轻量记录类（frozen dataclass，无继承） | 否决（评审） | 与「Region 不必要」裁决边缘相近；dict + 校验已足，避免无设计依据的新抽象 |
| cell 分组采用 block 内部编号 | 否决 | block 重组即指错单元；多类型块编址歧义；违反单一编址真相 |
| IO 层内置名称→数学类别推断表 | 否决 | 物理语义僭越；同名不同义（ADR-010）；错误随格式清单复制 |
| 物理组全量映射为边界 | 否决 | 计算域误注册为边界：Spec 可绑定域、corner 查询污染 |
| 各格式 loader 自行实现分类与构造 | 否决 | 契约复制漂移；Fluent/Abaqus/ICEM 会各自发明规则 |

## 影响（Consequences）

- Phase 2 模块清单：`io/` 增加管线基类模块（abstract loader）与
  `gmsh.py`（钩子实现）；`core/boundary/` 增加 `region.py`；
  `core/region.py` 不再需要（phase2-cae-data.md 模块树待本 ADR 评审
  通过后另行同步）。
- Mesh 组成：geometry / topology / boundary / **domain groups（朴素
  数据）** / fields（anti god-object 边界不变，ADR-007 D3）。
- Testing 需覆盖：全局重编号正确性（多 block 场景）、域并=全体单元、
  dim 分类（域组不入边界注册表）、低维组跳过告警、Spec 绑定域名被拒、
  索引界内、IO 无 BoundaryType 推断。
- 未来格式加载器继承第 2、3、6 条契约，作为其各自 ADR 的既定前提。
- 不改变依赖方向与 PyG 边界（ADR-007 不变）；不冻结 IO 引擎
  （ADR-013 provisional）。
