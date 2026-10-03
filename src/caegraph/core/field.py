"""Field declaration and realization data (ADR-018/020)."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from caegraph.core.base import BaseObject

__all__ = ["Field", "FieldData"]


class Field(BaseObject):
    """Stable physical quantity declaration (ADR-020 D1).

    A :class:`Field` declares that a physical quantity exists in the
    problem: its name, unit, entity association and component
    semantics are the single authoritative source (ADR-020 D3). It
    carries **no values and no timestep** — realization data lives on
    :class:`FieldData` (one Field to zero-or-many realizations), and
    a Field may legally exist without any realization data
    (problem-before-solving, ADR-020 D4).

    Fields are *associated with entities* — never directly with
    geometry or topology, and never *owned* by the representation
    object (ADR-018). The semantic role is frozen; the exact
    member/API form is not frozen (ADR-020), and the
    component-semantics vocabulary is deferred / NOT frozen
    (ADR-020 D1).

    Args:
        name: Non-empty field name, for example ``"pressure"``.
        unit: Optional physical unit label, for example ``"Pa"``.
        association: Optional entity scope label identifying the
            entity family the quantity attaches to — for example
            ``"node"``, ``"cell"`` or ``"particle"``. Labels denote
            entity families, never topology positions or semantic
            regions (ADR-018).
        metadata: Optional free-form key/value annotations.

    Raises:
        ValueError: If ``name`` is empty, or ``unit``/``association``
            is an empty string (checked only when not ``None``).
        TypeError: If ``unit``/``association`` are not strings, or
            the initial state fails :meth:`validate`.

    Examples:
        >>> field = Field("pressure", unit="Pa", association="node")
        >>> field.name
        'pressure'
        >>> field.association
        'node'
    """

    def __init__(
        self,
        name: str,
        *,
        unit: str | None = None,
        association: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize the declaration semantics, then validate."""
        if unit is not None and (not isinstance(unit, str) or not unit.strip()):
            raise ValueError("unit must be a non-empty string or None")
        if association is not None and (
            not isinstance(association, str) or not association.strip()
        ):
            raise ValueError("association must be a non-empty string or None")
        self._unit = unit
        self._association = association
        super().__init__(name, metadata)

    @property
    def unit(self) -> str | None:
        """Physical unit label, if declared."""
        return self._unit

    @property
    def association(self) -> str | None:
        """Entity scope the quantity attaches to (for example ``"node"``)."""
        return self._association

    def validate(self) -> None:
        """Raise if the declaration is in an invalid state (state layer only).

        Single state-only check: no metadata or cross layers are
        declared — metadata is an annotation channel (ARCHITECTURE.md
        §3.4).
        """
        if self._unit is not None and (
            not isinstance(self._unit, str) or not self._unit.strip()
        ):
            raise ValueError("unit must be a non-empty string or None")
        if self._association is not None and (
            not isinstance(self._association, str) or not self._association.strip()
        ):
            raise ValueError("association must be a non-empty string or None")


class FieldData:
    """One realization of a :class:`Field` declaration (ADR-020 D2).

    ``FieldData`` carries the values payload and realization metadata
    of exactly one Field. The referenced Field is the single
    authoritative source of name/unit/association semantics
    (ADR-020 D3): FieldData must not independently define, modify or
    override them, and consumers resolve semantics through the
    ``field`` reference. The identity/reference mechanism (read-only
    proxies, caches, derived accessors) is deferred / NOT frozen
    (ADR-020 D3).

    Realization data lives in the CAEGraph canonical data flow,
    accessible via the canonical representation (ADR-020 D4);
    ownership / container / storage forms are NOT frozen, and the
    representation builder is the only write path (an ADR-020
    scope-exclusion implementation microdecision, re-evaluable at
    gate 4b). Lineage: a plain class — deliberately not a
    :class:`~caegraph.core.BaseObject` subclass in Phase 2, because
    BaseObject's name-based identity would duplicate Field
    semantics.

    Member set (finalized in the field-split dispatch): ``field``,
    ``values``, ``timestep``, ``metadata``. Time, coverage and sample
    identity are deferred / NOT frozen (ADR-020 D2).

    Args:
        field: The declaration this realization belongs to.
        values: Realization payload — any array-like object. A
            missing argument is a signature error (Python
            ``TypeError``); an explicit ``None`` payload is rejected.
        timestep: Optional temporal index or label of this
            realization.
        metadata: Optional free-form key/value annotations.

    Raises:
        TypeError: If ``field`` is not a :class:`Field`, or
            ``timestep`` is not a number (bools rejected despite
            being int subclasses).
        ValueError: If ``values`` is explicitly ``None``.

    Examples:
        >>> pressure = Field("pressure", unit="Pa", association="node")
        >>> frame = FieldData(pressure, [0.1, 0.2], timestep=3)
        >>> frame.field is pressure
        True
        >>> frame.field.unit
        'Pa'
        >>> frame.timestep
        3
    """

    def __init__(
        self,
        field: Field,
        values: Any,
        *,
        timestep: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize the realization payload and its declaration reference."""
        if not isinstance(field, Field):
            raise TypeError("field must be a Field declaration (ADR-020 D3)")
        if values is None:
            raise ValueError(
                "values are required: a realization without data is not a realization"
            )
        if timestep is not None and (
            not isinstance(timestep, (int, float)) or isinstance(timestep, bool)
        ):
            raise TypeError("timestep must be a number or None")
        self._field = field
        self._values = values
        self._timestep = timestep
        self._metadata: dict[str, Any] = dict(metadata) if metadata else {}

    @property
    def field(self) -> Field:
        """The declaration this realization belongs to (authoritative source)."""
        return self._field

    @property
    def values(self) -> Any:
        """Backend-agnostic realization payload."""
        return self._values

    @property
    def timestep(self) -> float | None:
        """Temporal index or label of this realization, if declared."""
        return self._timestep

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Free-form annotations of this realization (read-only view)."""
        return MappingProxyType(self._metadata)

    def validate(self) -> None:
        """Raise if the realization is in an invalid state.

        Internal consistency check: a :class:`Field` reference, a
        non-``None`` values payload and a numeric (or absent)
        timestep.
        """
        if not isinstance(self._field, Field):
            raise TypeError("field must be a Field declaration (ADR-020 D3)")
        if self._values is None:
            raise ValueError(
                "values are required: a realization without data is not a realization"
            )
        if self._timestep is not None and (
            not isinstance(self._timestep, (int, float))
            or isinstance(self._timestep, bool)
        ):
            raise TypeError("timestep must be a number or None")
