"""JuliaAdapter — concrete adapter backed by Julia XCore/XTensor via juliacall.

Uses the Python xCore runtime (_runtime.py) to lazily initialise Julia and
load XCore.jl once per process.  Evaluates Julia expressions translated from
the TOML test vocabulary (Wolfram → Julia syntax).

Per-file isolation is achieved by resetting XCore and XTensor global state on
teardown.

Actions that require xTensor (DefManifold, DefMetric, DefTensor, ToCanonical,
Contract, SignDetOfMetric, Simplify) are dispatched to the Julia XTensor module.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar
from typing import Literal as _Literal

from sxact.adapter.base import (
    AdapterError,
    EqualityMode,
    NormalizedExpr,
    TestAdapter,
    VersionInfo,
)
from sxact.adapter.julia_comparison import (
    bind_fresh_symbols as _bind_fresh_symbols,
)
from sxact.adapter.julia_comparison import (
    bind_wl_atoms as _bind_wl_atoms,
)
from sxact.adapter.julia_comparison import (
    try_numerical_tolerance_via_canonical as _try_numerical_tolerance_via_canonical,
)
from sxact.adapter.julia_comparison import (
    try_tensor_string_comparison as _try_tensor_string_comparison,
)
from sxact.adapter.julia_comparison import (
    try_to_canonical_comparison as _try_to_canonical_comparison,
)
from sxact.adapter.julia_names import (
    DEF_MANIFOLD as _JN_DEF_MANIFOLD,
)
from sxact.adapter.julia_names import (
    DEF_METRIC as _JN_DEF_METRIC,
)
from sxact.adapter.julia_names import (
    DEF_PERTURBATION as _JN_DEF_PERTURBATION,
)
from sxact.adapter.julia_names import (
    DEF_TENSOR as _JN_DEF_TENSOR,
)
from sxact.normalize import normalize as _normalize
from sxact.oracle.result import Result
from sxact.translate.wl_to_julia import (
    is_tensor_expr as _is_tensor_expr,
)
from sxact.translate.wl_to_julia import (
    is_trivially_equal as _is_trivially_equal,
)
from sxact.translate.wl_to_julia import (
    postprocess_dimino as _postprocess_dimino,
)
from sxact.translate.wl_to_julia import (
    wl_to_jl as _wl_to_jl,
)
from xact._bridge import (
    jl_call,
    jl_int,
    jl_str,
    jl_sym,
    jl_sym_list,
    timed_seval,
    validate_ident,
)

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_Symmetry = _Literal["Symmetric", "Antisymmetric"]


def _parse_symmetry(sym_str: str) -> _Symmetry | None:
    """Extract symmetry type from xAct symmetry string.

    Returns 'Symmetric', 'Antisymmetric', or None.
    GradedSymmetric maps to 'Antisymmetric' for Tier 3 numeric array generation.
    """
    if not sym_str:
        return None
    if sym_str.startswith("Symmetric"):
        return "Symmetric"
    if sym_str.startswith("Antisymmetric"):
        return "Antisymmetric"
    if sym_str.startswith("GradedSymmetric"):
        return "Antisymmetric"
    return None


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


class _JuliaContext:
    """Opaque per-file context for JuliaAdapter.

    Tracks manifold/metric/tensor definitions made during this context so that
    a TensorContext can be built for Tier 3 numeric comparison.
    """

    def __init__(self) -> None:
        self.alive: bool = True
        # Populated by _def_manifold / _def_metric / _def_tensor
        from sxact.compare.tensor_objects import Manifold, Metric, TensorField

        self._manifolds: list[Manifold] = []
        self._metrics: list[Metric] = []
        self._tensors: list[TensorField] = []


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class JuliaAdapter(TestAdapter[_JuliaContext]):
    """Concrete adapter for the Julia XCore + XTensor backend."""

    # Tier 2 deferred actions
    _DEFERRED_ACTIONS: frozenset[str] = frozenset()

    # XCore module-level mutable state to reset on teardown
    _RESET_STMTS: ClassVar[list[str]] = ["xAct.reset_state!()"]

    def __init__(self) -> None:
        self._jl: Any = None
        self._xact_version: str = "unknown"
        self._julia_version: str = "unknown"
        # Action → handler registry.  Handlers that need ctx take (ctx, args);
        # handlers that don't take (args) only.  _CTX_ACTIONS lists the former.
        self._ACTION_HANDLERS: dict[str, str] = {
            "DefManifold": "_def_manifold",
            "DefMetric": "_def_metric",
            "DefTensor": "_def_tensor",
            "DefBasis": "_def_basis",
            "DefChart": "_def_chart",
            "ToCanonical": "_to_canonical",
            "Contract": "_contract",
            "CommuteCovDs": "_commute_covds",
            "SortCovDs": "_sort_covds",
            "DefPerturbation": "_def_perturbation",
            "CheckMetricConsistency": "_check_metric_consistency",
            "Perturb": "_perturb",
            "PerturbCurvature": "_perturb_curvature",
            "Simplify": "_simplify",
            "PerturbationOrder": "_perturbation_order",
            "PerturbationAtOrder": "_perturbation_at_order",
            "IntegrateByParts": "_integrate_by_parts",
            "TotalDerivativeQ": "_total_derivative_q",
            "VarD": "_vard",
            "SetBasisChange": "_set_basis_change",
            "ChangeBasis": "_change_basis",
            "GetJacobian": "_get_jacobian",
            "BasisChangeQ": "_basis_change_q",
            "SetComponents": "_set_components",
            "GetComponents": "_get_components",
            "ComponentValue": "_component_value",
            "CTensorQ": "_ctensor_q",
            "ToBasis": "_to_basis",
            "FromBasis": "_from_basis",
            "TraceBasisDummy": "_trace_basis_dummy",
            "Christoffel": "_christoffel",
            "CollectTensors": "_collect_tensors",
            "AllContractions": "_all_contractions",
            "SymmetryOf": "_symmetry_of",
            "MakeTraceFree": "_make_trace_free",
            "RiemannSimplify": "_riemann_simplify",
        }
        self._CTX_ACTIONS = frozenset({"DefManifold", "DefMetric", "DefTensor", "DefPerturbation"})

    def _ensure_ready(self) -> None:
        if self._jl is not None:
            return
        try:
            from xact.xcore._runtime import get_julia, get_xcore

            self._jl = get_julia()
            get_xcore()
            raw = self._jl.seval("string(VERSION)")
            self._julia_version = str(raw).strip()
            # Try to get xAct package version
            try:
                raw_xa = self._jl.seval("string(pkgversion(xAct))")
                self._xact_version = str(raw_xa).strip()
            except Exception:
                self._xact_version = "dev"
        except Exception as exc:
            raise AdapterError(f"Julia/XCore initialisation failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> _JuliaContext:
        try:
            self._ensure_ready()
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterError(f"Julia/XCore unavailable: {exc}") from exc
        return _JuliaContext()

    def teardown(self, ctx: _JuliaContext) -> None:
        ctx.alive = False
        if self._jl is None:
            return
        for stmt in self._RESET_STMTS:
            try:
                self._jl.seval(stmt)
            except Exception:
                import warnings

                warnings.warn(
                    f"JuliaAdapter.teardown: failed to execute '{stmt}'",
                    RuntimeWarning,
                    stacklevel=2,
                )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, ctx: _JuliaContext, action: str, args: dict[str, Any]) -> Result:
        if action not in self.supported_actions():
            raise ValueError(f"Unknown action: {action!r}")

        if action in self._DEFERRED_ACTIONS:
            return Result(
                status="error",
                type="",
                repr="",
                normalized="",
                error=f"action {action!r} is deferred to Tier 2",
            )

        self._ensure_ready()

        if action in self._ACTION_HANDLERS:
            return self._execute_xtensor(ctx, action, args)

        if action == "Evaluate":
            expr = args.get("expression", "")
            # Intercept numerical_tolerance comparisons BEFORE the early-return so
            # Max[Abs[Flatten[N[...]]]] tensor expressions are handled via ToCanonical.
            canonical_result = _try_numerical_tolerance_via_canonical(self._jl, expr)
            if canonical_result is not None:
                return canonical_result
            # If it looks like a tensor expression (contains Name[...] with index syntax),
            # return it as-is for later ToCanonical use — no Julia evaluation needed.
            # Exception: if the expression contains a comparison operator (===) it is a
            # law-check from the property runner and must be evaluated in Julia.
            if _is_tensor_expr(expr) and "===" not in expr:
                return Result(status="ok", type="Expr", repr=expr, normalized=_normalize(expr))
            return self._execute_expr(expr)
        if action == "Assert":
            return self._execute_assert(
                args.get("condition", ""),
                args.get("message"),
            )
        # Unreachable if supported_actions() is correct
        return Result(
            status="error",
            type="",
            repr="",
            normalized="",
            error=f"unhandled action: {action!r}",
        )

    def _execute_xtensor(self, ctx: _JuliaContext, action: str, args: dict[str, Any]) -> Result:
        """Dispatch xTensor actions via handler registry."""
        method_name = self._ACTION_HANDLERS.get(action)
        if method_name is None:
            return Result(
                status="error",
                type="",
                repr="",
                normalized="",
                error=f"unhandled xTensor action: {action!r}",
            )
        try:
            handler = getattr(self, method_name)
            result: Result
            if action in self._CTX_ACTIONS:
                result = handler(ctx, args)
            else:
                result = handler(args)
            return result
        except Exception as exc:
            import traceback as _tb

            tb_str = _tb.format_exc()
            return Result(
                status="error",
                type="",
                repr="",
                normalized="",
                error=f"{exc}\n{tb_str}",
            )

    def _def_manifold(self, ctx: _JuliaContext, args: dict[str, Any]) -> Result:
        from sxact.compare.tensor_objects import Manifold

        name = validate_ident(str(args["name"]), "manifold name")
        dim = int(args["dimension"])
        indices = list(args["indices"])
        jl_call(
            self._jl,
            _JN_DEF_MANIFOLD,
            jl_sym(name, "manifold name"),
            jl_int(dim),
            jl_sym_list(indices, "manifold indices"),
        )
        # Bind in Main scope as Symbols for Assert conditions:
        #   Dimension(Bm4) → Dimension(:Bm4); ManifoldQ(Bm4) → ManifoldQ(:Bm4)
        tangent_name = validate_ident(f"Tangent{name}", "tangent bundle name")
        self._jl.seval(f"Main.eval(:(global {name} = :{name}))")
        self._jl.seval(f"Main.eval(:(global {tangent_name} = :{tangent_name}))")
        for idx in indices:
            idx = validate_ident(idx, "manifold index")
            self._jl.seval(f"Main.eval(:(global {idx} = :{idx}))")
        ctx._manifolds.append(Manifold(name=name, dimension=dim))
        return Result(status="ok", type="Handle", repr=name, normalized=name)

    def _def_tensor(self, ctx: _JuliaContext, args: dict[str, Any]) -> Result:
        from sxact.compare.tensor_objects import TensorField

        name = validate_ident(str(args["name"]), "tensor name")
        indices = args["indices"]
        sym_str = args.get("symmetry") or ""
        idx_jl = "[" + ", ".join(jl_str(i) for i in indices) + "]"
        sym_arg = f", symmetry_str={jl_str(sym_str)}" if sym_str else ""

        # Support both "manifold" (single) and "manifolds" (list, multi-index-set)
        raw_manifolds = args.get("manifolds")
        if raw_manifolds is not None:
            # Multi-index-set: pass a Vector of Symbols to Julia
            manifold_names = [validate_ident(str(m), "manifold name") for m in raw_manifolds]
            jl_manifolds = "Symbol[" + ", ".join(f":{m}" for m in manifold_names) + "]"
            jl_call(
                self._jl,
                _JN_DEF_TENSOR,
                jl_sym(name, "tensor name"),
                idx_jl,
                jl_manifolds + sym_arg,
            )
            # Primary manifold for TensorContext = first in list
            primary_manifold_name = manifold_names[0] if manifold_names else None
        else:
            manifold = validate_ident(str(args["manifold"]), "manifold name")
            jl_call(
                self._jl,
                _JN_DEF_TENSOR,
                jl_sym(name, "tensor name"),
                idx_jl,
                jl_sym(manifold, "manifold name") + sym_arg,
            )
            primary_manifold_name = manifold

        # Bind tensor name in Main as a Symbol for TensorQ(Bts) etc.
        self._jl.seval(f"Main.eval(:(global {name} = :{name}))")
        # Record for TensorContext (Tier 3 numeric comparison)
        manifold_obj = next(
            (m for m in reversed(ctx._manifolds) if m.name == primary_manifold_name),
            ctx._manifolds[-1] if ctx._manifolds else None,
        )
        if manifold_obj is not None:
            symmetry = _parse_symmetry(sym_str)
            ctx._tensors.append(
                TensorField(
                    name=name,
                    rank=len(indices),
                    manifold=manifold_obj,
                    symmetry=symmetry,
                )
            )
        return Result(status="ok", type="Handle", repr=name, normalized=name)

    def _def_metric(self, ctx: _JuliaContext, args: dict[str, Any]) -> Result:
        import re as _re

        from sxact.compare.tensor_objects import Metric

        signdet = int(args["signdet"])
        metric_raw = str(args["metric"])
        covd = validate_ident(str(args["covd"]), "covariant derivative name")
        jl_call(
            self._jl,
            _JN_DEF_METRIC,
            jl_int(signdet),
            jl_str(metric_raw),
            jl_sym(covd, "covd name"),
        )
        # Bind the covd name in Main as a Symbol (for CovDQ assertions)
        self._jl.seval(f"Main.eval(:(global {covd} = :{covd}))")
        # Bind the metric tensor name in Main as a Symbol (for SignDetOfMetric assertions)
        m_name_match = _re.match(r"^(\w+)", metric_raw)
        metric_name = m_name_match.group(1) if m_name_match else None
        if metric_name:
            metric_name = validate_ident(metric_name, "metric name")
            self._jl.seval(f"Main.eval(:(global {metric_name} = :{metric_name}))")
        # Bind auto-created curvature tensor names in Main as Symbols
        for prefix in ("Riemann", "Ricci", "RicciScalar", "Einstein", "Weyl"):
            auto_name = validate_ident(f"{prefix}{covd}", "curvature tensor name")
            self._jl.seval(
                f"if XTensor.TensorQ(:{auto_name})\n"
                f"    Main.eval(:(global {auto_name} = :{auto_name}))\n"
                f"end"
            )
        # Record metric for TensorContext (use last manifold as the associated manifold)
        if metric_name and ctx._manifolds:
            # signdet == 1 → Euclidean (0 negative eigenvalues); -1 → Lorentzian (1 neg)
            signature = 1 if signdet == -1 else 0
            ctx._metrics.append(
                Metric(name=metric_name, manifold=ctx._manifolds[-1], signature=signature)
            )
        repr_str = metric_raw
        return Result(status="ok", type="Handle", repr=repr_str, normalized=repr_str)

    def _def_basis(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        name = validate_ident(str(args["name"]), "basis name")
        _api.def_basis(name, str(args["vbundle"]), list(args["cnumbers"]))
        self._jl.seval(f"Main.eval(:(global {name} = :{name}))")
        return Result(status="ok", type="Handle", repr=name, normalized=name)

    def _def_chart(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        name = validate_ident(str(args["name"]), "chart name")
        scalars = list(args["scalars"])
        _api.def_chart(name, str(args["manifold"]), list(args["cnumbers"]), scalars)
        self._jl.seval(f"Main.eval(:(global {name} = :{name}))")
        for sc in scalars:
            sc = validate_ident(sc, "chart scalar")
            self._jl.seval(f"Main.eval(:(global {sc} = :{sc}))")
        return Result(status="ok", type="Handle", repr=name, normalized=name)

    def _to_canonical(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        raw = _api.canonicalize(str(args["expression"]))
        return Result(status="ok", type="Expr", repr=raw, normalized=_normalize(raw))

    def _contract(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        raw = _api.contract(str(args["expression"]))
        return Result(status="ok", type="Expr", repr=raw, normalized=_normalize(raw))

    def _commute_covds(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        indices = list(args["indices"])
        if len(indices) != 2:
            return Result(
                status="error",
                type="",
                repr="",
                normalized="",
                error=f"CommuteCovDs: expected 2 indices, got {len(indices)}",
            )
        raw = _api.commute_covds(
            str(args["expression"]), str(args["covd"]), str(indices[0]), str(indices[1])
        )
        return Result(status="ok", type="Expr", repr=raw, normalized=_normalize(raw))

    def _sort_covds(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        raw = _api.sort_covds(str(args["expression"]), str(args["covd"]))
        return Result(status="ok", type="Expr", repr=raw, normalized=_normalize(raw))

    def _def_perturbation(self, ctx: _JuliaContext, args: dict[str, Any]) -> Result:
        tensor = validate_ident(str(args["tensor"]), "perturbation tensor")
        background = validate_ident(str(args["background"]), "background tensor")
        order = int(args["order"])
        jl_call(
            self._jl,
            _JN_DEF_PERTURBATION,
            jl_sym(tensor, "tensor"),
            jl_sym(background, "background"),
            jl_int(order),
        )
        # Bind the perturbation tensor name in Main as a Symbol (for PerturbationQ assertions)
        self._jl.seval(f"Main.eval(:(global {tensor} = :{tensor}))")
        return Result(status="ok", type="Handle", repr=tensor, normalized=tensor)

    def _perturb(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.perturb(str(args["expr"]), int(args["order"]))
        return Result(status="ok", type="String", repr=s, normalized=s)

    def _check_metric_consistency(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        ok = _api.check_metric_consistency(str(args["metric"]))
        raw = "True" if ok else "False"
        return Result(status="ok", type="Bool", repr=raw, normalized=raw)

    def _perturbation_order(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        order = _api.perturbation_order(str(args["tensor"]))
        return Result(status="ok", type="Int", repr=str(order), normalized=str(order))

    def _perturbation_at_order(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        name = _api.perturbation_at_order(str(args["background"]), int(args["order"]))
        return Result(status="ok", type="String", repr=name, normalized=name)

    def _simplify(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.simplify(str(args["expression"]))
        return Result(status="ok", type="String", repr=s, normalized=s)

    def _perturb_curvature(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        key = args.get("key")
        jl_dict = _api.perturb_curvature(
            str(args["covd"]),
            str(args["perturbation"]),
            order=int(args.get("order", 1)),
        )
        if key is not None:
            formula = jl_dict.get(str(key), "")
            return Result(status="ok", type="Expr", repr=formula, normalized=_normalize(formula))
        lines = [f"{k}: {v}" for k, v in sorted(jl_dict.items())]
        raw = "\n".join(lines)
        return Result(status="ok", type="Dict", repr=raw, normalized=raw)

    def _integrate_by_parts(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.ibp(str(args["expression"]), str(args["covd"]))
        return Result(status="ok", type="Expr", repr=s, normalized=_normalize(s))

    def _total_derivative_q(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        is_true = _api.total_derivative_q(str(args["expression"]), str(args["covd"]))
        s = "True" if is_true else "False"
        return Result(status="ok", type="Bool", repr=s, normalized=s)

    def _vard(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.var_d(str(args["expression"]), str(args["field"]), str(args["covd"]))
        return Result(status="ok", type="Expr", repr=s, normalized=_normalize(s))

    def _set_basis_change(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        from_basis = str(args["from_basis"])
        to_basis = str(args["to_basis"])
        _api.set_basis_change(from_basis, to_basis, list(args["matrix"]))
        repr_str = f"BasisChange({from_basis}, {to_basis})"
        return Result(status="ok", type="Handle", repr=repr_str, normalized=repr_str)

    def _change_basis(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        raw = _api.change_basis(
            str(args["expr"]),
            int(args["slot"]),
            str(args["from_basis"]),
            str(args["to_basis"]),
        )
        return Result(status="ok", type="Expr", repr=raw, normalized=_normalize(raw))

    def _get_jacobian(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        raw = _api.get_jacobian(str(args["basis1"]), str(args["basis2"]))
        return Result(status="ok", type="Scalar", repr=raw, normalized=raw)

    def _basis_change_q(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        ok = _api.basis_change_q(str(args["from_basis"]), str(args["to_basis"]))
        raw = "True" if ok else "False"
        return Result(status="ok", type="Bool", repr=raw, normalized=raw)

    def _set_components(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        tensor = str(args["tensor"])
        bases = [str(b) for b in args["bases"]]
        _api.set_components(tensor, list(args["array"]), bases, weight=int(args.get("weight", 0)))
        repr_str = f"CTensor({tensor}, {bases})"
        return Result(status="ok", type="Handle", repr=repr_str, normalized=repr_str)

    def _get_components(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        ct = _api.get_components(str(args["tensor"]), [str(b) for b in args["bases"]])
        raw = ct._julia_str or repr(ct)
        return Result(status="ok", type="Expr", repr=raw, normalized=raw)

    def _component_value(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        val = _api.component_value(
            str(args["tensor"]),
            [int(i) for i in args["indices"]],
            [str(b) for b in args["bases"]],
        )
        raw = str(val)
        return Result(status="ok", type="Scalar", repr=raw, normalized=raw)

    def _ctensor_q(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        ok = _api.ctensor_q(str(args["tensor"]), *[str(b) for b in args["bases"]])
        raw = "True" if ok else "False"
        return Result(status="ok", type="Bool", repr=raw, normalized=raw)

    def _to_basis(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        ct = _api.to_basis(str(args["expression"]), str(args["basis"]))
        raw = ct._julia_str or repr(ct)
        return Result(status="ok", type="Expr", repr=raw, normalized=raw)

    def _from_basis(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        raw = _api.from_basis(str(args["tensor"]), [str(b) for b in args["bases"]])
        return Result(status="ok", type="Expr", repr=raw, normalized=raw)

    def _trace_basis_dummy(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        ct = _api.trace_basis_dummy(str(args["tensor"]), [str(b) for b in args["bases"]])
        raw = ct._julia_str or repr(ct)
        return Result(status="ok", type="Expr", repr=raw, normalized=raw)

    def _christoffel(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        ct = _api.christoffel(
            str(args["metric"]),
            str(args["basis"]),
            metric_derivs=args.get("metric_derivs"),
        )
        raw = repr(ct)
        return Result(status="ok", type="Expr", repr=raw, normalized=raw)

    # ------------------------------------------------------------------
    # xTras actions
    # ------------------------------------------------------------------

    def _collect_tensors(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.collect_tensors(str(args["expression"]))
        return Result(status="ok", type="String", repr=s, normalized=s)

    def _all_contractions(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        items = _api.all_contractions(str(args["expression"]), str(args["metric"]))
        s = ", ".join(items) if len(items) > 1 else (items[0] if items else "")
        return Result(status="ok", type="String", repr=s, normalized=s)

    def _symmetry_of(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.symmetry_of(str(args["expression"]))
        return Result(status="ok", type="String", repr=s, normalized=s)

    def _make_trace_free(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.make_trace_free(str(args["expression"]), str(args["metric"]))
        return Result(status="ok", type="String", repr=s, normalized=s)

    def _riemann_simplify(self, args: dict[str, Any]) -> Result:
        import xact.api as _api

        s = _api.riemann_simplify(
            str(args["expression"]), str(args["covd"]), level=int(args.get("level", 6))
        )
        return Result(status="ok", type="String", repr=s, normalized=_normalize(s))

    def _execute_expr(self, wolfram_expr: str) -> Result:
        julia_expr = _wl_to_jl(wolfram_expr)
        julia_expr = _postprocess_dimino(julia_expr)
        _bind_fresh_symbols(self._jl, julia_expr)
        _bind_wl_atoms(self._jl, julia_expr)
        try:
            # NOTE: seval with translator output — safety relies on _wl_to_jl
            # producing well-formed Julia. Will be addressed when translator is hardened.
            val = timed_seval(self._jl, julia_expr, label="execute_expr")
            # PythonCall adds "Julia: " prefix for custom types inside containers.
            # Strip it to get clean WL-compatible repr.
            raw = str(val).replace("Julia: ", "")
            return Result(
                status="ok",
                type="Expr",
                repr=raw,
                normalized=_normalize(raw),
            )
        except Exception as exc:
            return Result(
                status="error",
                type="",
                repr="",
                normalized="",
                error=str(exc),
            )

    def _execute_assert(self, wolfram_condition: str, message: str | None) -> Result:
        # Check for tensor expression string comparisons first:
        # "$once == $twice" after binding substitution becomes two tensor expr strings.
        # These should be compared as strings, not evaluated as Julia.
        tensor_cmp = _try_tensor_string_comparison(wolfram_condition)
        if tensor_cmp is not None:
            passed, lhs_str, rhs_str = tensor_cmp
            if passed:
                return Result(status="ok", type="Bool", repr="True", normalized="True")
            msg = message or f"Assertion failed: {wolfram_condition!r}"
            return Result(
                status="error",
                type="Bool",
                repr=str(passed),
                normalized=str(passed),
                error=msg,
            )

        # Check for tensor // ToCanonical === value patterns (with optional || prefix).
        # These arise when the condition substitutes a tensor result and then
        # applies ToCanonical postfix, e.g.: "(Conv[coa] - Conv[coa]) // ToCanonical === 0"
        # Also handles: "TensorQ[$r] || ($r - Conw[-coa]) // ToCanonical === 0"
        to_canon_cmp = _try_to_canonical_comparison(wolfram_condition, self._jl)
        if to_canon_cmp is not None:
            passed, actual, expected = to_canon_cmp
            if passed:
                return Result(status="ok", type="Bool", repr="True", normalized="True")
            msg = message or f"Assertion failed: {wolfram_condition!r}"
            return Result(
                status="error",
                type="Bool",
                repr=str(passed),
                normalized=str(passed),
                error=msg,
            )

        julia_cond = _wl_to_jl(wolfram_condition)
        # If preprocessing reduced the condition to a trivially true "X == X" form,
        # return True immediately without calling Julia (avoids issues with unbound
        # symbol atoms that cannot be called as functions).
        if _is_trivially_equal(julia_cond):
            return Result(status="ok", type="Bool", repr="True", normalized="True")
        _bind_fresh_symbols(self._jl, julia_cond)
        _bind_wl_atoms(self._jl, julia_cond)
        try:
            # NOTE: seval with translator output — safety relies on _wl_to_jl
            # producing well-formed Julia. Will be addressed when translator is hardened.
            val = timed_seval(self._jl, julia_cond, label="execute_assert")
            passed = val is True or str(val).lower() == "true"
            if passed:
                return Result(status="ok", type="Bool", repr="True", normalized="True")
            # Assertion evaluated but returned false — this is a valid result,
            # not an error. Return status="ok" so snapshot comparators can
            # compare the "False" result against oracle snapshots.
            return Result(
                status="ok",
                type="Bool",
                repr="False",
                normalized="False",
            )
        except Exception as exc:
            # Julia evaluation threw — this is an infrastructure failure, not a
            # semantically false assertion.  Surface the error so callers (runner,
            # snapshot comparator) can distinguish crashes from logical failures.
            _log.warning(
                "Assert seval raised %s: %s (condition: %s)",
                type(exc).__name__,
                exc,
                wolfram_condition,
            )
            return Result(
                status="error",
                type="Bool",
                repr="False",
                normalized="False",
                error=f"{type(exc).__name__}: {exc}",
                diagnostics={"exception_type": type(exc).__name__},
            )

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def normalize(self, expr: str) -> NormalizedExpr:
        return NormalizedExpr(_normalize(expr))

    def equals(
        self,
        a: NormalizedExpr,
        b: NormalizedExpr,
        mode: EqualityMode,
        ctx: _JuliaContext | None = None,
    ) -> bool:
        # Tier 1 normalized string comparison only; semantic/numeric require oracle
        return a == b

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_properties(self, expr: str, ctx: _JuliaContext | None = None) -> dict[str, Any]:
        return {}

    def get_version(self) -> VersionInfo:
        if self._jl is None:
            try:
                self._ensure_ready()
            except AdapterError:
                pass
        return VersionInfo(
            cas_name="Julia",
            cas_version=self._julia_version,
            adapter_version=f"0.1.0 (xAct {self._xact_version})",
        )

    def get_tensor_context(self, ctx: _JuliaContext, rng: Any | None = None) -> Any:
        """Build a TensorContext from the manifold/tensor state in *ctx*.

        Returns a :class:`~sxact.compare.sampling.TensorContext` populated with
        random component arrays for all tensors and metrics defined in this context.
        Pass the result to :func:`~sxact.compare.sampling.sample_numeric` for
        Tier 3 numeric comparison.

        Args:
            ctx: The active context (must have been used with ``DefManifold`` /
                 ``DefMetric`` / ``DefTensor`` calls).
            rng: Optional NumPy random generator for reproducibility.

        Returns:
            A ``TensorContext`` ready for substitution.
        """
        from sxact.compare.sampling import build_tensor_context

        return build_tensor_context(ctx._manifolds, ctx._metrics, ctx._tensors, rng=rng)
