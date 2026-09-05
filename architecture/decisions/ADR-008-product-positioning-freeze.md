# ADR-008: 产品定位冻结（Product Positioning Freeze）

- 编号：ADR-008
- 标题：冻结 CAEGraph 为 "CAE 仿真 → Physics AI 工作流框架"；四项核心需求与边界
- 日期：2026-09-05
- 状态：accepted
- 关联：ADR-007（图抽象与后端集成，本 ADR 的技术推论）、Phase 1–4、
  Design UML、ARCHITECTURE.md §1/§7

## 背景（Context）

CAEGraph 的定位经历四轮演进（数据基础设施 ⇄ solver 框架 ⇄ 图学习框架 ⇄
工作流框架），每轮摇摆的根源都是**定位未冻结**而非技术分歧——每种定位
各自蕴含不同的技术答案。需求级输入（四项核心功能）现已明确，本 ADR 将
定位、边界与纪律一次性冻结，终结反复推倒。

## 需求（Requirements — 四项核心功能）

- **R1**：CAE 软件计算数据方便地转为 GNN 训练数据——网格解析、拓扑构建、
  节点/边特征工程、物理场映射、边界编码、图构建。
- **R2**：方便 GNN 训练流程，且该流程**适配** CAE 数据特性（多物理量
  节点/边特征、时间步、工况、边界条件、物理约束）——非重造训练框架。
- **R3**：任一网格 + 经本流程预训练的 GNN → 生成数据（**神经仿真**，
  对标传统 CAE 工作流 Geometry→Mesh→BC→Solver→Solution 的 AI 对应物）。
- **R4**（附加）：以实验数据修补 mesh+GNN 生成的数据（**物理信息数据
  同化**，如 PIV 稀疏测量修正稠密预测）。

## 决策（Decision）

**一句话定位**：

> CAEGraph 连接 CAE 仿真与 Physics AI，提供 **CAE 数据 → 图表示 → GNN
> 训练 → 新网格神经仿真 → 实验数据同化** 的完整工作流。
>
> CAEGraph bridges CAE simulation and physics AI through a
> **CAE → GNN → AI workflow**: converting CAE data into graph
> representations, enabling GNN training on engineering problems, running
> neural simulation on new meshes with pretrained models, and correcting
> predictions with experimental observations.

措辞纪律：不自称"训练框架"（避免 Lightning/PhysicsNeMo 误读），不自称
"数据基础设施"（避免 meshio 误读）；与 PyG 的关系是 **extends the PyG
ecosystem for computational engineering**。

**职责矩阵**：

| 对象 | 身份 | 规则 |
| --- | --- | --- |
| Mesh / Field / Boundary | 工程真源（domain truth） | 框架无关，torch-only，永不依赖 PyG |
| `Graph(torch_geometric.data.Data)` | 神经表示（neural representation） | PyG 原生；只加 CAE 字段与校验，不加操作 |
| `models` 包 | Model 接口 + CAE-aware 公用设施 | **禁止 GNN zoo**：MeshGraphNet/GNO/Transformer 等具体模型 → examples 或外部项目 |
| `workflow` 包 | 训练公用设施（loss 组装、CAE 批处理适配、约束装配） | 无 fit 循环，不替代 Lightning |
| `inference` 包 | 神经仿真壳（mesh→graph→model→场重构→导出；rollout 循环壳） | 数值格式（RK 等）属模型侧，库永不实现 |
| `assimilation` 包 | 观测/修正算子（模型能力） | 双模式：训练约束（workflow 消费）+ 推理后修正（inference 消费） |

**Non-goals**：不做网格生成器；不做 CFD/FEA solver，不实现数值时间推进
格式；不做训练框架（无 Trainer.fit / optimizer / 分布式引擎）；不重造
PyG；不做 GNN 模型动物园。

**需求 ↔ Phase 映射**：R1→Phase 2；R2+R4→Phase 3；R3→Phase 4
（含 VTK 写回闭环与 release）。

**生态位**：与 meshio/PyVista（纯数据层）、PyTorch Lightning/PhysicsNeMo
（训练系统）、DeepXDE（PINN 求解器）互补而非竞争；独占价值在三问——
CAE 如何变成图、物理信息如何进入 GNN、PyG 如何适配复杂工程问题。

**冻结纪律（Freeze Discipline）**：

> **CAEGraph positioning is frozen (ADR-008).** 未经新 ADR，任何 Agent
> 不得引入：solver 抽象、trainer 抽象、替代图后端层。
> "Graph 是不是 Data""要不要 Trainer""要不要 Solver"之辩就此关闭。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| CAE 数据基础设施（meshio 生态位） | 否决 | 无法承载 R2/R3/R4；被 R1 之外的诉求证伪 |
| CAE 训练框架（Lightning 生态位） | 否决 | 重造 PyTorch 生态；R2 只需"适配"不需"替代" |
| 物理 GNN 求解器（DiNN 生态位） | 否决 | 绑定单一范式；R3 需要的是工作流壳不是求解器 |
| **CAE→GNN→AI 工作流框架** | 采纳 | 四项需求全覆盖；与 PyG extends 关系自洽 |

## 影响（Consequences）

- 正面：定位、包结构、抽象体系一次性稳定；Agent 分工与 Phase 路线获得
  需求骨架；创新点明确。
- 代价：assimilation / inference 的"壳 vs 数值"边界需在 Phase 3/4 评审中
  持续把关；examples 通道（具体模型栖息地）需建设。
- 后续：ADR-007 按本 ADR 终版化；架构文档、骨架、测试按终版 DAG 同步；
  后续结构决策自 ADR-009 起记录。
