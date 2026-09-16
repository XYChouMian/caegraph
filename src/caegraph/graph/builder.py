"""Mesh-to-CAEGraph representation construction (ADR-016/019)."""

from __future__ import annotations

from collections.abc import Iterable

from caegraph.core.boundary.manager import BoundaryManager
from caegraph.core.caegraph import CAEGraph
from caegraph.core.enums import NodeCategory
from caegraph.core.field import Field
from caegraph.core.topology.mesh import Mesh

__all__ = ["MeshRepresentationBuilder"]


class MeshRepresentationBuilder:
    """Construct a :class:`~caegraph.core.CAEGraph` from a cell-based Mesh source.

    Phase 2 cell-based construction strategy (ADR-016 boundary,
    ADR-019 semantics): entities are the mesh nodes; relations are
    undirected node pairs expanded from every cell's codim-1 face
    templates (canonical ``(min, max)``, globally deduplicated). For
    1D sources (``topo_dim == 1``) each LINE2 cell contributes its
    own node pair as an edge, because dimension-0 facets are absent
    from the canonical topology (ADR-014/019). Per-node
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

    Field length validation executes here (ADR-014 as amended /
    ADR-019 D5): fields whose ``association`` is ``"node"`` or
    ``"cell"`` must carry exactly ``n_nodes`` / ``n_cells`` sized
    values; other association labels are not length-checked.

    No builder registry exists in Phase 2 (single construction
    strategy, ADR-019 D6); further source families extend this layer
    per ADR-016 without new ADRs unless the frozen boundary changes.
    """

    def __call__(
        self,
        mesh: Mesh,
        boundaries: BoundaryManager | None = None,
        fields: Iterable[Field] | None = None,
    ) -> CAEGraph:
        """Construct the CAEGraph representation for ``mesh``.

        Args:
            mesh: Cell-based canonical topology source (ADR-014),
                referenced by the produced graph as its topology
                provider.
            boundaries: Optional semantic-region registry whose
                regions drive NodeCategory derivation and are
                re-registered on the produced graph.
            fields: Optional fields to associate after construction
                (length-validated for node/cell associations).

        Returns:
            The fully populated CAEGraph, named after the mesh.

        Raises:
            TypeError: If ``mesh`` is not a
                :class:`~caegraph.core.topology.Mesh`.
            ValueError: If a region references an unknown facet id or
                a field fails its association length check.
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
                self._validate_field(field, mesh)
                graph.associate_field(field)
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
        from the canonical topology (ADR-014/019 D2). Every candidate
        is canonicalized to ``(min, max)`` and deduplicated globally.
        """
        edges: set[tuple[int, int]] = set()
        for cell_id in range(mesh.n_cells):
            cell_type = mesh.cell_type(cell_id)
            nodes = mesh.cell_nodes(cell_id).tolist()
            if cell_type.dim == 1:
                first, second = nodes
                edges.add((min(first, second), max(first, second)))
                continue
            for face in cell_type.faces:
                ring = [nodes[local] for local in face]
                for index in range(len(ring)):
                    first = ring[index]
                    second = ring[(index + 1) % len(ring)]
                    edges.add((min(first, second), max(first, second)))
        return tuple(sorted(edges))

    def _validate_field(self, field: Field, mesh: Mesh) -> None:
        """Enforce the association length contract (ADR-019 D5).

        Raises:
            ValueError: If a node/cell-associated field carries
                non-sized values or a mismatched value count.
        """
        association = field.association
        if association not in ("node", "cell"):
            return
        try:
            length = len(field.values)  # type: ignore[arg-type]
        except TypeError as error:
            raise ValueError(
                f"field {field.name!r} with association {association!r} "
                "must carry sized values"
            ) from error
        expected = mesh.n_nodes if association == "node" else mesh.n_cells
        if length != expected:
            raise ValueError(
                f"field {field.name!r} carries {length} values but "
                f"association {association!r} requires {expected}"
            )
