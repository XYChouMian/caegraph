# API 参考

CAEGraph 处于 Phase 2（CAE 数据管线）：Phase 1 词汇已就绪（`caegraph.core` 的 `BaseObject` / `Registry` / 共享枚举 `BoundaryType` / `NodeCategory`，`caegraph.utils` 的 `get_logger`）。CAEGraph 领域核心已落地（coding gate 1+2）——`caegraph.core` 提供 canonical 领域表示 `CAEGraph`（ADR-015/018）、`Field`（fields belong to entities）与 `caegraph.core.boundary` 语义区域词汇（`BoundaryRegion` / `BoundarySpec` / `BoundaryManager`，ADR-010/011/018）。topology subsystem 已落地（coding gate 3）——`caegraph.core.topology` 提供 `Mesh`（canonical cell-based 拓扑模型：cells/facets 双 CSR、winding-free 显式 facets、validated `facet_cells` 邻接、domain groups；ADR-014）与 `CellType`。数据带（loaders、representation builder、backend adapter、transforms、dataset）实现中。

API 文档由此处的 [mkdocstrings](https://mkdocstrings.github.io/) 从 docstring 自动生成：

::: caegraph
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
