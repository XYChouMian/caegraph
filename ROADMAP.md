# CAEGraph Roadmap

CAEGraph's strategic plan: what we intend to build, in which order.

This file is the **strategy layer**. The layering is:

```
ROADMAP.md (future direction)
    ↓
architecture/phases/ (per-phase design)
    ↓
GitHub Milestones (concrete goals) → Issues (tasks) → Code → CHANGELOG (record)
```

Rules of engagement:

- `architecture/ARCHITECTURE.md` §6 is the **binding** phase table; this file
  is its strategy-facing mirror.
- Agents implement the **current phase only**. Out-of-phase ideas go to the
  corresponding phase backlog (see `.agent/skills/project_management/SKILL.md`).
- Statuses: `Planned` → `In progress` → `Done`.

---

## Vision

CAEGraph aims to become a general graph-based computational framework for
CAE simulation data and scientific machine learning — the missing link
between solver worlds (meshes, fields, boundary conditions) and graph
learning worlds (PyTorch, PyTorch Geometric).

---

## Phase 0 — Foundation · `Done`

Establish the project skeleton so that everything later is architecture-gated.

- [x] src-layout package + `pyproject.toml`
- [x] Architecture spec, dual UML system, ADRs
- [x] Agent governance (`.agent/`: workflow, skills, validation)
- [x] Bilingual MkDocs site (Material + i18n + mkdocstrings)
- [x] pytest framework + pre-commit + GitHub CI
- [x] First clean end-to-end run in `caegraph-dev` (install → pytest → docs build)

Details: [`architecture/phases/phase0-foundation.md`](architecture/phases/phase0-foundation.md)

## Phase 1 — Core Data Structures · `In progress`

Fundamental abstractions in `caegraph.core`: `BaseObject`, registries,
shared types. First Generated UML produced by tooling.

Details: [`architecture/phases/phase1-core.md`](architecture/phases/phase1-core.md)

## Phase 2 — CAE Data Pipeline · `Planned`

`caegraph.data`: CAE result loading, `Mesh` representation, Mesh→Graph
conversion, datasets. Conversion invariants (topology, conservation,
boundary mapping) scientifically validated.

Details: [`architecture/phases/phase2-cae-data.md`](architecture/phases/phase2-cae-data.md)

## Phase 3 — Machine Learning Interface · `Planned`

`caegraph.models` + `caegraph.physics`: GNN building blocks on PyG,
physics-informed losses, Trainer; end-to-end train/inference on synthetic
benchmarks.

Details: [`architecture/phases/phase3-ml-models.md`](architecture/phases/phase3-ml-models.md)

## Phase 4 — Release & Applications · `Planned`

API freeze, packaging polish, v1.0; scientific applications on top
(CFD surrogates, reduced-order modeling, multiphysics learning) as the
community grows.

Details: [`architecture/phases/phase4-release.md`](architecture/phases/phase4-release.md)
