"""Tests for caegraph.core.boundary.region.BoundaryRegion."""

from __future__ import annotations

import pytest

from caegraph.core import BoundaryRegion


def test_membership_is_stored_order_free_and_duplicate_free():
    region = BoundaryRegion("fluid_wall", [12, 3, 12])
    assert region.membership == frozenset({3, 12})


def test_empty_membership_is_rejected():
    with pytest.raises(ValueError, match="at least one member"):
        BoundaryRegion("fluid_wall", [])


def test_non_int_member_is_rejected():
    with pytest.raises(TypeError, match="must be ints"):
        BoundaryRegion("fluid_wall", [1, "2"])  # type: ignore[list-item]


def test_bool_member_is_rejected():
    with pytest.raises(TypeError, match="must be ints"):
        BoundaryRegion("fluid_wall", [True])  # type: ignore[list-item]


def test_empty_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        BoundaryRegion("   ", [1])


def test_software_naming_lives_in_metadata():
    region = BoundaryRegion("fluid_wall", [1, 2], metadata={"software_name": "wall"})
    assert region.metadata == {"software_name": "wall"}


def test_region_is_a_domain_truth_base_object():
    region = BoundaryRegion("fluid_wall", [1])
    assert region.name == "fluid_wall"
    assert repr(region) == "BoundaryRegion(name='fluid_wall')"


def test_frozenset_input_is_accepted():
    region = BoundaryRegion("fluid_wall", frozenset({7, 8}))
    assert region.membership == frozenset({7, 8})
