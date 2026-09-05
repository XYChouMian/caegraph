# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

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

- Phase 2 data-layer architecture design (ADR-007): a PyG-native `Graph`
  subclass contract, a two-layer boundary-condition architecture
  (specs/managers in `caegraph.data`, compiled operators in
  `caegraph.models`), and interior/boundary/corner node categories;
  shared `BoundaryType`/`NodeCategory` enums planned for `caegraph.core`.
- Shared Git governance for all Agent roles, including permission boundaries,
  branch and commit conventions, review gates, and release authorization.
- Python 3.10 compatibility testing (CI test matrix covers both 3.10 and
  3.11).
- `.agent/skills/aggregate_skills.py`: script aggregating all
  `SKILL.md` files into `.agent/ALL_SKILLS.md`.

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
