# Phase 2 — CAE Data Pipeline (bridge band)

Status: Planned

Goal: implement the CAE → GNN bridge (ADR-007): the domain-core objects
plus the geometry / io / graph / integrations / dataset service band.

## New modules (planned)

```
src/caegraph/core/          # domain objects join the Phase 1 vocabulary
├── mesh.py                 # Mesh + composition (geometry/topology/boundary/fields)
├── graph.py                # Graph: domain-level abstraction, tensor storage
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

src/caegraph/graph/
├── builder.py              # node graph / cell graph construction
└── transform.py            # graph-space transforms

src/caegraph/integrations/pyg/
└── adapter.py              # to_pyg() + PyG datasets; the ONLY PyG import site

src/caegraph/dataset/
└── dataset.py              # collections, transforms, splits
```

## Planned public APIs

- `Mesh` / `Graph` / `Field` — domain core (ADR-007 D1/D3/D6)
- `mesh.to_graph()` with configurable edge construction (node / cell graph)
- `BoundarySpec` / `BoundaryManager` / `FieldFunction`
- `to_pyg()` adapter and PyG datasets (integrations)
- gmsh loader; VTK writer

## Validation focus (Validation Agent, mandatory)

- topology preservation (node/edge counts, connectivity)
- boundary-condition mapping: gmsh physical groups → regions /
  NodeCategory semantics (interior / boundary / corner;
  corner = multi-region membership)
- Graph schema conformance: tensor-only attributes, collate-safe
- PyG confinement: no `torch_geometric` import outside
  `integrations.pyg` (ADR-007 D2)
- VTK round-trip: mesh → graph → VTK → re-read

## Rules

- Loaders register via the core registry; no loader hard-imports another.
- Synthetic meshes only in tests (Testing Skill CAE rules).
- Real solver formats (Fluent, Abaqus, OpenFOAM…) enter here — each new
  format is a feature request routed through PM (Architecture review first).
- Never call backend (PyG) APIs from core / geometry / io / graph / dataset.

## Depends on

Phase 1 (core vocabulary: BaseObject, registry, enums).
