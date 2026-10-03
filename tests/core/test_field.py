"""Tests for caegraph.core.field.Field (declaration, ADR-020 D1)."""

from __future__ import annotations

import pytest

from caegraph.core import Field


def test_construction_stores_declaration_semantics():
    field = Field("pressure", unit="Pa", association="node")
    assert field.name == "pressure"
    assert field.unit == "Pa"
    assert field.association == "node"


def test_optional_slots_default_to_none():
    field = Field("velocity_x")
    assert field.unit is None
    assert field.association is None


def test_field_carries_no_values_or_timestep_members():
    # ADR-020 D1: Field is a stable declaration — values and timestep
    # belong to FieldData realizations. Both the attribute surface and
    # the constructor signature must reject the retired payload slots
    # (invariant registry ADR-020-D1-01).
    field = Field("pressure", unit="Pa", association="node")
    assert not hasattr(field, "values")
    assert not hasattr(field, "timestep")
    with pytest.raises(TypeError):
        Field("pressure", [0.1, 0.2])  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        Field("pressure", timestep=3)  # type: ignore[call-arg]


def test_empty_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        Field("  ")


def test_blank_unit_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", unit="   ")


def test_non_string_unit_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", unit=5)  # type: ignore[arg-type]


def test_blank_association_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", association="")


def test_metadata_is_carried_through():
    field = Field("pressure", metadata={"source": "probe"})
    assert field.metadata == {"source": "probe"}
