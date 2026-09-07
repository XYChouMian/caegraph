# CAEGraph UML Guide

CAEGraph maintains a **dual UML system**. Understanding the difference is mandatory for every contributor and agent.

---

## 1. The two systems

| | Design UML | Generated UML |
| --- | --- | --- |
| Location | `architecture/design/*.puml` | `diagrams/generated/` |
| Meaning | **The planned design** — what the architecture intends | **The real state** — what the code actually contains |
| Source | Hand-written PlantUML, maintained by the Architecture agent | Generated from source code (e.g. `pyreverse`, `py2puml`) |
| When updated | **Before** code changes (design-first workflow) | After code changes (regeneration) |
| Review value | Contract / blueprint | Ground truth |

## 2. Why two systems?

- Design UML encodes *intent*: reviewers judge changes against the plan.
- Generated UML encodes *reality*: it exposes drift between plan and code.
- The gap between the two is the project's **structural technical debt** —it must be visible, not hidden.

## 3. Workflow

1. Proposing structural change?→ Update `architecture/design/class_diagram.puml` first.
2. Implementing code that matches the approved design.
3. Regenerate diagrams into `diagrams/generated/`:
   ```bash
   # from the repository root (requires pyreverse, ships with pylint)
   pyreverse -o puml -p caegraph --output-directory diagrams/generated src/caegraph
   ```
4. **Compare** design vs. generated. Any divergence must be either:
   - fixed in code (code drifted), or
   - reflected in the design UML (design evolved — justify it in the PR).

## 4. Rules

- `diagrams/generated/` is machine-managed. Do not hand-edit generated files.
- Design UML shows abstractions and responsibilities, not method signatures.
- Both systems are versioned in Git; keep them in the same PR as the code.
- Agents MUST check both before and after implementing (see `architecture/ARCHITECTURE.md` §5).

## 5. Current status

- Phase 2 is in progress. The design UML defines the principal abstractions per ADR-015 (`CAEGraph` as the canonical domain representation, `Mesh` (topology subsystem), `Field`, `CAEDataset`, `Model`, plus the PyG adapter) and the ADR-008 workflow bands: geometry/io/graph/transforms/dataset (R1), physics/models/assimilation/workflow (R2+R4), inference (R3).
- ADR-009 (as amended by ADR-015) makes the conversion and inheritance boundaries explicit: RepresentationBuilder owns source-discretization → CAEGraph; the PyG adapter (`graph/pyg.py`) owns CAEGraph → `torch_geometric.data.Data`; BaseObject covers the domain object family (CAEGraph, Mesh, Field); CAEDataset/Model remain backend-specific (PyG Dataset / torch.nn.Module are the Phase 2 choices).
- Generated UML contains the current package graph plus the Phase 1 classes (`BaseObject`, `Registry`, `BoundaryType`, `NodeCategory`). The Phase 2 abstractions (`CAEGraph`, `Mesh`, `Field`, ...) still live only in the design UML and will appear in generated diagrams as they are implemented and regenerated.
