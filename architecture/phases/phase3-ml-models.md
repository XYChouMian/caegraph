# Phase 3 — Machine Learning Interface

Status: Planned

Goal: learning on CAE graphs — `caegraph.physics` + `caegraph.models` +
`caegraph.assimilation` + `caegraph.workflow` (ADR-008: R2 + R4).

## Scope guard (ADR-007 D5 / ADR-008)

- **No Trainer abstraction**: no fit loop, no optimizer/distributed
  engines — training loops belong to users (PyTorch / Lightning).
- **No GNN zoo**: `models` provides the Model interface + CAE-aware
  utilities only; concrete architectures (MeshGraphNet, GNO,
  Transformers…) live in `examples/` or external projects.
- **No solver numerics**: time-integration schemes are model-side.

## New modules (planned)

```
src/caegraph/physics/
├── equations.py     # PDE residuals
└── constraints.py   # physics-informed loss terms (PhysicsLoss)

src/caegraph/models/
├── base.py          # Model: encode-process-decode contract
├── interface.py     # typing / protocols for CAE-aware models
└── operators.py     # CAE-aware model utilities

src/caegraph/assimilation/
├── observation.py   # observation operators (sparse measurements, e.g. PIV)
└── correction.py    # correction operators (dense prediction + observation)

src/caegraph/workflow/
├── losses.py        # loss assembly: data + physics + observation terms
└── batching.py      # CAE-aware batch adaptation helpers
```

## Planned public APIs

- `Model(torch.nn.Module)` contract (six principal abstractions, ADR-008/009)
  — ecosystem-native interface, not zoo
- `PhysicsLoss` consumed by physics-informed models
- `Observation` / `Correction` operators (R4)
- loss-assembly + batch-adaptation utilities (R2)

## Validation focus

- End-to-end train on synthetic benchmark (small ruled mesh, analytic
  ground truth), user-provided training loop
- Observation-constraint mode: sparse synthetic measurements improve
  predictions vs. data-only baseline (R4, quantified)
- Loss convergence sanity + reproducibility under fixed seed

## Depends on

Phase 2 (graphs/datasets/transforms); `physics` depends only on
core/graph.
