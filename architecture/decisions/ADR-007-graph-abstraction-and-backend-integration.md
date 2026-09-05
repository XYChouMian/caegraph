# ADR-007: 图抽象与后端集成（Graph abstraction and backend integration）

- 编号：ADR-007
- 标题：Graph 是 PyG 原生的神经表示层；工程真源（Mesh/Field/Boundary）框架无关
- 日期：2026-09-05（历经四轮定位演进后终版化，上位依据 ADR-008）
- 状态：accepted
- 关联：ADR-008（定位冻结）、Phase 2/3/4、Design UML `class_diagram.puml`、
  前身项目 CFD-paradigm 与多份重构研究文档（本地未入库）

## 背景（Context）

CAEGraph 的定位经历四轮演进（详见 ADR-008），本 ADR 曾随之两度改向——
根源是定位未冻结而非技术分歧。ADR-008 冻结定位后，本 ADR 作为其技术
推论终版化。

核心问题：**CAEGraph 是否拥有自己的图抽象层？** 终版答案分域：

- **工程真源**（Mesh / Field / Boundary）自有且框架无关（torch-only）；
- **学习图表示**（Graph）是 PyG 原生的域扩展（domain extension）。

## 决策（Decision）

**D1. Graph = PyG-compatible domain extension**（ADR-008 推论）

- `caegraph.graph.Graph` 继承 `torch_geometric.data.Data`：PyG 运行时
  生态（Transform / Dataset / DataLoader / Batch / MessagePassing）直接可用；
- 增加且仅增加：CAE 域字段（node_category、边界掩码、区域索引等）+
  `validate()` 契约；表述纪律：Graph 是 **neural representation**，
  不是 engineering truth source；
- 正确绑定 vs 错误绑定：✅ 持有拓扑/几何张量/BC 掩码/场/校验；
  ❌ 任何 solver 行为（`solve_pressure` 式方法）。BC 的训练时施加以
  PyG Transform 形式存在于 transforms 层，不驻留 Graph 方法。

**D2. 工程真源纯净性**

- core（Mesh / Field / boundary 词汇 / registry / enums）、geometry、io
  永不 import PyG；自 `caegraph.graph` 起为 PyG 原生层。

**D3. 域核包**：core = BaseObject + Mesh + Field + registry + enums
（torch-only）；Mesh 反 God-Object 组合（geometry / topology / boundary /
fields）；边界几何词汇（BoundarySpec / BoundaryManager / FieldFunction）
为 Mesh 内部结构。Graph 落位 `caegraph.graph`（神经表示层），不在 core。

**D4. NodeCategory**：interior / boundary / corner 三分类；corner = 多
边界区域归属节点；以张量掩码/索引表示。

**D5. 定位边界（ADR-008 落实）**

- inference 壳（rollout 循环、场重构、导出编排）入库（R3）；
  **数值推进格式（RK 等）属模型侧，永不入库**；
- assimilation（观测/修正算子）入库为模型能力，Phase 3（R4）；
- Monitor / 训练循环 / solver 编排不入库；
- gmsh 首发 loader；VTK 写回闭环。

**D6. 六抽象**（ADR-008 冻结、ADR-009 明确继承与命名）：BaseObject / Mesh /
Graph / Field / CAEDataset / Model（Trainer 出局）。`Field(name, values, unit, timestep,
node/cell 归属)` 是工程真源的一等公民，graph 特征装配由此成为显式
特征工程。

**D7. 包架构与依赖 DAG（终版）**

```
utils ← core ← {geometry, io} ← graph ← transforms ← dataset
       ← physics ← {models, assimilation} ← {workflow, inference} ← visualization
```

- 跳层依赖允许，反向禁止；同层互依禁止（兄弟层互不依赖）；
- BC 双层模式：mesh 级 BoundaryManager（几何真源）+ transforms 级
  BC Transform（训练时施加，`data.x[data.inlet_mask] = value` 模式）；
- assimilation 双模式消费：workflow（训练约束，观测 loss 项）与
  inference（推理后修正，稀疏测量修正稠密预测）。

**演进史（四轮，驱动因素 = 定位澄清）**：

| 轮次 | 决策 | 定位驱动 | 结局 |
| --- | --- | --- | --- |
| 1 | `Graph(Data)` 薄子类 | 隐含 solver 定位 | 被轮 2 取代 |
| 2 | 自有 Graph + integrations 适配层 | "纯数据基础设施" + 防重造 PyG | 被 Transform 生态税与语义生命周期错位证伪 |
| 3 | A-enhanced 分层（Graph(Data) 居 graph 层，core 纯净） | "图学习框架" | 与轮 1 同向，分层精化保留 |
| 4 | **终版 = 轮 1+3 合并** | "CAE→GNN→AI 工作流框架"（ADR-008） | 冻结 |

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| Graph(Data) 域扩展 + 真源分层（本决策） | 采纳 | PyG 生态零税；真源纯净；与 ADR-008 定位自洽 |
| 自有 Graph + adapter（integrations） | 否决 | Transform/Dataset/Batch 需重造（违反防重造护栏）；自有 Graph 沦为瞬态仪式品 |
| 不定义 Graph（裸 Data + 约定） | 否决 | 丢失域语义与校验契约 |
| 自有抽象 + 平行 PyGGraph 类层次 | 否决 | 重造 PyG 风险 |
| 继承 igraph.Graph（前身方案） | 否决 | C 后端重状态、逐顶点存储、可视化 hack，已被实践证伪 |
| solver/trainer 组件入库 | 否决 | 见 ADR-008 non-goals；数值格式属模型侧 |

## 影响（Consequences）

- 正面：训练与推理路径直接进入 PyG 生态；真源（core/geometry/io）可在
  无 PyG 环境测试；R1–R4 四需求均有明确结构落点。
- 代价：mypy 对 Data 动态存储有摩擦（显式注解缓解）；PyG 大版本耦合
  （`torch-geometric>=2.5,<3.0` 上界约束）。
- 后续：Phase 2 实现桥接带（core 域对象 + geometry/io/graph/transforms/
  dataset）；Phase 3 落地 physics / models / assimilation / workflow；
  Phase 4 落地 inference 与 VTK 写回；转换与继承契约见 ADR-009，后续
  结构决策自 ADR-010 起记录。
