"""Name-keyed registry/factory mechanism for loaders and transforms."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

__all__ = ["Registry"]

T = TypeVar("T")


class Registry(Generic[T]):
    """Map string names to factories of one kind.

    A :class:`Registry` is the extension point where IO format readers
    (``caegraph.io``) and graph transforms (``caegraph.transforms``)
    plug in. Entries are classes or callables sharing a common result
    type ``T``. Registration accepts both a direct and a decorator
    form; duplicate names are rejected so that implicit shadowing can
    not happen.

    Args:
        kind: Human-readable label of the registered kind, used in
            error messages (for example ``"mesh loader"``).

    Examples:
        >>> loaders: Registry[object] = Registry("mesh loader")
        >>> @loaders.register("gmsh")
        ... class GmshLoader:
        ...     pass
        >>> loader = loaders.build("gmsh")
        >>> "gmsh" in loaders
        True

    """

    def __init__(self, kind: str) -> None:
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError("kind must be a non-empty string")
        self._kind = kind
        self._entries: dict[str, Callable[..., T]] = {}

    @property
    def kind(self) -> str:
        """Label of the registered kind."""
        return self._kind

    def register(
        self,
        name: str,
        factory: Callable[..., T] | None = None,
    ) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
        """Register ``factory`` under ``name``, directly or as decorator.

        Args:
            name: Unique registration key; duplicates are rejected.
            factory: The class or callable to register. When omitted,
                the call returns a decorator that registers its target.

        Returns:
            The registered factory itself, or a decorator when
            ``factory`` is omitted.

        Raises:
            ValueError: If ``name`` is empty or already registered.
            TypeError: If the target is not callable.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("registration name must be a non-empty string")

        def _register(target: Callable[..., T]) -> Callable[..., T]:
            if not callable(target):
                raise TypeError(f"{name!r} must map to a callable factory")
            if name in self._entries:
                raise ValueError(f"{self._kind} {name!r} is already registered")
            self._entries[name] = target
            return target

        if factory is None:
            return _register
        return _register(factory)

    def get(self, name: str) -> Callable[..., T]:
        """Return the factory registered under ``name``.

        Raises:
            KeyError: If ``name`` is unknown; the message lists all
                registered names of this registry.
        """
        if name not in self._entries:
            available = ", ".join(sorted(self._entries)) or "<none>"
            raise KeyError(f"unknown {self._kind} {name!r}; registered: {available}")
        return self._entries[name]

    def build(self, name: str, /, *args: object, **kwargs: object) -> T:
        """Instantiate the factory registered under ``name``.

        Args:
            name: Registration key.
            *args: Positional arguments forwarded to the factory.
            **kwargs: Keyword arguments forwarded to the factory.

        Returns:
            The constructed object.

        Raises:
            KeyError: If ``name`` is unknown.
        """
        factory = self.get(name)
        return factory(*args, **kwargs)

    def unregister(self, name: str) -> None:
        """Remove the entry registered under ``name``.

        Raises:
            KeyError: If ``name`` is unknown.
        """
        if name not in self._entries:
            raise KeyError(f"unknown {self._kind} {name!r}")
        del self._entries[name]

    def names(self) -> list[str]:
        """Return the sorted registration keys."""
        return sorted(self._entries)

    def __contains__(self, name: object) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(kind={self._kind!r}, n={len(self._entries)})"
