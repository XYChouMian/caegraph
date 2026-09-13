"""Cell type vocabulary for the canonical mesh topology (ADR-014).

:class:`CellType` is the *current canonical vocabulary* of supported
linear element types of the canonical :class:`~caegraph.core.Mesh`.
Each member carries three per-type facts the whole topology layer
builds on:

- an **explicit, stable integer code** used as the internal storage
  identity (e.g. in the ``cell_types`` array). The mapping is declared
  explicitly below and must never be derived from the enum declaration
  order — reordering the members must not change any code;
- the topological **dimension** of the element;
- the **codim-1 face templates** (the boundary entities of the
  element), shared by ``Mesh.validate`` (facet-cell consistency,
  ADR-014 8a) and the geometry layer.

Values are lowercase strings (str-Enum, same style as
:class:`~caegraph.core.BoundaryType`) so the serialization face is
stable, lowercase and format-independent. The set is the vocabulary
supported by the current canonical topology contract; further linear
and higher-order elements (POINT, TRI6, TET10, ...) are recorded
future extensions and are deliberately absent here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique

__all__ = ["CellType"]


@dataclass(frozen=True)
class _CellSpec:
    """Frozen per-type facts of a :class:`CellType` (ADR-014)."""

    code: int
    dim: int
    node_count: int
    faces: tuple[tuple[int, ...], ...]


@unique
class CellType(str, Enum):
    """Linear cell types of the canonical Mesh (ADR-014 decision 4).

    Local-node conventions are **CAEGraph-owned**: the numbering of the
    reference element is defined by this table and freezes with this
    implementation. IO adapters normalize each external source ordering
    into this convention before constructing canonical Mesh objects;
    no backend-specific numbering (meshio, VTK, Abaqus, Gmsh, ...) is
    referenced here and none may leak into core.

    =========  ====  =====  =========================================
    member     dim   nodes  local-node convention (0-based)
    =========  ====  =====  =========================================
    LINE2      1     2      segment a-b
    TRI3       2     3      triangle a-b-c
    QUAD4      2     4      quad a-b-c-d
    TET4       3     4      tetra a-b-c-d
    PYR5       3     5      quad base a-b-c-d + apex e
    WEDGE6     3     6      bottom triangle a-b-c + top d-e-f
    HEX8       3     8      CAEGraph reference hexahedron node
                            convention (see face templates below)
    =========  ====  =====  =========================================

    ``faces`` are the codim-1 face membership templates, one tuple of
    local node indices per face. They define *membership* (which nodes
    form a face); their internal ordering is a deterministic CAEGraph
    convention and must **not** be interpreted as an intrinsic facet
    normal orientation (facet connectivity is winding-free and normals
    are always cell-relative, ADR-014 decision 3). Facet-cell matching
    therefore compares node sets. Face template ordering exists only
    for deterministic topology operations; normal orientation is
    computed from adjacent cell context.
    """

    LINE2 = "line2"
    TRI3 = "tri3"
    QUAD4 = "quad4"
    TET4 = "tet4"
    PYR5 = "pyr5"
    WEDGE6 = "wedge6"
    HEX8 = "hex8"

    @property
    def code(self) -> int:
        """Explicit, stable integer code (internal storage identity)."""
        return _CELL_SPECS[self].code

    @property
    def dim(self) -> int:
        """Topological dimension of the element."""
        return _CELL_SPECS[self].dim

    @property
    def node_count(self) -> int:
        """Number of corner nodes of the element."""
        return _CELL_SPECS[self].node_count

    @property
    def faces(self) -> tuple[tuple[int, ...], ...]:
        """Codim-1 face membership templates as tuples of local indices."""
        return _CELL_SPECS[self].faces

    @classmethod
    def from_code(cls, code: int) -> CellType:
        """Return the member with the given explicit integer ``code``.

        Raises:
            ValueError: if ``code`` is not a registered cell code.
        """
        try:
            return _CODE_TO_CELLTYPE[code]
        except KeyError:
            raise ValueError(f"unknown CellType code: {code!r}") from None


# Explicit, stable per-type facts (ADR-014). The integer codes are
# declared here on purpose: they must never be renumbered implicitly by
# reordering the enum members above.
_CELL_SPECS: dict[CellType, _CellSpec] = {
    CellType.LINE2: _CellSpec(
        code=1,
        dim=1,
        node_count=2,
        # Point (dim 0) facets are not represented in the current
        # canonical topology (facets are codim-1 only); POINT support
        # is a recorded future extension (ADR-014 decision 2/4).
        faces=(),
    ),
    CellType.TRI3: _CellSpec(
        code=2,
        dim=2,
        node_count=3,
        faces=((0, 1), (1, 2), (2, 0)),
    ),
    CellType.QUAD4: _CellSpec(
        code=3,
        dim=2,
        node_count=4,
        faces=((0, 1), (1, 2), (2, 3), (3, 0)),
    ),
    CellType.TET4: _CellSpec(
        code=4,
        dim=3,
        node_count=4,
        faces=((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2)),
    ),
    CellType.PYR5: _CellSpec(
        code=5,
        dim=3,
        node_count=5,
        faces=((0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)),
    ),
    CellType.WEDGE6: _CellSpec(
        code=6,
        dim=3,
        node_count=6,
        faces=((0, 1, 2), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)),
    ),
    CellType.HEX8: _CellSpec(
        code=7,
        dim=3,
        node_count=8,
        faces=(
            (0, 3, 2, 1),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        ),
    ),
}

# O(1) reverse lookup, single-sourced from the explicit spec table.
_CODE_TO_CELLTYPE: dict[int, CellType] = {
    spec.code: member for member, spec in _CELL_SPECS.items()
}
