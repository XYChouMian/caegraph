"""Tests for caegraph.utils.logging."""

from __future__ import annotations

import logging

import pytest

from caegraph.utils import get_logger


def test_component_name_is_namespaced_under_caegraph():
    assert get_logger("core.base").name == "caegraph.core.base"


def test_caegraph_prefixed_names_are_used_verbatim():
    assert get_logger("caegraph.io").name == "caegraph.io"
    assert get_logger("caegraph").name == "caegraph"


def test_same_name_returns_same_logger_object():
    assert get_logger("graph") is get_logger("graph")


def test_namespace_root_guards_with_null_handler():
    root = logging.getLogger("caegraph")
    assert any(isinstance(h, logging.NullHandler) for h in root.handlers)


def test_blank_name_is_rejected():
    for bad in ("", "   ", None):
        with pytest.raises(ValueError, match="non-empty"):
            get_logger(bad)  # type: ignore[arg-type]
