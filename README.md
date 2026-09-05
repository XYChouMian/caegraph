# CAEGraph

A CAE-to-Physics-AI workflow framework built for the PyG ecosystem.

CAEGraph connects **CAE data → graph representations → GNN training → neural
simulation on new meshes → experimental-data assimilation**. It keeps
engineering truth framework-independent while extending PyTorch Geometric for
computational engineering.

> **Status: Pre-Alpha (Phase 1 — Core Data Structures, in progress).** The
> Phase 0 foundation is complete. Work has begun on the shared core
> abstractions; CAE/GNN algorithms remain planned and are not implemented.

## Features (planned)

- **CAE data band** — Mesh/Field/Boundary truth, loaders, geometry services,
  PyG-native graph construction, transforms and datasets
- **Physics AI utilities** — physics losses, observation assimilation and
  CAE-aware training workflow components without replacing user training loops
- **Neural simulation** — pretrained models on new meshes, field reconstruction
  and VTK write-back
- Built on [PyTorch](https://pytorch.org) and
  [PyTorch Geometric](https://pyg.org), without introducing an alternative graph
  backend, Trainer or solver abstraction

## Installation

CAEGraph requires Python 3.10 or later. The canonical development environment
uses Python 3.10, while CI also verifies Python 3.11 compatibility.

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
