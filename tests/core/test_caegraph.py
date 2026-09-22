"""Tests for caegraph.core.caegraph.CAEGraph (ADR-015/018)."""

from __future__ import annotations

import pytest

import caegraph.core
from caegraph.core import (
    BoundaryRegion,
    BoundarySpec,
    BoundaryType,
    CAEGraph,
    Field,
    Mesh,
    NodeCategory,
)
from caegraph.core.topology.celltype import CellType


def _tiny_mesh() -> Mesh:
    """Minimal valid cell-based topology provider (single TRI3)."""
    return Mesh(
        "tri_mesh",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        topo_dim=2,
        cell_types=[CellType.TRI3.code],
        cells=[0, 1, 2],
        cell_offsets=[0, 3],
    )


def test_construction_without_topology_is_the_mesh_free_state():
    graph = CAEGraph("channel_flow")
    assert graph.name == "channel_flow"
    assert graph.topology is None


def test_topology_provider_is_referenced_not_required():
    provider = _tiny_mesh()
    graph = CAEGraph("channel_flow", topology=provider)
    assert graph.topology is provider


def test_non_mesh_topology_is_rejected():
    with pytest.raises(TypeError, match="topology"):
        CAEGraph("channel_flow", topology=object())  # type: ignore[arg-type]


def test_field_cannot_impersonate_a_topology_provider():
    # ADR-018: only topology-subsystem objects qualify as providers;
    # a Field is domain-truth but belongs to a different family.
    with pytest.raises(TypeError, match="topology"):
        CAEGraph("channel_flow", topology=Field("pressure", [1.0]))  # type: ignore[arg-type]


def test_regions_cannot_impersonate_a_topology_provider():
    with pytest.raises(TypeError, match="topology"):
        CAEGraph(
            "channel_flow",
            topology=BoundaryRegion("fluid_wall", [1]),  # type: ignore[arg-type]
        )


def test_empty_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        CAEGraph("   ")


def test_boundary_manager_is_available():
    graph = CAEGraph("channel_flow")
    graph.boundaries.register(BoundaryRegion("fluid_wall", [1, 2]))
    graph.boundaries.bind(BoundarySpec("fluid_wall", BoundaryType.DIRICHLET, value=0.0))
    assert len(graph.boundaries) == 1
    assert graph.boundaries.region("fluid_wall").membership == frozenset({1, 2})


def test_associate_field_keeps_reference_semantics():
    graph = CAEGraph("channel_flow")
    field = Field("pressure", [0.1, 0.2], association="node")
    graph.associate_field(field)
    assert graph.associated_fields == (field,)


def test_associated_fields_are_ordered_by_name():
    graph = CAEGraph("channel_flow")
    pressure = Field("pressure", [1.0])
    velocity = Field("velocity", [2.0])
    graph.associate_field(pressure)
    graph.associate_field(velocity)
    assert graph.associated_fields == (pressure, velocity)


def test_duplicate_field_names_are_rejected():
    graph = CAEGraph("channel_flow")
    graph.associate_field(Field("pressure", [1.0]))
    with pytest.raises(ValueError, match="already associated"):
        graph.associate_field(Field("pressure", [2.0]))


def test_associate_field_rejects_non_fields():
    with pytest.raises(TypeError, match="Field"):
        CAEGraph("channel_flow").associate_field("pressure")  # type: ignore[arg-type]


def test_associate_field_skips_cardinality_validation():
    # ADR-019 D5: associate_field is a lightweight association API —
    # topology-cardinality checks happen only at construction time.
    # The field below is intentionally mismatched (2 values vs 3
    # entities); Field itself performs no cardinality check, so both
    # the field construction and this association succeeding prove
    # the lightweight contract (invariant registry ADR-019-D5-04).
    graph = CAEGraph("g", n_entities=3, edges=[(0, 1), (1, 2)])
    field = Field("pressure", [1.0, 2.0], association="node")
    graph.associate_field(field)
    assert graph.associated_fields == (field,)


def test_metadata_is_carried_through():
    graph = CAEGraph("channel_flow", metadata={"case": "re200"})
    assert graph.metadata == {"case": "re200"}


def test_metadata_is_defensively_copied():
    source = {"case": "re200"}
    graph = CAEGraph("channel_flow", metadata=source)
    source["case"] = "mutated"
    assert graph.metadata == {"case": "re200"}


def test_repr_shows_class_and_name():
    assert repr(CAEGraph("channel_flow")) == "CAEGraph(name='channel_flow')"


# --- construction-time entity/relation model (ADR-019) ----------------------


def test_graph_data_defaults_to_empty_entity_model():
    graph = CAEGraph("channel_flow")
    assert graph.n_entities == 0
    assert graph.edges == ()
    assert graph.node_categories == ()


def test_graph_data_is_normalized_at_construction():
    graph = CAEGraph("g", n_entities=3, edges=[(2, 0), (1, 0), (0, 1)])
    assert graph.edges == ((0, 1), (0, 2))
    assert graph.node_categories == (
        NodeCategory.INTERIOR,
        NodeCategory.INTERIOR,
        NodeCategory.INTERIOR,
    )


def test_explicit_node_categories_are_stored():
    graph = CAEGraph(
        "g",
        n_entities=2,
        edges=[(0, 1)],
        node_categories=[NodeCategory.BOUNDARY, NodeCategory.CORNER],
    )
    assert graph.node_categories == (NodeCategory.BOUNDARY, NodeCategory.CORNER)


def test_graph_data_requires_n_entities():
    with pytest.raises(ValueError, match="n_entities is required"):
        CAEGraph("g", edges=[(0, 1)])


def test_non_positive_n_entities_is_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        CAEGraph("g", n_entities=0)


def test_bool_n_entities_is_rejected():
    with pytest.raises(TypeError, match="integer"):
        CAEGraph("g", n_entities=True)  # type: ignore[arg-type]


def test_self_loop_edges_are_rejected():
    with pytest.raises(ValueError, match="self-loop"):
        CAEGraph("g", n_entities=2, edges=[(1, 1)])


def test_out_of_range_edges_are_rejected():
    with pytest.raises(ValueError, match="out of range"):
        CAEGraph("g", n_entities=2, edges=[(0, 5)])


def test_malformed_edge_pairs_are_rejected():
    with pytest.raises(ValueError, match=r"\(int, int\) pairs"):
        CAEGraph("g", n_entities=2, edges=[(0, 1, 2)])  # type: ignore[list-item]


@pytest.mark.parametrize("bad_edge", [(0.5, 1), ("0", 1), (0, True), (False, 0)])
def test_non_integer_edge_endpoints_are_rejected(bad_edge):
    # entity IDs are canonical node indices (ADR-019) — floats,
    # strings and bools must fail fast with a clear TypeError
    with pytest.raises(TypeError, match="edge endpoints must be integers"):
        CAEGraph("g", n_entities=2, edges=[bad_edge])  # type: ignore[list-item]


def test_node_categories_length_must_match():
    with pytest.raises(ValueError, match="match n_entities"):
        CAEGraph("g", n_entities=3, node_categories=[NodeCategory.INTERIOR])


def test_non_enum_categories_are_rejected():
    with pytest.raises(TypeError, match="NodeCategory"):
        CAEGraph("g", n_entities=1, node_categories=["interior"])  # type: ignore[list-item]


def test_no_entity_wrapper_classes_or_cell_entity_storage():
    # ADR-019 D1: entity identity lives in canonical Mesh indices —
    # wrapper classes or duplicated cell-entity storage must never
    # appear (invariant registry ADR-019-D1-03). Assertions turn red
    # the moment such a wrapper or storage member is introduced.
    assert not hasattr(caegraph.core, "NodeEntity")
    assert not hasattr(caegraph.core, "CellEntity")
    graph = CAEGraph("g", n_entities=2, edges=[(0, 1)])
    assert not hasattr(graph, "cell_entities")
    assert not hasattr(graph, "node_entities")


# --- validate() invariant tamper paths (ADR-019) ------------------------------


def test_validate_rejects_tampered_non_canonical_edges():
    graph = CAEGraph("g", n_entities=3, edges=[(0, 1)])
    graph._edges = ((1, 0),)  # type: ignore[assignment]
    with pytest.raises(ValueError, match="canonical"):
        graph.validate()


def test_validate_rejects_tampered_out_of_range_edges():
    graph = CAEGraph("g", n_entities=2, edges=[(0, 1)])
    graph._edges = ((0, 5),)  # type: ignore[assignment]
    with pytest.raises(ValueError, match="out of range"):
        graph.validate()


def test_validate_rejects_tampered_unsorted_duplicated_edges():
    graph = CAEGraph("g", n_entities=3, edges=[(0, 1), (1, 2)])
    graph._edges = ((1, 2), (1, 2))  # type: ignore[assignment]
    with pytest.raises(ValueError, match="sorted and deduplicated"):
        graph.validate()


def test_validate_rejects_tampered_category_length():
    graph = CAEGraph("g", n_entities=2, edges=[(0, 1)])
    graph._node_categories = (NodeCategory.INTERIOR,)  # type: ignore[assignment]
    with pytest.raises(ValueError, match="match n_entities"):
        graph.validate()
