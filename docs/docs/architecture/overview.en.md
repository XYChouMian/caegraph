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
| `caegraph.core` | domain abstractions: BaseObject, Mesh, Graph, Field; registries, shared enums | — |
| `caegraph.geometry` | geometric services: metrics, edge features, interpolation | core |
| `caegraph.io` | loaders (gmsh first) and writers (VTK); format registry | core |
| `caegraph.graph` | graph construction (node/cell graphs) and transforms | core, geometry |
| `caegraph.integrations` | backend adapters: PyG `to_pyg()`, PyG datasets — the only PyG import site | core, graph |
| `caegraph.dataset` | collections, transforms, splits | core, graph, integrations |
| `caegraph.physics` | PDE residuals, physics losses, constraints | core |
| `caegraph.models` | composable GNN components, physics-informed models, Trainer | core, dataset, integrations, physics |
| `caegraph.visualization` | mesh/field/graph plotting | core, io, models |
| `caegraph.utils` | logging, IO, reproducibility helpers | — |

## UML dual system

- **Design UML** (`architecture/design/`) — the planned design.
- **Generated UML** (`diagrams/generated/`) — the real state of the code.

See the [UML guide](https://github.com/XYChouMian/caegraph/blob/main/architecture/UML_GUIDE.md).
