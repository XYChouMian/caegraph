# ADR-007: 图抽象与后端集成（Graph abstraction and backend integration）

- 编号：ADR-007
- 标题：CAEGraph 拥有域级图抽象层；PyG 等框架以后端集成方式接入
- 日期：2026-09-05
- 状态：accepted
- 关联：Phase 1（core 词汇）、Phase 2（桥接带）、Phase 3（physics/models）、
  Design UML `class_diagram.puml`、前身项目 CFD-paradigm 与两份重构
  研究文档（本地未入库）

## 背景（Context）

CAEGraph 的定位经历了根本性澄清：从早期受前身 DiNN 思路影响的
"物理 GNN 求解器框架"，重新定位为 **CAE ⇄ GNN 桥接数据基础设施**——
将 CAE 软件中的网格、场变量与物理信息转换为统一图表示，为 GNN /
Neural Operator / Physics-informed AI 提供标准数据接口。

由此产生本 ADR 的核心问题：**CAEGraph 是否拥有自己的图抽象层？**
Graph 的身份是"PyG 训练样本"，还是"CAEGraph 的域级中间表示、
PyG 只是其后端之一"？这一裁决决定包结构、依赖方向与项目生态位。

## 决策（Decision）

**核心决策：CAEGraph 拥有自己的域级图抽象层。**

**D1. Graph = domain-level graph abstraction with tensor storage**

- Graph 表达 CAE 域语义（节点、边、NodeCategory、边界区域），
  张量存储是实现细节而非身份；
- 表述纪律：不使用"torch 张量基座""PyG 兼容图"等措辞，防止未来
  被诱导直接调用 PyG API；
- 自有 Graph 只做哑容器：标准属性（pos / edge_index / node_category /
  边界掩码 / 区域索引）+ schema 校验；**禁止**实现 collate、message
  passing、transforms 框架、图算法——这些属于后端框架（防重造 PyG）。

**D2. 后端圈禁（PyG confinement）**

- `import torch_geometric` 只允许出现在 `caegraph.integrations.pyg` 内；
- core / geometry / io / graph / dataset 仅依赖 torch，永不 import PyG；
- 适配层形态：`to_pyg()` 转换函数 + PyG 数据集（`__getitem__` 直接
  产出 `torch_geometric.data.Data`），不建平行 PyGGraph 类层次；
- 转换税由数据集层吸收（一次性转换 + 缓存）；
- 未来 DGL / JAX 后端按 `integrations/<backend>` 平行扩展，不预建。

**D3. 域核包（domain core）**

- `caegraph.core` = BaseObject + Mesh + Graph + Field + registry +
  共享枚举（BoundaryType / NodeCategory）；
- core 依赖 torch（张量存储），永不依赖 PyG；
- Mesh 反 God-Object：以组合子结构组织（geometry / topology /
  boundary / fields）；边界条件几何层（BoundarySpec / BoundaryManager /
  FieldFunction）作为 Mesh 内部域词汇。

**D4. NodeCategory 语义**：interior / boundary / corner 三分类；
corner = 多边界区域归属节点（前身 `get_corner_vertices` 的升级）；
以张量掩码 / 索引表示。

**D5. 定位裁决：纯桥接层**

- solver 侧组件（RK 时间积分器、PDE rollout 系统、Monitor 体系）
  排除出库，属用户应用层（至多 Phase 4 示例代码）；
- 首个 loader：gmsh（物理组 → 边界语义映射完整，前身已验证）；
- 写回闭环纳入愿景：VTK writer（GNN 结果回 ParaView 生态）。

**D6. Field 第七抽象**：`Field(name, values, unit, timestep, node/cell
归属)`——场变量是一等公民；graph 特征装配（x 的构造）由此成为
显式特征工程，而非无语义的属性堆砌。

**D7. 包架构与依赖 DAG**

```
utils ← core ← {geometry, io} ← graph ← integrations ← dataset
      ← physics ← models ← visualization
```

- 跳层依赖允许，反向禁止；同层互依禁止（geometry 与 io 互不依赖）；
- graph（builder / transform）消费 geometry（边特征）；integrations
  消费 graph；dataset 消费 integrations（PyG 数据集）与 graph（中性
  集合）；physics 依赖 core；models 消费 dataset / integrations /
  physics；visualization 居顶。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 域级图抽象 + 后端集成（本决策） | 采纳 | 与基础设施定位一致；域语义集中；PyG 圈禁使 core 测试可脱离 PyG；多后端扇出路径清晰 |
| `Graph(torch_geometric.data.Data)` 薄子类 | 否决 | 身份绑定为"PyG 样本"；mypy 对 Data 动态存储有摩擦；BaseObject 契约需多继承 mixin；数据集层吸收转换税后，其人体工学优势不再关键 |
| 不定义自有 Graph（裸 PyG Data + 命名约定） | 否决 | 丢失域语义与 BaseObject 契约；PyG API 渗透所有层 |
| 自有抽象 + 平行 PyGGraph 类层次 | 否决 | 重造 PyG 的风险；函数 + 数据集形态的适配层已足够 |
| 继承 igraph.Graph（前身方案） | 否决 | C 后端重状态类、逐顶点属性存储、可视化 hack，已被实践证伪 |
| solver 侧组件进库（RK / GraphPDESystem / Monitor） | 否决 | 违反"非求解器"non-goal；绑定单一训练范式，排斥 surrogate / FEM / PINN 多元用户 |

## 影响（Consequences）

- 正面：框架中立（PyG 圈禁于 integrations）；域语义集中于 core；
  Mesh → Graph → 多后端扇出清晰；写回闭环完整；core / geometry /
  io / graph / dataset 可在无 PyG 环境下测试。
- 代价：适配层维护成本；单图推理路径多一次 `to_pyg()`；包数量增多
  带来治理成本。
- 后续：Phase 2 实现桥接带（core 域对象 + 服务带）；Phase 3 落地
  physics 与可组合组件；后续结构决策自 ADR-008 起记录。
