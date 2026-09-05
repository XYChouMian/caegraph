# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Clarified the ADR-007/008 architecture through ADR-009: GraphBuilder owns
  Mesh-to-Graph conversion, BaseObject is limited to domain-truth objects, and
  Graph/CAEDataset/Model use their native PyG/PyTorch base classes.
- Marked Phase 0 as complete and Phase 1 (Core Data Structures) as in progress
  across the phase pointer, architecture specification, README, and MkDocs site.
- Switched the project license from MIT to the Apache License 2.0
  (`LICENSE`, package classifiers, and README updated).
- Standard development environment `caegraph-dev` downgraded from Python 3.11
  to Python 3.10 (ADR-003); CI keeps testing both 3.10 and 3.11, and the docs
  build job now runs on 3.10.
- Consolidated the temporary Python compatibility decisions from ADR-005 and
  ADR-006 into the canonical environment strategy in ADR-003.

### Added

- Froze the product positioning (ADR-008): CAEGraph bridges CAE
  simulation and physics AI through a **CAE → GNN → AI workflow**
  (CAE data → graph representation → GNN training → neural simulation
  on new meshes → experimental assimilation). Architecture redesigned
  accordingly (ADR-007): a PyG-native
  `Graph(torch_geometric.data.Data)` neural-representation layer, a
  framework-free domain core (`BaseObject`/`Mesh`/`Field`), transforms
  and dataset bands, physics losses, a Model interface without a GNN
  zoo, assimilation operators, workflow training utilities, and an
  inference (neural simulation) harness with VTK write-back.
  Positioning is frozen — no solver/trainer/alternative-backend
  abstractions without a new ADR.
- Shared Git governance for all Agent roles, including permission boundaries,
  branch and commit conventions, review gates, and release authorization.
- Python 3.10 compatibility testing (CI test matrix covers both 3.10 and
  3.11).
- `.agent/skills/aggregate_skills.py`: script aggregating all
  `SKILL.md` files into `.agent/ALL_SKILLS.md`.

### Deprecated

- The empty `caegraph.data` umbrella namespace is retained for compatibility
  but deprecated. New imports should use `caegraph.core`, `caegraph.io`,
  `caegraph.graph`, `caegraph.transforms`, or `caegraph.dataset`. Removal is
  planned no earlier than version 0.3.0.

## [0.1.0] - 2026-09-03

### Added

- Phase 0 project foundation:
  - src-layout package skeleton (`src/caegraph/` with `core`, `data`,
    `models`, `physics`, `visualization`, `utils` subpackages)
  - `pyproject.toml` with modern packaging metadata
  - Architecture specification (`architecture/ARCHITECTURE.md`)
  - UML dual system: design UML (`architecture/design/class_diagram.puml`)
    and generated UML (`diagrams/generated/`) with
    `architecture/UML_GUIDE.md`
  - Agent development standards (`.agent/skills/*/SKILL.md`)
  - MkDocs documentation site (Material theme + mkdocstrings)
  - pytest test framework with import smoke test
  - pre-commit hooks (black, ruff, pytest)
  - GitHub Actions CI (install, pytest, MkDocs build)
