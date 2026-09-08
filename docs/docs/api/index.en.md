# API Reference

CAEGraph is in Phase 2 (CAE Data Pipeline): the Phase 1 vocabulary is in place (`BaseObject` / `Registry` / shared enums in `caegraph.core`, `get_logger` in `caegraph.utils`). The architecture has adopted ADR-015 — CAEGraph is the top-level canonical domain representation and Mesh is repositioned as a topology subsystem; the topology vocabulary `CellType` has landed, while the CAEGraph core and the data band (loaders, representation builder, backend adapter, transforms, dataset) are being implemented.

API documentation is generated automatically from docstrings via [mkdocstrings](https://mkdocstrings.github.io/):

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
