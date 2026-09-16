"""Representation construction and backend adaptation layer (ADR-016/017).

Phase 2 provides the cell-based mesh construction strategy
(:class:`~caegraph.graph.MeshRepresentationBuilder`, ADR-019); the
backend adapter lands with the adaptation slice (ADR-017).
"""

from caegraph.graph.builder import MeshRepresentationBuilder

__all__ = ["MeshRepresentationBuilder"]
