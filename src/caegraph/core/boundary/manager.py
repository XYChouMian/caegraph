"""Semantic region registry with spec binding and corner queries (ADR-018)."""

from __future__ import annotations

from caegraph.core.boundary.region import BoundaryRegion
from caegraph.core.boundary.spec import BoundarySpec

__all__ = ["BoundaryManager"]


class BoundaryManager:
    """Registry of semantic regions and their bound condition declarations.

    The manager is the region-facing half of CAEGraph's semantic
    composition (ADR-018): it registers
    :class:`~caegraph.core.BoundaryRegion` objects by name, resolves
    :class:`~caegraph.core.BoundarySpec` bindings by name, and answers
    multi-region membership ("corner") queries over canonical member
    identifiers. It references topology — membership identifiers are
    resolved through a topology provider elsewhere — and owns no
    topology itself.

    Node-level ``NodeCategory.CORNER`` annotation is *derived* from
    these multi-region queries once node sets are resolvable through
    the topology subsystem (later Phase 2 gates); the manager itself
    stays at canonical-identifier granularity.

    Examples:
        >>> manager = BoundaryManager()
        >>> wall = BoundaryRegion("fluid_wall", [4, 5])
        >>> inlet = BoundaryRegion("fluid_inlet", [1, 5])
        >>> manager.register(wall) is wall
        True
        >>> manager.multi_region_members()
        {5: (inlet, wall)}
    """

    def __init__(self) -> None:
        """Start with an empty region registry and no bound specs."""
        self._regions: dict[str, BoundaryRegion] = {}
        self._specs: list[BoundarySpec] = []

    @property
    def regions(self) -> tuple[BoundaryRegion, ...]:
        """Registered regions, ordered by name."""
        return tuple(self._regions[name] for name in sorted(self._regions))

    @property
    def specs(self) -> tuple[BoundarySpec, ...]:
        """Bound specs, in binding order."""
        return tuple(self._specs)

    def register(self, region: BoundaryRegion) -> BoundaryRegion:
        """Register ``region`` under its name.

        Args:
            region: The semantic region to register.

        Returns:
            The registered region, unchanged.

        Raises:
            TypeError: If ``region`` is not a
                :class:`~caegraph.core.BoundaryRegion`.
            ValueError: If its name is already registered.
        """
        if not isinstance(region, BoundaryRegion):
            raise TypeError("register expects a BoundaryRegion")
        if region.name in self._regions:
            raise ValueError(f"boundary region {region.name!r} is already registered")
        self._regions[region.name] = region
        return region

    def region(self, name: str) -> BoundaryRegion:
        """Return the region registered under ``name``.

        Raises:
            KeyError: If ``name`` is unknown; the message lists all
                registered region names.
        """
        if name not in self._regions:
            available = ", ".join(sorted(self._regions)) or "<none>"
            raise KeyError(f"unknown boundary region {name!r}; registered: {available}")
        return self._regions[name]

    def regions_containing(self, member_id: int) -> tuple[BoundaryRegion, ...]:
        """Return the regions whose membership contains ``member_id``.

        Args:
            member_id: Canonical member identifier (a global facet ID
                for cell-based sources, ADR-014).

        Returns:
            Matching regions, ordered by name.
        """
        return tuple(
            self._regions[name]
            for name in sorted(self._regions)
            if member_id in self._regions[name].membership
        )

    def multi_region_members(self) -> dict[int, tuple[BoundaryRegion, ...]]:
        """Return member identifiers belonging to more than one region.

        Linear scan over total membership — intended for batch corner
        derivation, not hot loops. Known performance concern for
        large graphs: every call re-scans all region memberships,
        O(total members) time and memory, which is prohibitive at CAE
        scale (millions of facets). TODO: optimize with an inverted
        member-to-regions index (lazy cache) once hot consumers
        appear — ADR-018 defers storage and indexing decisions, so
        the optimization requires no API change.

        Returns:
            Mapping ``member_id -> regions`` (ordered by name) for
            every canonical identifier with multi-region membership.
            These are the seeds of node-level ``NodeCategory.CORNER``
            derivation, which composes this query with node sets
            derived through the topology subsystem.
        """
        owners: dict[int, list[BoundaryRegion]] = {}
        for region in self._regions.values():
            for member_id in region.membership:
                owners.setdefault(member_id, []).append(region)
        return {
            member_id: tuple(sorted(members, key=lambda r: r.name))
            for member_id, members in sorted(owners.items())
            if len(members) > 1
        }

    def bind(self, spec: BoundarySpec) -> None:
        """Bind ``spec`` by resolving its region names to objects.

        The spec's ``region`` (and ``paired_region`` when declared) is
        resolved against the registry; the resolution result is cached
        on the spec at binding time (``target`` / ``paired_target``)
        while the region names remain the canonical references.

        Args:
            spec: The boundary declaration to bind.

        Raises:
            TypeError: If ``spec`` is not a
                :class:`~caegraph.core.BoundarySpec`.
            ValueError: If the spec is already bound.
            KeyError: If a referenced region name is not registered.
        """
        if not isinstance(spec, BoundarySpec):
            raise TypeError("bind expects a BoundarySpec")
        if spec.target is not None:
            raise ValueError(f"spec for region {spec.region!r} is already bound")
        target = self.region(spec.region)
        paired_target = (
            self.region(spec.paired_region) if spec.paired_region is not None else None
        )
        spec._target = target
        spec._paired_target = paired_target
        self._specs.append(spec)

    def specs_for(self, region_name: str) -> tuple[BoundarySpec, ...]:
        """Return bound specs targeting ``region_name``, in binding order."""
        return tuple(spec for spec in self._specs if spec.region == region_name)

    def __contains__(self, name: object) -> bool:
        return name in self._regions

    def __len__(self) -> int:
        return len(self._regions)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(regions={len(self._regions)}, specs={len(self._specs)})"
