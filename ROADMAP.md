# CAEGraph Roadmap

CAEGraph's strategic plan: what we intend to build, in which order.

This file is the **strategy layer**. The layering is:

```mermaid
flowchart TD
    classDef nowrap white-space:nowrap

    A["<b>ROADMAP.md</b> — future direction"]
    B["<b>architecture/phases/</b> — per-phase design"]
    C["<b>GitHub Milestones</b> — concrete goals"]
    D["<b>Issues</b> — tasks"]
    E["<b>Code</b>"]
    F["<b>CHANGELOG</b> — record"]

    A --> B --> C --> D --> E --> F

    class A,B,C,D,E,F nowrap
```

Rules of engagement:

- `architecture/ARCHITECTURE.md` §6 is the **binding** phase table; this file is its strategy-facing mirror.
- Agents implement the **current phase only**. Out-of-phase ideas go to the corresponding phase backlog (see `.agent/skills/project_management/SKILL.md`).
- Statuses: `Planned` → `In progress` → `Done`.

---

## Vision

CAEGraph bridges CAE simulation and physics AI through a **CAE → GNN → AI workflow** — normalizing heterogeneous CAE data into **CAEGraph**, the graph-native canonical domain representation (ADR-015), enabling GNN training on engineering problems through a backend adapter, running neural simulation across different discretizations with pretrained models, and correcting predictions with experimental observations (ADR-008).

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

## Phase 1 — Core Data Structures · `Done`

Fundamental abstractions in `caegraph.core`: `BaseObject`, registries, shared types. First Generated UML produced by tooling.

Details: [`architecture/phases/phase1-core.md`](architecture/phases/phase1-core.md)

## Phase 2 — CAE Data Pipeline · `In progress`

**R1** — the `caegraph.core` domain core: **CAEGraph**, the graph-native canonical domain representation (ADR-015), with the topology subsystem (`Mesh`/`CellType` for cell-based discretizations), `Field`, and boundary vocabulary; plus the data band: `caegraph.geometry`/`caegraph.io`/`caegraph.graph`/`caegraph.transforms`/`caegraph.dataset` — CAE loading (gmsh first) via source normalization into canonical topology, representation construction (construction boundary: ADR-016, accepted), the backend adapter (CAEGraph → PyG Data in Phase 2; adaptation boundary: ADR-017, accepted), transforms (BC encoding), CAEDataset, VTK write-back. Conversion invariants (topology, conservation, boundary mapping) scientifically validated. Before Phase 3, benchmark the canonical data layout (memory usage, graph construction, neighbor query, CAEGraph→PyG conversion) — CAEGraph is optimized for domain representation and data interoperability, not for replacing general graph algorithm libraries (ADR-015).

Details: [`architecture/phases/phase2-cae-data.md`](architecture/phases/phase2-cae-data.md)

### Performance line: P2-PERF-02 · `HOLD — deferred until first-E2E checkpoint`

The NumPy-first data-pipeline restructuring (P2-PERF-02) is on **HOLD**. It is **not a Gate 5 blocker**. The current critical path is: Gate 5 CLOSED → first end-to-end run (Gmsh → Loader → Mesh → MeshRepresentationBuilder → CAEGraph → validate → to_pyg_data) → representative real-scale workload benchmark (end-to-end time and memory recorded) → PM re-evaluation of NumPy-first restructuring → either P2-PERF-02a or continue to Gate 6.

- Recorded future candidates (not started): **P2-PERF-02a** — internal NumPy-first representation (`_edges` ndarray, `_facet_cells` CSR, builder vectorization, relation normalization/validation vectorization, Mesh hot-path vectorization), in principle without requiring a BREAKING public API; **P2-PERF-02b** — public ndarray contract (`CAEGraph.edges`, `facet_adjacent_cells`, other public numerical collections), an independent decision; **not starting 02b is a legal final outcome**. ADR-025 is not created; if the restructuring window reopens, draft it from the then-latest main plus E2E and workload evidence.
- Re-evaluation trigger (all three must hold): ① first E2E succeeded with a trustworthy behavioral baseline; ② a representative real-scale workload demonstrates a perceptible time or memory bottleneck in the current Python-container paths (synthetic benchmarks alone do not satisfy this); ③ downstream (Gate 6 / Dataset / Transforms) has not yet come to depend on the concrete container representation. Otherwise stay on HOLD; re-evaluation may happen after each gate but must never block the critical path.
- Experiment evidence: the closed N1 experiment (`_expand_edges` vectorization, synthetic 4.3–10.1× local speedup) is archived in [`architecture/perf/P2-PERF-01a-evidence.md`](architecture/perf/P2-PERF-01a-evidence.md); its implementation never landed on `main` and is not an implementation baseline. During HOLD, new code must depend on semantics and public APIs only — never on storage representations such as `_edges` / `_facet_cells`.

## Phase 3 — Machine Learning Interface · `Planned`

**R2 + R4** — `caegraph.physics` (losses/constraints), `caegraph.models` (Model interface + utilities, no GNN zoo), `caegraph.assimilation` (observation/correction), `caegraph.workflow` (loss assembly, batch adaptation — no fit loop); end-to-end training on synthetic benchmarks with user-provided loops, incl. observation-constraint mode.

Details: [`architecture/phases/phase3-ml-models.md`](architecture/phases/phase3-ml-models.md)

## Phase 4 — Neural Simulation & Release · `Planned`

**R3** — `caegraph.inference` (simulator + rollout harness, numerics model-side), VTK write-back closed loop, examples (concrete model architectures live outside the library); API freeze, packaging polish, v1.0.

Details: [`architecture/phases/phase4-release.md`](architecture/phases/phase4-release.md)
