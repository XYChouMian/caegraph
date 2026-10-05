"""Field declaration and realization data (ADR-018/020/021/023)."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from caegraph.core.base import BaseObject

__all__ = ["Field", "FieldData"]

_SUPPORTED_REALIZATION_FAMILIES: frozenset[str] = frozenset({"node", "cell"})
_GLOBAL_SCOPE: str = "global"
_SNAPSHOT_SCOPE: str = "snapshot"
_REALIZATION_SCOPES: frozenset[str] = frozenset({_GLOBAL_SCOPE, _SNAPSHOT_SCOPE})


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

    ``association`` is **required** (ADR-021 D3): ``None`` is not a
    legal canonical Field state. The label vocabulary is open —
    ``node`` / ``cell`` / ``particle`` are declarable examples — with
    ``node`` / ``cell`` as the Phase 2 supported realization families
    (ADR-021 D2); unsupported families are declarable but
    realization-less (ADR-021 D5).

    Args:
        name: Non-empty field name, for example ``"pressure"``.
        association: Entity family the quantity attaches to —
            required, non-empty (ADR-021 D3). Labels denote entity
            families, never topology positions or semantic regions
            (ADR-018).
        unit: Optional physical unit label, for example ``"Pa"``.
        metadata: Optional free-form key/value annotations.

    Raises:
        ValueError: If ``name`` is empty, or ``association`` is not
            a non-empty string, or ``unit`` is an empty string
            (checked only when not ``None`` — non-string values fail
            the same check), or the initial state fails
            :meth:`validate`.

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
        association: str,
        unit: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize the declaration semantics, then validate."""
        if not isinstance(association, str) or not association.strip():
            raise ValueError("association must be a non-empty string")
        if unit is not None and (not isinstance(unit, str) or not unit.strip()):
            raise ValueError("unit must be a non-empty string or None")
        self._unit = unit
        self._association = association
        super().__init__(name, metadata)

    @property
    def unit(self) -> str | None:
        """Physical unit label, if declared."""
        return self._unit

    @property
    def association(self) -> str:
        """Entity family the quantity attaches to (required, ADR-021 D3)."""
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
        if not isinstance(self._association, str) or not self._association.strip():
            raise ValueError("association must be a non-empty string")


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

    Only supported realization families carry realization data —
    ``field.association`` must name ``node`` or ``cell``
    (ADR-021 D5); unsupported-family declarations are
    realization-less and their realizations are rejected at
    construction.

    Every realization carries an **explicit scope** (ADR-023 D-04):
    ``"global"`` (global/static realization — belongs to no Snapshot)
    or ``"snapshot"`` (snapshot-scoped realization — belongs to
    exactly one Snapshot). Scope is a required keyword: it is never
    inferred from timestep values, missing time information or
    membership presence, and it is immutable after construction.

    Member set (current Phase 2 implementation choice): ``field``,
    ``values``, ``scope``, ``timestep``, ``metadata``. Time, coverage
    and sample identity are deferred / NOT frozen (ADR-020 D2).
    ``timestep`` is a legacy / compatibility member with **no
    canonical temporal authority** (ADR-023 D-07): it participates in
    no membership, ordering, alignment or selection, and no mapping
    to ``physical_time`` or ``solver_step`` is defined.

    Args:
        field: The declaration this realization belongs to — its
            association must name a supported realization family
            (``node`` / ``cell``, ADR-021 D5).
        values: Realization payload — any array-like object. A
            missing argument is a signature error (Python
            ``TypeError``); an explicit ``None`` payload is rejected.
        scope: Explicit realization scope — ``"global"`` or
            ``"snapshot"`` (required keyword, no default, ADR-023
            D-04). Global/static realizations enter the canonical
            registry through the representation builder;
            snapshot-scoped realizations enter atomically with their
            Snapshot membership via ``CAEGraph.register_snapshot``.
        timestep: Optional numeric temporal index of this
            realization (``int`` or ``float``; bools rejected) —
            legacy / compatibility member without canonical temporal
            authority (ADR-023 D-07).
        metadata: Optional free-form key/value annotations.

    Raises:
        TypeError: If ``field`` is not a :class:`Field`, or
            ``timestep`` is not a number (bools rejected despite
            being int subclasses). A missing ``scope`` (or
            ``values``) argument is likewise a signature error.
        ValueError: If ``values`` is explicitly ``None``,
            ``scope`` is not ``"global"`` / ``"snapshot"``, or
            ``field.association`` names an unsupported realization
            family (ADR-021 D5).

    Examples:
        >>> pressure = Field("pressure", unit="Pa", association="node")
        >>> frame = FieldData(pressure, [0.1, 0.2], scope="global", timestep=3)
        >>> frame.field is pressure
        True
        >>> frame.field.unit
        'Pa'
        >>> frame.timestep
        3
        >>> frame.scope
        'global'
    """

    def __init__(
        self,
        field: Field,
        values: Any,
        *,
        scope: str,
        timestep: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize the realization payload and its declaration reference.

        Assigns the member set and then delegates to
        :meth:`validate` — mirroring the BaseObject lifecycle pattern
        (construction-time validation).
        """
        if not isinstance(field, Field):
            raise TypeError("field must be a Field declaration (ADR-020 D3)")
        if field.association not in _SUPPORTED_REALIZATION_FAMILIES:
            raise ValueError(
                f"unsupported realization family {field.association!r}: "
                f"FieldData requires {sorted(_SUPPORTED_REALIZATION_FAMILIES)} "
                "(no cardinality contract for this family yet — ADR-021 D5)"
            )
        if values is None:
            raise ValueError(
                "values are required: a realization without data is not a realization"
            )
        if not isinstance(scope, str) or scope not in _REALIZATION_SCOPES:
            raise ValueError(
                f"scope must be one of {sorted(_REALIZATION_SCOPES)} "
                "(explicit realization scope — never inferred, ADR-023 D-04)"
            )
        if timestep is not None and (
            not isinstance(timestep, (int, float)) or isinstance(timestep, bool)
        ):
            raise TypeError("timestep must be a number or None")
        self._field = field
        self._values = values
        self._scope = scope
        self._timestep = timestep
        self._metadata: dict[str, Any] = dict(metadata) if metadata is not None else {}
        self.validate()

    @property
    def field(self) -> Field:
        """The declaration this realization belongs to (authoritative source)."""
        return self._field

    @property
    def values(self) -> Any:
        """Backend-agnostic realization payload."""
        return self._values

    @property
    def scope(self) -> str:
        """Explicit realization scope: ``"global"`` or ``"snapshot"`` (ADR-023 D-04)."""
        return self._scope

    @property
    def timestep(self) -> float | None:
        """Legacy temporal index without canonical temporal authority (ADR-023 D-07)."""
        return self._timestep

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Free-form annotations of this realization (read-only view)."""
        return MappingProxyType(self._metadata)

    def validate(self) -> None:
        """Raise if the realization is in an invalid state.

        Internal consistency check: a :class:`Field` reference to a
        supported realization family, a non-``None`` values payload,
        an explicit realization scope and a numeric (or absent)
        timestep. Mirrors the BaseObject lifecycle pattern —
        ``__init__`` assigns and then delegates to this method.
        """
        if not isinstance(self._field, Field):
            raise TypeError("field must be a Field declaration (ADR-020 D3)")
        if self._field.association not in _SUPPORTED_REALIZATION_FAMILIES:
            raise ValueError(
                f"unsupported realization family {self._field.association!r}: "
                f"FieldData requires {sorted(_SUPPORTED_REALIZATION_FAMILIES)} "
                "(ADR-021 D5)"
            )
        if self._values is None:
            raise ValueError(
                "values are required: a realization without data is not a realization"
            )
        if not isinstance(self._scope, str) or self._scope not in _REALIZATION_SCOPES:
            raise ValueError(
                f"scope must be one of {sorted(_REALIZATION_SCOPES)} "
                "(explicit realization scope, ADR-023 D-04)"
            )
        if self._timestep is not None and (
            not isinstance(self._timestep, (int, float))
            or isinstance(self._timestep, bool)
        ):
            raise TypeError("timestep must be a number or None")
