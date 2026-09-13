"""Tests for caegraph.core.topology.mesh (ADR-014)."""

from __future__ import annotations

import numpy as np
import pytest

from caegraph.core import Mesh
from caegraph.core.topology import canonical_facet_nodes
from caegraph.core.topology.celltype import CellType


def _two_triangle_mesh(**overrides) -> Mesh:
    """Two TRI3 cells sharing edge (1, 2); five explicit LINE2 facets."""
    args: dict = dict(
        name="two_tri",
        nodes=[
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
            [2.0, 0.0, 0.0],
        ],
        topo_dim=2,
        cell_types=[CellType.TRI3.code, CellType.TRI3.code],
        cells=[0, 1, 2, 1, 3, 2],
        cell_offsets=[0, 3, 6],
        facet_types=[CellType.LINE2.code] * 5,
        facets=[1, 0, 2, 0, 1, 2, 1, 3, 3, 2],
        facet_offsets=[0, 2, 4, 6, 8, 10],
        facet_cells=[[0], [0], [0, 1], [1], [1]],
        domain_groups={"fluid": [0, 1]},
    )
    args.update(overrides)
    return Mesh(**args)


def test_valid_two_triangle_mesh_shape_and_accessors():
    mesh = _two_triangle_mesh()
    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets, mesh.topo_dim) == (4, 2, 5, 2)
    assert mesh.cell_type(0) is CellType.TRI3
    assert mesh.cell_nodes(0).tolist() == [0, 1, 2]
    assert mesh.cell_nodes(1).tolist() == [1, 3, 2]
    assert mesh.facet_adjacent_cells(2) == (0, 1)
    assert set(mesh.domain_groups) == {"fluid"}
    assert mesh.domain_groups["fluid"].tolist() == [0, 1]


def test_facet_connectivity_is_canonicalized_at_construction():
    mesh = _two_triangle_mesh()
    # given orders [1,0], [2,0], [1,2], [1,3], [3,2] -> canonical rotations
    assert mesh.facet_nodes(0).tolist() == [0, 1]
    assert mesh.facet_nodes(1).tolist() == [0, 2]
    assert mesh.facet_nodes(2).tolist() == [1, 2]
    assert mesh.facet_nodes(3).tolist() == [1, 3]
    assert mesh.facet_nodes(4).tolist() == [2, 3]


def test_single_hex8_mesh_with_all_six_faces():
    mesh = Mesh(
        name="hex",
        nodes=np.arange(24, dtype=np.float64).reshape(8, 3),
        topo_dim=3,
        cell_types=[CellType.HEX8.code],
        cells=list(range(8)),
        cell_offsets=[0, 8],
        facet_types=[CellType.QUAD4.code] * 6,
        facets=[local for face in CellType.HEX8.faces for local in face],
        facet_offsets=[0, 4, 8, 12, 16, 20, 24],
        facet_cells=[[0]] * 6,
    )
    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets) == (8, 1, 6)
    for index in range(6):
        assert mesh.facet_adjacent_cells(index) == (0,)


def test_single_quad4_mesh():
    Mesh(
        name="quad",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]],
        topo_dim=2,
        cell_types=[CellType.QUAD4.code],
        cells=[0, 1, 2, 3],
        cell_offsets=[0, 4],
        facet_types=[CellType.LINE2.code] * 4,
        facets=[0, 1, 1, 2, 2, 3, 3, 0],
        facet_offsets=[0, 2, 4, 6, 8],
        facet_cells=[[0]] * 4,
    )


def test_mesh_without_groups_and_without_facets_is_valid():
    mesh = Mesh(
        name="bare",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        topo_dim=2,
        cell_types=[CellType.TRI3.code],
        cells=[0, 1, 2],
        cell_offsets=[0, 3],
    )
    assert mesh.n_facets == 0
    assert mesh.facet_cells == ()
    assert dict(mesh.domain_groups) == {}


def test_line2_mesh_with_no_facets_is_valid():
    mesh = Mesh(
        name="beam",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
        topo_dim=1,
        cell_types=[CellType.LINE2.code],
        cells=[0, 1],
        cell_offsets=[0, 2],
    )
    assert (mesh.n_cells, mesh.n_facets, mesh.topo_dim) == (1, 0, 1)


def test_2d_mesh_stores_three_coordinate_columns():
    mesh = _two_triangle_mesh()
    assert mesh.nodes.shape == (4, 3)
    assert mesh.nodes.dtype == np.float64


def test_partial_facet_table_is_rejected():
    with pytest.raises(ValueError, match="together"):
        _two_triangle_mesh(facets=None, facet_types=[1], facet_offsets=[0, 2])


# --- canonicalization determinism (ADR-014 decision 3) ----------------------


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ([3, 9], (3, 9)),
        ([9, 3], (3, 9)),
        ([5, 8, 3], (3, 5, 8)),
        ([3, 8, 5], (3, 5, 8)),
        ([8, 3, 5], (3, 5, 8)),
        ([7, 1, 4, 2], (1, 4, 2, 7)),
        ([2, 7, 1, 4], (1, 4, 2, 7)),
    ],
)
def test_canonical_facet_nodes_determinism(given, expected):
    assert canonical_facet_nodes(given) == expected


def test_same_facet_through_different_windings_collapses():
    mesh_a = _two_triangle_mesh()
    mesh_b = _two_triangle_mesh(facets=[0, 1, 0, 2, 2, 1, 3, 1, 2, 3])
    np.testing.assert_array_equal(mesh_a.facets, mesh_b.facets)


# --- 8a failure matrix ------------------------------------------------------


def test_nodes_wrong_shape_is_rejected():
    with pytest.raises(ValueError, match=r"\(n_nodes, 3\)"):
        _two_triangle_mesh(nodes=[[0.0, 0.0], [1.0, 0.0], [0.5, 1.0], [2.0, 0.0]])


def test_column_count_cannot_carry_topo_dim():
    with pytest.raises(ValueError, match=r"\(n_nodes, 3\)"):
        _two_triangle_mesh(
            nodes=[[0.0, 0.0], [1.0, 0.0], [0.5, 1.0], [2.0, 0.0]],
        )


def test_empty_nodes_is_rejected():
    with pytest.raises(ValueError, match="at least one node"):
        _two_triangle_mesh(nodes=np.empty((0, 3)))


def test_invalid_topo_dim_is_rejected():
    with pytest.raises(ValueError, match="topo_dim"):
        _two_triangle_mesh(topo_dim=0)


def test_unknown_cell_code_is_rejected():
    with pytest.raises(ValueError, match="unknown CellType code"):
        _two_triangle_mesh(cell_types=[99, CellType.TRI3.code])


def test_cell_dim_mismatching_topo_dim_is_rejected():
    with pytest.raises(ValueError, match="topo_dim"):
        _two_triangle_mesh(
            topo_dim=2,
            cell_types=[CellType.LINE2.code, CellType.TRI3.code],
            cells=[0, 1, 1, 2, 3],
            cell_offsets=[0, 2, 5],
        )


def test_cell_offsets_wrong_length_is_rejected():
    with pytest.raises(ValueError, match="n_cells \\+ 1"):
        _two_triangle_mesh(cell_offsets=[0, 3])


def test_cell_offsets_must_start_at_zero():
    with pytest.raises(ValueError, match="start at 0"):
        _two_triangle_mesh(cell_offsets=[1, 3, 6], cells=[0, 2, 1, 2, 3])


def test_cell_connectivity_size_mismatch_is_rejected():
    with pytest.raises(ValueError, match="node counts"):
        _two_triangle_mesh(cells=[0, 1, 0, 1, 3, 2], cell_offsets=[0, 2, 6])


def test_cell_node_index_out_of_range_is_rejected():
    with pytest.raises(ValueError, match="out of range"):
        _two_triangle_mesh(cells=[0, 1, 2, 1, 3, 9])


def test_facet_dim_mismatching_topo_dim_is_rejected():
    # a TRI3 facet (dim 2) cannot live on a 2D mesh whose facets
    # must be dim 1 == topo_dim - 1
    bad_types = [CellType.TRI3.code] + [CellType.LINE2.code] * 4
    with pytest.raises(ValueError, match="topo_dim - 1"):
        _two_triangle_mesh(
            facet_types=bad_types,
            facet_offsets=[0, 3, 5, 7, 9, 11],
            facets=[0, 1, 2, 1, 0, 1, 2, 1, 3, 3, 2],
            facet_cells=[[0], [0], [0, 1], [1], [1]],
        )


def test_facet_connectivity_size_mismatch_is_rejected():
    with pytest.raises(ValueError, match="nodes"):
        _two_triangle_mesh(
            facet_offsets=[0, 1, 3, 5, 7, 9],
            facets=[0, 1, 2, 1, 3, 3, 2, 1, 2],
            facet_cells=[[0], [0], [0, 1], [1], [1]],
        )


def test_facet_without_adjacent_cell_is_rejected():
    with pytest.raises(ValueError, match="no adjacent cell"):
        _two_triangle_mesh(facet_cells=[[], [0], [0, 1], [1], [1]])


def test_facet_adjacency_length_mismatch_is_rejected():
    with pytest.raises(ValueError, match="one entry per facet"):
        _two_triangle_mesh(facet_cells=[[0], [0], [0, 1], [1]])


def test_facet_adjacent_cell_out_of_range_is_rejected():
    with pytest.raises(ValueError, match="out of range"):
        _two_triangle_mesh(facet_cells=[[0], [0], [0, 7], [1], [1]])


def test_facet_adjacency_duplicates_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        _two_triangle_mesh(facet_cells=[[0], [0], [0, 0], [1], [1]])


def test_forged_facet_cell_adjacency_is_rejected():
    # facet (0, 1) belongs to cell 0 only; claiming cell 1 must fail the
    # codim-1 face-template match (ADR-014 8a, required failure case)
    with pytest.raises(ValueError, match="codim-1 face"):
        _two_triangle_mesh(facet_cells=[[0, 1], [0], [0, 1], [1], [1]])


def test_domain_group_out_of_range_is_rejected():
    with pytest.raises(ValueError, match="domain group"):
        _two_triangle_mesh(domain_groups={"fluid": [0, 9]})


def test_domain_group_blank_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        _two_triangle_mesh(domain_groups={"  ": [0]})


def test_float_connectivity_is_rejected():
    with pytest.raises(TypeError, match="integers"):
        _two_triangle_mesh(cells=[0.0, 1.0, 2.0, 1.0, 3.0, 2.0])


def test_scalar_cell_types_are_rejected():
    with pytest.raises(TypeError, match="one-dimensional"):
        _two_triangle_mesh(cell_types=CellType.TRI3.code)


# --- frozen structure -------------------------------------------------------


def test_exposed_arrays_are_read_only():
    mesh = _two_triangle_mesh()
    for array in (
        mesh.nodes,
        mesh.cell_types,
        mesh.cells,
        mesh.cell_offsets,
        mesh.facet_types,
        mesh.facets,
        mesh.facet_offsets,
    ):
        assert not array.flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        mesh.nodes[0, 0] = 99.0


def test_input_arrays_are_decoupled_from_mesh_storage():
    nodes = np.zeros((4, 3))
    cell_types = np.array([CellType.TRI3.code, CellType.TRI3.code])
    mesh = _two_triangle_mesh(nodes=nodes, cell_types=cell_types)
    assert not mesh.nodes.flags.writeable
    assert nodes.flags.writeable
    assert cell_types.flags.writeable


def test_repr_reports_structure():
    mesh = _two_triangle_mesh()
    assert repr(mesh) == (
        "Mesh(name='two_tri', nodes=4, cells=2, facets=5, topo_dim=2)"
    )


def test_base_object_contract_still_applies():
    with pytest.raises(ValueError, match="non-empty"):
        _two_triangle_mesh(name="   ")
    mesh = _two_triangle_mesh(metadata={"source": "synthetic"})
    assert mesh.metadata == {"source": "synthetic"}
