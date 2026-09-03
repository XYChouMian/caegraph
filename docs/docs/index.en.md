# CAEGraph

**A PyG-style graph computation framework for CAE data.**

CAEGraph connects CAE data structures, mesh representations, graph
representations, datasets, and GNN / physics-informed learning models.

```
CAE Data → Mesh → Graph → Dataset → Model → Training/Inference → Visualization
```

!!! note "Project status"

    CAEGraph is in **Phase 0 (Foundation)**. The package skeleton, architecture
    specification, UML system, documentation and CI are in place. No CAE/GNN
    algorithms are implemented yet — all pages describe planned structure.

## Getting started

```bash
pip install -e .
```

```python
import caegraph
print(caegraph.__version__)
```

## Where to go next

- [Architecture overview](architecture/overview.md)
- [API reference](api/index.md)
- [Tutorials](tutorials/index.md)
- [Examples](examples/index.md)
