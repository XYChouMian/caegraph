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
| `caegraph.core` | domain truth: BaseObject, Mesh, Field; boundary vocabulary, registries, shared enums | — |
| `caegraph.geometry` | geometric services: metrics, edge features, interpolation | core |
| `caegraph.io` | loaders (gmsh first) and writers (VTK); format registry | core |
| `caegraph.graph` | `Graph(torch_geometric.data.Data)` neural representation + builders | core, geometry |
| `caegraph.transforms` | geometry / feature / physics transforms (BC encoding) | graph |
| `caegraph.dataset` | CAEDataset (PyG): collections, splits | graph, transforms |
| `caegraph.physics` | PDE residuals, physics losses, constraints | core, graph |
| `caegraph.models` | Model interface + CAE model utilities (no GNN zoo) | core, graph, physics |
| `caegraph.assimilation` | observation / correction operators (data assimilation) | core, graph, physics |
| `caegraph.workflow` | training utilities: loss assembly, CAE batch adaptation (no fit loop) | physics, models, assimilation, dataset |
| `caegraph.inference` | neural-simulation harness: simulator, rollout loop (numerics model-side) | models, assimilation, io |
| `caegraph.visualization` | mesh/field/graph plotting | core, io |
| `caegraph.utils` | logging, IO, reproducibility helpers | — |

## UML dual system

- **Design UML** (`architecture/design/`) — the planned design.
- **Generated UML** (`diagrams/generated/`) — the real state of the code.

See the [UML guide](https://github.com/XYChouMian/caegraph/blob/main/architecture/UML_GUIDE.md).
