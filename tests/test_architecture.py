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
LEGACY_NAMESPACES = {"data"}


def _python_files() -> Iterator[Path]:
    """Yield tracked-source candidates without relying on Git metadata."""
    yield from PACKAGE_ROOT.rglob("*.py")


def _source_package(path: Path) -> str | None:
    """Return the first CAEGraph package component for a source file."""
    relative = path.relative_to(PACKAGE_ROOT)
    return relative.parts[0] if len(relative.parts) > 1 else None


def _internal_imports(path: Path) -> Iterator[str]:
    """Yield top-level CAEGraph packages imported by *path*."""
    relative = path.relative_to(PACKAGE_ROOT).with_suffix("")
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
            elif len(module_parts) > 1 and module_parts[0] == "caegraph":
                yield module_parts[1]


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


def test_internal_imports_follow_dependency_layers():
    """Packages may depend only on lower layers or themselves."""
    violations = []
    for path in _python_files():
        source = _source_package(path)
        if source not in LAYERS:
            continue
        for target in _internal_imports(path):
            if target not in LAYERS or target == source:
                continue
            if LAYERS[target] >= LAYERS[source]:
                violations.append(f"{path.relative_to(PACKAGE_ROOT)} -> {target}")

    assert not violations, "invalid CAEGraph dependencies: " + ", ".join(violations)


def test_engineering_truth_layers_do_not_import_pyg():
    """Core, geometry, and IO must remain independent of PyG."""
    violations = []
    for path in _python_files():
        if _source_package(path) in PYG_FREE_PACKAGES and _imports_torch_geometric(
            path
        ):
            violations.append(str(path.relative_to(PACKAGE_ROOT)))

    assert not violations, "PyG imports below graph layer: " + ", ".join(violations)


def test_legacy_namespaces_do_not_hide_internal_dependencies():
    """Compatibility namespaces remain empty dependency leaves."""
    violations = []
    for path in _python_files():
        if _source_package(path) not in LEGACY_NAMESPACES:
            continue
        for target in _internal_imports(path):
            if target in LAYERS:
                violations.append(f"{path.relative_to(PACKAGE_ROOT)} -> {target}")

    assert not violations, "legacy namespace dependencies: " + ", ".join(violations)
