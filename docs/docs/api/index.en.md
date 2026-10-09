# API Reference

CAEGraph is in Phase 2 (CAE Data Pipeline): the Phase 1 vocabulary is in place (`BaseObject` / `Registry` / shared enums in `caegraph.core`, `get_logger` in `caegraph.utils`). The CAEGraph domain core has landed (coding gates 1+2) — `caegraph.core` provides the canonical domain representation `CAEGraph` (ADR-015/018/019, including construction-time entity/relation/NodeCategory storage), `Field`/`FieldData` (fields belong to entities; the declaration / realization-data split follows ADR-020 — Field is the single authoritative semantics source, FieldData carries values and realization metadata, with the representation builder as the only write path) and the `caegraph.core.boundary` semantic-region vocabulary (`BoundaryRegion` / `BoundarySpec` / `BoundaryManager`, ADR-010/011/018). The topology subsystem has landed (coding gate 3) — `caegraph.core.topology` provides `Mesh` (ADR-014) and `CellType`. Representation construction has landed (coding gate 4a) — `caegraph.graph.MeshRepresentationBuilder` (ADR-016/019: Mesh → CAEGraph node-graph construction with NodeCategory derivation and FieldData cardinality validation). The snapshot temporal organization and single-state projection have landed (ADR-023/024) — `caegraph.core.Snapshot` (instantaneous-state organization) and `caegraph.core.CAEGraph.project_snapshot` (returning a new canonical representation); `Field.association` is a required entity-family identifier (ADR-021). Backend adaptation has landed (coding gate 4b) — `caegraph.graph.to_pyg_data` (ADR-022: CAEGraph → PyG `Data` with the frozen schema and a fail-fast profile). Source IO has landed (coding gate 5) — `caegraph.io` provides `AbstractMeshLoader` (the ADR-012 five-step source-normalization pipeline with `__call__(path) -> Mesh` as the stable public boundary), `GmshLoader` (ADR-013: reads Gmsh `.msh` through meshio — meshio types and exceptions never enter the core / public type contract) and `FORMAT_REGISTRY` (reusing the core `Registry` name → factory mechanism, first key `"gmsh"`). The remaining data band (transforms, dataset) is being implemented.

API documentation is generated automatically from docstrings via [mkdocstrings](https://mkdocstrings.github.io/):

::: caegraph
    options:
      show_source: false
      heading_level: 3

## Source IO (caegraph.io)

`AbstractMeshLoader.__call__(path) -> Mesh` is the stable cross-format loading boundary (ADR-012): obtain the source → source-specific normalization → canonical build (ADR-014) → validate → return. The protected hooks are adapter implementation details — their count and names are not frozen and are not part of the public contract. `GmshLoader` imports meshio lazily at read time (ADR-013); meshio types live only inside `caegraph.io`, and read failures collapse into a single stable `ValueError` at the io boundary.

Usage semantics: a `.msh` source may legally mix dimensions across blocks — entities with `dim == topo_dim` enter the canonical cell space, `dim == topo_dim - 1` entities are facet candidates, and lower-dimensional entities are diagnosed and excluded; `topo_dim` is the highest supported source-cell dimension, never derived from groups. Gmsh physical groups (the `meshio.field_data` name↔tag mapping) are named *source* groups and are entirely unrelated to CAEGraph `FieldData` (physical realizations) — the loader never creates `FieldData`: domain groups are recorded with global cell IDs in `Mesh.domain_groups`; boundary/interface groups declare the canonical facet subset and are recorded with global facet IDs in `Mesh.metadata` (preserved for downstream region construction); the loader never infers `BoundaryType` and never produces `BoundarySpec` / conditions. complete_coverage / complete_partition remain caller-declared (ADR-014 8b — no API yet, never assumed by the loader).

::: caegraph.io
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
