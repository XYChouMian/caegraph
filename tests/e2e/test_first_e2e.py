"""Phase 2 First E2E correctness chain (Gate 5 CLOSED follow-up smoke).

Full public path over a synthetic real-format Gmsh source:
GmshLoader → Mesh → MeshRepresentationBuilder → CAEGraph.validate()
→ to_pyg_data → minimal consumer. The source carries cross-block
supported volume cells and a codim-1 physical group; the node field
enters strictly *after* the Mesh load through the builder's public
write path (ADR-020 — Gmsh physical groups are never confused with
CAEGraph FieldData). Assertions anchor the ADR-022 frozen backend key
contract only; the minimal consumer proves consumability with the
simplest public tensor operations.
"""

from __future__ import annotations

from pathlib import Path

import meshio
import numpy as np
import pytest
import torch

from caegraph.core import Field, FieldData
from caegraph.graph import MeshRepresentationBuilder, to_pyg_data
from caegraph.io import GmshLoader


def _small_volume_source(tmp_path: Path):
    """Two tetra blocks (cross-block) + declared skin triangles."""
    points = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
    ]
    cells = [
        ("tetra", np.array([[0, 1, 2, 3]])),
        ("tetra", np.array([[1, 4, 2, 3]])),
        (
            "triangle",
            np.array(
                [
                    [0, 1, 2],
                    [0, 1, 3],
                    [0, 2, 3],
                    [1, 4, 2],
                    [1, 4, 3],
                    [2, 4, 3],
                ]
            ),
        ),
    ]
    cell_data = {
        "gmsh:physical": [
            np.array([1]),
            np.array([1]),
            np.array([5] * 6),
        ]
    }
    field_data = {"solid": [1, 3], "skin": [5, 2]}
    path = tmp_path / "first_e2e.msh"
    mesh = meshio.Mesh(
        np.asarray(points, dtype=np.float64),
        cells,
        cell_data=cell_data,
        field_data=field_data,
    )
    meshio.write(str(path), mesh, file_format="gmsh22", binary=False)
    return path


def test_first_e2e_full_public_chain(tmp_path):
    path = _small_volume_source(tmp_path)

    # --- stage 1: source normalization ----------------------------------
    mesh = GmshLoader()(path)
    mesh.validate()
    assert (mesh.n_nodes, mesh.n_cells, mesh.n_facets) == (5, 2, 6)
    assert mesh.topo_dim == 3
    assert mesh.domain_groups["solid"].tolist() == [0, 1]
    skin_facets = mesh.metadata["boundary_source_groups"]["skin"]
    assert sorted(skin_facets) == list(range(6))

    # --- stage 2: representation construction ----------------------------
    # ADR-020: the node field joins through the builder's public write
    # path after the Mesh load — never synthesized from Gmsh groups.
    pressure = Field("p", association="node")
    graph = MeshRepresentationBuilder()(
        mesh,
        fields=[pressure],
        field_data=[FieldData(pressure, [1.0, 2.0, 3.0, 4.0, 5.0], scope="global")],
    )
    graph.validate()
    assert graph.n_entities == 5
    # 9 unique edges over the two tets (6 + 6 candidates minus shared).
    assert len(graph.edges) == 9

    # --- stage 3: backend materialization --------------------------------
    data = to_pyg_data(graph)
    assert data.num_nodes == 5
    assert set(data.keys()) == {
        "edge_index",
        "num_nodes",
        "pos",
        "node_category",
        "field_families",
        "p",
    }
    assert data.edge_index.dtype == torch.long
    assert data.edge_index.shape == (2, 18)  # 9 undirected pairs
    assert data.pos.dtype == torch.float64
    assert data.pos.shape == (5, 3)
    assert data.node_category.dtype == torch.long
    assert data.field_families == {"p": "node"}

    # --- stage 4: minimal consumer (public tensor operations only) -------
    assert data["p"].shape[0] == data.num_nodes
    assert float(data["p"].mean()) == pytest.approx(3.0)
    directed = {tuple(pair) for pair in data.edge_index.t().tolist()}
    assert all((v, u) in directed for u, v in directed)
    assert torch.isfinite(data.pos).all()
