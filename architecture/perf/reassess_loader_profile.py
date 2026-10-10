"""P2-PERF-02 Reassessment reproduction artifact (evidence, NOT production code).

Origin: the /tmp profiling script used by the P2-PERF-02 reassessment
run (2026-10-10, WSL2, conda env ``caegraph-dev``: Python 3.10.21,
meshio 5.3.5, torch 2.14.0+cu130) on the First E2E 48k workload
(20x20x20 Kuhn 6-tet grid, 9261 nodes / 48000 tets / 800 boundary
triangles). Archived so the attribution numbers in
``P2-PERF-02-reassessment.md`` are reproducible.

Evidence only — this script is not part of the package, is not
imported anywhere, and must never be treated as a contract or a
production utility.

The loader is exercised exclusively through its public entry point
``GmshLoader()(path)``; the protected hooks (``_load_source`` /
``_normalize_source`` / ``_build_topology``) are only *observed* by
the profiler's call tree and are never called directly by this
script.

Usage:
    python reassess_loader_profile.py
"""

from __future__ import annotations

import cProfile
import io
import os
import pstats
import tempfile

import numpy as np
import meshio

from caegraph.io import GmshLoader


def build_grid_file(path: str, nx: int, ny: int, nz: int) -> None:
    """Generate the synthetic 2.2-ASCII structured tet grid fixture."""
    n = (nx + 1) * (ny + 1) * (nz + 1)
    g = np.arange(n, dtype=np.int64)
    i = g % (nx + 1)
    j = (g // (nx + 1)) % (ny + 1)
    k = g // ((nx + 1) * (ny + 1))
    pts = np.stack(
        [i.astype(np.float64), j.astype(np.float64), k.astype(np.float64)],
        axis=1,
    )
    tets = []
    for kk in range(nz):
        for jj in range(ny):
            for ii in range(nx):
                v = lambda di, dj, dk: (ii + di) + (jj + dj) * (nx + 1) + (kk + dk) * (nx + 1) * (ny + 1)  # noqa: E731
                c = [
                    v(0, 0, 0), v(1, 0, 0), v(0, 1, 0), v(1, 1, 0),
                    v(0, 0, 1), v(1, 0, 1), v(0, 1, 1), v(1, 1, 1),
                ]
                tets += [
                    [c[0], c[1], c[3], c[7]],
                    [c[0], c[1], c[5], c[7]],
                    [c[0], c[5], c[4], c[7]],
                    [c[0], c[3], c[2], c[7]],
                    [c[0], c[2], c[6], c[7]],
                    [c[0], c[6], c[4], c[7]],
                ]
    tris = []
    for kk in range(nz):
        for jj in range(ny):
            v = lambda dj, dk: (jj + dj) * (nx + 1) + (kk + dk) * (nx + 1) * (ny + 1)  # noqa: E731
            a, b, cc, dd = v(0, 0), v(1, 0), v(1, 1), v(0, 1)
            tris += [[a, b, cc], [a, cc, dd]]
    m = meshio.Mesh(
        pts,
        [("tetra", np.array(tets)), ("triangle", np.array(tris))],
        cell_data={
            "gmsh:physical": [np.array([1] * len(tets)), np.array([5] * len(tris))]
        },
        field_data={"solid": [1, 3], "skin": [5, 2]},
    )
    meshio.write(path, m, file_format="gmsh22", binary=False)


def main() -> None:
    d = tempfile.mkdtemp()
    path = os.path.join(d, "grid48k.msh")
    build_grid_file(path, 20, 20, 20)

    loader = GmshLoader()
    loader(path)  # warm-up: lazy imports and caches

    prof = cProfile.Profile()
    prof.enable()
    mesh = loader(path)  # public entry only
    prof.disable()
    prof.dump_stats("/tmp/perf02_loader.prof")
    assert mesh.n_cells == 48000

    s = io.StringIO()
    pstats.Stats(prof, stream=s).sort_stats("tottime").print_stats(28)
    print(s.getvalue())

    # Hierarchical attribution by tottime (self time) — self time never
    # counts sub-calls, so the buckets sum to exactly 100% of profiled
    # CPU; inclusive cumtime is reported separately and never summed.
    stats = pstats.Stats(prof)
    buckets = {
        "meshio parse (external engine)": 0.0,
        "caegraph io normalization (gmsh.py)": 0.0,
        "canonical construction (io/base.py + mesh init/canonical)": 0.0,
        "Mesh.validate": 0.0,
        "numpy/ndarray ops": 0.0,
        "python runtime / builtins / other": 0.0,
    }
    total = 0.0
    for (filename, _lineno, funcname), entry in stats.stats.items():
        _cc, _nc, tt, _ct, _callers = entry
        total += tt
        fn = filename.replace("\\", "/")
        if "meshio" in fn:
            bucket = "meshio parse (external engine)"
        elif "/io/gmsh.py" in fn:
            bucket = "caegraph io normalization (gmsh.py)"
        elif "/io/base.py" in fn or (
            "topology/mesh.py" in fn
            and funcname not in ("validate", "_validate_state", "_validate_metadata")
        ):
            bucket = "canonical construction (io/base.py + mesh init/canonical)"
        elif "topology/mesh.py" in fn and funcname in (
            "validate",
            "_validate_state",
            "_validate_metadata",
        ):
            bucket = "Mesh.validate"
        elif fn.startswith("<") or "numpy" in fn:
            bucket = "numpy/ndarray ops"
        else:
            bucket = "python runtime / builtins / other"
        buckets[bucket] += tt

    print("=== hierarchical attribution (tottime self-time; buckets sum to 100%) ===")
    for name, seconds in sorted(buckets.items(), key=lambda kv: -kv[1]):
        print(f"{name:58s} {seconds:8.3f}s  {100 * seconds / total:5.1f}%")
    print(f"{'TOTAL profiled':58s} {total:8.3f}s  100.0%")

    print("=== top cumtime (inclusive; for call-tree reading, never summed) ===")
    s2 = io.StringIO()
    pstats.Stats(prof, stream=s2).sort_stats("cumulative").print_stats(16)
    print(s2.getvalue())


if __name__ == "__main__":
    main()
