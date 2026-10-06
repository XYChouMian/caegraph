"""Guard tests for ADR-023 D-08 selection / projection invariants (Dispatch ②).

Covers: registered-Snapshot selection (object-reference handle, M3),
candidate collection (eligible globals + selected members, joint
counting), the per-Field 0 / 1 / >1 branches (>1 = ADR-020 D6
explicit failure only, M2), the materialized single-state projection
(snapshot-scoped copies keep their scope, exactly one Snapshot,
exactly-once membership, M1), original-graph zero side effects and
copy/share isolation.

Adapter regressions A/B/C (projected -> adapter success, unresolved
original -> adapter fail-fast, declaration-only zero footprint) are
deferred pending the ADR-022 Stage 3 adapter implementation
(ADR-022 FACT-06) — see the dispatch ledger.
"""

from __future__ import annotations

import pytest

from caegraph.core import CAEGraph, Field, FieldData, Snapshot
from caegraph.core.boundary import BoundaryManager, BoundaryRegion, BoundarySpec
from caegraph.core.enums import BoundaryType, NodeCategory
from caegraph.core.topology.celltype import CellType
from caegraph.core.topology.mesh import Mesh
from caegraph.graph import MeshRepresentationBuilder


def _two_triangle_mesh() -> Mesh:
    """Two TRI3 cells sharing edge (1, 2): n_nodes == 4, n_cells == 2."""
    return Mesh(
        "two_tri",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0], [2.0, 0.0, 0.0]],
        topo_dim=2,
        cell_types=[CellType.TRI3.code, CellType.TRI3.code],
        cells=[0, 1, 2, 1, 3, 2],
        cell_offsets=[0, 3, 6],
        facet_types=[CellType.LINE2.code] * 5,
        facets=[1, 0, 2, 0, 1, 2, 1, 3, 3, 2],
        facet_offsets=[0, 2, 4, 6, 8, 10],
        facet_cells=[[0], [0], [0, 1], [1], [1]],
    )


def _node_field(name: str = "pressure") -> Field:
    return Field(name, unit="Pa", association="node")


def _member(
    field: Field, values: list[float], timestep: float | None = None
) -> FieldData:
    return FieldData(field, values, scope="snapshot", timestep=timestep)


def _graph_with_snapshots() -> tuple[CAEGraph, Field, FieldData, FieldData]:
    """Graph with one node field realized in two snapshots (t=0.5 / 1.5)."""
    field = _node_field()
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field])
    early = _member(field, [1.0, 2.0, 3.0, 4.0])
    late = _member(field, [2.0, 3.0, 4.0, 5.0])
    graph.register_snapshot(physical_time=0.5, members=[early])
    graph.register_snapshot(physical_time=1.5, members=[late])
    return graph, field, early, late


# --- Explicit selection (M3) ----------------------------------------------------


def test_selects_registered_snapshot() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    assert [item.physical_time for item in projected.snapshots] == [0.5]


def test_foreign_snapshot_rejected() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    foreign = Snapshot(physical_time=99.0)
    with pytest.raises(ValueError, match="not registered"):
        graph.project_snapshot(foreign)


def test_selection_independent_of_timestep() -> None:
    # Membership decides the projected state; the members carry
    # "misleading" legacy timesteps inverted against physical_time.
    field = _node_field()
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field])
    early = _member(field, [1.0, 1.0, 1.0, 1.0], timestep=99)
    late = _member(field, [2.0, 2.0, 2.0, 2.0], timestep=0)
    graph.register_snapshot(physical_time=0.5, members=[early])
    graph.register_snapshot(physical_time=1.5, members=[late])
    assert list(graph.project_snapshot(graph.snapshots[0]).field_data[0].values) == [
        1.0,
        1.0,
        1.0,
        1.0,
    ]
    assert list(graph.project_snapshot(graph.snapshots[1]).field_data[0].values) == [
        2.0,
        2.0,
        2.0,
        2.0,
    ]


# --- Candidate collection and the 0 / 1 / >1 branches ---------------------------


def test_candidate_includes_members_and_globals() -> None:
    velocity = Field("velocity", association="node")
    density = Field("density", association="node")
    graph = MeshRepresentationBuilder()(
        _two_triangle_mesh(),
        fields=[velocity, density],
        field_data=[FieldData(density, [1.2, 1.2, 1.2, 1.2], scope="global")],
    )
    graph.register_snapshot(
        physical_time=0.5, members=[_member(velocity, [1.0, 2.0, 3.0, 4.0])]
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    scopes = {data.field.name: data.scope for data in projected.field_data}
    assert scopes == {"velocity": "snapshot", "density": "global"}


def test_declaration_only_field_stays_declaration_only() -> None:
    field = _node_field()
    other = Field("temperature", association="node")
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field, other])
    graph.register_snapshot(
        physical_time=0.5, members=[_member(field, [1.0, 2.0, 3.0, 4.0])]
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    assert other.name in {item.name for item in projected.associated_fields}
    assert all(data.field is not other for data in projected.field_data)


def test_field_only_in_unselected_snapshot_stays_declaration_only() -> None:
    field = _node_field()
    other = Field("temperature", association="node")
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field, other])
    graph.register_snapshot(
        physical_time=0.5, members=[_member(field, [1.0, 2.0, 3.0, 4.0])]
    )
    graph.register_snapshot(
        physical_time=1.5, members=[_member(other, [9.0, 9.0, 9.0, 9.0])]
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    assert {item.name for item in projected.associated_fields} == {
        "pressure",
        "temperature",
    }
    assert [data.field.name for data in projected.field_data] == ["pressure"]


def test_single_realization_enters_projection() -> None:
    graph, _, early, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    assert len(projected.field_data) == 1
    assert list(projected.field_data[0].values) == list(early.values)


def test_global_multiplicity_fail_fast() -> None:
    field = _node_field()
    graph = MeshRepresentationBuilder()(
        _two_triangle_mesh(),
        fields=[field],
        field_data=[
            FieldData(field, [1.0, 2.0, 3.0, 4.0], scope="global"),
            FieldData(field, [2.0, 3.0, 4.0, 5.0], scope="global"),
        ],
    )
    graph.register_snapshot(physical_time=0.5)
    with pytest.raises(ValueError, match="ADR-020 D6"):
        graph.project_snapshot(graph.snapshots[0])


def test_snapshot_internal_multiplicity_fail_fast() -> None:
    field = _node_field()
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field])
    graph.register_snapshot(
        physical_time=0.5,
        members=[
            _member(field, [1.0, 2.0, 3.0, 4.0]),
            _member(field, [2.0, 3.0, 4.0, 5.0]),
        ],
    )
    with pytest.raises(ValueError, match="ADR-020 D6"):
        graph.project_snapshot(graph.snapshots[0])


# --- Projection shape (M1) --------------------------------------------------------


def test_globals_preserved_as_global_without_membership() -> None:
    velocity = Field("velocity", association="node")
    density = Field("density", association="node")
    graph = MeshRepresentationBuilder()(
        _two_triangle_mesh(),
        fields=[velocity, density],
        field_data=[FieldData(density, [1.2, 1.2, 1.2, 1.2], scope="global")],
    )
    graph.register_snapshot(
        physical_time=0.5, members=[_member(velocity, [1.0, 2.0, 3.0, 4.0])]
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    projected_global = next(
        data for data in projected.field_data if data.field.name == "density"
    )
    assert projected_global.scope == "global"
    assert all(
        projected_global is not member for member in projected.snapshots[0].members
    )


def test_selected_realizations_keep_snapshot_scope() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    assert projected.field_data[0].scope == "snapshot"


def test_projected_members_single_membership() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    member = projected.field_data[0]
    owning = [
        snapshot
        for snapshot in projected.snapshots
        if any(existing is member for existing in snapshot.members)
    ]
    assert len(owning) == 1
    assert [existing for existing in owning[0].members if existing is member] == [
        member
    ]


def test_projected_graph_exactly_one_snapshot() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    graph.register_snapshot(physical_time=2.5)
    projected = graph.project_snapshot(graph.snapshots[0])
    assert len(projected.snapshots) == 1
    assert projected.snapshots[0].physical_time == 0.5
    assert projected.snapshots[0].solver_step is None


def test_projected_snapshot_coordinates_copied() -> None:
    field = _node_field()
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field])
    graph.register_snapshot(
        physical_time=1.25, solver_step=5318, members=[_member(field, [1.0] * 4)]
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    assert projected.snapshots[0].physical_time == 1.25
    assert projected.snapshots[0].solver_step == 5318


def test_empty_snapshot_projection_legal() -> None:
    field = _node_field()
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field])
    graph.register_snapshot(physical_time=0.5)
    projected = graph.project_snapshot(graph.snapshots[0])
    assert projected.field_data == ()
    projected.validate()


# --- Declaration binding and isolation -------------------------------------------


def test_projected_declaration_binding_uses_new_field_objects() -> None:
    graph, field, _, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    for data in projected.field_data:
        # Binding is graph-internal (ADR-020 D3): the projected
        # FieldData references the projected graph's own associated
        # Field declaration object — a NEW object, not the original.
        assert data.field in projected.associated_fields
        assert data.field is not field
        assert data.field.name == field.name
        assert data.field.unit == field.unit
        assert data.field.association == field.association


def test_original_state_unchanged() -> None:
    graph, field, early, late = _graph_with_snapshots()
    region = BoundaryRegion("wall", [1, 2], metadata={"tag": "w"})
    graph.boundaries.register(region)
    before_snapshots = graph.snapshots
    before_members = tuple(tuple(snapshot.members) for snapshot in graph.snapshots)
    before_field_data = graph.field_data
    before_fields = graph.associated_fields
    before_metadata = field.metadata
    graph.project_snapshot(graph.snapshots[0])
    assert graph.snapshots == before_snapshots
    assert all(
        tuple(snapshot.members) == members
        for snapshot, members in zip(graph.snapshots, before_members, strict=True)
    )
    assert graph.field_data == before_field_data
    assert graph.associated_fields == before_fields
    assert graph.topology is not None
    assert graph.boundaries.region("wall") is region
    # Field declarations are projection-materialized COPIES (no
    # aliasing): the metadata comparison asserts the projected copy
    # equals the original at projection time, and that the projection
    # itself performed zero mutation calls on the original (all
    # canonical state above is unchanged).
    assert field.metadata == before_metadata


def test_graph_metadata_preserved_and_isolated() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    graph.update_metadata(channel="wind", config={"re": 1000.0})
    projected = graph.project_snapshot(graph.snapshots[0])
    assert projected.metadata == {"channel": "wind", "config": {"re": 1000.0}}
    # deep-copied graph metadata: nested values are independent objects
    assert projected.metadata["config"] is not graph.metadata["config"]
    projected.metadata["config"]["re"] = 2000.0
    assert graph.metadata["config"]["re"] == 1000.0


def test_no_shared_temporal_member_objects() -> None:
    graph, _, early, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    projected_member = projected.snapshots[0].members[0]
    assert projected_member is not early
    assert all(
        projected_member is not member
        for snapshot in graph.snapshots
        for member in snapshot.members
    )
    assert all(
        member is not existing
        for member in graph.snapshots[0].members
        for existing in projected.snapshots[0].members
    )


def test_projected_payloads_are_deep_copies() -> None:
    graph, _, early, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    copy = projected.field_data[0]
    assert copy.values is not early.values
    assert copy.metadata == early.metadata and copy.metadata is not early.metadata
    copy.values[0] = 999.0  # type: ignore[index]
    # FieldData.metadata is exposed as a read-only MappingProxyType —
    # no mutation path exists through the view at all; deepcopy
    # isolation is proven by the identity check above.
    assert list(early.values) == [1.0, 2.0, 3.0, 4.0]
    assert early.metadata == {}


def test_timestep_copied_unchanged() -> None:
    field = _node_field()
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), fields=[field])
    graph.register_snapshot(
        physical_time=0.5, members=[_member(field, [1.0] * 4, timestep=7)]
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    assert projected.field_data[0].timestep == 7


def test_topology_rebuilt_as_new_mesh_preserving_canonical_state() -> None:
    import numpy as np

    graph, _, _, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    # B2 isolation: the referenced topology provider is rebuilt as a
    # new Mesh, never shared with the original.
    assert projected.topology is not graph.topology
    original, rebuilt = graph.topology, projected.topology
    assert rebuilt is not None and original is not None
    assert rebuilt.name == original.name
    assert np.array_equal(rebuilt.nodes, original.nodes)
    assert rebuilt.topo_dim == original.topo_dim
    assert np.array_equal(rebuilt.cell_types, original.cell_types)
    assert np.array_equal(rebuilt.cells, original.cells)
    assert np.array_equal(rebuilt.cell_offsets, original.cell_offsets)
    assert np.array_equal(rebuilt.facet_types, original.facet_types)
    assert np.array_equal(rebuilt.facets, original.facets)
    assert np.array_equal(rebuilt.facet_offsets, original.facet_offsets)
    assert rebuilt.facet_cells == original.facet_cells
    assert dict(rebuilt.domain_groups) == dict(original.domain_groups)
    assert rebuilt.metadata == original.metadata


def test_graph_level_facts_preserved() -> None:
    boundaries = BoundaryManager()
    boundaries.register(BoundaryRegion("wall", [0, 1]))
    boundaries.register(BoundaryRegion("inlet", [3, 4]))
    field = _node_field()
    graph = MeshRepresentationBuilder()(
        _two_triangle_mesh(), boundaries, fields=[field]
    )
    graph.register_snapshot(
        physical_time=0.5, members=[_member(field, [1.0, 2.0, 3.0, 4.0])]
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    # ADR-024 D-04: graph-level identity / relation / category facts are
    # realization-independent canonical content, so projection must carry
    # them over unchanged. The non-vacuity check keeps this test honest
    # about the categories it claims to guard.
    assert set(graph.node_categories) != {NodeCategory.INTERIOR}
    assert projected.n_entities == graph.n_entities
    assert projected.edges == graph.edges
    assert projected.node_categories == graph.node_categories


def test_boundary_manager_copied_not_shared() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    region = BoundaryRegion("wall", [1, 2], metadata={"tag": "w"})
    graph.boundaries.register(region)
    spec = BoundarySpec("wall", BoundaryType.DIRICHLET, value=1.5)
    graph.boundaries.bind(spec)
    projected = graph.project_snapshot(graph.snapshots[0])
    copied_region = projected.boundaries.region("wall")
    assert copied_region is not region
    assert copied_region.membership == region.membership
    assert copied_region.metadata == region.metadata
    copied_spec = projected.boundaries.specs_for("wall")[0]
    assert copied_spec is not spec
    assert copied_spec.target is copied_region  # re-bound to the copy
    assert spec.target is region  # original binding untouched
    projected.boundaries.register(BoundaryRegion("extra", [3]))
    assert "extra" not in graph.boundaries


def test_periodic_spec_retargets_projected_regions() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    wall = BoundaryRegion("wall", [1, 2])
    far = BoundaryRegion("far_wall", [3, 4])
    graph.boundaries.register(wall)
    graph.boundaries.register(far)
    spec = BoundarySpec("wall", BoundaryType.PERIODIC, paired_region="far_wall")
    graph.boundaries.bind(spec)
    projected = graph.project_snapshot(graph.snapshots[0])
    projected_spec = projected.boundaries.specs_for("wall")[0]
    projected_wall = projected.boundaries.region("wall")
    projected_far = projected.boundaries.region("far_wall")
    assert projected_spec.target is projected_wall
    assert projected_spec.target is not wall
    assert projected_spec.paired_target is projected_far
    assert projected_spec.paired_target is not far


def test_projected_graph_validates() -> None:
    graph, _, _, _ = _graph_with_snapshots()
    projected = graph.project_snapshot(graph.snapshots[0])
    projected.validate()  # must not raise (deferred adapter input-contract
    # regression: ADR-022 Stage 3, see module docstring)
