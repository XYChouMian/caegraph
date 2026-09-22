# API Reference

CAEGraph is in Phase 2 (CAE Data Pipeline): the Phase 1 vocabulary is in place (`BaseObject` / `Registry` / shared enums in `caegraph.core`, `get_logger` in `caegraph.utils`). The CAEGraph domain core has landed (coding gates 1+2) — `caegraph.core` provides the canonical domain representation `CAEGraph` (ADR-015/018/019, including construction-time entity/relation/NodeCategory storage), `Field` (fields belong to entities) and the `caegraph.core.boundary` semantic-region vocabulary (`BoundaryRegion` / `BoundarySpec` / `BoundaryManager`, ADR-010/011/018). The topology subsystem has landed (coding gate 3) — `caegraph.core.topology` provides `Mesh` (ADR-014) and `CellType`. Representation construction has landed (coding gate 4a) — `caegraph.graph.MeshRepresentationBuilder` (ADR-016/019: Mesh → CAEGraph node-graph construction with NodeCategory derivation and field length validation). The remaining data band (loaders, backend adapter, transforms, dataset) is being implemented.

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
