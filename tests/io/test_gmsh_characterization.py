"""P2-PERF-02a-1 Phase 0 characterization oracle: Source -> Mesh public semantics.

Freezes the ``GmshLoader()(path) -> Mesh`` public contract (ADR-012
pipeline, ADR-014 canonical data model) that the 02a-1 NumPy-first
internal restructuring must reproduce unchanged. The oracle anchors
public semantics only:

- exact equality for the frozen integer payload — connectivity
  contents, dense canonical IDs, CSR offsets, public group mappings,
  canonical winding-free facet forms and ``facet_cells`` adjacency;
- ``np.allclose`` with the Phase-0 coordinate tolerance (see
  ``_RTOL``/``_ATOL`` below) for float payloads;
- lower-dimensional diagnostics by warning category + group name.

Deliberately NOT frozen here: ``_NormalizedSource`` / ``_SourceBlock``
and any private container form, shape or layout; the normalization
steps; the raw physical-tag representation; warning message text; the
mesh name derivation; and the ``KeyError`` raised when a declared
facet matches no codim-1 face (recorded backlog, not contract).
"""

from __future__ import annotations

from pathlib import Path

import meshio
import numpy as np
import pytest

from caegraph.core import CellType
from caegraph.core.topology.mesh import canonical_facet_nodes
from caegraph.io import GmshLoader

# Phase-0 tolerance proposal for float payloads (node coordinates).
# meshio writes gmsh 2.2 ASCII coordinates with 16 significant digits
# (``.16e``) while exact float64 round-trip needs 17; the loader
# passes coordinates through with no arithmetic (2D sources are only
# zero-padded). 1e-15 covers the ~5e-16 formatting bound with ~2x
# headroom; on these fixtures the measured round-trip error is 0.0
# (binary-exact coordinate values). PM-frozen after the Phase-0 stop
# report; Phase 1 must reuse verbatim and must not widen.
_RTOL = 1e-15
_ATOL = 1e-15


def _write_msh(
    tmp_path: Path,
    name: str,
    points,
    cells,
    cell_data=None,
    field_data=None,
):
    """Write a synthetic real-format Gmsh 2.2 ASCII file and return its path."""
    path = tmp_path / name
    mesh = meshio.Mesh(
        np.asarray(points, dtype=np.float64),
        list(cells),
        cell_data=cell_data,
        field_data=field_data,
    )
    meshio.write(str(path), mesh, file_format="gmsh22", binary=False)
    return path


# 1 — dual-TET4 primary fixture -----------------------------------------------------


_TET_POINTS = [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 1.0, 1.0],
]
_TET_SOURCE_TRIANGLES = ((0, 1, 2), (0, 2, 3), (1, 4, 3), (1, 2, 3))


def _tet_pair_source(tmp_path: Path, *, reverse_windings: bool = False) -> Path:
    """Two TET4 blocks sharing face {1,2,3}, declared as an interface group.

    Entity stream: tetra A (omega_a), tetra B (omega_b), one triangle
    block (wall, wall, inlet, interface) and one dim-1 line block
    (axis). ``reverse_windings`` flips every facet winding only — cell
    connectivity keeps its source order.
    """
    triangles = (
        [list(reversed(triangle)) for triangle in _TET_SOURCE_TRIANGLES]
        if reverse_windings
        else [list(triangle) for triangle in _TET_SOURCE_TRIANGLES]
    )
    lines = [[1, 0]] if reverse_windings else [[0, 1]]
    return _write_msh(
        tmp_path,
        "tet_pair.msh",
        points=_TET_POINTS,
        cells=[
            ("tetra", np.array([[0, 1, 2, 3]])),
            ("tetra", np.array([[1, 4, 2, 3]])),
            ("triangle", np.array(triangles)),
            ("line", np.array(lines)),
        ],
        cell_data={
            "gmsh:physical": [
                np.array([1]),
                np.array([2]),
                np.array([3, 3, 4, 5]),
                np.array([9]),
            ]
        },
        field_data={
            "omega_a": [1, 3],
            "omega_b": [2, 3],
            "wall": [3, 2],
            "inlet": [4, 2],
            "interface": [5, 2],
            "axis": [9, 1],
        },
    )


def test_tet_pair_public_output_is_frozen(tmp_path):
    path = _tet_pair_source(tmp_path)
    with pytest.warns(UserWarning, match="axis"):
        mesh = GmshLoader()(path)
    mesh.validate()

    # counts, dimensionality and the coordinate contract
    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets) == (5, 2, 4)
    assert mesh.topo_dim == 3
    assert mesh.nodes.shape == (5, 3)
    assert mesh.nodes.dtype == np.dtype(np.float64)
    assert np.allclose(mesh.nodes, _TET_POINTS, rtol=_RTOL, atol=_ATOL)

    # canonical cell space: cross-block dense enumeration, cell IDs 0/1
    # carry the tetra blocks in source-entity stream order
    assert mesh.cell_types.tolist() == [CellType.TET4.code, CellType.TET4.code]
    assert mesh.cells.tolist() == [0, 1, 2, 3, 1, 4, 2, 3]
    assert mesh.cell_offsets.tolist() == [0, 4, 8]
    assert mesh.cell_nodes(0).tolist() == [0, 1, 2, 3]
    assert mesh.cell_nodes(1).tolist() == [1, 4, 2, 3]

    # declared facet namespace: exactly the four adapter-declared
    # triangles enter the table in declaration order, each stored in
    # canonical winding-free form
    assert mesh.facet_types.tolist() == [CellType.TRI3.code] * 4
    assert mesh.facets.tolist() == [0, 1, 2, 0, 2, 3, 1, 3, 4, 1, 2, 3]
    assert mesh.facet_offsets.tolist() == [0, 3, 6, 9, 12]
    for index, expected in enumerate(_TET_SOURCE_TRIANGLES):
        assert tuple(mesh.facet_nodes(index).tolist()) == canonical_facet_nodes(
            expected
        )

    # facet_cells adjacency: exterior facets carry their single owner,
    # the declared interface facet carries both cross-block cells
    assert mesh.facet_cells == ((0,), (0,), (1,), (0, 1))

    # public group mappings
    assert set(mesh.domain_groups) == {"omega_a", "omega_b"}
    assert mesh.domain_groups["omega_a"].tolist() == [0]
    assert mesh.domain_groups["omega_b"].tolist() == [1]
    carriers = mesh.metadata["boundary_source_groups"]
    assert carriers == {"wall": (0, 1), "inlet": (2,), "interface": (3,)}
    assert mesh.metadata["source_format"] == "gmsh"
    union = {facet_id for ids in carriers.values() for facet_id in ids}
    assert union == set(range(mesh.n_facets))


def test_tet_pair_winding_variant_is_identical(tmp_path):
    straight_dir = tmp_path / "a"
    flipped_dir = tmp_path / "b"
    straight_dir.mkdir()
    flipped_dir.mkdir()
    with pytest.warns(UserWarning, match="axis"):
        straight = GmshLoader()(_tet_pair_source(straight_dir))
    with pytest.warns(UserWarning, match="axis"):
        flipped = GmshLoader()(_tet_pair_source(flipped_dir, reverse_windings=True))
    for table in (
        "nodes",
        "cells",
        "cell_types",
        "cell_offsets",
        "facets",
        "facet_types",
        "facet_offsets",
    ):
        np.testing.assert_array_equal(getattr(straight, table), getattr(flipped, table))
    assert straight.facet_cells == flipped.facet_cells
    assert (
        straight.metadata["boundary_source_groups"]
        == flipped.metadata["boundary_source_groups"]
    )
    for name in ("omega_a", "omega_b"):
        np.testing.assert_array_equal(
            straight.domain_groups[name], flipped.domain_groups[name]
        )


def test_tet_pair_lower_dimension_group_is_diagnosed_and_excluded(tmp_path):
    path = _tet_pair_source(tmp_path)
    with pytest.warns(UserWarning, match="axis"):
        mesh = GmshLoader()(path)
    mesh.validate()
    # dim 1 < topo_dim - 1 = 2: diagnosed, excluded from the canonical
    # topology and absent from the boundary source groups (ADR-012 decision 2)
    assert mesh.n_cells == 2
    assert mesh.n_facets == 4
    assert "axis" not in mesh.metadata["boundary_source_groups"]


# 2 — dual-QUAD4 fixture (2D edge facet namespace) -----------------------------------


_QUAD_POINTS = [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [2.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [1.0, 1.0, 0.0],
    [2.0, 1.0, 0.0],
]
_QUAD_SOURCE_LINES = ((0, 1), (1, 4), (2, 5))


def _quad_pair_source(tmp_path: Path) -> Path:
    """Two QUAD4 blocks sharing edge {1,4}, declared as an interface group."""
    return _write_msh(
        tmp_path,
        "quad_pair.msh",
        points=_QUAD_POINTS,
        cells=[
            ("quad", np.array([[0, 1, 4, 3]])),
            ("quad", np.array([[1, 2, 5, 4]])),
            ("line", np.array([list(line) for line in _QUAD_SOURCE_LINES])),
        ],
        cell_data={
            "gmsh:physical": [
                np.array([1]),
                np.array([2]),
                np.array([3, 5, 4]),
            ]
        },
        field_data={
            "omega_a": [1, 2],
            "omega_b": [2, 2],
            "wall": [3, 1],
            "interface": [5, 1],
            "inlet": [4, 1],
        },
    )


def test_quad_pair_public_output_is_frozen(tmp_path):
    mesh = GmshLoader()(_quad_pair_source(tmp_path))
    mesh.validate()

    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets) == (6, 2, 3)
    assert mesh.topo_dim == 2
    assert np.allclose(mesh.nodes, _QUAD_POINTS, rtol=_RTOL, atol=_ATOL)

    assert mesh.cell_types.tolist() == [CellType.QUAD4.code, CellType.QUAD4.code]
    assert mesh.cells.tolist() == [0, 1, 4, 3, 1, 2, 5, 4]
    assert mesh.cell_offsets.tolist() == [0, 4, 8]
    assert mesh.cell_nodes(0).tolist() == [0, 1, 4, 3]
    assert mesh.cell_nodes(1).tolist() == [1, 2, 5, 4]

    # QUAD4 codim-1 faces are LINE2 facets; the shared edge is the
    # declared interface with two-owner adjacency
    assert mesh.facet_types.tolist() == [CellType.LINE2.code] * 3
    assert mesh.facets.tolist() == [0, 1, 1, 4, 2, 5]
    assert mesh.facet_offsets.tolist() == [0, 2, 4, 6]
    for index, expected in enumerate(_QUAD_SOURCE_LINES):
        assert tuple(mesh.facet_nodes(index).tolist()) == canonical_facet_nodes(
            expected
        )
    assert mesh.facet_cells == ((0,), (0, 1), (1,))

    assert set(mesh.domain_groups) == {"omega_a", "omega_b"}
    assert mesh.domain_groups["omega_a"].tolist() == [0]
    assert mesh.domain_groups["omega_b"].tolist() == [1]
    carriers = mesh.metadata["boundary_source_groups"]
    assert carriers == {"wall": (0,), "interface": (1,), "inlet": (2,)}


# 3 — dual-HEX8 fixture (3D quad facet namespace) ------------------------------------


_HEX_POINTS = [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 0.0, 1.0],
    [1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0],
    [2.0, 0.0, 0.0],
    [2.0, 1.0, 0.0],
    [2.0, 0.0, 1.0],
    [2.0, 1.0, 1.0],
]
_HEX_SOURCE_QUADS = ((0, 3, 2, 1), (1, 2, 6, 5), (8, 9, 11, 10))


def _hex_pair_source(tmp_path: Path) -> Path:
    """Two HEX8 blocks sharing the x=1 quad face, declared as an interface group."""
    return _write_msh(
        tmp_path,
        "hex_pair.msh",
        points=_HEX_POINTS,
        cells=[
            ("hexahedron", np.array([[0, 1, 2, 3, 4, 5, 6, 7]])),
            ("hexahedron", np.array([[1, 8, 9, 2, 5, 10, 11, 6]])),
            ("quad", np.array([list(quad) for quad in _HEX_SOURCE_QUADS])),
        ],
        cell_data={
            "gmsh:physical": [
                np.array([1]),
                np.array([2]),
                np.array([3, 5, 4]),
            ]
        },
        field_data={
            "omega_a": [1, 3],
            "omega_b": [2, 3],
            "wall": [3, 2],
            "interface": [5, 2],
            "inlet": [4, 2],
        },
    )


def test_hex_pair_public_output_is_frozen(tmp_path):
    mesh = GmshLoader()(_hex_pair_source(tmp_path))
    mesh.validate()

    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets) == (12, 2, 3)
    assert mesh.topo_dim == 3
    assert np.allclose(mesh.nodes, _HEX_POINTS, rtol=_RTOL, atol=_ATOL)

    assert mesh.cell_types.tolist() == [CellType.HEX8.code, CellType.HEX8.code]
    assert mesh.cells.tolist() == [0, 1, 2, 3, 4, 5, 6, 7, 1, 8, 9, 2, 5, 10, 11, 6]
    assert mesh.cell_offsets.tolist() == [0, 8, 16]
    assert mesh.cell_nodes(0).tolist() == [0, 1, 2, 3, 4, 5, 6, 7]
    assert mesh.cell_nodes(1).tolist() == [1, 8, 9, 2, 5, 10, 11, 6]

    # HEX8 codim-1 faces are QUAD4 facets stored in canonical
    # winding-free form; the shared x=1 face is the two-owner interface
    assert mesh.facet_types.tolist() == [CellType.QUAD4.code] * 3
    assert mesh.facets.tolist() == [0, 1, 2, 3, 1, 2, 6, 5, 8, 9, 11, 10]
    assert mesh.facet_offsets.tolist() == [0, 4, 8, 12]
    for index, expected in enumerate(_HEX_SOURCE_QUADS):
        assert tuple(mesh.facet_nodes(index).tolist()) == canonical_facet_nodes(
            expected
        )
    assert mesh.facet_cells == ((0,), (0, 1), (1,))

    assert set(mesh.domain_groups) == {"omega_a", "omega_b"}
    assert mesh.domain_groups["omega_a"].tolist() == [0]
    assert mesh.domain_groups["omega_b"].tolist() == [1]
    carriers = mesh.metadata["boundary_source_groups"]
    assert carriers == {"wall": (0,), "interface": (1,), "inlet": (2,)}


# 4 — PYRA5 + WEDGE6 mixed fixture (heterogeneous facet types) ------------------------


_PYR_WEDGE_POINTS = [
    [0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.5, 0.5, 1.0],
    [2.0, 0.0, 0.0],
    [3.0, 0.0, 0.0],
    [2.0, 1.0, 0.0],
    [2.0, 0.0, 1.0],
    [3.0, 0.0, 1.0],
    [2.0, 1.0, 1.0],
]
_PYR_WEDGE_SOURCE_TRIANGLES = ((0, 1, 4), (5, 6, 7))
_PYR_WEDGE_SOURCE_QUADS = ((0, 1, 2, 3), (5, 6, 9, 8))


def _pyra_wedge_source(tmp_path: Path) -> Path:
    """One PYR5 block + one WEDGE6 block (same topo_dim) with declared
    triangle and quad facets: a PYR5 side + base, a WEDGE6 bottom + side."""
    return _write_msh(
        tmp_path,
        "pyra_wedge.msh",
        points=_PYR_WEDGE_POINTS,
        cells=[
            ("pyramid", np.array([[0, 1, 2, 3, 4]])),
            ("wedge", np.array([[5, 6, 7, 8, 9, 10]])),
            (
                "triangle",
                np.array([list(triangle) for triangle in _PYR_WEDGE_SOURCE_TRIANGLES]),
            ),
            ("quad", np.array([list(quad) for quad in _PYR_WEDGE_SOURCE_QUADS])),
        ],
        cell_data={
            "gmsh:physical": [
                np.array([1]),
                np.array([2]),
                np.array([3, 4]),
                np.array([3, 4]),
            ]
        },
        field_data={
            "omega_pyra": [1, 3],
            "omega_wedge": [2, 3],
            "pyra_skin": [3, 2],
            "wedge_skin": [4, 2],
        },
    )


def test_pyra_wedge_heterogeneous_facets_are_frozen(tmp_path):
    mesh = GmshLoader()(_pyra_wedge_source(tmp_path))
    mesh.validate()

    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets) == (11, 2, 4)
    assert mesh.topo_dim == 3
    assert np.allclose(mesh.nodes, _PYR_WEDGE_POINTS, rtol=_RTOL, atol=_ATOL)

    # mixed same-topo_dim cell types share one dense cell space
    assert mesh.cell_types.tolist() == [CellType.PYR5.code, CellType.WEDGE6.code]
    assert mesh.cells.tolist() == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert mesh.cell_offsets.tolist() == [0, 5, 11]

    # heterogeneous facet table: the triangle block's entities land
    # before the quad block's in declaration stream order
    assert mesh.facet_types.tolist() == [
        CellType.TRI3.code,
        CellType.TRI3.code,
        CellType.QUAD4.code,
        CellType.QUAD4.code,
    ]
    assert mesh.facets.tolist() == [0, 1, 4, 5, 6, 7, 0, 1, 2, 3, 5, 6, 9, 8]
    assert mesh.facet_offsets.tolist() == [0, 3, 6, 10, 14]
    for index, expected in enumerate(
        _PYR_WEDGE_SOURCE_TRIANGLES + _PYR_WEDGE_SOURCE_QUADS
    ):
        assert tuple(mesh.facet_nodes(index).tolist()) == canonical_facet_nodes(
            expected
        )
    assert mesh.facet_cells == ((0,), (1,), (0,), (1,))

    # one boundary group may span facet types: pyra_skin covers a TRI3
    # and a QUAD4 facet of the same source group
    assert set(mesh.domain_groups) == {"omega_pyra", "omega_wedge"}
    assert mesh.domain_groups["omega_pyra"].tolist() == [0]
    assert mesh.domain_groups["omega_wedge"].tolist() == [1]
    carriers = mesh.metadata["boundary_source_groups"]
    assert carriers == {"pyra_skin": (0, 2), "wedge_skin": (1, 3)}
    union = {facet_id for ids in carriers.values() for facet_id in ids}
    assert union == set(range(mesh.n_facets))
