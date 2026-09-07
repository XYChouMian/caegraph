# Phase 2 — CAE Data Pipeline

Status: In progress — architecture re-evaluation open (ADR-015: CAEGraph canonical representation, **proposed**); `mesh.py` / mesh-centric io pipeline implementation is paused pending the decision; CellType (topology subsystem member) has landed and is unaffected by any outcome.

Goal: implement **R1** — the CAE → GNN data band (ADR-007/008): the domain-core objects plus geometry / io / graph / transforms / dataset.

## New modules (planned)

The tree below reflects the ADR-015 (**proposed**) representation hierarchy; the already-landed `core/celltype.py` migrates into `core/topology/` upon ADR-015 acceptance.

```
src/caegraph/core/          # domain canonical representation (ADR-015 proposed)
├── caegraph.py             # CAEGraph: entity-centric canonical representation —
│                           #   entities + stable IDs, relations, geometry hooks,
│                           #   fields, semantic regions; never imports PyG
├── field.py                # Field: named field data (unit, timestep, association)
├── boundary/               # semantic-region vocabulary (annotates CAEGraph)
│   ├── region.py           # BoundaryRegion: named codim-1 facet region
│   │                       #   (exterior boundary / internal interface)
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
                            #   one realization of the topology subsystem
                            #   (FEM/FVM); nodes (n,3), cells CSR, explicit
                            #   facets CSR + facet_cells, domain groups;
                            #   canonical global IDs — backend block indices
                            #   never escape io normalization

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

src/caegraph/graph/         # representation builders + GNN backend adapter layer
├── builder.py              # RepresentationBuilder: source discretization →
│                           #   CAEGraph entities + relations (FEM / FVM / FDM / SPH)
└── pyg.py                  # PyTorch Geometric adapter: CAEGraph →
                            #   torch_geometric.data.Data (PyG is a backend,
                            #   never the domain graph object; ADR-015)

src/caegraph/transforms/    # BC application lives HERE, not on Graph
├── geometry.py             # coordinate / feature normalization
├── feature.py              # CAE feature engineering
└── physics.py              # boundary-condition encoding:
                            #   data.x[data.inlet_mask] = value pattern

src/caegraph/dataset/
└── dataset.py              # CAEDataset(PyG Dataset): collections, splits
```

## Planned public APIs

- `CAEGraph` — domain canonical representation (ADR-015 proposed): entities + stable IDs, relations, fields, geometry hooks, semantic regions; never imports PyG
- `Mesh` / `CellType` — topology subsystem (ADR-014 narrowed): Mesh is a topology-rich discretization representation (FEM/FVM realization), no longer the top-level canonical object
- `Field` / `BoundaryRegion` / `BoundarySpec` / `BoundaryManager` — field & semantic-region vocabulary (ADR-007 D6, ADR-010/011); `FieldFunction` deferred
- `AbstractMeshLoader` + gmsh adapter — source loading pipeline (ADR-012; target object redefined by ADR-015 upon acceptance); meshio provisional engine (ADR-013)
- `RepresentationBuilder` (FEM/FVM/FDM/SPH) — source discretization → CAEGraph entities + relations; replaces the single `Mesh → GraphBuilder` contract
- PyG adapter — `CAEGraph → torch_geometric.data.Data` (backend adapter, not a domain object)
- Geometry / feature / physics transforms (PyG transform protocol)
- `CAEDataset`; VTK writer

## Validation focus (Validation Agent, mandatory)

- topology preservation (node/edge counts, connectivity)
- source named group mapping: source groups (e.g. Gmsh physical groups) → domain groups / BoundaryRegion (global facet IDs), classified by dimension per ADR-012
- NodeCategory semantics: interior / boundary / corner; corner derived from membership in multiple boundary/interface facet regions (not from a legacy node-set boundary model)
- Graph schema conformance: required CAE field and graph attributes present; `validate()` enforced (Graph is the neural representation, not a full Mesh copy)
- PyG boundary: `core`/`geometry`/`io` never import `torch_geometric`
- VTK validation: canonical Mesh → VTK → re-read topology consistency. Phase 2 owns the Mesh→VTK writer; Graph-layer predicted-field export stays with Phase 4.

## Rules

- Loaders register via the core registry; no loader hard-imports another.
- Synthetic meshes only in tests (Testing Skill CAE rules).
- Real solver formats (Fluent, Abaqus, OpenFOAM…) enter here — each new format is a feature request routed through PM (Architecture review first).
- Registry stays a name→factory mapping (Phase 1 contract: callable check only — Python type erasure makes runtime generic checks a non-goal). Runtime type enforcement (`Registry(kind, base_class=...)` + `issubclass`) is a recorded future option (Design UML Registry note); adopt it only if Phase 2 loader wiring needs it, decided explicitly.
- Loading and Mesh structure follow ADR-012 (source normalization → canonical build) and ADR-014 (canonical Mesh data model); meshio is the provisional IO engine (ADR-013).
- Resolved design question (ADR-011): the ADR-010 "未来演进" re-evaluation is complete — keep the single seven-value `BoundaryType` through Phase 2. `BoundarySpec` must enforce per-type slot-coherence validation (`paired_region` required for PERIODIC; value slots meaningful only for constraint-valued types); refined Phase 3 re-trigger conditions for a possible orthogonal role × constraint split are recorded in ADR-011.

## Coding gate

Coding order follows the ADR-015 (**proposed**) hierarchy — CAEGraph core first, topology/discretization adapters after:

1. `CAEGraph` core (entities + stable IDs, relations, field/region hooks; never PyG)
2. `Field` / semantic regions (`boundary/`)
3. topology subsystem + discretization adapters (FEM: Mesh topology + CellType — the CellType foundation has already landed and is tested)
4. PyG adapter (`graph/pyg.py`)

CellType prerequisites remain binding for any topology work: stable integer codes (explicit mapping, not enum-declaration order), CAEGraph local-node conventions, codim-1 face templates — frozen with the implementation (docstring + tests).

## Depends on

Phase 1 (core vocabulary: BaseObject, registry, enums).
