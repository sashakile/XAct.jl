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


def canonicalize(expr: str | Any) -> str:
    """Bring a tensor expression into canonical form.

    Uses the Butler-Portugal algorithm to find the lexicographically
    smallest representative under index permutation symmetries.

    Accepts either a string expression or a typed expression object
    (from :mod:`xact.expr`).

    Example
    -------
    >>> xact.canonicalize("T[-b,-a] - T[-a,-b]")
    '0'
    """
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    _, mod = _ensure_init()
    return str(mod.ToCanonical(expr))


def contract(expr: str | Any) -> str:
    """Evaluate metric contractions in a tensor expression.

    Accepts either a string expression or a typed expression object.

    Example
    -------
    >>> xact.contract("V[a] * g[-a,-b]")
    'V[-b]'
    """
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    _, mod = _ensure_init()
    return str(mod.Contract(expr))


def simplify(expr: str | Any) -> str:
    """Iteratively contract and canonicalize until stable.

    Accepts either a string expression or a typed expression object.

    Example
    -------
    >>> xact.simplify("T[-a,-b] * g[a,b]")
    """
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    _, mod = _ensure_init()
    return str(mod.Simplify(expr))


def perturb(expr: str | Any, order: int = 1) -> str:
    """Perturb a tensor expression to the given order.

    Applies the multinomial Leibniz expansion.
    Accepts either a string expression or a typed expression object.

    Example
    -------
    >>> xact.perturb("g[-a,-b]", order=1)
    'h[-a,-b]'
    """
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    _, mod = _ensure_init()
    return str(mod.perturb(expr, order))


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
    _, mod = _ensure_init()
    return str(mod.CommuteCovDs(expr, covd, index1, index2))


def sort_covds(expr: str | Any, covd: str) -> str:
    """Sort all covariant derivatives into canonical order."""
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    _, mod = _ensure_init()
    return str(mod.SortCovDs(expr, covd))


def ibp(expr: str | Any, covd: str) -> str:
    """Integration by parts — move a covariant derivative off a field."""
    from xact.expr import TExpr  # noqa: PLC0415

    if isinstance(expr, TExpr):
        expr = str(expr)
    _, mod = _ensure_init()
    return str(mod.IBP(expr, covd))


def total_derivative_q(expr: str, covd: str) -> bool:
    """Check whether an expression is a total covariant derivative."""
    _, mod = _ensure_init()
    return bool(mod.TotalDerivativeQ(expr, covd))


def var_d(expr: str, field: str, covd: str) -> str:
    """Euler-Lagrange variational derivative."""
    _, mod = _ensure_init()
    return str(mod.VarD(expr, field, covd))


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
    return str(mod.RiemannSimplify(expr, covd, level))


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
