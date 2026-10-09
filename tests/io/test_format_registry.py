"""Format registry guards: core Registry reuse, name -> factory (ADR-013)."""

from __future__ import annotations

import pytest

from caegraph.io import FORMAT_REGISTRY, GmshLoader


def test_gmsh_is_registered_in_the_format_registry():
    assert "gmsh" in FORMAT_REGISTRY
    assert isinstance(FORMAT_REGISTRY.build("gmsh"), GmshLoader)


def test_unknown_format_names_are_rejected():
    with pytest.raises(KeyError):
        FORMAT_REGISTRY.build("fluent")


def test_duplicate_registration_is_rejected():
    with pytest.raises(ValueError, match="registered"):
        FORMAT_REGISTRY.register("gmsh", GmshLoader)


def test_registry_is_the_core_mechanism():
    assert FORMAT_REGISTRY.kind == "mesh loader"
