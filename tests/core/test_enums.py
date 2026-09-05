"""Tests for caegraph.core.enums shared vocabulary."""

from __future__ import annotations

from caegraph.core import BoundaryType, NodeCategory


def test_boundary_type_members_and_values():
    assert BoundaryType.DIRICHLET.value == "dirichlet"
    assert BoundaryType.NEUMANN.value == "neumann"
    assert BoundaryType.FREE.value == "free"
    assert len(BoundaryType) == 3


def test_boundary_type_compares_against_plain_strings():
    assert BoundaryType.DIRICHLET == "dirichlet"


def test_node_category_members_and_values():
    assert NodeCategory.INTERIOR.value == "interior"
    assert NodeCategory.BOUNDARY.value == "boundary"
    assert NodeCategory.CORNER.value == "corner"
    assert len(NodeCategory) == 3


def test_node_category_by_value_lookup():
    assert NodeCategory("corner") is NodeCategory.CORNER
