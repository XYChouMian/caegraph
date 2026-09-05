# CAEGraph UML Guide

CAEGraph maintains a **dual UML system**. Understanding the difference is
mandatory for every contributor and agent.

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
- The gap between the two is the project's **structural technical debt** —
  it must be visible, not hidden.

## 3. Workflow

1. Proposing structural change?
   → Update `architecture/design/class_diagram.puml` first.
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
- Agents MUST check both before and after implementing (see
  `architecture/ARCHITECTURE.md` §5).

## 5. Current status

- Phase 1 is in progress. The design UML defines the seven core
  abstractions (`BaseObject`, `Mesh`, `Graph`, `Field`, `Dataset`,
  `Model`, `Trainer`) plus the ADR-007 bridge band (geometry / io /
  graph / integrations / dataset).
- Generated UML: empty — no concrete classes have been implemented yet.
