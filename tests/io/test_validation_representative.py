"""Representative source -> canonical validation evidence (Gate 5 Batch 3).

One known-answer end-to-end case over a synthetic real-format Gmsh
source: cross-block TET4 volumes + declared TRI3 surface groups + a
lower-dimensional LINE2 marker group, chained through the loader into
the canonical Mesh, the representation builder and the CAEGraph.

ID discipline: exact numeric IDs are asserted only where the contract
guarantees determinism (dense ID spaces, in-range membership, declared
facet count). Group membership is validated as the *semantic mapping*
of source entities to canonical entities via connectivity node sets —
the meshio block traversal order is an implementation detail and is
deliberately not frozen here (ADR-012 normalization obligations;
ADR-014 canonical identity).
"""

from __future__ import annotations

from pathlib import Path

import meshio
import numpy as np
import pytest

from caegraph.core import BoundaryManager, BoundaryRegion
from caegraph.core.topology.mesh import canonical_facet_nodes
from caegraph.graph import MeshRepresentationBuilder
from caegraph.io import GmshLoader

_TET_A = (0, 1, 2, 3)
_TET_B = (1, 4, 2, 3)
_SHARED_FACE = (1, 2, 3)
_SURFACE_TRIANGLES = (
    (0, 1, 2),
    (0, 1, 3),
    (0, 2, 3),  # tet A exterior
    (1, 4, 2),
    (1, 4, 3),
    (2, 4, 3),  # tet B exterior
)


def _representative_source(tmp_path: Path) -> Path:
    """Two-block TET4 volume + declared TRI3 skin + dim-1 curve markers."""
    points = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
    ]
    cells = [
        ("tetra", np.array([list(_TET_A)])),
        ("tetra", np.array([list(_TET_B)])),
        ("triangle", np.array([list(triangle) for triangle in _SURFACE_TRIANGLES])),
        ("line", np.array([[0, 1]])),
    ]
    cell_data = {
        "gmsh:physical": [
            np.array([1]),
            np.array([1]),
            np.array([5] * len(_SURFACE_TRIANGLES)),
            np.array([9]),
        ]
    }
    field_data = {
        "solid": [1, 3],
        "skin": [5, 2],
        "skin_mirror": [5, 2],
        "markers": [9, 1],
    }
    path = tmp_path / "representative.msh"
    mesh = meshio.Mesh(
        np.asarray(points, dtype=np.float64),
        cells,
        cell_data=cell_data,
        field_data=field_data,
    )
    meshio.write(str(path), mesh, file_format="gmsh22", binary=False)
    return path


def test_representative_source_to_canonical_chain(tmp_path):
    path = _representative_source(tmp_path)
    with pytest.warns(UserWarning, match="markers"):
        mesh = GmshLoader()(path)
    mesh.validate()

    # --- canonical cell space: semantic source-entity mapping ----------
    # topo_dim comes from the highest supported source-cell dimension
    # (3), never from the groups; both volume blocks land in one cell
    # space with dense canonical IDs.
    assert mesh.topo_dim == 3
    assert mesh.n_cells == 2
    cell_node_sets = {
        frozenset(mesh.cell_nodes(index).tolist()) for index in range(mesh.n_cells)
    }
    assert cell_node_sets == {
        frozenset(_TET_A),
        frozenset(_TET_B),
    }
    solid_ids = mesh.domain_groups["solid"]
    assert solid_ids.dtype == np.dtype(np.int64)
    assert set(int(value) for value in solid_ids) == set(range(mesh.n_cells))
    assert {
        frozenset(mesh.cell_nodes(int(cell_id)).tolist()) for cell_id in solid_ids
    } == {frozenset(_TET_A), frozenset(_TET_B)}

    # --- declared facet namespace: winding-free semantic identity ------
    # Exactly the six adapter-declared surface triangles enter the
    # facet table (ADR-014 decision 2); the shared interior face
    # {1,2,3} — never referenced by a source group — stays out, and so
    # do the dim-1 markers.
    assert mesh.n_facets == len(_SURFACE_TRIANGLES)
    expected_canonical = {
        canonical_facet_nodes(triangle) for triangle in _SURFACE_TRIANGLES
    }
    actual_canonical = {
        tuple(mesh.facet_nodes(index).tolist()) for index in range(mesh.n_facets)
    }
    assert actual_canonical == expected_canonical
    assert canonical_facet_nodes(_SHARED_FACE) not in actual_canonical

    # boundary groups carry global facet IDs; both names referencing
    # the same source triangles resolve to the same facet set — and
    # their union covers every declared facet exactly once.
    carriers = mesh.metadata["boundary_source_groups"]
    facet_id_sets = {
        name: {int(value) for value in facet_ids}
        for name, facet_ids in carriers.items()
    }
    assert facet_id_sets["skin"] == facet_id_sets["skin_mirror"]
    assert facet_id_sets["skin"] | facet_id_sets["skin_mirror"] == set(
        range(mesh.n_facets)
    )
    for facet_id in facet_id_sets["skin"]:
        assert tuple(mesh.facet_nodes(facet_id).tolist()) in expected_canonical
    assert "markers" not in carriers

    # --- facet_cells: node-set adjacency semantics ----------------------
    # Every declared facet is adjacent to the cells whose codim-1 face
    # carries the same node set; all six skin triangles are exterior
    # faces of exactly one tet.
    for index in range(mesh.n_facets):
        node_set = frozenset(mesh.facet_nodes(index).tolist())
        adjacency = mesh.facet_adjacent_cells(index)
        assert len(adjacency) == 1
        owner = mesh.cell_nodes(adjacency[0]).tolist()
        assert node_set <= set(owner)

    # --- full consumer chain: builder -> CAEGraph -----------------------
    manager = BoundaryManager()
    for name, facet_ids in sorted(carriers.items()):
        manager.register(BoundaryRegion(name, facet_ids))
    graph = MeshRepresentationBuilder()(mesh, manager)
    graph.validate()
    assert graph.n_entities == mesh.n_nodes
