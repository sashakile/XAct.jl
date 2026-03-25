"""Wolfram Language → Julia syntax translator.

Pure string-to-string translation of Wolfram xCore notation to Julia syntax.
No Julia runtime dependency — this module only does text transformation.

Extracted from sxact.adapter.julia_stub (sxAct-y5f1).
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WL_KEYWORDS: dict[str, str] = {
    "True": "true",
    "False": "false",
    "Null": "nothing",
    "Length": "length",
}

# Regex that matches tensor index notation.
# Two patterns combined (either is sufficient):
#   1. `-[a-z]`         — covariant index: Sps[-spa], Riemann[-a,-b]
#   2. `\w+\[[a-z]{2,}` — contravariant multi-letter index: Conv[coa], QGTorsion[qga,...]
# xPerm uses integers, single-letter lowercase, or capitalized names — none match.
_TENSOR_EXPR_RE = re.compile(r"-[a-z]|\w+\[[a-z]{2,}")

_SCHREIER_ORBIT_RE = re.compile(r"SchreierOrbit\[([^,\[]+),\s*GenSet\[([^\]]+)\],\s*([^\]]+)\]")
_SCHREIER_ORBITS_RE = re.compile(r"SchreierOrbits\[GenSet\[([^\]]+)\],\s*([^\]]+)\]")

# Post-process Dimino after WL→Julia translation.
# Matches: Dimino(GenSet(g1, g2, ...))
# Captures the comma-separated generator names after Julia translation.
_DIMINO_GENSET_POST_RE = re.compile(r"\bDimino\(GenSet\(([^)]+)\)\)")

# WL pattern notation: strip Blank/BlankSequence/BlankNullSequence suffixes.
_WL_PATTERN_RE = re.compile(r"\b([a-z][a-zA-Z0-9]*)_+(?![a-z])(?:[A-Z]\w*)?")

_PREFIX_AT_RE = re.compile(r"(\b[A-Za-z_]\w*)\s*@(?!@)")

# WL machine-precision backtick notation: 1.234`5.678\ Second → 1.234
_WL_BACKTICK_RE = re.compile(r"(\d+\.\d+)`[\d.]*\\?\s*\w*")

# WL list destructuring: {a, b} = expr  →  (a, b) = expr
_WL_DESTRUCT_RE = re.compile(r"\{([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\}\s*(=)(?!=)")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_tensor_expr(expr: str) -> bool:
    """True if the expression looks like a tensor algebra expression (not a Julia predicate)."""
    return bool(_TENSOR_EXPR_RE.search(expr))


def top_level_split(s: str, sep: str) -> list[str]:
    """Split `s` on `sep` but only at depth 0 (not inside brackets or strings)."""
    parts: list[str] = []
    depth = 0
    in_string = False
    string_char = ""
    current: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch in ('"', "'") and not in_string:
            in_string = True
            string_char = ch
            current.append(ch)
        elif in_string and ch == string_char:
            in_string = False
            current.append(ch)
        elif in_string:
            current.append(ch)
        elif ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif s[i : i + len(sep)] == sep and depth == 0:
            parts.append("".join(current))
            current = []
            i += len(sep)
            continue
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return parts


def is_trivially_equal(julia_cond: str) -> bool:
    """Return True if *julia_cond* is syntactically of the form ``X == X``."""
    julia_cond = julia_cond.strip()
    parts = top_level_split(julia_cond, " == ")
    if len(parts) == 2:
        return parts[0].strip() == parts[1].strip()
    return False


def postprocess_dimino(julia_expr: str) -> str:
    """Inject name registry into Dimino(GenSet(...)) calls (post WL→Julia translation).

    Dimino(GenSet(g1, g2, ...)) → Dimino(GenSet(g1, g2, ...), ["g1"=>g1, "g2"=>g2, ...])
    """

    def replace_dimino(m: re.Match[str]) -> str:
        gens_str = m.group(1).strip()
        gen_names = [g.strip() for g in gens_str.split(",")]
        pairs = ", ".join(f'"{nm}"=>{nm}' for nm in gen_names)
        return f"Dimino(GenSet({gens_str}), [{pairs}])"

    return _DIMINO_GENSET_POST_RE.sub(replace_dimino, julia_expr)


def wl_to_jl(expr: str) -> str:
    """Translate basic Wolfram xCore notation to Julia syntax.

    Handles:
    - f[args] → f(args)          (function application)
    - {a, b}  → [a, b]           (list literals)
    - ===     → ==                (structural equality → value equality)
    - True / False / Null → true / false / nothing
    - expr // f → f(expr)         (Wolfram postfix application)
    - $Name   → Name              (dollar-prefix strip)
    - SubsetQ[A, B] → issubset(B, A)  (note: args reversed in Julia)
    - \\[Equal] → ==              (Wolfram Unicode Equal operator)
    - SchreierOrbit[pt, GenSet[g1,...], n] → SchreierOrbit(pt, [...], n, ["g1",...])
    - x_, x_Type patterns → x    (WL pattern notation stripped)
    """
    expr = _preprocess_subhead(expr)
    expr = _preprocess_wl_patterns(expr)
    expr = _preprocess_nopattern(expr)
    expr = _preprocess_prefix_at(expr)
    expr = _preprocess_apply_op(expr)
    expr = _preprocess_schreier_orbit(expr)
    expr = _preprocess_timing_destruct(expr)
    expr = _WL_BACKTICK_RE.sub(r"\1", expr)

    expr = expr.replace("\\[Equal]", "==")
    expr = expr.replace(":>", "=>")
    expr = re.sub(r"(?<![=-])->(?!>)", "=>", expr)
    expr = _rewrite_postfix(expr)
    expr = re.sub(r"\$([A-Za-z_]\w*)", r"\1", expr)
    expr = expr.replace("===", "\x00")

    out: list[str] = []
    i = 0
    n = len(expr)
    stack: list[str] = []

    while i < n:
        ch = expr[i]

        # String literals — pass through verbatim
        if ch == '"':
            j = i + 1
            while j < n:
                if expr[j] == "\\":
                    j += 2
                    continue
                if expr[j] == '"':
                    break
                j += 1
            out.append(expr[i : j + 1])
            i = j + 1
            continue

        # Identifier: may be a keyword-mapped name or a function call
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (expr[j].isalnum() or expr[j] in ("_", "\u2040")):
                j += 1
            name = expr[i:j]
            if j < n and expr[j] == "[":
                if name == "SubsetQ":
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    inner = expr[j + 1 : k - 1]
                    parts = top_level_split(inner, ",")
                    if len(parts) == 2:
                        a_jl = wl_to_jl(parts[0].strip())
                        b_jl = wl_to_jl(parts[1].strip())
                        out.append(f"issubset({b_jl}, {a_jl})")
                    else:
                        out.append(f"issubset({wl_to_jl(inner)})")
                    i = k
                elif name == "Cases":
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    inner = expr[j + 1 : k - 1]
                    parts = top_level_split(inner, ",")
                    if (
                        len(parts) == 3
                        and parts[1].strip() == "_Symbol"
                        and parts[2].strip() == "Infinity"
                    ):
                        out.append(f"FindSymbols({wl_to_jl(parts[0].strip())})")
                    else:
                        out.append(f"Cases({wl_to_jl(inner)})")
                    i = k
                elif name == "StringQ":
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    inner = wl_to_jl(expr[j + 1 : k - 1].strip())
                    out.append(f"isa({inner}, String)")
                    i = k
                elif name == "StringLength":
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    inner = wl_to_jl(expr[j + 1 : k - 1].strip())
                    out.append(f"length({inner})")
                    i = k
                elif name == "Catch":
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    inner = wl_to_jl(expr[j + 1 : k - 1].strip())
                    out.append(f"try {inner} catch e nothing end")
                    i = k
                elif name == "ClearAll":
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    out.append("nothing")
                    i = k
                elif name in ("Rule", "RuleDelayed"):
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    inner = expr[j + 1 : k - 1]
                    parts = top_level_split(inner, ",")
                    if len(parts) == 2:
                        lhs = wl_to_jl(parts[0].strip())
                        rhs = wl_to_jl(parts[1].strip())
                        out.append(f"({lhs} => {rhs})")
                    else:
                        out.append(f"Rule({wl_to_jl(inner)})")
                    i = k
                elif name == "Head":
                    depth2 = 1
                    k = j + 1
                    while k < n and depth2 > 0:
                        if expr[k] == "[":
                            depth2 += 1
                        elif expr[k] == "]":
                            depth2 -= 1
                        k += 1
                    inner = wl_to_jl(expr[j + 1 : k - 1].strip())
                    out.append(f"typeof({inner})")
                    i = k
                else:
                    translated = WL_KEYWORDS.get(name, name)
                    out.append(translated + "(")
                    stack.append("call")
                    i = j + 1
            else:
                translated = WL_KEYWORDS.get(name, name)
                if "\u2040" in translated:
                    out.append(f'Symbol("{translated}")')
                else:
                    out.append(translated)
                i = j
            continue

        if ch == "{":
            out.append("[")
            stack.append("list")
            i += 1
            continue

        if ch == "}":
            out.append("]")
            if stack and stack[-1] == "list":
                stack.pop()
            i += 1
            continue

        if ch == "]":
            if stack and stack[-1] == "call":
                out.append(")")
                stack.pop()
            else:
                out.append("]")
                if stack and stack[-1] == "list":
                    stack.pop()
            i += 1
            continue

        if ch == "[":
            out.append("[")
            stack.append("list")
            i += 1
            continue

        if ch == "\x00":
            out.append("==")
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


# ---------------------------------------------------------------------------
# Internal preprocessing helpers
# ---------------------------------------------------------------------------


def _rewrite_postfix(expr: str) -> str:
    """Rewrite Wolfram postfix // operator: 'expr // f' → 'f(expr)'."""
    while True:
        depth = 0
        pos = -1
        for i, ch in enumerate(expr):
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "/" and depth == 0 and i + 1 < len(expr) and expr[i + 1] == "/":
                pos = i
                break
        if pos == -1:
            break
        lhs = expr[:pos].rstrip()
        rhs = expr[pos + 2 :].lstrip()
        m = re.match(r"^([A-Za-z_]\w*)$", rhs)
        if m:
            expr = f"{rhs}({lhs})"
        else:
            expr = f"({lhs}) |> {rhs}"
        break
    return expr


def _preprocess_prefix_at(expr: str) -> str:
    """Transform WL prefix application f@expr → f[expr]."""
    result = []
    i = 0
    n = len(expr)
    while i < n:
        m = _PREFIX_AT_RE.search(expr, i)
        if m is None:
            result.append(expr[i:])
            break
        result.append(expr[i : m.start()])
        func_name = m.group(1)
        result.append(func_name)
        result.append("[")
        j = m.end()
        while j < n and expr[j] == " ":
            j += 1
        if j < n and expr[j] in "([{":
            open_ch = expr[j]
            close_ch = {"(": ")", "[": "]", "{": "}"}[open_ch]
            depth = 1
            result.append(expr[j])
            j += 1
            while j < n and depth > 0:
                if expr[j] == open_ch:
                    depth += 1
                elif expr[j] == close_ch:
                    depth -= 1
                result.append(expr[j])
                j += 1
        else:
            k = j
            while k < n and (expr[k].isalnum() or expr[k] == "_"):
                k += 1
            result.append(expr[j:k])
            j = k
            if j < n and expr[j] in "([{":
                open_ch = expr[j]
                close_ch = {"(": ")", "[": "]", "{": "}"}[open_ch]
                depth = 1
                result.append(expr[j])
                j += 1
                while j < n and depth > 0:
                    if expr[j] == open_ch:
                        depth += 1
                    elif expr[j] == close_ch:
                        depth -= 1
                    result.append(expr[j])
                    j += 1
        result.append("]")
        i = j
    return "".join(result)


def _preprocess_apply_op(expr: str) -> str:
    """Transform f @@ {a, b, c} → f(a, b, c) (WL Apply with list)."""
    result: list[str] = []
    i = 0
    n = len(expr)
    while i < n:
        if i + 1 < n and expr[i : i + 2] == "@@":
            j = i + 2
            while j < n and expr[j] == " ":
                j += 1
            if j < n and expr[j] == "{":
                depth = 1
                k = j + 1
                while k < n and depth > 0:
                    if expr[k] in "{[":
                        depth += 1
                    elif expr[k] in "}]":
                        depth -= 1
                    k += 1
                while result and result[-1] == " ":
                    result.pop()
                inner = expr[j + 1 : k - 1]
                result.append("(")
                result.append(inner)
                result.append(")")
                i = k
                continue
            while result and result[-1] == " ":
                result.pop()
            k = j
            depth = 0
            while k < n:
                if expr[k] in "([{":
                    depth += 1
                elif expr[k] in ")]}":
                    if depth == 0:
                        break
                    depth -= 1
                k += 1
            inner = expr[j:k]
            result.append("(")
            result.append(inner)
            result.append("...)")
            i = k
            continue
        result.append(expr[i])
        i += 1
    return "".join(result)


def _preprocess_schreier_orbit(expr: str) -> str:
    """Transform SchreierOrbit/SchreierOrbits calls to inject generator names."""

    def replace_single(m: re.Match[str]) -> str:
        pt = m.group(1).strip()
        gens = m.group(2).strip()
        n = m.group(3).strip()
        gen_names = [g.strip() for g in gens.split(",")]
        names_arr = "[" + ", ".join(f'"{name}"' for name in gen_names) + "]"
        gens_arr = "[" + ", ".join(gen_names) + "]"
        return f"SchreierOrbit({pt}, {gens_arr}, {n}, {names_arr})"

    def replace_multi(m: re.Match[str]) -> str:
        gens = m.group(1).strip()
        n = m.group(2).strip()
        gen_names = [g.strip() for g in gens.split(",")]
        names_arr = "[" + ", ".join(f'"{name}"' for name in gen_names) + "]"
        gens_arr = "[" + ", ".join(gen_names) + "]"
        return f"SchreierOrbits({gens_arr}, {n}, {names_arr})"

    expr = _SCHREIER_ORBITS_RE.sub(replace_multi, expr)
    expr = _SCHREIER_ORBIT_RE.sub(replace_single, expr)
    return expr


def _preprocess_wl_patterns(expr: str) -> str:
    """Strip WL pattern (Blank) notation from identifiers."""
    return _WL_PATTERN_RE.sub(r"\1", expr)


def _wl_subhead(wl_arg: str) -> str:
    """Extract the outermost function head from a WL expression string."""
    wl_arg = wl_arg.strip()
    pos = wl_arg.find("[")
    if pos == -1:
        return wl_arg
    return wl_arg[:pos]


def _preprocess_nopattern(expr: str) -> str:
    """Replace ``NoPattern[...]`` with its argument (NoPattern is identity)."""
    result: list[str] = []
    i = 0
    n = len(expr)
    while i < n:
        if expr[i : i + 10] == "NoPattern[":
            depth = 1
            j = i + 10
            while j < n and depth > 0:
                if expr[j] == "[":
                    depth += 1
                elif expr[j] == "]":
                    depth -= 1
                j += 1
            inner = expr[i + 10 : j - 1]
            result.append(inner)
            i = j
            continue
        result.append(expr[i])
        i += 1
    return "".join(result)


def _preprocess_subhead(expr: str) -> str:
    """Rewrite ``SubHead[...]`` in WL notation to a Julia Symbol literal."""
    result: list[str] = []
    i = 0
    n = len(expr)
    while i < n:
        if expr[i : i + 8] == "SubHead[":
            depth = 1
            j = i + 8
            while j < n and depth > 0:
                if expr[j] == "[":
                    depth += 1
                elif expr[j] == "]":
                    depth -= 1
                j += 1
            inner = expr[i + 8 : j - 1]
            head = _wl_subhead(inner)
            result.append(f":{head}")
            i = j
            continue
        result.append(expr[i])
        i += 1
    return "".join(result)


def _preprocess_timing_destruct(expr: str) -> str:
    """Transform WL list destructuring {a, b, ...} = expr → (a, b, ...) = expr."""
    return _WL_DESTRUCT_RE.sub(lambda m: f"({m.group(1)}) {m.group(2)}", expr)
