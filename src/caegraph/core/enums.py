"""Shared vocabulary enums for boundary conditions and node roles (ADR-007/010)."""

from __future__ import annotations

from enum import Enum, unique

__all__ = ["BoundaryType", "NodeCategory"]


@unique
class BoundaryType(str, Enum):
    """Mathematical boundary-condition categories (ADR-010).

    The enum is deliberately cross-software: it records the
    *mathematical* kind of a constraint, never CAE-application names
    such as wall/inlet/outlet — the same "inlet" may be a Dirichlet
    velocity, a Neumann mass flux, or a pressure constraint, so
    application names belong to BoundaryRegion metadata instead.

    Members:
        DIRICHLET: prescribed value, ``u = g``.
        NEUMANN: prescribed gradient/flux, ``du/dn = g``.
        ROBIN: mixed condition, ``a*u + b*du/dn = g``.
        PERIODIC: paired-region constraint.
        SYMMETRY: symmetry-plane constraint.
        INTERFACE: coupling/interface constraint (FSI, CHT, multi-domain).
        NONE: tracked region without an active constraint.

    Phase 2 binds these to boundary regions discovered from CAE
    physical groups.
    """

    DIRICHLET = "dirichlet"
    NEUMANN = "neumann"
    ROBIN = "robin"
    PERIODIC = "periodic"
    SYMMETRY = "symmetry"
    INTERFACE = "interface"
    NONE = "none"


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
