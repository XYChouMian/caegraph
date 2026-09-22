"""Graph-native canonical domain representation (ADR-015/018/019)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from caegraph.core.base import BaseObject
from caegraph.core.boundary.manager import BoundaryManager
from caegraph.core.enums import NodeCategory
from caegraph.core.field import Field
from caegraph.core.topology.mesh import Mesh

__all__ = ["CAEGraph"]


class CAEGraph(BaseObject):
    """Graph-native canonical domain representation (ADR-015).

    Semantic composition (ADR-018): entities, relations, geometry,
    fields, regions, conditions — plus the topology subsystem as an
    *optional semantic provider* referenced by this object (present
    for cell-based discretizations, absent for mesh-free ones,
    ADR-014). Semantic composition deliberately does not define class
    members or storage layout by itself: the Phase 2 minimal
    entity/relation model — node and cell entity families (node
    entities with canonical Mesh node IDs serve as the Phase 2 graph
    vertices, a representation choice; cell entities with canonical
    Mesh cell IDs carry identity via the Mesh, with no independent
    storage), relations as deduplicated ``(min, max)`` node pairs,
    per-node-entity NodeCategory annotations — is authorized and
    frozen by ADR-019 and populated at representation construction
    time (:class:`~caegraph.graph.MeshRepresentationBuilder`).

    This class also exposes the minimal association hooks the Phase 2
    domain vocabulary needs: an optional topology provider reference,
    a field association list (references — fields belong to entities,
    never to the representation object, ADR-018), and the boundary
    manager hosting semantic regions and condition declarations.

    CAEGraph never imports ``torch_geometric``: PyG / networkx /
    igraph are backends or analysis engines reached through the
    backend adapter layer (ADR-007/017), never the domain model.

    Args:
        name: Non-empty name of the representation instance.
        topology: Optional topology subsystem provider referenced by
            this representation. Only objects belonging to the
            topology subsystem qualify as providers — enforced as a
            :class:`~caegraph.core.topology.Mesh` membership check in
            Phase 2 (the current and only cell-based provider,
            ADR-014); future topology-subsystem members require an
            ADR and widen this check. ``None`` denotes a mesh-free
            representation or a provider not yet attached.
        n_entities: Optional entity count of the construction-time
            entity model (ADR-019). Required when any graph data is
            provided; omitted for semantic-only representations. The
            representation builder derives it from the topology
            (``Mesh.n_nodes``); direct construction is deliberately
            not cross-checked against ``topology`` (future
            multi-graph construction may legitimately differ,
            an ADR-019 deferred item). For Phase 2 this counts the
            node-graph
            vertex set — node entities serving as graph vertices is
            a representation choice, not the domain entity total
            (ADR-019 D1); cell entities are addressed through the
            topology provider's cell IDs.
        edges: Optional node-pair relations. Each pair is normalized
            to ``(min, max)``, self-loops are rejected, indices are
            bounds-checked against ``n_entities`` and the stored set
            is deduplicated and sorted at construction.
        node_categories: Optional per-entity
            :class:`~caegraph.core.NodeCategory` annotations;
            defaults to all-INTERIOR when graph data is provided
            without explicit categories.
        metadata: Optional free-form annotations.

    Raises:
        TypeError: If ``topology`` is neither ``None`` nor a
            :class:`~caegraph.core.topology.Mesh` (topology providers
            belong to the topology subsystem, never to other
            domain-truth families such as fields or regions),
            ``n_entities`` is not an integer, edge endpoints are not
            integers (bools are rejected despite being int
            subclasses), or category entries are not NodeCategory
            members.
        ValueError: If graph data is inconsistent (missing or
            non-positive ``n_entities``, malformed edge pairs,
            self-loop or out-of-range edges, category-length
            mismatch).

    Examples:
        >>> graph = CAEGraph("channel_flow")
        >>> graph.topology is None  # mesh-free state until a provider is attached
        True
        >>> graph.associate_field(Field("pressure", [0.1, 0.2], association="node"))
        >>> [field.name for field in graph.associated_fields]
        ['pressure']
    """

    def __init__(
        self,
        name: str,
        *,
        topology: Mesh | None = None,
        n_entities: int | None = None,
        edges: Iterable[tuple[int, int]] | None = None,
        node_categories: Iterable[NodeCategory] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize graph data and association hooks, then validate.

        Raises:
            TypeError: If ``topology`` is neither ``None`` nor a
                :class:`~caegraph.core.topology.Mesh`, or graph data
                types are invalid.
            ValueError: If graph data is inconsistent.
        """
        if topology is not None and not isinstance(topology, Mesh):
            raise TypeError(
                "topology must be a Mesh provider of the topology "
                "subsystem or None (referenced provider, never a framework "
                "object or another domain-truth family)"
            )
        self._topology: Mesh | None = topology

        graph_data_provided = not (
            n_entities is None and edges is None and node_categories is None
        )
        if n_entities is not None and (
            not isinstance(n_entities, int) or isinstance(n_entities, bool)
        ):
            raise TypeError("n_entities must be an integer")
        if graph_data_provided:
            if n_entities is None:
                raise ValueError("n_entities is required when graph data is provided")
            if n_entities < 1:
                raise ValueError("n_entities must be at least 1")
        self._n_entities = n_entities if n_entities is not None else 0

        if edges is not None:
            normalized: set[tuple[int, int]] = set()
            for pair in edges:
                try:
                    first, second = pair
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"edges must be (int, int) pairs, got {pair!r}"
                    ) from error
                if any(
                    not isinstance(endpoint, int) or isinstance(endpoint, bool)
                    for endpoint in (first, second)
                ):
                    raise TypeError(
                        f"edge endpoints must be integers, got {pair!r} "
                        "(entity IDs are canonical node indices, ADR-019)"
                    )
                low, high = (first, second) if first <= second else (second, first)
                if low == high:
                    raise ValueError(
                        f"self-loop edge ({low}, {high}) is not representable"
                    )
                if low < 0 or high >= self._n_entities:
                    raise ValueError(
                        f"edge ({first}, {second}) references entities out of range"
                    )
                normalized.add((low, high))
            self._edges = tuple(sorted(normalized))
        else:
            self._edges = ()

        if node_categories is not None:
            categories = tuple(node_categories)
            for category in categories:
                if not isinstance(category, NodeCategory):
                    raise TypeError(
                        "node_categories entries must be NodeCategory members"
                    )
            if len(categories) != self._n_entities:
                raise ValueError("node_categories length must match n_entities")
            self._node_categories = categories
        else:
            self._node_categories = (
                (NodeCategory.INTERIOR,) * self._n_entities if self._n_entities else ()
            )

        self._fields: dict[str, Field] = {}
        self._boundaries = BoundaryManager()
        super().__init__(name, metadata)

    @property
    def topology(self) -> Mesh | None:
        """Referenced topology subsystem provider; ``None`` if absent."""
        return self._topology

    @property
    def n_entities(self) -> int:
        """Node-graph vertex count of the construction-time entity model (ADR-019 D1)."""
        return self._n_entities

    @property
    def edges(self) -> tuple[tuple[int, int], ...]:
        """Canonical node-pair relations: ``(min, max)``, sorted, deduplicated."""
        return self._edges

    @property
    def node_categories(self) -> tuple[NodeCategory, ...]:
        """Per-entity NodeCategory annotations derived at construction."""
        return self._node_categories

    @property
    def boundaries(self) -> BoundaryManager:
        """Semantic region registry and condition declarations (ADR-018)."""
        return self._boundaries

    @property
    def associated_fields(self) -> tuple[Field, ...]:
        """Associated field data, ordered by name (references, not ownership)."""
        return tuple(self._fields[name] for name in sorted(self._fields))

    def associate_field(self, field: Field) -> None:
        """Associate ``field`` with this representation (ADR-018).

        Association is a reference, not ownership: fields belong to
        entities and keep their own entity scope. Field names are
        unique per representation. Phase 2 status: lightweight
        association API — no topology-cardinality validation happens
        here (cardinality is checked at construction time by the
        representation builder, ADR-019 D5).

        Args:
            field: The field data to associate.

        Raises:
            TypeError: If ``field`` is not a
                :class:`~caegraph.core.Field`.
            ValueError: If a field with the same name is already
                associated.
        """
        if not isinstance(field, Field):
            raise TypeError("associate_field expects a Field")
        if field.name in self._fields:
            raise ValueError(f"field {field.name!r} is already associated")
        self._fields[field.name] = field

    def validate(self) -> None:
        """Raise if the representation is in an invalid state.

        The topology provider must remain a topology-subsystem
        :class:`~caegraph.core.topology.Mesh` (or absent), associated
        entries must remain fields, and the construction-time graph
        data must keep its ADR-019 invariants (canonical sorted
        deduplicated edges without self-loops, in-range indices,
        category count matching the entity count).
        """
        if self._topology is not None and not isinstance(self._topology, Mesh):
            raise TypeError(
                "topology must be a Mesh provider of the topology subsystem or None"
            )
        for field in self._fields.values():
            if not isinstance(field, Field):
                raise TypeError("associated entries must be Field objects")
        if self._edges != tuple(sorted(set(self._edges))):
            raise ValueError("edges must be sorted and deduplicated")
        for low, high in self._edges:
            if low >= high:
                raise ValueError("edges must be canonical (min, max) pairs")
            if low < 0 or high >= self._n_entities:
                raise ValueError("edges reference entities out of range")
        if len(self._node_categories) != self._n_entities:
            raise ValueError("node_categories length must match n_entities")
