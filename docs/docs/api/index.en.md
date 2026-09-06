# API Reference

CAEGraph is in Phase 2 (CAE Data Pipeline): the Phase 1 vocabulary is in
place (`BaseObject` / `Registry` / shared enums in `caegraph.core`,
`get_logger` in `caegraph.utils`); `Mesh` / `Field` and the data band are
being implemented.

API documentation is generated automatically from docstrings via
[mkdocstrings](https://mkdocstrings.github.io/):

::: caegraph
    options:
      show_source: false
      heading_level: 3

Top-level modules (see the architecture specification):

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
