"""Cell type vocabulary for the canonical mesh topology (ADR-014).

:class:`CellType` is the closed vocabulary of supported linear element
types of the canonical :class:`~caegraph.core.Mesh`. Each member carries
three per-type facts the whole topology layer builds on:

- an **explicit, stable integer code** used as the internal storage
  identity (e.g. in the ``cell_types`` array). The mapping is declared
  explicitly below and must never be derived from the enum declaration
  order — reordering the members must not change any code;
- the topological **dimension** of the element;
- the **codim-1 face templates** (the boundary entities of the element),
  shared by ``Mesh.validate`` (facet-cell consistency, ADR-014 8a) and
  the geometry layer.

Values are lowercase strings (str-Enum, same style as
:class:`~caegraph.core.BoundaryType`) so the serialization face is
stable, lowercase and format-independent. Higher-order elements
(TRI6/TET10/...) and ``POINT`` are recorded as future extensions and are
deliberately absent here.
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

    Local-node conventions follow the meshio/VTK linear ordering, which
    the IO adapters normalize *into*; this convention table is the
    CAEGraph-owned reference and freezes with this implementation:

    =========  ====  =====  =========================================
    member     dim   nodes  local-node convention (0-based)
    =========  ====  =====  =========================================
    LINE2      1     2      segment a-b
    TRI3       2     3      CCW triangle a-b-c
    QUAD4      2     4      CCW quad a-b-c-d
    TET4       3     4      tetra a-b-c-d
    PYR5       3     5      quad base a-b-c-d + apex e
    WEDGE6     3     6      bottom triangle a-b-c + top d-e-f
    HEX8       3     8      VTK hex ordering 0..7
    =========  ====  =====  =========================================

    ``faces`` are the codim-1 face templates given as tuples of local
    node indices. Node order inside a template is not normative —
    facet-cell matching compares node *sets* because facet connectivity
    is winding-free (ADR-014 decision 3).
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
        """Codim-1 face templates as tuples of local node indices."""
        return _CELL_SPECS[self].faces

    @classmethod
    def from_code(cls, code: int) -> CellType:
        """Return the member with the given explicit integer ``code``.

        Raises:
            ValueError: if ``code`` is not a registered cell code.
        """
        for member in cls:
            if member.code == code:
                return member
        raise ValueError(f"unknown CellType code: {code!r}")


# Explicit, stable per-type facts (ADR-014). The integer codes are
# declared here on purpose: they must never be renumbered implicitly by
# reordering the enum members above.
_CELL_SPECS: dict[CellType, _CellSpec] = {
    CellType.LINE2: _CellSpec(code=1, dim=1, node_count=2, faces=()),
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
