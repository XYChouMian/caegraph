"""Tests for caegraph.core.boundary.spec.BoundarySpec slot coherence (ADR-011)."""

from __future__ import annotations

import pytest

from caegraph.core import BoundarySpec, BoundaryType

CONSTRAINT_VALUED = (BoundaryType.DIRICHLET, BoundaryType.NEUMANN, BoundaryType.ROBIN)
PAIRING_TYPES = (BoundaryType.PERIODIC, BoundaryType.INTERFACE)
VALUELESS = (BoundaryType.SYMMETRY, BoundaryType.INTERFACE, BoundaryType.NONE)


def test_minimal_declaration_for_every_type():
    for boundary_type in BoundaryType:
        if boundary_type is BoundaryType.PERIODIC:
            spec = BoundarySpec("r", boundary_type, paired_region="r2")
        else:
            spec = BoundarySpec("r", boundary_type)
        assert spec.region == "r"
        assert spec.boundary_type is boundary_type


@pytest.mark.parametrize("boundary_type", CONSTRAINT_VALUED)
def test_value_slots_accepted_for_constraint_valued_types(boundary_type):
    spec = BoundarySpec(
        "r",
        boundary_type,
        value=1.5,
        weight=0.5,
        time_dependent=True,
        space_dependent=True,
    )
    assert spec.value == 1.5
    assert spec.weight == 0.5
    assert spec.time_dependent is True
    assert spec.space_dependent is True


@pytest.mark.parametrize("boundary_type", VALUELESS)
@pytest.mark.parametrize(
    "slots",
    [
        {"value": 1.0},
        {"weight": 0.5},
        {"time_dependent": True},
        {"space_dependent": True},
    ],
)
def test_value_slots_rejected_for_valueless_types(boundary_type, slots):
    with pytest.raises(ValueError, match="constraint-valued"):
        BoundarySpec("r", boundary_type, **slots)


def test_periodic_requires_paired_region():
    with pytest.raises(ValueError, match="PERIODIC requires a paired_region"):
        BoundarySpec("r", BoundaryType.PERIODIC)


def test_periodic_paired_region_must_differ_from_region():
    with pytest.raises(ValueError, match="must differ"):
        BoundarySpec("r", BoundaryType.PERIODIC, paired_region="r")


def test_interface_accepts_optional_paired_region():
    spec = BoundarySpec(
        "left_domain", BoundaryType.INTERFACE, paired_region="right_domain"
    )
    assert spec.paired_region == "right_domain"


def test_interface_paired_region_must_differ_from_region():
    with pytest.raises(ValueError, match="must differ"):
        BoundarySpec("r", BoundaryType.INTERFACE, paired_region="r")


def test_constraint_valued_types_forbid_paired_region():
    with pytest.raises(ValueError, match="reserved for PERIODIC"):
        BoundarySpec("r", BoundaryType.DIRICHLET, paired_region="r2")


@pytest.mark.parametrize(
    "boundary_type",
    [
        BoundaryType.DIRICHLET,
        BoundaryType.NEUMANN,
        BoundaryType.SYMMETRY,
        BoundaryType.NONE,
    ],
)
def test_parameters_are_reserved_for_robin(boundary_type):
    with pytest.raises(ValueError, match="reserved for ROBIN"):
        BoundarySpec("r", boundary_type, parameters={"a": 1.0})


def test_robin_accepts_coefficient_parameters():
    spec = BoundarySpec(
        "r",
        BoundaryType.ROBIN,
        value=2.0,
        parameters={"a": 0.5, "b": 1.5},
    )
    assert spec.parameters == {"a": 0.5, "b": 1.5}


def test_robin_without_parameters_is_valid():
    spec = BoundarySpec("r", BoundaryType.ROBIN)
    assert spec.parameters is None


def test_empty_parameters_are_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        BoundarySpec("r", BoundaryType.ROBIN, parameters={})


def test_non_numeric_coefficient_is_rejected():
    with pytest.raises(TypeError, match="numbers"):
        BoundarySpec("r", BoundaryType.ROBIN, parameters={"a": "fast"})  # type: ignore[dict-item]


def test_empty_region_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        BoundarySpec("  ", BoundaryType.DIRICHLET)


def test_boundary_type_must_be_the_enum():
    with pytest.raises(TypeError, match="BoundaryType"):
        BoundarySpec("r", "dirichlet")  # type: ignore[arg-type]


def test_non_numeric_value_is_rejected():
    with pytest.raises(TypeError, match="number"):
        BoundarySpec("r", BoundaryType.DIRICHLET, value="high")  # type: ignore[arg-type]


def test_non_bool_dependence_flag_is_rejected():
    with pytest.raises(TypeError, match="bools"):
        BoundarySpec("r", BoundaryType.DIRICHLET, time_dependent="yes")  # type: ignore[arg-type]


def test_blank_paired_region_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        BoundarySpec("r", BoundaryType.PERIODIC, paired_region="   ")


def test_targets_start_unresolved():
    spec = BoundarySpec("r", BoundaryType.DIRICHLET)
    assert spec.target is None
    assert spec.paired_target is None


def test_parameters_are_defensively_copied():
    source = {"a": 1.0}
    spec = BoundarySpec("r", BoundaryType.ROBIN, parameters=source)
    snapshot = spec.parameters
    snapshot["a"] = 99.0
    assert spec.parameters == {"a": 1.0}


def test_repr_shows_region_and_type():
    spec = BoundarySpec("r", BoundaryType.DIRICHLET)
    assert (
        repr(spec)
        == "BoundarySpec(region='r', boundary_type=<BoundaryType.DIRICHLET: 'dirichlet'>)"
    )
