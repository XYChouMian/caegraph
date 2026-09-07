# CAEGraph

A CAE-to-Physics-AI workflow framework built for the PyG ecosystem.

CAEGraph connects **CAE data → canonical graph representation → GNN training → neural simulation across different discretizations → experimental-data assimilation**. It normalizes heterogeneous CAE sources into **CAEGraph**, the graph-native canonical domain representation (ADR-015), and reaches learning backends — PyTorch Geometric today — through DataGraph adapters, keeping the engineering truth framework-independent.

> **Status: Pre-Alpha (Phase 2 — CAE Data Pipeline, in progress).** The Phase 1 core vocabulary (`BaseObject`, registry, shared enums, logging) is complete. The architecture has adopted ADR-015 (CAEGraph as the canonical domain representation; Mesh repositioned as a topology subsystem); the topology vocabulary `CellType` has landed, and the CAEGraph core plus the data band follow its design. GNN training utilities remain planned.

## Features (planned)

- **CAE data band** — CAEGraph canonical representation with topology (Mesh, cell-based), Field and boundary vocabularies; loaders, geometry services, representation construction (meshes, grids, particles), DataGraph adapters (PyG), transforms and datasets
- **Physics AI utilities** — physics losses, observation assimilation and CAE-aware training workflow components without replacing user training loops
- **Neural simulation** — pretrained models across different discretizations, field reconstruction and VTK write-back
- Built on [PyTorch](https://pytorch.org) and [PyTorch Geometric](https://pyg.org), without introducing an alternative graph backend, Trainer or solver abstraction

## Installation

CAEGraph requires Python 3.10 or later. The canonical development environment uses Python 3.10, while CI also verifies Python 3.11 compatibility.

```bash
pip install -e .
```

For development (docs, tests, linting):

```bash
pip install -e ".[dev,docs]"
```

## Quick start

```python
import caegraph

print(caegraph.__version__)
```

## Project layout

```
caegraph/
├── src/caegraph/        # source code (src-layout)
├── tests/               # pytest test suite
├── docs/                # MkDocs documentation site
├── architecture/        # architecture spec + design UML
├── diagrams/generated/  # UML generated from code
├── .agent/skills/       # agent development standards
└── .github/workflows/   # CI
```

## Development principles

Every contribution must keep seven things consistent:

```
Code ⇔ Architecture ⇔ UML ⇔ Documentation ⇔ Testing ⇔ Environment ⇔ Release
```

See [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) for details.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
