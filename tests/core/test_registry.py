"""Tests for caegraph.core.registry.Registry."""

from __future__ import annotations

import pytest

from caegraph.core import Registry


def _make_loader(default: str = "ok") -> str:
    return default


def test_direct_registration_and_get():
    registry: Registry[str] = Registry("loader")
    registry.register("gmsh", _make_loader)
    assert registry.get("gmsh") is _make_loader


def test_decorator_form_registers_and_returns_target():
    registry: Registry[str] = Registry("loader")

    @registry.register("ansys")
    def loader() -> str:
        return "ansys"

    assert "ansys" in registry
    assert loader() == "ansys"


def test_duplicate_registration_is_rejected():
    registry: Registry[str] = Registry("loader")
    registry.register("gmsh", _make_loader)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("gmsh", _make_loader)


def test_blank_registration_name_is_rejected():
    registry: Registry[str] = Registry("loader")
    with pytest.raises(ValueError, match="non-empty"):
        registry.register("  ", _make_loader)


def test_non_callable_factory_is_rejected():
    registry: Registry[str] = Registry("loader")
    with pytest.raises(TypeError, match="callable"):
        registry.register("bad", "not-callable")  # type: ignore[arg-type]


def test_unknown_get_lists_available_names():
    registry: Registry[str] = Registry("mesh loader")
    registry.register("gmsh", _make_loader)
    with pytest.raises(KeyError, match="gmsh"):
        registry.get("fluent")


def test_unknown_get_on_empty_registry_mentions_none():
    registry: Registry[str] = Registry("mesh loader")
    with pytest.raises(KeyError, match="<none>"):
        registry.get("gmsh")


def test_build_forwards_arguments():
    registry: Registry[str] = Registry("factory")
    registry.register("echo", lambda prefix, suffix="": f"{prefix}{suffix}")
    assert registry.build("echo", "a", suffix="b") == "ab"


def test_unregister_removes_entry():
    registry: Registry[str] = Registry("loader")
    registry.register("gmsh", _make_loader)
    registry.unregister("gmsh")
    assert "gmsh" not in registry
    assert len(registry) == 0


def test_unregister_unknown_name_is_rejected():
    registry: Registry[str] = Registry("loader")
    with pytest.raises(KeyError, match="unknown"):
        registry.unregister("gmsh")


def test_names_are_sorted():
    registry: Registry[str] = Registry("loader")
    for name in ("fluent", "abaqus", "gmsh"):
        registry.register(name, _make_loader)
    assert registry.names() == ["abaqus", "fluent", "gmsh"]


def test_blank_kind_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        Registry(" ")
