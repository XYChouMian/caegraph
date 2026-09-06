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
    after every metadata update, and can be re-invoked explicitly to
    re-check mutated state.

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
        """Merge ``values`` into the metadata and re-validate.

        Args:
            **values: Metadata entries to set or overwrite.

        Raises:
            ValueError: If the resulting state fails :meth:`validate`.
        """
        self._metadata.update(values)
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
