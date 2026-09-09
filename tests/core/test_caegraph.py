"""Tests for caegraph.core.caegraph.CAEGraph (ADR-015/018)."""

from __future__ import annotations

import pytest

from caegraph.core import (
    BaseObject,
    BoundaryRegion,
    BoundarySpec,
    BoundaryType,
    CAEGraph,
    Field,
)


class _TopologyProbe(BaseObject):
    """Minimal stand-in for the cell-based Mesh provider (gate 3)."""

    def validate(self) -> None:
        return None


def test_construction_without_topology_is_the_mesh_free_state():
    graph = CAEGraph("channel_flow")
    assert graph.name == "channel_flow"
    assert graph.topology is None


def test_topology_provider_is_referenced_not_required():
    provider = _TopologyProbe("tri_mesh")
    graph = CAEGraph("channel_flow", topology=provider)
    assert graph.topology is provider


def test_non_base_object_topology_is_rejected():
    with pytest.raises(TypeError, match="topology"):
        CAEGraph("channel_flow", topology=object())  # type: ignore[arg-type]


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
