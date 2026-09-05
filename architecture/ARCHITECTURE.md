# CAEGraph Architecture Specification

> This document is the single source of truth for the software architecture
> of CAEGraph. **Every contributor — human or AI agent — MUST read this
> document before writing any code.**

---

## 1. Project Vision

CAEGraph is a Python framework that bridges CAE simulation and physics AI
through a **CAE → GNN → AI workflow**: it converts CAE simulation data —
meshes, fields, boundary conditions, physics metadata — into graph
representations, enables GNN training on engineering problems, runs
neural simulation on new meshes with pretrained models, and corrects
predictions with experimental observations. It **extends**
[PyTorch Geometric (PyG)](https://pyg.org) for computational engineering.

Four core requirements (frozen, ADR-008):

- **R1** — CAE data → GNN training data (parsing, topology, features,
  fields, boundary encoding).
- **R2** — GNN training workflows adapted to CAE data (not a training
  framework).
- **R3** — any mesh + a pretrained GNN → neural simulation (the AI
  counterpart of the CAE workflow).
- **R4** — experimental-data assimilation (e.g. PIV sparse measurements
  correcting dense predictions).

```
CAE software (Fluent, Abaqus, OpenFOAM, gmsh, VTK/ParaView)
   ↓  io (loaders, registry)
Mesh Representation        nodes, elements, boundary regions, fields
   ↓  geometry (metrics, edge features) · graph (Graph(Data) + builder)
Graph Representation       PyG-native neural representation (ADR-007)
   ↓  transforms (feature / physics / boundary-condition encoding)
Dataset                    CAEDataset (PyG), transforms, splits
   ↓  physics · models (interface + utilities) · workflow (loss assembly)
Training                   user loop or Lightning — caegraph never replaces it
   ↓  pretrained model + new mesh
Inference (neural simulation)   rollout harness → field reconstruction
   ↓                              ↘ assimilation (observation correction)
io (writers: VTK)  →  Visualization (ParaView ecosystem)
```

Long-term goals:

- A stable, public, PyPI-installable scientific library — **not** a script collection.
- First-class support for mesh-to-graph conversion (node graphs, cell graphs, heterogeneous graphs).
- CAE-aware model utilities on top of the PyG-native graph layer; the
  library never locks users into one training paradigm and never becomes
  a GNN zoo (ADR-008).
- Reproducible, tested, documented — everything an open-source scientific project requires.

Non-goals (explicitly out of scope):

- CAEGraph is **not** a mesh generator and **not** a CFD/FEA solver.
- CAEGraph is **not** a training framework: no Trainer/optimizer/
  distributed engines (ADR-008); training loops belong to users
  (PyTorch / Lightning).
- CAEGraph does not implement solver numerics (time-integration
  schemes); the inference layer provides workflow harnesses only
  (ADR-007 D5).
- CAEGraph does not reimplement PyG; it extends the PyG ecosystem for
  computational engineering (ADR-008) while keeping its engineering
  truth (Mesh/Field/Boundary) framework-free.

---

## 2. Design Philosophy

1. **Modular design** — each subpackage has one responsibility; cross-package
   dependencies only point "downward" (models → dataset → core, never core → models).
2. **Reusable components** — building blocks (transformations, losses, encoders)
   are small, composable, and independent of specific solvers or file formats.
3. **Clear abstraction** — every public class implements an explicit abstraction
   documented in the design UML; no implicit interfaces, no god objects.
4. **API stability** — anything exported in `caegraph.__init__` or documented in
   the API reference is a public contract. Breaking changes require a changelog
   entry, a deprecation cycle, and a major-version bump.
5. **Documentation consistency** — every public module, class, and function has
   a docstring; docs are generated from code (mkdocstrings), so documentation
   drift is a bug, not a nuisance.

---

## 3. Core Architecture

### 3.1 Processing pipeline

The framework is organized around the canonical data flow:

```
CAD / CFD / FEM software   raw solver/cad data
   ↓
io                         loaders (gmsh first), writers (VTK)
   ↓
Mesh                       domain truth: nodes, elements, regions, fields
   ↓
geometry                   metrics, edge features, interpolation
   ↓
Graph                      PyG-native neural representation, tensor storage
   ↓
transforms                 feature / physics / boundary-condition encoding
   ↓
Dataset                    CAEDataset (PyG) + transforms + splits
   ↓
Training                   physics losses · Model interface · workflow
   (user loop / Lightning) utilities — caegraph adapts, never replaces
   ↓
Inference                  neural simulation harness (rollout, reconstruction)
   ↓
Assimilation               observation correction of predictions (R4)
   ↓
Visualization              plotting + VTK write-back (ParaView ecosystem)
```

### 3.2 Package map

| Package | Responsibility | Depends on |
| --- | --- | --- |
| `caegraph.utils` | logging, IO, reproducibility helpers | (nothing internal) |
| `caegraph.core` | domain truth: BaseObject, Mesh, Field; boundary vocabulary; registries; shared enums | utils (torch allowed, PyG forbidden) |
| `caegraph.geometry` | geometric services: metrics, edge features, interpolation | core |
| `caegraph.io` | loaders (gmsh first) and writers (VTK); format registry | core |
| `caegraph.graph` | `Graph(torch_geometric.data.Data)` neural representation + builders | core, geometry |
| `caegraph.transforms` | geometry / feature / physics transforms (BC encoding) on Graph | graph |
| `caegraph.dataset` | CAEDataset (PyG): collections, splits | graph, transforms |
| `caegraph.physics` | PDE residuals, physics losses, constraints | core, graph |
| `caegraph.models` | Model interface + CAE-aware utilities (no GNN zoo) | core, graph, physics |
| `caegraph.assimilation` | observation / correction operators (R4) | core, graph, physics |
| `caegraph.workflow` | training utilities: loss assembly, CAE batch adaptation (no fit loop) | physics, models, assimilation, dataset |
| `caegraph.inference` | neural-simulation harness: simulator, rollout loop (numerics model-side) | models, assimilation, io |
| `caegraph.visualization` | mesh/field/graph plotting | core, io |

Dependency layers (lower layers must never import higher layers;
same-layer imports are forbidden):

```
utils        (bottom)
  ↑
core         (domain truth; torch-only, never PyG)
  ↑
geometry / io   (sibling services; must not import each other)
  ↑
graph        (Graph(Data): PyG-native neural representation)
  ↑
transforms
  ↑
dataset
  ↑
physics
  ↑
models / assimilation   (Model interface + utilities; observation/correction)
  ↑
workflow / inference    (training utilities; neural-simulation harness)
  ↑
visualization (top)
```

Notes on `physics` placement:

- `physics` sits **below** `models` deliberately: physics-informed models
  (e.g. a PINN model in `models`) consume PDE residuals and physics losses
  from `physics` (e.g. a `PhysicsLoss`), never the reverse.
- `physics` depends only on `core`/`utils` (plus `graph` for
  graph-structured inputs); it must never import `models`.
- PyG boundary: `torch_geometric` may be imported from `caegraph.graph`
  upward; `core`/`geometry`/`io` never import it (ADR-007 D2).
- `assimilation` is consumed in two modes: by `workflow`
  (training-constraint mode — observation loss terms) and by `inference`
  (post-prediction correction).
- If future physics-informed learning needs force a richer structure, the
  preferred evolution is splitting `physics` into submodules
  (`equations`, `constraints`, ...) inside the same layer — recorded via an
  ADR — not reordering the layers.
- No circular imports, ever.
- Only truly cross-domain logic may live in `utils`; single-domain logic
  stays inside its own subpackage.
- "Garbage drawer" modules (`helper.py`, `common.py`, `misc.py`,
  `*_utils.py`) require Architecture Agent approval. Domain-scoped tool
  modules inside their owning subpackage (e.g. plotting helpers inside
  `visualization`) are fine.

### 3.3 UML dual system

- **Design UML** (`architecture/design/*.puml`) — the *planned* design,
  maintained by the Architecture agent. Changes here precede code changes.
- **Generated UML** (`diagrams/generated/`) — the *actual* state of the code,
  generated from source. It never diverges silently from reality.

See `architecture/UML_GUIDE.md`. The two must be reconciled regularly;
divergence is treated as technical debt.

---

## 4. Coding Rules

### 4.1 Language & style

- Python ≥ 3.10, type hints on all public APIs. The canonical development
  environment is Python 3.10 (ADR-003); CI verifies every supported minor
  version including 3.11.
- Formatting via **black**; linting via **ruff** (config in `pyproject.toml`).
- Line length 88.

### 4.2 Structure rules

- All source lives in `src/caegraph/` (src-layout). **No Python files in the
  repository root**, ever.
- No single-file scripts as core functionality; no throwaway tool scripts in
  the repository.
- Every module has exactly one clear responsibility, stated in its docstring.
- No duplicated code: three similar lines are better than a premature
  abstraction, but real duplication must be factored into the correct existing
  module — **not** into a new `helpers.py`.
- Do not create helper/util files on a whim; utilities belong in
  `caegraph.utils` with a stated responsibility.
- Functionality must not be scattered: a feature lives in its designated
  subpackage per the package map above.

### 4.3 Documentation rules

- Every **public class** has a docstring (purpose, responsibilities, usage).
- Every **public function/method** has a docstring with Args/Returns/Raises.
- Every **module** has a docstring stating its responsibility.
- Docstrings feed the generated API docs — write them for users.

### 4.4 Testing rules

- Every public behavior gets a test in `tests/`, mirroring the `src/` layout.
- Tests must not depend on network access or huge CAE files; use small
  synthetic fixtures.
- A change without tests is incomplete.

### 4.5 Compatibility rules

- Do not pin exact dependency versions in `pyproject.toml`; use lower bounds.
- Keep the package PyPI-publishable at all times.

---

## 5. Agent Development Rules

All code agents (human or AI) MUST follow this workflow **before writing code**:

1. **Read `architecture/ARCHITECTURE.md`** (this file) and the relevant
   `.agent/skills/*/SKILL.md` for your role.
2. **Check existing UML** — inspect `architecture/design/*.puml` (design) and
   `diagrams/generated/` (current reality). Never invent an abstraction that
   is not in the design UML.
3. **Modify the design first** — if a change affects structure, update the
   design UML and get it reviewed *before* coding. Code follows design;
   design never retro-fitted to code.
4. **Synchronize documentation and tests** — a code change is complete only
   when docstrings, MkDocs pages, the CHANGELOG, and tests are updated
   together.

Additionally:

- Respect the Phase gates: do not implement features outside the current
  phase. The binding table lives in §6; the current-phase pointer is
  `architecture/phases/CURRENT.md`; the strategy mirror is `ROADMAP.md`;
  per-phase designs are `architecture/phases/phaseN-*.md`.
- Keep the consistency invariant at all times:

```
Code ⇔ Architecture ⇔ UML ⇔ Documentation ⇔ Testing ⇔ Environment ⇔ Release
```

Violations of any rule in this file are blocking review findings.

- Git is a shared engineering capability across all Agent roles. Branches,
  commits, reviews, merges, tags, and release operations follow
  `.agent/skills/git/SKILL.md`; Git permissions never override role boundaries.

---

## 6. Phase roadmap

Development is gated by phases. Agents must not implement features outside
the current phase; phase transitions require a Review pass.

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| **Phase 0 — Foundation** (done) | packaging, architecture spec, UML dual system, docs, CI, agent governance | `pip install -e .` + pytest + `mkdocs build --strict` all pass; no CAE/GNN code |
| **Phase 1 — Core data structures** (current) | `BaseObject`, registries, shared types in `caegraph.core` | core API tested + docstringed; first Generated UML produced |
| **Phase 2 — CAE data pipeline** | domain-truth objects (`Mesh`/`Field`) + geometry/io/graph/transforms/dataset data band, `Graph(torch_geometric.data.Data)`, gmsh first, VTK write-back (R1) | conversion invariants validated (topology/conservation/BC mapping); PyG boundary enforced |
| **Phase 3 — ML models** | physics losses, Model interface + CAE utilities, assimilation operators, workflow training utilities in `caegraph.physics`/`models`/`assimilation`/`workflow` | end-to-end training on synthetic benchmark incl. observation-constraint mode (R2+R4) |
| **Phase 4 — Neural simulation & release** | inference harness (simulator, rollout), VTK write-back, examples, API freeze, v1.0 | rollout on unseen mesh validated (R3); Release Agent checklist fully green |

References to "Phase" anywhere in the agent governance system
(`.agent/`) mean this table.

Strategy layer: `ROADMAP.md` mirrors this table for users/contributors.
Per-phase designs (scope, planned modules/APIs, validation criteria):
`architecture/phases/phaseN-*.md`. Current-phase pointer (the single file
agents must check): `architecture/phases/CURRENT.md`.

## 7. Change management

- Architecture changes: edit this file + design UML in the same PR, and
  record an Architecture Decision Record in `architecture/decisions/`
  (see `ADR-000-template.md`).
- **Positioning freeze (ADR-008)**: no solver abstraction, no trainer
  abstraction, no alternative graph backend layer — without a new ADR.
- Every user-visible change: update `CHANGELOG.md`.
- Versioning: [Semantic Versioning](https://semver.org). While `0.x`, minor
  releases may break APIs; from `1.0` the public API is frozen per policy.
