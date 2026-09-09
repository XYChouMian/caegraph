"""Tests for caegraph.core.field.Field."""

from __future__ import annotations

import pytest

from caegraph.core import Field


def test_construction_stores_payload_and_semantics():
    field = Field("pressure", [0.1, 0.2], unit="Pa", timestep=3, association="node")
    assert field.name == "pressure"
    assert field.values == [0.1, 0.2]
    assert field.unit == "Pa"
    assert field.timestep == 3
    assert field.association == "node"


def test_optional_slots_default_to_none():
    field = Field("velocity_x", [1.0])
    assert field.unit is None
    assert field.timestep is None
    assert field.association is None


def test_values_are_required():
    with pytest.raises(ValueError, match="values are required"):
        Field("pressure", None)  # type: ignore[arg-type]


def test_empty_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        Field("  ", [1.0])


def test_blank_unit_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", [1.0], unit="   ")


def test_non_string_unit_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", [1.0], unit=5)  # type: ignore[arg-type]


def test_non_numeric_timestep_is_rejected():
    with pytest.raises(TypeError, match="number"):
        Field("pressure", [1.0], timestep="t0")  # type: ignore[arg-type]


def test_bool_timestep_is_rejected():
    with pytest.raises(TypeError, match="number"):
        Field("pressure", [1.0], timestep=True)  # type: ignore[arg-type]


def test_blank_association_is_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        Field("pressure", [1.0], association="")


def test_int_timestep_is_accepted():
    field = Field("pressure", [1.0], timestep=2)
    assert field.timestep == 2


def test_metadata_is_carried_through():
    field = Field("pressure", [1.0], metadata={"source": "probe"})
    assert field.metadata == {"source": "probe"}
