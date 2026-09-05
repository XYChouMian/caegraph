"""Tests for caegraph.core.enums shared vocabulary."""

from __future__ import annotations

import pytest

from caegraph.core import BoundaryType, NodeCategory


def test_boundary_type_members_and_values():
    expected = {
        "DIRICHLET": "dirichlet",
        "NEUMANN": "neumann",
        "ROBIN": "robin",
        "PERIODIC": "periodic",
        "SYMMETRY": "symmetry",
        "INTERFACE": "interface",
        "NONE": "none",
    }
    for member, value in expected.items():
        assert BoundaryType[member].value == value
    assert len(BoundaryType) == len(expected)


def test_boundary_type_members_are_serializable_strings():
    for member in BoundaryType:
        assert isinstance(member.value, str)
        assert member == member.value


def test_invalid_boundary_type_fails():
    with pytest.raises(ValueError):
        BoundaryType("wall")


def test_free_was_replaced_by_none():
    assert not hasattr(BoundaryType, "FREE")
    assert BoundaryType.NONE.value == "none"


def test_node_category_members_and_values():
    assert NodeCategory.INTERIOR.value == "interior"
    assert NodeCategory.BOUNDARY.value == "boundary"
    assert NodeCategory.CORNER.value == "corner"
    assert len(NodeCategory) == 3


def test_node_category_by_value_lookup():
    assert NodeCategory("corner") is NodeCategory.CORNER
