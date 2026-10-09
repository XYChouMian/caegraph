# API 参考

CAEGraph 处于 Phase 2（CAE 数据管线）：Phase 1 词汇已就绪（`caegraph.core` 的 `BaseObject` / `Registry` / 共享枚举 `BoundaryType` / `NodeCategory`，`caegraph.utils` 的 `get_logger`）。CAEGraph 领域核心已落地（coding gate 1+2）——`caegraph.core` 提供 canonical 领域表示 `CAEGraph`（ADR-015/018/019：含构造期实体/关系/NodeCategory 存储）、`Field`/`FieldData`（fields belong to entities；声明 + 单次实现数据的拆分按 ADR-020——Field 为语义唯一真源，FieldData 携带 values 与 realization metadata，builder 为唯一写入路径）与 `caegraph.core.boundary` 语义区域词汇（`BoundaryRegion` / `BoundarySpec` / `BoundaryManager`，ADR-010/011/018）。topology subsystem 已落地（coding gate 3）——`caegraph.core.topology` 提供 `Mesh`（ADR-014）与 `CellType`。表示构造已落地（coding gate 4a）——`caegraph.graph.MeshRepresentationBuilder`（ADR-016/019：Mesh → CAEGraph node-graph 构造 + NodeCategory 推导 + FieldData 基数校验）。snapshot 时间组织与 single-state projection 已落地（ADR-023/024）——`caegraph.core.Snapshot`（瞬时状态组织）与 `caegraph.core.CAEGraph.project_snapshot`（返回新的 canonical 表示）；`Field.association` 为必填的 entity-family 标识（ADR-021）。后端适配已落地（coding gate 4b）——`caegraph.graph.to_pyg_data`（ADR-022：CAEGraph → PyG `Data`，frozen schema 与 fail-fast profile）。Source IO 已落地（coding gate 5）——`caegraph.io` 提供 `AbstractMeshLoader`（ADR-012 五步 source normalization 管线，`__call__(path) -> Mesh` 为稳定 public 边界）、`GmshLoader`（ADR-013：经 meshio 读取 Gmsh `.msh`，meshio 类型与异常不进入 core / public 类型契约）与 `FORMAT_REGISTRY`（复用 core `Registry` 的 name → factory 机制，首个 key 为 `"gmsh"`）。其余数据带（transforms、dataset）实现中。

API 文档由此处的 [mkdocstrings](https://mkdocstrings.github.io/) 从 docstring 自动生成：

::: caegraph
    options:
      show_source: false
      heading_level: 3

## Source IO（caegraph.io）

`AbstractMeshLoader.__call__(path) -> Mesh` 是跨格式加载的稳定 public 边界（ADR-012）：obtain source → source-specific normalization → canonical build（ADR-014）→ validate → return。protected 钩子是 adapter 实现细节，数量与名称不冻结，不属于公共契约。`GmshLoader` 在读取时才懒加载 meshio（ADR-013）；meshio 类型仅存在于 `caegraph.io` 内部，读取失败在 IO 边界收敛为稳定的 `ValueError`。

使用语义要点：`.msh` source 可合法包含跨维 blocks——`dim == topo_dim` 的实体进入 canonical cell space，`dim == topo_dim - 1` 的实体是 facet 候选，更低维实体被诊断并排除；`topo_dim` 取自最高受支持的 source-cell 维度，绝不从 group 反推。Gmsh physical group（`meshio.field_data` 的 name↔tag 映射）是 source 命名分组，与 CAEGraph 的 `FieldData`（物理场 realization）完全无关，loader 不会创建 `FieldData`：domain group 以 global cell IDs 记入 `Mesh.domain_groups`；boundary/interface group 声明 canonical facet 子集并以 global facet IDs 记入 `Mesh.metadata`（供下游 region 构造），loader 不推断 `BoundaryType`、不产生 `BoundarySpec` / Condition。complete_coverage / complete_partition 保持 caller-declared（ADR-014 8b——暂无 API，loader 不代为声明）。

::: caegraph.io
    options:
      show_source: false
      heading_level: 3

顶层模块（见架构规范）：

- `caegraph.core`
- `caegraph.geometry`
- `caegraph.io`
- `caegraph.graph`
- `caegraph.transforms`
- `caegraph.dataset`
- `caegraph.physics`
- `caegraph.models`
- `caegraph.assimilation`
- `caegraph.workflow`
- `caegraph.inference`
- `caegraph.visualization`
- `caegraph.utils`
