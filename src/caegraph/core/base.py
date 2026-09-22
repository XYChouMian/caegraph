"""Base abstraction for CAEGraph engineering domain-truth objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

__all__ = ["BaseObject"]


class BaseObject(ABC):
    """Shared base for framework-independent domain-truth objects.

    Provides identity (a non-empty name), free-form metadata and a
    fail-fast validation contract. Subclasses implement
    :meth:`validate`; it runs automatically at construction time and
    after every metadata update (atomically — a failed update rolls
    the whole batch back and leaves the object unchanged), and can be
    re-invoked explicitly to re-check mutated state.

    Learning-layer classes (``Graph``, ``CAEDataset``, ``Model``)
    intentionally do *not* inherit from :class:`BaseObject`; they use
    their ecosystem-native bases and follow their own protocols
    (ADR-009).

    Examples:
        >>> class Sensor(BaseObject):
        ...     def validate(self) -> None:
        ...         if self.metadata.get("gain", 1.0) < 0:
        ...             raise ValueError("gain must be non-negative")
        >>> sensor = Sensor("pressure_probe", {"gain": 2.0})
        >>> sensor.name
        'pressure_probe'

    """

    def __init__(self, name: str, metadata: Mapping[str, Any] | None = None) -> None:
        """Initialize identity and metadata, then validate.

        Args:
            name: Non-empty human-readable identity of the object.
            metadata: Optional free-form key/value annotations. The
                mapping is copied; later mutations of the source do not
                affect the object.

        Raises:
            ValueError: If ``name`` is not a non-empty string or the
                initial state fails :meth:`validate`.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        self._name = name
        self._metadata: dict[str, Any] = dict(metadata) if metadata is not None else {}
        self.validate()

    @property
    def name(self) -> str:
        """Identity of the object."""
        return self._name

    @property
    def metadata(self) -> dict[str, Any]:
        """A defensive copy of the object metadata."""
        return dict(self._metadata)

    def update_metadata(self, **values: Any) -> None:
        """Merge ``values`` into the metadata and re-validate atomically.

        The candidate mapping is staged on a fresh dict first; when
        validation fails, the previous metadata is restored
        (fail-clean, not only fail-loud) and the original validation
        error is re-raised unchanged — the whole batch rolls back,
        including entries that would have been legal on their own.

        Args:
            **values: Metadata entries to set or overwrite.

        Raises:
            Exception: Whatever :meth:`on_metadata_changed` (by
                default :meth:`validate`) raises, propagated
                unchanged after rollback.
        """
        # never mutated: candidates are fresh dicts (ARCHITECTURE.md §3.4)
        old_metadata = self._metadata
        self._metadata = {**old_metadata, **values}
        try:
            self.on_metadata_changed()
        except Exception:
            self._metadata = old_metadata
            raise

    def on_metadata_changed(self) -> None:
        """Re-validate after a metadata change.

        Extension point for subclasses: the default implementation
        runs the full :meth:`validate` check (backward compatible);
        subclasses that intentionally assign semantic meaning to
        specific metadata keys (or have expensive state checks) may
        override it for targeted re-validation.
        Precision triggering is deliberately deferred until the first
        metadata-carrying subclass exists.
        """
        self.validate()

    @abstractmethod
    def validate(self) -> None:
        """Raise if the object is in an invalid state.

        Subclasses must implement this as a pure check: it raises on
        invalid state and returns ``None`` otherwise. It is invoked at
        construction time and after every metadata update (fail-fast
        contract).
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self._name!r})"
