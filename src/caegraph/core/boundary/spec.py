"""User-facing boundary declarations with slot-coherence validation (ADR-010/011)."""

from __future__ import annotations

from collections.abc import Mapping

from caegraph.core.boundary.region import BoundaryRegion
from caegraph.core.enums import BoundaryType

__all__ = ["BoundarySpec"]

_CONSTRAINT_VALUED = frozenset(
    {BoundaryType.DIRICHLET, BoundaryType.NEUMANN, BoundaryType.ROBIN}
)


class BoundarySpec:
    """Boundary declaration: a region name plus a type and coherent slots.

    A :class:`BoundarySpec` is the user-facing constraint *declaration*
    (ADR-018: conditions are declarations that reference regions and
    field data — never the evaluated constraint itself). It targets a
    :class:`~caegraph.core.BoundaryRegion` **by name**; the object
    link is optional and resolved later by
    :meth:`~caegraph.core.BoundaryManager.bind`.

    Slot coherence is validated fail-fast per type (ADR-011):

    - ``PERIODIC`` requires ``paired_region`` (differing from
      ``region``); cross-domain pairing information for ``INTERFACE``
      regions also travels in ``paired_region``; every other type
      forbids it.
    - Value slots (``value``, ``weight``, ``time_dependent``,
      ``space_dependent``) are meaningful only for constraint-valued
      types (DIRICHLET / NEUMANN / ROBIN); illegal combinations raise
      instead of being silently ignored.
    - ``parameters`` (generic coefficient container, e.g. ``a``/``b``
      for ``a*u + b*du/dn = g``) is reserved for ``ROBIN``.

    The callable-value form (:class:`~caegraph.core.FieldFunction`,
    ``(t, pos) -> tensors``) is deferred to the BC-declaration slice;
    in Phase 2 the value slot carries plain data only (ADR-011).

    Args:
        region: Name of the targeted semantic region.
        boundary_type: Mathematical boundary category (ADR-010).
        value: Optional prescribed value ``g`` (constraint-valued
            types only).
        weight: Optional combination weight (constraint-valued types
            only).
        paired_region: Name of the paired region — required for
            ``PERIODIC``, optional for ``INTERFACE``, forbidden
            otherwise.
        parameters: Optional non-empty coefficient mapping (``ROBIN``
            only).
        time_dependent: Value varies in time (constraint-valued types
            only).
        space_dependent: Value varies in space (constraint-valued
            types only).

    Raises:
        ValueError: If any slot combination violates the coherence
            matrix above.
        TypeError: If ``region``/``paired_region`` are not non-empty
            strings, ``boundary_type`` is not a
            :class:`~caegraph.core.BoundaryType`, ``value``/``weight``
            are not numbers, ``parameters`` is not a numeric mapping,
            or the dependence flags are not bools.

    Examples:
        >>> spec = BoundarySpec("fluid_inlet", BoundaryType.DIRICHLET, value=1.5)
        >>> spec.boundary_type
        <BoundaryType.DIRICHLET: 'dirichlet'>
    """

    def __init__(
        self,
        region: str,
        boundary_type: BoundaryType,
        *,
        value: float | None = None,
        weight: float | None = None,
        paired_region: str | None = None,
        parameters: Mapping[str, float] | None = None,
        time_dependent: bool = False,
        space_dependent: bool = False,
    ) -> None:
        """Store declaration slots, then validate coherence."""
        if not isinstance(region, str) or not region.strip():
            raise ValueError("region must be a non-empty region name")
        if not isinstance(boundary_type, BoundaryType):
            raise TypeError("boundary_type must be a BoundaryType (ADR-010)")
        if value is not None and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            raise TypeError("value must be a number or None")
        if weight is not None and (
            not isinstance(weight, (int, float)) or isinstance(weight, bool)
        ):
            raise TypeError("weight must be a number or None")
        if paired_region is not None and (
            not isinstance(paired_region, str) or not paired_region.strip()
        ):
            raise ValueError("paired_region must be a non-empty region name or None")
        if parameters is not None:
            if not isinstance(parameters, Mapping):
                raise TypeError(
                    "parameters must be a mapping of coefficient names to numbers"
                )
            if not parameters:
                raise ValueError("parameters must be non-empty when provided")
            for coefficient in parameters.values():
                if not isinstance(coefficient, (int, float)) or isinstance(
                    coefficient, bool
                ):
                    raise TypeError("parameter coefficients must be numbers")
        if not isinstance(time_dependent, bool) or not isinstance(
            space_dependent, bool
        ):
            raise TypeError("time_dependent and space_dependent must be bools")

        self._region = region
        self._boundary_type = boundary_type
        self._value = value
        self._weight = weight
        self._paired_region = paired_region
        self._parameters: dict[str, float] | None = (
            dict(parameters) if parameters is not None else None
        )
        self._time_dependent = time_dependent
        self._space_dependent = space_dependent
        self._target: BoundaryRegion | None = None
        self._paired_target: BoundaryRegion | None = None
        self.validate()

    @property
    def region(self) -> str:
        """Name of the targeted semantic region."""
        return self._region

    @property
    def boundary_type(self) -> BoundaryType:
        """Mathematical boundary category (ADR-010)."""
        return self._boundary_type

    @property
    def value(self) -> float | None:
        """Prescribed value ``g`` (constraint-valued types only)."""
        return self._value

    @property
    def weight(self) -> float | None:
        """Combination weight (constraint-valued types only)."""
        return self._weight

    @property
    def paired_region(self) -> str | None:
        """Paired region name: required for PERIODIC, optional for INTERFACE."""
        return self._paired_region

    @property
    def parameters(self) -> dict[str, float] | None:
        """Defensive copy of the coefficient mapping (``ROBIN`` only)."""
        return dict(self._parameters) if self._parameters is not None else None

    @property
    def time_dependent(self) -> bool:
        """Whether the value varies in time (constraint-valued types only)."""
        return self._time_dependent

    @property
    def space_dependent(self) -> bool:
        """Whether the value varies in space (constraint-valued types only)."""
        return self._space_dependent

    @property
    def target(self) -> BoundaryRegion | None:
        """Resolved target region, once bound by the BoundaryManager.

        The resolved object reference is a binding-time cache; the
        region name remains the canonical reference.
        """
        return self._target

    @property
    def paired_target(self) -> BoundaryRegion | None:
        """Resolved paired region, once bound (PERIODIC / INTERFACE).

        The resolved object reference is a binding-time cache; the
        paired region name remains the canonical reference.
        """
        return self._paired_target

    def validate(self) -> None:
        """Enforce the per-type slot-coherence matrix (ADR-011), fail-fast.

        Raises:
            ValueError: If a slot combination is meaningless for the
                declared :attr:`boundary_type`.
        """
        if self._boundary_type is BoundaryType.PERIODIC:
            if self._paired_region is None:
                raise ValueError("PERIODIC requires a paired_region (ADR-011)")
            if self._paired_region == self._region:
                raise ValueError("paired_region must differ from region")
        elif self._boundary_type is BoundaryType.INTERFACE:
            if self._paired_region == self._region:
                raise ValueError("paired_region must differ from region")
        elif self._paired_region is not None:
            raise ValueError(
                "paired_region is reserved for PERIODIC (required) "
                "and INTERFACE (optional cross-domain pairing, ADR-011)"
            )

        if self._boundary_type not in _CONSTRAINT_VALUED and (
            self._value is not None
            or self._weight is not None
            or self._time_dependent
            or self._space_dependent
        ):
            raise ValueError(
                "value slots (value/weight/time_dependent/space_dependent) are only "
                "meaningful for constraint-valued types (dirichlet/neumann/robin, ADR-011)"
            )

        if (
            self._parameters is not None
            and self._boundary_type is not BoundaryType.ROBIN
        ):
            raise ValueError("parameters are reserved for ROBIN coefficients (ADR-011)")

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(region={self._region!r}, "
            f"boundary_type={self._boundary_type!r})"
        )
