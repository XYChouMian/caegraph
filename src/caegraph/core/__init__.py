"""Framework-independent domain vocabulary of CAEGraph.

This package hosts the shared vocabulary of the engineering domain
core: :class:`~caegraph.core.BaseObject` (identity, metadata and
validation contract for domain-truth objects such as the Phase 2
``Mesh`` and ``Field``), the name-keyed
:class:`~caegraph.core.Registry` used by loaders and transforms, and
the shared enums :class:`~caegraph.core.BoundaryType`,
:class:`~caegraph.core.NodeCategory` (ADR-007) and
:class:`~caegraph.core.CellType` (ADR-014).

The core layer stays torch-free and PyG-free forever; the PyG boundary
starts at :mod:`caegraph.graph` (ADR-007 D2).
"""

from caegraph.core.base import BaseObject
from caegraph.core.celltype import CellType
from caegraph.core.enums import BoundaryType, NodeCategory
from caegraph.core.registry import Registry

__all__ = ["BaseObject", "BoundaryType", "CellType", "NodeCategory", "Registry"]
