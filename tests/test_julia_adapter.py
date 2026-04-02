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
from tests.test_adapter_conformance import *  # noqa: E402, F403

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
        adapter = self._make_adapter_with_failing_seval(TypeError("cannot convert JuliaObject"))
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


# ---------------------------------------------------------------------------
# _top_level_split string literal handling (sxAct-fcfq)
# ---------------------------------------------------------------------------


class TestTopLevelSplit:
    """_top_level_split must skip separators inside brackets and strings."""

    def test_basic_split(self):
        from sxact.translate.wl_to_julia import top_level_split as _top_level_split

        assert _top_level_split("a === b", " === ") == ["a", "b"]

    def test_brackets_prevent_split(self):
        from sxact.translate.wl_to_julia import top_level_split as _top_level_split

        result = _top_level_split("f(a === b) === c", " === ")
        assert result == ["f(a === b)", "c"]

    def test_string_literal_prevents_split(self):
        from sxact.translate.wl_to_julia import top_level_split as _top_level_split

        # Separator inside quotes should NOT trigger a split
        result = _top_level_split('"a === b" === "c"', " === ")
        assert len(result) == 2
        assert result[0] == '"a === b"'
        assert result[1] == '"c"'

    def test_no_sep_returns_whole(self):
        from sxact.translate.wl_to_julia import top_level_split as _top_level_split

        assert _top_level_split("no separator here", " === ") == ["no separator here"]


# ---------------------------------------------------------------------------
# WL pattern stripping must not mangle snake_case Julia names (sxAct-yg6v)
# ---------------------------------------------------------------------------


class TestWlPatternStripping:
    """_preprocess_wl_patterns must strip WL blanks but preserve snake_case."""

    def test_simple_blank_stripped(self):
        from sxact.translate.wl_to_julia import _preprocess_wl_patterns

        assert _preprocess_wl_patterns("x_") == "x"

    def test_typed_blank_stripped(self):
        from sxact.translate.wl_to_julia import _preprocess_wl_patterns

        assert _preprocess_wl_patterns("x_Integer") == "x"

    def test_blank_sequence_stripped(self):
        from sxact.translate.wl_to_julia import _preprocess_wl_patterns

        assert _preprocess_wl_patterns("x__") == "x"

    def test_blank_null_sequence_stripped(self):
        from sxact.translate.wl_to_julia import _preprocess_wl_patterns

        assert _preprocess_wl_patterns("x___") == "x"

    def test_snake_case_preserved(self):
        from sxact.translate.wl_to_julia import _preprocess_wl_patterns

        assert _preprocess_wl_patterns("check_perturbation_order") == "check_perturbation_order"

    def test_snake_case_in_call_preserved(self):
        from sxact.translate.wl_to_julia import _preprocess_wl_patterns

        expr = "check_perturbation_order(Pertg1, 1) === true"
        assert _preprocess_wl_patterns(expr) == expr

    def test_mixed_snake_and_blank(self):
        from sxact.translate.wl_to_julia import _preprocess_wl_patterns

        # x_ should be stripped but check_order should be preserved
        assert _preprocess_wl_patterns("f[x_, check_order]") == "f[x, check_order]"

    def test_wl_to_jl_preserves_snake_case(self):
        from sxact.translate.wl_to_julia import wl_to_jl as _wl_to_jl

        result = _wl_to_jl("check_perturbation_order(Pertg1, 1) === true")
        assert "check_perturbation_order" in result


# ---------------------------------------------------------------------------
# _to_canonical must expand CovD bracket syntax before canonicalizing
# ---------------------------------------------------------------------------


class TestToCanonicalCovDBrackets:
    """_to_canonical must handle expressions containing CovD bracket syntax.

    CommuteCovDs returns expressions with CovD bracket notation like
    CVD[-a][CVD[-b][V[-c]]]. When these are substituted into a ToCanonical
    expression, the adapter must expand them via SortCovDs first.
    """

    @pytest.fixture(autouse=True)
    def _setup(self):
        adapter = JuliaAdapter()
        self.ctx = adapter.initialize()
        self.adapter = adapter
        adapter.execute(
            self.ctx,
            "DefManifold",
            {"name": "CCm", "dimension": 4, "indices": ["cca", "ccb", "ccc", "ccd", "cce", "ccf"]},
        )
        adapter.execute(
            self.ctx,
            "DefMetric",
            {"signdet": -1, "metric": "CCg[-cca,-ccb]", "covd": "CCD"},
        )
        adapter.execute(
            self.ctx,
            "DefTensor",
            {"name": "CCv", "indices": ["-cca"], "manifold": "CCm"},
        )
        yield
        adapter.teardown(self.ctx)

    def test_to_canonical_with_covd_brackets_returns_zero(self):
        """Expression where CovD bracket terms cancel should return '0'."""
        expr = "CCD[-ccb][CCD[-cca][CCv[-ccc]]] - CCD[-ccb][CCD[-cca][CCv[-ccc]]]"
        result = self.adapter._to_canonical({"expression": expr})
        assert result.status == "ok"
        assert result.repr == "0"

    def test_commute_then_canonical_verification(self):
        """CommuteCovDs result fed into ToCanonical verification equals zero."""
        r1 = self.adapter.execute(
            self.ctx,
            "CommuteCovDs",
            {
                "expression": "CCD[-cca][CCD[-ccb][CCv[-ccc]]]",
                "covd": "CCD",
                "indices": ["-cca", "-ccb"],
            },
        )
        check_expr = (
            f"{r1.repr} - CCD[-ccb][CCD[-cca][CCv[-ccc]]]"
            " + RiemannCCD[-ccc,ccd,-cca,-ccb] CCv[-ccd]"
        )
        r2 = self.adapter._to_canonical({"expression": check_expr})
        assert r2.status == "ok"
        assert r2.repr == "0"
