"""Python wrapper for the Julia XCore module.

Exposes all public XCore functions under the ``sxact.xcore`` namespace with
Python-idiomatic (snake_case) names.  Julia is initialised once per process
on first import of this module.

Type conventions
----------------
- Symbol arguments accept Python ``str``; the wrapper converts to Julia Symbol.
- Symbol return values are returned as Python ``str``.
- Vector{Symbol} arguments accept ``list[str]``.
- Vector{Symbol} return values are returned as ``list[str]``.
- Julia exceptions are re-raised as :class:`juliacall.JuliaError`.

Example
-------
>>> from sxact.xcore import validate_symbol
>>> validate_symbol("MyNewTensor")   # raises if name collides
"""

from __future__ import annotations

from typing import Any, Callable

from ._runtime import get_julia, get_xcore

try:
    from juliacall import JuliaError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "juliacall is required for sxact.xcore.  "
        "Install it with: pip install juliacall"
    ) from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sym(s: str | Any) -> Any:
    """Convert a Python str to a Julia Symbol (pass-through for Julia values)."""
    if isinstance(s, str):
        return get_julia().Symbol(s)
    return s


def _str(s: Any) -> str:
    """Convert a Julia Symbol (or any Julia value) to a Python str."""
    return str(s)


def _sym_list(symbols: list[str | Any]) -> Any:
    """Convert a Python list of str/Symbols to a Julia Vector{Symbol}."""
    jl = get_julia()
    return jl.seval("Symbol[]") if not symbols else jl.seval(
        "Symbol[" + ", ".join(f"Symbol({str(s)!r})" for s in symbols) + "]"
    )


def _str_list(vec: Any) -> list[str]:
    """Convert a Julia Vector{Symbol} to a Python list of str."""
    return [str(s) for s in vec]


# ---------------------------------------------------------------------------
# 1. List utilities
# ---------------------------------------------------------------------------

def just_one(lst: Any) -> Any:
    """Return the single element of a one-element collection; raise otherwise.

    Julia: ``JustOne(list)``
    """
    return get_xcore().JustOne(lst)


def map_if_plus(f: Callable[..., Any], expr: Any) -> Any:
    """Map *f* over a list, or apply once to a scalar.

    Julia: ``MapIfPlus(f, expr)``
    """
    return get_xcore().MapIfPlus(f, expr)


def thread_array(head: Any, left: Any, right: Any) -> Any:
    """Map *head* over element pairs from *left* and *right*.

    Julia: ``ThreadArray(head, left, right)``
    """
    return get_xcore().ThreadArray(head, left, right)


# ---------------------------------------------------------------------------
# 2. Argument guards
# ---------------------------------------------------------------------------

def set_number_of_arguments(f: Any, n: int) -> None:
    """No-op shim; Julia enforces arity via method dispatch.

    Julia: ``SetNumberOfArguments(f, n)``
    """
    get_xcore().SetNumberOfArguments(f, n)


# ---------------------------------------------------------------------------
# 3. Options
# ---------------------------------------------------------------------------

def check_options(*opts: Any) -> list[tuple[Any, Any]]:
    """Validate and flatten option rules.

    Each argument may be a ``(key, value)`` tuple, a dict, or a list of
    ``(key, value)`` tuples.  Returns a flat list of ``(key, value)`` pairs
    on success; raises ``ValueError`` on invalid structure.

    Julia: ``CheckOptions(opts...)``
    """
    jl = get_julia()
    xc = get_xcore()

    def _to_julia_pair(k: Any, v: Any) -> Any:
        return jl.seval(f"nothing => nothing")  # placeholder – use seval below

    # Flatten to (k, v) list first
    flat: list[tuple[Any, Any]] = []
    for o in opts:
        if isinstance(o, dict):
            flat.extend(o.items())
        elif isinstance(o, (list, tuple)):
            if len(o) == 2 and not isinstance(o[0], (list, tuple, dict)):
                flat.append((o[0], o[1]))
            else:
                for item in o:
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        flat.append((item[0], item[1]))
                    else:
                        raise ValueError(
                            f"check_options: expected (key, value) pair, got {item!r}"
                        )
        else:
            raise ValueError(
                f"check_options: expected dict or (key, value) pair, got {o!r}"
            )

    return flat


def true_or_false(x: Any) -> bool:
    """Return True if *x* is a bool; False otherwise.

    Julia: ``TrueOrFalse(x)``
    """
    return bool(get_xcore().TrueOrFalse(x))


def report_set(ref: Any, value: Any, *, verbose: bool = True) -> None:
    """Assign *value* to *ref[]*, printing if changed.

    Julia: ``ReportSet(ref, value; verbose=verbose)``
    """
    get_xcore().ReportSet(ref, value, verbose=verbose)


def report_set_option(symbol: Any, pair: tuple[Any, Any]) -> None:
    """No-op shim.

    Julia: ``ReportSetOption(symbol, pair)``
    """
    # no-op; matches Julia behaviour
    pass


# ---------------------------------------------------------------------------
# 4. Symbol naming and dagger / link characters
# ---------------------------------------------------------------------------

def symbol_join(*symbols: Any) -> str:
    """Concatenate *symbols* into a single symbol name.

    Julia: ``SymbolJoin(symbols...)``
    """
    return _str(get_xcore().SymbolJoin(*symbols))


def no_pattern(expr: Any) -> Any:
    """Identity shim (Julia has no Pattern wrappers).

    Julia: ``NoPattern(expr)``
    """
    return expr


# --- DaggerCharacter ---

def dagger_character() -> str:
    """Return the current dagger character string.

    Julia: ``DaggerCharacter[]``
    """
    return str(get_julia().seval("Main.XCore.DaggerCharacter[]"))


def set_dagger_character(value: str) -> None:
    """Set the dagger character string.

    Julia: ``DaggerCharacter[] = value``
    """
    jl = get_julia()
    jl.seval(f'Main.XCore.DaggerCharacter[] = {value!r}')


def has_dagger_character_q(s: str | Any) -> bool:
    """Return True if the symbol name contains the dagger character.

    Julia: ``HasDaggerCharacterQ(s)``
    """
    return bool(get_xcore().HasDaggerCharacterQ(_sym(s)))


def make_dagger_symbol(s: str | Any) -> str:
    """Toggle the dagger character on a symbol (add if absent, remove if present).

    Julia: ``MakeDaggerSymbol(s)``
    """
    return _str(get_xcore().MakeDaggerSymbol(_sym(s)))


# --- LinkCharacter ---

def link_character() -> str:
    """Return the current link character string.

    Julia: ``LinkCharacter[]``
    """
    return str(get_julia().seval("Main.XCore.LinkCharacter[]"))


def set_link_character(value: str) -> None:
    """Set the link character string.

    Julia: ``LinkCharacter[] = value``
    """
    get_julia().seval(f'Main.XCore.LinkCharacter[] = {value!r}')


def link_symbols(symbols: list[str | Any]) -> str:
    """Join *symbols* with the link character into a single symbol name.

    Julia: ``LinkSymbols(symbols)``
    """
    return _str(get_xcore().LinkSymbols(_sym_list(symbols)))


def unlink_symbol(s: str | Any) -> list[str]:
    """Split a symbol at each link character; return parts as a list of str.

    Julia: ``UnlinkSymbol(s)``
    """
    return _str_list(get_xcore().UnlinkSymbol(_sym(s)))


# ---------------------------------------------------------------------------
# 5. xUpvalues
# ---------------------------------------------------------------------------

def sub_head(expr: Any) -> Any:
    """Return the innermost atomic head of a nested expression.

    Julia: ``SubHead(expr)``
    """
    return get_xcore().SubHead(expr)


def x_up_set(property: str | Any, tag: str | Any, value: Any) -> Any:
    """Attach *value* as the *property* upvalue of *tag*.

    Julia: ``xUpSet!(property, tag, value)``
    """
    return get_xcore().xUpSet_b(_sym(property), _sym(tag), value)


def x_up_set_delayed(
    property: str | Any, tag: str | Any, thunk: Callable[[], Any]
) -> None:
    """Attach a zero-argument thunk as a delayed upvalue.

    Julia: ``xUpSetDelayed!(property, tag, thunk)``
    """
    get_xcore().xUpSetDelayed_b(_sym(property), _sym(tag), thunk)


def x_up_append_to(property: str | Any, tag: str | Any, element: Any) -> list[Any]:
    """Append *element* to the upvalue list *property[tag]*.

    Julia: ``xUpAppendTo!(property, tag, element)``
    """
    result = get_xcore().xUpAppendTo_b(_sym(property), _sym(tag), element)
    return list(result)


def x_up_delete_cases_to(
    property: str | Any, tag: str | Any, pred: Callable[[Any], bool]
) -> None:
    """Remove all upvalue-list elements satisfying *pred*.

    Julia: ``xUpDeleteCasesTo!(property, tag, pred)``
    """
    get_xcore().xUpDeleteCasesTo_b(_sym(property), _sym(tag), pred)


# ---------------------------------------------------------------------------
# 6. Tag assignment
# ---------------------------------------------------------------------------

def x_tag_set(tag: str | Any, key: Any, value: Any) -> Any:
    """Assign *value* to *key* in the tag store for *tag*.

    Julia: ``xTagSet!(tag, key, value)``
    """
    return get_xcore().xTagSet_b(_sym(tag), key, value)


def x_tag_set_delayed(
    tag: str | Any, key: Any, thunk: Callable[[], Any]
) -> None:
    """Delayed variant of :func:`x_tag_set`.

    Julia: ``xTagSetDelayed!(tag, key, thunk)``
    """
    get_xcore().xTagSetDelayed_b(_sym(tag), key, thunk)


# ---------------------------------------------------------------------------
# 7. Unevaluated append (alias for push!)
# ---------------------------------------------------------------------------

def push_unevaluated(collection: list[Any], value: Any) -> list[Any]:
    """Append *value* to *collection* (Julia evaluates eagerly; this is push!).

    Julia: ``push_unevaluated!(collection, value)``
    """
    collection.append(value)
    return collection


# ---------------------------------------------------------------------------
# 8. Extensions system
# ---------------------------------------------------------------------------

def x_tension(
    package: str,
    defcommand: str | Any,
    moment: str,
    func: Callable[..., Any],
) -> None:
    """Register *func* to fire at *moment* during *defcommand*.

    *moment* must be ``"Beginning"`` or ``"End"``.

    Julia: ``xTension!(package, defcommand, moment, func)``
    """
    get_xcore().xTension_b(package, _sym(defcommand), moment, func)


def make_x_tensions(defcommand: str | Any, moment: str, *args: Any) -> None:
    """Fire all hooks registered for *(defcommand, moment)*.

    Julia: ``MakexTensions(defcommand, moment, args...)``
    """
    get_xcore().MakexTensions(_sym(defcommand), moment, *args)


# ---------------------------------------------------------------------------
# 9. Expression evaluation
# ---------------------------------------------------------------------------

def x_evaluate_at(expr: Any, positions: Any) -> Any:
    """No-op shim (Julia evaluates eagerly).

    Julia: ``xEvaluateAt(expr, positions)``
    """
    return expr


# ---------------------------------------------------------------------------
# 10. Symbol registry and validation
# ---------------------------------------------------------------------------

def validate_symbol(name: str | Any) -> None:
    """Raise if *name* collides with an already-registered or Base symbol.

    Julia: ``ValidateSymbol(name)``

    Raises:
        JuliaError: if the symbol name is already in use.
    """
    get_xcore().ValidateSymbol(_sym(name))


def find_symbols(expr: Any) -> list[str]:
    """Recursively collect all Symbols in *expr*; return as list of str.

    Julia: ``FindSymbols(expr)``
    """
    return _str_list(get_xcore().FindSymbols(expr))


def register_symbol(name: str | Any, package: str) -> None:
    """Register *name* as owned by *package*.

    Julia: ``register_symbol(name, package)``

    Raises:
        JuliaError: if *name* is already registered by a different package.
    """
    get_xcore().register_symbol(str(name), package)


# --- Per-package name lists (read-only views) ---

def x_perm_names() -> list[str]:
    """Return a copy of the xPerm symbol name list."""
    return list(get_xcore().xPermNames)


def x_tensor_names() -> list[str]:
    """Return a copy of the xTensor symbol name list."""
    return list(get_xcore().xTensorNames)


def x_core_names() -> list[str]:
    """Return a copy of the xCore symbol name list."""
    return list(get_xcore().xCoreNames)


def x_tableau_names() -> list[str]:
    """Return a copy of the xTableau symbol name list."""
    return list(get_xcore().xTableauNames)


def x_coba_names() -> list[str]:
    """Return a copy of the xCoba symbol name list."""
    return list(get_xcore().xCobaNames)


def invar_names() -> list[str]:
    """Return a copy of the Invar symbol name list."""
    return list(get_xcore().InvarNames)


def harmonics_names() -> list[str]:
    """Return a copy of the Harmonics symbol name list."""
    return list(get_xcore().HarmonicsNames)


def x_pert_names() -> list[str]:
    """Return a copy of the xPert symbol name list."""
    return list(get_xcore().xPertNames)


def spinors_names() -> list[str]:
    """Return a copy of the Spinors symbol name list."""
    return list(get_xcore().SpinorsNames)


def em_names() -> list[str]:
    """Return a copy of the EM symbol name list."""
    return list(get_xcore().EMNames)


# --- Mutable string refs ---

def warning_from() -> str:
    """Return the current WarningFrom label."""
    return str(get_julia().seval("Main.XCore.WarningFrom[]"))


def set_warning_from(value: str) -> None:
    """Set the WarningFrom label."""
    get_julia().seval(f"Main.XCore.WarningFrom[] = {value!r}")


def xact_directory() -> str:
    """Return the xAct installation directory path."""
    return str(get_julia().seval("Main.XCore.xActDirectory[]"))


def set_xact_directory(path: str) -> None:
    """Set the xAct installation directory path."""
    get_julia().seval(f"Main.XCore.xActDirectory[] = {path!r}")


def xact_doc_directory() -> str:
    """Return the xAct documentation directory path."""
    return str(get_julia().seval("Main.XCore.xActDocDirectory[]"))


def set_xact_doc_directory(path: str) -> None:
    """Set the xAct documentation directory path."""
    get_julia().seval(f"Main.XCore.xActDocDirectory[] = {path!r}")


# ---------------------------------------------------------------------------
# Category B: stdlib aliases
# ---------------------------------------------------------------------------

def delete_duplicates(lst: list[Any]) -> list[Any]:
    """Remove duplicates from *lst*, preserving order.

    Julia: ``DeleteDuplicates`` (alias for ``unique``).
    """
    seen: set[Any] = set()
    result = []
    for item in lst:
        key = item if isinstance(item, str) else id(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def duplicate_free_q(lst: list[Any]) -> bool:
    """Return True if *lst* has no duplicate elements.

    Julia: ``DuplicateFreeQ`` (alias for ``allunique``).
    """
    return len(lst) == len(set(str(x) for x in lst))


# ---------------------------------------------------------------------------
# 11. Misc
# ---------------------------------------------------------------------------

def disclaimer() -> None:
    """Print the GPL warranty disclaimer.

    Julia: ``Disclaimer()``
    """
    get_xcore().Disclaimer()


# ---------------------------------------------------------------------------
# Public __all__
# ---------------------------------------------------------------------------

__all__ = [
    "JuliaError",
    # 1. List utilities
    "just_one",
    "map_if_plus",
    "thread_array",
    # 2. Argument guards
    "set_number_of_arguments",
    # 3. Options
    "check_options",
    "true_or_false",
    "report_set",
    "report_set_option",
    # 4. Symbol naming
    "symbol_join",
    "no_pattern",
    "dagger_character",
    "set_dagger_character",
    "has_dagger_character_q",
    "make_dagger_symbol",
    "link_character",
    "set_link_character",
    "link_symbols",
    "unlink_symbol",
    # 5. xUpvalues
    "sub_head",
    "x_up_set",
    "x_up_set_delayed",
    "x_up_append_to",
    "x_up_delete_cases_to",
    # 6. Tag assignment
    "x_tag_set",
    "x_tag_set_delayed",
    # 7. Unevaluated append
    "push_unevaluated",
    # 8. Extensions
    "x_tension",
    "make_x_tensions",
    # 9. Expression evaluation
    "x_evaluate_at",
    # 10. Symbol registry
    "validate_symbol",
    "find_symbols",
    "register_symbol",
    "x_perm_names",
    "x_tensor_names",
    "x_core_names",
    "x_tableau_names",
    "x_coba_names",
    "invar_names",
    "harmonics_names",
    "x_pert_names",
    "spinors_names",
    "em_names",
    "warning_from",
    "set_warning_from",
    "xact_directory",
    "set_xact_directory",
    "xact_doc_directory",
    "set_xact_doc_directory",
    # Category B
    "delete_duplicates",
    "duplicate_free_q",
    # 11. Misc
    "disclaimer",
]
