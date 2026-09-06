# ADR-012: Region 抽象体系与物理组语义契约

- 编号：ADR-012
- 标题：落地 Region 抽象体系（Region 基类 + DomainRegion / BoundaryRegion），
  冻结 CAE 物理组的维度分类契约与「IO 永不推断 BoundaryType」职责边界
- 日期：2026-09-06
- 状态：accepted
- 关联：ADR-007（D3 反 god-object / D4 共享词汇）、ADR-008（跨软件定位）、
  ADR-009（BaseObject 限于 domain-truth）、ADR-010（三层职责链与区域元数据）、
  ADR-011（槽位一致性校验）、ADR-013（meshio IO 引擎）、Phase 2、
  Design UML `class_diagram.puml`

## 背景（Context）

Phase 2 的 gmsh 读取切片开工前，暴露出四个必须先冻结的架构问题：

1. **BoundaryManager 的内部表示**：保存 `name → 节点索引集`（方案 A）还是
   `name → BoundaryRegion 对象`（方案 B）？
2. **物理组语义分类**：gmsh physical group 不全是边界——二维网格的
   `fluid_domain`（dim 2）是计算域，`inlet/wall`（dim 1）才是边界；三维
   同理（体域 vs 边界面）。若全量映射进 BoundaryRegion，计算域将被错误
   注册为边界（Spec 可绑定到域、corner 查询被污染）。
3. **物理语义的职责边界**：`inlet → DIRICHLET` 之类的名称→数学类别推断
   是否允许出现在 IO 层？（ADR-010 已裁定软件命名≠数学类别，但未明确
   IO 层的禁止条款。）
4. **抽象的诞生地**：Region 相关类是核心领域抽象，必须先进入 Design UML
   与 ADR，禁止 Coding Agent 在 `io/gmsh.py` 里顺手创造。

本 ADR 一并回答以上四问，使未来 Fluent / Abaqus / OpenFOAM 加载器直接
继承同一契约而非各自发明。

## 决策（Decision）

1. **Region 抽象体系**（三方均继承 BaseObject，domain-truth 家族）：
   - `Region(BaseObject, abstract)`——公共槽：唯一名、拓扑维度、成员
     索引集、开放元数据（str→Any）；
   - `DomainRegion(Region)`——`dim == topo_dim`：计算域/子域/材料块，
     **cell 成员集**，由 Mesh 持有（`Mesh o-- "*" DomainRegion`），
     **不可被 BoundarySpec 绑定**；
   - `BoundaryRegion(Region)`——`dim == topo_dim − 1`：边界位置，**节点
     成员集**，注册于 BoundaryManager，可被 BoundarySpec 按名绑定，
     承载软件命名元数据（wall/inlet…，ADR-010）与角色提示（ADR-011）。
2. **BoundaryManager 选方案 B**：内部保存 `name → BoundaryRegion 对象`。
   方案 A（纯索引集）使 ADR-010 要求的区域元数据无家可归，必然催生平行
   dict 形成双真相源；三层职责链（Region→Spec→Type，ADR-010 决策 4）
   要求 Region 作为对象存在。
3. **物理组维度分类契约**（格式无关，所有加载器继承）：
   以 `topo_dim = 网格最高单元维度`（加载时推断）为基准：
   - `group_dim == topo_dim` → `DomainRegion`（cell 成员）；
   - `group_dim == topo_dim − 1` → `BoundaryRegion`（节点成员，由边界
     单元归纳）；
   - `group_dim < topo_dim − 1` → 跳过并输出 warning 日志（确定性，
     不静默丢弃）。
   meshio `field_data` 为 `name → [tag, dim]` 单命名空间，按维度二分后
   域/边界命名不冲突。
4. **IO 永不推断 BoundaryType**：加载器的职责终点是产出命名 Region；
   数学类别只能来自用户声明的 BoundarySpec。禁止任何
   `名称 → 数学类别` 映射表（`inlet→DIRICHLET` 等）进入 IO 层——
   同名在不同问题中可为三种数学类别（ADR-010 背景论据）。
5. **Spec 按名引用**：`BoundarySpec` 以名字符串引用目标区域（不持对象
   引用），由 BoundaryManager 在 bind 时解析并校验存在性与目标类型
   （拒绝绑定 DomainRegion）；约束声明因此可先于/独立于网格存在。
6. **诞生地约束**：`core/region.py`（Region + DomainRegion）与
   `core/boundary/region.py`（BoundaryRegion）为核心层模块；io 层只
   消费、只构造，禁止重新定义。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| Manager 存纯索引集（方案 A） | 否决 | 区域元数据无家可归，双真相源漂移；违背 ADR-010 三层链 |
| BoundaryRegion / DomainRegion 各自独立、无公共基类 | 否决 | 物理组来源与槽位重复无统一类型锚点，loader 返回类型退化为 Union |
| Region 基类 + 两子类（本决策） | 采纳 | 统一物化路径与成员查询；未来 INTERFACE 跨域逻辑有公共落点 |
| 物理组全量映射为 BoundaryRegion | 否决 | 计算域误注册为边界：Spec 可绑定域、corner 查询污染 |
| IO 层内置名称→数学类别推断表 | 否决 | 物理语义僭越；同名不同义（ADR-010）；错误会随格式清单复制 |
| 低维组静默忽略 | 否决 | 静默丢数据不可审计；改为跳过 + warning（确定性留痕） |

## 影响（Consequences）

- Phase 2 模块清单在 `core/` 增加 `region.py`、`core/boundary/` 增加
  `region.py`（phase2-cae-data.md 模块树待本 ADR 评审通过后另行同步）。
- Mesh 组合更新：geometry / topology / boundary / **domain regions** /
  fields（anti god-object 边界不变，ADR-007 D3）。
- Testing 需覆盖：维度分类（域组不入边界注册表）、低维组跳过告警、
  Spec 绑定 DomainRegion 被拒、命名空间不冲突、成员集不变量
  （域⊆单元集、边界⊆节点集、域分组存在时域并=全体单元）。
- 未来格式加载器（Fluent/Abaqus/OpenFOAM）继承第 3、4 条契约，作为
  其各自 ADR 的既定前提。
- 本 ADR 不改变依赖方向与 PyG 边界（ADR-007 不变）；不引入新第三方
  依赖（meshio 见 ADR-013）。
