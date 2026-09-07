# Phase 2 — CAE Data Pipeline

Status: In progress

Goal: implement **R1** — the CAE → GNN data band (ADR-007/008): the domain-core objects plus geometry / io / graph / transforms / dataset.

## New modules (planned)

```
src/caegraph/core/          # domain objects join the Phase 1 vocabulary
├── celltype.py             # CellType: vocabulary, explicit stable integer codes,
│                           #   dim/node_count, CAEGraph local-node convention +
│                           #   codim-1 face templates (ADR-014; frozen with impl)
├── mesh.py                 # Mesh canonical representation (ADR-014): nodes (n,3),
│                           #   cells CSR, explicit facets CSR + facet_cells,
│                           #   domain groups (plain data), fields; structure frozen
├── field.py                # Field: named field data (unit, timestep, association)
└── boundary/               # mesh-internal boundary vocabulary
    ├── region.py           # BoundaryRegion: named codim-1 facet region
    │                       #   (exterior boundary / internal interface)
    ├── manager.py          # BoundaryManager: semantic grouping + spec binding
    └── spec.py             # BoundarySpec (slot-coherence validation, ADR-011)
                            #   function.py (FieldFunction) is deferred to the
                            #   BC-declaration slice

src/caegraph/geometry/
├── metrics.py              # edge features: distance/direction/normal/quality
└── interpolation.py        # field interpolation onto mesh nodes

src/caegraph/io/
├── base.py                 # AbstractMeshLoader: __call__ pipeline (ADR-012);
│                           #   protected hooks are implementation details
├── registry.py             # format registry on the core registry
├── gmsh.py                 # first adapter: gmsh source named groups via meshio
└── vtk_writer.py           # write-back into the ParaView ecosystem

src/caegraph/graph/         # PyG-native neural-representation layer
├── graph.py                # Graph(torch_geometric.data.Data): CAE fields
│                           #   + validate(), never operations (ADR-007 D1)
└── builder.py              # node graph / cell graph construction

src/caegraph/transforms/    # BC application lives HERE, not on Graph
├── geometry.py             # coordinate / feature normalization
├── feature.py              # CAE feature engineering
└── physics.py              # boundary-condition encoding:
                            #   data.x[data.inlet_mask] = value pattern

src/caegraph/dataset/
└── dataset.py              # CAEDataset(PyG Dataset): collections, splits
```

## Planned public APIs

- `Mesh` / `Field` / `CellType` / `BoundaryRegion` — domain truth (ADR-007 D3/D6, ADR-014)
- `BoundarySpec` / `BoundaryManager` — boundary vocabulary (ADR-010/011); `FieldFunction` deferred
- `AbstractMeshLoader` + gmsh adapter — loading pipeline (ADR-012); meshio provisional engine (ADR-013)
- `GraphBuilder.build(mesh, *, view="node" | "cell")` →`Graph(torch_geometric.data.Data)`; Mesh stays unaware of graph
- Geometry / feature / physics transforms (PyG transform protocol)
- `CAEDataset`; VTK writer

## Validation focus (Validation Agent, mandatory)

- topology preservation (node/edge counts, connectivity)
- source named group mapping: source groups (e.g. Gmsh physical groups) → domain groups / BoundaryRegion (global facet IDs), classified by dimension per ADR-012; NodeCategory semantics (interior / boundary / corner; corner = multi-region membership)
- Graph schema conformance: CAE fields present, `validate()` enforced
- PyG boundary: `core`/`geometry`/`io` never import `torch_geometric`
- VTK round-trip: mesh → graph → VTK → re-read. Phase 2 owns and implements the writer; Phase 4 reuses it for predicted-field export.

## Rules

- Loaders register via the core registry; no loader hard-imports another.
- Synthetic meshes only in tests (Testing Skill CAE rules).
- Real solver formats (Fluent, Abaqus, OpenFOAM…) enter here — each new format is a feature request routed through PM (Architecture review first).
- Registry stays a name→factory mapping (Phase 1 contract: callable check only — Python type erasure makes runtime generic checks a non-goal). Runtime type enforcement (`Registry(kind, base_class=...)` + `issubclass`) is a recorded future option (Design UML Registry note); adopt it only if Phase 2 loader wiring needs it, decided explicitly.
- Loading and Mesh structure follow ADR-012 (source normalization → canonical build) and ADR-014 (canonical Mesh data model); meshio is the provisional IO engine (ADR-013).
- Resolved design question (ADR-011): the ADR-010 "未来演进" re-evaluation is complete — keep the single seven-value `BoundaryType` through Phase 2. `BoundarySpec` must enforce per-type slot-coherence validation (`paired_region` required for PERIODIC; value slots meaningful only for constraint-valued types); refined Phase 3 re-trigger conditions for a possible orthogonal role × constraint split are recorded in ADR-011.

## Depends on

Phase 1 (core vocabulary: BaseObject, registry, enums).
