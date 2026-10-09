"""Gate 5 source IO contract guards for the Gmsh loader (ADR-012/013/014).

Synthetic but real-format ``.msh`` fixtures are generated at test
runtime through meshio (gmsh 2.2 ASCII for determinism, ADR-013 risk
note) — no external CAE data, no network. Assertions target the
ADR-012 normalization obligations and the ADR-014 canonical contract,
not implementation details.
"""

from __future__ import annotations

import os
import subprocess
import sys
import typing
from pathlib import Path

import meshio
import numpy as np
import pytest

from caegraph.core import BoundaryManager, BoundaryRegion, CellType
from caegraph.graph import MeshRepresentationBuilder
from caegraph.io import AbstractMeshLoader, GmshLoader

_SRC_ROOT = str(Path(__file__).resolve().parents[2] / "src")


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


def _load(path):
    return GmshLoader()(path)


def _two_triangle_source(tmp_path: Path, *, reverse_lines: bool = False):
    """Two TRI3 sharing edge (1,2); five LINE2 with three boundary groups.

    line block: shared (1,2) tag 30, boundary (0,1)/(0,2) tag 40,
    (1,3)/(2,3) tag 50. ``reverse_lines`` flips every line's winding.
    """
    lines = (
        [[2, 1], [1, 0], [2, 0], [3, 1], [3, 2]]
        if reverse_lines
        else [[1, 2], [0, 1], [0, 2], [1, 3], [2, 3]]
    )
    return _write_msh(
        tmp_path,
        "two_tri.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
        cells=[
            ("triangle", np.array([[0, 1, 2], [1, 3, 2]])),
            ("line", np.array(lines)),
        ],
        cell_data={
            "gmsh:physical": [
                np.array([10, 20]),
                np.array([30, 30, 40, 40, 50]),
            ]
        },
        field_data={
            "omega_a": [10, 2],
            "omega_b": [20, 2],
            "wall": [30, 1],
            "inlet": [40, 1],
            "outlet": [50, 1],
        },
    )


# 1 — single supported cell type -------------------------------------------------


def test_single_supported_cell_type_loads_and_validates(tmp_path):
    path = _write_msh(
        tmp_path,
        "single.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        cells=[("triangle", np.array([[0, 1, 2]]))],
    )
    mesh = _load(path)
    mesh.validate()
    assert mesh.topo_dim == 2
    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets) == (3, 1, 0)
    assert mesh.domain_groups == {}
    assert mesh.metadata["source_format"] == "gmsh"
    assert "boundary_source_groups" not in mesh.metadata


# 2 — same topo_dim mixed cell types ---------------------------------------------


def test_same_topo_dim_mixed_cell_types_stay_one_cell_space(tmp_path):
    path = _write_msh(
        tmp_path,
        "mixed2d.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [2, 0.5, 0]],
        cells=[
            ("quad", np.array([[0, 1, 3, 2]])),
            ("triangle", np.array([[1, 4, 3]])),
        ],
    )
    mesh = _load(path)
    mesh.validate()
    assert mesh.n_cells == 2
    assert mesh.cell_types.tolist() == [CellType.QUAD4.code, CellType.TRI3.code]
    assert mesh.cell_nodes(0).tolist() == [0, 1, 3, 2]
    assert mesh.cell_nodes(1).tolist() == [1, 4, 3]
    assert mesh.topo_dim == 2


# 3 — legal cross-dimension source blocks ----------------------------------------


def test_cross_dimension_source_blocks_are_normalized(tmp_path):
    # 2D: LINE2 surface + TRI3 cells; the lines are facet candidates.
    flat = _two_triangle_source(tmp_path)
    mesh = _load(flat)
    mesh.validate()
    assert [CellType.from_code(int(code)) for code in mesh.cell_types] == [
        CellType.TRI3,
        CellType.TRI3,
    ]
    assert all(
        CellType.from_code(int(code)) == CellType.LINE2 for code in mesh.facet_types
    )

    # 3D: TET4 volume + TRI3 surface; the triangles are facet candidates.
    volume = _write_msh(
        tmp_path,
        "vol.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
        cells=[
            ("tetra", np.array([[0, 1, 2, 3]])),
            ("triangle", np.array([[0, 1, 2], [0, 1, 3]])),
        ],
        cell_data={"gmsh:physical": [np.array([1]), np.array([5, 5])]},
        field_data={"vol": [1, 3], "skin": [5, 2]},
    )
    mesh3d = _load(volume)
    mesh3d.validate()
    assert mesh3d.topo_dim == 3
    assert mesh3d.n_cells == 1
    assert mesh3d.n_facets == 2
    assert mesh3d.domain_groups["vol"].tolist() == [0]


# 4 — block-local entities receive canonical global IDs ---------------------------


def test_entities_are_renumbered_canonically_across_blocks(tmp_path):
    path = _write_msh(
        tmp_path,
        "split_blocks.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
        cells=[
            ("triangle", np.array([[0, 1, 2]])),
            ("triangle", np.array([[1, 3, 2]])),
        ],
        cell_data={"gmsh:physical": [np.array([10]), np.array([10])]},
        field_data={"both": [10, 2]},
    )
    mesh = _load(path)
    mesh.validate()
    # One cell per source block; canonical cell IDs are the dense
    # canonical enumeration across blocks (0, 1) — never block-local.
    assert mesh.n_cells == 2
    assert mesh.cell_nodes(0).tolist() == [0, 1, 2]
    assert mesh.cell_nodes(1).tolist() == [1, 3, 2]
    assert mesh.domain_groups["both"].tolist() == [0, 1]


# 5 — physical domain group -> global cell IDs ------------------------------------


def test_physical_domain_groups_map_to_global_cell_ids(tmp_path):
    path = _two_triangle_source(tmp_path)
    mesh = _load(path)
    mesh.validate()
    assert mesh.domain_groups["omega_a"].tolist() == [0]
    assert mesh.domain_groups["omega_b"].tolist() == [1]


# 6 — physical boundary group -> global facet IDs ---------------------------------


def test_physical_boundary_groups_map_to_global_facet_ids(tmp_path):
    path = _two_triangle_source(tmp_path)
    mesh = _load(path)
    mesh.validate()
    # All five declared lines enter the facet table (ADR-014 decision 2:
    # adapter-declared facets); groups carry their global facet IDs in
    # metadata for downstream region construction.
    assert mesh.n_facets == 5
    carriers = mesh.metadata["boundary_source_groups"]
    assert carriers["wall"] == (0, 1)
    assert carriers["inlet"] == (2, 3)
    assert carriers["outlet"] == (4,)
    assert sorted(carriers["wall"] + carriers["inlet"] + carriers["outlet"]) == [
        *range(5)
    ]


# 7 — lower-dimensional group -> diagnostics, excluded ----------------------------


def test_lower_dimension_group_is_diagnosed_and_excluded(tmp_path):
    path = _write_msh(
        tmp_path,
        "curve_markers.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
        cells=[
            ("tetra", np.array([[0, 1, 2, 3]])),
            ("line", np.array([[0, 1]])),
        ],
        cell_data={"gmsh:physical": [np.array([1]), np.array([9])]},
        field_data={"vol": [1, 3], "markers": [9, 1]},
    )
    with pytest.warns(UserWarning, match="markers"):
        mesh = _load(path)
    mesh.validate()
    # dim 1 < topo_dim - 1 = 2: excluded from the canonical topology.
    assert mesh.n_cells == 1
    assert mesh.n_facets == 0
    assert "markers" not in mesh.metadata.get("boundary_source_groups", {})


# 8 — meshio.field_data tag/name mapping is respected ------------------------------


def test_field_data_tag_mapping_resolves_members_by_tag(tmp_path):
    path = _write_msh(
        tmp_path,
        "tags.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
        cells=[
            ("triangle", np.array([[0, 1, 2], [1, 3, 2]])),
            ("line", np.array([[0, 1]])),
        ],
        cell_data={"gmsh:physical": [np.array([42, 17]), np.array([7])]},
        field_data={
            "zeta": [42, 2],
            "alpha": [7, 1],
            "beta": [17, 2],
        },
    )
    mesh = _load(path)
    mesh.validate()
    assert mesh.domain_groups["zeta"].tolist() == [0]
    assert mesh.domain_groups["beta"].tolist() == [1]
    assert mesh.metadata["boundary_source_groups"]["alpha"] == (0,)


# 9 — facet winding does not change canonical identity -----------------------------


def test_facet_source_winding_does_not_change_canonical_identity(tmp_path):
    straight_dir = tmp_path / "a"
    flipped_dir = tmp_path / "b"
    straight_dir.mkdir()
    flipped_dir.mkdir()
    straight = _load(_two_triangle_source(straight_dir))
    flipped = _load(_two_triangle_source(flipped_dir, reverse_lines=True))
    np.testing.assert_array_equal(straight.facets, flipped.facets)
    assert (
        straight.metadata["boundary_source_groups"]
        == flipped.metadata["boundary_source_groups"]
    )
    assert straight.facet_cells == flipped.facet_cells


# 10 — facet_cells consistency ------------------------------------------------------


def test_facet_cells_is_the_validated_cell_adjacency(tmp_path):
    path = _two_triangle_source(tmp_path)
    mesh = _load(path)
    mesh.validate()
    # facet 0 is the shared interior edge (1,2) of cells 0 and 1.
    assert mesh.facet_adjacent_cells(0) == (0, 1)
    assert mesh.facet_nodes(0).tolist() == [1, 2]
    # boundary edges carry exactly their own cell.
    assert mesh.facet_adjacent_cells(1) == (0,)
    assert mesh.facet_adjacent_cells(4) == (1,)
    for index in range(mesh.n_facets):
        assert len(mesh.facet_adjacent_cells(index)) >= 1


# 11 — supported CellType mapping ----------------------------------------------------


@pytest.mark.parametrize(
    ("meshio_type", "expected"),
    [
        ("line", CellType.LINE2),
        ("triangle", CellType.TRI3),
        ("quad", CellType.QUAD4),
        ("tetra", CellType.TET4),
        ("pyramid", CellType.PYR5),
        ("wedge", CellType.WEDGE6),
        ("hexahedron", CellType.HEX8),
    ],
)
def test_every_supported_source_type_maps_to_canonical_vocabulary(
    tmp_path, meshio_type, expected
):
    width = expected.node_count
    points = [[float(index), 0.0, 0.0] for index in range(width)]
    path = _write_msh(
        tmp_path,
        f"{meshio_type}.msh",
        points=points,
        cells=[(meshio_type, np.array([list(range(width))]))],
    )
    mesh = _load(path)
    mesh.validate()
    assert mesh.cell_type(0) == expected


# 12 — complete_coverage / partition are not declared by the loader -----------------


def test_loader_never_declares_coverage_or_partition(tmp_path):
    # Ungrouped cells and partially declared boundaries are legal: the
    # loader assumes no coverage/partition (ADR-012) and declares no
    # such semantics (ADR-014 8b keeps them caller-declared, no API).
    path = _write_msh(
        tmp_path,
        "partial.msh",
        points=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
        cells=[
            ("triangle", np.array([[0, 1, 2], [1, 3, 2]])),
            ("line", np.array([[0, 1]])),
        ],
        cell_data={"gmsh:physical": [np.array([10, 5]), np.array([30])]},
        field_data={"omega": [10, 2], "edge": [30, 1]},
    )
    mesh = _load(path)
    mesh.validate()
    # cell 1 carries no physical tag and stays ungrouped — legal.
    assert mesh.domain_groups["omega"].tolist() == [0]
    assert mesh.n_cells == 2
    keys = set(mesh.metadata)
    assert not any("coverage" in key or "partition" in key for key in keys)


# 13 — rejection behavior ------------------------------------------------------------


def test_unreadable_source_is_rejected_with_value_error(tmp_path):
    with pytest.raises(ValueError, match="io engine"):
        _load(tmp_path / "does_not_exist.msh")


def test_unsupported_element_type_is_rejected(tmp_path):
    # Handwritten real-format 2.2 source carrying element type 11
    # (2nd-order tetra, 10 nodes) — outside the canonical vocabulary.
    nodes = "\n".join(f"{index} 0.1 0.2 0.3" for index in range(1, 11))
    node_tags = " ".join(str(index) for index in range(1, 11))
    path = tmp_path / "high_order.msh"
    path.write_text(
        "$MeshFormat\n2.2 0 8\n$EndMeshFormat\n"
        f"$Nodes\n10\n{nodes}\n$EndNodes\n"
        f"$Elements\n1\n1 11 0 {node_tags}\n$EndElements\n",
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="unsupported source element type"):
        _load(path)


def test_source_without_supported_cells_is_rejected(tmp_path):
    path = tmp_path / "nodes_only.msh"
    path.write_text(
        "$MeshFormat\n2.2 0 8\n$EndMeshFormat\n"
        "$Nodes\n4\n"
        "1 0 0 0\n2 1 0 0\n3 0 1 0\n4 0 0 1\n"
        "$EndNodes\n"
        "$Elements\n0\n$EndElements\n",
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="no supported cell entities"):
        _load(path)


# 14 — meshio stays out of the public contract (types + lazy import) -----------------


def test_public_signatures_never_mention_meshio_types():
    for func in (AbstractMeshLoader.__call__, GmshLoader.__call__):
        for hint in typing.get_type_hints(func).values():
            module = getattr(hint, "__module__", "") or ""
            assert not module.startswith("meshio")


def test_import_caegraph_io_does_not_import_meshio():
    # Fresh process: registration/module import stays engine-free
    # (ADR-013 decision 4 lazy import) — never assert this against the
    # running pytest process, where other fixtures may have imported it.
    code = (
        "import sys; import caegraph.io; "
        "sys.exit(1 if 'meshio' in sys.modules else 0)"
    )
    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        env={**os.environ, "PYTHONPATH": _SRC_ROOT},
    )


# 15 — canonical IDs carry no Gmsh/meshio numbering ----------------------------------


def test_canonical_ids_are_dense_and_free_of_source_numbering(tmp_path):
    path = _two_triangle_source(tmp_path)
    mesh = _load(path)
    # canonical node IDs are the dense 0-based point space; cell and
    # facet IDs are the dense canonical enumerations — no Gmsh tag or
    # block-local index survives anywhere.
    assert set(mesh.cells.tolist()) == set(range(mesh.n_nodes))
    assert set(mesh.facets.tolist()) == set(range(mesh.n_nodes))
    assert np.array_equal(mesh.cell_offsets, np.arange(mesh.n_cells + 1) * 3)
    cell_ids = {int(value) for ids in mesh.domain_groups.values() for value in ids}
    assert cell_ids <= set(range(mesh.n_cells))
    facet_ids = {
        int(value)
        for ids in mesh.metadata["boundary_source_groups"].values()
        for value in ids
    }
    assert facet_ids == set(range(mesh.n_facets))
    for ids in mesh.domain_groups.values():
        assert ids.dtype == np.dtype(np.int64)


# compatibility smoke: the existing consumer accepts loader output ---------------------------------


def test_loaded_mesh_feeds_the_existing_representation_builder(tmp_path):
    path = _two_triangle_source(tmp_path)
    mesh = _load(path)
    manager = BoundaryManager()
    for name, facet_ids in sorted(mesh.metadata["boundary_source_groups"].items()):
        manager.register(BoundaryRegion(name, facet_ids))
    graph = MeshRepresentationBuilder()(mesh, manager)
    graph.validate()
    assert graph.n_entities == mesh.n_nodes
    assert {region.name for region in graph.boundaries.regions} == {
        "inlet",
        "outlet",
        "wall",
    }
