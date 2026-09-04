# Phase 2 — CAE Data Pipeline

Status: Planned

Goal: `caegraph.data` becomes real — from raw CAE-ish data to PyG-ready
graphs, with scientific validation of every conversion invariant.

## New modules (planned)

```
src/caegraph/data/
├── mesh.py          # Mesh: nodes, elements, boundary regions, fields
├── graph.py         # Graph: PyG-compatible conversion of a Mesh
├── dataset.py       # Dataset: collections, transforms, splits
└── transforms.py    # composable mesh/graph transformations
```

## Planned public APIs

- `Mesh` / `Graph` / `Dataset` (already in Design UML)
- `mesh_to_graph` conversion with configurable edge construction
  (node graph / cell graph)

## Validation focus (Validation Agent, mandatory)

- topology preservation (node/edge counts, connectivity)
- conservation of interpolated field integrals within tolerance
- boundary-condition mapping correctness

## Rules

- Loaders register via the Phase 1 registry; no loader hard-imports another.
- Synthetic meshes only in tests (Testing Skill CAE rules).
- Real solver formats (Fluent, Abaqus, VTK…) enter here — each new format
  is a feature request routed through PM (Architecture review first).

## Depends on

Phase 1 (`core` registry, `BaseObject`).
