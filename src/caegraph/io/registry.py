"""Format registry for mesh loaders on the core Registry (ADR-013).

Loaders register under their format name (lowercase software name per
ADR-013 — ``"gmsh"`` first) in the name → factory mechanism of
:class:`~caegraph.core.Registry`; no second registry abstraction exists.
Registration never imports the IO engine — the format adapters import
meshio lazily inside their read hooks (ADR-013 decision 4).
"""

from __future__ import annotations

from caegraph.core import Registry
from caegraph.io.base import AbstractMeshLoader
from caegraph.io.gmsh import GmshLoader

__all__ = ["FORMAT_REGISTRY"]

FORMAT_REGISTRY: Registry[AbstractMeshLoader] = Registry("mesh loader")

FORMAT_REGISTRY.register("gmsh", GmshLoader)
