"""Framework-independent domain vocabulary of CAEGraph.

This package hosts the engineering domain core: the canonical domain
representation :class:`~caegraph.core.CAEGraph` (ADR-015/018),
:class:`~caegraph.core.BaseObject` (identity, metadata and validation
contract for domain-truth objects such as ``Mesh`` and
:class:`~caegraph.core.Field`), the semantic-region vocabulary of
:mod:`caegraph.core.boundary` (regions, declarations, registry;
ADR-010/011/018), the name-keyed :class:`~caegraph.core.Registry`
used by loaders and transforms, and the shared enums
:class:`~caegraph.core.BoundaryType`, :class:`~caegraph.core.NodeCategory`
(ADR-007) and :class:`~caegraph.core.CellType` (ADR-014).

The core layer is torch-only and PyG-free forever; the PyG boundary
starts at :mod:`caegraph.graph` (ADR-007 D2).
"""

from caegraph.core.base import BaseObject
from caegraph.core.boundary import BoundaryManager, BoundaryRegion, BoundarySpec
from caegraph.core.caegraph import CAEGraph
from caegraph.core.celltype import CellType
from caegraph.core.enums import BoundaryType, NodeCategory
from caegraph.core.field import Field
from caegraph.core.registry import Registry

__all__ = [
    "BaseObject",
    "BoundaryManager",
    "BoundaryRegion",
    "BoundarySpec",
    "BoundaryType",
    "CAEGraph",
    "CellType",
    "Field",
    "NodeCategory",
    "Registry",
]
