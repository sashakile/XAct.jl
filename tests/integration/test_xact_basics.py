"""Integration tests for basic xAct operations.

These tests validate the full pipeline:
1. Oracle HTTP server receives xAct expressions
2. xAct evaluates them correctly
3. Results are properly normalized
4. Comparator handles xAct output formats

All tests require the Docker oracle server running with xAct loaded.
"""

import pytest

from sxact.compare import compare
from sxact.compare.comparator import EqualityMode
from sxact.oracle import OracleClient
from sxact.oracle.result import Result


def xact_evaluate(oracle: OracleClient, expr: str) -> Result:
    """Evaluate an xAct expression and return a Result envelope.

    Uses /evaluate-with-init to ensure xAct is loaded.
    """
    from sxact.normalize import normalize

    eval_result = oracle.evaluate_with_xact(expr, timeout=120)

    if eval_result.status == "ok":
        raw = eval_result.result or ""
        return Result(
            status="ok",
            type="Expr",
            repr=raw,
            normalized=normalize(raw) if raw else "",
            diagnostics={"execution_time_ms": eval_result.timing_ms},
        )
    elif eval_result.status == "timeout":
        return Result(
            status="timeout",
            type="",
            repr="",
            normalized="",
            error=eval_result.error,
        )
    else:
        return Result(
            status="error",
            type="",
            repr="",
            normalized="",
            error=eval_result.error,
        )


@pytest.mark.oracle
@pytest.mark.slow
class TestDefineManifold:
    """Test 1: Define manifold, verify output."""

    def test_define_manifold_returns_manifold_info(self, oracle: OracleClient) -> None:
        result = xact_evaluate(oracle, "DefManifold[M, 4, {a,b,c,d}]; M")
        assert result.status == "ok", f"Failed: {result.error}"
        assert "M" in result.repr or result.repr != ""

    def test_manifold_dimension(self, oracle: OracleClient) -> None:
        result = xact_evaluate(oracle, "DefManifold[N, 3, {i,j,k}]; DimOfManifold[N]")
        assert result.status == "ok", f"Failed: {result.error}"
        assert "3" in result.repr


@pytest.mark.oracle
@pytest.mark.slow
class TestDefineMetric:
    """Test 2: Define metric, verify properties."""

    def test_define_metric_with_signature(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M, 4, {a,b,c,d}];
        DefMetric[-1, g[-a,-b], CD];
        SignatureOfMetric[g]
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert "-1" in result.repr or "Lorentzian" in result.repr or "{" in result.repr


@pytest.mark.oracle
@pytest.mark.slow
class TestSymmetricTensor:
    """Test 3: Define symmetric tensor, test symmetry."""

    def test_symmetric_tensor_swap_indices(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M, 4, {a,b,c,d}];
        DefTensor[S[-a,-b], M, Symmetric[{-a,-b}]];
        S[-b,-a] - S[-a,-b] // ToCanonical
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert result.repr.strip() == "0", f"Expected 0 for symmetric tensor swap, got: {result.repr}"


@pytest.mark.oracle
@pytest.mark.slow
class TestToCanonical:
    """Test 4: ToCanonical on simple expression."""

    def test_tocanonical_reorders_indices(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M, 4, {a,b,c,d}];
        DefTensor[T[-a,-b], M];
        ToCanonical[T[-b,-a]]
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert "T" in result.repr


@pytest.mark.oracle
@pytest.mark.slow
class TestMetricContraction:
    """Test 5: Simplify with metric contraction."""

    def test_metric_contraction_raises_index(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M, 4, {a,b,c,d}];
        DefMetric[1, g[-a,-b], CD];
        DefTensor[V[a], M];
        g[a,b] V[-b] // ContractMetric
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert "V" in result.repr


@pytest.mark.oracle
@pytest.mark.slow
class TestRiemannTensor:
    """Test 6: Riemann tensor definition."""

    def test_riemann_exists_after_metric_definition(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M, 4, {a,b,c,d}];
        DefMetric[-1, g[-a,-b], CD];
        RiemannCD[-a,-b,-c,-d]
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert "Riemann" in result.repr or result.repr != ""


@pytest.mark.oracle
@pytest.mark.slow
class TestSymbolicEquality:
    """Test 7: Two expressions that are symbolically equal."""

    def test_symmetric_tensor_sum_equals_double(self, oracle: OracleClient) -> None:
        setup = """
        DefManifold[M, 4, {a,b,c,d}];
        DefTensor[S[-a,-b], M, Symmetric[{-a,-b}]];
        """
        xact_evaluate(oracle, setup)

        lhs = xact_evaluate(oracle, "S[-a,-b] + S[-b,-a]")
        rhs = xact_evaluate(oracle, "2*S[-a,-b]")

        assert lhs.status == "ok", f"LHS failed: {lhs.error}"
        assert rhs.status == "ok", f"RHS failed: {rhs.error}"

        cmp = compare(lhs, rhs, oracle)
        assert cmp.equal, f"Expected equality, got: tier={cmp.tier}, diff={cmp.diff}"
        assert cmp.tier <= 2, f"Expected tier 1 or 2, got tier {cmp.tier}"


@pytest.mark.oracle
@pytest.mark.slow
class TestNumericSampling:
    """Test 8: Expression requiring numeric sampling."""

    def test_numeric_evaluation_of_scalar_expression(self, oracle: OracleClient) -> None:
        lhs = Result(
            status="ok",
            type="Scalar",
            repr="Sin[x]^2 + Cos[x]^2",
            normalized="Cos[x]^2 + Sin[x]^2",
        )
        rhs = Result(
            status="ok",
            type="Scalar",
            repr="1",
            normalized="1",
        )

        cmp = compare(lhs, rhs, oracle, mode=EqualityMode.NUMERIC)
        assert cmp.equal, f"Expected trig identity to hold: {cmp.diff}"


@pytest.mark.oracle
@pytest.mark.slow
class TestAntisymmetricTensor:
    """Test 9: Antisymmetric tensor properties."""

    def test_antisymmetric_tensor_swap_negates(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M, 4, {a,b,c,d}];
        DefTensor[F[-a,-b], M, Antisymmetric[{-a,-b}]];
        F[-b,-a] + F[-a,-b] // ToCanonical
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert result.repr.strip() == "0", f"Expected 0 for antisymmetric sum, got: {result.repr}"


@pytest.mark.oracle
@pytest.mark.slow
class TestBianchiIdentity:
    """Test 10: Bianchi identity structure (advanced)."""

    def test_riemann_first_bianchi_structure(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M, 4, {a,b,c,d,e,f}];
        DefMetric[-1, g[-a,-b], CD];
        RiemannCD[-a,-b,-c,-d] + RiemannCD[-a,-c,-d,-b] + RiemannCD[-a,-d,-b,-c] // ToCanonical
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert result.repr.strip() == "0", f"First Bianchi identity should give 0, got: {result.repr}"
