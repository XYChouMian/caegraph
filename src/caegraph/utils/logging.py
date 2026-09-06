"""Framework-wide logging helpers."""

from __future__ import annotations

import logging

__all__ = ["get_logger"]

_ROOT = "caegraph"

_ROOT_LOGGER = logging.getLogger(_ROOT)
if not any(
    isinstance(handler, logging.NullHandler) for handler in _ROOT_LOGGER.handlers
):
    _ROOT_LOGGER.addHandler(logging.NullHandler())


def get_logger(name: str) -> logging.Logger:
    """Return a logger in the ``caegraph`` namespace.

    Library modules log through this helper so that CAEGraph emits no
    handlers of its own (a :class:`~logging.NullHandler` guards the
    namespace root) and applications keep full logging control.

    Args:
        name: Module or component name. Names already under
            ``caegraph`` (including ``"caegraph"`` itself) are used
            verbatim; any other name is placed under ``caegraph.``.

    Returns:
        The requested :class:`logging.Logger`.

    Raises:
        ValueError: If ``name`` is empty or not a string.

    Examples:
        >>> logger = get_logger("core.base")
        >>> logger.name
        'caegraph.core.base'

    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("logger name must be a non-empty string")
    if name == _ROOT or name.startswith(_ROOT + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_ROOT}.{name}")
