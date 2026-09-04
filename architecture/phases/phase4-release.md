# Phase 4 — Release & Applications

Status: Planned

Goal: CAEGraph v1.0 — a frozen public API — and the first scientific
applications on top.

## Scope

1. **API freeze**
   - Full public-API audit (Reviewer): every export documented, every
     breaking change from 0.x resolved or deprecated.
   - Import stability guaranteed; deprecation policy active.
2. **Packaging polish**
   - Single version source (ADR; replaces dual-file sync), `python -m build`
     + clean-wheel install verification.
   - Docs complete: tutorials for every major workflow, bilingual parity.
3. **Applications (community-facing)**
   - CFD surrogate modeling example
   - Reduced-order modeling (ROM) example
   - Multiphysics learning example
   Applications live in docs/examples + a separate examples repo if heavy —
   never inside `src/caegraph` (root: no application code in the library).

## Exit criteria

- Release Agent checklist fully green for `1.0.0`.
- ROADMAP/ARCHITECTURE updated for the post-1.0 cycle.

## Depends on

Phase 3 complete + validation green.
