# API 参考

CAEGraph 处于 Phase 2（CAE 数据管线）：Phase 1 词汇已就绪（`caegraph.core` 的 `BaseObject` / `Registry` / 共享枚举 `BoundaryType` / `NodeCategory`，`caegraph.utils` 的 `get_logger`）。架构已采纳 ADR-015——CAEGraph 为顶层 canonical 领域表示，Mesh 归位 topology subsystem；topology 词汇 `CellType` 已落地，CAEGraph core 与数据带（loaders、representation builder、DataGraph adapter、transforms、dataset）实现中。

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
