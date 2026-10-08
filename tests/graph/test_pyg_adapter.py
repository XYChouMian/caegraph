"""ADR-022 contract guards for the PyG backend adapter (Gate 4b Stage 3).

Covers the frozen Phase 2 node-graph backend profile and Data schema
(ADR-022 D-01..D-07, D-01 as clarified in v1.3) at the contract level,
including the deferred adapter regressions A / B / C recorded in
``tests/core/test_projection.py``. Assertions target the contract, not
the copy mechanism.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
from torch_geometric.data import Data  # type: ignore[import-untyped]

from caegraph.core import CAEGraph, Field, FieldData, Mesh, NodeCategory
from caegraph.core.topology.celltype import CellType
from caegraph.graph import MeshRepresentationBuilder, to_pyg_data

_FROZEN_SCHEMA_KEYS = {
    "edge_index",
    "num_nodes",
    "pos",
    "node_category",
    "field_families",
}


def _two_triangle_mesh() -> Mesh:
    """Two TRI3 cells over four nodes; builder output has 5 unique edges."""
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


def _node_cell_graph() -> CAEGraph:
    """Graph with one node-family and one cell-family realization."""
    mesh = _two_triangle_mesh()
    pressure = Field("p", association="node")
    volume = Field("vol", association="cell")
    return MeshRepresentationBuilder()(
        mesh,
        fields=[pressure, volume],
        field_data=[
            FieldData(pressure, [1.0, 2.0, 3.0, 4.0], scope="global"),
            FieldData(volume, [0.5, 1.5], scope="global"),
        ],
    )


def _direct_graph(
    node_categories: tuple[NodeCategory, ...] | None = None,
    edges: tuple[tuple[int, int], ...] | None = ((0, 1), (1, 2), (2, 3)),
) -> CAEGraph:
    """Directly constructed profile-legal graph over the 4-node mesh."""
    return CAEGraph(
        "direct",
        topology=_two_triangle_mesh(),
        n_entities=4,
        edges=edges,
        node_categories=node_categories,
    )


def test_valid_graph_materializes_frozen_schema_without_extras():
    # Deferred regression A + exact schema: every frozen key materializes
    # and no key outside the frozen set + field names appears.
    data = to_pyg_data(_node_cell_graph())
    assert isinstance(data, Data)
    assert data.num_nodes == 4
    assert _FROZEN_SCHEMA_KEYS <= set(data.keys())
    extra = set(data.keys()) - _FROZEN_SCHEMA_KEYS
    assert extra == {"p", "vol"}


def test_projected_single_state_graph_materializes():
    # Deferred regression A through the full upstream chain:
    # snapshot selection -> single-state projection -> adapter.
    mesh = _two_triangle_mesh()
    pressure = Field("p", association="node")
    graph = MeshRepresentationBuilder()(mesh, fields=[pressure])
    graph.register_snapshot(
        physical_time=0.5,
        members=[FieldData(pressure, [7.0, 8.0, 9.0, 10.0], scope="snapshot")],
    )
    projected = graph.project_snapshot(graph.snapshots[0])
    data = to_pyg_data(projected)
    assert data.num_nodes == 4
    assert torch.equal(data["p"], torch.tensor([7.0, 8.0, 9.0, 10.0]))
    assert data.field_families == {"p": "node"}


def test_symmetric_directed_edge_index_expansion():
    graph = _node_cell_graph()
    data = to_pyg_data(graph)
    assert data.edge_index.dtype == torch.long
    assert data.edge_index.shape == (2, 10)  # 5 undirected pairs -> 2E
    directed = {tuple(pair) for pair in data.edge_index.t().tolist()}
    expected = set()
    for u, v in graph.edges:
        expected.add((u, v))
        expected.add((v, u))
    assert directed == expected
    assert all(u != v for u, v in directed)


def test_empty_edge_graph_produces_2x0_edge_index():
    data = to_pyg_data(_direct_graph(edges=None))
    assert data.edge_index.shape == (2, 0)
    assert data.edge_index.dtype == torch.long
    assert data.num_nodes == 4


def test_num_nodes_equals_n_entities():
    graph = _node_cell_graph()
    assert to_pyg_data(graph).num_nodes == graph.n_entities


def test_pos_is_topology_coordinates_in_float64():
    graph = _node_cell_graph()
    data = to_pyg_data(graph)
    assert data.pos.dtype == torch.float64
    assert data.pos.shape == (4, 3)
    assert np.array_equal(data.pos.numpy(), graph.topology.nodes)


def test_node_category_explicit_mapping_is_long():
    # ADR-022 D-07 explicit mapping, not the enum declaration order:
    # INTERIOR -> 0, BOUNDARY -> 1, CORNER -> 2.
    graph = _direct_graph(
        node_categories=(
            NodeCategory.BOUNDARY,
            NodeCategory.CORNER,
            NodeCategory.INTERIOR,
            NodeCategory.BOUNDARY,
        )
    )
    data = to_pyg_data(graph)
    assert data.node_category.dtype == torch.long
    assert torch.equal(data.node_category, torch.tensor([1, 2, 0, 1]))


def test_node_field_data_keyed_by_field_name():
    data = to_pyg_data(_node_cell_graph())
    assert torch.equal(data["p"], torch.tensor([1.0, 2.0, 3.0, 4.0]))


def test_cell_field_data_carried_as_is_without_interpolation():
    # ADR-022 D-03: cell-family payload keeps its leading n_cells axis,
    # carried in original form — no cell->node interpolation.
    data = to_pyg_data(_node_cell_graph())
    assert data["vol"].shape == (2,)
    assert torch.equal(data["vol"], torch.tensor([0.5, 1.5]))


def test_field_dtype_is_preserved_without_silent_cast():
    # ADR-022 D-07: field data receives no unjustified dtype cast.
    mesh = _two_triangle_mesh()
    flag = Field("flag", association="node")
    graph = MeshRepresentationBuilder()(
        mesh,
        fields=[flag],
        field_data=[FieldData(flag, [1, 0, 1, 1], scope="global")],
    )
    assert to_pyg_data(graph)["flag"].dtype == torch.int64


def test_field_families_matches_materialized_payload():
    # ADR-022 D-03: association fidelity — every materialized field key
    # maps to its Field.association family.
    data = to_pyg_data(_node_cell_graph())
    assert data.field_families == {"p": "node", "vol": "cell"}
    materialized = set(data.keys()) - _FROZEN_SCHEMA_KEYS
    assert set(data.field_families) == materialized


def test_declaration_only_fields_leave_zero_footprint():
    # Deferred regression C + ADR-022 D-06: declaration-only fields
    # produce no key, no mapping entry, no fabricated values; the
    # field_families container is always present and may be empty.
    mesh = _two_triangle_mesh()
    graph = MeshRepresentationBuilder()(mesh, fields=[Field("p", association="node")])
    data = to_pyg_data(graph)
    assert "p" not in data.keys()
    assert data.field_families == {}
    assert set(data.keys()) == _FROZEN_SCHEMA_KEYS


def test_multiple_realizations_of_one_field_are_rejected():
    # Deferred regression B + ADR-022 D-05: more than one FieldData for
    # one Field fails fast regardless of timestep values; the adapter
    # implements no selector (ADR-020 D6).
    mesh = _two_triangle_mesh()
    pressure = Field("p", association="node")
    frame0 = FieldData(pressure, [1.0, 2.0, 3.0, 4.0], timestep=0, scope="global")
    frame1 = FieldData(pressure, [2.0, 3.0, 4.0, 5.0], timestep=1, scope="global")
    graph = MeshRepresentationBuilder()(
        mesh, fields=[pressure], field_data=[frame0, frame1]
    )
    with pytest.raises(ValueError, match="no selection mechanism"):
        to_pyg_data(graph)


@pytest.mark.parametrize("name", ["x", "pos", "field_families", "y", "edge_attr"])
def test_reserved_key_collision_is_rejected(name):
    # ADR-022 D-04: fail-fast at backend adaptation only.
    mesh = _two_triangle_mesh()
    field = Field(name, association="node")
    graph = MeshRepresentationBuilder()(
        mesh,
        fields=[field],
        field_data=[FieldData(field, [1.0, 2.0, 3.0, 4.0], scope="global")],
    )
    with pytest.raises(ValueError, match="reserved"):
        to_pyg_data(graph)


def test_mesh_free_graph_is_rejected():
    # ADR-022 D-01 ③: the node-graph profile requires a cell-based
    # Mesh topology provider.
    with pytest.raises(ValueError, match="topology provider"):
        to_pyg_data(CAEGraph("declaration_only"))


def test_node_count_mismatch_is_rejected():
    # ADR-022 D-01 ④ (v1.3): a legal direct-construction canonical
    # state with n_entities != topology.n_nodes is outside the Phase 2
    # backend profile and fails fast at adaptation only.
    graph = CAEGraph(
        "mismatched",
        topology=_two_triangle_mesh(),
        n_entities=3,
        edges=((0, 1), (1, 2)),
    )
    with pytest.raises(ValueError, match="n_nodes == n_entities"):
        to_pyg_data(graph)


def test_non_caegraph_input_is_rejected():
    # ADR-022 D-01 ①: the sole domain input is a CAEGraph.
    with pytest.raises(ValueError, match="CAEGraph"):
        to_pyg_data("two_tri")  # type: ignore[arg-type]


def test_unrepresentable_payload_fails_fast_as_backend_profile_condition():
    # A PyG backend-profile condition only: a payload that cannot be
    # losslessly represented as a torch Tensor fails fast at adaptation;
    # the canonical legality of the FieldData / CAEGraph is unaffected.
    mesh = _two_triangle_mesh()
    label = Field("label", association="node")
    graph = MeshRepresentationBuilder()(
        mesh,
        fields=[label],
        field_data=[FieldData(label, ["a", "b", "c", "d"], scope="global")],
    )
    graph.validate()  # the canonical state itself remains legal
    with pytest.raises(ValueError, match="backend profile condition"):
        to_pyg_data(graph)
    assert graph.field_data[0].values == ["a", "b", "c", "d"]


def test_adapter_output_is_independent_of_timestep_values():
    # Zero-selector evidence (ADR-022 D-05): graphs differing only in
    # legacy timestep values produce identical backend representations;
    # the adapter never reads timestep, physical_time or Snapshots.
    outputs = []
    for timestep in (0.0, 99.0):
        mesh = _two_triangle_mesh()
        pressure = Field("p", association="node")
        graph = MeshRepresentationBuilder()(
            mesh,
            fields=[pressure],
            field_data=[
                FieldData(
                    pressure, [1.0, 2.0, 3.0, 4.0], timestep=timestep, scope="global"
                )
            ],
        )
        data = to_pyg_data(graph)
        outputs.append({key: data[key] for key in data.keys()})
        assert outputs[-1]["p"] is not None
    for key, value in outputs[0].items():
        if isinstance(value, torch.Tensor):
            assert torch.equal(value, outputs[1][key])
        else:
            assert value == outputs[1][key]
