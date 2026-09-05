# API 参考

CAEGraph 处于 Phase 1（核心数据结构）：`BaseObject`、注册机制与共享类型正在
实现，核心公共 API 尚未发布。

模块落地后，将由此处的
[mkdocstrings](https://mkdocstrings.github.io/)
自动生成文档，例如：

::: caegraph
    options:
      show_source: false
      heading_level: 3

规划中的顶层模块（见架构规范）：

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

兼容说明：旧的 `caegraph.data` 空命名空间暂时保留并发出弃用警告；新代码应使用
上述职责明确的包。该兼容命名空间不会早于 0.3.0 移除。
