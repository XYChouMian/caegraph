"""Abstract mesh loading pipeline: source normalization (ADR-012).

:class:`AbstractMeshLoader` freezes the stable five-step pipeline of
ADR-012 decision 1 — obtain a source representation, perform
source-specific normalization, build the canonical topology according
to ADR-014, validate it, and return the :class:`~caegraph.core.Mesh`
topology representation consumed by representation builders (ADR-015).

The stable public surface is exactly :meth:`AbstractMeshLoader.__call__`.
The protected hooks are adapter implementation details (ADR-012:
neither their count nor their names are frozen); they are not part of
the public contract and may change without an architecture decision.

Source-group semantics follow ADR-012 decision 2: ``topo_dim`` is the
highest supported dimension among the recognized source-cell
candidates (never derived from groups); ``dim == topo_dim`` entities
form the canonical cell space, ``dim == topo_dim - 1`` entities are
facet candidates, and lower-dimensional entities are diagnosed and
excluded from the canonical topology (ADR-014 decision 2). Explicit
canonical facets are the adapter-declared subset of the facet
candidates (ADR-014 decision 2: only facets that need to keep
independent semantics or stable references enter the facet table);
domain groups carry global cell IDs on the Mesh, boundary/interface
source groups travel as metadata — global facet IDs preserved for
downstream region construction (ADR-012 decision 3, ADR-014 decision 7
metadata slot; ``BoundaryManager`` lives on the representation layer).

complete_coverage / complete_partition are caller-declared semantics
(ADR-014 8b — deliberately no API yet): loaders never declare them.
"""

from __future__ import annotations

import os
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from caegraph.core.topology.celltype import CellType
from caegraph.core.topology.mesh import Mesh

__all__ = ["AbstractMeshLoader"]

_METADATA_BOUNDARY_GROUPS = "boundary_source_groups"


@dataclass(frozen=True)
class _SourceBlock:
    """Recognized block of same-type source entities (implementation detail).

    ``connectivity`` rows already carry global node identifiers of the
    normalized source node space.
    """

    cell_type: CellType
    connectivity: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class _SourceGroup:
    """Named source group with raw member indices (implementation detail).

    ``members`` are indices into the recognized source-entity stream
    (blocks in order, entities in order) — the shared build resolves
    them to canonical global cell/facet IDs after the dimension
    classification.
    """

    name: str
    dim: int
    members: tuple[int, ...]


@dataclass(frozen=True)
class _NormalizedSource:
    """Format-neutral normalized source (implementation detail).

    The intermediate between the format-specific normalization (step 2)
    and the shared canonical build (step 3) of the ADR-012 pipeline.
    """

    name: str
    nodes: np.ndarray
    blocks: tuple[_SourceBlock, ...]
    groups: tuple[_SourceGroup, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class AbstractMeshLoader(ABC):
    """Cross-format loading pipeline producing canonical topology (ADR-012).

    Subclasses implement the two format-specific protected hooks and
    inherit the stable pipeline; classification, canonical assembly and
    validation after normalization are shared so the ADR-014 build
    semantics are never duplicated per format (ADR-012 decision 1).
    """

    def __call__(self, path: str | os.PathLike[str]) -> Mesh:
        """Load ``path`` and return the validated canonical Mesh.

        The stable ADR-012 pipeline: ① obtain the source
        representation; ② perform source-specific normalization; ③
        build the canonical topology according to ADR-014; ④ validate
        it; ⑤ return the Mesh topology representation.

        Args:
            path: Filesystem path of the source file.

        Returns:
            The validated canonical :class:`~caegraph.core.Mesh`.

        Raises:
            ValueError: If the source cannot be read or normalized
                (unreadable file, unsupported element type, malformed
                topology — no supported cell entities), or if the
                assembled topology violates an ADR-014 8a invariant.
        """
        source = self._load_source(Path(path))
        normalized = self._normalize_source(source)
        mesh = self._build_topology(normalized)
        mesh.validate()
        return mesh

    @abstractmethod
    def _load_source(self, path: Path) -> Any:
        """Obtain the source representation of ``path`` (pipeline step ①).

        Implementation detail — not a public contract; the returned
        object is the format-specific source representation and never
        crosses the io layer.
        """

    @abstractmethod
    def _normalize_source(self, source: Any) -> _NormalizedSource:
        """Normalize ``source`` into the format-neutral form (step ②).

        Implementation detail — not a public contract. Recognition of
        source cell types into the canonical :class:`~caegraph.core.
        topology.CellType` vocabulary, block-local to global node ID
        resolution, local-node convention normalization and source-group
        extraction all happen here (ADR-012 decision 3).
        """

    def _build_topology(self, normalized: _NormalizedSource) -> Mesh:
        """Assemble and return the canonical Mesh (pipeline steps ③④).

        Shared across formats (ADR-012: the build semantics after the
        normalization step are never duplicated per format).
        """
        blocks = normalized.blocks
        if not blocks:
            raise ValueError(
                "source contains no supported cell entities; the canonical "
                "topology requires at least one recognized cell"
            )
        topo_dim = max(block.cell_type.dim for block in blocks)

        cells: list[tuple[CellType, tuple[int, ...]]] = []
        facet_candidates: list[tuple[int, CellType, tuple[int, ...]]] = []
        entity_to_cell: dict[int, int] = {}
        cell_id = 0
        entity_index = 0
        for block in blocks:
            for connectivity in block.connectivity:
                if block.cell_type.dim == topo_dim:
                    entity_to_cell[entity_index] = cell_id
                    cells.append((block.cell_type, connectivity))
                    cell_id += 1
                elif block.cell_type.dim == topo_dim - 1:
                    facet_candidates.append(
                        (entity_index, block.cell_type, connectivity)
                    )
                entity_index += 1

        domain_groups: dict[str, np.ndarray] = {}
        boundary_groups: dict[str, tuple[int, ...]] = {}
        declared_facet_entities: set[int] = set()
        for group in normalized.groups:
            if group.dim == topo_dim:
                domain_groups[group.name] = np.array(
                    sorted(entity_to_cell[member] for member in group.members),
                    dtype=np.int64,
                )
            elif group.dim == topo_dim - 1:
                declared_facet_entities.update(group.members)
                boundary_groups[group.name] = tuple(sorted(group.members))
            else:
                warnings.warn(
                    f"source group {group.name!r} has dim {group.dim} "
                    f"< topo_dim - 1 ({topo_dim - 1}) and is excluded from "
                    "the canonical topology (ADR-012 decision 2)",
                    UserWarning,
                    stacklevel=3,
                )

        entity_to_facet: dict[int, int] = {}
        facet_types: list[int] = []
        facet_connectivity: list[tuple[int, ...]] = []
        for entity_index, facet_type, connectivity in facet_candidates:
            if entity_index not in declared_facet_entities:
                continue
            entity_to_facet[entity_index] = len(facet_connectivity)
            facet_types.append(facet_type.code)
            facet_connectivity.append(connectivity)

        face_cells: dict[frozenset[int], list[int]] = {}
        for cell_id, (cell_type, connectivity) in enumerate(cells):
            for face in cell_type.faces:
                key = frozenset(connectivity[local] for local in face)
                face_cells.setdefault(key, []).append(cell_id)
        facet_cells = [
            tuple(face_cells[frozenset(connectivity)])
            for connectivity in facet_connectivity
        ]

        for group_name, members in boundary_groups.items():
            boundary_groups[group_name] = tuple(
                sorted(entity_to_facet[member] for member in members)
            )
        metadata = dict(normalized.metadata)
        if boundary_groups:
            metadata[_METADATA_BOUNDARY_GROUPS] = boundary_groups

        return Mesh(
            normalized.name,
            nodes=normalized.nodes,
            topo_dim=topo_dim,
            cell_types=[cell_type.code for cell_type, _ in cells],
            cells=[node for _, connectivity in cells for node in connectivity],
            cell_offsets=np.cumsum(
                [0] + [len(connectivity) for _, connectivity in cells]
            ),
            facet_types=facet_types,
            facets=[
                node for connectivity in facet_connectivity for node in connectivity
            ],
            facet_offsets=np.cumsum([0] + [len(entry) for entry in facet_connectivity]),
            facet_cells=facet_cells,
            domain_groups=domain_groups,
            metadata=metadata,
        )
