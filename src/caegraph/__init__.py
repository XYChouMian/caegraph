"""CAEGraph: data infrastructure between CAE software and graph ML.

CAEGraph converts computational-engineering data (meshes, fields,
boundary conditions, physics metadata) into unified graph
representations and provides standard data interfaces for GNN /
physics-informed AI backends (ADR-007).

This is the package entry point. Subpackages are exposed lazily as they
are implemented.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
