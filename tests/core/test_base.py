"""Tests for caegraph.core.base.BaseObject."""

from __future__ import annotations

import pytest

from caegraph.core import BaseObject


class _Probe(BaseObject):
    """Minimal concrete probe: valid unless metadata marks it broken."""

    def validate(self) -> None:
        if self.metadata.get("broken"):
            raise ValueError("probe is broken")


class _ConstrainedProbe(BaseObject):
    """Probe assigning domain semantics to metadata keys.

    Rejects ``broken`` metadata at construction (full validate) and
    on updates by overriding the ``on_metadata_changed`` mutation
    hook — the canonical pattern for classes with metadata
    constraints (ARCHITECTURE.md §3.4).
    """

    def validate(self) -> None:
        if self.metadata.get("broken"):
            raise ValueError("probe is broken")

    def on_metadata_changed(self) -> None:
        self.validate()


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


def test_update_metadata_default_performs_no_validation():
    # default lifecycle: metadata is an annotation channel — updating
    # it performs no validation, even when validate() would reject
    # the resulting metadata (opt-in happens via hook override)
    probe = _Probe("p")
    probe.update_metadata(broken=True)
    assert probe.metadata == {"broken": True}


def test_constrained_probe_construction_still_validates_metadata():
    # construction keeps the full consistency check: an invalid
    # initial metadata fails at birth even for the default probe
    with pytest.raises(ValueError, match="probe is broken"):
        _ConstrainedProbe("p", {"broken": True})


def test_update_metadata_keeps_previous_entries():
    probe = _Probe("p", {"a": 1})
    probe.update_metadata(b=2)
    assert probe.metadata == {"a": 1, "b": 2}


def test_update_metadata_failure_reraises_original_exception():
    # spec 1 (constrained probe): the hook's error propagates
    # unchanged — same type and message, never swallowed or wrapped
    with pytest.raises(ValueError, match="probe is broken"):
        _ConstrainedProbe("p").update_metadata(broken=True)


def test_update_metadata_failure_rolls_back_whole_batch():
    # spec 2 (constrained probe): a mixed batch (legal entries + a
    # failing trigger) rolls back entirely — legal values do not
    # survive a failed update
    probe = _ConstrainedProbe("p", {"a": 1})
    with pytest.raises(ValueError, match="probe is broken"):
        probe.update_metadata(a=2, b=3, broken=True)
    assert probe.metadata == {"a": 1}


def test_update_metadata_failure_restores_previous_metadata():
    # spec 3 (constrained probe): after a failed update the metadata
    # is restored to the pre-call state (public property assertion)
    probe = _ConstrainedProbe("p", {"a": 1, "b": 2})
    with pytest.raises(ValueError, match="probe is broken"):
        probe.update_metadata(broken=True)
    assert probe.metadata == {"a": 1, "b": 2}


def test_repr_shows_class_and_name():
    probe = _Probe("pressure")
    assert repr(probe) == "_Probe(name='pressure')"
