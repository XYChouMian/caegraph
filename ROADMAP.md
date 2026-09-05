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

CAEGraph bridges CAE simulation and physics AI through a
**CAE → GNN → AI workflow** — converting CAE data into graph
representations, enabling GNN training on engineering problems, running
neural simulation on new meshes with pretrained models, and correcting
predictions with experimental observations (ADR-008).

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

**R1** — domain-truth objects (`Mesh`/`Field`) plus the data band:
`caegraph.geometry`/`caegraph.io`/`caegraph.graph`/
`caegraph.transforms`/`caegraph.dataset` — CAE loading (gmsh first),
Mesh→`Graph(torch_geometric.data.Data)` conversion, transforms (BC
encoding), CAEDataset, VTK write-back. Conversion invariants (topology,
conservation, boundary mapping) scientifically validated.

Details: [`architecture/phases/phase2-cae-data.md`](architecture/phases/phase2-cae-data.md)

## Phase 3 — Machine Learning Interface · `Planned`

**R2 + R4** — `caegraph.physics` (losses/constraints), `caegraph.models`
(Model interface + utilities, no GNN zoo), `caegraph.assimilation`
(observation/correction), `caegraph.workflow` (loss assembly, batch
adaptation — no fit loop); end-to-end training on synthetic benchmarks
with user-provided loops, incl. observation-constraint mode.

Details: [`architecture/phases/phase3-ml-models.md`](architecture/phases/phase3-ml-models.md)

## Phase 4 — Neural Simulation & Release · `Planned`

**R3** — `caegraph.inference` (simulator + rollout harness, numerics
model-side), VTK write-back closed loop, examples (concrete model
architectures live outside the library); API freeze, packaging polish,
v1.0.

Details: [`architecture/phases/phase4-release.md`](architecture/phases/phase4-release.md)
