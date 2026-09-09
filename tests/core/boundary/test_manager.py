"""Tests for caegraph.core.boundary.manager.BoundaryManager."""

from __future__ import annotations

import pytest

from caegraph.core import BoundaryManager, BoundaryRegion, BoundarySpec, BoundaryType


def _two_region_manager() -> BoundaryManager:
    manager = BoundaryManager()
    manager.register(BoundaryRegion("fluid_inlet", [1, 5]))
    manager.register(BoundaryRegion("fluid_wall", [4, 5]))
    return manager


def test_register_returns_the_region():
    manager = BoundaryManager()
    region = BoundaryRegion("fluid_wall", [1])
    assert manager.register(region) is region


def test_duplicate_region_names_are_rejected():
    manager = BoundaryManager()
    manager.register(BoundaryRegion("fluid_wall", [1]))
    with pytest.raises(ValueError, match="already registered"):
        manager.register(BoundaryRegion("fluid_wall", [2]))


def test_register_rejects_non_regions():
    with pytest.raises(TypeError, match="BoundaryRegion"):
        BoundaryManager().register("fluid_wall")  # type: ignore[arg-type]


def test_region_resolution_and_unknown_key_error():
    manager = _two_region_manager()
    assert manager.region("fluid_wall").name == "fluid_wall"
    with pytest.raises(KeyError, match="fluid_outlet.*fluid_inlet, fluid_wall"):
        manager.region("fluid_outlet")


def test_regions_are_ordered_by_name():
    manager = _two_region_manager()
    assert [region.name for region in manager.regions] == ["fluid_inlet", "fluid_wall"]


def test_len_and_contains_reflect_the_registry():
    manager = _two_region_manager()
    assert len(manager) == 2
    assert "fluid_wall" in manager
    assert "fluid_outlet" not in manager


def test_regions_containing_returns_name_ordered_matches():
    manager = _two_region_manager()
    matches = manager.regions_containing(5)
    assert [region.name for region in matches] == ["fluid_inlet", "fluid_wall"]
    assert manager.regions_containing(1) == (manager.region("fluid_inlet"),)
    assert manager.regions_containing(999) == ()


def test_multi_region_members_reports_corner_seeds():
    manager = _two_region_manager()
    assert manager.multi_region_members() == {
        5: (manager.region("fluid_inlet"), manager.region("fluid_wall"))
    }


def test_multi_region_members_empty_without_overlap():
    manager = BoundaryManager()
    manager.register(BoundaryRegion("a", [1, 2]))
    manager.register(BoundaryRegion("b", [3, 4]))
    assert manager.multi_region_members() == {}


def test_bind_resolves_target_and_paired_target():
    manager = _two_region_manager()
    spec = BoundarySpec("fluid_wall", BoundaryType.DIRICHLET, value=0.0)
    manager.bind(spec)
    assert spec.target is manager.region("fluid_wall")
    assert spec.paired_target is None
    assert manager.specs == (spec,)


def test_bind_resolves_periodic_pairing():
    manager = _two_region_manager()
    spec = BoundarySpec(
        "fluid_inlet", BoundaryType.PERIODIC, paired_region="fluid_wall"
    )
    manager.bind(spec)
    assert spec.target is manager.region("fluid_inlet")
    assert spec.paired_target is manager.region("fluid_wall")


def test_bind_rejects_non_specs():
    with pytest.raises(TypeError, match="BoundarySpec"):
        BoundaryManager().bind("spec")  # type: ignore[arg-type]


def test_bind_rejects_already_bound_specs():
    manager = _two_region_manager()
    spec = BoundarySpec("fluid_wall", BoundaryType.DIRICHLET)
    manager.bind(spec)
    with pytest.raises(ValueError, match="already bound"):
        manager.bind(spec)


def test_bind_unknown_region_raises_key_error():
    manager = BoundaryManager()
    spec = BoundarySpec("fluid_wall", BoundaryType.DIRICHLET)
    with pytest.raises(KeyError, match="fluid_wall"):
        manager.bind(spec)


def test_bind_unknown_paired_region_raises_key_error():
    manager = _two_region_manager()
    spec = BoundarySpec("fluid_inlet", BoundaryType.PERIODIC, paired_region="ghost")
    with pytest.raises(KeyError, match="ghost"):
        manager.bind(spec)


def test_multiple_specs_can_target_one_region():
    manager = _two_region_manager()
    first = BoundarySpec("fluid_wall", BoundaryType.DIRICHLET, value=0.0)
    second = BoundarySpec("fluid_wall", BoundaryType.NEUMANN, value=1.0)
    manager.bind(first)
    manager.bind(second)
    assert manager.specs_for("fluid_wall") == (first, second)
    assert manager.specs_for("fluid_inlet") == ()


def test_repr_counts_regions_and_specs():
    manager = _two_region_manager()
    assert repr(manager) == "BoundaryManager(regions=2, specs=0)"
