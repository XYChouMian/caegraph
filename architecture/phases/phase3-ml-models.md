# Phase 3 — Machine Learning Interface

Status: Planned

Goal: learning on CAE graphs — `caegraph.models` + `caegraph.physics`.

Scope guard (ADR-007 D5): this phase delivers composable components and
physics losses only. Solver-side orchestration — time integrators
(Euler/RK), PDE rollout systems, training monitors — is **out of library
scope**; it belongs to user applications (at most Phase 4 example code).

## New modules (planned)

```
src/caegraph/physics/
├── equations.py     # PDE residuals
└── constraints.py   # physics-informed loss terms (PhysicsLoss)

src/caegraph/models/
├── encoders.py      # mesh/graph encoders
├── processors.py    # message-passing cores (PyG-based)
├── decoders.py      # field decoders
└── trainer.py       # Trainer: train/eval/checkpoint orchestration
```

## Planned public APIs

- `Model` (encode–process–decode contract), `Trainer` (already in Design UML)
- `PhysicsLoss` consumed by physics-informed models (models → physics,
  never reverse)

## Validation focus

- End-to-end train/inference on synthetic benchmark (small ruled mesh,
  analytic solution as ground truth)
- Loss convergence sanity + reproducibility under fixed seed

## Rules

- Thin wrappers over PyG; no reimplementation of message passing.
- Trainer is framework-API only: logging via `caegraph.utils`, no
  wandb/tensorboard hard dependency.

## Depends on

Phase 2 (graphs/datasets); `physics` depends only on core/utils.
