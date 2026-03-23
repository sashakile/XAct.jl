"""Conformance tests for JuliaAdapter stub."""

import logging
from unittest.mock import MagicMock

import pytest

from sxact.adapter.julia_stub import JuliaAdapter


# Override the fixture so the conformance suite runs against JuliaAdapter
@pytest.fixture
def adapter_factory():
    return JuliaAdapter


# Pull in all conformance tests
from tests.test_adapter_conformance import *  # noqa: E402,F401,F403


# ---------------------------------------------------------------------------
# Regression: _execute_assert must not swallow Julia exceptions (sxAct-bko5)
# ---------------------------------------------------------------------------


class TestExecuteAssertExceptionDiagnostics:
    """When seval() throws during Assert, the error must be surfaced."""

    def _make_adapter_with_failing_seval(self, exc: Exception) -> JuliaAdapter:
        adapter = JuliaAdapter()
        jl = MagicMock()
        jl.seval.side_effect = exc
        adapter._jl = jl
        return adapter

    def test_exception_returns_error_status(self):
        adapter = self._make_adapter_with_failing_seval(RuntimeError("segfault"))
        result = adapter._execute_assert("TensorQ[x]", None)
        assert result.status == "error", (
            "Infrastructure exception must produce status='error', not 'ok'"
        )

    def test_exception_includes_error_message(self):
        adapter = self._make_adapter_with_failing_seval(
            TypeError("cannot convert JuliaObject")
        )
        result = adapter._execute_assert("TensorQ[x]", None)
        assert result.error is not None
        assert "cannot convert JuliaObject" in result.error

    def test_exception_preserved_in_diagnostics(self):
        adapter = self._make_adapter_with_failing_seval(MemoryError("out of memory"))
        result = adapter._execute_assert("big_expr === 0", None)
        assert "exception_type" in result.diagnostics
        assert result.diagnostics["exception_type"] == "MemoryError"

    def test_exception_logged_at_warning(self, caplog):
        adapter = self._make_adapter_with_failing_seval(RuntimeError("stack overflow"))
        with caplog.at_level(logging.WARNING):
            adapter._execute_assert("foo === bar", None)
        assert any("stack overflow" in r.message for r in caplog.records)

    def test_false_evaluation_still_returns_ok(self):
        """A legitimately false assertion must still return status='ok'."""
        adapter = JuliaAdapter()
        jl = MagicMock()
        jl.seval.return_value = False
        adapter._jl = jl
        result = adapter._execute_assert("1 == 2", None)
        assert result.status == "ok"
        assert result.repr == "False"
