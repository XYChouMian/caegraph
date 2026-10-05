"""Guard tests for the ADR-023 structural temporal invariants (Dispatch ①).

Covers the five registered invariants of
``architecture/decisions/ADR-023-invariants.yaml`` at the
representation layer: D02-01 (physical_time required + unique),
D03-01 (snapshot-scoped membership exactly one Snapshot), D04-01
(explicit scope dichotomy), D04-02 (per-Field scope exclusivity) and
D07-01 (membership independent of timestep values — proven
behaviourally, no runtime assertion). Selection / candidate /
disambiguation / projection are out of scope (Dispatch ②).
"""

from __future__ import annotations

import pytest

from caegraph.core import CAEGraph, Field, FieldData, Snapshot
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


def _node_field() -> Field:
    return Field("pressure", unit="Pa", association="node")


def _cell_field() -> Field:
    return Field("volume", association="cell")


def _graph(*fields: Field) -> CAEGraph:
    return MeshRepresentationBuilder()(_two_triangle_mesh(), fields=list(fields))


def _node_member(field: Field, timestep: float | None = None) -> FieldData:
    return FieldData(field, [1.0, 2.0, 3.0, 4.0], scope="snapshot", timestep=timestep)


# --- Snapshot temporal coordinates (D-02) --------------------------------------


def test_snapshot_physical_time_is_required() -> None:
    with pytest.raises(TypeError):
        Snapshot()  # type: ignore[call-arg]


@pytest.mark.parametrize("bad", ["t0", True, None])
def test_snapshot_rejects_non_numeric_physical_time(bad: object) -> None:
    with pytest.raises(TypeError):
        Snapshot(physical_time=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["s0", True])
def test_snapshot_rejects_non_numeric_solver_step(bad: object) -> None:
    with pytest.raises(TypeError):
        Snapshot(physical_time=1.0, solver_step=bad)  # type: ignore[arg-type]


def test_snapshot_coordinates_are_immutable() -> None:
    snapshot = Snapshot(physical_time=1.0)
    with pytest.raises(AttributeError):
        snapshot.physical_time = 2.0  # type: ignore[misc]
    with pytest.raises(AttributeError):
        snapshot.solver_step = 5  # type: ignore[misc]


def test_snapshot_seal_is_once_only() -> None:
    snapshot = Snapshot(physical_time=1.0)
    snapshot._seal(())
    with pytest.raises(RuntimeError):
        snapshot._seal(())


def test_register_snapshot_rejects_duplicate_physical_time() -> None:
    graph = _graph(_node_field())
    graph.register_snapshot(physical_time=0.5)
    with pytest.raises(ValueError, match="physical_time"):
        graph.register_snapshot(physical_time=0.5)


def test_register_snapshot_int_and_float_compare_equal() -> None:
    graph = _graph(_node_field())
    graph.register_snapshot(physical_time=3)
    with pytest.raises(ValueError, match="physical_time"):
        graph.register_snapshot(physical_time=3.0)


def test_snapshots_order_by_physical_time_ascending() -> None:
    graph = _graph(_node_field())
    graph.register_snapshot(physical_time=2.0)
    graph.register_snapshot(physical_time=0.5)
    graph.register_snapshot(physical_time=1.0)
    assert [item.physical_time for item in graph.snapshots] == [0.5, 1.0, 2.0]


def test_non_uniform_physical_time_spacing_is_legal() -> None:
    graph = _graph(_node_field())
    graph.register_snapshot(physical_time=0.0)
    graph.register_snapshot(physical_time=0.1)
    graph.register_snapshot(physical_time=7.5)
    assert len(graph.snapshots) == 3


# --- Explicit scope dichotomy (D-04) --------------------------------------------


def test_field_data_scope_is_required() -> None:
    with pytest.raises(TypeError):
        FieldData(_node_field(), [1.0, 2.0, 3.0, 4.0])  # type: ignore[call-arg]


@pytest.mark.parametrize("bad", ["steady", 3, None])
def test_field_data_rejects_invalid_scope(bad: object) -> None:
    with pytest.raises(ValueError, match="scope"):
        FieldData(_node_field(), [1.0, 2.0, 3.0, 4.0], scope=bad)  # type: ignore[arg-type]


def test_field_data_scope_is_immutable() -> None:
    data = FieldData(_node_field(), [1.0, 2.0, 3.0, 4.0], scope="global")
    assert data.scope == "global"
    with pytest.raises(AttributeError):
        data.scope = "snapshot"  # type: ignore[misc]


def test_register_snapshot_rejects_global_scoped_member() -> None:
    graph = _graph(_node_field())
    member = FieldData(_node_field(), [1.0, 2.0, 3.0, 4.0], scope="global")
    with pytest.raises(ValueError, match="snapshot-scoped"):
        graph.register_snapshot(physical_time=0.5, members=[member])


def test_builder_rejects_snapshot_scoped_field_data() -> None:
    field = _node_field()
    with pytest.raises(ValueError, match="register_snapshot"):
        MeshRepresentationBuilder()(
            _two_triangle_mesh(),
            fields=[field],
            field_data=[_node_member(field)],
        )


def test_scope_mixing_within_one_field_is_rejected() -> None:
    field = _node_field()
    graph = MeshRepresentationBuilder()(
        _two_triangle_mesh(),
        fields=[field],
        field_data=[FieldData(field, [1.0, 2.0, 3.0, 4.0], scope="global")],
    )
    with pytest.raises(ValueError, match="mixes global and snapshot-scoped"):
        graph.register_snapshot(physical_time=0.5, members=[_node_member(field)])


# --- Membership single-valuedness and atomicity (D-03) --------------------------


def test_snapshot_scoped_member_belongs_to_exactly_one_snapshot() -> None:
    field = _node_field()
    graph = _graph(field)
    member = _node_member(field)
    snapshot = graph.register_snapshot(physical_time=0.5, members=[member])
    assert snapshot.members == (member,)
    owning = [
        item
        for item in graph.snapshots
        if any(existing is member for existing in item.members)
    ]
    assert len(owning) == 1


def test_duplicate_membership_is_rejected() -> None:
    field = _node_field()
    graph = _graph(field)
    member = _node_member(field)
    graph.register_snapshot(physical_time=0.5, members=[member])
    with pytest.raises(ValueError, match="another Snapshot"):
        graph.register_snapshot(physical_time=1.5, members=[member])


def test_duplicate_member_within_one_registration_is_rejected() -> None:
    field = _node_field()
    graph = _graph(field)
    member = _node_member(field)
    with pytest.raises(ValueError, match="duplicate FieldData object"):
        graph.register_snapshot(physical_time=0.5, members=[member, member])


def test_failed_registration_leaves_no_partial_state() -> None:
    field = _node_field()
    graph = _graph(field)
    member = _node_member(field)
    graph.register_snapshot(physical_time=0.5, members=[member])
    before_data, before_snapshots = graph.field_data, graph.snapshots
    with pytest.raises(ValueError):
        graph.register_snapshot(physical_time=0.5)  # duplicate physical_time
    assert graph.field_data == before_data
    assert graph.snapshots == before_snapshots


def test_members_enter_the_canonical_registry() -> None:
    field = _node_field()
    graph = _graph(field)
    member = _node_member(field)
    graph.register_snapshot(physical_time=0.5, members=[member])
    assert graph.field_data == (member,)
    assert graph.snapshots[0].members == (member,)


# --- Declaration / family / cardinality binding --------------------------------


def test_member_requires_declared_field() -> None:
    graph = _graph()  # no fields declared
    with pytest.raises(ValueError, match="no associated declaration"):
        graph.register_snapshot(
            physical_time=0.5, members=[_node_member(_node_field())]
        )


def test_member_requires_the_declared_field_object() -> None:
    graph = _graph(_node_field())
    with pytest.raises(ValueError, match="declared Field object itself"):
        graph.register_snapshot(
            physical_time=0.5, members=[_node_member(_node_field())]
        )


def test_member_cardinality_mismatch_is_rejected() -> None:
    field = _node_field()
    graph = _graph(field)
    member = FieldData(field, [1.0, 2.0], scope="snapshot")
    with pytest.raises(ValueError, match="leading entity axis"):
        graph.register_snapshot(physical_time=0.5, members=[member])


def test_cell_family_member_requires_topology_provider() -> None:
    graph = CAEGraph("semantic", n_entities=2, edges=[(0, 1)])
    field = _cell_field()
    graph.associate_field(field)
    member = FieldData(field, [1.0, 2.0], scope="snapshot")
    with pytest.raises(ValueError, match="topology provider"):
        graph.register_snapshot(physical_time=0.5, members=[member])


def test_cell_family_member_cardinality_uses_topology() -> None:
    field = _cell_field()
    graph = _graph(field)
    good = FieldData(field, [1.0, 2.0], scope="snapshot")
    graph.register_snapshot(physical_time=0.5, members=[good])
    bad = FieldData(field, [1.0, 2.0, 3.0], scope="snapshot")
    with pytest.raises(ValueError, match="leading entity axis"):
        graph.register_snapshot(physical_time=1.5, members=[bad])


# --- Legal representable shapes (no (Snapshot, Field) cap) ----------------------


def test_same_snapshot_same_field_multiple_realizations_legal() -> None:
    field = _node_field()
    graph = _graph(field)
    first = _node_member(field, timestep=0)
    second = _node_member(field, timestep=0)
    snapshot = graph.register_snapshot(physical_time=0.5, members=[first, second])
    assert snapshot.members == (first, second)


def test_same_field_across_snapshots_legal() -> None:
    field = _node_field()
    graph = _graph(field)
    early = _node_member(field)
    late = _node_member(field)
    graph.register_snapshot(physical_time=0.5, members=[early])
    graph.register_snapshot(physical_time=1.5, members=[late])
    assert graph.field_data == (early, late)


def test_global_multi_realization_legal() -> None:
    field = _node_field()
    graph = MeshRepresentationBuilder()(
        _two_triangle_mesh(),
        fields=[field],
        field_data=[
            FieldData(field, [1.0, 2.0, 3.0, 4.0], scope="global", timestep=0),
            FieldData(field, [2.0, 3.0, 4.0, 5.0], scope="global", timestep=1),
        ],
    )
    assert len(graph.field_data) == 2
    assert graph.snapshots == ()


def test_empty_snapshot_legal() -> None:
    graph = _graph(_node_field())
    snapshot = graph.register_snapshot(physical_time=0.5)
    assert snapshot.members == ()


def test_zero_snapshot_steady_only_graph_legal() -> None:
    graph = _graph(_node_field())
    assert graph.snapshots == ()


def test_snapshot_missing_fields_legal() -> None:
    pressure = _node_field()
    volume = _cell_field()
    graph = _graph(pressure, volume)
    graph.register_snapshot(physical_time=0.5, members=[_node_member(pressure)])
    assert len(graph.snapshots[0].members) == 1


# --- Membership independence of timestep values (D-07) --------------------------


def test_membership_independent_of_timestep_values() -> None:
    field = _node_field()
    graph = _graph(field)
    for index, timestep in enumerate((None, 0, 999.5)):
        member = _node_member(field, timestep=timestep)
        graph.register_snapshot(physical_time=index + 0.5, members=[member])
    assert len(graph.snapshots) == 3


def test_identical_timestep_values_do_not_interfere() -> None:
    field = _node_field()
    graph = _graph(field)
    early = _node_member(field, timestep=7)
    late = _node_member(field, timestep=7)
    graph.register_snapshot(physical_time=0.5, members=[early])
    graph.register_snapshot(physical_time=1.5, members=[late])
    assert graph.snapshots[0].members == (early,)
    assert graph.snapshots[1].members == (late,)


def test_snapshot_order_follows_physical_time_not_timestep() -> None:
    field = _node_field()
    graph = _graph(field)
    graph.register_snapshot(
        physical_time=1.5, members=[_node_member(field, timestep=0)]
    )
    graph.register_snapshot(
        physical_time=0.5, members=[_node_member(field, timestep=99)]
    )
    assert [item.physical_time for item in graph.snapshots] == [0.5, 1.5]


# --- No reverse membership path --------------------------------------------------


def test_field_data_has_no_reverse_membership_path() -> None:
    member = _node_member(_node_field())
    assert not hasattr(member, "snapshot")
    related = [
        name
        for name in dir(member)
        if "snapshot" in name.lower()
        or "register" in name.lower()
        or "member" in name.lower()
    ]
    assert related == []
