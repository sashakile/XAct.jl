# ============================================================
# Def functions
# ============================================================

"""
    def_manifold!(name, dim, index_labels) → ManifoldObj

Define a new abstract manifold.
"""
function def_manifold!(
    name::Symbol,
    dim::Int,
    index_labels::Vector{Symbol};
    session::Session=_default_session[],
)::ManifoldObj
    @assert dim >= 1 "def_manifold!: dimension must be ≥ 1, got $dim"
    @assert length(index_labels) >= 2 "def_manifold!: need ≥ 2 index labels, got $(length(index_labels))"
    @assert length(unique(index_labels)) == length(index_labels) "def_manifold!: duplicate index labels"
    validate_identifier(name; context="manifold name")
    session.validate_symbol_hook(name)
    ValidateSymbolInSession(name; session)

    tb_name = Symbol("Tangent" * string(name))

    m = ManifoldObj(name, dim, index_labels)
    tb = VBundleObj(tb_name, name, index_labels)

    session.manifolds[name] = m
    session.vbundles[tb.name] = tb
    push!(session.manifold_list, name)
    push!(session.vbundle_list, tb.name)

    session.register_symbol_hook(name, "XTensor")
    session.register_symbol_hook(tb_name, "XTensor")

    m
end

# Convenience overloads for string input
function def_manifold!(
    name::AbstractString,
    dim::Int,
    index_labels::Vector;
    session::Session=_default_session[],
)::ManifoldObj
    sym_name = Symbol(name)
    sym_labels = [Symbol(string(l)) for l in index_labels]
    def_manifold!(sym_name, dim, sym_labels; session)
end

"""
    def_tensor!(name, index_specs, manifold; symmetry_str=nothing) → TensorObj

Define a new abstract tensor.
index_specs: vector of strings like ["-bta","-btb"] or ["bta"].
"""
function def_tensor!(
    name::Symbol,
    index_specs::Vector{String},
    manifold::Symbol;
    symmetry_str::Union{String,Nothing}=nothing,
    _skip_validation::Bool=false,
    session::Session=_default_session[],
)::TensorObj
    if !_skip_validation
        validate_identifier(name; context="tensor name")
        session.validate_symbol_hook(name)
        ValidateSymbolInSession(name; session)
    end

    m = get(session.manifolds, manifold, nothing)
    isnothing(m) && error("def_tensor!: manifold $manifold not defined")

    # Parse index specs into IndexSpec
    slots = IndexSpec[]
    for spec in index_specs
        if startswith(spec, "-")
            push!(slots, IndexSpec(Symbol(spec[2:end]), true))
        else
            push!(slots, IndexSpec(Symbol(spec), false))
        end
    end

    # Validate labels belong to manifold's index set
    allowed = Set(m.index_labels)
    for s in slots
        s.label in allowed ||
            error("Index label $(s.label) not in manifold $manifold indices")
    end

    sym = _parse_symmetry(symmetry_str, slots)
    t = TensorObj(name, slots, manifold, sym)
    session.tensors[name] = t
    push!(session.tensor_list, name)

    session.register_symbol_hook(name, "XTensor")

    # Auto-register first Bianchi identity for RiemannSymmetric tensors
    if sym.type == :RiemannSymmetric && length(slots) == 4
        RegisterIdentity!(name, _make_bianchi_identity(name); session)
    end

    t
end

function def_tensor!(
    name::AbstractString,
    index_specs::Vector,
    manifold::AbstractString;
    symmetry_str::Union{String,Nothing}=nothing,
    session::Session=_default_session[],
)::TensorObj
    sym_name = Symbol(name)
    sym_manifold = Symbol(manifold)
    str_specs = [string(s) for s in index_specs]
    def_tensor!(sym_name, str_specs, sym_manifold; symmetry_str=symmetry_str, session)
end

"""
    def_tensor!(name, index_specs, manifolds::Vector{Symbol}; symmetry_str=nothing) → TensorObj

Multi-index-set variant: each index label must belong to one of the given manifolds.
The first manifold in the list is used as the primary manifold stored in TensorObj.manifold.
This enables tensors that mix indices from e.g. spacetime and internal gauge manifolds.
"""
function def_tensor!(
    name::Symbol,
    index_specs::Vector{String},
    manifolds::Vector{Symbol};
    symmetry_str::Union{String,Nothing}=nothing,
    _skip_validation::Bool=false,
    session::Session=_default_session[],
)::TensorObj
    isempty(manifolds) && error("def_tensor!: manifolds list is empty")

    if !_skip_validation
        session.validate_symbol_hook(name)
        ValidateSymbolInSession(name; session)
    end

    # Validate all listed manifolds exist and build union of allowed labels
    allowed = Set{Symbol}()
    for mname in manifolds
        m = get(session.manifolds, mname, nothing)
        isnothing(m) && error("def_tensor!: manifold $mname not defined")
        union!(allowed, m.index_labels)
    end

    # Parse index specs into IndexSpec
    slots = IndexSpec[]
    for spec in index_specs
        if startswith(spec, "-")
            push!(slots, IndexSpec(Symbol(spec[2:end]), true))
        else
            push!(slots, IndexSpec(Symbol(spec), false))
        end
    end

    # Validate each label belongs to one of the manifolds
    for s in slots
        s.label in allowed ||
            error("Index label $(s.label) not found in any of manifolds $manifolds")
    end

    # Primary manifold = first in list (used by CommuteCovDs for fresh index selection)
    primary_manifold = manifolds[1]
    sym = _parse_symmetry(symmetry_str, slots)
    t = TensorObj(name, slots, primary_manifold, sym)
    session.tensors[name] = t
    push!(session.tensor_list, name)

    session.register_symbol_hook(name, "XTensor")

    # Auto-register first Bianchi identity for RiemannSymmetric tensors
    if sym.type == :RiemannSymmetric && length(slots) == 4
        RegisterIdentity!(name, _make_bianchi_identity(name); session)
    end

    t
end

# Convenience overload: Vector of manifold name strings
function def_tensor!(
    name::AbstractString,
    index_specs::Vector,
    manifolds::Vector;
    symmetry_str::Union{String,Nothing}=nothing,
    session::Session=_default_session[],
)::TensorObj
    sym_name = Symbol(name)
    sym_manifolds = Symbol[Symbol(string(m)) for m in manifolds]
    str_specs = [string(s) for s in index_specs]
    def_tensor!(sym_name, str_specs, sym_manifolds; symmetry_str=symmetry_str, session)
end

"""
    def_metric!(signdet, metric_expr, covd_name) → MetricObj

Define a metric tensor and auto-create curvature tensors.
metric_expr: e.g. "Cng[-cna,-cnb]"
covd_name: e.g. "Cnd" (used as suffix for auto-created curvature tensors)
"""
function def_metric!(
    signdet::Int,
    metric_expr::AbstractString,
    covd_name::Symbol;
    session::Session=_default_session[],
)::MetricObj
    @assert signdet in (-1, 0, 1) "def_metric!: signdet must be -1, 0, or 1, got $signdet"
    # Validate covd name against xAct registry and session
    validate_identifier(covd_name; context="covariant derivative name")
    session.validate_symbol_hook(covd_name)
    ValidateSymbolInSession(covd_name; session)

    # Parse metric_expr: extract name and slots
    m = match(r"^(\w+)\[([^\]]*)\]$", metric_expr)
    isnothing(m) && error("Cannot parse metric expression: $metric_expr")

    metric_name = Symbol(m.captures[1])
    slot_strs = String[strip(s) for s in split(m.captures[2], ",")]

    # Determine manifold: find which manifold has these index labels
    manifold_sym = _find_manifold_for_indices(slot_strs; session)
    isnothing(manifold_sym) &&
        error("Cannot determine manifold for metric indices: $slot_strs")

    # Register the metric tensor (symmetric rank-2 covariant)
    # (metric tensor name validated inside def_tensor!)
    sym_str = "Symmetric[{$(join(slot_strs, ","))}]"
    def_tensor!(metric_name, slot_strs, manifold_sym; symmetry_str=sym_str, session)

    metric = MetricObj(metric_name, manifold_sym, covd_name, signdet)
    session.metrics[covd_name] = metric
    session.metric_name_index[metric_name] = covd_name

    session.register_symbol_hook(covd_name, "XTensor")

    # Auto-create curvature tensors
    _auto_create_curvature!(manifold_sym, covd_name; session)

    metric
end

function def_metric!(
    signdet::Int,
    metric_expr::AbstractString,
    covd_name::AbstractString;
    session::Session=_default_session[],
)::MetricObj
    def_metric!(signdet, metric_expr, Symbol(covd_name); session)
end

# ============================================================
# Basis and Chart definitions
# ============================================================

"""
    def_basis!(name, vbundle, cnumbers) → BasisObj

Define a basis of vector fields on a vector bundle.
`cnumbers` are integer labels for the basis elements (length must equal dim of vbundle).
Auto-creates a parallel derivative symbol `PD<name>`.
"""
function def_basis!(
    name::Symbol,
    vbundle::Symbol,
    cnumbers::Vector{Int};
    _skip_validation::Bool=false,
    session::Session=_default_session[],
)::BasisObj
    if !_skip_validation
        session.validate_symbol_hook(name)
        ValidateSymbolInSession(name; session)
    end

    # Validate vbundle exists
    vb = get(session.vbundles, vbundle, nothing)
    isnothing(vb) && throw(ArgumentError("def_basis!: vector bundle $vbundle not defined"))

    # Validate cnumbers length matches dimension
    manifold = session.manifolds[vb.manifold]
    dim = manifold.dimension
    length(cnumbers) == dim || throw(
        ArgumentError(
            "def_basis!: cnumbers length $(length(cnumbers)) != dimension $dim of $vbundle",
        ),
    )

    # Validate cnumbers are distinct integers
    length(unique(cnumbers)) == length(cnumbers) ||
        throw(ArgumentError("def_basis!: cnumbers must be distinct"))

    # Auto-create parallel derivative name
    pd_name = Symbol("PD" * string(name))

    b = BasisObj(name, vbundle, sort(cnumbers), pd_name, false)
    session.bases[name] = b
    session.parallel_deriv_index[pd_name] = name
    push!(session.basis_list, name)

    session.register_symbol_hook(name, "XTensor")
    session.register_symbol_hook(pd_name, "XTensor")

    b
end

function def_basis!(
    name::AbstractString,
    vbundle::AbstractString,
    cnumbers::Vector{Int};
    session::Session=_default_session[],
)::BasisObj
    def_basis!(Symbol(name), Symbol(vbundle), cnumbers; session)
end

function def_basis!(
    name::AbstractString,
    vbundle::AbstractString,
    cnumbers::Vector;
    session::Session=_default_session[],
)::BasisObj
    def_basis!(Symbol(name), Symbol(vbundle), Int[Int(c) for c in cnumbers]; session)
end

"""
    def_chart!(name, manifold, cnumbers, scalars) → ChartObj

Define a coordinate chart on a manifold. Internally creates a BasisObj (coordinate basis)
and registers the coordinate scalar fields as tensors.
`scalars` are the coordinate field names, e.g. [:t, :r, :theta, :phi].
"""
function def_chart!(
    name::Symbol,
    manifold::Symbol,
    cnumbers::Vector{Int},
    scalars::Vector{Symbol};
    session::Session=_default_session[],
)::ChartObj
    session.validate_symbol_hook(name)
    ValidateSymbolInSession(name; session)

    # Validate manifold exists
    m = get(session.manifolds, manifold, nothing)
    isnothing(m) && throw(ArgumentError("def_chart!: manifold $manifold not defined"))

    dim = m.dimension
    length(cnumbers) == dim || throw(
        ArgumentError("def_chart!: cnumbers length $(length(cnumbers)) != dimension $dim"),
    )
    length(scalars) == dim || throw(
        ArgumentError("def_chart!: scalars length $(length(scalars)) != dimension $dim")
    )
    length(unique(cnumbers)) == length(cnumbers) ||
        throw(ArgumentError("def_chart!: cnumbers must be distinct"))

    # Create the coordinate basis on the tangent bundle
    tb_name = Symbol("Tangent" * string(manifold))
    def_basis!(name, tb_name, cnumbers; _skip_validation=true, session)
    # Mark it as a chart basis
    session.bases[name] = BasisObj(
        name, tb_name, sort(cnumbers), session.bases[name].parallel_deriv, true
    )

    # Register coordinate scalars as rank-0 tensors on this manifold
    for sc in scalars
        if !TensorQ(sc; session)
            t = TensorObj(sc, IndexSpec[], manifold, SymmetrySpec(:NoSymmetry, Int[]))
            session.tensors[sc] = t
            push!(session.tensor_list, sc)
            session.register_symbol_hook(sc, "XTensor")
        end
    end

    chart = ChartObj(name, manifold, sort(cnumbers), scalars)
    session.charts[name] = chart
    push!(session.chart_list, name)

    session.register_symbol_hook(name, "XTensor")

    chart
end

function def_chart!(
    name::AbstractString,
    manifold::AbstractString,
    cnumbers::Vector,
    scalars::Vector;
    session::Session=_default_session[],
)::ChartObj
    def_chart!(
        Symbol(name),
        Symbol(manifold),
        Int[Int(c) for c in cnumbers],
        Symbol[Symbol(s) for s in scalars];
        session,
    )
end

"""
Find which manifold has all of the given index labels (stripping '-').
"""
function _find_manifold_for_indices(
    slot_strs; session::Session=_default_session[]
)::Union{Symbol,Nothing}
    # Strip '-' from each label
    bare = Set([Symbol(startswith(s, "-") ? s[2:end] : string(s)) for s in slot_strs])
    for (name, m) in session.manifolds
        if bare ⊆ Set(m.index_labels)
            return name
        end
    end
    nothing
end

"""
Auto-create Riemann, Ricci, RicciScalar, Einstein tensors for a metric.
"""
function _auto_create_curvature!(
    manifold::Symbol, covd::Symbol; session::Session=_default_session[]
)
    m = session.manifolds[manifold]
    idxs = m.index_labels
    n = length(idxs)
    covd_str = string(covd)

    # Ricci scalar: always created (scalar, no indices)
    ricci_scalar_name = Symbol("RicciScalar" * covd_str)
    if !haskey(session.tensors, ricci_scalar_name)
        t = TensorObj(
            ricci_scalar_name, IndexSpec[], manifold, SymmetrySpec(:NoSymmetry, Int[])
        )
        session.tensors[ricci_scalar_name] = t
        push!(session.tensor_list, ricci_scalar_name)
        session.register_symbol_hook(ricci_scalar_name, "XTensor")
    end

    # Need at least 2 indices for Ricci and Einstein
    n >= 2 || return nothing

    i1, i2 = "-" * string(idxs[1]), "-" * string(idxs[2])

    ricci_name = Symbol("Ricci" * covd_str)
    if !haskey(session.tensors, ricci_name)
        slots2 = String[i1, i2]
        sym2 = "Symmetric[{$i1,$i2}]"
        def_tensor!(ricci_name, slots2, manifold; symmetry_str=sym2, session)
    end

    einstein_name = Symbol("Einstein" * covd_str)
    if !haskey(session.tensors, einstein_name)
        slots2 = String[i1, i2]
        sym2 = "Symmetric[{$i1,$i2}]"
        def_tensor!(einstein_name, slots2, manifold; symmetry_str=sym2, session)
    end

    # Christoffel (second kind): Γ^a_{bc}, symmetric in last two covariant slots
    # For manifolds with ≥ 3 labels, use distinct labels; for 2-label manifolds,
    # reuse label 1 for the contravariant slot (a ≠ b,c is fine since variance differs)
    if n >= 2
        c_i1 = string(idxs[1])                   # contravariant slot
        c_i2 = i2                                  # first covariant slot
        c_i3 = n >= 3 ? "-" * string(idxs[3]) : "-" * string(idxs[1])
        christoffel_name = Symbol("Christoffel" * covd_str)
        if !haskey(session.tensors, christoffel_name)
            slots3 = String[c_i1, c_i2, c_i3]
            sym3 = "Symmetric[{$c_i2,$c_i3}]"
            def_tensor!(christoffel_name, slots3, manifold; symmetry_str=sym3, session)
        end
    end

    # Need at least 4 indices for Riemann
    n >= 4 || return nothing

    i3, i4 = "-" * string(idxs[3]), "-" * string(idxs[4])

    riemann_name = Symbol("Riemann" * covd_str)
    if !haskey(session.tensors, riemann_name)
        slots4 = String[i1, i2, i3, i4]
        sym4 = "RiemannSymmetric[{$i1,$i2,$i3,$i4}]"
        def_tensor!(riemann_name, slots4, manifold; symmetry_str=sym4, session)
    end

    # Register CovD commutation as a multi-term identity (Ricci identity).
    RegisterIdentity!(
        covd,
        MultiTermIdentity(
            :RicciIdentity,   # name
            covd,             # tensor (keyed under the CovD symbol)
            0,                # n_slots (not a single-tensor identity)
            Int[],            # fixed_slots
            Int[],            # cycled_slots
            Vector{Int}[],    # slot_perms
            Rational{Int}[],  # coefficients
            0,                # eliminate
        );
        session,
    )

    # Also register Weyl tensor (curvature_invariants.toml uses WeylCID)
    weyl_name = Symbol("Weyl" * covd_str)
    if !haskey(session.tensors, weyl_name)
        slots4 = String[i1, i2, i3, i4]
        sym4 = "RiemannSymmetric[{$i1,$i2,$i3,$i4}]"
        def_tensor!(weyl_name, slots4, manifold; symmetry_str=sym4, session)
    end
    # Mark Weyl as traceless (any trace over any pair of its indices = 0)
    push!(session.traceless_tensors, weyl_name)

    # Register Einstein tensor trace rule: tr(G_{ab}) = g^{ab} G_{ab} = -R
    # In n dimensions: g^{ab} G_{ab} = R - (n/2)*R = (1 - n/2)*R
    # The coefficient is (1 - dim/2).  For dim=4: coeff = -1.
    n = m.dimension
    coeff_int = 1 - n // 2  # Rational — correct for all dimensions
    if !haskey(session.trace_scalars, einstein_name)
        session.trace_scalars[einstein_name] = (ricci_scalar_name, coeff_int)
    end

    # Register Einstein expansion rule: G_{ab} = R_{ab} - (1/2) g_{ab} R
    metric_obj = get(session.metrics, covd, nothing)
    if !isnothing(metric_obj) && !haskey(session.einstein_expansion, einstein_name)
        session.einstein_expansion[einstein_name] = (
            ricci_name, metric_obj.name, ricci_scalar_name
        )
    end
end
