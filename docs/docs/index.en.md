# CAEGraph

**A PyG-style graph computation framework for CAE data.**

CAEGraph connects CAE data structures, mesh representations, graph
representations, datasets, and GNN / physics-informed learning models.

```
CAE Data → Mesh → Graph → Dataset → Model → Training/Inference → Visualization
```

!!! note "Project status"

    CAEGraph is in **Phase 1 (Core Data Structures)**. The Phase 0 package
    skeleton, architecture specification, UML system, documentation and CI are
    complete. Shared core abstractions are being implemented; CAE/GNN algorithms
    remain planned.

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
