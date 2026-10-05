"""Snapshot temporal organization construct (ADR-023)."""

from __future__ import annotations

from collections.abc import Iterable

from caegraph.core.field import FieldData

__all__ = ["Snapshot"]


class Snapshot:
    """Instantaneous physical state organization construct (ADR-023 D-01).

    A :class:`Snapshot` groups existing
    :class:`~caegraph.core.FieldData` realizations into one
    instantaneous physical state through explicit membership. It adds
    realization temporal organization semantics only — it is NOT a new
    physical-domain concept category (no ADR-018 / ADR-007 count
    increase) and carries no selection or projection responsibility
    (ADR-023 D-08).

    Membership is held here as the **authoritative non-owning**
    organization relation (ADR-023 D-03): a Snapshot associates
    ``0..*`` snapshot-scoped realizations, a snapshot-scoped
    realization belongs to exactly one Snapshot, and global/static
    realizations have no membership. Reverse access
    (FieldData -> Snapshot), if ever provided, must stay derived —
    no second independently-modifiable membership truth source may
    exist.

    Temporal coordinates are semantically distinct (ADR-023 D-02):
    ``physical_time`` is REQUIRED and unique within one temporal
    organization (the sole global-ordering coordinate; non-uniform
    spacing is legal), while ``solver_step`` is optional source
    provenance that never carries identity. Exact member forms are
    deferred (ADR-023 D-02); in particular the Python object identity
    of a Snapshot is an in-memory implementation detail, never a
    canonical or persistent identifier.

    A Snapshot is **immutable once atomically registered** on a
    :class:`~caegraph.core.CAEGraph`: temporal coordinates have no
    setters, and membership is attached exactly once by the
    registration boundary (:meth:`CAEGraph.register_snapshot`).
    Constructing a standalone Snapshot is legal but produces an
    unregistered (member-less) construct.

    Args:
        physical_time: Required physical time of the instantaneous
            state (``int`` or ``float``; bools rejected).
        solver_step: Optional solver / data-source step number
            (``int`` or ``float``; bools rejected).

    Raises:
        TypeError: If ``physical_time`` is missing or not a number,
            or ``solver_step`` is neither a number nor ``None``.

    Examples:
        >>> snapshot = Snapshot(physical_time=1.25)
        >>> snapshot.physical_time
        1.25
        >>> snapshot.solver_step is None
        True
        >>> snapshot.members
        ()
    """

    def __init__(
        self,
        *,
        physical_time: float,
        solver_step: float | None = None,
    ) -> None:
        """Initialize the temporal coordinates, then validate."""
        if not isinstance(physical_time, (int, float)) or isinstance(
            physical_time, bool
        ):
            raise TypeError("physical_time must be a number")
        if solver_step is not None and (
            not isinstance(solver_step, (int, float)) or isinstance(solver_step, bool)
        ):
            raise TypeError("solver_step must be a number or None")
        self._physical_time = physical_time
        self._solver_step = solver_step
        self._members: list[FieldData] = []
        self._sealed = False

    @property
    def physical_time(self) -> float:
        """Physical time of the instantaneous state (required, ADR-023 D-02)."""
        return self._physical_time

    @property
    def solver_step(self) -> float | None:
        """Optional solver / data-source step number (provenance only)."""
        return self._solver_step

    @property
    def members(self) -> tuple[FieldData, ...]:
        """Authoritative non-owning membership, read-only view (ADR-023 D-03)."""
        return tuple(self._members)

    def _seal(self, members: Iterable[FieldData]) -> None:
        """Attach the authoritative membership exactly once (CAEGraph-authorized).

        Internal construction path: :meth:`CAEGraph.register_snapshot`
        is the only authorized caller — it performs the full
        consistency validation first and then seals the membership
        atomically. A second call fails: this private entry must never
        become a second membership mutation path (ADR-023 D-03/D-04).
        """
        if self._sealed:
            raise RuntimeError(
                "Snapshot membership is sealed at atomic registration "
                "and cannot be mutated (ADR-023)"
            )
        self._members.extend(members)
        self._sealed = True
