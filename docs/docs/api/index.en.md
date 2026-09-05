# API Reference

CAEGraph is in Phase 1 (Core Data Structures): `caegraph.core` provides
`BaseObject`, `Registry`, and the shared enums `BoundaryType` /
`NodeCategory`; `caegraph.utils` provides `get_logger`. `Mesh`, `Field`, and
the data band land in Phase 2.

API documentation is generated automatically from docstrings via
[mkdocstrings](https://mkdocstrings.github.io/):

::: caegraph
    options:
      show_source: false
      heading_level: 3

Top-level modules (see the architecture specification):

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
