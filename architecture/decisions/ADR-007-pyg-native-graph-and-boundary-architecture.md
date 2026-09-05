# ADR-007: PyG 原生 Graph 子类与边界条件两层架构

- 编号：ADR-007
- 标题：`caegraph.Graph` 继承 PyG `Data`（薄子类 + 护栏）；边界条件按"几何 / 计算"两层分层
- 日期：2026-09-05
- 状态：accepted
- 关联：Phase 1（core 共享枚举）、Phase 2（data 层实现）、Design UML
  `class_diagram.puml`（caegraph.core / caegraph.data / caegraph.models）、
  前身项目 CFD-paradigm（本地未入库，`temp/` 已 gitignore）

## 背景（Context）

CAEGraph 的前身 CFD-paradigm 基于 igraph + torch，留下两类资产与教训：

- `MeshGraph` 继承 `igraph.Graph`：C 后端重状态类、逐顶点属性存储
  （`vs[i]["pos"]`）、为让 `ig.plot()` 工作需要 `__class__` 欺骗 hack——
  继承外部图库的代价已被实践验证。
- 边界条件形成了成熟的两层模式：几何层 `BoundarySpec` /
  `BoundaryManager`（物理组注册、spec 绑定、corner 检测）→ 编译 →
  计算层 `BoundaryOperator(nn.Module)`（register_buffer、加权 lerp 混合、
  `apply(y, t)`）。

转向 PyG 后需要决定：

1. `caegraph.Graph` 与 `torch_geometric.data.Data` 的集成方式；
2. 边界条件与节点分类在依赖分层（utils ← core ← data ← physics ←
   models）中的归属。

## 决策（Decision）

1. **Graph = `torch_geometric.data.Data` 的薄子类**，附四条护栏：
   - 张量-only 纪律：Graph 只存张量与基元；区域名表留在 Mesh 侧，
     富对象（BC spec 等）不进 Graph；
   - 对 caegraph 标准属性（pos / x / edge_index / edge_attr /
     node_category / 边界掩码）显式声明类型注解；
   - 实现 `__inc__` / `__cat_dim__` 钩子，保证自定义属性参与
     Batch / collate 时语义正确；
   - 子类保持"薄"（类型化访问器 + 构造校验 + 批处理钩子），
     不承载业务逻辑。
2. **Mesh 用自有 numpy 结构**（nodes / elements / regions / fields +
   BoundaryManager 聚合），不继承任何图库。
3. **边界条件两层架构**：
   - data 层（几何 + 用户意图）：`BoundaryType`（core 枚举）、
     `BoundarySpec`（dataclass）、`BoundaryManager`（区域注册与 spec
     绑定）、`FieldFunction`（ABC：`__call__(t, pos) -> (B, N, C)`，
     含形状自验证）；
   - models 层（计算）：`BoundaryOperator(nn.Module)`（buffer 管理、
     加权 lerp、`apply(y, t)`）与编译函数，消费 data 层 manager 的
     产物；
   - 依赖方向不变：data → core；models → data。
4. **NodeCategory 语义**：interior / boundary / corner 三分类；
   corner = 多边界区域归属节点（前身 `get_corner_vertices` 的升级）；
   在 Graph 上以张量掩码 / 索引表示。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| Graph 继承 `Data`（薄子类 + 护栏） | 采纳 | PyG 官方同款模式（`HeteroData` / `TemporalData` 先例）；DataLoader / Batch / 生态零成本；`Data` 是纯 Python 字典容器、整图存张量，与 igraph 的逐点存储本质不同 |
| 组合包装（自有类 + `to_data()` 导出） | 否决 | 训练环节转换税；包装与 Data 影子双源真相必然漂移；"摆脱 PyG 依赖"是伪收益（属性本来就是 torch 张量） |
| 裸 Data + 命名约定（不定义 Graph 类） | 否决 | 丢失 BaseObject 契约（identity / metadata / validation），与设计 UML 六抽象冲突 |
| 继承 igraph.Graph（前身方案） | 否决 | C 后端重状态、逐顶点存储、可视化 hack；已被 CFD-paradigm 实践证伪 |

## 影响（Consequences）

- 正面：训练管线零转换成本；边界条件继承已验证的两层设计；
  NodeCategory 使 interior / boundary / corner 语义成为一等公民。
- 代价：mypy 对 `Data` 动态存储有摩擦（护栏 b 缓解）；对 PyG 大版本
  有耦合（`torch-geometric>=2.5,<3.0` 上界约束）。
- 退出条件：若 PyG 3.0 的破坏性变更使子类维护成本失控，退守组合模式；
  "薄子类"约束保证迁移面最小。
- 后续：Phase 2 按 `phase2-cae-data.md` 实现 data 层；`BoundaryType` /
  `NodeCategory` 随 Phase 1 落入 `caegraph.core.enums`；Generated UML
  建立后比对 Design / Generated 一致性。
