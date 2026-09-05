# CAEGraph

**A workflow framework bridging CAE simulation and Physics AI.**

CAEGraph converts framework-independent engineering truth into PyG-native graph
representations, supports GNN training for engineering problems, runs neural
simulation on new meshes, and assimilates experimental observations.

```
CAE Data → Graph Representation → GNN Training → Neural Simulation → Assimilation
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
