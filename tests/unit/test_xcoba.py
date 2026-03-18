"""Unit tests for xCoba Python API — coordinate basis and chart infrastructure."""

import pytest

import xact


@pytest.fixture(autouse=True)
def _reset():
    xact.reset()


@pytest.fixture()
def manifold_4d():
    return xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])


@pytest.fixture()
def metric(manifold_4d):
    return xact.Metric(manifold_4d, "g", signature=-1, covd="CD")


# ---------------------------------------------------------------------------
# Basis handle class
# ---------------------------------------------------------------------------


class TestBasis:
    def test_create(self, manifold_4d, metric):
        B = xact.Basis("B", "TangentM", [1, 2, 3, 4])
        assert B.name == "B"
        assert B.vbundle == "TangentM"
        assert B.cnumbers == [1, 2, 3, 4]

    def test_repr(self, manifold_4d, metric):
        B = xact.Basis("B", "TangentM", [1, 2, 3, 4])
        assert repr(B) == "Basis('B', 'TangentM')"

    def test_creates_julia_basis(self, manifold_4d, metric):
        xact.Basis("B", "TangentM", [1, 2, 3, 4])
        # The basis should be queryable from Julia
        jl, _ = xact.api._ensure_init()
        assert jl.seval("XTensor.BasisQ(:B)") is True


# ---------------------------------------------------------------------------
# Chart handle class
# ---------------------------------------------------------------------------


class TestChart:
    def test_create(self, manifold_4d):
        C = xact.Chart("SchC", manifold_4d, [1, 2, 3, 4], ["t", "r", "th", "ph"])
        assert C.name == "SchC"
        assert C.manifold is manifold_4d
        assert C.cnumbers == [1, 2, 3, 4]
        assert C.scalars == ["t", "r", "th", "ph"]

    def test_create_with_manifold_name(self, manifold_4d):
        C = xact.Chart("SchC", "M", [1, 2, 3, 4], ["t", "r", "th", "ph"])
        assert C.name == "SchC"

    def test_repr(self, manifold_4d):
        C = xact.Chart("SchC", manifold_4d, [1, 2, 3, 4], ["t", "r", "th", "ph"])
        assert repr(C) == "Chart('SchC', 'M')"

    def test_creates_julia_chart(self, manifold_4d):
        xact.Chart("SchC", manifold_4d, [1, 2, 3, 4], ["t", "r", "th", "ph"])
        jl, _ = xact.api._ensure_init()
        assert jl.seval("XTensor.ChartQ(:SchC)") is True

    def test_registers_coordinate_scalars(self, manifold_4d):
        xact.Chart("SchC", manifold_4d, [1, 2, 3, 4], ["t", "r", "th", "ph"])
        jl, _ = xact.api._ensure_init()
        # Each scalar should be registered as a tensor
        for sc in ["t", "r", "th", "ph"]:
            assert jl.seval(f"XTensor.TensorQ(:{sc})") is True


# ---------------------------------------------------------------------------
# def_basis / def_chart functions (module-level)
# ---------------------------------------------------------------------------


class TestDefBasis:
    def test_def_basis(self, manifold_4d, metric):
        xact.def_basis("B2", "TangentM", [1, 2, 3, 4])
        jl, _ = xact.api._ensure_init()
        assert jl.seval("XTensor.BasisQ(:B2)") is True

    def test_def_basis_wrong_vbundle(self, manifold_4d, metric):
        with pytest.raises(Exception):
            xact.def_basis("B3", "NonExistentBundle", [1, 2, 3, 4])


class TestDefChart:
    def test_def_chart(self, manifold_4d):
        xact.def_chart("SchC2", "M", [1, 2, 3, 4], ["t2", "r2", "th2", "ph2"])
        jl, _ = xact.api._ensure_init()
        assert jl.seval("XTensor.ChartQ(:SchC2)") is True

    def test_def_chart_wrong_dim(self, manifold_4d):
        with pytest.raises(Exception):
            xact.def_chart("SchC3", "M", [1, 2, 3], ["t3", "r3", "th3"])


# ---------------------------------------------------------------------------
# Basis change operations
# ---------------------------------------------------------------------------


class TestBasisChange:
    @pytest.fixture()
    def two_bases(self, manifold_4d, metric):
        B1 = xact.Basis("Bcart", "TangentM", [1, 2, 3, 4])
        B2 = xact.Basis("Bpol", "TangentM", [1, 2, 3, 4])
        # Simple identity Jacobian (diagonal 1s)
        identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        xact.set_basis_change("Bcart", "Bpol", identity)
        return B1, B2

    def test_set_basis_change(self, two_bases):
        assert xact.basis_change_q("Bcart", "Bpol") is True

    def test_basis_change_q_false(self, manifold_4d, metric):
        xact.Basis("Bx", "TangentM", [1, 2, 3, 4])
        xact.Basis("By", "TangentM", [1, 2, 3, 4])
        assert xact.basis_change_q("Bx", "By") is False

    def test_get_jacobian(self, two_bases):
        j = xact.get_jacobian("Bcart", "Bpol")
        assert isinstance(j, str)
        # Jacobian should be a CTensor object representation
        assert len(j) > 0


# ---------------------------------------------------------------------------
# Exported symbols
# ---------------------------------------------------------------------------


class TestExports:
    def test_basis_exported(self):
        assert hasattr(xact, "Basis")

    def test_chart_exported(self):
        assert hasattr(xact, "Chart")

    def test_def_basis_exported(self):
        assert hasattr(xact, "def_basis")

    def test_def_chart_exported(self):
        assert hasattr(xact, "def_chart")

    def test_set_basis_change_exported(self):
        assert hasattr(xact, "set_basis_change")

    def test_change_basis_exported(self):
        assert hasattr(xact, "change_basis")

    def test_get_jacobian_exported(self):
        assert hasattr(xact, "get_jacobian")

    def test_basis_change_q_exported(self):
        assert hasattr(xact, "basis_change_q")
