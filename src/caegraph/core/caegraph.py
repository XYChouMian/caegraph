"""Graph-native canonical domain representation (ADR-015/018/019)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any

from caegraph.core.base import BaseObject
from caegraph.core.boundary.manager import BoundaryManager
from caegraph.core.boundary.region import BoundaryRegion
from caegraph.core.boundary.spec import BoundarySpec
from caegraph.core.enums import NodeCategory
from caegraph.core.field import (
    _GLOBAL_SCOPE,
    _SNAPSHOT_SCOPE,
    _SUPPORTED_REALIZATION_FAMILIES,
    Field,
    FieldData,
)
from caegraph.core.temporal import Snapshot
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
    never to the representation object, ADR-018) with realization
    data accessible through the canonical data flow (ADR-020:
    builder-only write path, read-only ``field_data`` access), and
    the boundary manager hosting semantic regions and condition
    declarations.

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
        >>> graph.associate_field(Field("pressure", association="node"))
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
        """Initialize graph data and association hooks, then validate."""
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
        self._field_data: list[FieldData] = []
        self._snapshots: list[Snapshot] = []
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
        """Associated field declarations, ordered by name (references, not ownership)."""
        return tuple(self._fields[name] for name in sorted(self._fields))

    @property
    def field_data(self) -> tuple[FieldData, ...]:
        """Canonical FieldData registry, read-only view (ADR-020 D4 / ADR-023).

        The registry holds **every** realization of this
        representation — global/static realizations (registered
        through the representation builder, the only global write
        path) and snapshot-scoped realizations (registered atomically
        with their Snapshot membership via
        :meth:`register_snapshot`, ADR-023). Snapshot membership is
        the authoritative temporal organization relation and never
        replaces this registry.
        """
        return tuple(self._field_data)

    def associate_field(self, field: Field) -> None:
        """Associate the field ``declaration`` with this representation (ADR-018).

        Association is a reference, not ownership: fields belong to
        entities and keep their own entity scope. Field names are
        unique per representation. Phase 2 status: lightweight
        association API — no topology-cardinality validation happens
        here (cardinality is checked at construction time by the
        representation builder, ADR-019 D5).

        Args:
            field: The field declaration to associate.

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

    def _register_field_data(self, data: FieldData) -> None:
        """Append validated realization data (internal, builder-authorized).

        Internal construction path: the representation builder is the
        only authorized caller — it performs the cardinality and
        dangling-declaration checks first (ADR-019 D5 / ADR-020 D5).
        Not a public API: the builder-only write path is an ADR-020
        scope-exclusion implementation microdecision, re-evaluable at
        gate 4b.
        """
        self._field_data.append(data)

    @property
    def snapshots(self) -> tuple[Snapshot, ...]:
        """Snapshots of this temporal organization (ADR-023).

        Ordered by ascending ``physical_time`` — the sole canonical
        temporal ordering coordinate (ADR-023 D-02/D-08); registration
        order, list indices and ``solver_step`` never define order.
        Non-uniform spacing is legal. An empty tuple denotes a
        steady-only / zero-Snapshot representation (legal, D-01).
        """
        return tuple(sorted(self._snapshots, key=lambda item: item.physical_time))

    def register_snapshot(
        self,
        *,
        physical_time: float,
        solver_step: float | None = None,
        members: Iterable[FieldData] = (),
    ) -> Snapshot:
        """Atomically register a Snapshot with its authoritative membership.

        This is the single temporal mutation entry of the
        representation (ADR-023 D-03/D-04): all consistency checks run
        first, then the members enter the canonical FieldData
        registry, the Snapshot membership is sealed and the Snapshot
        is registered — any failure leaves the representation
        unchanged (no partial state).

        Checks (fail-fast): ``physical_time`` is a number and unique
        within this temporal organization (D-02); every member is a
        snapshot-scoped :class:`~caegraph.core.FieldData`
        (``"global"`` realizations have no membership, D-04)
        referencing the associated declaration object itself
        (no dangling / same-name-distinct-object realizations,
        ADR-020 D3 guard) with a supported family and a correct
        leading-entity-axis cardinality (node → ``n_entities``;
        cell → ``topology.n_cells`` — a cell-family member requires
        an attached topology provider, otherwise cardinality is
        unverifiable and registration fails); no member of a Field
        that already has global realizations (per-Field scope
        exclusivity — the single ADR-023 Phase 2 narrowing, D-04);
        no FieldData already belonging to another Snapshot and no
        duplicate object within ``members`` (membership is
        single-valued, D-03). Membership never reads or compares
        ``FieldData.timestep`` values (D-07).

        Args:
            physical_time: Required physical time of the
                instantaneous state (``int`` / ``float``; bools
                rejected).
            solver_step: Optional solver / data-source step number
                (provenance only, never identity — ADR-023 D-02).
            members: Snapshot-scoped realizations forming the
                instantaneous state. May be empty (empty Snapshot is
                legal, ADR-023 D-06); a Snapshot may also miss Fields
                that exist elsewhere in the organization.

        Returns:
            The registered :class:`~caegraph.core.Snapshot`
            (immutable after this atomic registration).

        Raises:
            TypeError: If ``physical_time`` / ``solver_step`` are not
                numbers or a member is not a
                :class:`~caegraph.core.FieldData`.
            ValueError: If any structural temporal invariant would be
                violated (see the check list above).

        Examples:
            >>> graph = CAEGraph("flow", n_entities=2, edges=[(0, 1)])
            >>> field = Field("pressure", association="node")
            >>> graph.associate_field(field)
            >>> frame = FieldData(field, [1.0, 2.0], scope="snapshot")
            >>> snapshot = graph.register_snapshot(physical_time=0.5, members=[frame])
            >>> snapshot.members[0] is frame
            True
            >>> [item.physical_time for item in graph.snapshots]
            [0.5]
        """
        member_list = list(members)
        for member in member_list:
            if not isinstance(member, FieldData):
                raise TypeError("snapshot members must be FieldData objects")
        # Construct first: the Snapshot validates the physical_time type
        # and value (incl. NaN) *before* any duplicate comparison — a
        # bool physical_time must report a TypeError, never a
        # duplicate mismatch (ADR-023 D-02).
        snapshot = Snapshot(physical_time=physical_time, solver_step=solver_step)
        for registered in self._snapshots:
            if registered.physical_time == physical_time:
                raise ValueError(
                    f"physical_time {physical_time!r} duplicates an existing "
                    "Snapshot of this temporal organization (ADR-023 D-02)"
                )
        for index, member in enumerate(member_list):
            for other in member_list[index + 1 :]:
                if member is other:
                    raise ValueError(
                        "duplicate FieldData object in snapshot members "
                        "(membership is single-valued, ADR-023 D-03)"
                    )
        for member in member_list:
            if member.scope != _SNAPSHOT_SCOPE:
                raise ValueError(
                    "snapshot members must be snapshot-scoped FieldData - "
                    "global/static realizations have no membership (ADR-023 D-04)"
                )
            self._validate_field_data_binding(member)
            field = member.field
            for data in self._field_data:
                if data.scope == _GLOBAL_SCOPE and data.field is field:
                    raise ValueError(
                        f"field {field.name!r} mixes global and "
                        "snapshot-scoped realizations (ADR-023 D-04, the "
                        "single Phase 2 temporal-profile narrowing)"
                    )
            for existing_snapshot in self._snapshots:
                for existing in existing_snapshot.members:
                    if existing is member:
                        raise ValueError(
                            "FieldData already belongs to another Snapshot "
                            "(membership is single-valued, ADR-023 D-03)"
                        )
        self._field_data.extend(member_list)
        snapshot._seal(member_list)
        self._snapshots.append(snapshot)
        return snapshot

    def _validate_field_data_binding(self, data: FieldData) -> None:
        """Validate the declaration / family / cardinality binding of ``data``.

        Fail-fast checks re-used by the snapshot-registration and
        projection paths (ADR-019 D5 / ADR-020 D3 / ADR-021 D5): the
        realization must reference the explicitly associated Field
        declaration **object itself** (no dangling realizations, no
        same-named distinct object), name a supported realization
        family and carry a sized leading entity axis of the correct
        length (node → ``n_entities``; cell → topology ``n_cells``,
        requiring an attached topology provider). Pure move of the
        checks originally inlined in :meth:`register_snapshot`.
        """
        field = data.field
        declared = self._fields.get(field.name)
        if declared is None:
            raise ValueError(
                f"field data for {field.name!r} has no associated "
                "declaration — declare the Field first (ADR-020 D3)"
            )
        if declared is not field:
            raise ValueError(
                f"field data for {field.name!r} must reference the "
                "declared Field object itself, not a distinct object "
                "that merely shares the name (Phase 2 implementation "
                "consistency guard)"
            )
        association = field.association
        if association not in _SUPPORTED_REALIZATION_FAMILIES:
            raise ValueError(
                f"field data for {field.name!r} references unsupported "
                f"realization family {association!r} (ADR-021 D5)"
            )
        try:
            length = len(data.values)  # type: ignore[arg-type]
        except TypeError as error:
            raise ValueError(
                f"field data for {field.name!r} with association "
                f"{association!r} must carry a sized leading entity axis"
            ) from error
        if association == "node":
            expected = self._n_entities
        else:
            if self._topology is None:
                raise ValueError(
                    f"cell-family realization for {field.name!r} requires "
                    "an attached topology provider to validate cardinality "
                    "(ADR-019 D5 / ADR-020 D5)"
                )
            expected = self._topology.n_cells
        if length != expected:
            raise ValueError(
                f"field data for {field.name!r} has a leading entity "
                f"axis of {length} entries but association "
                f"{association!r} requires {expected}"
            )

    def project_snapshot(self, snapshot: Snapshot) -> CAEGraph:
        """Materialize the single-state canonical projection of ``snapshot``.

        Implements the ADR-023 D-08 consumption chain on the canonical
        temporal layer: explicit selection of a **registered** Snapshot
        (object-reference handle only — selection never reads
        ``FieldData.timestep``), candidate collection (per declared
        Field: eligible global realizations + the Field's members of
        the selected Snapshot, counted jointly with no source
        priority), the per-Field 0 / 1 / >1 branches (0 → the Field
        stays declaration-only, 1 → enters the projection, >1 →
        fail-fast per ADR-020 D6 — explicit failure only, automatic
        selection of any kind is forbidden) and the materialized
        single-state result.

        The projection is a **new** :class:`CAEGraph` — exactly one
        Snapshot with the selected Snapshot's temporal coordinates,
        temporal realizations kept as snapshot-scoped **new** FieldData
        objects (each belonging exactly once to the projected
        Snapshot; the original Snapshot keeps its own authoritative
        membership, ADR-023 D-03), eligible global realizations kept
        as new global FieldData objects with no membership, and every
        Field ending with at most one realization. By-design aliasing:
        Field declarations and the topology provider are referenced
        non-owning objects (ADR-018/014) shared with the original;
        graph-owned state (realization payloads and metadata, Snapshot
        membership, the boundary manager and its regions/specs) is
        newly built. The original graph is left completely unchanged.

        The result satisfies the CAEGraph validation contract; its
        conformance to the ADR-022 adapter input contract is pending
        the ADR-022 Stage 3 adapter implementation (deferred
        regression, see the dispatch ledger).

        Args:
            snapshot: A Snapshot registered in this temporal
                organization.

        Returns:
            The materialized single-state canonical projection.

        Raises:
            ValueError: If ``snapshot`` is not registered here, or a
                Field has more than one candidate realization in the
                selected state (ADR-020 D6 explicit failure — the
                explicit-selection branch is not implemented).

        Examples:
            >>> graph = CAEGraph("flow", n_entities=2, edges=[(0, 1)])
            >>> field = Field("pressure", association="node")
            >>> graph.associate_field(field)
            >>> _ = graph.register_snapshot(
            ...     physical_time=0.5,
            ...     members=[FieldData(field, [1.0, 2.0], scope="snapshot")],
            ... )
            >>> projected = graph.project_snapshot(graph.snapshots[0])
            >>> len(projected.snapshots)
            1
            >>> projected.field_data[0].scope
            'snapshot'
            >>> projected.field_data[0] is graph.field_data[0]
            False
        """
        if not any(registered is snapshot for registered in self._snapshots):
            raise ValueError(
                "Snapshot is not registered in this temporal organization - "
                "selection accepts registered Snapshot references only "
                "(ADR-023 D-08)"
            )
        globals_by_field: dict[Field, list[FieldData]] = {}
        for data in self._field_data:
            if data.scope == _GLOBAL_SCOPE:
                globals_by_field.setdefault(data.field, []).append(data)
        members_by_field: dict[Field, list[FieldData]] = {}
        for member in snapshot.members:
            members_by_field.setdefault(member.field, []).append(member)
        included: list[FieldData] = []
        for field in self._fields.values():
            global_side = globals_by_field.get(field, [])
            snapshot_side = members_by_field.get(field, [])
            total = len(global_side) + len(snapshot_side)
            if total > 1:
                raise ValueError(
                    f"field {field.name!r} has {total} candidate "
                    "realizations in the selected instantaneous state "
                    f"({len(global_side)} global + {len(snapshot_side)} "
                    "snapshot-scoped) - explicit selection is required "
                    "before projection and automatic selection is "
                    "forbidden (ADR-020 D6)"
                )
            if total == 1:
                included.append(global_side[0] if global_side else snapshot_side[0])
        projected = CAEGraph(
            self.name,
            topology=self._topology,
            n_entities=self._n_entities or None,
            edges=self._edges or None,
            node_categories=self._node_categories or None,
        )
        for field in self._fields.values():
            projected.associate_field(field)
        temporal_copies: list[FieldData] = []
        for data in included:
            copy = FieldData(
                data.field,
                deepcopy(data.values),
                scope=data.scope,
                timestep=data.timestep,
                metadata=deepcopy(dict(data.metadata)),
            )
            if copy.scope == _SNAPSHOT_SCOPE:
                temporal_copies.append(copy)
            else:
                projected._validate_field_data_binding(copy)
                projected._register_field_data(copy)
        projected.register_snapshot(
            physical_time=snapshot.physical_time,
            solver_step=snapshot.solver_step,
            members=temporal_copies,
        )
        self._copy_boundaries_onto(projected)
        projected.validate()
        return projected

    def _copy_boundaries_onto(self, projected: CAEGraph) -> None:
        """Rebuild the boundary manager of ``projected`` from graph-owned copies.

        Regions and specs are graph-owned mutable state (BaseObject
        metadata channels / binding caches): the projection registers
        **new** region objects and binds **new** unbound specs so that
        no mutation path reaches the original manager.
        """
        for region in self._boundaries.regions:
            projected._boundaries.register(
                BoundaryRegion(
                    region.name,
                    region.membership,
                    metadata=deepcopy(region.metadata),
                )
            )
        for spec in self._boundaries.specs:
            projected._boundaries.bind(
                BoundarySpec(
                    spec.region,
                    spec.boundary_type,
                    value=spec.value,
                    weight=spec.weight,
                    paired_region=spec.paired_region,
                    parameters=dict(spec.parameters) if spec.parameters else None,
                    time_dependent=spec.time_dependent,
                    space_dependent=spec.space_dependent,
                )
            )

    def validate(self) -> None:
        """Raise if the representation is in an invalid state.

        Composes the validation layers of the BaseObject layering
        convention (ARCHITECTURE.md §3.4): the state layer and the
        metadata layer. No cross layer is defined — CAEGraph
        explicitly declares no cross constraints.
        """
        self._validate_state()
        self._validate_metadata()

    # No _validate_cross layer: CAEGraph declares no cross-layer
    # (state x metadata) constraints — an explicitly registered
    # decision (ARCHITECTURE.md §3.4).

    def _validate_state(self) -> None:
        """Check the state-layer invariants (never read metadata).

        The topology provider must remain a topology-subsystem
        :class:`~caegraph.core.topology.Mesh` (or absent), associated
        entries must remain fields, and the construction-time graph
        data must keep its ADR-019 invariants (canonical sorted
        deduplicated edges without self-loops, in-range indices,
        category count matching the entity count).
        Internal validation hook invoked by BaseObject lifecycle
        (construction, explicit re-check; metadata updates only via
        an overriding on_metadata_changed). Not a public API.
        """
        if self._topology is not None and not isinstance(self._topology, Mesh):
            raise TypeError(
                "topology must be a Mesh provider of the topology subsystem or None"
            )
        for field in self._fields.values():
            if not isinstance(field, Field):
                raise TypeError("associated entries must be Field objects")
        for data in self._field_data:
            if not isinstance(data, FieldData):
                raise TypeError("field_data entries must be FieldData objects")
        for snapshot in self._snapshots:
            if not isinstance(snapshot, Snapshot):
                raise TypeError("snapshots entries must be Snapshot objects")
        if self._edges != tuple(sorted(set(self._edges))):
            raise ValueError("edges must be sorted and deduplicated")
        for low, high in self._edges:
            if low >= high:
                raise ValueError("edges must be canonical (min, max) pairs")
            if low < 0 or high >= self._n_entities:
                raise ValueError("edges reference entities out of range")
        if len(self._node_categories) != self._n_entities:
            raise ValueError("node_categories length must match n_entities")

    def _validate_metadata(self) -> None:
        """Check the metadata-layer invariants (annotation itself).

        Explicit no-op: CAEGraph assigns no semantics to metadata
        keys — metadata is annotation, not domain state, and
        undeclared means free (ARCHITECTURE.md §3.4).
        Internal validation hook invoked by BaseObject lifecycle
        (construction, explicit re-check; metadata updates only via
        an overriding on_metadata_changed). Not a public API.
        """
        # no metadata constraints declared (explicit decision)
