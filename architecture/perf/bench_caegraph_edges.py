"""P2-PERF-01a benchmark: _expand_edges before/after (repo-external, /tmp only).

Usage: python /tmp/bench_caegraph_edges.py <tree-root> [repeats]
The tree root's src/ is force-prepended to sys.path and the resolved
builder module path is printed, so the measured implementation is
always the intended checkout (guards against the editable install
resolving to another worktree). Read-only: no repo files are modified.

Stage split (P2-PERF-01a constraint): candidate generation vs
dedup+sort, measured through in-script replicas of the historical
sequential algorithm and the vectorized algorithm. The replicas use
only public Mesh accessors and are independent of which implementation
is imported.
"""

from __future__ import annotations

import sys
import time
import tracemalloc

TREE_ROOT = sys.argv[1]
REPEATS = int(sys.argv[2]) if len(sys.argv) > 2 else 5

sys.path.insert(0, TREE_ROOT + "/src")

import numpy as np  # noqa: E402

from caegraph.core.topology.celltype import CellType  # noqa: E402
from caegraph.core.topology.mesh import Mesh, canonical_facet_nodes  # noqa: E402
from caegraph.graph.builder import MeshRepresentationBuilder  # noqa: E402
import caegraph.graph.builder as builder_module  # noqa: E402
from caegraph.graph.pyg import to_pyg_data  # noqa: E402


def structured_tet_mesh(nx: int) -> Mesh:
    idx = np.arange(nx * nx * nx, dtype=np.int64).reshape(nx, nx, nx)

    def corner(di, dj, dk):
        sl = tuple(slice(0 + d, nx - 1 + d) for d in (di, dj, dk))
        return idx[sl]

    p000, p100, p110, p010 = corner(0, 0, 0), corner(1, 0, 0), corner(1, 1, 0), corner(0, 1, 0)
    p001, p101, p111, p011 = corner(0, 0, 1), corner(1, 0, 1), corner(1, 1, 1), corner(0, 1, 1)
    tets = (
        (p000, p100, p110, p111),
        (p000, p110, p010, p111),
        (p000, p010, p011, p111),
        (p000, p011, p001, p111),
        (p000, p001, p101, p111),
        (p000, p101, p100, p111),
    )
    cells = np.concatenate([np.stack(t, axis=-1).reshape(-1, 4) for t in tets], axis=0)
    n_cells = cells.shape[0]
    grid = np.indices((nx, nx, nx), dtype=np.float64)
    nodes = grid.reshape(3, -1).T
    return Mesh(
        "bench_tet",
        nodes=nodes,
        topo_dim=3,
        cell_types=np.full(n_cells, CellType.TET4.code, dtype=np.int64),
        cells=cells.ravel(),
        cell_offsets=np.arange(0, 4 * n_cells + 1, 4, dtype=np.int64),
    )


def mesh_from_cells(name, topo_dim, cells_spec):
    cell_types, cells, cell_offsets = [], [], [0]
    facet_index, facet_types, facets, facet_offsets, facet_cells = {}, [], [], [0], []
    for cell_type, local_nodes in cells_spec:
        cell_types.append(cell_type.code)
        cells.extend(local_nodes)
        cell_offsets.append(len(cells))
        for face in cell_type.faces:
            canonical = tuple(canonical_facet_nodes([local_nodes[i] for i in face]))
            fid = facet_index.get(canonical)
            if fid is None:
                fid = len(facet_types)
                facet_index[canonical] = fid
                facet_types.append(
                    CellType.LINE2.code
                    if len(canonical) == 2
                    else (CellType.TRI3.code if len(canonical) == 3 else CellType.QUAD4.code)
                )
                facets.extend(canonical)
                facet_offsets.append(len(facets))
                facet_cells.append([])
            facet_cells[fid].append(len(cell_types) - 1)
    k = int(len(cells) and max(max(s[1]) for s in cells_spec) + 1)
    nodes = [[float(i % 64), float((i * 7) % 64), 0.0] for i in range(k + 1)]
    return Mesh(
        name,
        nodes=nodes,
        topo_dim=topo_dim,
        cell_types=cell_types,
        cells=cells,
        cell_offsets=cell_offsets,
        facet_types=facet_types,
        facets=facets,
        facet_offsets=facet_offsets,
        facet_cells=facet_cells,
    )


def tri_grid(k):
    def v(i, j):
        return i * (k + 1) + j

    specs = []
    for i in range(k):
        for j in range(k):
            a, b, c, d = v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)
            specs.append((CellType.TRI3, [a, b, c]))
            specs.append((CellType.TRI3, [a, c, d]))
    return mesh_from_cells(f"tri{k}x{k}", 2, specs)


def mixed_grid(k):
    def v(i, j):
        return i * (k + 1) + j

    specs = []
    for i in range(k):
        for j in range(k):
            a, b, c, d = v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)
            if (i + j) % 2 == 0:
                specs.append((CellType.TRI3, [a, b, c]))
                specs.append((CellType.TRI3, [a, c, d]))
            else:
                specs.append((CellType.QUAD4, [a, b, c, d]))
    return mesh_from_cells(f"mixed{k}x{k}", 2, specs)


def old_gen_and_set(mesh):
    """Historical sequential algorithm replica: generation + set dedup fused."""
    edges = set()
    for cell_id in range(mesh.n_cells):
        cell_type = mesh.cell_type(cell_id)
        nodes = mesh.cell_nodes(cell_id).tolist()
        if cell_type.dim == 1:
            first, second = nodes
            if first != second:
                edges.add((min(first, second), max(first, second)))
            continue
        for face in cell_type.faces:
            ring = [nodes[local] for local in face]
            for index in range(len(ring)):
                first = ring[index]
                second = ring[(index + 1) % len(ring)]
                if first != second:
                    edges.add((min(first, second), max(first, second)))
    return edges


def new_gen(mesh):
    """Vectorized replica: candidate generation + canonicalization + filter."""
    parts = []
    cell_types = mesh.cell_types
    cells = mesh.cells
    starts_all = mesh.cell_offsets[:-1]
    for code in np.unique(cell_types):
        ct = CellType.from_code(int(code))
        starts = starts_all[cell_types == code]
        if ct.dim == 1:
            conn = cells[starts[:, None] + np.arange(2)[None, :]]
            first, second = conn[:, 0], conn[:, 1]
        else:
            conn = cells[starts[:, None] + np.arange(ct.node_count)[None, :]]
            pairs = [
                np.stack(
                    (conn[:, list(face)], np.roll(conn[:, list(face)], -1, axis=1)),
                    axis=-1,
                ).reshape(-1, 2)
                for face in ct.faces
            ]
            uv = np.concatenate(pairs, axis=0)
            first, second = uv[:, 0], uv[:, 1]
        keep = first != second
        first, second = first[keep], second[keep]
        parts.append(
            np.stack((np.minimum(first, second), np.maximum(first, second)), axis=1)
        )
    return np.concatenate(parts, axis=0)


def best_of(fn, repeats):
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best


def main():
    builder = MeshRepresentationBuilder()
    print(f"tree={TREE_ROOT} repeats={REPEATS}")
    print(f"imported builder: {builder_module.__file__}")
    header = (
        f"{'case':>24} {'n_cells':>8} {'n_cand':>9} {'n_edges':>8} | "
        f"{'gen_old':>8} {'sort_old':>8} {'tot_old':>8} | "
        f"{'gen_new':>8} {'uniq_new':>8} {'expand':>8} | "
        f"{'builder':>8} {'validate':>8} {'to_pyg':>8} {'peak':>7}"
    )
    print(header)
    cases = [
        ("tet 12^3(1728 cells)", structured_tet_mesh(12)),
        ("tet 24^3(13.8k cells)", structured_tet_mesh(24)),
        ("tet 36^3(46.6k cells)", structured_tet_mesh(36)),
        ("tri 120x120(28.8k)", tri_grid(120)),
        ("mixed 120x120(28.8k)", mixed_grid(120)),
    ]
    for name, mesh in cases:
        edges = builder._expand_edges(mesh)
        n_unique = len(edges)
        n_cand = int(new_gen(mesh).shape[0])

        t_gen_old = best_of(lambda: old_gen_and_set(mesh), REPEATS)
        old_set = old_gen_and_set(mesh)
        t_sort_old = best_of(lambda: tuple(sorted(old_set)), REPEATS)
        t_gen_new = best_of(lambda: new_gen(mesh), REPEATS)
        cand = new_gen(mesh)
        n_nodes = mesh.n_nodes
        t_uniq_new = best_of(
            lambda: (
                np.stack(
                    (keys // n_nodes, keys % n_nodes), axis=1
                )
                if len(
                    keys := np.unique(
                        cand[:, 0] * np.int64(n_nodes) + cand[:, 1]
                    )
                )
                else np.empty((0, 2), dtype=np.int64)
            ),
            REPEATS,
        )
        t_expand = best_of(lambda: builder._expand_edges(mesh), REPEATS)
        t_builder = best_of(lambda: builder(mesh), max(3, REPEATS // 2))

        graph = builder(mesh)
        t_validate = best_of(graph.validate, REPEATS)
        t_pyg = best_of(lambda: to_pyg_data(graph), REPEATS)
        tracemalloc.start()
        builder(mesh)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(
            f"{name:>24} {mesh.n_cells:>8} {n_cand:>9} {n_unique:>8} | "
            f"{t_gen_old * 1e3:>7.1f} {t_sort_old * 1e3:>7.1f} "
            f"{(t_gen_old + t_sort_old) * 1e3:>7.1f} | "
            f"{t_gen_new * 1e3:>7.1f} {t_uniq_new * 1e3:>7.1f} "
            f"{t_expand * 1e3:>7.1f} | "
            f"{t_builder * 1e3:>7.1f} {t_validate * 1e3:>7.1f} "
            f"{t_pyg * 1e3:>7.1f} {peak / 1e6:>6.1f}M"
        )


if __name__ == "__main__":
    main()
