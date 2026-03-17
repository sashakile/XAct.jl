"""Typed expression layer for xact.

Provides index types (Idx, DnIdx), tensor handles (TensorHead), and
expression nodes (AppliedTensor, SumExpr, ProdExpr, CovDExpr) that
support Python operator overloading and serialise to the string format
expected by the xAct engine.

Engine functions in api.py are overloaded to accept these typed expressions
transparently — they convert via str() before calling the Julia engine.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from xact.api import Manifold

# ---------------------------------------------------------------------------
# Index types
# ---------------------------------------------------------------------------


class Idx:
    """Abstract (contravariant / up) index bound to a manifold."""

    __slots__ = ("label", "manifold")

    def __init__(self, label: str, manifold: str) -> None:
        self.label = label
        self.manifold = manifold

    def __neg__(self) -> DnIdx:
        return DnIdx(self)

    def __repr__(self) -> str:
        return self.label

    def __str__(self) -> str:
        return self.label


class DnIdx:
    """Covariant (down) index — wraps an Idx."""

    __slots__ = ("parent",)

    def __init__(self, parent: Idx) -> None:
        self.parent = parent

    def __neg__(self) -> Idx:
        """Double negation returns the bare Idx (identity)."""
        return self.parent

    def __repr__(self) -> str:
        return f"-{self.parent.label}"

    def __str__(self) -> str:
        return f"-{self.parent.label}"


SlotIdx = Union[Idx, DnIdx]


# ---------------------------------------------------------------------------
# Expression base class
# ---------------------------------------------------------------------------


class TExpr:
    """Base class for all typed tensor expressions."""

    def __add__(self, other: TExpr) -> SumExpr:
        return SumExpr(_flatten_sum([self, other]))

    def __radd__(self, other: TExpr) -> SumExpr:
        return SumExpr(_flatten_sum([other, self]))

    def __sub__(self, other: TExpr) -> SumExpr:
        return SumExpr(_flatten_sum([self, _make_prod(-1, [other])]))

    def __rsub__(self, other: TExpr) -> SumExpr:
        return SumExpr(_flatten_sum([other, _make_prod(-1, [self])]))

    def __mul__(self, other: object) -> ProdExpr:
        if isinstance(other, (int, Fraction)):
            return _make_prod(other, [self])
        if isinstance(other, TExpr):
            return _make_prod(1, [self, other])
        return NotImplemented

    def __rmul__(self, other: object) -> ProdExpr:
        if isinstance(other, (int, Fraction)):
            return _make_prod(other, [self])
        return NotImplemented

    def __neg__(self) -> ProdExpr:
        return _make_prod(-1, [self])


# ---------------------------------------------------------------------------
# Expression node types
# ---------------------------------------------------------------------------


class AppliedTensor(TExpr):
    """A tensor with indices applied, e.g. T[-a, -b]."""

    def __init__(self, head: TensorHead, indices: list[SlotIdx]) -> None:
        self.head = head
        self.indices = indices

    def __str__(self) -> str:
        idx = ",".join(str(i) for i in self.indices)
        return f"{self.head.name}[{idx}]"

    def __repr__(self) -> str:
        return str(self)


class SumExpr(TExpr):
    """Sum of tensor expressions."""

    def __init__(self, terms: list[TExpr]) -> None:
        self.terms = terms

    def __str__(self) -> str:
        if not self.terms:
            return "0"
        buf = []
        for i, term in enumerate(self.terms):
            s = str(term)
            if i == 0:
                buf.append(s)
            elif s.startswith("-"):
                buf.append(" - ")
                buf.append(s[1:])
            else:
                buf.append(" + ")
                buf.append(s)
        return "".join(buf)

    def __repr__(self) -> str:
        return str(self)


class ProdExpr(TExpr):
    """Product of tensor expressions with a rational coefficient."""

    def __init__(self, coeff: Fraction, factors: list[TExpr]) -> None:
        self.coeff = coeff
        self.factors = factors

    def __str__(self) -> str:
        parts = [_str_factor(f) for f in self.factors]
        body = " * ".join(parts)
        if self.coeff == 1:
            return body
        elif self.coeff == -1:
            return "-" + body
        elif self.coeff.denominator == 1:
            return f"{self.coeff.numerator} * {body}"
        else:
            return f"({self.coeff.numerator}/{self.coeff.denominator}) * {body}"

    def __repr__(self) -> str:
        return str(self)


class CovDExpr(TExpr):
    """Covariant derivative applied to an expression: CD[-a](T[-b,-c])."""

    def __init__(self, covd: str, index: SlotIdx, operand: TExpr) -> None:
        self.covd = covd
        self.index = index
        self.operand = operand

    def __str__(self) -> str:
        return f"{self.covd}[{self.index}][{self.operand}]"

    def __repr__(self) -> str:
        return str(self)


# ---------------------------------------------------------------------------
# TensorHead
# ---------------------------------------------------------------------------


class TensorHead:
    """Lightweight handle for a registered tensor.  Supports T[-a, -b] syntax.

    Instances are created by :func:`tensor`.  The ``_nslots`` attribute stores
    the expected arity for fast Python-side validation.
    """

    def __init__(self, name: str, nslots: int = -1) -> None:
        self.name = name
        self._nslots = nslots

    def __getitem__(self, indices: object) -> AppliedTensor:
        if indices is None:
            idx_list: list[SlotIdx] = []
        elif isinstance(indices, tuple):
            idx_list = list(indices)
        else:
            idx_list = [indices]  # type: ignore[list-item]
        if self._nslots >= 0 and len(idx_list) != self._nslots:
            raise IndexError(
                f"{self.name} has {self._nslots} slots, got {len(idx_list)}"
            )
        return AppliedTensor(self, idx_list)

    def __repr__(self) -> str:
        return f"TensorHead({self.name!r})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_prod(coeff: int | Fraction, nodes: list[TExpr]) -> ProdExpr:
    """Flatten nested ProdExpr and merge coefficients."""
    c = Fraction(coeff)
    flat: list[TExpr] = []
    for node in nodes:
        if isinstance(node, ProdExpr):
            c *= node.coeff
            flat.extend(node.factors)
        else:
            flat.append(node)
    return ProdExpr(c, flat)


def _flatten_sum(nodes: list[TExpr]) -> list[TExpr]:
    """Flatten nested SumExpr into a single flat term list."""
    terms: list[TExpr] = []
    for node in nodes:
        if isinstance(node, SumExpr):
            terms.extend(node.terms)
        else:
            terms.append(node)
    return terms


def _str_factor(f: TExpr) -> str:
    """Serialise a factor, parenthesising sums inside products."""
    return f"({f})" if isinstance(f, SumExpr) else str(f)


# ---------------------------------------------------------------------------
# Public factory functions (need Julia bridge — imported lazily from api)
# ---------------------------------------------------------------------------


def indices(manifold: Manifold) -> tuple[Idx, ...]:
    """Return Idx objects for all abstract index labels of *manifold*.

    Example::

        a, b, c, d, e, f = xact.indices(M)
    """
    return tuple(Idx(label, manifold.name) for label in manifold.indices)


def tensor(name: str) -> TensorHead:
    """Look up a registered tensor and return a :class:`TensorHead`.

    Parameters
    ----------
    name:
        The tensor name as registered via :class:`~xact.Tensor` or
        auto-created by :class:`~xact.Metric` (e.g. ``"RiemannCD"``).

    Raises
    ------
    ValueError
        If the tensor is not registered in the current Julia session.
    """
    # Lazy import to avoid circular dependency
    from xact.api import _ensure_init  # noqa: PLC0415

    _, mod = _ensure_init()
    if not bool(mod.TensorQ(name)):
        raise ValueError(f"Tensor {name!r} is not defined")
    nslots = len(mod.SlotsOfTensor(name))
    return TensorHead(name, nslots=nslots)
