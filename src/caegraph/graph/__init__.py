"""Representation construction and backend adaptation layer (ADR-016/017).

Phase 2 provides the cell-based mesh construction strategy
(:class:`~caegraph.graph.MeshRepresentationBuilder`, ADR-019) and the
PyG backend adapter (:func:`~caegraph.graph.to_pyg_data`,
ADR-017/022).
"""

from caegraph.graph.builder import MeshRepresentationBuilder
from caegraph.graph.pyg import to_pyg_data

__all__ = ["MeshRepresentationBuilder", "to_pyg_data"]
