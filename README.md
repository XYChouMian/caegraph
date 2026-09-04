# CAEGraph

A PyG-style graph computation framework for CAE (Computer-Aided Engineering) data.

CAEGraph connects **CAE data structures → mesh representations → graph
representations → datasets → GNN / physics-informed learning models →
visualization** in a single, well-architected Python framework.

> **Status: Pre-Alpha (Phase 0 — Foundation).** The package skeleton,
> architecture specification, UML system, documentation and testing
> infrastructure are in place. No CAE/GNN algorithms are implemented yet.

## Features (planned)

- **Data layer** — CAE result loading, mesh representation, graph conversion
- **Model layer** — GNN building blocks and physics-informed models
- **Physics layer** — PDE residuals and physics-informed losses
- **Visualization** — mesh, field and graph plotting
- Built on [PyTorch](https://pytorch.org) and
  [PyTorch Geometric](https://pyg.org)

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

Every contribution must keep five things consistent:

```
Code → Architecture → UML → Documentation → Testing
```

See [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) for details.

## License

MIT — see [LICENSE](LICENSE).
