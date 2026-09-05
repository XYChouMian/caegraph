# Phase 4 — Neural Simulation & Release

Status: Planned

Goal: **R3** — any mesh + a pretrained GNN → generated data (the AI
counterpart of the CAE workflow) — then the v1.0 release.

## New modules (planned)

```
src/caegraph/inference/
├── simulator.py     # mesh + pretrained model -> fields:
│                    #   graph -> forward -> field reconstruction
└── rollout.py       # transient rollout LOOP harness;
                     #   numerical schemes stay model-side (ADR-007 D5)

examples/            # concrete model architectures + end-to-end
                     # applications live here — never inside src/caegraph
                     # (no GNN zoo, ADR-008)
```

## Planned public APIs

- `Simulator`: `mesh + model → fields` neural-simulation workflow
- `Rollout`: transient loop harness (model-defined stepping)
- Optional post-inference `Correction` application (assimilation from
  Phase 3, R4 at deployment time)
- VTK write-back of predicted fields

The VTK writer is implemented in Phase 2. Phase 4 reuses it to close the
prediction-export loop; it is not reimplemented here.

## Scope

1. **Neural simulation (R3)**
   - Inference on meshes unseen during training (mesh-agnostic
     transforms from Phase 2 are the enabling mechanism)
   - Rollout harness for transient models; steady single-pass for others
   - Field reconstruction + VTK export for ParaView visualization
   - Before calling the model, Simulator validates the input contract:
     required node/edge features, units, boundary encoding, normalization
     state, supported topology and schema version. Incompatible inputs fail
     with an explicit validation error rather than reaching model execution.
2. **API freeze**
   - Full public-API audit (Reviewer); deprecation policy active
3. **Packaging polish**
   - Single version source; `python -m build` + clean-wheel verification
   - Docs: tutorials for the full CAE → GNN → AI workflow, bilingual parity
4. **Applications (community-facing, examples only)**
   - CFD surrogate, ROM, multiphysics examples

## Exit criteria

- Rollout on an unseen mesh demonstrated and validated (R3)
- Incompatible feature/unit/boundary/normalization/topology/schema inputs are
  rejected before model execution
- VTK round-trip: mesh → graph → prediction → VTK → ParaView
- Release Agent checklist fully green for `1.0.0`

## Depends on

Phase 3 complete + validation green.
