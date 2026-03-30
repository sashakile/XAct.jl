"""Comparison and assertion helpers for JuliaAdapter.

Module-level functions that handle tensor expression string comparisons,
ToCanonical pattern matching, numerical tolerance interception, xPerm
preprocessing, and Wolfram-atom symbol binding.

Extracted from julia_stub.py for modularity (sxAct-pgjn).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from sxact.adapter.julia_names import (
    TENSOR_Q as _JN_TENSOR_Q,
)
from sxact.adapter.julia_names import (
    TO_CANONICAL as _JN_TO_CANONICAL,
)
from sxact.normalize import normalize as _normalize
from sxact.oracle.result import Result
from sxact.translate.wl_to_julia import (
    is_tensor_expr as _is_tensor_expr,
)
from sxact.translate.wl_to_julia import (
    top_level_split as _top_level_split,
)
from xact._bridge import (
    jl_call,
    jl_str,
    jl_sym,
)

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tensor expression string comparison
# ---------------------------------------------------------------------------


def try_tensor_string_comparison(condition: str) -> tuple[bool, str, str] | None:
    """If `condition` is a tensor-expression string comparison, return (passed, lhs, rhs).

    Handles: "expr1 == expr2" where one or both sides are tensor expressions.
    Returns None if not a tensor expression comparison (use Julia eval instead).
    """
    # Only handle conditions of the form "lhs == rhs" (exactly one == that is not ===)
    # Split on " == " at top level
    parts = _top_level_split(condition, " == ")
    if len(parts) != 2:
        return None
    lhs, rhs = parts[0].strip(), parts[1].strip()
    # If either side is a tensor expression, do string comparison
    if _is_tensor_expr(lhs) or _is_tensor_expr(rhs):
        # Normalize both sides: strip whitespace, treat "0" == "0"
        lhs_n = _normalize(lhs)
        rhs_n = _normalize(rhs)
        return (lhs_n == rhs_n, lhs_n, rhs_n)
    return None


# ---------------------------------------------------------------------------
# ToCanonical pattern matching
# ---------------------------------------------------------------------------


def try_to_canonical_comparison(condition: str, jl: Any) -> tuple[bool, str, str] | None:
    """Handle conditions of the form: tensor_expr // ToCanonical === value.

    Also handles OR conditions: "clause1 || tensor_expr // ToCanonical === value"
    where ANY clause being true makes the whole condition true.

    Returns (passed, actual, expected) or None if the pattern doesn't match.
    """
    # If condition has top-level "||", split and try each part
    or_parts = _top_level_split(condition, " || ")
    if len(or_parts) > 1:
        any_matched = False
        # Try each clause; if any returns (True, ...) the whole thing passes
        for part in or_parts:
            part = part.strip()
            # Try ToCanonical comparison
            result = _try_single_to_canonical_comparison(part, jl)
            if result is not None:
                any_matched = True
                if result[0]:
                    return result
            # Try TensorQ[expr] — if expr is a tensor expression, check if tensor is registered
            tq_result = _try_tensor_q(part, jl)
            if tq_result is not None:
                any_matched = True
                if tq_result[0]:
                    return tq_result
            # Try simple string comparison
            tc_result = try_tensor_string_comparison(part)
            if tc_result is not None:
                any_matched = True
                if tc_result[0]:
                    return tc_result
        if any_matched:
            return (False, "", "")
        return None

    return _try_single_to_canonical_comparison(condition, jl)


_TENSOR_Q_RE = re.compile(r"^TensorQ\[(\w+)(?:\[.*\])?\]$")


def _try_tensor_q(condition: str, jl: Any) -> tuple[bool, str, str] | None:
    """Handle TensorQ[TensorExpr] conditions.

    If the condition is TensorQ[Name[...]] or TensorQ[Name], checks if Name
    is a registered tensor via XTensor.TensorQ.

    Returns (True, "True", "True") if the tensor is registered, else None.
    """
    m = _TENSOR_Q_RE.match(condition.strip())
    if m is None:
        return None
    tensor_name = m.group(1)
    try:
        val = jl_call(jl, _JN_TENSOR_Q, jl_sym(tensor_name, "tensor name"))
        if val is True or str(val).lower() == "true":
            return (True, "True", "True")
        return (False, "False", "True")
    except Exception:
        return None


def _try_single_to_canonical_comparison(condition: str, jl: Any) -> tuple[bool, str, str] | None:
    """Handle a single (no ||) condition of the form: tensor_expr // ToCanonical === value."""
    # Pattern: something // ToCanonical === something_else
    # Split on " === " first to find the comparison value
    parts_strict = _top_level_split(condition, " === ")
    if len(parts_strict) != 2:
        return None

    lhs_raw, rhs_raw = parts_strict[0].strip(), parts_strict[1].strip()

    # LHS must contain "// ToCanonical" at the top level
    lhs_parts = _top_level_split(lhs_raw, " // ToCanonical")
    if len(lhs_parts) < 2:
        lhs_parts = _top_level_split(lhs_raw, "// ToCanonical")
    if len(lhs_parts) < 2:
        return None

    tensor_expr = lhs_parts[0].strip()
    # Strip outer parens from tensor_expr
    if tensor_expr.startswith("(") and tensor_expr.endswith(")"):
        tensor_expr = tensor_expr[1:-1].strip()

    # Must be a tensor expression
    if not _is_tensor_expr(tensor_expr):
        return None

    # Call XTensor.ToCanonical on the tensor expression
    try:
        result = str(jl_call(jl, _JN_TO_CANONICAL, jl_str(tensor_expr)))
    except Exception:
        return None

    # Compare result to rhs
    expected = rhs_raw.strip()
    actual_n = _normalize(result)
    expected_n = _normalize(expected)
    return (actual_n == expected_n, actual_n, expected_n)


# ---------------------------------------------------------------------------
# xPerm preprocessing
# ---------------------------------------------------------------------------

# Regex matching fresh property-test symbols generated by property_runner.py.
# Pattern: "px" + one-or-more uppercase letters + generator name (lowercase) + suffix (lowercase).
# Examples: pxBAGsbq, pxKBIsbr, pxBKYsbt, pxLYPabu
_FRESH_SYMBOL_RE = re.compile(r"\bpx[A-Z]+[a-z]+\b")

# Regex matching the property runner's numerical_tolerance comparison expression.
_NUMERICAL_TOL_RE = re.compile(r"^Max\[Abs\[Flatten\[N\[(.+)\]\]\]\]$", re.DOTALL)

# XTensor functions that take a string argument and return a string result.
_XPERM_STRING_FUNCS = ("ToCanonical", "Contract")


def preprocess_xperm_calls(jl: Any, expr: str) -> str:
    """Recursively evaluate ToCanonical[...] and Contract[...] calls in expr.

    Replaces each such call with its Julia string result so that the
    remaining expression can be passed to XTensor.ToCanonical for final
    canonicalization.
    """
    _MAX_PREPROCESS_ITERS = 50
    for func_name in _XPERM_STRING_FUNCS:
        func_prefix = func_name + "["
        iters = 0
        while func_prefix in expr:
            iters += 1
            if iters > _MAX_PREPROCESS_ITERS:
                _log.warning(
                    "Exceeded %d iterations preprocessing %s calls; breaking",
                    _MAX_PREPROCESS_ITERS,
                    func_name,
                )
                break
            pos = expr.find(func_prefix)
            start = pos + len(func_prefix)
            depth = 1
            i = start
            while i < len(expr) and depth > 0:
                if expr[i] == "[":
                    depth += 1
                elif expr[i] == "]":
                    depth -= 1
                i += 1
            inner = expr[start : i - 1]
            # Recursively preprocess the inner expression first
            inner_processed = preprocess_xperm_calls(jl, inner)
            try:
                result = str(jl_call(jl, f"XTensor.{func_name}", jl_str(inner_processed)))
            except Exception:
                # If preprocessing fails, leave the call in place
                break
            expr = expr[:pos] + result + expr[i:]
    return expr


def try_numerical_tolerance_via_canonical(jl: Any, wolfram_expr: str) -> Result | None:
    """Intercept Max[Abs[Flatten[N[(lhs) - (rhs)]]]] for tensor expressions.

    The property runner generates this pattern for numerical_tolerance checks.
    For the Julia symbolic adapter, we instead apply ToCanonical to the
    difference expression.  If the result is "0" (the tensors are equal by
    symmetry), return "0.0" (passes the < tolerance check).

    Returns None if the expression doesn't match the pattern or if we cannot
    determine a canonical result.
    """
    m = _NUMERICAL_TOL_RE.match(wolfram_expr.strip())
    if not m:
        return None
    inner = m.group(1).strip()
    if not _is_tensor_expr(inner):
        return None

    # Use inner directly as diff_expr.
    # The property runner always generates (lhs) - (rhs), and XTensor._parse_sum!
    # has paren-depth tracking so it handles nested paren groups correctly.
    # Stripping parens from a multi-term rhs would lose sign distribution
    # (e.g. "(T+S) - (S+T)" → "T+S - S+T = 2T" instead of 0).
    diff_expr = inner

    # Preprocess any nested ToCanonical/Contract calls
    try:
        preprocessed = preprocess_xperm_calls(jl, diff_expr)
    except Exception:
        preprocessed = diff_expr

    # Apply ToCanonical to the whole difference
    try:
        result = str(jl_call(jl, _JN_TO_CANONICAL, jl_str(preprocessed)))
    except Exception:
        return None

    if result == "0":
        return Result(status="ok", type="Float", repr="0.0", normalized="0.0")

    # Try to interpret as a numeric value (e.g. if all terms cancel to a number)
    try:
        float(result)
        return Result(status="ok", type="Float", repr=result, normalized=result)
    except ValueError:
        pass

    return None


# ---------------------------------------------------------------------------
# Symbol binding
# ---------------------------------------------------------------------------

# Julia reserved keywords that must NOT be re-bound as Symbols.
_JULIA_KEYWORDS: frozenset[str] = frozenset(
    {
        "abstract",
        "baremodule",
        "begin",
        "break",
        "catch",
        "const",
        "continue",
        "do",
        "else",
        "elseif",
        "end",
        "export",
        "false",
        "finally",
        "for",
        "function",
        "global",
        "if",
        "import",
        "in",
        "isa",
        "let",
        "local",
        "macro",
        "module",
        "mutable",
        "new",
        "nothing",
        "primitive",
        "quote",
        "return",
        "struct",
        "true",
        "try",
        "type",
        "using",
        "where",
        "while",
    }
)

# Identifiers that are known Julia built-in names and should not be shadowed.
_JULIA_BUILTINS: frozenset[str] = frozenset(
    {
        "length",
        "unique",
        "string",
        "println",
        "print",
        "show",
        "collect",
        "filter",
        "map",
        "push",
        "pop",
        "sort",
        "sum",
        "prod",
        "any",
        "all",
        "issubset",
        "in",
        "vcat",
        "hcat",
        "first",
        "last",
        "isempty",
        "empty",
        "haskey",
        "get",
        "Dict",
        "Set",
        "Vector",
        "Matrix",
        "Tuple",
        "Array",
        "Int",
        "Float64",
        "Bool",
        "Symbol",
        "String",
        "Expr",
        "Nothing",
    }
)

# Mapping from WL built-in head names to the Julia operator Symbol they correspond to.
_WL_OP_TO_JULIA: dict[str, str] = {
    "Plus": "+",
    "Times": "*",
    "Power": "^",
    "Subtract": "-",
    "Divide": "/",
}


def bind_wl_atoms(jl: Any, julia_expr: str) -> None:
    """Bind WL atom-like identifiers in *julia_expr* as Julia Symbols in Main.

    Scans the expression for identifiers that:
    1. Are NOT Julia keywords or known built-in names
    2. Are NOT followed by ``(`` (i.e., not function calls)
    3. Are NOT inside string literals

    These are treated as WL symbolic atoms and pre-bound as Julia Symbols
    (``Main.x = :x``) so that functions like ``SubHead``, ``NoPattern``,
    ``MemberQ``, and ``FindSymbols`` receive the right types.

    This is idempotent: re-binding an already-bound symbol is harmless.
    """
    # Scan token by token, skipping string literals
    expr = julia_expr
    n = len(expr)
    i = 0
    candidates: set[str] = set()
    while i < n:
        ch = expr[i]
        # Skip string literals
        if ch == '"':
            i += 1
            while i < n:
                if expr[i] == "\\":
                    i += 2
                    continue
                if expr[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        # Identifier token
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (expr[j].isalnum() or expr[j] == "_"):
                j += 1
            name = expr[i:j]
            # Skip if followed by ( — that's a function call, not an atom
            k = j
            while k < n and expr[k] == " ":
                k += 1
            if k < n and expr[k] == "(":
                i = j
                continue
            # Skip Julia keywords and known built-ins
            if name in _JULIA_KEYWORDS or name in _JULIA_BUILTINS:
                i = j
                continue
            # Skip numeric literals start (shouldn't happen here but be safe)
            if name[0].isdigit():
                i = j
                continue
            candidates.add(name)
            i = j
            continue
        i += 1

    for sym in candidates:
        try:
            # Only bind if the symbol is not already defined in Julia Main.
            # This prevents overwriting Perm/tensor objects defined during setup.
            already_defined = bool(jl.seval(f"isdefined(Main, :{sym})"))
            if already_defined:
                continue
            if sym in _WL_OP_TO_JULIA:
                # WL operator head name (e.g. Plus) → Julia operator Symbol (e.g. :+)
                julia_sym = _WL_OP_TO_JULIA[sym]
                jl.seval(f'Main.eval(:(global {sym} = Symbol("{julia_sym}")))')
            else:
                jl.seval(f"Main.eval(:(global {sym} = :{sym}))")
        except Exception:
            pass  # If binding fails, skip — symbol may already be defined correctly


def bind_fresh_symbols(jl: Any, julia_expr: str) -> None:
    """Bind any fresh property-test symbols found in *julia_expr* as Julia Symbols in Main.

    The property runner generates names like ``pxBAGsbq`` (lowercase-start, prefixed
    with ``px`` + uppercase block).  These are unknown Julia identifiers and cause
    ``UndefVarError`` if evaluated directly.  We pre-bind each one as the corresponding
    Julia Symbol (``Main.pxBAGsbq = :pxBAGsbq``) so XCore functions that accept
    ``Symbol`` arguments receive the right value.
    """
    for sym in _FRESH_SYMBOL_RE.findall(julia_expr):
        try:
            already_defined = bool(jl.seval(f"isdefined(Main, :{sym})"))
            if not already_defined:
                jl.seval(f"Main.eval(:(global {sym} = :{sym}))")
        except Exception:
            pass
