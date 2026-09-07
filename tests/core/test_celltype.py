"""Tests for caegraph.core.celltype vocabulary (ADR-014)."""

from __future__ import annotations

import pytest

from caegraph.core import CellType


def test_members_values_and_uniqueness():
    expected = {
        "LINE2": "line2",
        "TRI3": "tri3",
        "QUAD4": "quad4",
        "TET4": "tet4",
        "PYR5": "pyr5",
        "WEDGE6": "wedge6",
        "HEX8": "hex8",
    }
    for member, value in expected.items():
        assert CellType[member].value == value
    assert len(CellType) == len(expected)


def test_members_are_serializable_lowercase_strings():
    for member in CellType:
        assert isinstance(member.value, str)
        assert member == member.value
        assert member.value == member.value.lower()


def test_by_value_lookup():
    assert CellType("tri3") is CellType.TRI3


def test_invalid_value_fails():
    with pytest.raises(ValueError):
        CellType("hexahedron")


def test_explicit_stable_integer_codes():
    expected_codes = {
        CellType.LINE2: 1,
        CellType.TRI3: 2,
        CellType.QUAD4: 3,
        CellType.TET4: 4,
        CellType.PYR5: 5,
        CellType.WEDGE6: 6,
        CellType.HEX8: 7,
    }
    # The mapping is declared explicitly and must not drift: reordering
    # the enum members must never renumber the codes (ADR-014 decision 4).
    assert {member.code for member in CellType} == set(expected_codes.values())
    for member, code in expected_codes.items():
        assert member.code == code


def test_from_code_roundtrip():
    for member in CellType:
        assert CellType.from_code(member.code) is member


def test_from_code_unknown_fails():
    with pytest.raises(ValueError):
        CellType.from_code(0)
    with pytest.raises(ValueError):
        CellType.from_code(99)


def test_dim_and_node_count():
    expected = {
        CellType.LINE2: (1, 2),
        CellType.TRI3: (2, 3),
        CellType.QUAD4: (2, 4),
        CellType.TET4: (3, 4),
        CellType.PYR5: (3, 5),
        CellType.WEDGE6: (3, 6),
        CellType.HEX8: (3, 8),
    }
    for member, (dim, node_count) in expected.items():
        assert member.dim == dim
        assert member.node_count == node_count


def test_codim1_face_templates_present_and_valid():
    for member in CellType:
        faces = member.faces
        for face in faces:
            # face nodes are a subset of the element's local nodes
            assert len(face) > 0
            assert all(0 <= n < member.node_count for n in face)
            assert len(set(face)) == len(face)
            # face size matches a codim-1 entity (edge or surface)
            if member.dim == 2:
                assert len(face) == 2
            else:
                assert len(face) in (3, 4)


def test_codim1_face_counts_and_sets():
    expected = {
        CellType.LINE2: (),
        CellType.TRI3: ((0, 1), (1, 2), (2, 0)),
        CellType.QUAD4: ((0, 1), (1, 2), (2, 3), (3, 0)),
        CellType.TET4: ((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2)),
        CellType.PYR5: ((0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)),
        CellType.WEDGE6: (
            (0, 1, 2),
            (3, 4, 5),
            (0, 1, 4, 3),
            (1, 2, 5, 4),
            (2, 0, 3, 5),
        ),
        CellType.HEX8: (
            (0, 3, 2, 1),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        ),
    }
    for member, faces in expected.items():
        assert member.faces == faces


def test_future_extensions_absent():
    # Higher-order elements and POINT are recorded future extensions.
    for name in ("POINT", "TRI6", "QUAD8", "TET10"):
        assert not hasattr(CellType, name)
