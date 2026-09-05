"""CAEGraph: bridging CAE simulation and physics AI.

CAEGraph provides a CAE -> GNN -> AI workflow: converting CAE data
(meshes, fields, boundary conditions, physics metadata) into graph
representations, enabling GNN training on engineering problems, running
neural simulation on new meshes with pretrained models, and correcting
predictions with experimental observations (ADR-008).

This is the package entry point. Subpackages are exposed lazily as they
are implemented.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
