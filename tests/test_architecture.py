"""Static tests for CAEGraph package dependency boundaries."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "caegraph"

LAYERS = {
    "utils": 0,
    "core": 1,
    "geometry": 2,
    "io": 2,
    "graph": 3,
    "transforms": 4,
    "dataset": 5,
    "physics": 6,
    "models": 7,
    "assimilation": 7,
    "workflow": 8,
    "inference": 8,
    "visualization": 9,
}

PYG_FREE_PACKAGES = {"core", "geometry", "io"}


def _python_files(package_root: Path) -> Iterator[Path]:
    """Yield tracked-source candidates without relying on Git metadata."""
    yield from package_root.rglob("*.py")


def _source_package(path: Path, package_root: Path) -> str | None:
    """Return the first CAEGraph package component for a source file.

    Modules sitting directly under the package root (``caegraph/__init__.py``
    and any future package-level module) are the package facade rather than a
    layer member, so they return ``None`` and stay outside the layer rule.
    """
    relative = path.relative_to(package_root)
    return relative.parts[0] if len(relative.parts) > 1 else None


def _internal_imports(path: Path, package_root: Path) -> Iterator[str]:
    """Yield top-level CAEGraph packages imported by *path*."""
    relative = path.relative_to(package_root).with_suffix("")
    package_parts = relative.parts[:-1]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if len(parts) > 1 and parts[0] == "caegraph":
                    yield parts[1]
        elif isinstance(node, ast.ImportFrom):
            module_parts = tuple((node.module or "").split(".")) if node.module else ()
            if node.level:
                keep = max(0, len(package_parts) - (node.level - 1))
                resolved = package_parts[:keep] + module_parts
                if resolved:
                    yield resolved[0]
            elif module_parts and module_parts[0] == "caegraph":
                if len(module_parts) > 1:
                    yield module_parts[1]
                else:
                    # ``from caegraph import graph`` binds a top-level package
                    # without spelling it as a module path; the layer rule
                    # (ADR-007 D7) must still see the target.
                    for alias in node.names:
                        yield alias.name.split(".")[0]


def _imports_torch_geometric(path: Path) -> bool:
    """Return whether *path* imports torch_geometric directly."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name.split(".")[0] == "torch_geometric" for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == "torch_geometric":
                return True
    return False


def _layer_violations(package_root: Path) -> list[str]:
    """Return the dependency-layer violations found under *package_root*.

    A violation is an import of a package whose layer index is greater than or
    equal to the importing package's own index, so both upward dependencies
    and same-layer sibling dependencies are rejected (ADR-007 D7).
    """
    violations = []
    for path in _python_files(package_root):
        source = _source_package(path, package_root)
        if source not in LAYERS:
            continue
        for target in _internal_imports(path, package_root):
            if target not in LAYERS or target == source:
                continue
            if LAYERS[target] >= LAYERS[source]:
                violations.append(f"{path.relative_to(package_root)} -> {target}")

    return sorted(violations)


def _write_probe(package_root: Path, relative: str, source: str) -> None:
    """Write a synthetic module under *package_root* for guard testing."""
    target = package_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def test_internal_imports_follow_dependency_layers():
    """Packages may depend only on lower layers or themselves."""
    violations = _layer_violations(PACKAGE_ROOT)

    assert not violations, "invalid CAEGraph dependencies: " + ", ".join(violations)


def test_engineering_truth_layers_do_not_import_pyg():
    """Core, geometry, and IO must remain independent of PyG."""
    violations = []
    for path in _python_files(PACKAGE_ROOT):
        source = _source_package(path, PACKAGE_ROOT)
        if source in PYG_FREE_PACKAGES and _imports_torch_geometric(path):
            violations.append(str(path.relative_to(PACKAGE_ROOT)))

    assert not violations, "PyG imports below graph layer: " + ", ".join(violations)


def test_layer_guard_sees_package_root_binding(tmp_path: Path):
    """``from caegraph import <package>`` must reach the layer rule."""
    _write_probe(tmp_path, "core/probe.py", "from caegraph import graph\n")

    assert _layer_violations(tmp_path) == ["core/probe.py -> graph"]


def test_layer_guard_sees_module_path_imports(tmp_path: Path):
    """``import caegraph.x`` and ``from caegraph.x import y`` are both seen."""
    _write_probe(tmp_path, "core/probe.py", "import caegraph.graph\n")
    _write_probe(tmp_path, "graph/probe.py", "from caegraph.dataset import sample\n")

    assert _layer_violations(tmp_path) == [
        "core/probe.py -> graph",
        "graph/probe.py -> dataset",
    ]


def test_layer_guard_rejects_sibling_dependencies(tmp_path: Path):
    """Same-layer sibling packages must not import each other."""
    _write_probe(tmp_path, "geometry/probe.py", "from caegraph import io\n")

    assert _layer_violations(tmp_path) == ["geometry/probe.py -> io"]


def test_layer_guard_accepts_downward_dependencies(tmp_path: Path):
    """A strictly lower layer stays legal, including via a root binding."""
    _write_probe(tmp_path, "graph/probe.py", "from caegraph import core\n")
    _write_probe(tmp_path, "models/probe.py", "from caegraph import physics\n")

    assert _layer_violations(tmp_path) == []
