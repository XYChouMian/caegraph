"""Tests for caegraph.core.base.BaseObject."""

from __future__ import annotations

import pytest

from caegraph.core import BaseObject


class _Probe(BaseObject):
    """Minimal concrete probe: valid unless metadata marks it broken."""

    def validate(self) -> None:
        if self.metadata.get("broken"):
            raise ValueError("probe is broken")


def test_construction_runs_validation_and_fails_fast():
    with pytest.raises(ValueError, match="probe is broken"):
        _Probe("bad", {"broken": True})


def test_empty_name_is_rejected():
    for bad in ("", "   "):
        with pytest.raises(ValueError, match="non-empty"):
            _Probe(bad)


def test_non_string_name_is_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        _Probe(42)  # type: ignore[arg-type]


def test_metadata_is_defensively_copied_on_read():
    probe = _Probe("p", {"a": 1})
    snapshot = probe.metadata
    snapshot["a"] = 999
    assert probe.metadata == {"a": 1}


def test_metadata_is_defensively_copied_on_init():
    source: dict[str, int] = {"a": 1}
    probe = _Probe("p", source)
    source["a"] = 999
    assert probe.metadata == {"a": 1}


def test_update_metadata_reruns_validation():
    probe = _Probe("p")
    with pytest.raises(ValueError, match="probe is broken"):
        probe.update_metadata(broken=True)


def test_update_metadata_keeps_previous_entries():
    probe = _Probe("p", {"a": 1})
    probe.update_metadata(b=2)
    assert probe.metadata == {"a": 1, "b": 2}


def test_repr_shows_class_and_name():
    probe = _Probe("pressure")
    assert repr(probe) == "_Probe(name='pressure')"
