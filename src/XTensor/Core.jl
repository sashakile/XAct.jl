# ============================================================
# Types
# ============================================================

"""
An abstract index slot: the declared label and its variance.
"""
struct IndexSpec
    label::Symbol    # e.g. :a (without the '-' prefix)
    covariant::Bool  # true ↔ '-a' (covariant/down); false ↔ 'a' (contravariant/up)
end

struct ManifoldObj
    name::Symbol
    dimension::Int
    index_labels::Vector{Symbol}   # declared abstract index names (without '-')
end

struct VBundleObj
    name::Symbol          # e.g. :TangentM
    manifold::Symbol
    index_labels::Vector{Symbol}
end

"""
Describes the permutation symmetry of a tensor's slot group.
type  — one of: :Symmetric, :Antisymmetric, :GradedSymmetric, :RiemannSymmetric, :YoungSymmetry, :NoSymmetry
slots — 1-indexed positions (within this tensor's slot list) that the symmetry acts on.
For :RiemannSymmetric, exactly 4 elements.
For :NoSymmetry, empty.
"""
struct SymmetrySpec
    type::Symbol
    slots::Vector{Int}
    partition::Vector{Int}  # non-empty for :YoungSymmetry only
end
SymmetrySpec(type::Symbol, slots::Vector{Int}) = SymmetrySpec(type, slots, Int[])

"""
A fully defined tensor object.
"""
struct TensorObj
    name::Symbol
    slots::Vector{IndexSpec}   # declared slot list
    manifold::Symbol
    symmetry::SymmetrySpec
end

struct MetricObj
    name::Symbol
    manifold::Symbol
    covd::Symbol     # name of auto-created covariant derivative
    signdet::Int     # +1 (Riemannian) or -1 (Lorentzian)
end

"""
A perturbation of a tensor: records the perturbed tensor name, its background
tensor name, and the perturbation order (1 = first order, 2 = second order, ...).
"""
struct PerturbationObj
    name::Symbol        # e.g. :Pertg1 (the perturbed tensor)
    background::Symbol  # e.g. :g (the background tensor)
    order::Int          # perturbation order ≥ 1
end

"""
A basis of vector fields on a vector bundle (non-coordinate frame).
Created by `def_basis!` or internally by `def_chart!`.
"""
struct BasisObj
    name::Symbol            # e.g. :tetrad
    vbundle::Symbol         # e.g. :TangentM
    cnumbers::Vector{Int}   # integer labels for basis elements, length == dim
    parallel_deriv::Symbol  # auto-created parallel derivative
    is_chart::Bool          # true if created by def_chart!
end

"""
A coordinate chart on a manifold. Internally creates a BasisObj.
"""
struct ChartObj
    name::Symbol            # e.g. :Schw (also the basis name)
    manifold::Symbol        # e.g. :M
    cnumbers::Vector{Int}   # coordinate integer labels
    scalars::Vector{Symbol} # coordinate scalar fields, e.g. [:t, :r, :theta, :phi]
end

"""
A coordinate transformation between two bases (stored as matrix + inverse + jacobian).
"""
struct BasisChangeObj{T<:Number}
    from_basis::Symbol      # source basis name
    to_basis::Symbol        # target basis name
    matrix::Matrix{T}       # transformation matrix (n×n)
    inverse::Matrix{T}      # inverse matrix
    jacobian::T             # determinant of matrix (cached)
end

"""
A component tensor: stores explicit numerical values of a tensor in a given basis.
"""
struct CTensorObj{T<:Number,N}
    tensor::Symbol          # which abstract tensor this represents (e.g. :g)
    array::Array{T,N}       # N-dimensional array of component values
    bases::Vector{Symbol}   # basis for each slot (length == ndims(array))
    weight::Int             # density weight (usually 0)
end

"""
Convert an array to a concrete numeric array, promoting Any elements.
"""
function _to_numeric_array(a::AbstractArray{T}) where {T<:Number}
    return Array(a)
end
function _to_numeric_array(a::AbstractArray)
    # Promote Any arrays: infer numeric type from elements without full copy
    isempty(a) && return Array{Float64}(a)
    T = mapreduce(typeof, promote_type, a)
    T <: Number || error("set_components!: array contains non-numeric elements of type $T")
    return Array{T}(a)
end

"""
    MultiTermIdentity

A multi-term identity relating N canonical tensor terms by a linear relation.

The identity asserts: Σᵢ coefficients[i] * T[slot_perms[i](free_indices)] = 0

Fields:

  - `name`: identity label (e.g. :FirstBianchi)
  - `tensor`: which tensor this applies to (e.g. :RiemannCD)
  - `n_slots`: total tensor rank (4 for Riemann)
  - `fixed_slots`: slot positions held constant across terms
  - `cycled_slots`: slot positions permuted across terms
  - `slot_perms`: for each term, the rank-permutation of cycled_slot values
  - `coefficients`: coefficient of each term in the identity (Σ coefficients[i] * X_i = 0)
  - `eliminate`: which term index to eliminate (reduce away)

Example — First Bianchi identity R_{a[bcd]} = 0:
Three canonical forms for 4 distinct indices p < q < r < s:
X₁ = R[p,q,r,s]  →  cycled ranks [1,2,3]
X₂ = R[p,r,q,s]  →  cycled ranks [2,1,3]
X₃ = R[p,s,q,r]  →  cycled ranks [3,1,2]
Identity: X₁ - X₂ + X₃ = 0;  eliminate X₃.
"""
struct MultiTermIdentity
    name::Symbol
    tensor::Symbol
    n_slots::Int
    fixed_slots::Vector{Int}
    cycled_slots::Vector{Int}
    slot_perms::Vector{Vector{Int}}
    coefficients::Vector{Rational{Int}}
    eliminate::Int
end

# ============================================================
# Session struct
# ============================================================

"""
    Session

Holds all mutable state for one xAct session. Replaces 22 global containers.
Enables concurrent sessions, proper reset semantics, and structural thread safety.

The default session shares its dict objects with the module-level globals, so
existing code that reads/writes globals implicitly uses the default session.
"""
mutable struct Session
    generation::Int

    # Primary registries
    manifolds::Dict{Symbol,ManifoldObj}
    vbundles::Dict{Symbol,VBundleObj}
    tensors::Dict{Symbol,TensorObj}
    metrics::Dict{Symbol,MetricObj}
    perturbations::Dict{Symbol,PerturbationObj}
    bases::Dict{Symbol,BasisObj}
    charts::Dict{Symbol,ChartObj}
    basis_changes::Dict{Tuple{Symbol,Symbol},BasisChangeObj{<:Number}}
    ctensors::Dict{Tuple{Symbol,Vararg{Symbol}},CTensorObj{<:Number}}

    # Reverse-lookup indices
    metric_name_index::Dict{Symbol,Symbol}
    parallel_deriv_index::Dict{Symbol,Symbol}

    # Ordered lists (insertion order)
    manifold_list::Vector{Symbol}
    tensor_list::Vector{Symbol}
    vbundle_list::Vector{Symbol}
    perturbation_list::Vector{Symbol}
    basis_list::Vector{Symbol}
    chart_list::Vector{Symbol}

    # Contract support
    traceless_tensors::Set{Symbol}
    trace_scalars::Dict{Symbol,Tuple{Symbol,Rational{Int}}}
    einstein_expansion::Dict{Symbol,Tuple{Symbol,Symbol,Symbol}}

    # Multi-term identities
    identity_registry::Dict{Symbol,Vector{MultiTermIdentity}}

    # Symbol validation hooks
    validate_symbol_hook::Function
    register_symbol_hook::Function
end

"""
    Session()

Create a new empty Session with generation 0 and no-op symbol hooks.
"""
function Session()
    Session(
        0,
        Dict{Symbol,ManifoldObj}(),
        Dict{Symbol,VBundleObj}(),
        Dict{Symbol,TensorObj}(),
        Dict{Symbol,MetricObj}(),
        Dict{Symbol,PerturbationObj}(),
        Dict{Symbol,BasisObj}(),
        Dict{Symbol,ChartObj}(),
        Dict{Tuple{Symbol,Symbol},BasisChangeObj{<:Number}}(),
        Dict{Tuple{Symbol,Vararg{Symbol}},CTensorObj{<:Number}}(),
        Dict{Symbol,Symbol}(),
        Dict{Symbol,Symbol}(),
        Symbol[],
        Symbol[],
        Symbol[],
        Symbol[],
        Symbol[],
        Symbol[],
        Set{Symbol}(),
        Dict{Symbol,Tuple{Symbol,Rational{Int}}}(),
        Dict{Symbol,Tuple{Symbol,Symbol,Symbol}}(),
        Dict{Symbol,Vector{MultiTermIdentity}}(),
        (_) -> nothing,
        (_, _) -> nothing,
    )
end

"""
    reset_session!(s::Session)

Clear all state in session `s` and increment its generation counter.
"""
function reset_session!(s::Session)
    s.generation += 1
    empty!(s.manifolds)
    empty!(s.vbundles)
    empty!(s.tensors)
    empty!(s.metrics)
    empty!(s.perturbations)
    empty!(s.bases)
    empty!(s.charts)
    empty!(s.basis_changes)
    empty!(s.ctensors)
    empty!(s.metric_name_index)
    empty!(s.parallel_deriv_index)
    empty!(s.manifold_list)
    empty!(s.tensor_list)
    empty!(s.vbundle_list)
    empty!(s.perturbation_list)
    empty!(s.basis_list)
    empty!(s.chart_list)
    empty!(s.traceless_tensors)
    empty!(s.trace_scalars)
    empty!(s.einstein_expansion)
    empty!(s.identity_registry)
    nothing
end

# ============================================================
# Global state
# ============================================================

const _manifolds = Dict{Symbol,ManifoldObj}()
const _vbundles = Dict{Symbol,VBundleObj}()
const _tensors = Dict{Symbol,TensorObj}()
const _metrics = Dict{Symbol,MetricObj}()
const _metric_name_index = Dict{Symbol,Symbol}()  # metric tensor name → covd name
const _perturbations = Dict{Symbol,PerturbationObj}()
const _bases = Dict{Symbol,BasisObj}()
const _parallel_deriv_index = Dict{Symbol,Symbol}()  # parallel_deriv → basis name
const _charts = Dict{Symbol,ChartObj}()
const _basis_changes = Dict{Tuple{Symbol,Symbol},BasisChangeObj{<:Number}}()
const _ctensors = Dict{Tuple{Symbol,Vararg{Symbol}},CTensorObj{<:Number}}()

const Manifolds = Symbol[]   # ordered list
const Tensors = Symbol[]
const VBundles = Symbol[]
const Perturbations = Symbol[]   # perturbation tensor names (ordered)
const Bases = Symbol[]
const Charts = Symbol[]

# Contract support: physics rules
# Tensors whose full trace vanishes (e.g. Weyl tensor)
const _traceless_tensors = Set{Symbol}()
# Trace rules: trace_of_tensor → (scalar_tensor_name, Int_coefficient)
# e.g. EinsteinXXX → (:RicciScalarXXX, -1)  meaning tr(G) = -1 * R
const _trace_scalars = Dict{Symbol,Tuple{Symbol,Rational{Int}}}()

# Einstein expansion rules: EinsteinXXX → (RicciXXX, metricXXX, RicciScalarXXX)
# Allows ToCanonical to substitute G_{ab} = R_{ab} - (1/2) g_{ab} R
const _einstein_expansion = Dict{Symbol,Tuple{Symbol,Symbol,Symbol}}()

# Multi-term identity registry: tensor name → list of identities
# Auto-populated by def_tensor! for RiemannSymmetric tensors (first Bianchi).
const _identity_registry = Dict{Symbol,Vector{MultiTermIdentity}}()

# ============================================================
# Symbol validation hooks
# ============================================================
#
# XTensor runs standalone (no XCore dependency at module level).
# When loaded via XAct.jl, set_symbol_hooks! wires in XCore.ValidateSymbol
# and XCore.register_symbol so that every def_*! call validates names against
# the global xAct symbol registry.  In standalone mode, the hooks are no-ops
# and validation is limited to XTensor's own session-level checks.

const _validate_symbol_hook = Ref{Function}((_) -> nothing)
const _register_symbol_hook = Ref{Function}((_, _) -> nothing)

# Default session: fields SHARE the same Dict objects as the globals above.
# Any code that reads/writes _manifolds also reads/writes _default_session[].manifolds.
const _default_session = Ref{Session}(
    Session(
        0,
        _manifolds,
        _vbundles,
        _tensors,
        _metrics,
        _perturbations,
        _bases,
        _charts,
        _basis_changes,
        _ctensors,
        _metric_name_index,
        _parallel_deriv_index,
        Manifolds,
        Tensors,
        VBundles,
        Perturbations,
        Bases,
        Charts,
        _traceless_tensors,
        _trace_scalars,
        _einstein_expansion,
        _identity_registry,
        _validate_symbol_hook[],
        _register_symbol_hook[],
    ),
)

"""
    set_symbol_hooks!(validate, register)

Install XCore symbol-validation and registration hooks.

Called by XAct.jl after loading both XCore and XTensor:

    XTensor.set_symbol_hooks!(XCore.ValidateSymbol, XCore.register_symbol)
"""
function set_symbol_hooks!(validate::Function, register::Function)
    _validate_symbol_hook[] = validate
    _register_symbol_hook[] = register
    _default_session[].validate_symbol_hook = validate
    _default_session[].register_symbol_hook = register
    nothing
end

"""
    ValidateSymbolInSession(name::Symbol)

Check that `name` is not already used as a manifold, tensor, metric, vbundle,
covariant derivative, or perturbation in the current session.  Throws on
collision.  Analogous to Wolfram `ValidateSymbolInSession`.
"""
function ValidateSymbolInSession(name::Symbol; session::Session=_default_session[])
    sname = string(name)
    hint = " Call reset_state!() to clear all definitions or choose a different name."
    ManifoldQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a manifold." * hint
        ),
    )
    VBundleQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a vector bundle." * hint,
        ),
    )
    MetricQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a metric." * hint
        ),
    )
    TensorQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a tensor." * hint
        ),
    )
    CovDQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a covariant derivative." *
            hint,
        ),
    )
    PerturbationQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a perturbation." * hint
        ),
    )
    BasisQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a basis." * hint
        ),
    )
    ChartQ(name; session) && throw(
        ArgumentError(
            "ValidateSymbolInSession: \"$sname\" already used as a chart." * hint
        ),
    )
    nothing
end
function ValidateSymbolInSession(name::AbstractString; session::Session=_default_session[])
    ValidateSymbolInSession(Symbol(name); session)
end

# ============================================================
# State management
# ============================================================

function reset_state!()
    reset_session!(_default_session[])
end

# ============================================================
# Multi-term identity framework
# ============================================================

"""
    RegisterIdentity!(tensor_name, identity)

Register a multi-term identity for a tensor. Identities are applied during
canonicalization by `_apply_identities!`.
"""
function RegisterIdentity!(
    tensor_name::Symbol, identity::MultiTermIdentity; session::Session=_default_session[]
)
    if !haskey(session.identity_registry, tensor_name)
        session.identity_registry[tensor_name] = MultiTermIdentity[]
    end
    push!(session.identity_registry[tensor_name], identity)
    nothing
end

"""
    _make_bianchi_identity(tensor_name)

Construct the first Bianchi identity R_{a[bcd]} = 0 for a 4-slot tensor
with RiemannSymmetric symmetry.

Canonical forms for indices p < q < r < s:
X₁ = R[p,q,r,s]  →  cycled ranks [1,2,3]
X₂ = R[p,r,q,s]  →  cycled ranks [2,1,3]
X₃ = R[p,s,q,r]  →  cycled ranks [3,1,2]
Identity: X₁ - X₂ + X₃ = 0;  eliminate X₃.
"""
function _make_bianchi_identity(tensor_name::Symbol)
    MultiTermIdentity(
        :FirstBianchi,
        tensor_name,
        4,
        [1],
        [2, 3, 4],
        [[1, 2, 3], [2, 1, 3], [3, 1, 2]],
        [1 // 1, -1 // 1, 1 // 1],
        3,
    )
end

# Type alias for structured key (used before TermAST is defined)
const _StructKey = Vector{Tuple{Symbol,Vector{String}}}

"""
    _apply_identities!(coeff_map, key_order)

Apply all registered multi-term identities to the canonical term map.
Replaces the hardcoded `_bianchi_reduce!` with a general framework.
"""
function _apply_identities!(
    coeff_map::Dict{String,Rational{Int}},
    struct_map::Dict{String,_StructKey},
    key_order::Vector{String},
)
    isempty(_identity_registry) && return nothing
    for (_, identities) in _identity_registry
        for identity in identities
            _apply_single_identity!(coeff_map, struct_map, key_order, identity)
        end
    end
    nothing
end

"""
    _apply_single_identity!(coeff_map, key_order, id)

Apply one multi-term identity to the canonical term map.

Groups single-factor terms by sector (values at fixed_slots + sorted values at cycled_slots),
then for each complete sector eliminates the designated term.
"""
function _apply_single_identity!(
    coeff_map::Dict{String,Rational{Int}},
    struct_map::Dict{String,_StructKey},
    key_order::Vector{String},
    id::MultiTermIdentity,
)
    # Map: sector_key → (rank_perm → skey)
    # sector_key = (fixed_values, sorted_cycled_values)
    SectorKey = Tuple{Vector{String},Vector{String}}
    sectors = Dict{SectorKey,Dict{Vector{Int},String}}()

    for skey in key_order
        get(coeff_map, skey, 0 // 1) == 0 && continue
        sk = struct_map[skey]
        length(sk) != 1 && continue
        tname, indices = sk[1]
        tname != id.tensor && continue
        length(indices) != id.n_slots && continue

        bare = [_bare(idx) for idx in indices]
        fixed_vals = [bare[s] for s in id.fixed_slots]
        cycled_vals = [bare[s] for s in id.cycled_slots]
        sorted_cycled = sort(cycled_vals)

        sector_key = (fixed_vals, sorted_cycled)
        if !haskey(sectors, sector_key)
            sectors[sector_key] = Dict{Vector{Int},String}()
        end

        # Compute rank permutation: map each cycled value to its rank in sorted order
        rank_map = Dict{String,Int}()
        for (i, v) in enumerate(sorted_cycled)
            rank_map[v] = i
        end
        perm = [rank_map[v] for v in cycled_vals]

        sectors[sector_key][perm] = skey
    end

    # Apply identity to each complete sector
    n_terms = length(id.coefficients)
    for (_, perm_to_key) in sectors
        length(perm_to_key) < n_terms && continue

        # Check all identity terms are present
        all_present = true
        for sp in id.slot_perms
            if !haskey(perm_to_key, sp)
                all_present = false
                break
            end
        end
        all_present || continue

        elim_key = perm_to_key[id.slot_perms[id.eliminate]]
        c_e = get(coeff_map, elim_key, 0 // 1)
        iszero(c_e) && continue

        # Eliminate: X_e = -(1/c_id_e) Σ_{i≠e} c_id_i * X_i
        c_id_e = id.coefficients[id.eliminate]
        for (i, sp) in enumerate(id.slot_perms)
            i == id.eliminate && continue
            other_key = perm_to_key[sp]
            coeff_map[other_key] =
                get(coeff_map, other_key, 0 // 1) + c_e * (-id.coefficients[i] / c_id_e)
        end
        coeff_map[elim_key] = 0 // 1
    end
    nothing
end

# ============================================================
# Accessor functions
# ============================================================

function get_manifold(name::Symbol; session::Session=_default_session[])
    get(session.manifolds, name, nothing)
end
function get_tensor(name::Symbol; session::Session=_default_session[])
    get(session.tensors, name, nothing)
end
function get_vbundle(name::Symbol; session::Session=_default_session[])
    get(session.vbundles, name, nothing)
end
function get_metric(name::Symbol; session::Session=_default_session[])
    get(session.metrics, name, nothing)
end
function get_basis(name::Symbol; session::Session=_default_session[])
    get(session.bases, name, nothing)
end
function get_chart(name::Symbol; session::Session=_default_session[])
    get(session.charts, name, nothing)
end
list_manifolds(; session::Session=_default_session[]) = copy(session.manifold_list)
list_tensors(; session::Session=_default_session[]) = copy(session.tensor_list)
list_vbundles(; session::Session=_default_session[]) = copy(session.vbundle_list)
list_bases(; session::Session=_default_session[]) = copy(session.basis_list)
list_charts(; session::Session=_default_session[]) = copy(session.chart_list)

function get_manifold(name::AbstractString; session::Session=_default_session[])
    get_manifold(Symbol(name); session)
end
function get_tensor(name::AbstractString; session::Session=_default_session[])
    get_tensor(Symbol(name); session)
end
function get_vbundle(name::AbstractString; session::Session=_default_session[])
    get_vbundle(Symbol(name); session)
end
function get_metric(name::AbstractString; session::Session=_default_session[])
    get_metric(Symbol(name); session)
end
function get_basis(name::AbstractString; session::Session=_default_session[])
    get_basis(Symbol(name); session)
end
function get_chart(name::AbstractString; session::Session=_default_session[])
    get_chart(Symbol(name); session)
end

# ============================================================
# Query predicates
# ============================================================

ManifoldQ(s::Symbol; session::Session=_default_session[]) = haskey(session.manifolds, s)
function ManifoldQ(s::AbstractString; session::Session=_default_session[])
    ManifoldQ(Symbol(s); session)
end
TensorQ(s::Symbol; session::Session=_default_session[]) = haskey(session.tensors, s)
function TensorQ(s::AbstractString; session::Session=_default_session[])
    TensorQ(Symbol(s); session)
end
VBundleQ(s::Symbol; session::Session=_default_session[]) = haskey(session.vbundles, s)
function VBundleQ(s::AbstractString; session::Session=_default_session[])
    VBundleQ(Symbol(s); session)
end
MetricQ(s::Symbol; session::Session=_default_session[]) = haskey(session.metrics, s)
function MetricQ(s::AbstractString; session::Session=_default_session[])
    MetricQ(Symbol(s); session)
end
BasisQ(s::Symbol; session::Session=_default_session[]) = haskey(session.bases, s)
BasisQ(s::AbstractString; session::Session=_default_session[]) = BasisQ(Symbol(s); session)
ChartQ(s::Symbol; session::Session=_default_session[]) = haskey(session.charts, s)
ChartQ(s::AbstractString; session::Session=_default_session[]) = ChartQ(Symbol(s); session)
function CovDQ(s::Symbol; session::Session=_default_session[])
    haskey(session.metrics, s) || haskey(session.parallel_deriv_index, s)
end
CovDQ(s::AbstractString; session::Session=_default_session[]) = CovDQ(Symbol(s); session)
function PerturbationQ(s::Symbol; session::Session=_default_session[])
    haskey(session.perturbations, s)
end
function PerturbationQ(s::AbstractString; session::Session=_default_session[])
    PerturbationQ(Symbol(s); session)
end
function FermionicQ(s::Symbol; session::Session=_default_session[])
    t = get(session.tensors, s, nothing)
    !isnothing(t) && t.symmetry.type == :GradedSymmetric
end
function FermionicQ(s::AbstractString; session::Session=_default_session[])
    FermionicQ(Symbol(s); session)
end

function Dimension(s::Symbol; session::Session=_default_session[])
    m = get(session.manifolds, s, nothing)
    isnothing(m) && throw(
        ArgumentError(
            "Dimension: manifold $s not defined. Register it with def_manifold!(:$s, dim, indices).",
        ),
    )
    m.dimension
end
function Dimension(s::AbstractString; session::Session=_default_session[])
    Dimension(Symbol(s); session)
end

function IndicesOfVBundle(s::Symbol; session::Session=_default_session[])
    vb = get(session.vbundles, s, nothing)
    isnothing(vb) && error("IndicesOfVBundle: VBundle $s not defined")
    vb.index_labels
end
function IndicesOfVBundle(s::AbstractString; session::Session=_default_session[])
    IndicesOfVBundle(Symbol(s); session)
end

function SlotsOfTensor(s::Symbol; session::Session=_default_session[])
    t = get(session.tensors, s, nothing)
    isnothing(t) && error("SlotsOfTensor: tensor $s not defined")
    t.slots
end
function SlotsOfTensor(s::AbstractString; session::Session=_default_session[])
    SlotsOfTensor(Symbol(s); session)
end

function VBundleOfBasis(s::Symbol; session::Session=_default_session[])
    b = get(session.bases, s, nothing)
    isnothing(b) && error("VBundleOfBasis: basis $s not defined")
    b.vbundle
end
function VBundleOfBasis(s::AbstractString; session::Session=_default_session[])
    VBundleOfBasis(Symbol(s); session)
end

function BasesOfVBundle(vb::Symbol; session::Session=_default_session[])
    [b.name for b in values(session.bases) if b.vbundle == vb]
end
function BasesOfVBundle(vb::AbstractString; session::Session=_default_session[])
    BasesOfVBundle(Symbol(vb); session)
end

function CNumbersOf(s::Symbol; session::Session=_default_session[])
    b = get(session.bases, s, nothing)
    isnothing(b) && error("CNumbersOf: basis $s not defined")
    copy(b.cnumbers)
end
function CNumbersOf(s::AbstractString; session::Session=_default_session[])
    CNumbersOf(Symbol(s); session)
end

function PDOfBasis(s::Symbol; session::Session=_default_session[])
    b = get(session.bases, s, nothing)
    isnothing(b) && error("PDOfBasis: basis $s not defined")
    b.parallel_deriv
end
function PDOfBasis(s::AbstractString; session::Session=_default_session[])
    PDOfBasis(Symbol(s); session)
end

function ManifoldOfChart(s::Symbol; session::Session=_default_session[])
    c = get(session.charts, s, nothing)
    isnothing(c) && error("ManifoldOfChart: chart $s not defined")
    c.manifold
end
function ManifoldOfChart(s::AbstractString; session::Session=_default_session[])
    ManifoldOfChart(Symbol(s); session)
end

function ScalarsOfChart(s::Symbol; session::Session=_default_session[])
    c = get(session.charts, s, nothing)
    isnothing(c) && error("ScalarsOfChart: chart $s not defined")
    copy(c.scalars)
end
function ScalarsOfChart(s::AbstractString; session::Session=_default_session[])
    ScalarsOfChart(Symbol(s); session)
end

function MemberQ(collection::Symbol, s::Symbol; session::Session=_default_session[])
    if collection == :Manifolds
        s in session.manifold_list
    elseif collection == :Tensors
        s in session.tensor_list
    elseif collection == :VBundles
        s in session.vbundle_list
    elseif collection == :Perturbations
        s in session.perturbation_list
    elseif collection == :Bases
        s in session.basis_list
    elseif collection == :Charts
        s in session.chart_list
    else
        false
    end
end
# Also accept a live collection (e.g. when `Manifolds` resolves to the actual Vector)
MemberQ(collection::AbstractVector, s::Symbol) = s in collection
MemberQ(collection::AbstractVector, s::AbstractString) = Symbol(s) in collection
function MemberQ(collection::Symbol, s::AbstractString; session::Session=_default_session[])
    MemberQ(collection, Symbol(s); session)
end
function MemberQ(collection::AbstractString, s; session::Session=_default_session[])
    MemberQ(Symbol(collection), s; session)
end

"""
    SignDetOfMetric(metric_name) → Int

Return the sign of the determinant (+1 Riemannian, -1 Lorentzian) for a registered metric.
"""
function SignDetOfMetric(metric_name::Symbol; session::Session=_default_session[])::Int
    covd = get(session.metric_name_index, metric_name, nothing)
    if covd !== nothing
        return session.metrics[covd].signdet
    end
    error("SignDetOfMetric: metric $metric_name not found")
end
function SignDetOfMetric(s::AbstractString; session::Session=_default_session[])
    SignDetOfMetric(Symbol(s); session)
end

# ============================================================
# Symmetry string parser
# ============================================================

"""
    _parse_symmetry(sym_str, slot_specs) → SymmetrySpec

Parse a Wolfram symmetry string like "Symmetric[{-bta,-btb}]" into a SymmetrySpec.
`slot_specs` is the tensor's slot list for mapping labels → slot positions.
"""
function _parse_symmetry(
    sym_str::Union{String,Nothing}, slot_specs::Vector{IndexSpec}
)::SymmetrySpec
    (isnothing(sym_str) || isempty(sym_str)) && return SymmetrySpec(:NoSymmetry, Int[])

    # Young[{k1,k2,...}] — applies to all tensor slots in order
    m_young = match(r"^Young\[\{([^}]*)\}\]$", sym_str)
    if !isnothing(m_young)
        partition = [
            parse(Int, strip(s)) for s in split(something(m_young.captures[1]), ",")
        ]
        all_slots = collect(1:length(slot_specs))
        sum(partition) == length(all_slots) || error(
            "Young partition sum $(sum(partition)) ≠ tensor arity $(length(all_slots))"
        )
        return SymmetrySpec(:YoungSymmetry, all_slots, partition)
    end

    m = match(
        r"^(Symmetric|Antisymmetric|GradedSymmetric|RiemannSymmetric)\[\{([^}]*)\}\]$",
        sym_str,
    )
    isnothing(m) && error("Cannot parse symmetry string: $sym_str")

    type_str = something(m.captures[1])
    labels_str = something(m.captures[2])

    sym_type = Symbol(type_str)

    if isempty(strip(labels_str))
        return SymmetrySpec(:NoSymmetry, Int[])
    end

    raw_labels = split(labels_str, ",")
    label_names = String[strip(lstrip(strip(l), '-')) for l in raw_labels]

    # Map label names to 1-based slot positions
    slot_positions = Int[]
    for lbl in label_names
        lbl_sym = Symbol(lbl)
        pos = findfirst(s -> s.label == lbl_sym, slot_specs)
        isnothing(pos) && error("Symmetry label '$lbl' not found in tensor slots")
        push!(slot_positions, pos)
    end

    if sym_type == :RiemannSymmetric && length(slot_positions) != 4
        error("RiemannSymmetric requires exactly 4 slots, got $(length(slot_positions))")
    end

    SymmetrySpec(sym_type, slot_positions)
end
