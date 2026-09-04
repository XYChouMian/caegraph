# CAEGraph Architecture Specification

> This document is the single source of truth for the software architecture
> of CAEGraph. **Every contributor — human or AI agent — MUST read this
> document before writing any code.**

---

## 1. Project Vision

CAEGraph is a Python framework for **graph-based computation on CAE
(Computer-Aided Engineering) data**, in the style of
[PyTorch Geometric (PyG)](https://pyg.org).

Its mission is to bridge the gap between two worlds that today require
glue code:

| World | Examples | Existing tooling |
| --- | --- | --- |
| CAE / simulation | meshes, fields, boundary conditions, solver results | solver-specific formats, ad-hoc scripts |
| Graph machine learning | graphs, datasets, GNN models, training loops | PyTorch, PyG |

CAEGraph provides the **connecting layer**:

```
CAE Data  →  Mesh Representation  →  Graph Representation  →  Dataset
                                                          ↓
                     Visualization  ←  Training/Inference  ←  Model
```

Long-term goals:

- A stable, public, PyPI-installable scientific library — **not** a script collection.
- First-class support for mesh-to-graph conversion (node graphs, cell graphs, heterogeneous graphs).
- Composable GNN / physics-informed learning models on top of PyG.
- Reproducible, tested, documented — everything an open-source scientific project requires.

Non-goals (explicitly out of scope):

- CAEGraph is **not** a mesh generator and **not** a CFD/FEA solver.
- CAEGraph does not reimplement PyG; it builds on it.

---

## 2. Design Philosophy

1. **Modular design** — each subpackage has one responsibility; cross-package
   dependencies only point "downward" (models → data → core, never core → models).
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
CAE Data            raw solver/cad data (imports, field containers)
   ↓
Mesh Representation nodes, elements, boundaries, fields on mesh
   ↓
Graph Representation PyG Data/HeteroData built from the mesh
   ↓
Dataset             collections + transforms + splits + loading
   ↓
Model               GNN / physics-informed neural networks
   ↓
Training/Inference  Trainer, evaluators, checkpoints, logging
   ↓
Visualization       mesh, field, and graph plotting
```

### 3.2 Package map

| Package | Responsibility | Depends on |
| --- | --- | --- |
| `caegraph.utils` | logging, IO, reproducibility helpers | (nothing internal) |
| `caegraph.core` | base abstractions, registries, shared types | utils |
| `caegraph.data` | CAE data loading, mesh & graph representations, datasets | core |
| `caegraph.physics` | PDE residuals, physics losses, units | core |
| `caegraph.models` | GNN components, physics-informed models, Trainer | core, data, physics |
| `caegraph.visualization` | mesh/field/graph plotting | core, data |

Dependency layers (lower layers must never import higher layers;
same-layer imports are forbidden):

```
utils        (bottom)
  ↑
core
  ↑
data
  ↑
physics
  ↑
models
  ↑
visualization (top)
```

Notes on `physics` placement:

- `physics` sits **below** `models` deliberately: physics-informed models
  (e.g. a PINN model in `models`) consume PDE residuals and physics losses
  from `physics` (e.g. a `PhysicsLoss`), never the reverse.
- `physics` depends only on `core`/`utils`; it must never import `models`.
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

- Python ≥ 3.11, type hints on all public APIs.
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

---

## 6. Phase roadmap

Development is gated by phases. Agents must not implement features outside
the current phase; phase transitions require a Review pass.

| Phase | Scope | Exit criteria |
| --- | --- | --- |
| **Phase 0 — Foundation** (current) | packaging, architecture spec, UML dual system, docs, CI, agent governance | `pip install -e .` + pytest + `mkdocs build --strict` all pass; no CAE/GNN code |
| **Phase 1 — Core data structures** | `BaseObject`, registries, shared types in `caegraph.core` | core API tested + docstringed; first Generated UML produced |
| **Phase 2 — CAE data pipeline** | CAE loading, `Mesh`, Mesh→Graph conversion, datasets in `caegraph.data` | conversion invariants validated (topology/conservation/BC mapping) |
| **Phase 3 — ML models** | GNN components, physics-informed losses, Trainer in `caegraph.models`/`caegraph.physics` | end-to-end train/inference on synthetic benchmark |
| **Phase 4 — Release & applications** | API freeze, packaging polish, v1.0; CFD surrogate / ROM / multiphysics examples | Release Agent checklist fully green |

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
- Every user-visible change: update `CHANGELOG.md`.
- Versioning: [Semantic Versioning](https://semver.org). While `0.x`, minor
  releases may break APIs; from `1.0` the public API is frozen per policy.
