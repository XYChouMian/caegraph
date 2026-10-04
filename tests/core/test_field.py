"""Tests for caegraph.core.field.Field (declaration, ADR-020 D1)."""

from __future__ import annotations

import pytest

from caegraph.core import Field


def test_construction_stores_declaration_semantics():
    field = Field("pressure", unit="Pa", association="node")
    assert field.name == "pressure"
    assert field.unit == "Pa"
    assert field.association == "node"


def test_unit_defaults_to_none():
    field = Field("velocity_x", association="node")
    assert field.unit is None


def test_association_is_required():
    # ADR-021 D3: None is not a legal canonical Field state — the
    # declaration must carry a non-empty entity family. A missing
    # argument is Python's own signature TypeError; an explicit None
    # payload is an explicitly illegal value → ValueError (same
    # convention as FieldData.values; invariant registry
    # ADR-021-D03-01).
    with pytest.raises(TypeError):
        Field("pressure")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", association=None)  # type: ignore[arg-type]


def test_non_string_association_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", association=5)  # type: ignore[arg-type]


def test_field_carries_no_values_or_timestep_members():
    # ADR-020 D1: Field is a stable declaration — values and timestep
    # belong to FieldData realizations. Both the attribute surface and
    # the constructor signature must reject the retired payload slots
    # (invariant registry ADR-020-D1-01).
    field = Field("pressure", unit="Pa", association="node")
    assert not hasattr(field, "values")
    assert not hasattr(field, "timestep")
    with pytest.raises(TypeError):
        Field("pressure", [0.1, 0.2], association="node")  # type: ignore[misc]
    with pytest.raises(TypeError):
        Field("pressure", association="node", timestep=3)  # type: ignore[call-arg]


def test_empty_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        Field("  ", association="node")


def test_blank_unit_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", association="node", unit="   ")


def test_non_string_unit_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", association="node", unit=5)  # type: ignore[arg-type]


def test_blank_association_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", association="")


def test_metadata_is_carried_through():
    field = Field("pressure", association="node", metadata={"source": "probe"})
    assert field.metadata == {"source": "probe"}
