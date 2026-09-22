"""Named semantic regions with source-discretization-dependent membership (ADR-018)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from caegraph.core.base import BaseObject

__all__ = ["BoundaryRegion"]


class BoundaryRegion(BaseObject):
    """Named semantic region with source-discretization-dependent membership.

    A region unifies boundary, interface and physical groups as one
    semantic concept (ADR-018). Membership is represented according to
    the source discretization: cell-based sources use canonical global
    topology identifiers — global facet IDs per ADR-014 — while
    mesh-free sources group entities directly. Node sets are *derived
    views* resolved through the topology provider, never stored here;
    this class references topology, it does not own it
    (ADR-014/018).

    Software-specific names (``wall``, ``inlet``, ``outlet`` ...) live
    in :attr:`metadata`, never in the boundary-type vocabulary
    (ADR-010).

    Args:
        name: Non-empty semantic region name, for example
            ``"fluid_wall"``.
        membership: Canonical member identifiers of the region —
            global facet IDs for cell-based sources (ADR-014). Must be
            a non-empty iterable of ints; order is irrelevant and
            duplicates collapse.
        metadata: Optional free-form annotations; carries software
            naming metadata per ADR-010.

    Raises:
        ValueError: If ``name`` is empty or ``membership`` is empty.
        TypeError: If a member identifier is not an int.

    Examples:
        >>> wall = BoundaryRegion("fluid_wall", [12, 3, 12])
        >>> sorted(wall.membership)
        [3, 12]
    """

    def __init__(
        self,
        name: str,
        membership: Iterable[int],
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize membership identifiers, then validate."""
        members = frozenset(membership)
        if not members:
            raise ValueError("membership must contain at least one member identifier")
        for member in members:
            if not isinstance(member, int) or isinstance(member, bool):
                raise TypeError(
                    "membership identifiers must be ints "
                    "(global facet IDs for cell-based sources, ADR-014)"
                )
        self._membership = members
        super().__init__(name, metadata)

    @property
    def membership(self) -> frozenset[int]:
        """Canonical member identifiers (order-free, duplicate-free)."""
        return self._membership

    def validate(self) -> None:
        """Raise if the region is in an invalid state (state layer only).

        Single state-only check: no metadata or cross layers are
        declared — metadata is an annotation channel (ARCHITECTURE.md
        §3.4).
        """
        if not self._membership:
            raise ValueError("membership must contain at least one member identifier")
