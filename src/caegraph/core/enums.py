"""Shared vocabulary enums for boundary conditions and node roles (ADR-007)."""

from __future__ import annotations

from enum import Enum, unique

__all__ = ["BoundaryType", "NodeCategory"]


@unique
class BoundaryType(str, Enum):
    """Physical boundary-condition types (design vocabulary, ADR-007).

    Phase 2 binds these to boundary regions discovered from CAE
    physical groups; ``FREE`` marks regions that are tracked but carry
    no essential or natural constraint.
    """

    DIRICHLET = "dirichlet"
    NEUMANN = "neumann"
    FREE = "free"


@unique
class NodeCategory(str, Enum):
    """Role of a mesh node with respect to boundary regions (ADR-007).

    ``CORNER`` identifies nodes that belong to more than one boundary
    region; it is derived during Mesh-to-Graph conversion, never
    declared by users.
    """

    INTERIOR = "interior"
    BOUNDARY = "boundary"
    CORNER = "corner"
