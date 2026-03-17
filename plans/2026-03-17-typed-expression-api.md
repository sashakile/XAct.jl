# Type-Safe Expression API for sxAct

**Ticket:** sxAct-6w62
**Status:** Design spec (research deliverable)
**Date:** 2026-03-17

## 1. Motivation

Every expression in sxAct is currently a string:

```julia
# Julia — string API
ToCanonical("RiemannCD[-a,-b,-c,-d] + RiemannCD[-a,-c,-d,-b] + RiemannCD[-a,-d,-b,-c]")
Contract("V[a] * g[-a,-b]")
```

```python
# Python — string API
xact.canonicalize("T[-b,-a] - T[-a,-b]")
xact.contract("V[a] * g[-a,-b]")
```

With a typed expression layer, the same workflows become:

```julia
# Julia — typed API
@indices M a b c d e f
Riem = tensor(:RiemannCD)
ToCanonical(Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c])

V = tensor(:V);  g = tensor(:g)
Contract(V[a] * g[-a,-b])
```

```python
# Python — typed API
a, b, c, d, e, f = xact.indices(M)
Riem = xact.tensor("RiemannCD")
xact.canonicalize(Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c])

V = xact.Tensor("V", ["a"], M)
xact.contract(V[a] * g[-a,-b])
```

The string API works, but creates friction:

| Problem | Example |
|---------|---------|
| No slot-count checking | `"T[-a,-b,-c]"` silently wrong if T is rank-2 |
| No manifold checking | Mixing indices from different manifolds |
| No dummy-index validation | Index appearing 3 times only caught deep in canonicalization |
| No discoverability | Must know string names of auto-created tensors (RiemannCD, RicciCD, ...) |
| No composability | Can't build expressions across statements; everything is string concat |
| No tab-completion | IDE can't help with tensor names or index labels |

A typed expression layer solves all of these while keeping the existing string engine unchanged.

## 2. Design Principles

1. **Wrapper, not replacement** — The string engine stays. Typed expressions compile to strings, call the engine, and (in Stage 2) parse results back.
2. **Minimal types** — Follow SymbolicUtils' lesson: fewer node types = simpler system. We need ~7 types, not a deep hierarchy.
3. **Julia-native syntax** — Exploit `getindex`, unary `-`, and arithmetic overloading so `T[-a,-b]` is valid Julia.
4. **Validation at construction** — Catch errors when expressions are built, not when they're evaluated.
5. **Incremental adoption** — String API remains first-class. All functions accept both `String` and `TExpr`.

## 3. Proposed Type Hierarchy (Julia)

```
                     TExpr (abstract)
                       │
    ┌────────┬─────────┼─────────┬─────────┐
    │        │         │         │         │
 TScalar  TTensor   TProd     TSum     TCovD
```

Supporting types (not TExpr):

```
  Idx          DnIdx         TensorHead      CovDHead
  (up index)   (down index)  (tensor name)   (covd name)
```

### 3.1 Index Types

```julia
"""An abstract index label bound to a manifold."""
struct Idx
    label::Symbol     # :a, :b, :c
    manifold::Symbol  # :M

    function Idx(label::Symbol, manifold::Symbol)
        # Runtime validation: label must be registered for manifold
        haskey(_manifolds, manifold) ||
            error("Manifold $manifold is not defined")
        mobj = _manifolds[manifold]
        label in mobj.index_labels ||
            error("Index $label is not registered for manifold $manifold")
        new(label, manifold)
    end
end

"""A covariant (down) index."""
struct DnIdx
    parent::Idx
end

# Unary minus creates covariant index
Base.:-(i::Idx) = DnIdx(i)

# Double negation returns the bare index
Base.:-(i::DnIdx) = i.parent

# Type alias for "anything that goes in a tensor slot"
const SlotIdx = Union{Idx, DnIdx}
```

Convention (matches physics and Mathematica xAct):
- `a` bare -> contravariant (up)
- `-a` -> covariant (down)
- `-(-a)` -> `a` (identity)

### 3.2 Index Declaration Macro

```julia
"""
    @indices M a b c d e f

Create Idx objects bound to manifold M.
The macro generates runtime Idx() constructor calls, which validate
that each label is registered for the manifold.
"""
macro indices(manifold, names...)
    exprs = []
    for name in names
        push!(exprs, :($(esc(name)) = Idx($(QuoteNode(name)), $(QuoteNode(manifold)))))
    end
    quote $(exprs...) end
end
```

Usage:
```julia
def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f])
@indices M a b c d e f
# Now: a = Idx(:a, :M), b = Idx(:b, :M), ...
```

> **Caveat:** Index variables can be shadowed by loop variables or
> reassignment (`for a in 1:10` overwrites `a`). Avoid reusing index
> labels as local variable names.

### 3.3 Expression Types

```julia
abstract type TExpr end

"""Numeric scalar."""
struct TScalar <: TExpr
    value::Rational{Int}
end

"""A tensor head — lightweight handle for a registered tensor name.
Not a TExpr: must apply indices via getindex to produce a TTensor."""
struct TensorHead
    name::Symbol
end

"""A tensor with indices applied: T[-a, -b]."""
struct TTensor <: TExpr
    head::TensorHead
    indices::Vector{SlotIdx}
end

"""Product of tensor expressions: T[-a,-b] * V[a]."""
struct TProd <: TExpr
    coeff::Rational{Int}
    factors::Vector{TExpr}   # each factor is TTensor, TCovD, or TScalar
end

"""Sum of tensor expressions: T[-a,-b] + S[-a,-b]."""
struct TSum <: TExpr
    terms::Vector{TExpr}     # each term is TTensor, TProd, TCovD, or TScalar
end

"""Covariant derivative application: CD[-a](T[-b,-c])."""
struct TCovD <: TExpr
    covd::Symbol
    index::SlotIdx
    operand::TExpr
end

"""A covariant derivative head — callable constructor for TCovD nodes.
Not a TExpr."""
struct CovDHead
    name::Symbol
end
```

### 3.4 Construction via Overloading

#### Tensor application

```julia
# T[-a, -b] calls getindex(::TensorHead, ::SlotIdx...)
function Base.getindex(t::TensorHead, indices::SlotIdx...)
    _validate_tensor_indices(t.name, indices)
    TTensor(t, collect(indices))
end

# Rank-0 tensors: RS[] calls getindex(::TensorHead) with no index args
function Base.getindex(t::TensorHead)
    _validate_tensor_indices(t.name, ())
    TTensor(t, SlotIdx[])
end
```

#### Arithmetic

```julia
Base.:*(a::TExpr, b::TExpr) = TProd(1//1, _flatten_prod(1//1, [a, b]))
Base.:+(a::TExpr, b::TExpr) = TSum(_flatten_sum([a, b]))
Base.:-(a::TExpr, b::TExpr) = TSum(_flatten_sum([a, TProd(-1//1, [b])]))
Base.:-(a::TExpr) = TProd(-1//1, [a])

# Scalar * TExpr (restrict to exact numeric types)
Base.:*(c::Union{Integer, Rational}, a::TExpr) = TProd(Rational{Int}(c), _flatten_prod(1//1, [a]))
Base.:*(a::TExpr, c::Union{Integer, Rational}) = c * a
```

> **Note:** Float coefficients are not supported to avoid silent precision
> loss via `Rational{Int}(0.3)`. Use exact rationals: `(1//3) * T[-a,-b]`.

#### Flattening helpers

```julia
"""Flatten nested TProd into a single flat factor list, merging coefficients."""
function _flatten_prod(coeff::Rational{Int}, nodes::Vector{<:TExpr})
    factors = TExpr[]
    merged_coeff = coeff
    for node in nodes
        if node isa TProd
            merged_coeff *= node.coeff
            append!(factors, node.factors)
        elseif node isa TScalar
            merged_coeff *= node.value
        else
            push!(factors, node)
        end
    end
    # If all factors were scalars, return a TScalar
    if isempty(factors)
        return TExpr[TScalar(merged_coeff)]
    end
    # Store the final merged coefficient; return the flat factor list
    # (caller wraps in TProd with merged_coeff)
    return factors
end

# For TProd construction with flattening:
function _make_prod(coeff::Rational{Int}, nodes::Vector{<:TExpr})
    flat = TExpr[]
    c = coeff
    for node in nodes
        if node isa TProd
            c *= node.coeff
            append!(flat, node.factors)
        elseif node isa TScalar
            c *= node.value
        else
            push!(flat, node)
        end
    end
    isempty(flat) ? TScalar(c) : TProd(c, flat)
end

"""Flatten nested TSum into a single flat term list."""
function _flatten_sum(nodes::Vector{<:TExpr})
    terms = TExpr[]
    for node in nodes
        if node isa TSum
            append!(terms, node.terms)
        else
            push!(terms, node)
        end
    end
    terms
end
```

#### Covariant derivative construction

```julia
"""
    covd(name::Symbol) -> CovDHead

Create a covariant derivative head. Used to build TCovD expression nodes.
"""
function covd(name::Symbol)
    # Validate that this CovD is registered (it's a key in _metrics)
    haskey(_metrics, name) || error("Covariant derivative $name is not defined")
    CovDHead(name)
end
covd(name::String) = covd(Symbol(name))

# CD[-a] returns a callable that wraps an expression in TCovD
function Base.getindex(c::CovDHead, idx::SlotIdx)
    _CovDApplicator(c.name, idx)
end

"""Intermediate callable: CD[-a] produces this, then CD[-a](expr) applies it."""
struct _CovDApplicator
    covd::Symbol
    index::SlotIdx
end

# CD[-a](expr) creates the TCovD node
(app::_CovDApplicator)(operand::TExpr) = TCovD(app.covd, app.index, operand)
```

Usage:
```julia
CD = covd(:CD)
expr = CD[-a](CD[-b](phi[]))    # double covariant derivative
```

### 3.5 Tensor Head Constructors

```julia
"""
    tensor(name::Symbol) -> TensorHead

Look up a registered tensor and return a TensorHead handle.
Throws if the tensor is not defined or was unregistered by reset_state!().
"""
function tensor(name::Symbol)
    haskey(_tensors, name) ||
        error("Tensor $name is not defined (was reset_state!() called?)")
    TensorHead(name)
end

tensor(name::String) = tensor(Symbol(name))
```

For rank-0 tensors (scalars like RicciScalarCD), `tensor()` returns a
`TensorHead` and the user writes `RS[]` to get a `TTensor` usable in
expressions:

```julia
RS = tensor(:RicciScalarCD)

# RS alone is a TensorHead (not TExpr) — can't use in arithmetic
# RS[] is a TTensor with empty index list — valid TExpr
Simplify(RS[] * g[-a,-b])
```

### 3.6 Display

```julia
# REPL display uses the string-serialization form
Base.show(io::IO, e::TExpr) = print(io, _to_string(e))
Base.show(io::IO, i::Idx) = print(io, i.label)
Base.show(io::IO, i::DnIdx) = print(io, "-", i.parent.label)
Base.show(io::IO, t::TensorHead) = print(io, "TensorHead(:", t.name, ")")
```

```
julia> @indices M a b c d
julia> Riem = tensor(:RiemannCD)
julia> Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b]
RiemannCD[-a,-b,-c,-d] + RiemannCD[-a,-c,-d,-b]
```

## 4. Validation Rules

### 4.1 At Index Construction (Idx constructor)

Validation happens at runtime in the `Idx` inner constructor (Section 3.1),
not at macro-expansion time. The `@indices` macro simply generates `Idx()`
calls which validate when executed.

```julia
@indices M a b c d e f
# At runtime: Idx(:a, :M) checks :a in _manifolds[:M].index_labels
# ERROR if manifold :M is not defined or :a is not one of its indices
```

### 4.2 At Tensor Application (`getindex`)

```julia
function _validate_tensor_indices(name::Symbol, indices)
    haskey(_tensors, name) ||
        error("Tensor $name is not defined (was reset_state!() called?)")
    tobj = _tensors[name]

    # 1. Slot count
    length(indices) == length(tobj.slots) ||
        error("$name has $(length(tobj.slots)) slots, got $(length(indices))")

    # 2. Manifold match
    for (i, idx) in enumerate(indices)
        bare = idx isa DnIdx ? idx.parent : idx
        bare.manifold == tobj.manifold ||
            error("Index $(bare.label) is from manifold $(bare.manifold), "
                  * "but slot $i of $(name) expects $(tobj.manifold)")
    end

    # 3. Variance match — intentionally not enforced.
    # Users may freely raise/lower indices; the engine handles this
    # via metric contraction. Enforcing variance would prevent valid
    # expressions like V[-a] (a vector with lowered index).
end
```

### 4.3 At Expression Construction (optional)

```julia
"""Validate that all terms in a sum have the same free indices."""
function _validate_sum(expr::TSum)
    reference = _free_indices(expr.terms[1])
    for term in expr.terms[2:end]
        got = _free_indices(term)
        got == reference ||
            error("Free-index mismatch in sum: expected $reference, got $got")
    end
end
```

This is opt-in (not called automatically) because:
- It's O(n) in term count, which matters for large expressions
- The engine catches this anyway during processing
- Some intermediate constructions may transiently have mismatched indices

## 5. String Conversion (Serialization)

Every `TExpr` converts to the string format the engine expects.

```julia
function _to_string(i::Idx)::String
    string(i.label)
end

function _to_string(i::DnIdx)::String
    "-" * string(i.parent.label)
end

function _to_string(t::TTensor)::String
    if isempty(t.indices)
        "$(t.head.name)[]"
    else
        idx_str = join([_to_string(i) for i in t.indices], ",")
        "$(t.head.name)[$idx_str]"
    end
end

function _to_string(s::TScalar)::String
    if s.value.den == 1
        string(s.value.num)
    else
        "($(s.value.num)/$(s.value.den))"
    end
end

function _to_string(p::TProd)::String
    parts = [_to_string_factor(f) for f in p.factors]
    body = join(parts, " * ")
    if p.coeff == 1//1
        body
    elseif p.coeff == -1//1
        "-" * body
    elseif p.coeff.den == 1
        "$(p.coeff.num) * $body"
    else
        "($(p.coeff.num)/$(p.coeff.den)) * $body"
    end
end

"""Serialize a factor inside a product, adding parentheses around sums."""
function _to_string_factor(f::TExpr)::String
    if f isa TSum
        "(" * _to_string(f) * ")"
    else
        _to_string(f)
    end
end

function _to_string(s::TSum)::String
    isempty(s.terms) && return "0"
    buf = IOBuffer()
    for (i, term) in enumerate(s.terms)
        if i == 1
            print(buf, _to_string(term))
        else
            # Extract sign from TProd coefficient for clean formatting
            str = _to_string(term)
            if startswith(str, "-")
                print(buf, " - ", str[2:end])
            else
                print(buf, " + ", str)
            end
        end
    end
    String(take!(buf))
end

function _to_string(c::TCovD)::String
    idx_str = _to_string(c.index)
    op_str = _to_string(c.operand)
    "$(c.covd)[$idx_str][$op_str]"
end

# Engine functions accept TExpr via string conversion
ToCanonical(expr::TExpr) = ToCanonical(_to_string(expr))
Contract(expr::TExpr) = Contract(_to_string(expr))
Simplify(expr::TExpr) = Simplify(_to_string(expr))
CommuteCovDs(expr::TExpr, covd, i1, i2) = CommuteCovDs(_to_string(expr), covd, i1, i2)
SortCovDs(expr::TExpr, covd) = SortCovDs(_to_string(expr), covd)
perturb(expr::TExpr, order::Int) = perturb(_to_string(expr), order)
IBP(expr::TExpr, covd) = IBP(_to_string(expr), covd)
TotalDerivativeQ(expr::TExpr, covd) = TotalDerivativeQ(_to_string(expr), covd)
VarD(expr::TExpr, field, covd) = VarD(_to_string(expr), field, covd)
```

> **Stage 1 note:** All engine functions return `String`, not `TExpr`.
> This means the first operation in a chain uses typed syntax but subsequent
> operations fall back to strings:
> ```julia
> r1 = ToCanonical(Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b])  # String
> r2 = Contract(r1)  # String in, string out — works fine
> ```
> Full typed round-tripping (TExpr in, TExpr out) comes in Stage 2.

## 6. API Examples

### 6.1 Julia — Basic Workflow

```julia
using xAct

reset_state!()

# 1. Define manifold and metric
def_manifold!(:M, 4, [:a, :b, :c, :d, :e, :f])
def_metric!(-1, "g[-a,-b]", :CD)

# 2. Create index objects
@indices M a b c d e f

# 3. Get tensor heads
g    = tensor(:g)
Riem = tensor(:RiemannCD)
Ric  = tensor(:RicciCD)
RS   = tensor(:RicciScalarCD)

# 4. Build and simplify expressions
# First Bianchi identity
expr = Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c]
ToCanonical(expr)  # "0"

# Pair symmetry
ToCanonical(Riem[-a,-b,-c,-d] - Riem[-c,-d,-a,-b])  # "0"

# Metric contraction
def_tensor!(:V, ["a"], :M)
V = tensor(:V)
Contract(V[a] * g[-a,-b])  # "V[-b]"

# Rank-0 (scalar) in expressions
Simplify(RS[] * g[-a,-b])

# Error catching at construction time
Riem[-a,-b,-c]  # ERROR: RiemannCD has 4 slots, got 3
```

### 6.2 Julia — Perturbation Theory

```julia
def_tensor!(:h, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")
def_perturbation!(:h, :g, 1)

h = tensor(:h)

perturb(g[-a,-b], 1)  # "h[-a,-b]"
```

### 6.3 Julia — Covariant Derivatives

```julia
def_tensor!(:phi, String[], :M)  # scalar field
phi = tensor(:phi)

# Build CovD expressions
CD = covd(:CD)
expr = CD[-a](CD[-b](phi[]))     # nabla_a nabla_b phi
CommuteCovDs(_to_string(expr), "CD", "-a", "-b")

# Nested: derivative of a tensor
def_tensor!(:T, ["-a", "-b"], :M; symmetry_str="Symmetric[{-a,-b}]")
T = tensor(:T)
expr2 = CD[-c](T[-a,-b])         # nabla_c T_ab
```

### 6.4 Python — Full Workflow

```python
import xact

xact.reset()

# Define geometry
M = xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])
g = xact.Metric(M, "g", signature=-1, covd="CD")

# Create typed indices
a, b, c, d, e, f = xact.indices(M)

# Tensor heads via lookup
Riem = xact.tensor("RiemannCD")
Ric  = xact.tensor("RicciCD")

# New tensors — Tensor gains __getitem__
T = xact.Tensor("T", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")
V = xact.Tensor("V", ["a"], M)

# Build expressions with operator overloading
expr = Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b] + Riem[-a,-d,-b,-c]
xact.canonicalize(expr)  # "0"

# Contraction — Metric gains __getitem__ for use in expressions
xact.contract(V[a] * g[-a,-b])  # "V[-b]"

# Type errors caught at construction time
T[-a, -b, -c]  # IndexError: T has 2 slots, got 3
```

#### Python Implementation Notes

```python
class Idx:
    """Abstract index bound to a manifold."""
    __slots__ = ("label", "manifold")

    def __init__(self, label: str, manifold: str):
        self.label = label
        self.manifold = manifold

    def __neg__(self) -> DnIdx:
        return DnIdx(self)

    def __repr__(self) -> str:
        return self.label


class DnIdx:
    """Covariant (down) index."""
    __slots__ = ("parent",)

    def __init__(self, parent: Idx):
        self.parent = parent

    def __neg__(self) -> Idx:
        """Double negation returns the bare index."""
        return self.parent

    def __repr__(self) -> str:
        return f"-{self.parent.label}"


SlotIdx = Idx | DnIdx


def indices(manifold: Manifold) -> tuple[Idx, ...]:
    """Create Idx objects for all indices of a manifold."""
    return tuple(Idx(label, manifold.name) for label in manifold.indices)


def tensor(name: str) -> TensorHead:
    """Look up a registered tensor and return a TensorHead handle."""
    _, mod = _ensure_init()
    # Validate that the tensor exists in the Julia registry
    if not bool(mod.haskey_tensors(name)):
        raise ValueError(f"Tensor {name!r} is not defined")
    return TensorHead(name)
```

The `Tensor` and `Metric` classes gain `__getitem__`:

```python
class TensorHead:
    """Lightweight handle for a registered tensor. Supports T[-a, -b] syntax."""
    def __init__(self, name: str):
        self.name = name

    def __getitem__(self, indices: SlotIdx | tuple[SlotIdx, ...]) -> AppliedTensor:
        if not isinstance(indices, tuple):
            indices = (indices,)
        _validate_indices(self.name, indices)
        return AppliedTensor(self, list(indices))

    def __repr__(self) -> str:
        return f"TensorHead({self.name!r})"


class Tensor:
    # ... existing __init__ unchanged ...

    def __getitem__(self, indices: SlotIdx | tuple[SlotIdx, ...]) -> AppliedTensor:
        if not isinstance(indices, tuple):
            indices = (indices,)
        _validate_indices(self.name, indices)
        return AppliedTensor(TensorHead(self.name), list(indices))


class Metric:
    # ... existing __init__ unchanged ...

    def __getitem__(self, indices: SlotIdx | tuple[SlotIdx, ...]) -> AppliedTensor:
        if not isinstance(indices, tuple):
            indices = (indices,)
        _validate_indices(self.name, indices)
        return AppliedTensor(TensorHead(self.name), list(indices))
```

`AppliedTensor` and other expression types implement `__add__`, `__sub__`,
`__mul__`, `__neg__`, `__str__`:

```python
class AppliedTensor:
    """A tensor with indices applied. Implements TExpr arithmetic."""
    def __init__(self, head: TensorHead, indices: list[SlotIdx]):
        self.head = head
        self.indices = indices

    def __add__(self, other): ...   # returns SumExpr
    def __sub__(self, other): ...   # returns SumExpr
    def __mul__(self, other): ...   # returns ProdExpr
    def __neg__(self): ...          # returns ProdExpr with coeff=-1

    def __str__(self) -> str:
        idx = ",".join(str(i) for i in self.indices)
        return f"{self.head.name}[{idx}]"
```

## 7. Interaction with Canonicalization Engine

The typed API is a **thin layer above** the existing engine:

```
User code          Typed layer              Engine (unchanged)
---------          -----------              ------------------
T[-a,-b]     ->   TTensor(:T, [DnIdx..])
                       |
                  _to_string()
                       |
                  "T[-a,-b]"         ->    _parse_expression()
                                           _canonicalize_term()
                                           canonicalize_slots()   <- XPerm
                                           _apply_identities!()
                                           _serialize()
                                                |
                  result string      <-    "T[-a,-b]"
```

**XPerm is completely untouched.** It operates on string indices and slot
positions. The typed layer converts to strings at the boundary.

### Future: Typed Output (Stage 2)

In a later stage, engine functions return `TExpr` directly:

```julia
ToCanonical(expr::TExpr)::TExpr  # parse result string back into TExpr
```

This requires a `_parse_to_texpr(result_str)` function that maps result
strings back to typed expressions using the current index/tensor registries.
Tractable because the engine output format is well-defined.

## 8. def_* Functions — Return Value Changes

**Recommendation**: Add `tensor()` and `covd()` lookup functions.
No changes to existing `def_*!` return types.

```julia
# Existing (unchanged)
def_tensor!(:T, ["-a", "-b"], :M) :: TensorObj
def_metric!(-1, "g[-a,-b]", :CD) :: MetricObj

# New convenience lookups
tensor(:T) :: TensorHead
tensor(:RiemannCD) :: TensorHead   # auto-created by def_metric!
covd(:CD) :: CovDHead
```

This is non-breaking. Existing code that ignores the return value of
`def_tensor!` continues to work. Users of the typed API call `tensor()`
to get handles.

## 9. Prior Art Analysis

| Package | Approach | Relevance to sxAct |
|---------|----------|-------------------|
| **SymbolicUtils.jl** | Tagged union `BasicSymbolic{T}` with 6 variants | Model for minimal expression types |
| **Symbolics.jl** | `Num <: Real` wrapper around expression tree | Model for "wrapper over engine" pattern |
| **TensorOperations.jl** | `@tensor` macro, compile-time lowering | Good for fixed contractions; not suitable for CAS (no lazy expressions) |
| **ITensors.jl** | `Index` objects with identity + `*` for contraction | Index-as-object pattern; but numerical, not symbolic |
| **TensorKit.jl** | Category-theoretic `AbstractTensorMap{T,S,N1,N2}` | Over-engineered for a CAS; rigid domain/codomain split |
| **Mathematica xAct** | Head-as-tensor, upvalue metadata, pattern matching | Direct inspiration; translate upvalue pattern -> Julia registry |

**Key lessons applied:**
- From SymbolicUtils: Few types, flat hierarchy, `operation/arguments` interface
- From Symbolics: Wrapper pattern -- light types that delegate to a powerful engine
- From ITensors: Index-as-object with identity is powerful and natural
- From TensorOperations: Macros are good for declaration, but runtime types needed for CAS manipulation
- From xAct: Abstract index paradigm with manifold/bundle typing is the right model for GR

## 10. File Placement

### Julia

New file: **`src/TExpr.jl`**

Contains all typed expression types, `@indices`, `tensor()`, `covd()`,
`_to_string()`, `_validate_tensor_indices()`, `_flatten_*` helpers,
`show()` methods, and `TExpr` method overloads for engine functions.

Included from `xAct.jl` after `XTensor.jl` (needs access to `_tensors`,
`_manifolds`, `_metrics` registries).

### Python

Additions to existing **`packages/xact-py/src/xact/`**:

- `expr.py` — `Idx`, `DnIdx`, `TensorHead`, `AppliedTensor`, `SumExpr`,
  `ProdExpr`, `CovDExpr`, `indices()`, `tensor()` functions
- `api.py` — Add `TExpr` overloads to `canonicalize()`, `contract()`, etc.
  Add `__getitem__` to `Tensor` and `Metric` classes.
- `__init__.py` — Re-export new public names

## 11. Migration Strategy

> **Note:** These stages are independent of the Invar pipeline phases
> (Phases 4-11 in `plans/2026-03-11-multi-term-symmetry-engine.md`).
> To avoid confusion, we use "Stage" here.

### Stage 1: Typed Construction (non-breaking)

**Scope:** `Idx`, `DnIdx`, `TensorHead`, `CovDHead`, `TTensor`, `TProd`,
`TSum`, `TCovD`, `TScalar`. `@indices` macro. `tensor()` and `covd()`
lookups. `_to_string()` serialization. `show()` methods. `TExpr` overloads
for all engine functions.

**Effort:** ~350 lines Julia (`src/TExpr.jl`), ~200 lines Python
(`expr.py` + `api.py` changes).

**Migration:** Zero breaking changes. String API unchanged. Both APIs coexist:

```julia
# Old (still works)
ToCanonical("T[-b,-a] - T[-a,-b]")

# New (also works)
ToCanonical(T[-b,-a] - T[-a,-b])
```

**Limitation:** Engine functions return `String`, not `TExpr`. Multi-step
workflows after the first operation use the string API. This is acceptable
because the string API is already functional.

### Stage 2: Typed Output

**Scope:** `_parse_to_texpr()` parser. Engine functions gain `TExpr` return
overloads. Full round-trip: `TExpr -> String -> engine -> String -> TExpr`.

**Depends on:** Stage 1 stable.

**Effort:** ~200 lines Julia, ~100 lines Python.

### Stage 3: Rich Display

**Scope:** Unicode math rendering in REPL. LaTeX output for Jupyter/Quarto
notebooks.

**Examples:**
```
julia> Riem[-a,-b,-c,-d] + Riem[-a,-c,-d,-b]
R_{abcd} + R_{acdb}

julia> display(MIME"text/latex"(), expr)
R_{abcd} + R_{acdb}
```

### Stage 4: Expression Introspection

**Scope:** `free_indices()`, `dummy_indices()`, `rank()`, `factors()`,
`terms()`, `head()`. Programmatic expression manipulation.

### Not Planned

- Replacing the string engine internals with typed ASTs (unnecessary)
- Macro-only approach without runtime types (insufficient for CAS)
- Type-parameterized tensors `TTensor{N}` (premature optimization)
- Float coefficients (use `Rational{Int}` for exactness)

## 12. Recommendation

**Do it.** Implement Stage 1 now.

The typed expression API provides significant UX improvements with minimal
engineering cost and zero risk to the existing engine:

- **~550 lines** total (Julia + Python) for Stage 1
- **Non-breaking** — pure addition to the existing API
- **Validates at construction** — catches errors early
- **Composes naturally** — Julia/Python operator overloading
- **Discoverable** — tab-completion on tensor heads and indices

The key insight from SymbolicUtils and Symbolics is that a thin typed
wrapper over a working engine is vastly simpler than rewriting the engine.
Our string engine (5000+ lines of XTensor.jl, 400+ tests) is battle-tested
-- the typed layer delegates to it.

Stage 1 can be implemented independently of all Invar pipeline work. It
touches no existing code paths -- only adds new types and method signatures.
