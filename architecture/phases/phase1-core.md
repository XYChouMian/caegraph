# Phase 1 — Core Data Structures

Status: In progress

Goal: the minimal shared vocabulary everything else builds on —
`caegraph.core` and `caegraph.utils` become real code.

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

- `BaseObject` — ancestor of Mesh/Graph/Dataset per Design UML
- registry decorators for future loader/transform plugins
- `BoundaryType` / `NodeCategory` — shared vocabulary enums for the
  Phase 2 boundary-condition and node-category semantics (ADR-007)

## UML changes

- Design UML gains concrete members for `BaseObject` (attributes +
  contract methods) — added *before* implementation.
- Design UML gains `BoundaryType` and `NodeCategory` enums in
  `caegraph.core` (ADR-007), before any implementation.
- First Generated UML produced via `pyreverse` into `diagrams/generated/`;
  Architecture Agent runs the first design-vs-generated diff.

## Validation criteria

- Behavior tests with synthetic fixtures only; deterministic.
- No dependency on torch/PyG at this layer (core stays lightweight).

## Depends on

Phase 0 exit. Nothing else — this is the bottom of the dependency stack
(above `utils` only).
