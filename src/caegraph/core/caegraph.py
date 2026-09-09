"""Graph-native canonical domain representation (ADR-015/018)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from caegraph.core.base import BaseObject
from caegraph.core.boundary.manager import BoundaryManager
from caegraph.core.field import Field

__all__ = ["CAEGraph"]


class CAEGraph(BaseObject):
    """Graph-native canonical domain representation (ADR-015).

    Semantic composition (ADR-018): entities, relations, geometry,
    fields, regions, conditions — plus the topology subsystem as an
    *optional semantic provider* referenced by this object (present
    for cell-based discretizations, absent for mesh-free ones,
    ADR-014). Semantic composition deliberately does not define class
    members or storage layout: entity and relation population arrives
    with representation construction (ADR-016) and is not frozen
    here.

    This class exposes only the minimal association hooks the Phase 2
    domain vocabulary needs: an optional topology provider reference,
    a field association list (references — fields belong to entities,
    never to the representation object, ADR-018), and the boundary
    manager hosting semantic regions and condition declarations.

    CAEGraph never imports ``torch_geometric``: PyG / networkx /
    igraph are backends or analysis engines reached through the
    backend adapter layer (ADR-007/017), never the domain model.

    Args:
        name: Non-empty name of the representation instance.
        topology: Optional topology provider — the cell-based ``Mesh``
            of the topology subsystem once implemented (construction
            gate 3). ``None`` denotes a mesh-free representation or a
            provider not yet attached.
        metadata: Optional free-form annotations.

    Raises:
        TypeError: If ``topology`` is neither ``None`` nor a
            :class:`~caegraph.core.BaseObject` (topology providers
            belong to the domain-truth family).

    Examples:
        >>> graph = CAEGraph("channel_flow")
        >>> graph.topology is None  # mesh-free state until a provider is attached
        True
        >>> graph.associate_field(Field("pressure", [0.1, 0.2], association="node"))
        >>> [field.name for field in graph.associated_fields]
        ['pressure']
    """

    def __init__(
        self,
        name: str,
        *,
        topology: BaseObject | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize association hooks, then validate.

        Raises:
            TypeError: If ``topology`` is neither ``None`` nor a
                :class:`~caegraph.core.BaseObject`.
        """
        if topology is not None and not isinstance(topology, BaseObject):
            raise TypeError(
                "topology must be a BaseObject provider of the topology "
                "subsystem or None (referenced provider, never a framework object)"
            )
        self._topology = topology
        self._fields: dict[str, Field] = {}
        self._boundaries = BoundaryManager()
        super().__init__(name, metadata)

    @property
    def topology(self) -> BaseObject | None:
        """Referenced topology provider (cell-based ``Mesh``); ``None`` if absent."""
        return self._topology

    @property
    def boundaries(self) -> BoundaryManager:
        """Semantic region registry and condition declarations (ADR-018)."""
        return self._boundaries

    @property
    def associated_fields(self) -> tuple[Field, ...]:
        """Associated field data, ordered by name (references, not ownership)."""
        return tuple(self._fields[name] for name in sorted(self._fields))

    def associate_field(self, field: Field) -> None:
        """Associate ``field`` with this representation (ADR-018).

        Association is a reference, not ownership: fields belong to
        entities and keep their own entity scope. Field names are
        unique per representation.

        Args:
            field: The field data to associate.

        Raises:
            TypeError: If ``field`` is not a
                :class:`~caegraph.core.Field`.
            ValueError: If a field with the same name is already
                associated.
        """
        if not isinstance(field, Field):
            raise TypeError("associate_field expects a Field")
        if field.name in self._fields:
            raise ValueError(f"field {field.name!r} is already associated")
        self._fields[field.name] = field

    def validate(self) -> None:
        """Raise if the representation is in an invalid state.

        The topology provider must remain a domain-truth object (or
        absent), and associated entries must remain fields.
        """
        if self._topology is not None and not isinstance(self._topology, BaseObject):
            raise TypeError(
                "topology must be a BaseObject provider of the topology subsystem or None"
            )
        for field in self._fields.values():
            if not isinstance(field, Field):
                raise TypeError("associated entries must be Field objects")
