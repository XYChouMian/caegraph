"""Compatibility namespace for the former CAEGraph data layer.

Use the responsibility-specific :mod:`caegraph.core`, :mod:`caegraph.io`,
:mod:`caegraph.graph`, :mod:`caegraph.transforms`, and
:mod:`caegraph.dataset` packages for new code. This empty namespace is kept
temporarily so existing ``import caegraph.data`` statements continue to work.
"""

from warnings import warn

warn(
    "caegraph.data is deprecated; import from the responsibility-specific "
    "caegraph.core, caegraph.io, caegraph.graph, caegraph.transforms, or "
    "caegraph.dataset package instead",
    DeprecationWarning,
    stacklevel=2,
)
