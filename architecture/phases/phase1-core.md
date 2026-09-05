# Phase 1 — Core Data Structures

Status: In progress

Goal: the framework-independent foundation of the domain core —
`caegraph.core` and `caegraph.utils` become real code.

Per ADR-007 the full domain core later also holds `Mesh`, `Graph`, and
`Field` (tensor storage); those land in Phase 2 together with the bridge
band. Phase 1 delivers the vocabulary they build on.

## New modules

```
src/caegraph/core/
├── base.py        # BaseObject: identity, metadata, validation contract
├── registry.py    # registry/factory mechanism for loaders & transforms
└── enums.py       # shared enums: BoundaryType, NodeCategory (ADR-007)

src/caegraph/utils/
└── logging.py     # framework-wide logging helper
```

## Planned public APIs

- `BaseObject` — ancestor of Mesh/Graph/Field/Dataset/Model per Design UML
- registry decorators for future loader/transform plugins
- `BoundaryType` / `NodeCategory` — shared vocabulary for the Phase 2
  boundary-condition and node-category semantics (ADR-007)

## UML changes

- Design UML restructured to the ADR-007 package architecture; seven
  core abstractions (`BaseObject`, `Mesh`, `Graph`, `Field`, `Dataset`,
  `Model`, `Trainer`) with the bridge band (geometry / io / graph /
  integrations / dataset) around them.
- First Generated UML produced via `pyreverse` into `diagrams/generated/`;
  Architecture Agent runs the first design-vs-generated diff.

## Validation criteria

- Behavior tests with synthetic fixtures only; deterministic.
- Phase 1 deliverables are torch-free; the core layer is PyG-free
  forever (PyG imports live only in `caegraph.integrations.pyg`,
  ADR-007 D2).

## Depends on

Phase 0 exit. Nothing else — this is the bottom of the dependency stack
(above `utils` only).
