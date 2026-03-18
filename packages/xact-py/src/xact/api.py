"""Public Python API for xAct tensor algebra.

Provides a Pythonic interface to the Julia xAct.jl engine. All Julia
internals (juliacall, Symbol conversion, Vector wrapping) are hidden.

Example::

    import xact

    M = xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])
    g = xact.Metric(M, "g", signature=-1, covd="CD")
    T = xact.Tensor("T", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")

    xact.canonicalize("T[-b,-a] - T[-a,-b]")  # "0"
"""

from __future__ import annotations

import threading
from typing import Any

# ---------------------------------------------------------------------------
# Lazy Julia bridge — initialized on first use
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_xAct: Any = None
_jl: Any = None


def _ensure_init() -> tuple[Any, Any]:
    """Return (jl_Main, xAct_module), initializing Julia once."""
    global _xAct, _jl
    if _xAct is not None:
        return _jl, _xAct
    with _lock:
        if _xAct is None:
            from xact.xcore._runtime import get_julia

            _jl = get_julia()
            _xAct = _jl.xAct
    return _jl, _xAct


def _to_jl_vec(lst: list[str]) -> Any:
    """Convert a Python list of strings to a Julia Vector{String}."""
    jl, _ = _ensure_init()
    if not lst:
        return jl.seval("String[]")
    return jl.seval("collect")(lst)


# ---------------------------------------------------------------------------
# Handle types — lightweight Python representations of Julia objects
# ---------------------------------------------------------------------------


class Manifold:
    """A differentiable manifold.

    Parameters
    ----------
    name : str
        Manifold identifier (e.g. ``"M"``).
    dim : int
        Dimension of the manifold.
    indices : list[str]
        Abstract index labels (e.g. ``["a", "b", "c", "d"]``).

    Example
    -------
    >>> M = xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])
    """

    def __init__(self, name: str, dim: int, indices: list[str]) -> None:
        _, mod = _ensure_init()
        mod.def_manifold_b(name, dim, _to_jl_vec(indices))
        self.name = name
        self.dim = dim
        self.indices = indices

    def __repr__(self) -> str:
        return f"Manifold({self.name!r}, {self.dim})"


class Metric:
    """A metric tensor with associated covariant derivative.

    Automatically registers Riemann, Ricci, RicciScalar, Weyl, Einstein,
    and Christoffel tensors.

    Parameters
    ----------
    manifold : Manifold
        The manifold this metric lives on (used for documentation only;
        the Julia side infers the manifold from the index slots).
    name : str
        Metric tensor name (e.g. ``"g"``).
    signature : int
        Sign of the metric determinant (``-1`` for Lorentzian, ``1`` for
        Euclidean).
    covd : str
        Name of the associated covariant derivative (e.g. ``"CD"``).
    indices : tuple[str, str]
        Index slot specification. Defaults to ``("-a", "-b")`` using the
        first two indices of the manifold.

    Example
    -------
    >>> g = xact.Metric(M, "g", signature=-1, covd="CD")
    """

    def __init__(
        self,
        manifold: Manifold,
        name: str,
        *,
        signature: int = -1,
        covd: str = "CD",
        indices: tuple[str, str] | None = None,
    ) -> None:
        _, mod = _ensure_init()
        if indices is None:
            a, b = manifold.indices[0], manifold.indices[1]
            idx_str = f"{name}[-{a},-{b}]"
        else:
            idx_str = f"{name}[{indices[0]},{indices[1]}]"
        mod.def_metric_b(signature, idx_str, covd)
        self.name = name
        self.manifold = manifold
        self.covd = covd

    def __repr__(self) -> str:
        return f"Metric({self.name!r}, covd={self.covd!r})"

    def __getitem__(self, indices: object) -> Any:
        from xact.expr import AppliedTensor, TensorHead  # noqa: PLC0415

        if not isinstance(indices, tuple):
            indices = (indices,)
        return AppliedTensor(TensorHead(self.name), list(indices))


class Tensor:
    """An abstract tensor.

    Parameters
    ----------
    name : str
        Tensor identifier (e.g. ``"T"``).
    indices : list[str]
        Index slot specification (e.g. ``["-a", "-b"]`` for covariant).
    manifold : Manifold
        The manifold the tensor is defined on.
    symmetry : str, optional
        Symmetry specification in xAct syntax (e.g.
        ``"Symmetric[{-a,-b}]"``).

    Example
    -------
    >>> T = xact.Tensor("T", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")
    """

    def __init__(
        self,
        name: str,
        indices: list[str],
        manifold: Manifold,
        *,
        symmetry: str | None = None,
    ) -> None:
        _, mod = _ensure_init()
        kwargs: dict[str, str] = {}
        if symmetry is not None:
            kwargs["symmetry_str"] = symmetry
        mod.def_tensor_b(name, _to_jl_vec(indices), manifold.name, **kwargs)
        self.name = name
        self.indices = indices
        self.manifold = manifold

    def __getitem__(self, indices: object) -> Any:
        from xact.expr import AppliedTensor, TensorHead  # noqa: PLC0415

        if not isinstance(indices, tuple):
            indices = (indices,)
        nslots = len(self.indices)
        if len(indices) != nslots:
            raise IndexError(f"{self.name} has {nslots} slots, got {len(indices)}")
        return AppliedTensor(TensorHead(self.name), list(indices))

    def __repr__(self) -> str:
        return f"Tensor({self.name!r}, {self.indices})"


class Perturbation:
    """A perturbation of a background tensor.

    The perturbation tensor must be defined first via :class:`Tensor`.

    Parameters
    ----------
    tensor : Tensor
        The perturbation tensor (e.g. ``h``).
    background : Metric | Tensor
        The background tensor being perturbed (e.g. ``g``).
    order : int
        Perturbation order (>= 1).

    Example
    -------
    >>> h = xact.Tensor("h", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")
    >>> xact.Perturbation(h, g, order=1)
    """

    def __init__(
        self,
        tensor: Tensor,
        background: Metric | Tensor,
        *,
        order: int = 1,
    ) -> None:
        _, mod = _ensure_init()
        mod.def_perturbation_b(tensor.name, background.name, order)
        self.tensor = tensor
        self.background = background
        self.order = order

    def __repr__(self) -> str:
        return (
            f"Perturbation({self.tensor.name!r}, "
            f"{self.background.name!r}, order={self.order})"
        )


# ---------------------------------------------------------------------------
# Expression operations
# ---------------------------------------------------------------------------


def canonicalize(expr: str | Any) -> str | Any:
    """Bring a tensor expression into canonical form.

    Uses the Butler-Portugal algorithm to find the lexicographically
    smallest representative under index permutation symmetries.

    Accepts either a string expression or a typed expression object
    (from :mod:`xact.expr`).  When the input is a typed expression,
    the result is also returned as a typed expression.

    Example
    -------
    >>> xact.canonicalize("T[-b,-a] - T[-a,-b]")
    '0'
    """
    from xact.expr import TExpr, _parse_to_texpr  # noqa: PLC0415

    is_typed = isinstance(expr, TExpr)
    if is_typed:
        expr = str(expr)
    _, mod = _ensure_init()
    result = str(mod.ToCanonical(expr))
    return _parse_to_texpr(result) if is_typed else result


def contract(expr: str | Any) -> str | Any:
    """Evaluate metric contractions in a tensor expression.

    Accepts either a string expression or a typed expression object.
    When the input is typed, the result is also a typed expression.

    Example
    -------
    >>> xact.contract("V[a] * g[-a,-b]")
    'V[-b]'
    """
    from xact.expr import TExpr, _parse_to_texpr  # noqa: PLC0415

    is_typed = isinstance(expr, TExpr)
    if is_typed:
        expr = str(expr)
    _, mod = _ensure_init()
    result = str(mod.Contract(expr))
    return _parse_to_texpr(result) if is_typed else result


def simplify(expr: str | Any) -> str | Any:
    """Iteratively contract and canonicalize until stable.

    Accepts either a string expression or a typed expression object.
    When the input is typed, the result is also a typed expression.

    Example
    -------
    >>> xact.simplify("T[-a,-b] * g[a,b]")
    """
    from xact.expr import TExpr, _parse_to_texpr  # noqa: PLC0415

    is_typed = isinstance(expr, TExpr)
    if is_typed:
        expr = str(expr)
    _, mod = _ensure_init()
    result = str(mod.Simplify(expr))
    return _parse_to_texpr(result) if is_typed else result


def perturb(expr: str | Any, order: int = 1) -> str | Any:
    """Perturb a tensor expression to the given order.

    Applies the multinomial Leibniz expansion.
    Accepts either a string expression or a typed expression object.
    When the input is typed, the result is also a typed expression.

    Example
    -------
    >>> xact.perturb("g[-a,-b]", order=1)
    'h[-a,-b]'
    """
    from xact.expr import TExpr, _parse_to_texpr  # noqa: PLC0415

    is_typed = isinstance(expr, TExpr)
    if is_typed:
        expr = str(expr)
    _, mod = _ensure_init()
    result = str(mod.perturb(expr, order))
    return _parse_to_texpr(result) if is_typed else result


def commute_covds(expr: str | Any, covd: str, index1: str, index2: str) -> str:
    """Commute two covariant derivative indices, producing curvature terms.

    Parameters
    ----------
    expr : str or TExpr
        Expression containing covariant derivatives.
    covd : str
        Name of the covariant derivative (e.g. ``"CD"``).
    index1, index2 : str
        The two derivative indices to commute.
    """
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    jl, _ = _ensure_init()
    return str(
        jl.seval(
            f'XTensor.CommuteCovDs("{_jl_escape(expr)}", :{covd}, "{_jl_escape(index1)}", "{_jl_escape(index2)}")'
        )
    )


def sort_covds(expr: str | Any, covd: str) -> str:
    """Sort all covariant derivatives into canonical order."""
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    jl, _ = _ensure_init()
    return str(jl.seval(f'XTensor.SortCovDs("{_jl_escape(expr)}", :{covd})'))


def ibp(expr: str | Any, covd: str) -> str | Any:
    """Integration by parts — move a covariant derivative off a field.

    When the input is a typed expression, the result is also a typed expression.
    """
    from xact.expr import TExpr, _parse_to_texpr  # noqa: PLC0415

    is_typed = isinstance(expr, TExpr)
    if is_typed:
        expr = str(expr)
    _, mod = _ensure_init()
    result = str(mod.IBP(expr, covd))
    return _parse_to_texpr(result) if is_typed else result


def total_derivative_q(expr: str, covd: str) -> bool:
    """Check whether an expression is a total covariant derivative."""
    _, mod = _ensure_init()
    return bool(mod.TotalDerivativeQ(expr, covd))


def var_d(expr: str | Any, field: str, covd: str) -> str | Any:
    """Euler-Lagrange variational derivative.

    When the input is a typed expression, the result is also a typed expression.
    """
    from xact.expr import TExpr, _parse_to_texpr  # noqa: PLC0415

    is_typed = isinstance(expr, TExpr)
    if is_typed:
        expr = str(expr)
    _, mod = _ensure_init()
    result = str(mod.VarD(expr, field, covd))
    return _parse_to_texpr(result) if is_typed else result


def riemann_simplify(expr: str, covd: str, *, level: int = 6) -> str:
    """Simplify scalar Riemann polynomial expressions.

    Uses the Invar database to reduce expressions modulo
    algebraic and differential identities.

    Parameters
    ----------
    expr : str
        A scalar polynomial in Riemann, Ricci, etc.
    covd : str
        Covariant derivative name.
    level : int
        Simplification level (1-6). Default 6 (all identities).
    """
    _, mod = _ensure_init()
    return str(mod.RiemannSimplify(expr, covd, level=level))


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def reset() -> None:
    """Reset all global tensor algebra state.

    Clears all manifold, metric, tensor, and perturbation definitions.
    """
    _, mod = _ensure_init()
    mod.reset_state_b()


def dimension(manifold: Manifold | str) -> int:
    """Return the dimension of a manifold."""
    _, mod = _ensure_init()
    name = manifold.name if isinstance(manifold, Manifold) else manifold
    return int(mod.Dimension(name))


# ---------------------------------------------------------------------------
# Private seval helpers (for ops that need Julia array literals)
# ---------------------------------------------------------------------------


def _jl_escape(s: str) -> str:
    """Escape backslashes and double-quotes for Julia string literals."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _nested_list_to_julia(data: object) -> str:
    """Convert a nested Python list to a Julia array literal string for seval."""
    if not isinstance(data, list):
        return f"fill({data})"
    if not data:
        return "Any[]"
    if not isinstance(data[0], list):
        return "Any[" + ", ".join(str(x) for x in data) + "]"
    if not isinstance(data[0][0], list):
        rows = [" ".join(str(x) for x in row) for row in data]
        return "Any[" + "; ".join(rows) + "]"

    def _flatten(lst: object) -> list[object]:
        if not isinstance(lst, list):
            return [lst]
        result: list[object] = []
        for item in lst:
            result.extend(_flatten(item))
        return result

    def _shape(lst: object) -> list[int]:
        dims: list[int] = []
        cur: object = lst
        while isinstance(cur, list):
            dims.append(len(cur))
            cur = cur[0]
        return dims

    flat = _flatten(data)
    dims = _shape(data)
    flat_jl = "Any[" + ", ".join(str(x) for x in flat) + "]"
    dims_jl = ", ".join(str(d) for d in reversed(dims))
    return f"permutedims(reshape({flat_jl}, {dims_jl}), {len(dims)}:-1:1)"


# ---------------------------------------------------------------------------
# xCoba — coordinate basis and component operations
# ---------------------------------------------------------------------------


def def_basis(name: str, vbundle: str, cnumbers: list[int]) -> None:
    """Define a coordinate basis."""
    jl, _ = _ensure_init()
    cn_jl = "[" + ", ".join(str(c) for c in cnumbers) + "]"
    jl.seval(f"XTensor.def_basis!(:{name}, :{vbundle}, {cn_jl})")


def def_chart(
    name: str, manifold: str, cnumbers: list[int], scalars: list[str]
) -> None:
    """Define a coordinate chart with scalar coordinate symbols."""
    jl, _ = _ensure_init()
    cn_jl = "[" + ", ".join(str(c) for c in cnumbers) + "]"
    sc_jl = "[" + ", ".join(f":{s}" for s in scalars) + "]"
    jl.seval(f"XTensor.def_chart!(:{name}, :{manifold}, {cn_jl}, {sc_jl})")


def set_basis_change(
    from_basis: str, to_basis: str, matrix: list[list[object]]
) -> None:
    """Register the Jacobian matrix between two bases."""
    jl, _ = _ensure_init()
    mat_jl = _nested_list_to_julia(matrix)
    jl.seval(f"XTensor.set_basis_change!(:{from_basis}, :{to_basis}, {mat_jl})")


def change_basis(expr: str, slot: int, from_basis: str, to_basis: str) -> str:
    """Change the basis of one index slot in an expression."""
    jl, _ = _ensure_init()
    result = jl.seval(
        f"XTensor.change_basis({expr}, Symbol[], {slot}, :{from_basis}, :{to_basis})"
    )
    return str(result)


def get_jacobian(basis1: str, basis2: str) -> str:
    """Return the Jacobian scalar between two bases."""
    jl, _ = _ensure_init()
    result = jl.seval(f"XTensor.Jacobian(:{basis1}, :{basis2})")
    return str(result)


def basis_change_q(from_basis: str, to_basis: str) -> bool:
    """Return True if a basis change between two bases is registered."""
    jl, _ = _ensure_init()
    result = jl.seval(f"XTensor.BasisChangeQ(:{from_basis}, :{to_basis})")
    return result is True or str(result).lower() == "true"


def set_components(
    tensor: str, array: list[object], bases: list[str], *, weight: int = 0
) -> None:
    """Set coordinate components of a tensor."""
    jl, _ = _ensure_init()
    arr_jl = _nested_list_to_julia(array)
    bases_jl = "Symbol[" + ", ".join(f":{b}" for b in bases) + "]"
    jl.seval(
        f"XTensor.set_components!(:{tensor}, {arr_jl}, {bases_jl}; weight={weight})"
    )


def get_components(tensor: str, bases: list[str]) -> str:
    """Return the component array of a tensor as a string."""
    jl, _ = _ensure_init()
    bases_jl = "Symbol[" + ", ".join(f":{b}" for b in bases) + "]"
    result = jl.seval(f"string(XTensor.get_components(:{tensor}, {bases_jl}).array)")
    return str(result)


def component_value(tensor: str, indices: list[int], bases: list[str]) -> str:
    """Return a single component value of a tensor."""
    jl, _ = _ensure_init()
    idx_jl = "[" + ", ".join(str(i) for i in indices) + "]"
    bases_jl = "Symbol[" + ", ".join(f":{b}" for b in bases) + "]"
    result = jl.seval(f"XTensor.component_value(:{tensor}, {idx_jl}, {bases_jl})")
    return str(result)


def ctensor_q(tensor: str, *bases: str) -> bool:
    """Return True if tensor has components registered for the given bases."""
    jl, _ = _ensure_init()
    bases_args = ", ".join(f":{b}" for b in bases)
    result = jl.seval(f"XTensor.CTensorQ(:{tensor}, {bases_args})")
    return result is True or str(result).lower() == "true"


def to_basis(expr: str, basis: str) -> str:
    """Project an abstract expression into a coordinate basis."""
    jl, _ = _ensure_init()
    result = jl.seval(f'string(XTensor.ToBasis("{_jl_escape(expr)}", :{basis}).array)')
    return str(result)


def from_basis(tensor: str, bases: list[str]) -> str:
    """Convert component tensor back to abstract index notation."""
    jl, _ = _ensure_init()
    bases_jl = "Symbol[" + ", ".join(f":{b}" for b in bases) + "]"
    result = jl.seval(f"XTensor.FromBasis(:{tensor}, {bases_jl})")
    return str(result)


def trace_basis_dummy(tensor: str, bases: list[str]) -> str:
    """Trace dummy indices in component tensor."""
    jl, _ = _ensure_init()
    bases_jl = "Symbol[" + ", ".join(f":{b}" for b in bases) + "]"
    result = jl.seval(f"string(XTensor.TraceBasisDummy(:{tensor}, {bases_jl}).array)")
    return str(result)


def christoffel(
    metric: str, basis: str, *, metric_derivs: list[object] | None = None
) -> str:
    """Compute Christoffel symbols from metric components.

    Returns the component array of the Christoffel tensor as a string.
    """
    jl, _ = _ensure_init()
    if metric_derivs is not None:
        dg_jl = _nested_list_to_julia(metric_derivs)
        jl.seval(f"XTensor.christoffel!(:{metric}, :{basis}; metric_derivs={dg_jl})")
    else:
        jl.seval(f"XTensor.christoffel!(:{metric}, :{basis})")
    christoffel_name = jl.seval(
        f"""begin
            local _cd = nothing
            for (cd, m) in XTensor._metrics
                if m.name == :{metric}
                    _cd = cd
                    break
                end
            end
            string(Symbol("Christoffel" * string(_cd)))
        end"""
    )
    cname = str(christoffel_name)
    bases_jl = f"Symbol[:{basis}, :{basis}, :{basis}]"
    result = jl.seval(f"string(XTensor.get_components(:{cname}, {bases_jl}).array)")
    return str(result)


# ---------------------------------------------------------------------------
# xTras — extended tensor utilities
# ---------------------------------------------------------------------------


def collect_tensors(expr: str) -> str:
    """Group like tensor terms."""
    _, mod = _ensure_init()
    return str(mod.CollectTensors(expr))


def all_contractions(expr: str, metric: str) -> list[str]:
    """Enumerate all possible contractions of an expression."""
    jl, _ = _ensure_init()
    result = jl.seval(f'XTensor.AllContractions("{_jl_escape(expr)}", :{metric})')
    return [str(x) for x in result]


def symmetry_of(expr: str) -> str:
    """Return the symmetry type of a tensor expression."""
    _, mod = _ensure_init()
    return str(mod.SymmetryOf(expr))


def make_trace_free(expr: str, metric: str) -> str:
    """Project an expression to its trace-free part."""
    jl, _ = _ensure_init()
    return str(jl.seval(f'XTensor.MakeTraceFree("{_jl_escape(expr)}", :{metric})'))


# ---------------------------------------------------------------------------
# Perturbation utilities
# ---------------------------------------------------------------------------


def check_metric_consistency(metric: str) -> bool:
    """Check that a metric tensor is self-consistent."""
    jl, _ = _ensure_init()
    result = jl.seval(f"XTensor.check_metric_consistency(:{metric})")
    return result is True or str(result).lower() == "true"


def perturb_curvature(
    covd: str, perturbation: str, *, order: int = 1
) -> dict[str, str]:
    """Return first-order perturbations of curvature tensors.

    Returns a dict with keys ``"Christoffel1"``, ``"Riemann1"``,
    ``"Ricci1"``, ``"RicciScalar1"``.
    """
    jl, _ = _ensure_init()
    result = jl.seval(
        f"XTensor.perturb_curvature(:{covd}, :{perturbation}; order={order})"
    )
    return {str(k): str(v) for k, v in result.items()}


def perturbation_order(tensor: str) -> int:
    """Return the perturbation order of a tensor."""
    jl, _ = _ensure_init()
    return int(jl.seval(f"XTensor.PerturbationOrder(:{tensor})"))


def perturbation_at_order(background: str, order: int) -> str:
    """Return the name of the perturbation tensor at the given order."""
    jl, _ = _ensure_init()
    result = jl.seval(f"XTensor.PerturbationAtOrder(:{background}, {order})")
    name = str(result)
    return name[1:] if name.startswith(":") else name
