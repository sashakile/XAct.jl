# ============================================================
# xCoba: Coordinate transformations (basis changes)
# ============================================================

"""
    set_basis_change!(from_basis, to_basis, matrix) → BasisChangeObj

Register a coordinate transformation between two bases.
The matrix transforms components from `from_basis` to `to_basis`.
Both the forward (from→to) and inverse (to→from) directions are stored.

Validates:

  - Both bases exist (via BasisQ)
  - Both bases belong to the same vector bundle
  - Matrix is square with size matching the basis dimension
  - Matrix is invertible (non-singular)
"""
function set_basis_change!(
    from_basis::Symbol,
    to_basis::Symbol,
    matrix::AbstractMatrix;
    session::Session=_default_session[],
)::BasisChangeObj
    BasisQ(from_basis; session) || error("set_basis_change!: basis $from_basis not defined")
    BasisQ(to_basis; session) || error("set_basis_change!: basis $to_basis not defined")

    vb_from = VBundleOfBasis(from_basis; session)
    vb_to = VBundleOfBasis(to_basis; session)
    vb_from == vb_to || error(
        "set_basis_change!: bases $from_basis ($vb_from) and $to_basis ($vb_to) belong to different vector bundles",
    )

    dim = length(CNumbersOf(from_basis; session))
    n, m = size(matrix)
    (n == m == dim) ||
        error("set_basis_change!: matrix size ($n×$m) does not match basis dimension $dim")

    # Convert to Float64 for numeric operations (det, inv)
    fmat = Matrix{Float64}(matrix)
    jac = det(fmat)
    abs(jac) < 1e-15 && error("set_basis_change!: matrix is singular (det ≈ 0)")
    inv_mat = inv(fmat)

    bc = BasisChangeObj(from_basis, to_basis, fmat, inv_mat, jac)
    session.basis_changes[(from_basis, to_basis)] = bc

    # Store inverse direction
    bc_inv = BasisChangeObj(to_basis, from_basis, inv_mat, fmat, 1.0 / jac)
    session.basis_changes[(to_basis, from_basis)] = bc_inv

    bc
end

function set_basis_change!(
    from_basis::AbstractString,
    to_basis::AbstractString,
    matrix::AbstractMatrix;
    session::Session=_default_session[],
)::BasisChangeObj
    set_basis_change!(Symbol(from_basis), Symbol(to_basis), matrix; session)
end

"""
    BasisChangeQ(from, to) → Bool

Check if a basis change from `from` to `to` is registered.
"""
function BasisChangeQ(from::Symbol, to::Symbol; session::Session=_default_session[])
    haskey(session.basis_changes, (from, to))
end
function BasisChangeQ(
    from::AbstractString, to::AbstractString; session::Session=_default_session[]
)
    BasisChangeQ(Symbol(from), Symbol(to); session)
end

"""
    BasisChangeMatrix(from, to) → Matrix

Return the transformation matrix from `from` basis to `to` basis.
"""
function BasisChangeMatrix(
    from::Symbol, to::Symbol; session::Session=_default_session[]
)::Matrix{Any}
    haskey(session.basis_changes, (from, to)) ||
        error("BasisChangeMatrix: no basis change registered from $from to $to")
    session.basis_changes[(from, to)].matrix
end
function BasisChangeMatrix(
    from::AbstractString, to::AbstractString; session::Session=_default_session[]
)
    BasisChangeMatrix(Symbol(from), Symbol(to); session)
end

"""
    InverseBasisChangeMatrix(from, to) → Matrix

Return the inverse transformation matrix (i.e. the matrix that goes from `to` back to `from`).
"""
function InverseBasisChangeMatrix(
    from::Symbol, to::Symbol; session::Session=_default_session[]
)::Matrix{Any}
    haskey(session.basis_changes, (from, to)) ||
        error("InverseBasisChangeMatrix: no basis change registered from $from to $to")
    session.basis_changes[(from, to)].inverse
end
function InverseBasisChangeMatrix(
    from::AbstractString, to::AbstractString; session::Session=_default_session[]
)
    InverseBasisChangeMatrix(Symbol(from), Symbol(to); session)
end

"""
    Jacobian(basis1, basis2) → Any

Return the Jacobian determinant of the transformation from `basis1` to `basis2`.
"""
function Jacobian(basis1::Symbol, basis2::Symbol; session::Session=_default_session[])
    haskey(session.basis_changes, (basis1, basis2)) ||
        error("Jacobian: no basis change registered from $basis1 to $basis2")
    session.basis_changes[(basis1, basis2)].jacobian
end
function Jacobian(
    basis1::AbstractString, basis2::AbstractString; session::Session=_default_session[]
)
    Jacobian(Symbol(basis1), Symbol(basis2); session)
end

"""
    change_basis(array, bases, slot, from_basis, to_basis) → Array

Apply a basis change to a specific slot of a component array.

  - `array`      — the component array (Vector for rank-1, Matrix for rank-2, etc.)
  - `bases`      — vector of basis symbols for each slot (unused, reserved for future)
  - `slot`       — 1-indexed slot to transform
  - `from_basis` — current basis of that slot
  - `to_basis`   — target basis

For rank-1 (vector): result = M * v
For rank-2 (matrix): transforms the specified slot using the transformation matrix.
"""
function change_basis(
    array::AbstractArray,
    bases::Vector{Symbol},
    slot::Int,
    from_basis::Symbol,
    to_basis::Symbol;
    session::Session=_default_session[],
)::AbstractArray
    haskey(session.basis_changes, (from_basis, to_basis)) ||
        error("change_basis: no basis change registered from $from_basis to $to_basis")
    M = Float64.(session.basis_changes[(from_basis, to_basis)].matrix)
    ndims(array) == 0 && return array

    # Contract M along the `slot`-th dimension of the array
    # TensorContraction: result_{...i'...} = M_{i',i} * array_{...i...}
    # with i in position `slot`
    _contract_slot(M, array, slot)
end

function change_basis(
    array::AbstractArray,
    bases::Vector,
    slot::Int,
    from_basis::AbstractString,
    to_basis::AbstractString,
)::AbstractArray
    change_basis(
        array, Symbol[Symbol(b) for b in bases], slot, Symbol(from_basis), Symbol(to_basis)
    )
end

"""
Contract matrix M into array along the given slot dimension.
"""
function _contract_slot(M::AbstractMatrix, A::AbstractVector, slot::Int)
    slot == 1 || error("change_basis: slot $slot out of range for rank-1 array")
    M * A
end

function _contract_slot(M::AbstractMatrix, A::AbstractMatrix, slot::Int)
    if slot == 1
        # Transform first index: result[i',j] = sum_i M[i',i] * A[i,j]
        M * A
    elseif slot == 2
        # Transform second index: result[i,j'] = sum_j A[i,j] * M'[j,j']
        # = (M * A')'
        (M * A')'
    else
        error("change_basis: slot $slot out of range for rank-2 array")
    end
end

function _contract_slot(M::AbstractMatrix, A::AbstractArray, slot::Int)
    nd = ndims(A)
    (1 <= slot <= nd) || error("change_basis: slot $slot out of range for rank-$nd array")
    # General case: permute slot dimension to front, reshape, multiply, reshape back, permute back
    perm = vcat(slot, setdiff(1:nd, slot))
    iperm = invperm(perm)
    sz = size(A)
    Ap = permutedims(A, perm)
    n = sz[slot]
    Ar = reshape(Ap, n, :)
    Br = M * Ar
    Bp = reshape(Br, size(Ap))
    permutedims(Bp, iperm)
end

# ============================================================
# xCoba: Component tensors (CTensor)
# ============================================================

"""
    set_components!(tensor, array, bases; weight=0) → CTensorObj

Store component values for a tensor in the given bases.

Validates:

  - Tensor exists (via TensorQ or MetricQ)
  - Each basis exists (via BasisQ)
  - Array rank matches number of bases
  - Each array dimension matches the basis dimension (length of CNumbersOf)
"""
function set_components!(
    tensor::Symbol,
    array::AbstractArray,
    bases::Vector{Symbol};
    weight::Int=0,
    session::Session=_default_session[],
)::CTensorObj
    # Validate tensor exists
    TensorQ(tensor; session) || error("set_components!: tensor $tensor not defined")

    # Validate each basis exists
    for b in bases
        BasisQ(b; session) || error("set_components!: basis $b not defined")
    end

    # Validate array rank matches number of bases
    # Special case: rank-0 (scalar) tensor with 0 bases and a 0-dim array
    if isempty(bases)
        ndims(array) == 0 || error(
            "set_components!: expected rank-0 array for 0 bases, got rank-$(ndims(array))",
        )
    else
        ndims(array) == length(bases) || error(
            "set_components!: array rank $(ndims(array)) does not match number of bases $(length(bases))",
        )
    end

    # Validate each array dimension matches the basis dimension
    for (i, b) in enumerate(bases)
        dim = length(CNumbersOf(b; session))
        if size(array, i) != dim
            error(
                "set_components!: array dimension $i is $(size(array, i)), expected $dim (basis $b)",
            )
        end
    end

    key = (tensor, bases...)
    ct = CTensorObj(tensor, _to_numeric_array(array), collect(bases), weight)
    session.ctensors[key] = ct
    ct
end

function set_components!(
    tensor::AbstractString,
    array::AbstractArray,
    bases::Vector;
    weight::Int=0,
    session::Session=_default_session[],
)::CTensorObj
    set_components!(
        Symbol(tensor), array, Symbol[Symbol(b) for b in bases]; weight=weight, session
    )
end

"""
    get_components(tensor, bases) → CTensorObj

Retrieve stored component values for a tensor in the given bases.
If not directly stored, attempts to transform from a stored basis configuration
using registered basis changes.
"""
function get_components(
    tensor::Symbol, bases::Vector{Symbol}; session::Session=_default_session[]
)::CTensorObj
    key = (tensor, bases...)
    haskey(session.ctensors, key) && return session.ctensors[key]

    # Try to find stored components in a different basis configuration and transform
    for (stored_key, ct) in session.ctensors
        stored_key[1] == tensor || continue
        stored_bases = Symbol[stored_key[i] for i in 2:length(stored_key)]
        length(stored_bases) == length(bases) || continue

        # Check if we can transform each slot
        can_transform = true
        for (i, (from_b, to_b)) in enumerate(zip(stored_bases, bases))
            if from_b != to_b && !BasisChangeQ(from_b, to_b; session)
                can_transform = false
                break
            end
        end
        can_transform || continue

        # Transform slot by slot
        result_array = ct.array
        current_bases = copy(stored_bases)
        for (i, (from_b, to_b)) in enumerate(zip(stored_bases, bases))
            if from_b != to_b
                result_array = change_basis(
                    result_array, current_bases, i, from_b, to_b; session
                )
                current_bases[i] = to_b
            end
        end
        return CTensorObj(tensor, Array(result_array), collect(bases), ct.weight)
    end

    error(
        "get_components: no components stored for $tensor in bases $(bases), and no transform path available",
    )
end

function get_components(
    tensor::AbstractString, bases::Vector; session::Session=_default_session[]
)::CTensorObj
    get_components(Symbol(tensor), Symbol[Symbol(b) for b in bases]; session)
end

"""
    ComponentArray(tensor, bases) → Array

Return just the array of component values for a tensor in the given bases.
"""
function ComponentArray(
    tensor::Symbol, bases::Vector{Symbol}; session::Session=_default_session[]
)::Array
    get_components(tensor, bases; session).array
end

function ComponentArray(
    tensor::AbstractString, bases::Vector; session::Session=_default_session[]
)::Array
    ComponentArray(Symbol(tensor), Symbol[Symbol(b) for b in bases]; session)
end

"""
    CTensorQ(tensor, bases...) → Bool

Return true if component values are stored for the given tensor and bases.
"""
function CTensorQ(
    tensor::Symbol, bases::Symbol...; session::Session=_default_session[]
)::Bool
    haskey(session.ctensors, (tensor, bases...))
end

function CTensorQ(
    tensor::AbstractString, bases::AbstractString...; session::Session=_default_session[]
)::Bool
    CTensorQ(Symbol(tensor), (Symbol(b) for b in bases)...; session)
end

"""
    component_value(tensor, indices, bases) → Any

Return a single component value from a stored CTensor.
`indices` are 1-based integer indices into the array.
"""
function component_value(
    tensor::Symbol,
    indices::Vector{Int},
    bases::Vector{Symbol};
    session::Session=_default_session[],
)::Any
    ct = get_components(tensor, bases; session)
    arr = ct.array
    for (i, idx) in enumerate(indices)
        if idx < 1 || idx > size(arr, i)
            error(
                "component_value: index $idx out of range [1, $(size(arr, i))] for dimension $i",
            )
        end
    end
    arr[indices...]
end

function component_value(
    tensor::AbstractString,
    indices::Vector,
    bases::Vector;
    session::Session=_default_session[],
)::Any
    component_value(
        Symbol(tensor),
        Int[Int(i) for i in indices],
        Symbol[Symbol(b) for b in bases];
        session,
    )
end

"""
    ctensor_contract(tensor, bases, slot1, slot2) → CTensorObj

Contract (trace) two indices of a CTensor.
Both slots must be in the same basis. The result has rank reduced by 2.
For rank-2, this is the matrix trace.
"""
function ctensor_contract(
    tensor::Symbol,
    bases::Vector{Symbol},
    slot1::Int,
    slot2::Int;
    session::Session=_default_session[],
)::CTensorObj
    ct = get_components(tensor, bases; session)
    arr = ct.array
    nd = ndims(arr)
    (1 <= slot1 <= nd) || error("ctensor_contract: slot1=$slot1 out of range [1, $nd]")
    (1 <= slot2 <= nd) || error("ctensor_contract: slot2=$slot2 out of range [1, $nd]")
    slot1 != slot2 || error("ctensor_contract: slot1 and slot2 must be different")
    bases[slot1] == bases[slot2] || error(
        "ctensor_contract: slots $slot1 and $slot2 have different bases ($(bases[slot1]) vs $(bases[slot2]))",
    )

    s1, s2 = minmax(slot1, slot2)  # s1 < s2

    if nd == 2
        # Simple matrix trace
        result_val = sum(arr[i, i] for i in 1:size(arr, 1))
        result_array = fill(result_val)  # 0-dim array
        remaining_bases = Symbol[]
    else
        # General contraction: sum over matching indices
        remaining_dims = [i for i in 1:nd if i != s1 && i != s2]
        remaining_sizes = [size(arr, d) for d in remaining_dims]
        remaining_bases = [bases[d] for d in remaining_dims]
        trace_dim = size(arr, s1)  # == size(arr, s2)

        T = eltype(arr) === Any ? Float64 : eltype(arr)
        result_array = zeros(T, remaining_sizes...)
        for idx in CartesianIndices(Tuple(remaining_sizes))
            val = zero(T)
            for k in 1:trace_dim
                # Build full index tuple
                full_idx = Vector{Int}(undef, nd)
                rem_pos = 1
                for d in 1:nd
                    if d == s1
                        full_idx[d] = k
                    elseif d == s2
                        full_idx[d] = k
                    else
                        full_idx[d] = idx[rem_pos]
                        rem_pos += 1
                    end
                end
                val += arr[full_idx...]
            end
            result_array[idx] = val
        end
    end

    CTensorObj(tensor, result_array, remaining_bases, ct.weight)
end

function ctensor_contract(
    tensor::AbstractString,
    bases::Vector,
    slot1::Int,
    slot2::Int;
    session::Session=_default_session[],
)::CTensorObj
    ctensor_contract(
        Symbol(tensor), Symbol[Symbol(b) for b in bases], slot1, slot2; session
    )
end

# ============================================================
# xCoba: Christoffel symbols from metric components
# ============================================================

"""
    christoffel!(metric, basis; metric_derivs=nothing) → CTensorObj

Compute and store Christoffel symbols (second kind) from metric CTensor components.

The Christoffel symbol is:

    Γ^a_{bc} = (1/2) g^{ad} (∂_b g_{dc} + ∂_c g_{bd} - ∂_d g_{bc})

Arguments:

  - `metric`: the metric tensor symbol (must have stored components in `basis`)
  - `basis`: the coordinate basis (chart) in which to compute
  - `metric_derivs`: optional rank-3 array where `dg[c,a,b] = ∂_c g_{ab}`.
    If omitted, assumes constant metric (all derivatives zero → all Christoffels zero).

Returns the CTensorObj stored under the auto-created Christoffel tensor name.
"""
function christoffel!(
    metric::Symbol,
    basis::Symbol;
    metric_derivs::Union{Nothing,AbstractArray}=nothing,
    session::Session=_default_session[],
)::CTensorObj
    # Find the covariant derivative associated with this metric
    covd = nothing
    for (cd, mobj) in session.metrics
        if mobj.name == metric
            covd = cd
            break
        end
    end
    isnothing(covd) && error("christoffel!: no metric named $metric found")

    christoffel_name = Symbol("Christoffel" * string(covd))
    TensorQ(christoffel_name; session) ||
        error("christoffel!: Christoffel tensor $christoffel_name not registered")

    # Get metric components g_{ab}
    g_ct = get_components(metric, [basis, basis]; session)
    g_arr = g_ct.array
    dim = size(g_arr, 1)

    # Compute inverse metric g^{ab}
    g_inv = inv(convert(Matrix{Float64}, g_arr))

    # Metric derivatives: dg[c, a, b] = ∂_c g_{ab}
    if metric_derivs === nothing
        dg = zeros(Float64, dim, dim, dim)
    else
        dg = metric_derivs
        size(dg) == (dim, dim, dim) ||
            error("christoffel!: metric_derivs must be ($dim,$dim,$dim), got $(size(dg))")
    end

    # Γ^a_{bc} = (1/2) Σ_d g^{ad} (∂_b g_{dc} + ∂_c g_{bd} - ∂_d g_{bc})
    gamma = zeros(Float64, dim, dim, dim)
    for a in 1:dim, b in 1:dim, c in 1:dim
        val = 0.0
        for d in 1:dim
            val += g_inv[a, d] * (dg[b, d, c] + dg[c, b, d] - dg[d, b, c])
        end
        gamma[a, b, c] = 0.5 * val
    end

    set_components!(christoffel_name, gamma, [basis, basis, basis]; session)
end

function christoffel!(
    metric::AbstractString,
    basis::AbstractString;
    metric_derivs=nothing,
    session::Session=_default_session[],
)::CTensorObj
    christoffel!(Symbol(metric), Symbol(basis); metric_derivs=metric_derivs, session)
end

# ============================================================
# xCoba: ToBasis / FromBasis / TraceBasisDummy
# ============================================================

"""
    _index_label(idx_str) → Symbol

Extract the bare label from an index string (strip leading '-').
"""
function _index_label(idx_str::AbstractString)::Symbol
    s = strip(idx_str)
    startswith(s, "-") ? Symbol(s[2:end]) : Symbol(s)
end

"""
    _contract_array_axes(arr, ax1, ax2) → Array

Contract (trace over) two axes of an N-dimensional array.
"""
function _contract_array_axes(arr::AbstractArray, ax1::Int, ax2::Int)
    nd = ndims(arr)
    s1, s2 = minmax(ax1, ax2)
    dim = size(arr, s1)

    remaining_dims = [i for i in 1:nd if i != s1 && i != s2]

    if isempty(remaining_dims)
        # Scalar result
        total = zero(Float64)
        for k in 1:dim
            total += Float64(arr[ntuple(d -> k, nd)...])
        end
        return fill(total)
    end

    remaining_sizes = [size(arr, d) for d in remaining_dims]
    result = zeros(Float64, remaining_sizes...)

    for idx in CartesianIndices(Tuple(remaining_sizes))
        val = 0.0
        for k in 1:dim
            full_idx = Vector{Int}(undef, nd)
            rem_pos = 1
            for d in 1:nd
                if d == s1 || d == s2
                    full_idx[d] = k
                else
                    full_idx[d] = idx[rem_pos]
                    rem_pos += 1
                end
            end
            val += Float64(arr[full_idx...])
        end
        result[idx] = val
    end
    result
end

"""
    _tobasis_term(term, basis, dim) → (Array, Vector{Symbol})

Evaluate a single parsed term to component form.
Returns (array, free_index_labels).
Uses einsum-style evaluation: for each assignment of free index values,
sums over all dummy index values the product of factor components.
"""
function _tobasis_term(term::TermAST, basis::Symbol, dim::Int)
    factors = term.factors

    if isempty(factors)
        # Pure scalar coefficient
        return (fill(Float64(term.coeff)), Symbol[])
    end

    # Parse index labels per factor and count label occurrences
    factor_labels = Vector{Vector{Symbol}}()
    label_count = Dict{Symbol,Int}()
    for f in factors
        labels = Symbol[]
        for idx_str in f.indices
            lbl = _index_label(idx_str)
            push!(labels, lbl)
            label_count[lbl] = get(label_count, lbl, 0) + 1
        end
        push!(factor_labels, labels)
    end

    # Classify labels as free (appears once) or dummy (appears twice)
    dummy_labels = Symbol[]
    free_labels = Symbol[]
    seen = Set{Symbol}()
    for labels in factor_labels
        for lbl in labels
            if lbl ∉ seen
                if label_count[lbl] == 1
                    push!(free_labels, lbl)
                elseif label_count[lbl] == 2
                    push!(dummy_labels, lbl)
                else
                    error("ToBasis: index $lbl appears $(label_count[lbl]) times")
                end
                push!(seen, lbl)
            end
        end
    end

    # Get component arrays for each factor
    factor_arrays = AbstractArray[]
    for f in factors
        n_slots = length(f.indices)
        if n_slots == 0
            # Scalar tensor — retrieve its value
            ct = get_components(f.tensor_name, Symbol[])
            push!(factor_arrays, ct.array)
        else
            ct = get_components(f.tensor_name, fill(basis, n_slots))
            push!(factor_arrays, ct.array)
        end
    end

    coeff = Float64(term.coeff)
    n_free = length(free_labels)

    # Scalar result (no free indices)
    if n_free == 0
        total = _einsum_eval(
            factor_arrays, factor_labels, dummy_labels, Dict{Symbol,Int}(), dim
        )
        return (fill(coeff * total), free_labels)
    end

    # Tensor result
    result_shape = ntuple(_ -> dim, n_free)
    result = zeros(Float64, result_shape...)

    for free_idx in CartesianIndices(result_shape)
        assignment = Dict{Symbol,Int}()
        for (i, lbl) in enumerate(free_labels)
            assignment[lbl] = free_idx[i]
        end
        val = _einsum_eval(factor_arrays, factor_labels, dummy_labels, assignment, dim)
        result[free_idx] = coeff * val
    end

    (result, free_labels)
end

"""
    _einsum_eval(factor_arrays, factor_labels, dummy_labels, assignment, dim) → Float64

Recursively sum over dummy indices, then evaluate the product of all factors.
Uses a pre-allocated index buffer per factor and a flat assignment vector
(keyed by label ordinal) to avoid Dict/Array allocation in the inner loop.
"""
function _einsum_eval(
    factor_arrays::Vector{<:AbstractArray},
    factor_labels::Vector{Vector{Symbol}},
    dummy_labels::Vector{Symbol},
    assignment::Dict{Symbol,Int},
    dim::Int,
    dummy_idx::Int=1,
)::Float64
    # On first call, build mapping and pre-allocate buffers, then delegate
    if dummy_idx == 1
        # Map label → ordinal in a flat assignment vector
        all_labels = union(keys(assignment), dummy_labels)
        label_to_ord = Dict{Symbol,Int}()
        for (i, lbl) in enumerate(all_labels)
            label_to_ord[lbl] = i
        end
        # Flat assignment: ordinal → value
        flat = zeros(Int, length(all_labels))
        for (lbl, v) in assignment
            flat[label_to_ord[lbl]] = v
        end
        # Pre-compute ordinal indices for each factor (avoid repeated Dict lookup)
        factor_ords = [Int[label_to_ord[l] for l in labels] for labels in factor_labels]
        # Pre-allocate index buffer per factor
        factor_buf = [Vector{Int}(undef, length(labels)) for labels in factor_labels]
        # Dummy label ordinals
        dummy_ords = Int[label_to_ord[l] for l in dummy_labels]
        return _einsum_inner(
            factor_arrays, factor_ords, factor_buf, dummy_ords, flat, dim, 1
        )
    end
    # Fallback (should not be reached with the new path)
    error("_einsum_eval: unexpected dummy_idx > 1 in top-level call")
end

function _einsum_inner(
    factor_arrays::Vector{<:AbstractArray},
    factor_ords::Vector{Vector{Int}},
    factor_buf::Vector{Vector{Int}},
    dummy_ords::Vector{Int},
    flat::Vector{Int},
    dim::Int,
    dummy_idx::Int,
)::Float64
    if dummy_idx > length(dummy_ords)
        # All indices assigned — evaluate the product
        prod_val = 1.0
        for (fi, arr) in enumerate(factor_arrays)
            ords = factor_ords[fi]
            if isempty(ords)
                prod_val *= Float64(arr[])
            else
                buf = factor_buf[fi]
                @inbounds for k in eachindex(ords)
                    buf[k] = flat[ords[k]]
                end
                prod_val *= Float64(arr[buf...])
            end
        end
        return prod_val
    end

    # Sum over current dummy label
    ord = dummy_ords[dummy_idx]
    total = 0.0
    for v in 1:dim
        @inbounds flat[ord] = v
        total += _einsum_inner(
            factor_arrays, factor_ords, factor_buf, dummy_ords, flat, dim, dummy_idx + 1
        )
    end
    total
end

"""
    ToBasis(expr_str, basis) → CTensorObj

Convert an abstract-index tensor expression to component form in the given basis.

Handles single tensors, products, sums, and automatically contracts dummy
(repeated) indices via einsum.

# Examples

```julia
ToBasis("g[-a,-b]", :Polar)           # metric components
ToBasis("g[-a,-b] * v[a]", :Polar)    # contraction g_{ab} v^a
ToBasis("T[-a,-b] + S[-a,-b]", :Polar) # sum of tensors
```
"""
function ToBasis(expr_str::AbstractString, basis::Symbol)::CTensorObj
    BasisQ(basis) || error("ToBasis: basis $basis not defined")
    terms = _parse_expression(expr_str)
    isempty(terms) && error("ToBasis: cannot convert empty expression")

    dim = length(CNumbersOf(basis))

    # Evaluate each term
    term_results = [_tobasis_term(t, basis, dim) for t in terms]

    isempty(term_results) && error("ToBasis: no valid terms after evaluation")
    # All terms must have same number of free indices
    n_free = length(term_results[1][2])
    for (i, (_, free)) in enumerate(term_results)
        length(free) == n_free ||
            error("ToBasis: term $i has $(length(free)) free indices, expected $n_free")
    end

    # Sum all term arrays
    result = term_results[1][1]
    for i in 2:length(term_results)
        result = result .+ term_results[i][1]
    end

    bases = fill(basis, n_free)

    # Derive tensor name: use original name for single-factor single-term
    tname = :_ToBasis
    if length(terms) == 1 && length(terms[1].factors) == 1
        tname = terms[1].factors[1].tensor_name
    end

    CTensorObj(tname, Array(result), collect(bases), 0)
end

function ToBasis(expr_str::AbstractString, basis::AbstractString)::CTensorObj
    ToBasis(expr_str, Symbol(basis))
end

"""
    FromBasis(tensor, bases) → String

Return the abstract-index expression string for a tensor whose components
are stored in the given bases. Verifies components exist, then reconstructs
the symbolic form using the tensor's declared index slots.
"""
function FromBasis(tensor::Symbol, bases::Vector{Symbol})::String
    # Verify components exist (will error if not)
    get_components(tensor, bases)

    # Reconstruct abstract expression from tensor's declared slots
    if haskey(_metrics, tensor)
        m = _metrics[tensor]
        man = _manifolds[m.manifold]
        labels = man.index_labels
        return string(tensor) * "[-" * string(labels[1]) * ",-" * string(labels[2]) * "]"
    end

    haskey(_tensors, tensor) || error("FromBasis: tensor $tensor not found in registry")

    t_obj = _tensors[tensor]
    if isempty(t_obj.slots)
        return string(tensor) * "[]"
    end

    idx_strs = String[]
    for slot in t_obj.slots
        prefix = slot.covariant ? "-" : ""
        push!(idx_strs, prefix * string(slot.label))
    end
    string(tensor) * "[" * join(idx_strs, ",") * "]"
end

function FromBasis(tensor::AbstractString, bases::Vector)::String
    invoke(
        FromBasis,
        Tuple{Symbol,Vector{Symbol}},
        Symbol(tensor),
        Symbol[Symbol(b) for b in bases],
    )
end

"""
    TraceBasisDummy(tensor, bases) → CTensorObj

Automatically find and contract all pairs of basis indices where one slot is
covariant and the other is contravariant (with the same basis), mirroring
Wolfram's TraceBasisDummy. Returns the contracted CTensorObj.

For a rank-2 mixed tensor like T^a_{b} with both slots in the same basis,
this computes the trace.
"""
function TraceBasisDummy(tensor::Symbol, bases::Vector{Symbol})::CTensorObj
    ct = get_components(tensor, bases)

    # Get slot variance from tensor definition
    slots = if haskey(_tensors, tensor)
        _tensors[tensor].slots
    elseif haskey(_metrics, tensor)
        m = _metrics[tensor]
        man = _manifolds[m.manifold]
        labels = man.index_labels
        [IndexSpec(labels[1], true), IndexSpec(labels[2], true)]
    else
        error("TraceBasisDummy: tensor $tensor not found in registry")
    end

    length(slots) == length(bases) || error(
        "TraceBasisDummy: number of bases ($(length(bases))) ≠ number of slots ($(length(slots)))",
    )

    # Find pairs of same-basis slots with opposite variance
    contracted = Set{Int}()
    pairs = Tuple{Int,Int}[]
    for i in 1:length(bases)
        i in contracted && continue
        for j in (i + 1):length(bases)
            j in contracted && continue
            if bases[i] == bases[j] && slots[i].covariant != slots[j].covariant
                push!(pairs, (i, j))
                push!(contracted, i)
                push!(contracted, j)
                break
            end
        end
    end

    isempty(pairs) && error(
        "TraceBasisDummy: no dummy basis index pairs found (need same basis, opposite variance)",
    )

    # Contract pairs iteratively
    result_array = ct.array
    result_bases = collect(bases)
    offset = 0
    for (orig_i, orig_j) in pairs
        cur_i = orig_i - offset
        cur_j = orig_j - offset
        result_array = _contract_array_axes(result_array, cur_i, cur_j)
        # Remove the two contracted bases entries
        s1, s2 = minmax(cur_i, cur_j)
        deleteat!(result_bases, s2)
        deleteat!(result_bases, s1)
        offset += 2
    end

    CTensorObj(tensor, Array(result_array), result_bases, ct.weight)
end

function TraceBasisDummy(tensor::AbstractString, bases::Vector)::CTensorObj
    TraceBasisDummy(Symbol(tensor), Symbol[Symbol(b) for b in bases])
end
