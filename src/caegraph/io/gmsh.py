"""Gmsh source adapter: ``.msh`` normalization into canonical Mesh (ADR-012/013).

:class:`GmshLoader` is the first concrete
:class:`~caegraph.io.AbstractMeshLoader`. It reads Gmsh ``.msh``
sources through the external IO engine meshio (ADR-013 — provisional,
lazy-imported so importing this module never imports meshio) and
performs the ADR-012 normalization obligations:

- meshio/Gmsh element types are recognized into the canonical
  :class:`~caegraph.core.topology.CellType` vocabulary; unsupported
  element types are rejected;
- meshio global point indices become the canonical node IDs — raw
  Gmsh node tags never reach the canonical topology, and no meshio
  type crosses the io layer (ADR-013 decision 3);
- source local-node ordering is normalized to the CAEGraph-owned
  :class:`~caegraph.core.topology.CellType` local-node convention;
- cell and facet identities are enumerated canonically across blocks;
- Gmsh physical groups (``field_data`` name ↔ tag mapping plus the
  per-element ``gmsh:physical`` tags) become named source groups,
  classified by dimension per ADR-012 decision 2.

Gmsh physical-group data and CAEGraph field realizations are entirely
different concepts: this adapter never creates
:class:`~caegraph.core.FieldData` objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from caegraph.core.topology.celltype import CellType
from caegraph.io.base import (
    AbstractMeshLoader,
    _NormalizedSource,
    _SourceBlock,
    _SourceGroup,
)

__all__ = ["GmshLoader"]

_GMSH_PHYSICAL_KEY = "gmsh:physical"


_GMSH_TO_CELLTYPE: dict[str, CellType] = {
    # meshio block type string -> canonical CellType. The identity of
    # the canonical vocabulary is ADR-014 decision 4; meshio/Gmsh
    # type strings die inside the io layer.
    "line": CellType.LINE2,
    "triangle": CellType.TRI3,
    "quad": CellType.QUAD4,
    "tetra": CellType.TET4,
    "pyramid": CellType.PYR5,
    "wedge": CellType.WEDGE6,
    "hexahedron": CellType.HEX8,
}


class GmshLoader(AbstractMeshLoader):
    """Concrete loader for Gmsh ``.msh`` sources via meshio (ADR-013).

    The loader consumes Gmsh physical groups only as named source
    groups: domain groups (``dim == topo_dim``) surface as Mesh
    domain groups carrying global cell IDs; boundary/interface groups
    (``dim == topo_dim - 1``) declare the canonical facet subset and
    travel as Mesh metadata carrying global facet IDs for downstream
    region construction. Mathematical boundary categories are user
    declarations (ADR-010/012) — no name-to-category inference happens
    here, and no ``BoundarySpec``/condition is ever produced.
    """

    def _load_source(self, path: Path) -> Any:
        """Read ``path`` through meshio, wrapping engine failures (step ①).

        meshio is imported lazily inside the read (ADR-013 decision 4):
        registration and module import stay meshio-free. Engine-side
        failures (unreadable file, parse errors) surface as a single
        stable :class:`ValueError` at the io boundary — the meshio
        exception type is never part of the CAEGraph contract.
        """
        try:
            import meshio  # type: ignore[import-untyped]
        except ImportError as error:  # pragma: no cover - dependency is declared
            raise ValueError(
                "the gmsh loader requires the meshio dependency (ADR-013)"
            ) from error
        try:
            return meshio.read(path)
        except Exception as error:
            raise ValueError(
                f"failed to read Gmsh source {str(path)!r} through the "
                "io engine (ADR-013)"
            ) from error

    def _normalize_source(self, source: Any) -> _NormalizedSource:
        """Normalize a meshio source into the format-neutral form (step ②)."""
        import meshio  # type: ignore[import-untyped]

        if not isinstance(source, meshio.Mesh):
            raise ValueError("GmshLoader normalizes meshio Mesh sources only (ADR-013)")

        points = np.asarray(source.points, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] not in (2, 3) or points.shape[0] == 0:
            raise ValueError("Gmsh source carries no usable node coordinates")
        if points.shape[1] == 2:
            points = np.hstack([points, np.zeros((points.shape[0], 1))])

        blocks: list[_SourceBlock] = []
        entity_index = 0
        block_entity_starts: list[int] = []
        block_dims: list[int] = []
        for cell_block in source.cells:
            cell_type = _GMSH_TO_CELLTYPE.get(cell_block.type)
            if cell_type is None:
                raise ValueError(
                    f"unsupported source element type {cell_block.type!r} - "
                    "it is not part of the canonical CellType vocabulary "
                    "(ADR-014 decision 4)"
                )
            connectivity = np.asarray(cell_block.data)
            if connectivity.ndim != 2 or connectivity.shape[1] != cell_type.node_count:
                raise ValueError(
                    f"source block {cell_block.type!r} has malformed "
                    f"connectivity: expected {cell_type.node_count} nodes "
                    f"per entity, got shape {connectivity.shape}"
                )
            block_entity_starts.append(entity_index)
            block_dims.append(cell_type.dim)
            blocks.append(
                _SourceBlock(
                    cell_type=cell_type,
                    connectivity=tuple(
                        tuple(int(node) for node in row) for row in connectivity
                    ),
                )
            )
            entity_index += connectivity.shape[0]

        return _NormalizedSource(
            name=_source_name(source),
            nodes=points,
            blocks=tuple(blocks),
            groups=tuple(_extract_groups(source, block_entity_starts, block_dims)),
            metadata={"source_format": "gmsh"},
        )


def _source_name(source: Any) -> str:
    """Derive a Mesh name from the source file stem (fallback: generic)."""
    file_path = getattr(source, "file_path", None)
    if file_path:
        return Path(str(file_path)).stem
    return "gmsh_source"


def _extract_groups(
    source: Any, block_entity_starts: list[int], block_dims: list[int]
) -> list[_SourceGroup]:
    """Resolve Gmsh physical groups into named source groups (ADR-012).

    ``field_data`` maps group names to ``(physical tag, dimension)``;
    per-element physical tags arrive in ``cell_data['gmsh:physical']``
    aligned with the cell blocks. Group members are recorded as
    indices into the recognized source-entity stream; the dimension
    classification itself happens in the shared build.
    """
    field_data = getattr(source, "field_data", None) or {}
    if not field_data:
        return []
    physical = (getattr(source, "cell_data", None) or {}).get(_GMSH_PHYSICAL_KEY)
    if physical is None:
        return []

    groups: list[_SourceGroup] = []
    for name, tag_and_dim in field_data.items():
        tag, dim = int(tag_and_dim[0]), int(tag_and_dim[1])
        members: list[int] = []
        for block_index, start in enumerate(block_entity_starts):
            if block_dims[block_index] != dim or block_index >= len(physical):
                continue
            tags = np.asarray(physical[block_index]).reshape(-1)
            for offset in np.flatnonzero(tags == tag):
                members.append(start + int(offset))
        if members:
            groups.append(_SourceGroup(name=name, dim=dim, members=tuple(members)))
    return groups
