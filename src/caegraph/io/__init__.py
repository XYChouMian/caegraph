"""IO layer of CAEGraph (ADR-012/013).

Source normalization pipeline: format loaders turn external CAE
sources into the canonical :class:`~caegraph.core.Mesh` topology
representation consumed by representation builders (ADR-015). The
external IO engine (meshio, ADR-013 — provisional) is an
implementation detail behind the loaders and never crosses this
layer; mathematical boundary categories come from user-declared specs
only (ADR-012 decision 4 — the io layer never infers BoundaryType).

The layer is deliberately small: the loader abstraction, the format
registry on the core Registry, and the first source adapter. VTK
write-back arrives with its own slice.
"""

from caegraph.io.base import AbstractMeshLoader
from caegraph.io.gmsh import GmshLoader
from caegraph.io.registry import FORMAT_REGISTRY

__all__ = ["FORMAT_REGISTRY", "AbstractMeshLoader", "GmshLoader"]
