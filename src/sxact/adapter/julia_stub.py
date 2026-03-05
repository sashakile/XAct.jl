"""JuliaAdapter — concrete adapter backed by Julia XCore via juliacall.

Uses the Python xCore runtime (_runtime.py) to lazily initialise Julia and
load XCore.jl once per process.  Evaluates Julia expressions translated from
the TOML test vocabulary (Wolfram → Julia syntax).

Per-file isolation is achieved by resetting XCore global state on teardown:
  - _symbol_registry
  - per-package name lists (xCoreNames, xTensorNames, …)
  - _upvalue_store
  - _xtensions

Actions that require xTensor (DefManifold, DefMetric, DefTensor,
ToCanonical, Contract, Simplify) return error Results since xTensor is not
yet ported to Julia.
"""

from __future__ import annotations

from typing import Any

from sxact.adapter.base import (
    AdapterError,
    EqualityMode,
    NormalizedExpr,
    TestAdapter,
    VersionInfo,
)
from sxact.normalize import normalize as _normalize
from sxact.oracle.result import Result


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class _JuliaContext:
    """Opaque per-file context for JuliaAdapter."""

    def __init__(self) -> None:
        self.alive: bool = True


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class JuliaAdapter(TestAdapter[_JuliaContext]):
    """Concrete adapter for the Julia XCore backend.

    Evaluates Julia expressions translated from the TOML action vocabulary.
    Actions that require xTensor return error Results.
    """

    # Actions that require xTensor (not yet ported to Julia)
    _XTENSOR_ACTIONS = frozenset(
        {"DefManifold", "DefMetric", "DefTensor", "ToCanonical", "Contract", "Simplify"}
    )

    # XCore module-level mutable state to reset on teardown
    _RESET_STMTS = [
        "empty!(XCore._symbol_registry)",
        "empty!(XCore._upvalue_store)",
        "empty!(XCore._xtensions)",
        "empty!(XCore.xPermNames)",
        "empty!(XCore.xTensorNames)",
        "empty!(XCore.xCoreNames)",
        "empty!(XCore.xTableauNames)",
        "empty!(XCore.xCobaNames)",
        "empty!(XCore.InvarNames)",
        "empty!(XCore.HarmonicsNames)",
        "empty!(XCore.xPertNames)",
        "empty!(XCore.SpinorsNames)",
        "empty!(XCore.EMNames)",
    ]

    def __init__(self) -> None:
        self._jl: Any = None
        self._julia_version: str = "unknown"

    def _ensure_ready(self) -> None:
        if self._jl is not None:
            return
        try:
            from sxact.xcore._runtime import get_julia
            self._jl = get_julia()
            raw = self._jl.seval("string(VERSION)")
            self._julia_version = str(raw).strip()
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
                pass  # teardown must not raise

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, ctx: _JuliaContext, action: str, args: dict[str, Any]) -> Result:
        if action not in self.supported_actions():
            raise ValueError(f"Unknown action: {action!r}")

        if action in self._XTENSOR_ACTIONS:
            return Result(
                status="error",
                type="",
                repr="",
                normalized="",
                error=f"action {action!r} requires xTensor (not yet ported to Julia)",
            )

        self._ensure_ready()

        if action == "Evaluate":
            return self._execute_expr(args.get("expression", ""))
        if action == "Assert":
            return self._execute_assert(
                args.get("condition", ""),
                args.get("message"),
            )
        # Unreachable if supported_actions() is correct
        return Result(
            status="error", type="", repr="", normalized="",
            error=f"unhandled action: {action!r}",
        )

    def _execute_expr(self, wolfram_expr: str) -> Result:
        julia_expr = _wl_to_jl(wolfram_expr)
        try:
            val = self._jl.seval(julia_expr)
            raw = str(val)
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
        julia_cond = _wl_to_jl(wolfram_condition)
        try:
            val = self._jl.seval(julia_cond)
            passed = val is True or str(val).lower() == "true"
            if passed:
                return Result(status="ok", type="Bool", repr="True", normalized="True")
            msg = message or f"Assertion failed: {wolfram_condition}"
            return Result(
                status="error",
                type="Bool",
                repr=str(val),
                normalized=str(val),
                error=msg,
            )
        except Exception as exc:
            return Result(
                status="error",
                type="Bool",
                repr="",
                normalized="",
                error=str(exc),
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
            adapter_version="0.1.0",
        )


# ---------------------------------------------------------------------------
# Wolfram → Julia syntax translator
# ---------------------------------------------------------------------------

_WL_KEYWORDS: dict[str, str] = {
    "True": "true",
    "False": "false",
    "Null": "nothing",
}


def _wl_to_jl(expr: str) -> str:
    """Translate basic Wolfram xCore notation to Julia syntax.

    Handles:
    - f[args] → f(args)       (function application)
    - {a, b}  → [a, b]        (list literals)
    - ===     → ==             (structural equality → value equality)
    - True / False / Null → true / false / nothing

    Abstract Wolfram symbols used as atoms (e.g. ``a``, ``b``) are left
    as-is; they will cause Julia ``UndefVarError`` for tests that rely on
    Wolfram's symbolic algebra — those tests correctly fail in Julia.
    """
    # Replace === before the character pass so the placeholder is unambiguous
    expr = expr.replace("===", "\x00")

    out: list[str] = []
    i = 0
    n = len(expr)
    stack: list[str] = []  # "call" or "list"

    while i < n:
        ch = expr[i]

        # String literals — pass through verbatim (no translation inside)
        if ch == '"':
            j = i + 1
            while j < n:
                if expr[j] == '\\':
                    j += 2
                    continue
                if expr[j] == '"':
                    break
                j += 1
            out.append(expr[i:j + 1])
            i = j + 1
            continue

        # Identifier: may be a keyword-mapped name or a function call
        if ch.isalpha() or ch == '_':
            j = i
            while j < n and (expr[j].isalnum() or expr[j] == '_'):
                j += 1
            name = expr[i:j]
            if j < n and expr[j] == '[':
                # Function call: emit name( and push "call" context
                out.append(name + '(')
                stack.append('call')
                i = j + 1
            else:
                out.append(_WL_KEYWORDS.get(name, name))
                i = j
            continue

        # List open {
        if ch == '{':
            out.append('[')
            stack.append('list')
            i += 1
            continue

        # List close }
        if ch == '}':
            out.append(']')
            if stack and stack[-1] == 'list':
                stack.pop()
            i += 1
            continue

        # Close bracket ] — closes a function call or a bare list
        if ch == ']':
            if stack and stack[-1] == 'call':
                out.append(')')
                stack.pop()
            else:
                out.append(']')
                if stack and stack[-1] == 'list':
                    stack.pop()
            i += 1
            continue

        # Bare open bracket [ (shouldn't appear in Wolfram, but handle safely)
        if ch == '[':
            out.append('[')
            stack.append('list')
            i += 1
            continue

        # Equality placeholder (was ===)
        if ch == '\x00':
            out.append('==')
            i += 1
            continue

        out.append(ch)
        i += 1

    return ''.join(out)
