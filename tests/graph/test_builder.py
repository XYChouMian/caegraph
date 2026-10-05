"""Tests for caegraph.graph.builder.MeshRepresentationBuilder (ADR-016/019)."""

from __future__ import annotations

import numpy as np
import pytest

from caegraph.core import (
    BoundaryManager,
    BoundaryRegion,
    Field,
    FieldData,
    Mesh,
    NodeCategory,
)
from caegraph.core.topology.celltype import CellType
from caegraph.graph import MeshRepresentationBuilder


def _two_triangle_mesh() -> Mesh:
    """Two TRI3 cells sharing edge (1, 2); five explicit LINE2 facets.

    facets: (0,1)->cell0, (0,2)->cell0, (1,2)->cells 0+1 (shared),
    (1,3)->cell1, (2,3)->cell1.
    """
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


def _two_region_manager() -> BoundaryManager:
    """left region on facets {0, 1} (nodes 0,1,2); right on {3, 4} (nodes 1,2,3)."""
    manager = BoundaryManager()
    manager.register(BoundaryRegion("left", [0, 1]))
    manager.register(BoundaryRegion("right", [3, 4]))
    return manager


def _beam_mesh() -> Mesh:
    """1D source: three nodes connected by two LINE2 cells."""
    return Mesh(
        "beam",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
        topo_dim=1,
        cell_types=[CellType.LINE2.code, CellType.LINE2.code],
        cells=[0, 1, 1, 2],
        cell_offsets=[0, 2, 4],
    )


def test_node_and_edge_structure_of_two_triangle_mesh():
    graph = MeshRepresentationBuilder()(_two_triangle_mesh())
    assert graph.n_entities == 4
    # 2 cells x 3 face-edges, shared face counted once -> 5 unique edges
    assert graph.edges == ((0, 1), (0, 2), (1, 2), (1, 3), (2, 3))
    assert graph.topology is not None
    assert graph.topology.name == "two_tri"


def test_1d_line2_cells_contribute_their_node_pairs_as_edges():
    graph = MeshRepresentationBuilder()(_beam_mesh())
    assert graph.n_entities == 3
    assert graph.edges == ((0, 1), (1, 2))
    assert graph.node_categories == (NodeCategory.INTERIOR,) * 3


def test_1d_mesh_has_no_facets_so_regions_are_rejected():
    manager = BoundaryManager()
    manager.register(BoundaryRegion("end", [0]))
    with pytest.raises(ValueError, match="unknown facet"):
        MeshRepresentationBuilder()(_beam_mesh(), manager)


def test_duplicate_field_names_are_rejected():
    mesh = _two_triangle_mesh()
    with pytest.raises(ValueError, match="already associated"):
        MeshRepresentationBuilder()(
            mesh,
            fields=[
                Field("p", association="node"),
                Field("p", association="node"),
            ],
        )


def test_hex8_cube_edge_count():
    mesh = Mesh(
        "hex",
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
    graph = MeshRepresentationBuilder()(mesh)
    # 6 quad faces x 4 ring edges = 24 candidates, cube has 12 unique
    assert graph.n_entities == 8
    assert len(graph.edges) == 12


def test_node_categories_without_regions_are_all_interior():
    graph = MeshRepresentationBuilder()(_two_triangle_mesh())
    assert graph.node_categories == (NodeCategory.INTERIOR,) * 4


def test_node_categories_from_two_regions():
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), _two_region_manager())
    # left nodes {0,1,2}, right nodes {1,2,3}
    assert graph.node_categories == (
        NodeCategory.BOUNDARY,  # 0: left only
        NodeCategory.CORNER,  # 1: left + right
        NodeCategory.CORNER,  # 2: left + right
        NodeCategory.BOUNDARY,  # 3: right only
    )


def test_undeclared_boundary_nodes_remain_interior():
    mesh = _two_triangle_mesh()
    manager = BoundaryManager()
    manager.register(BoundaryRegion("left", [0]))  # only facet 0 -> nodes {0,1}
    graph = MeshRepresentationBuilder()(mesh, manager)
    assert graph.node_categories == (
        NodeCategory.BOUNDARY,
        NodeCategory.BOUNDARY,
        NodeCategory.INTERIOR,  # node 2: on facets 1/2 but no region
        NodeCategory.INTERIOR,
    )


def test_regions_are_registered_on_the_produced_graph():
    graph = MeshRepresentationBuilder()(_two_triangle_mesh(), _two_region_manager())
    assert {region.name for region in graph.boundaries.regions} == {"left", "right"}
    assert graph.boundaries.region("left").membership == frozenset({0, 1})


def test_region_with_unknown_facet_is_rejected():
    manager = BoundaryManager()
    manager.register(BoundaryRegion("ghost", [99]))
    with pytest.raises(ValueError, match="unknown facet"):
        MeshRepresentationBuilder()(_two_triangle_mesh(), manager)


def test_region_with_negative_facet_id_is_rejected():
    manager = BoundaryManager()
    manager.register(BoundaryRegion("ghost", [-1]))
    with pytest.raises(ValueError, match="unknown facet"):
        MeshRepresentationBuilder()(_two_triangle_mesh(), manager)


@pytest.mark.parametrize(
    ("cell_type", "node_count", "topo_dim", "unique_edges"),
    [
        (CellType.LINE2, 2, 1, 1),
        (CellType.TRI3, 3, 2, 3),
        (CellType.QUAD4, 4, 2, 4),
        (CellType.TET4, 4, 3, 6),
        (CellType.PYR5, 5, 3, 8),
        (CellType.WEDGE6, 6, 3, 9),
        (CellType.HEX8, 8, 3, 12),
    ],
)
def test_unique_edge_counts_per_cell_type(
    cell_type, node_count, topo_dim, unique_edges
):
    # ADR-019 reference table: candidates != unique edges (all 7 types;
    # the LINE2 case also re-exercises the 1D special-case branch on a
    # bare mesh, complementing the facet-context 1D test)
    mesh = Mesh(
        "single_cell",
        nodes=[[float(index), 0.0, 0.0] for index in range(node_count)],
        topo_dim=topo_dim,
        cell_types=[cell_type.code],
        cells=list(range(node_count)),
        cell_offsets=[0, node_count],
    )
    graph = MeshRepresentationBuilder()(mesh)
    assert len(graph.edges) == unique_edges


def test_degenerate_same_endpoint_candidates_are_discarded():
    mesh = Mesh(
        "degenerate_tri",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        topo_dim=2,
        cell_types=[CellType.TRI3.code],
        cells=[0, 1, 1],  # repeated node -> face (1, 2) degenerates to (1, 1)
        cell_offsets=[0, 3],
    )
    graph = MeshRepresentationBuilder()(mesh)
    # faces (0,1),(1,1),(1,0): (1,1) discarded, the rest collapse to (0,1)
    assert graph.edges == ((0, 1),)


def test_node_field_length_is_validated():
    mesh = _two_triangle_mesh()
    pressure = Field("p", association="node")
    with pytest.raises(ValueError, match="requires 4"):
        MeshRepresentationBuilder()(
            mesh,
            fields=[pressure],
            field_data=[FieldData(pressure, [1.0, 2.0, 3.0], scope="global")],
        )
    graph = MeshRepresentationBuilder()(
        mesh,
        fields=[pressure],
        field_data=[FieldData(pressure, [1.0, 2.0, 3.0, 4.0], scope="global")],
    )
    assert [field.name for field in graph.associated_fields] == ["p"]
    assert len(graph.field_data) == 1


def test_cell_field_length_is_validated():
    mesh = _two_triangle_mesh()
    volume = Field("vol", association="cell")
    with pytest.raises(ValueError, match="requires 2"):
        MeshRepresentationBuilder()(
            mesh,
            fields=[volume],
            field_data=[FieldData(volume, [1.0], scope="global")],
        )
    MeshRepresentationBuilder()(
        mesh,
        fields=[volume],
        field_data=[FieldData(volume, [1.0, 2.0], scope="global")],
    )


def test_unsized_values_for_sized_association_are_rejected():
    mesh = _two_triangle_mesh()
    flag = Field("flag", association="node")
    with pytest.raises(ValueError, match="sized"):
        MeshRepresentationBuilder()(
            mesh,
            fields=[flag],
            field_data=[FieldData(flag, 3.0, scope="global")],
        )


def test_unsupported_family_declaration_is_expressible():
    # ADR-021 D2/D5: the declaration vocabulary is open — an
    # unsupported-family declaration is legal on its own; only its
    # realizations are barred (rejected at FieldData construction).
    mesh = _two_triangle_mesh()
    graph = MeshRepresentationBuilder()(
        mesh, fields=[Field("meta", association="particle")]
    )
    assert [field.name for field in graph.associated_fields] == ["meta"]


def test_declaration_only_fields_are_legal():
    # ADR-020 D4: problem-before-solving — a declaration-only field
    # set is legal and performs no payload validation (invariant
    # registry ADR-020-D4-01).
    mesh = _two_triangle_mesh()
    graph = MeshRepresentationBuilder()(mesh, fields=[Field("p", association="node")])
    assert [field.name for field in graph.associated_fields] == ["p"]
    assert graph.field_data == ()


def test_multiple_field_data_per_field_are_stored():
    # ADR-020 D6: representation construction legally stores multiple
    # realizations per Field — no silent selection at storage time
    # (invariant registry ADR-020-D6-01).
    mesh = _two_triangle_mesh()
    pressure = Field("p", association="node")
    frame0 = FieldData(pressure, [1.0, 2.0, 3.0, 4.0], timestep=0, scope="global")
    frame1 = FieldData(pressure, [2.0, 3.0, 4.0, 5.0], timestep=1, scope="global")
    graph = MeshRepresentationBuilder()(
        mesh, fields=[pressure], field_data=[frame0, frame1]
    )
    assert graph.field_data == (frame0, frame1)


def test_dangling_field_data_is_rejected():
    mesh = _two_triangle_mesh()
    pressure = Field("p", association="node")
    with pytest.raises(ValueError, match="declaration"):
        MeshRepresentationBuilder()(
            mesh,
            fields=[],
            field_data=[FieldData(pressure, [1.0, 2.0, 3.0, 4.0], scope="global")],
        )


def test_same_name_different_field_object_is_rejected():
    # Phase 2 implementation consistency guard: a realization must
    # reference the declared Field OBJECT — a distinct object that
    # merely shares the name would smuggle different semantics (kPa /
    # cell here) under the declared identity. Implementation-level
    # guard only; not an ADR-020 D3 identity/reference freeze.
    mesh = _two_triangle_mesh()
    declared = Field("p", unit="Pa", association="node")
    same_name = Field("p", unit="kPa", association="cell")
    with pytest.raises(ValueError, match="declared Field object"):
        MeshRepresentationBuilder()(
            mesh,
            fields=[declared],
            field_data=[FieldData(same_name, [1.0, 2.0, 3.0, 4.0], scope="global")],
        )


def test_non_mesh_source_is_rejected():
    with pytest.raises(TypeError, match="Mesh"):
        MeshRepresentationBuilder()("two_tri")  # type: ignore[arg-type]


def test_mesh_without_facets_constructs_all_interior():
    mesh = Mesh(
        "bare",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        topo_dim=2,
        cell_types=[CellType.TRI3.code],
        cells=[0, 1, 2],
        cell_offsets=[0, 3],
    )
    graph = MeshRepresentationBuilder()(mesh)
    assert graph.edges == ((0, 1), (0, 2), (1, 2))
    assert graph.node_categories == (NodeCategory.INTERIOR,) * 3
