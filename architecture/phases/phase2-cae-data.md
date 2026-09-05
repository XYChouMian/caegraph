# Phase 2 — CAE Data Pipeline

Status: Planned

Goal: `caegraph.data` becomes real — from raw CAE-ish data to PyG-ready
graphs, with scientific validation of every conversion invariant.

## New modules (planned)

```
src/caegraph/data/
├── mesh.py          # Mesh: nodes, elements, boundary regions, fields
├── graph.py         # Graph: thin torch_geometric.data.Data subclass
│                   # (ADR-007 guardrails: tensor-only, typed, collate-safe)
├── boundary/        # boundary-condition geometry layer (ADR-007)
│   ├── spec.py      # BoundarySpec: user-facing declaration dataclass
│   ├── manager.py   # BoundaryManager: region registry + spec binding
│   └── function.py  # FieldFunction: analytic (t, pos) -> tensor callable
├── interpolate.py   # field interpolation onto mesh nodes
├── dataset.py       # Dataset: collections, transforms, splits
└── transforms.py    # composable mesh/graph transformations
```

## Planned public APIs

- `Mesh` / `Graph` / `Dataset` (already in Design UML)
- `mesh_to_graph` conversion with configurable edge construction
  (node graph / cell graph)
- `BoundarySpec` / `BoundaryManager` / `FieldFunction` — the geometry
  layer of the two-layer boundary architecture (ADR-007); the compiled
  `BoundaryOperator` modules land in Phase 3 (`caegraph.models`)
- `Graph` tensor-only schema: node categories, boundary masks and
  region indices are tensors; region name tables stay on `Mesh`

## Validation focus (Validation Agent, mandatory)

- topology preservation (node/edge counts, connectivity)
- conservation of interpolated field integrals within tolerance
- boundary-condition mapping correctness
- node-category semantics: interior/boundary/corner classification,
  corner = multi-region membership (ADR-007)
- Graph schema conformance: tensor-only attributes, collate-safe
  (no rich Python objects on Graph)

## Rules

- Loaders register via the Phase 1 registry; no loader hard-imports another.
- Synthetic meshes only in tests (Testing Skill CAE rules).
- Real solver formats (Fluent, Abaqus, VTK…) enter here — each new format
  is a feature request routed through PM (Architecture review first).

## Depends on

Phase 1 (`core` registry, `BaseObject`).
