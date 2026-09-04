# Architecture Overview

This page summarizes the architecture; the binding specification lives in
[`architecture/ARCHITECTURE.md`](https://github.com/XYChouMian/caegraph/blob/main/architecture/ARCHITECTURE.md).

## Design philosophy

- Modular design — one responsibility per subpackage
- Reusable components — small, composable building blocks
- Clear abstraction — documented, reviewed abstractions only
- API stability — documented APIs are contracts
- Documentation consistency — docs generated from code

## Package map

| Package | Responsibility | Depends on |
| --- | --- | --- |
| `caegraph.core` | base abstractions, registries, shared types | — |
| `caegraph.data` | CAE data loading, mesh & graph representations, datasets | core |
| `caegraph.models` | GNN components, physics-informed models, Trainer | core, data |
| `caegraph.physics` | PDE residuals, physics losses, units | core |
| `caegraph.visualization` | mesh/field/graph plotting | core, data |
| `caegraph.utils` | logging, IO, reproducibility helpers | — |

## UML dual system

- **Design UML** (`architecture/design/`) — the planned design.
- **Generated UML** (`diagrams/generated/`) — the real state of the code.

See the [UML guide](https://github.com/XYChouMian/caegraph/blob/main/architecture/UML_GUIDE.md).
