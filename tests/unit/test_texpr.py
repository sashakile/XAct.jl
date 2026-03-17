"""Unit tests for typed expression API (xact.expr)."""

from __future__ import annotations

import pytest

import xact
from xact.expr import AppliedTensor, DnIdx, TensorHead


@pytest.fixture(autouse=True)
def _reset():
    xact.reset()


@pytest.fixture()
def manifold():
    return xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])


@pytest.fixture()
def metric(manifold):
    return xact.Metric(manifold, "g", signature=-1, covd="CD")


class TestIdx:
    def test_create(self, manifold):
        a, b, c, d, e, f = xact.indices(manifold)
        assert a.label == "a"
        assert a.manifold == "M"

    def test_neg_creates_dnidx(self, manifold):
        a, *_ = xact.indices(manifold)
        da = -a
        assert isinstance(da, DnIdx)
        assert da.parent is a

    def test_double_neg(self, manifold):
        a, *_ = xact.indices(manifold)
        assert -(-a) is a

    def test_repr(self, manifold):
        a, *_ = xact.indices(manifold)
        assert repr(a) == "a"
        assert repr(-a) == "-a"

    def test_indices_count(self, manifold):
        indices = xact.indices(manifold)
        assert len(indices) == 6


class TestTensorHead:
    def test_lookup(self, manifold, metric):
        th = xact.tensor("g")
        assert isinstance(th, TensorHead)
        assert th.name == "g"

    def test_auto_tensors(self, manifold, metric):
        assert xact.tensor("RiemannCD").name == "RiemannCD"
        assert xact.tensor("RicciCD").name == "RicciCD"

    def test_unregistered(self, manifold, metric):
        with pytest.raises(ValueError):
            xact.tensor("NoSuchTensor")

    def test_repr(self, manifold, metric):
        th = xact.tensor("g")
        assert "TensorHead" in repr(th)


class TestAppliedTensor:
    def test_getitem(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        t = g[-a, -b]
        assert isinstance(t, AppliedTensor)
        assert len(t.indices) == 2

    def test_slot_count_error(self, manifold, metric):
        a, b, c, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        with pytest.raises((ValueError, IndexError)):
            g[-a, -b, -c]

    def test_str(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        assert str(g[-a, -b]) == "g[-a,-b]"

    def test_tensor_class_getitem(self, manifold, metric):
        """Tensor definition objects also support __getitem__."""
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold, symmetry="Symmetric[{-a,-b}]")
        t = T[-a, -b]
        assert isinstance(t, AppliedTensor)
        assert str(t) == "T[-a,-b]"

    def test_metric_class_getitem(self, manifold, metric):
        """Metric definition objects also support __getitem__."""
        a, b, *_ = xact.indices(manifold)
        t = metric[-a, -b]
        assert isinstance(t, AppliedTensor)
        assert str(t) == "g[-a,-b]"


class TestArithmetic:
    def test_add(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        S = xact.Tensor("S", ["-a", "-b"], manifold)
        expr = T[-a, -b] + S[-a, -b]
        assert "T[-a,-b]" in str(expr)
        assert "S[-a,-b]" in str(expr)
        assert "+" in str(expr)

    def test_sub(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        S = xact.Tensor("S", ["-a", "-b"], manifold)
        expr = T[-a, -b] - S[-a, -b]
        s = str(expr)
        assert " - " in s
        assert "+ -" not in s

    def test_scalar_mul(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        expr = 2 * T[-a, -b]
        assert str(expr).startswith("2")

    def test_neg(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        expr = -T[-a, -b]
        assert str(expr).startswith("-")

    def test_tensor_product(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold)
        V = xact.Tensor("V", ["a"], manifold)
        expr = T[-a, -b] * V[a]
        assert "T[-a,-b]" in str(expr)
        assert "V[a]" in str(expr)


class TestEngineIntegration:
    def test_canonicalize_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        T = xact.Tensor("T", ["-a", "-b"], manifold, symmetry="Symmetric[{-a,-b}]")
        result = xact.canonicalize(T[-b, -a] - T[-a, -b])
        assert result == "0"

    def test_canonicalize_typed_matches_string(self, manifold, metric):
        a, b, c, d, *_ = xact.indices(manifold)
        Riem = xact.tensor("RiemannCD")
        typed = xact.canonicalize(
            Riem[-a, -b, -c, -d] + Riem[-a, -c, -d, -b] + Riem[-a, -d, -b, -c]
        )
        string = xact.canonicalize(
            "RiemannCD[-a,-b,-c,-d] + RiemannCD[-a,-c,-d,-b] + RiemannCD[-a,-d,-b,-c]"
        )
        assert typed == string == "0"

    def test_contract_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        V = xact.Tensor("V", ["a"], manifold)
        g = xact.tensor("g")
        typed = xact.contract(V[a] * g[-a, -b])
        string = xact.contract("V[a] * g[-a,-b]")
        assert typed == string

    def test_simplify_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        g = xact.tensor("g")
        typed = xact.simplify(g[-a, -b])
        string = xact.simplify("g[-a,-b]")
        assert typed == string

    def test_perturb_typed(self, manifold, metric):
        a, b, *_ = xact.indices(manifold)
        h = xact.Tensor("h", ["-a", "-b"], manifold, symmetry="Symmetric[{-a,-b}]")
        xact.Perturbation(h, metric, order=1)
        g = xact.tensor("g")
        typed = xact.perturb(g[-a, -b], order=1)
        string = xact.perturb("g[-a,-b]", order=1)
        assert typed == string
