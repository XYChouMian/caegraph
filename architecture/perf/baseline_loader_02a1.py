"""P2-PERF-02a-1 Phase 0 before-baseline measurement (evidence, NOT production code).

Measures the 02a-1 acceptance boundary — the sole public entry
``GmshLoader()(path)`` call start -> ``Mesh`` return end (the pipeline's
internal ``validate()`` is included) — on the three-tier workload ladder
mandated by ``P2-PERF-02-reassessment.md``:

- 12k  = build_grid_file(10, 10, 20)  (2,541 nodes / 12,000 tets)
- 48k  = build_grid_file(20, 20, 20)  (9,261 nodes / 48,000 tets)
- 257k = build_grid_file(35, 35, 35)  (46,656 nodes / 257,250 tets;
        the file-based form of the historical 257k tier, same scale and
        Kuhn 6-tet topology, routed through GmshLoader per PM ruling)

``build_grid_file`` is copied verbatim from the archived reproduction
artifact ``reassess_loader_profile.py`` (itself the /tmp First E2E /
reassessment generator) so the 48k tier stays byte-comparable with the
archived md5 ``e0fa0c810716aabb0f718248770030bb``.

Protocols (Phase 1 must reuse verbatim):
- runtime: generate the workload file first (untimed), discard one
  warm-up load, then ``--reps`` timed loads, median primary;
- rss: the workload file is fully generated BEFORE any measurement
  subprocess starts; each run is a fresh process that only imports and
  loads (``resource.getrusage(RUSAGE_SELF).ru_maxrss``, Linux KB);
  median is the primary comparison, all values and the max are also
  reported.

If the 48k md5 does not match, generation is NOT adjusted and
measurement does NOT proceed (report and exit non-zero).

Usage:
    python baseline_loader_02a1.py <tree-root> --mode runtime --tier 48k
    python baseline_loader_02a1.py <tree-root> --mode rss --tier 48k
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TIERS: dict[str, tuple[int, int, int]] = {
    "12k": (10, 10, 20),
    "48k": (20, 20, 20),
    "257k": (35, 35, 35),
}
ARCHIVED_48K_MD5 = "e0fa0c810716aabb0f718248770030bb"

_RSS_CHILD_CODE = (
    "import resource, sys\n"
    "from caegraph.io import GmshLoader\n"
    "mesh = GmshLoader()(sys.argv[1])\n"
    "print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)\n"
)


def build_grid_file(path: str, nx: int, ny: int, nz: int) -> None:
    """Generate the synthetic 2.2-ASCII structured tet grid fixture.

    Verbatim copy of the archived generator (reassess_loader_profile.py):
    same node/tet ordering, same skin-on-x=0-face triangles, same
    physical-group layout — do not modify without a PM dispatch.
    """
    import meshio
    import numpy as np

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


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree_root", help="target code tree root (its src/ is prepended)")
    parser.add_argument("--mode", choices=("runtime", "rss"), required=True)
    parser.add_argument("--tier", choices=sorted(TIERS), required=True)
    parser.add_argument("--reps", type=int, default=6, help="timed loads (runtime mode)")
    parser.add_argument("--rss-runs", type=int, default=3, help="fresh processes (rss mode)")
    parser.add_argument(
        "--workdir", default=None, help="workload directory (default: fresh tempdir)"
    )
    args = parser.parse_args()

    root = Path(args.tree_root).resolve()
    sys.path.insert(0, str(root / "src"))
    import caegraph.io  # noqa: F401  (provenance import after path setup)
    from caegraph.io import GmshLoader

    print(f"[provenance] caegraph.io -> {Path(caegraph.io.__file__).resolve()}")
    print(
        f"[env] python {platform.python_version()} | "
        f"numpy {__import__('numpy').__version__} | "
        f"meshio {__import__('meshio').__version__} | {platform.system()} "
        f"{platform.release()}"
    )

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="perf02a1_"))
    workdir.mkdir(parents=True, exist_ok=True)
    nx, ny, nz = TIERS[args.tier]
    path = workdir / f"grid_{args.tier}.msh"
    if not path.exists():
        print(f"[gen] {args.tier} = build_grid_file({nx}, {ny}, {nz}) -> {path}")
        build_grid_file(str(path), nx, ny, nz)
    digest = _md5(path)
    print(f"[gen] size={path.stat().st_size} bytes  md5={digest}")
    if args.tier == "48k" and digest != ARCHIVED_48K_MD5:
        print(
            "[STOP] 48k md5 mismatch against the archived historical "
            f"generation ({ARCHIVED_48K_MD5}); measurement halted — "
            "investigate generation/byte-format differences before any retry"
        )
        return 1

    if args.mode == "runtime":
        GmshLoader()(str(path))  # warm-up: lazy imports and caches, discarded
        times = []
        for _ in range(args.reps):
            start = time.perf_counter()
            mesh = GmshLoader()(str(path))
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            print(f"[runtime] rep {len(times)}: {elapsed:.6f} s  (n_cells={mesh.n_cells})")
        print(
            f"[runtime] {args.tier}: reps={args.reps} "
            f"median={statistics.median(times):.6f} s  "
            f"min={min(times):.6f} s  max={max(times):.6f} s"
        )
    else:
        # Workload generation is complete before any subprocess starts;
        # each child only imports and loads, then reports its own peak.
        peaks = []
        for run in range(1, args.rss_runs + 1):
            child = subprocess.run(
                [sys.executable, "-c", _RSS_CHILD_CODE, str(path)],
                capture_output=True,
                text=True,
                check=True,
                env={"PYTHONPATH": str(root / "src")},
            )
            peaks.append(int(child.stdout.strip().splitlines()[-1]))
            print(f"[rss] run {run}: peak_rss={peaks[-1]} KB")
        print(
            f"[rss] {args.tier}: runs={args.rss_runs} "
            f"median={statistics.median(peaks)} KB  max={max(peaks)} KB"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
