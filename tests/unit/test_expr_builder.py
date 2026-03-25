"""Tests for sxact.elegua_bridge.build_xact_expr."""

from __future__ import annotations

import pytest

from sxact.elegua_bridge import build_xact_expr


class TestBuildXactExpr:
    def test_def_manifold(self):
        result = build_xact_expr(
            "DefManifold",
            {"name": "M", "dimension": 4, "indices": ["a", "b", "c", "d"]},
        )
        assert result == "DefManifold[M, 4, {a, b, c, d}]"

    def test_def_metric(self):
        result = build_xact_expr(
            "DefMetric",
            {"signdet": -1, "metric": "g[-a,-b]", "covd": "CD"},
        )
        assert result == "DefMetric[-1, g[-a,-b], CD]"

    def test_def_tensor_with_symmetry(self):
        result = build_xact_expr(
            "DefTensor",
            {
                "name": "T",
                "indices": ["-a", "-b"],
                "manifold": "M",
                "symmetry": "Symmetric[{-a,-b}]",
            },
        )
        assert result == "DefTensor[T[-a,-b], M, Symmetric[{-a,-b}]]"

    def test_def_tensor_minimal(self):
        result = build_xact_expr(
            "DefTensor",
            {"name": "V", "indices": ["-a"], "manifold": "M"},
        )
        assert result == "DefTensor[V[-a], M]"

    def test_evaluate(self):
        result = build_xact_expr("Evaluate", {"expression": "1 + 1"})
        assert result == "1 + 1"

    def test_to_canonical(self):
        result = build_xact_expr("ToCanonical", {"expression": "T[-b,-a]"})
        assert result == "ToCanonical[T[-b,-a]]"

    def test_contract(self):
        result = build_xact_expr("Contract", {"expression": "g[a,b] T[-a,-b]"})
        assert result == "ContractMetric[g[a,b] T[-a,-b]]"

    def test_simplify_basic(self):
        result = build_xact_expr("Simplify", {"expression": "T[-a,-b]"})
        assert result == "Simplify[T[-a,-b]]"

    def test_simplify_with_assumptions(self):
        result = build_xact_expr(
            "Simplify",
            {"expression": "T[-a,-b]", "assumptions": "dim == 4"},
        )
        assert result == "Simplify[T[-a,-b], dim == 4]"

    def test_assert(self):
        result = build_xact_expr("Assert", {"condition": "T[-a,-b] == 0"})
        assert result == "T[-a,-b] == 0"

    def test_commute_covds(self):
        result = build_xact_expr(
            "CommuteCovDs",
            {"expression": "T[-a,-b]", "covd": "CD", "indices": ["a", "b"]},
        )
        assert result == "CommuteCovDs[T[-a,-b], CD, {a, b}]"

    def test_perturb(self):
        result = build_xact_expr("Perturb", {"expr": "g[-a,-b]", "order": 1})
        assert result == "Perturb[g[-a,-b], 1]"

    def test_unknown_action_raises(self):
        with pytest.raises(ValueError, match="Unknown xAct action"):
            build_xact_expr("Bogus", {})
