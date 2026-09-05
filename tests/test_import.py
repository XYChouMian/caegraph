"""Smoke tests: verify the package installs and imports correctly."""

import pytest

import caegraph


def test_import_caegraph():
    """`import caegraph` must work after `pip install -e .`."""
    assert caegraph is not None


def test_version_defined():
    """The package must expose a valid version string."""
    version = caegraph.__version__
    assert isinstance(version, str)
    parts = version.split(".")
    assert len(parts) >= 2
    assert all(part.isdigit() for part in parts)


def test_subpackages_exist():
    """All planned subpackages must be importable (ADR-007 layout)."""
    import importlib

    names = (
        "core",
        "geometry",
        "io",
        "graph",
        "transforms",
        "dataset",
        "physics",
        "models",
        "assimilation",
        "workflow",
        "inference",
        "visualization",
        "utils",
    )
    for name in names:
        module = importlib.import_module(f"caegraph.{name}")
        assert module is not None


def test_legacy_data_namespace_remains_importable():
    """The former umbrella namespace warns but remains import-compatible."""
    import importlib
    import sys

    sys.modules.pop("caegraph.data", None)
    with pytest.warns(DeprecationWarning, match="caegraph.data is deprecated"):
        module = importlib.import_module("caegraph.data")
    assert module is not None
