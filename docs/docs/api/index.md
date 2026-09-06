# API 参考

CAEGraph 处于 Phase 1（核心数据结构）：`caegraph.core` 已提供 `BaseObject`、
`Registry` 与共享枚举 `BoundaryType` / `NodeCategory`，`caegraph.utils` 已提供
`get_logger`；`Mesh`、`Field` 与数据带随 Phase 2 落地。

API 文档由此处的
[mkdocstrings](https://mkdocstrings.github.io/)
从 docstring 自动生成：

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
