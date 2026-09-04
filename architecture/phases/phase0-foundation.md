# Phase 0 — Foundation

Status: **In progress** (current phase)

Goal: make everything that follows architecture-gated. No CAE algorithms,
no GNN models, no data processing — this phase produces zero functional
code by design.

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| src-layout package + `pyproject.toml` | done | ADR-001 |
| Architecture spec (`ARCHITECTURE.md`) | done | binding rules |
| Dual UML system + `UML_GUIDE.md` | done | ADR-002 |
| ADR mechanism (`decisions/`) | done | ADR-000..004 |
| Agent governance (`.agent/` workflow + 10 skills) | done | incl. Git governance, Validation Agent, emergency path |
| Bilingual MkDocs site (Material + i18n + mkdocstrings) | done | `.md` / `.en.md` convention |
| pytest framework (`tests/test_import.py`) | done | import smoke tests |
| pre-commit (black/ruff/pytest) + GitHub CI | done | `.pre-commit-config.yaml`, `test.yml` |
| Environment: `caegraph-dev` + `environment.yml` + `requirements-dev.txt` | done | ADR-003 |
| Clean end-to-end verification | pending | install → pytest → `mkdocs build --strict`, all green in `caegraph-dev` |

## Exit criteria

1. In `caegraph-dev` (Python 3.10): `pip install -e .`, `pytest`,
   `mkdocs build --strict` all pass with zero errors.
2. Reviewer Agent confirms: no functional code leaked into Phase 0.
3. PM Agent updates `CURRENT.md` → Phase 1 (only after a Review pass).

## Explicit non-goals

Mesh classes, graph conversion, any torch-dependent module beyond
declaring dependencies.
