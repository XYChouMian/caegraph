# Phase 1 — Core Data Structures

Status: In progress

Goal: the framework-independent foundation of the domain core —
`caegraph.core` and `caegraph.utils` become real code.

Per ADR-007 the full domain core later also holds `Mesh` and `Field`
(tensor storage); `Graph` lands in `caegraph.graph`, the PyG-native
neural-representation layer. All of those arrive in Phase 2 together
with the data band. Phase 1 delivers the vocabulary they build on.

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

- `BaseObject` — shared base for the domain-truth Mesh and Field objects;
  learning-layer classes use ecosystem-native bases (ADR-009)
- registry decorators for future loader/transform plugins
- `BoundaryType` / `NodeCategory` — shared vocabulary for the Phase 2
  boundary-condition and node-category semantics (ADR-007)

## UML changes

- Design UML restructured to the ADR-007/ADR-008 package architecture;
  six principal abstractions (`BaseObject`, `Mesh`, `Graph`, `Field`,
  `CAEDataset`, `Model`) with the workflow bands around them (geometry/io/
  graph/transforms/dataset → physics/models/assimilation → workflow/
  inference).
- First Generated UML produced via `pyreverse` into `diagrams/generated/`;
  Architecture Agent runs the first design-vs-generated diff.

## Validation criteria

- Behavior tests with synthetic fixtures only; deterministic.
- Phase 1 deliverables are torch-free; the core layer is PyG-free
  forever (the PyG boundary starts at `caegraph.graph`, ADR-007 D2).

## Depends on

Phase 0 exit. Nothing else — this is the bottom of the dependency stack
(above `utils` only).
