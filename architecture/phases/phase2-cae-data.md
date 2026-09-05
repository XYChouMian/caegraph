# Phase 2 — CAE Data Pipeline

Status: Planned

Goal: implement **R1** — the CAE → GNN data band (ADR-007/008): the
domain-core objects plus geometry / io / graph / transforms / dataset.

## New modules (planned)

```
src/caegraph/core/          # domain objects join the Phase 1 vocabulary
├── mesh.py                 # Mesh + composition (geometry/topology/boundary/fields)
├── field.py                # Field: named field data (unit, timestep, association)
└── boundary/               # mesh-internal boundary vocabulary
    ├── spec.py             # BoundarySpec
    ├── manager.py          # BoundaryManager
    └── function.py         # FieldFunction

src/caegraph/geometry/
├── metrics.py              # edge features: distance/direction/normal/quality
└── interpolation.py        # field interpolation onto mesh nodes

src/caegraph/io/
├── registry.py             # format registry on the core registry
├── gmsh.py                 # first loader: physical groups -> boundary regions
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

- `Mesh` / `Field` — domain truth (ADR-007 D3/D6)
- `GraphBuilder.build(mesh, *, view="node" | "cell")` →
  `Graph(torch_geometric.data.Data)`; Mesh stays unaware of graph
- `BoundarySpec` / `BoundaryManager` / `FieldFunction`
- Geometry / feature / physics transforms (PyG transform protocol)
- `CAEDataset`; gmsh loader; VTK writer

## Validation focus (Validation Agent, mandatory)

- topology preservation (node/edge counts, connectivity)
- boundary-condition mapping: gmsh physical groups → regions /
  NodeCategory semantics (interior / boundary / corner;
  corner = multi-region membership)
- Graph schema conformance: CAE fields present, `validate()` enforced
- PyG boundary: `core`/`geometry`/`io` never import `torch_geometric`
- VTK round-trip: mesh → graph → VTK → re-read. Phase 2 owns and implements
  the writer; Phase 4 reuses it for predicted-field export.

## Rules

- Loaders register via the core registry; no loader hard-imports another.
- Synthetic meshes only in tests (Testing Skill CAE rules).
- Real solver formats (Fluent, Abaqus, OpenFOAM…) enter here — each new
  format is a feature request routed through PM (Architecture review first).

## Depends on

Phase 1 (core vocabulary: BaseObject, registry, enums).
