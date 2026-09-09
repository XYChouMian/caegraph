# Phase 2 — CAE Data Pipeline

Status: In progress — ADR-015/016/017/018 accepted (graph-native canonical representation, construction / adaptation boundaries, domain composition); coding follows the Coding-gate order below (CAEGraph core first); CellType (topology subsystem member) has landed and is unaffected by any outcome.

Goal: implement **R1** — the CAE → GNN data band (ADR-007/008): the domain-core objects plus geometry / io / graph / transforms / dataset.

## New modules (planned)

The tree below reflects the ADR-015 representation hierarchy; the already-landed `core/celltype.py` migrates into `core/topology/` (ADR-015 accepted).

```
src/caegraph/core/          # domain canonical representation (ADR-015)
├── caegraph.py             # CAEGraph: graph-native canonical domain
│                           #   representation (ADR-015); semantic composition
│                           #   (ADR-018): entities, relations, geometry, fields,
│                           #   regions, conditions; topology subsystem =
│                           #   optional semantic provider, not class members;
│                           #   never imports PyG
├── field.py                # Field: named field data (unit, timestep, association)
├── boundary/               # semantic-region vocabulary (annotates CAEGraph)
│   ├── region.py           # BoundaryRegion: named semantic region (ADR-018) —
│   │                       #   membership per source discretization (cell-based:
│   │                       #   codim-1 facet region; exterior boundary /
│   │                       #   internal interface)
│   ├── manager.py          # BoundaryManager: semantic naming registry + spec
│   │                       #   binding resolution; topology ownership stays in
│   │                       #   the topology subsystem (references only)
│   └── spec.py             # BoundarySpec (slot-coherence validation, ADR-011);
│                           #   function.py (FieldFunction) deferred to the
│                           #   BC-declaration slice
└── topology/               # topology subsystem (ADR-014 narrowed; first-class
    ├── celltype.py         #   for cell-based discretizations) — CellType:
    │                       #   explicit stable integer codes, dim/node_count,
    │                       #   CAEGraph local-node convention + codim-1 face
    │                       #   templates (migrates from core/celltype.py)
    └── mesh.py             # Mesh: topology-rich discretization representation —
                            #   the cell-based topology representation supported
                            #   by the topology subsystem (FEM/FVM); nodes (n,3),
                            #   cells CSR, explicit facets CSR + facet_cells,
                            #   domain groups; canonical global IDs — backend
                            #   block indices never escape io normalization

src/caegraph/geometry/
├── metrics.py              # mesh-derived geometric entity features:
│                           #   distance/direction/normal/quality
└── interpolation.py        # field interpolation onto mesh nodes

src/caegraph/io/
├── base.py                 # AbstractMeshLoader: stable __call__ pipeline
│                           #   (ADR-012); protected hooks are adapter
│                           #   implementation details, not frozen
├── registry.py             # format registry on the core registry
├── gmsh.py                 # first source adapter: normalizes the Gmsh source
│                           #   representation through meshio (external IO
│                           #   engine, ADR-013) into the canonical Mesh
└── vtk_writer.py           # write-back into the ParaView ecosystem

src/caegraph/graph/         # representation construction + backend adapter layer;
│                           #   two logically separate concerns — construction
│                           #   (ADR-016) and adaptation (ADR-017); the layer
│                           #   must never be imported by core (no core → graph)
├── builder.py              # representation builder (extension point, ADR-015):
│                           #   source discretization → CAEGraph entities +
│                           #   relations; construction boundary: ADR-016
│                           #   (accepted; API/registry/layout not frozen)
└── pyg.py                  # backend adapter: CAEGraph → framework-specific
                            #   representation, concretized as
                            #   torch_geometric.data.Data in Phase 2
                            #   (adaptation contract: ADR-017; PyG is a
                            #   backend, never the domain model)

src/caegraph/transforms/    # BC application lives HERE, not on Graph
├── geometry.py             # coordinate / feature normalization
├── feature.py              # CAE feature engineering
└── physics.py              # boundary-condition encoding:
                            #   data.x[data.inlet_mask] = value pattern

src/caegraph/dataset/
└── dataset.py              # CAEDataset(PyG Dataset): collections, splits
```

## Planned public APIs

- `CAEGraph` — domain canonical representation (ADR-015): semantic composition (ADR-018) of entities, relations, fields, geometry, regions, conditions; topology subsystem = optional semantic provider; never imports PyG
- `Mesh` / `CellType` — topology subsystem (ADR-014 narrowed): Mesh is a topology-rich discretization representation (FEM/FVM), no longer the top-level canonical object
- `Field` / `BoundaryRegion` / `BoundarySpec` / `BoundaryManager` — field & semantic-region vocabulary (ADR-007 D6, ADR-010/011); `FieldFunction` deferred
- `AbstractMeshLoader` + gmsh adapter — source loading pipeline (ADR-012; target object redefined by ADR-015); meshio provisional engine (ADR-013)
- representation builder — source discretization → CAEGraph entities + relations; extension point per ADR-015, construction boundary frozen by ADR-016 (accepted; API/naming/registry deferred to the coding dispatch); replaces the single `Mesh → GraphBuilder` contract
- backend adapter — `CAEGraph → framework-specific representation` (PyG Data in Phase 2; adaptation boundary frozen by ADR-017, accepted — DataGraph is the conceptual backend representation layer, backend-side, owns no domain semantics, not a domain class)
- Geometry / feature / physics transforms (PyG transform protocol)
- `CAEDataset`; VTK writer

## Validation focus (Validation Agent, mandatory)

- topology preservation (node/edge counts, connectivity)
- source named group mapping: source groups (e.g. Gmsh physical groups) → domain groups / BoundaryRegion (global facet IDs — cell-based scope per ADR-014), classified by dimension per ADR-012
- NodeCategory semantics: interior / boundary / corner; corner derived from membership in multiple boundary/interface facet regions (not from a legacy node-set boundary model)
- Graph schema conformance: required CAE field and graph attributes present; `validate()` enforced (the learning-side representation, not a full Mesh copy)
- PyG boundary: `core`/`geometry`/`io` never import `torch_geometric`
- VTK validation: canonical Mesh → VTK → re-read topology consistency. Phase 2 owns the Mesh→VTK writer; Graph-layer predicted-field export stays with Phase 4.

## Rules

- Loaders register via the core registry; no loader hard-imports another.
- Synthetic meshes only in tests (Testing Skill CAE rules).
- Real solver formats (Fluent, Abaqus, OpenFOAM…) enter here — each new format is a feature request routed through PM (Architecture review first).
- Registry stays a name→factory mapping (Phase 1 contract: callable check only — Python type erasure makes runtime generic checks a non-goal). Runtime type enforcement (`Registry(kind, base_class=...)` + `issubclass`) is a recorded future option (Design UML Registry note); adopt it only if Phase 2 loader wiring needs it, decided explicitly.
- Loading and topology structure follow ADR-012 (source normalization → topology input per ADR-014; the product feeds CAEGraph construction, ADR-015/016) and ADR-014 (canonical cell-based topology model); meshio is the provisional IO engine (ADR-013).
- Resolved design question (ADR-011): the ADR-010 "未来演进" re-evaluation is complete — keep the single seven-value `BoundaryType` through Phase 2. `BoundarySpec` must enforce per-type slot-coherence validation (`paired_region` required for PERIODIC; value slots meaningful only for constraint-valued types); refined Phase 3 re-trigger conditions for a possible orthogonal role × constraint split are recorded in ADR-011.

## Coding gate

Coding order follows the ADR-015 hierarchy — CAEGraph core first, topology/discretization adapters after:

1. `CAEGraph` core (semantic composition — entities, relations, fields, regions, conditions; never PyG)
2. `Field` / semantic regions (`boundary/`)
3. topology subsystem + discretization adapters (FEM: Mesh topology + CellType — the CellType foundation has already landed and is tested)
4. backend adapter (PyG Data as the Phase 2 framework representation; ADR-017)

CellType prerequisites remain binding for any topology work: stable integer codes (explicit mapping, not enum-declaration order), CAEGraph local-node conventions, codim-1 face templates — frozen with the implementation (docstring + tests).

## Depends on

Phase 1 (core vocabulary: BaseObject, registry, enums).
