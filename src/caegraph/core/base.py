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
    :meth:`validate` as a complete object consistency check; it runs
    automatically at construction time and can be re-invoked
    explicitly (debug, pre-serialization checks). Metadata updates
    are handled through the :meth:`on_metadata_changed` hook, whose
    default implementation performs no validation because metadata
    is annotation unless a subclass assigns semantic meaning to it;
    :meth:`update_metadata` is a transaction boundary — a failing
    hook rolls the whole batch back and leaves the object unchanged.

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
        """Merge ``values`` into the metadata atomically.

        The update is a transaction boundary: the candidate mapping
        is staged on a fresh dict, :meth:`on_metadata_changed` is
        invoked, and any exception it raises rolls the whole batch
        back (including entries that would have been legal on their
        own) before being re-raised unchanged. The rollback is a
        transaction guarantee independent of validation semantics —
        it applies no matter what the hook does (the default hook
        performs no validation).

        Args:
            **values: Metadata entries to set or overwrite.

        Raises:
            Exception: Whatever :meth:`on_metadata_changed` raises,
                propagated unchanged after rollback (none by default).
        """
        # never mutated: candidates are fresh dicts (ARCHITECTURE.md §3.4)
        old_metadata = self._metadata
        self._metadata = {**old_metadata, **values}
        try:
            self.on_metadata_changed()
        except Exception:
            self._metadata = old_metadata
            raise

    def on_metadata_changed(self) -> None:  # noqa: B027 — intentional no-op hook
        """React to a metadata change (mutation hook, not a validate alias).

        The default implementation performs no validation: metadata
        is an annotation channel, and changing annotations does not
        imply domain-state validation. Classes assigning domain
        semantics to metadata keys must override this hook and define
        their own re-validation strategy (which layers to re-run is
        the override's decision).
        """
        pass

    @abstractmethod
    def validate(self) -> None:
        """Raise if the object is in an invalid state.

        Subclasses must implement this as a pure check: it raises on
        invalid state and returns ``None`` otherwise. It is invoked at
        construction time and on explicit re-check (debug,
        pre-serialization); metadata updates are handled separately by
        the :meth:`on_metadata_changed` mutation hook (fail-fast
        contract).
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self._name!r})"
