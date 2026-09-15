"""Topology subsystem of the canonical domain core (ADR-014/018).

The topology subsystem is an *optional semantic provider* referenced
by :class:`~caegraph.core.CAEGraph` — first-class for cell-based
discretizations (FEM/FVM), absent for mesh-free ones. It hosts the
cell-type vocabulary :class:`~caegraph.core.topology.CellType` and
the canonical cell-based topology model
:class:`~caegraph.core.topology.Mesh`.
"""

from caegraph.core.topology.celltype import CellType
from caegraph.core.topology.mesh import Mesh, canonical_facet_nodes

__all__ = ["CellType", "Mesh", "canonical_facet_nodes"]
