"""Named field data associated with entities (ADR-007 D6, ADR-018)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from caegraph.core.base import BaseObject

__all__ = ["Field"]


class Field(BaseObject):
    """Named field data: values plus unit, timestep and entity association.

    A :class:`Field` is the domain vocabulary for a physical quantity
    sampled on the entities of a representation (ADR-007 D6). Fields
    are *associated with entities* — never directly with geometry or
    topology, and never *owned* by the representation object: each
    field records its own entity scope, while
    :class:`~caegraph.core.CAEGraph` keeps association hooks only
    (ADR-018).

    Concrete entity binding and identifier mapping are defined by
    representation construction (ADR-016) and future entity model
    decisions, not by ``Field`` itself (ADR-018).

    Values are stored backend-agnostically (NumPy arrays, torch
    tensors, nested sequences, ...). Shape and entity-count consistency
    is the responsibility of representation construction and backend
    adaptation (ADR-016/017), not of this class.

    Args:
        name: Non-empty field name, for example ``"pressure"``.
        values: Field payload — any array-like object. Required: a
            field without data is a declaration, not a field.
        unit: Optional physical unit label, for example ``"Pa"``.
        timestep: Optional temporal index or label of the sample.
        association: Optional entity scope label identifying the
            entity family the values attach to — for example
            ``"node"``, ``"cell"`` or ``"particle"``. Labels denote
            entity families, never topology positions or semantic
            regions. The vocabulary is intentionally open because
            entity identity schemas are deliberately not frozen
            (ADR-018).
        metadata: Optional free-form key/value annotations.

    Raises:
        ValueError: If ``name`` is empty, ``values`` is ``None``, or
            ``unit``/``association`` is an empty string.
        TypeError: If ``unit``/``association`` are not strings,
            ``timestep`` is not a number, or the initial state fails
            :meth:`validate`.

    Examples:
        >>> field = Field("pressure", [0.1, 0.2], unit="Pa", association="node")
        >>> field.name
        'pressure'
        >>> field.association
        'node'
    """

    def __init__(
        self,
        name: str,
        values: Any,
        *,
        unit: str | None = None,
        timestep: float | None = None,
        association: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize payload and association semantics, then validate."""
        if values is None:
            raise ValueError(
                "values are required: a field without data is a declaration, not a field"
            )
        if unit is not None and (not isinstance(unit, str) or not unit.strip()):
            raise ValueError("unit must be a non-empty string or None")
        if timestep is not None and (
            not isinstance(timestep, (int, float)) or isinstance(timestep, bool)
        ):
            raise TypeError("timestep must be a number or None")
        if association is not None and (
            not isinstance(association, str) or not association.strip()
        ):
            raise ValueError("association must be a non-empty string or None")
        self._values = values
        self._unit = unit
        self._timestep = timestep
        self._association = association
        super().__init__(name, metadata)

    @property
    def values(self) -> Any:
        """Backend-agnostic field payload."""
        return self._values

    @property
    def unit(self) -> str | None:
        """Physical unit label, if declared."""
        return self._unit

    @property
    def timestep(self) -> float | None:
        """Temporal index or label of the sample, if declared."""
        return self._timestep

    @property
    def association(self) -> str | None:
        """Entity scope the values attach to (for example ``"node"``)."""
        return self._association

    def validate(self) -> None:
        """Raise if the field is in an invalid state (state layer only).

        Single state-only check: no metadata or cross layers are
        declared — metadata is an annotation channel (ARCHITECTURE.md
        §3.4).
        """
        if self._values is None:
            raise ValueError(
                "values are required: a field without data is a declaration, not a field"
            )
