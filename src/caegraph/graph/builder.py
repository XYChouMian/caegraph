"""Mesh-to-CAEGraph representation construction (ADR-016/019)."""

from __future__ import annotations

from collections.abc import Iterable

from caegraph.core.boundary.manager import BoundaryManager
from caegraph.core.caegraph import CAEGraph
from caegraph.core.enums import NodeCategory
from caegraph.core.field import (
    _SUPPORTED_REALIZATION_FAMILIES,
    Field,
    FieldData,
)
from caegraph.core.topology.mesh import Mesh

__all__ = ["MeshRepresentationBuilder"]


class MeshRepresentationBuilder:
    """Construct a :class:`~caegraph.core.CAEGraph` from a cell-based Mesh source.

    Phase 2 cell-based construction strategy (ADR-016 boundary,
    ADR-019 semantics): domain entities form two families — node
    entities (ID = canonical Mesh node ID) and cell entities (ID =
    canonical Mesh cell ID, identity via the Mesh cell index, no
    independent storage); the Phase 2 node graph uses node entities
    as its vertices (a representation choice, not the entity
    definition); relations are undirected node pairs expanded from
    every cell's codim-1 face templates (canonical ``(min, max)``,
    globally deduplicated). For 1D sources (``topo_dim == 1``) each
    LINE2 cell contributes its own node pair as an edge, because
    dimension-0 facets are absent from the canonical topology
    (ADR-014/019). Per-node
    :class:`~caegraph.core.NodeCategory` annotations are
    derived from the semantic regions registered on the caller's
    :class:`~caegraph.core.BoundaryManager` — INTERIOR (no region),
    BOUNDARY (exactly one), CORNER (two or more). Nodes on boundary
    facets that belong to no declared region remain INTERIOR
    (region-driven semantics, ADR-019 D4).

    The regions of the input manager are re-registered on the
    produced graph's own boundary manager; boundary *declarations*
    (specs) are not migrated — bind them against
    ``graph.boundaries`` after construction.

    FieldData validation executes here (ADR-019 D5 as amended by
    ADR-020 D5): the builder is the only write path for realization
    data — every :class:`~caegraph.core.FieldData` must reference the
    explicitly associated Field declaration object (no dangling and
    no same-name-distinct-object realizations), and node/cell-
    associated values must carry a leading entity axis of exactly
    ``n_nodes`` / ``n_cells`` entries; unsupported realization
    families are rejected outright (ADR-021 D5) — ``node`` / ``cell``
    are the supported families.
    Declaration-only field sets are legal (ADR-020 D4), and multiple
    realizations per Field are stored without silent selection
    (ADR-020 D6).

    No builder registry exists in Phase 2 (single construction
    strategy, an ADR-019 deferred item); further source families
    extend this layer per ADR-016 without new ADRs unless the frozen
    boundary changes.
    """

    def __call__(
        self,
        mesh: Mesh,
        boundaries: BoundaryManager | None = None,
        fields: Iterable[Field] | None = None,
        field_data: Iterable[FieldData] | None = None,
    ) -> CAEGraph:
        """Construct the CAEGraph representation for ``mesh``.

        Args:
            mesh: Cell-based canonical topology source (ADR-014),
                referenced by the produced graph as its topology
                provider.
            boundaries: Optional semantic-region registry whose
                regions drive NodeCategory derivation and are
                re-registered on the produced graph.
            fields: Optional field declarations to associate after
                construction (references, no payload validation —
                declarations may remain realization-free, ADR-020
                D4).
            field_data: Optional realization data to register after
                construction. Each entry is validated for a
                non-dangling, reference-consistent declaration and
                leading-entity-axis cardinality, then written through
                the internal construction path — the builder is the
                only FieldData write path (ADR-020).

        Returns:
            A CAEGraph satisfying the Phase 2 minimal representation
            contract (ADR-019 D5), named after the mesh.

        Raises:
            TypeError: If ``mesh`` is not a
                :class:`~caegraph.core.topology.Mesh`.
            ValueError: If a region references an unknown facet id, a
                FieldData realization has no associated declaration
                or references a same-named but distinct Field object,
                or a node/cell-associated payload fails its
                leading-entity-axis cardinality check.
        """
        if not isinstance(mesh, Mesh):
            raise TypeError("MeshRepresentationBuilder expects a Mesh source")
        node_categories = self._derive_node_categories(mesh, boundaries)
        edges = self._expand_edges(mesh)
        graph = CAEGraph(
            mesh.name,
            topology=mesh,
            n_entities=mesh.n_nodes,
            edges=edges,
            node_categories=node_categories,
        )
        if boundaries is not None:
            for region in boundaries.regions:
                graph.boundaries.register(region)
        if fields is not None:
            for field in fields:
                graph.associate_field(field)
        if field_data is not None:
            declared = {field.name: field for field in graph.associated_fields}
            for data in field_data:
                self._validate_field_data(data, mesh, declared)
                graph._register_field_data(data)
        return graph

    def _derive_node_categories(
        self, mesh: Mesh, boundaries: BoundaryManager | None
    ) -> tuple[NodeCategory, ...]:
        """Derive per-node categories from region memberships (ADR-019 D4).

        Raises:
            ValueError: If a region references a facet id unknown to
                ``mesh``.
        """
        memberships: dict[int, int] = {}
        if boundaries is not None:
            for region in boundaries.regions:
                region_nodes: set[int] = set()
                for facet_id in region.membership:
                    if facet_id < 0 or facet_id >= mesh.n_facets:
                        raise ValueError(
                            f"region {region.name!r} references unknown "
                            f"facet id {facet_id}"
                        )
                    region_nodes.update(mesh.facet_nodes(facet_id).tolist())
                for node_id in region_nodes:
                    memberships[node_id] = memberships.get(node_id, 0) + 1
        categories = []
        for node_id in range(mesh.n_nodes):
            count = memberships.get(node_id, 0)
            if count == 0:
                categories.append(NodeCategory.INTERIOR)
            elif count == 1:
                categories.append(NodeCategory.BOUNDARY)
            else:
                categories.append(NodeCategory.CORNER)
        return tuple(categories)

    def _expand_edges(self, mesh: Mesh) -> tuple[tuple[int, int], ...]:
        """Expand every cell into its deduplicated node-pair edges.

        For cells of dimension >= 2, consecutive node pairs of each
        codim-1 face template (closed ring) form candidate edges. A
        1D cell (LINE2) is itself an edge and contributes its own
        node pair — its codim-1 faces are dimension-0 points, absent
        from the canonical topology (ADR-014/019 D2). Degenerate
        same-endpoint candidates ``(a, a)`` are discarded. Every
        candidate is canonicalized to ``(min, max)`` and deduplicated
        globally.
        """
        edges: set[tuple[int, int]] = set()
        for cell_id in range(mesh.n_cells):
            cell_type = mesh.cell_type(cell_id)
            nodes = mesh.cell_nodes(cell_id).tolist()
            if cell_type.dim == 1:
                first, second = nodes
                if first != second:
                    edges.add((min(first, second), max(first, second)))
                continue
            for face in cell_type.faces:
                ring = [nodes[local] for local in face]
                for index in range(len(ring)):
                    first = ring[index]
                    second = ring[(index + 1) % len(ring)]
                    if first != second:
                        edges.add((min(first, second), max(first, second)))
        return tuple(sorted(edges))

    def _validate_field_data(
        self, data: FieldData, mesh: Mesh, declared: dict[str, Field]
    ) -> None:
        """Enforce the declaration, family, reference-consistency and cardinality contracts.

        Fail-fast checks (ADR-019 D5 / ADR-020 / ADR-021): first,
        every realization must reference an explicitly associated
        Field declaration (no dangling realizations); second, the
        reference must be the declared Field **object itself** — a
        distinct object that merely shares the name is rejected (a
        Phase 2 implementation consistency guard; not a freeze of the
        ADR-020 D3 identity/reference mechanism, which stays
        deferred); third, the realization family must be supported
        (``node`` / ``cell``, ADR-021 D5 — FieldData already rejects
        unsupported families at creation, the builder re-validates as
        the canonical gate). Finally the leading-entity-axis
        cardinality contract (ADR-019 D5 as amended by ADR-020 D5)
        on ``FieldData.values``.

        Raises:
            ValueError: If the realization has no associated
                declaration, references a same-named but distinct
                Field object, names an unsupported realization
                family, or a node/cell-associated payload is unsized
                or carries a mismatched leading-axis count.
        """
        if data.field.name not in declared:
            raise ValueError(
                f"field data for {data.field.name!r} has no associated "
                "declaration — declare the Field first (ADR-020 D3)"
            )
        if declared[data.field.name] is not data.field:
            raise ValueError(
                f"field data for {data.field.name!r} must reference the "
                "declared Field object itself, not a distinct object "
                "that merely shares the name (Phase 2 implementation "
                "consistency guard)"
            )
        association = data.field.association
        if association not in _SUPPORTED_REALIZATION_FAMILIES:
            raise ValueError(
                f"field data for {data.field.name!r} references unsupported "
                f"realization family {association!r} (ADR-021 D5)"
            )
        try:
            length = len(data.values)  # type: ignore[arg-type]
        except TypeError as error:
            raise ValueError(
                f"field data for {data.field.name!r} with association "
                f"{association!r} must carry a sized leading entity axis"
            ) from error
        expected = mesh.n_nodes if association == "node" else mesh.n_cells
        if length != expected:
            raise ValueError(
                f"field data for {data.field.name!r} has a leading entity "
                f"axis of {length} entries but association {association!r} "
                f"requires {expected}"
            )
