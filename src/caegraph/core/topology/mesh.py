"""Canonical cell-based topology model of the topology subsystem (ADR-014)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from numbers import Integral
from types import MappingProxyType
from typing import Any

import numpy as np

from caegraph.core.base import BaseObject
from caegraph.core.topology.celltype import CellType

__all__ = ["Mesh", "canonical_facet_nodes"]


def canonical_facet_nodes(nodes: Sequence[int]) -> tuple[int, ...]:
    """Return the winding-free canonical representation of one facet.

    The canonical form is the lexicographically smallest tuple among
    all cyclic rotations of the given order and of its reversal
    (ADR-014 decision 3). Facet connectivity is winding-free: no
    intrinsic facet normal is implied — normals are always defined
    relative to a specified adjacent cell — and identical facets
    entering through different source orderings or windings collapse
    to the same representation.

    Args:
        nodes: Node identifiers of one facet, in arbitrary order.

    Returns:
        The canonical (winding-free) node tuple.

    Raises:
        ValueError: If ``nodes`` is empty — every facet must carry at
            least one node identifier.

    Examples:
        >>> canonical_facet_nodes([5, 8, 3])
        (3, 5, 8)
        >>> canonical_facet_nodes([3, 8, 5]) == canonical_facet_nodes([5, 8, 3])
        True
    """
    if len(nodes) == 0:
        raise ValueError("facet connectivity must contain at least one node identifier")
    return min(
        order[start:] + order[:start]
        for order in (tuple(nodes), tuple(reversed(nodes)))
        for start in range(len(order))
    )


def _as_int_array(values: Iterable[int], label: str) -> np.ndarray:
    """Coerce ``values`` to an integer ndarray, rejecting other dtypes.

    Boolean identifiers are rejected (``True == 1`` makes silent
    bool-to-int coercion a classic pitfall), as are 0-dimensional
    scalar inputs.

    Raises:
        TypeError: If the input does not consist of integers (floats
            are never silently truncated), is boolean, or is not
            one-dimensional.
    """
    array = np.asarray(values)
    if array.ndim != 1:
        raise TypeError(f"{label} must be a one-dimensional integer array")
    if array.size == 0:
        return array.astype(np.int64)
    if not np.issubdtype(array.dtype, np.integer):
        raise TypeError(f"{label} must contain integers, got dtype {array.dtype!r}")
    return array.astype(np.int64)


class Mesh(BaseObject):
    """Topology-rich cell-based discretization representation (ADR-014/015).

    ``Mesh`` is the cell-based topology representation supported by
    the topology subsystem (FEM/FVM), referenced by
    :class:`~caegraph.core.CAEGraph` as an *optional semantic
    provider*. It owns the topology facts only — nodes, canonical
    cells, explicit facets and their validated cell adjacency — plus
    plain domain-group data; fields and semantic regions live on the
    representation layer (ADR-018).

    Mesh does not construct CAEGraph relations or backend graph
    objects — representation construction belongs to representation
    builders (ADR-016; the topology subsystem deliberately provides
    no ``to_graph()``-style conversion). Exposed arrays are read-only
    views of the frozen storage, never defensive copies.

    Storage follows the canonical contracts of ADR-014:

    - **Canonical identity**: entity IDs refer to canonical storage —
      ``nodes`` rows are global node IDs, cells and facets are indexed
      by their CSR position — never to loader/backend block-local
      indices.
    - **Cells**: ``cell_types`` (explicit integer codes per
      :class:`~caegraph.core.topology.CellType`) + flat connectivity
      ``cells`` + ``cell_offsets`` (CSR). Type-grouped blocks are
      derived views only; this triple is the single source of truth.
    - **Facets**: a parallel canonical CSR table (``facet_types`` /
      ``facets`` / ``facet_offsets``) holding only explicitly declared
      boundary/interface facets, plus ``facet_cells`` — the ragged,
      *validated* cell adjacency computed at build time.
    - **Winding-free facets**: facet connectivity is canonicalized at
      construction via :func:`canonical_facet_nodes`; cell
      connectivity retains oriented local-topology semantics under
      the CAEGraph local-node convention (no backend numbering).
    - **Frozen structure**: ``nodes``/cells/facets/groups are frozen
      after construction + :meth:`validate`; exposed arrays are
      read-only and there are no mutation methods.

    Every storage member described under ``Args`` is exposed as a
    same-named read-only property (a view of the frozen storage,
    never a copy), alongside the ``n_nodes`` / ``n_cells`` /
    ``n_facets`` count conveniences and O(1) per-entity accessors —
    :meth:`cell_type`, :meth:`cell_nodes`, :meth:`facet_nodes` and
    :meth:`facet_adjacent_cells` — so callers never slice the CSR
    offset arrays by hand.

    Args:
        name: Non-empty mesh name.
        nodes: Coordinates as a 2D array-like of shape
            ``(n_nodes, 3)`` and dtype float64 (canonical 3D
            storage: 2D meshes also store three coordinate columns —
            ``topo_dim`` never travels via the column count).
        topo_dim: Common topological dimension of all canonical
            cells (1, 2 or 3).
        cell_types: Explicit integer cell-type codes, one per cell.
        cells: Flat cell connectivity (global node IDs).
        cell_offsets: CSR offsets, ``n_cells + 1`` entries starting
            at 0.
        facet_types: Optional explicit-integer facet-type codes
            (boundary/interface facets only; unnamed interior facets
            are deliberately absent, ADR-014 decision 2).
        facets: Optional flat facet connectivity; canonicalized at
            construction.
        facet_offsets: Optional CSR offsets of the facet table.
        facet_cells: Optional ragged cell adjacency, one entry per
            facet (``len >= 1``; ``== 1`` exterior candidates,
            ``== 2`` internal/interface, ``>= 3`` non-manifold).
        domain_groups: Optional mapping of group name to global cell
            IDs — plain cell-ID grouping metadata, not semantic
            regions (boundary/interface groups become
            ``BoundaryRegion`` objects downstream, ADR-012/018);
            coverage/partition semantics are caller-declared
            (ADR-014 8b — never mesh invariants).
        metadata: Optional free-form annotations.

    Raises:
        ValueError: If any ADR-014 8a invariant is violated (shapes,
            dtypes, CSR consistency, index bounds, dimension
            hierarchy, facet adjacency completeness or facet↔cell
            template matching).
        TypeError: If integer tables receive non-integer input,
            ``topo_dim`` is not an integer (bools rejected), or
            ``facet_cells`` entries contain non-integers.

    Examples:
        >>> mesh = Mesh(
        ...     "single_tri",
        ...     nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        ...     topo_dim=2,
        ...     cell_types=[CellType.TRI3.code],
        ...     cells=[0, 1, 2],
        ...     cell_offsets=[0, 3],
        ...     facet_types=[CellType.LINE2.code],
        ...     facets=[1, 0],
        ...     facet_offsets=[0, 2],
        ...     facet_cells=[[0]],
        ... )
        >>> mesh.n_nodes, mesh.n_cells, mesh.n_facets
        (3, 1, 1)
        >>> mesh.facets.tolist()  # canonical winding-free order
        [0, 1]
    """

    def __init__(
        self,
        name: str,
        *,
        nodes: Any,
        topo_dim: int,
        cell_types: Iterable[int],
        cells: Iterable[int],
        cell_offsets: Iterable[int],
        facet_types: Iterable[int] | None = None,
        facets: Iterable[int] | None = None,
        facet_offsets: Iterable[int] | None = None,
        facet_cells: Sequence[Sequence[int]] | None = None,
        domain_groups: Mapping[str, Iterable[int]] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Coerce, canonicalize and freeze the topology, then validate."""
        if not isinstance(topo_dim, int) or isinstance(topo_dim, bool):
            raise TypeError(
                f"topo_dim must be an integer (1, 2 or 3), "
                f"got {type(topo_dim).__name__}"
            )
        self._nodes = np.array(nodes, dtype=np.float64)
        self._topo_dim = int(topo_dim)
        self._cell_types = _as_int_array(cell_types, "cell_types")
        self._cells = _as_int_array(cells, "cells")
        self._cell_offsets = _as_int_array(cell_offsets, "cell_offsets")

        if facet_types is None and facets is None and facet_offsets is None:
            self._facet_types = np.empty(0, dtype=np.int64)
            self._facets = np.empty(0, dtype=np.int64)
            self._facet_offsets = np.zeros(1, dtype=np.int64)
        elif facet_types is None or facets is None or facet_offsets is None:
            raise ValueError(
                "facet table requires facet_types, facets and facet_offsets together"
            )
        else:
            self._facet_types = _as_int_array(facet_types, "facet_types")
            facet_conn = _as_int_array(facets, "facets")
            self._facet_offsets = _as_int_array(facet_offsets, "facet_offsets")
            offsets = self._facet_offsets
            if (
                offsets.size != self._facet_types.size + 1
                or int(offsets[0]) != 0
                or bool(np.any(np.diff(offsets) < 0))
                or int(offsets[-1]) != facet_conn.size
            ):
                raise ValueError("facet_offsets is not a valid CSR offset array")
            canonical = np.empty_like(facet_conn)
            for index in range(self._facet_types.size):
                start, end = int(offsets[index]), int(offsets[index + 1])
                canonical[start:end] = canonical_facet_nodes(
                    facet_conn[start:end].tolist()
                )
            self._facets = canonical

        if facet_cells is None:
            self._facet_cells: tuple[tuple[int, ...], ...] = ()
        else:
            entries: list[tuple[int, ...]] = []
            for entry in facet_cells:
                for value in entry:
                    if not isinstance(value, Integral):
                        raise TypeError("facet_cells entries must contain integers")
                entries.append(tuple(int(value) for value in entry))
            self._facet_cells = tuple(entries)

        groups: dict[str, np.ndarray] = {}
        if domain_groups is not None:
            for group_name, group_ids in domain_groups.items():
                if not isinstance(group_name, str) or not group_name.strip():
                    raise ValueError("domain group names must be non-empty strings")
                groups[group_name] = _as_int_array(
                    group_ids, f"domain group {group_name!r}"
                )
        self._domain_groups = groups

        for array in (
            self._nodes,
            self._cell_types,
            self._cells,
            self._cell_offsets,
            self._facet_types,
            self._facets,
            self._facet_offsets,
            *self._domain_groups.values(),
        ):
            array.setflags(write=False)

        super().__init__(name, metadata)

    # --- frozen structure -------------------------------------------------

    @property
    def topo_dim(self) -> int:
        """Common topological dimension of all canonical cells."""
        return self._topo_dim

    @property
    def nodes(self) -> np.ndarray:
        """Read-only coordinates, shape ``(n_nodes, 3)``, dtype float64."""
        return self._nodes

    @property
    def cell_types(self) -> np.ndarray:
        """Read-only explicit integer cell-type codes (one per cell)."""
        return self._cell_types

    @property
    def cells(self) -> np.ndarray:
        """Read-only flat cell connectivity (global node IDs)."""
        return self._cells

    @property
    def cell_offsets(self) -> np.ndarray:
        """Read-only CSR offsets of the cell table (``n_cells + 1``)."""
        return self._cell_offsets

    @property
    def facet_types(self) -> np.ndarray:
        """Read-only explicit integer facet-type codes (one per facet)."""
        return self._facet_types

    @property
    def facets(self) -> np.ndarray:
        """Read-only flat facet connectivity in canonical winding-free order."""
        return self._facets

    @property
    def facet_offsets(self) -> np.ndarray:
        """Read-only CSR offsets of the facet table (``n_facets + 1``)."""
        return self._facet_offsets

    @property
    def facet_cells(self) -> tuple[tuple[int, ...], ...]:
        """Validated ragged cell adjacency, one tuple of cell IDs per facet.

        Stored as an immutable ragged structure (tuple of tuples).
        """
        return self._facet_cells

    @property
    def domain_groups(self) -> Mapping[str, np.ndarray]:
        """Read-only view of domain groups (name -> global cell IDs)."""
        return MappingProxyType(self._domain_groups)

    @property
    def n_nodes(self) -> int:
        """Number of nodes."""
        return int(self._nodes.shape[0])

    @property
    def n_cells(self) -> int:
        """Number of canonical cells."""
        return int(self._cell_types.size)

    @property
    def n_facets(self) -> int:
        """Number of explicit canonical facets."""
        return int(self._facet_types.size)

    # --- O(1) canonical accessors ------------------------------------------

    def cell_type(self, index: int) -> CellType:
        """Return the :class:`CellType` member of cell ``index``."""
        return CellType.from_code(int(self._cell_types[index]))

    def cell_nodes(self, index: int) -> np.ndarray:
        """Return the connectivity slice (global node IDs) of cell ``index``."""
        start = int(self._cell_offsets[index])
        return self._cells[start : int(self._cell_offsets[index + 1])]

    def facet_nodes(self, index: int) -> np.ndarray:
        """Return the connectivity slice of facet ``index`` (canonical order)."""
        start = int(self._facet_offsets[index])
        return self._facets[start : int(self._facet_offsets[index + 1])]

    def facet_adjacent_cells(self, index: int) -> tuple[int, ...]:
        """Return the validated adjacent cell IDs of facet ``index``."""
        return self._facet_cells[index]

    # --- validation ---------------------------------------------------------

    def validate(self) -> None:
        """Enforce the ADR-014 8a topology-legality invariants, fail-fast.

        Checks (all unconditional): nodes shape/dtype (canonical 3D
        storage); CSR offset consistency of both tables; per-entity
        node counts against ``CellType``; index bounds; dimension
        hierarchy (cells ``dim == topo_dim``, facets
        ``dim == topo_dim - 1``); winding-free canonical facet order;
        facet adjacency completeness (every facet has at least one
        in-range, duplicate-free adjacent cell and matches a legal
        codim-1 face template of each adjacent cell); domain-group
        cell-ID bounds.

        Raises:
            ValueError: If any invariant is violated.
        """
        n_nodes = self._nodes.shape[0]
        if self._nodes.ndim != 2 or self._nodes.shape[1] != 3:
            raise ValueError("nodes must be a 2D array of shape (n_nodes, 3)")
        if self._nodes.dtype != np.dtype(np.float64):
            raise ValueError("nodes must be float64 (canonical 3D storage)")
        if n_nodes == 0:
            raise ValueError("nodes must contain at least one node")
        if self._topo_dim not in (1, 2, 3):
            raise ValueError("topo_dim must be 1, 2 or 3")

        n_cells = self._cell_types.size
        if n_cells == 0:
            raise ValueError("cells table must contain at least one cell")
        if self._cell_offsets.size != n_cells + 1:
            raise ValueError("cell_offsets must have n_cells + 1 entries")
        if int(self._cell_offsets[0]) != 0:
            raise ValueError("cell_offsets must start at 0")
        if int(self._cell_offsets[-1]) != self._cells.size:
            raise ValueError("cell_offsets[-1] must equal the cells length")
        cell_type_members = [self.cell_type(index) for index in range(n_cells)]
        expected_counts = np.array(
            [member.node_count for member in cell_type_members], dtype=np.int64
        )
        actual_counts = np.diff(self._cell_offsets)
        if not np.array_equal(actual_counts, expected_counts):
            raise ValueError(
                "cell connectivity sizes must match the CellType node counts"
            )
        for index, member in enumerate(cell_type_members):
            if member.dim != self._topo_dim:
                raise ValueError(
                    f"cell {index} has dim {member.dim} != topo_dim {self._topo_dim}"
                )
        if self._cells.size and (
            int(self._cells.min()) < 0 or int(self._cells.max()) >= n_nodes
        ):
            raise ValueError("cell connectivity references node ids out of range")

        n_facets = self._facet_types.size
        if self._facet_offsets.size != n_facets + 1:
            raise ValueError("facet_offsets must have n_facets + 1 entries")
        if int(self._facet_offsets[0]) != 0:
            raise ValueError("facet_offsets must start at 0")
        if int(self._facet_offsets[-1]) != self._facets.size:
            raise ValueError("facet_offsets[-1] must equal the facets length")
        for index in range(n_facets):
            facet_member = CellType.from_code(int(self._facet_types[index]))
            if facet_member.dim != self._topo_dim - 1:
                raise ValueError(
                    f"facet {index} has dim {facet_member.dim} != "
                    f"topo_dim - 1 ({self._topo_dim - 1})"
                )
            start, end = int(self._facet_offsets[index]), int(
                self._facet_offsets[index + 1]
            )
            if end - start != facet_member.node_count:
                raise ValueError(
                    f"facet {index} connectivity size must match "
                    f"{facet_member.node_count} nodes"
                )
            stored = self._facets[start:end].tolist()
            if tuple(stored) != canonical_facet_nodes(stored):
                raise ValueError(
                    f"facet {index} connectivity is not in canonical winding-free order"
                )
        if self._facets.size and (
            int(self._facets.min()) < 0 or int(self._facets.max()) >= n_nodes
        ):
            raise ValueError("facet connectivity references node ids out of range")

        if len(self._facet_cells) != n_facets:
            raise ValueError("facet_cells must have one entry per facet")
        for index, adjacency in enumerate(self._facet_cells):
            if not adjacency:
                raise ValueError(f"facet {index} has no adjacent cell")
            if len(set(adjacency)) != len(adjacency):
                raise ValueError(f"facet {index} adjacency contains duplicate cells")
            facet_node_set = set(self.facet_nodes(index).tolist())
            for cell_id in adjacency:
                if cell_id < 0 or cell_id >= n_cells:
                    raise ValueError(
                        f"facet {index} adjacency references cell id {cell_id} "
                        "out of range"
                    )
                cell_ids = self.cell_nodes(cell_id).tolist()
                matched = any(
                    {cell_ids[local] for local in face} == facet_node_set
                    for face in cell_type_members[cell_id].faces
                )
                if not matched:
                    raise ValueError(
                        f"facet {index} does not match a codim-1 face of "
                        f"cell {cell_id}"
                    )

        for group_name, group_ids in self._domain_groups.items():
            if group_ids.size and (
                int(group_ids.min()) < 0 or int(group_ids.max()) >= n_cells
            ):
                raise ValueError(
                    f"domain group {group_name!r} references cell ids out of range"
                )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(name={self._name!r}, nodes={self.n_nodes}, "
            f"cells={self.n_cells}, facets={self.n_facets}, "
            f"topo_dim={self._topo_dim})"
        )
