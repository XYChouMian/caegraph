"""Conformance pins for the BaseObject validation layering (ARCHITECTURE.md §3.4)."""

from __future__ import annotations

from caegraph.core import BaseObject, BoundaryRegion, CAEGraph, Field, Mesh
from caegraph.core.topology.celltype import CellType


def _sample_objects() -> list[BaseObject]:
    """One instance of every BaseObject subclass in the core layer."""
    mesh = Mesh(
        "tri",
        nodes=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        topo_dim=2,
        cell_types=[CellType.TRI3.code],
        cells=[0, 1, 2],
        cell_offsets=[0, 3],
    )
    return [
        CAEGraph("g", topology=mesh, n_entities=3, edges=[(0, 1)]),
        mesh,
        Field("pressure", [1.0, 2.0, 3.0], association="node"),
        BoundaryRegion("wall", [0]),
    ]


def test_core_subclasses_declare_no_metadata_semantics():
    # ARCHITECTURE.md §3.4: metadata is an annotation channel unless a
    # class assigns domain semantics to metadata keys. The Phase 2 core
    # subclasses explicitly declare none, so they must not override the
    # mutation hook — adding metadata semantics later must be a
    # deliberate change that updates this pin (decision made visible).
    for obj in _sample_objects():
        assert type(obj).on_metadata_changed is BaseObject.on_metadata_changed, (
            f"{type(obj).__name__} must not override on_metadata_changed "
            "without declaring metadata semantics (ARCHITECTURE.md §3.4)"
        )
