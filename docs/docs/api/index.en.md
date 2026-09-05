# API Reference

CAEGraph is in Phase 1 (Core Data Structures): `BaseObject`, registries, and
shared types are being implemented; the core public API is not yet available.

Once modules land, they will be documented here automatically via
[mkdocstrings](https://mkdocstrings.github.io/), e.g.:

::: caegraph
    options:
      show_source: false
      heading_level: 3

Planned top-level modules (see the architecture specification):

- `caegraph.core`
- `caegraph.geometry`
- `caegraph.io`
- `caegraph.graph`
- `caegraph.transforms`
- `caegraph.dataset`
- `caegraph.physics`
- `caegraph.models`
- `caegraph.assimilation`
- `caegraph.workflow`
- `caegraph.inference`
- `caegraph.visualization`
- `caegraph.utils`

Compatibility: the former empty `caegraph.data` namespace is temporarily
retained with a deprecation warning. New code should use the responsibility-
specific packages above. The compatibility namespace will not be removed
before version 0.3.0.
