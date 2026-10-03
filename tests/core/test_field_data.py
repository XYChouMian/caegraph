"""Tests for caegraph.core.field.FieldData (realization data, ADR-020 D2)."""

from __future__ import annotations

import pytest

from caegraph.core import Field, FieldData


def _declaration() -> Field:
    return Field("pressure", unit="Pa", association="node")


def test_construction_stores_payload_and_reference():
    field = _declaration()
    data = FieldData(field, [0.1, 0.2], timestep=3)
    assert data.field is field
    assert data.values == [0.1, 0.2]
    assert data.timestep == 3


def test_optional_slots_default_to_none():
    data = FieldData(_declaration(), [1.0])
    assert data.timestep is None
    assert data.metadata == {}


def test_values_none_payload_is_rejected():
    with pytest.raises(ValueError, match="values are required"):
        FieldData(_declaration(), None)  # type: ignore[arg-type]


def test_missing_values_argument_is_a_signature_error():
    # The values parameter has no default: omitting it is Python's own
    # TypeError; only explicit illegal payloads get custom validation.
    with pytest.raises(TypeError):
        FieldData(_declaration())  # type: ignore[call-arg]


def test_non_field_reference_is_rejected():
    with pytest.raises(TypeError, match="Field"):
        FieldData("pressure", [1.0])  # type: ignore[arg-type]


def test_non_numeric_timestep_is_rejected():
    with pytest.raises(TypeError, match="number"):
        FieldData(_declaration(), [1.0], timestep="t0")  # type: ignore[arg-type]


def test_bool_timestep_is_rejected():
    with pytest.raises(TypeError, match="number"):
        FieldData(_declaration(), [1.0], timestep=True)  # type: ignore[arg-type]


def test_int_timestep_is_accepted():
    data = FieldData(_declaration(), [1.0], timestep=2)
    assert data.timestep == 2


def test_metadata_is_carried_through():
    data = FieldData(_declaration(), [1.0], metadata={"source": "probe"})
    assert data.metadata == {"source": "probe"}


def test_semantics_resolve_through_the_field_reference():
    # ADR-020 D3 usage contract: consumers resolve name/unit/association
    # semantics through the referenced declaration (Markdown-frozen
    # semantics; deliberately not an attribute-absence invariant).
    data = FieldData(_declaration(), [1.0])
    assert data.field.name == "pressure"
    assert data.field.unit == "Pa"
    assert data.field.association == "node"
