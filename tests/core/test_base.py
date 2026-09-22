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


def test_update_metadata_failure_reraises_original_exception():
    # spec 1: the validation error propagates unchanged — the same
    # type and message validate() raised, never swallowed or wrapped
    with pytest.raises(ValueError, match="probe is broken"):
        _Probe("p").update_metadata(broken=True)


def test_update_metadata_failure_rolls_back_whole_batch():
    # spec 2: a mixed batch (legal entries + a failing trigger) rolls
    # back entirely — legal values do not survive a failed update
    probe = _Probe("p", {"a": 1})
    with pytest.raises(ValueError, match="probe is broken"):
        probe.update_metadata(a=2, b=3, broken=True)
    assert probe.metadata == {"a": 1}


def test_update_metadata_failure_restores_previous_metadata():
    # spec 3: after a failed update the metadata is restored to the
    # pre-call state (asserted via the public metadata property)
    probe = _Probe("p", {"a": 1, "b": 2})
    with pytest.raises(ValueError, match="probe is broken"):
        probe.update_metadata(broken=True)
    assert probe.metadata == {"a": 1, "b": 2}


def test_repr_shows_class_and_name():
    probe = _Probe("pressure")
    assert repr(probe) == "_Probe(name='pressure')"
