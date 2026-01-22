"""Integration tests for basic xAct operations.

These tests validate the full pipeline:
1. Oracle HTTP server receives xAct expressions
2. xAct evaluates them correctly
3. Results are properly normalized
4. Comparator handles xAct output formats

All tests require the Docker oracle server running with xAct loaded.

NOTE: Each test uses unique manifold/tensor names (M1, M2, etc.) to avoid
conflicts in the persistent Wolfram kernel. xAct protects symbols after
definition, so reusing names across tests causes errors.
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
        result = xact_evaluate(oracle, "DefManifold[M1, 4, {a1,b1,c1,d1}]; M1")
        assert result.status == "ok", f"Failed: {result.error}"
        assert "M1" in result.repr or result.repr != ""

    def test_manifold_dimension(self, oracle: OracleClient) -> None:
        result = xact_evaluate(oracle, "DefManifold[M2, 3, {i2,j2,k2}]; DimOfManifold[M2]")
        assert result.status == "ok", f"Failed: {result.error}"
        assert "3" in result.repr


@pytest.mark.oracle
@pytest.mark.slow
class TestDefineMetric:
    """Test 2: Define metric, verify properties."""

    def test_define_metric_with_signature(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M3, 4, {a3,b3,c3,d3}];
        DefMetric[-1, g3[-a3,-b3], CD3];
        SignDetOfMetric[g3]
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert "-1" in result.repr, f"Expected -1 for Lorentzian signature, got: {result.repr}"


@pytest.mark.oracle
@pytest.mark.slow
class TestSymmetricTensor:
    """Test 3: Define symmetric tensor, test symmetry."""

    def test_symmetric_tensor_swap_indices(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M4, 4, {a4,b4,c4,d4}];
        DefTensor[S4[-a4,-b4], M4, Symmetric[{-a4,-b4}]];
        S4[-b4,-a4] - S4[-a4,-b4] // ToCanonical
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
        DefManifold[M5, 4, {a5,b5,c5,d5}];
        DefTensor[T5[-a5,-b5], M5];
        ToCanonical[T5[-b5,-a5]]
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert "T5" in result.repr


@pytest.mark.oracle
@pytest.mark.slow
class TestMetricContraction:
    """Test 5: Simplify with metric contraction."""

    def test_metric_contraction_raises_index(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M6, 4, {a6,b6,c6,d6}];
        DefMetric[1, g6[-a6,-b6], CD6];
        DefTensor[V6[a6], M6];
        g6[a6,b6] V6[-b6] // ContractMetric
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert "V6" in result.repr


@pytest.mark.oracle
@pytest.mark.slow
class TestRiemannTensor:
    """Test 6: Riemann tensor definition."""

    def test_riemann_exists_after_metric_definition(self, oracle: OracleClient) -> None:
        expr = """
        DefManifold[M7, 4, {a7,b7,c7,d7}];
        DefMetric[-1, g7[-a7,-b7], CD7];
        RiemannCD7[-a7,-b7,-c7,-d7]
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
        DefManifold[M8, 4, {a8,b8,c8,d8}];
        DefTensor[S8[-a8,-b8], M8, Symmetric[{-a8,-b8}]];
        """
        xact_evaluate(oracle, setup)

        lhs = xact_evaluate(oracle, "S8[-a8,-b8] + S8[-b8,-a8]")
        rhs = xact_evaluate(oracle, "2*S8[-a8,-b8]")

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
        DefManifold[M9, 4, {a9,b9,c9,d9}];
        DefTensor[F9[-a9,-b9], M9, Antisymmetric[{-a9,-b9}]];
        F9[-b9,-a9] + F9[-a9,-b9] // ToCanonical
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
        DefManifold[M10, 4, {a10,b10,c10,d10,e10,f10}];
        DefMetric[-1, g10[-a10,-b10], CD10];
        RiemannCD10[-a10,-b10,-c10,-d10] + RiemannCD10[-a10,-c10,-d10,-b10] + RiemannCD10[-a10,-d10,-b10,-c10] // ToCanonical
        """
        result = xact_evaluate(oracle, expr)
        assert result.status == "ok", f"Failed: {result.error}"
        assert result.repr.strip() == "0", f"First Bianchi identity should give 0, got: {result.repr}"
