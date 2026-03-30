# ============================================================
# xPert: Background metric consistency and perturbation order
# ============================================================

"""
    def_perturbation!(tensor, background, order) → PerturbationObj

Register a perturbation tensor.

  - `tensor`     — name of the perturbed tensor (e.g. `:Pertg1`)
  - `background` — name of the background tensor it perturbs (e.g. `:g`)
  - `order`      — perturbation order (≥ 1)

The perturbed tensor must already be registered (via `def_tensor!`).
The background tensor must already be registered (via `def_tensor!` or `def_metric!`).
Raises an error if either tensor is unknown, `order < 1`, or the perturbation
is already defined.
"""
function def_perturbation!(
    tensor::Symbol, background::Symbol, order::Int; session::Session=_default_session[]
)::PerturbationObj
    validate_order(order; context="def_perturbation! order")
    PerturbationQ(tensor; session) &&
        throw(ArgumentError("def_perturbation!: perturbation $tensor already defined"))
    haskey(session.tensors, tensor) || throw(
        ArgumentError(
            "def_perturbation!: tensor $tensor not registered — call def_tensor! first"
        ),
    )
    haskey(session.tensors, background) || throw(
        ArgumentError("def_perturbation!: background tensor $background not registered")
    )
    for (existing_name, existing_p) in session.perturbations
        if existing_p.background == background && existing_p.order == order
            throw(
                ArgumentError(
                    "def_perturbation!: order-$order perturbation for $background already registered as $existing_name",
                ),
            )
        end
    end

    p = PerturbationObj(tensor, background, order)
    session.perturbations[tensor] = p
    push!(session.perturbation_list, tensor)
    p
end

function def_perturbation!(
    tensor::AbstractString,
    background::AbstractString,
    order::Int;
    session::Session=_default_session[],
)
    def_perturbation!(Symbol(tensor), Symbol(background), order; session)
end

"""
    check_metric_consistency(metric_name) → Bool

Verify that a registered metric is internally consistent: its metric tensor
is symmetric and its inverse (raised-index version) is registered as its own
symmetric tensor.  Currently validates:

 1. The metric tensor exists in the tensor registry.
 2. The metric is recorded in the metric registry (via `def_metric!`).
 3. The metric tensor is symmetric (rank-2 with Symmetric symmetry).

Returns `true` if all checks pass, `false` otherwise (never throws).
"""
function check_metric_consistency(
    metric_name::Symbol; session::Session=_default_session[]
)::Bool
    # Check metric tensor is defined
    t = get(session.tensors, metric_name, nothing)
    isnothing(t) && return false

    # Check metric is registered in the metric registry
    found = false
    for (_, m) in session.metrics
        if m.name == metric_name
            found = true
            break
        end
    end
    found || return false

    # Check rank-2 symmetric
    length(t.slots) == 2 || return false
    t.symmetry.type == :Symmetric || return false

    true
end

function check_metric_consistency(
    metric_name::AbstractString; session::Session=_default_session[]
)::Bool
    check_metric_consistency(Symbol(metric_name); session)
end

"""
    check_perturbation_order(tensor_name, order) → Bool

Verify that a perturbation tensor is registered with the given perturbation order.
Returns `true` if `tensor_name` is a registered perturbation of exactly `order`,
`false` otherwise.
"""
function check_perturbation_order(
    tensor_name::Symbol, order::Int; session::Session=_default_session[]
)::Bool
    p = get(session.perturbations, tensor_name, nothing)
    isnothing(p) && return false
    p.order == order
end

function check_perturbation_order(
    tensor_name::AbstractString, order::Int; session::Session=_default_session[]
)::Bool
    check_perturbation_order(Symbol(tensor_name), order; session)
end

"""
    PerturbationOrder(tensor_name) → Int

Return the perturbation order of a registered perturbation tensor.
Throws an error if `tensor_name` is not a registered perturbation.

# Examples

```julia
PerturbationOrder(:Pertg1)   # → 1
PerturbationOrder(:Pertg2)   # → 2
```
"""
function PerturbationOrder(tensor_name::Symbol; session::Session=_default_session[])::Int
    p = get(session.perturbations, tensor_name, nothing)
    isnothing(p) && throw(
        ArgumentError("PerturbationOrder: $tensor_name is not a registered perturbation"),
    )
    p.order
end

function PerturbationOrder(
    tensor_name::AbstractString; session::Session=_default_session[]
)::Int
    PerturbationOrder(Symbol(tensor_name); session)
end

"""
    PerturbationAtOrder(background, order) → Symbol

Return the name of the perturbation tensor registered for `background` at
perturbation `order`.  Throws an error if no such perturbation is registered.

# Examples

```julia
PerturbationAtOrder(:g, 1)   # → :Pertg1
PerturbationAtOrder(:g, 2)   # → :Pertg2
```
"""
function PerturbationAtOrder(
    background::Symbol, order::Int; session::Session=_default_session[]
)::Symbol
    for (pname, p) in session.perturbations
        if p.background == background && p.order == order
            return pname
        end
    end
    throw(
        ArgumentError(
            "PerturbationAtOrder: no order-$order perturbation registered for $background"
        ),
    )
end

function PerturbationAtOrder(
    background::AbstractString, order::Int; session::Session=_default_session[]
)::Symbol
    PerturbationAtOrder(Symbol(background), order; session)
end

# ============================================================
# perturb() — Leibniz expansion of perturbations
# ============================================================

"""
    perturb(tensor_name::Symbol, order::Int) → String

Look up the registered perturbation tensor for `tensor_name` at the given
perturbation order.  Returns the perturbation tensor name as a String, or
throws an error if no such perturbation is registered.
"""
function perturb(tensor_name::Symbol, order::Int)::String
    validate_order(order)
    for (pname, p) in _perturbations
        if p.background == tensor_name && p.order == order
            return String(pname)
        end
    end
    throw(
        ArgumentError(
            "perturb: no order-$order perturbation registered for $tensor_name. " *
            "Register with def_perturbation!(:pert_name, :$tensor_name, $order).",
        ),
    )
end

"""
    perturb(expr::AbstractString, order::Int) → String

Apply the Leibniz rule to expand perturbations of a tensor expression at
the given order.

## Supported forms

  - Single tensor name  — looks up registered perturbation for that background.
    Index decorations (e.g. `Cng[-a,-b]`) are stripped before lookup.
  - Sum  `A + B`        — `perturb(A,n) + perturb(B,n)`.
  - Difference `A - B`  — `perturb(A,n) - perturb(B,n)`.
  - Product `A B` or `A * B` — general Leibniz (multinomial) rule:
    ``δⁿ(A₁⋯Aₖ) = Σ C(n;i₁,…,iₖ) δⁱ¹(A₁)⋯δⁱᵏ(Aₖ)``
    where the sum runs over all non-negative integer compositions
    ``i₁+⋯+iₖ = n`` and ``C`` is the multinomial coefficient.
  - Numeric coefficient `c A` — coefficient passes through unchanged.
  - Factor with no registered perturbation — treated as background (variation = 0).
"""
function perturb(expr::AbstractString, order::Int)::String
    validate_order(order)
    s = strip(expr)

    # ── 1. Sum / difference (split on " + " and " - ") ──────────────────────
    plus_parts = split(s, " + ")
    if length(plus_parts) > 1
        perturbed = [perturb(strip(p), order) for p in plus_parts]
        return join(perturbed, " + ")
    end

    minus_parts = split(s, " - ")
    if length(minus_parts) > 1
        result_parts = String[]
        push!(result_parts, perturb(strip(minus_parts[1]), order))
        for p in minus_parts[2:end]
            push!(result_parts, perturb(strip(p), order))
        end
        return join(result_parts, " - ")
    end

    # ── 2. Product (space-separated or "*"-separated factors) ────────────────
    s_norm = replace(s, " * " => " ")
    factors = split(s_norm)

    # Separate leading numeric coefficient (first factor only)
    coeff = ""
    tensor_factors = String[]
    for (i, f) in enumerate(factors)
        fs = String(f)
        if i == 1 && (tryparse(Float64, fs) !== nothing || tryparse(Int, fs) !== nothing)
            coeff = fs
        else
            push!(tensor_factors, fs)
        end
    end

    if isempty(tensor_factors)
        return "0"   # pure numeric — no variation
    end

    if length(tensor_factors) == 1
        # Strip index decorations before registry lookup (e.g. "Cng[-a,-b]" → "Cng")
        raw = tensor_factors[1]
        bare = replace(raw, r"\[.*\]$" => "")
        tname = Symbol(bare)
        # If the factor is itself a registered perturbation, return it at its own
        # order and 0 at any other order.
        if haskey(_perturbations, tname)
            p = _perturbations[tname]
            result = p.order == order ? String(tname) : "0"
            return coeff == "" ? result : "$coeff $result"
        end
        # Look up registered perturbation by background + order; return "0" if none
        try
            perturbed_name = perturb(tname, order)
            return coeff == "" ? perturbed_name : "$coeff $perturbed_name"
        catch e
            e isa ArgumentError || rethrow(e)
            return "0"
        end
    end

    # Multiple tensor factors — general multinomial Leibniz rule
    k = length(tensor_factors)
    comps = _compositions(order, k)

    # Parse numeric coefficient once (already validated as parseable above)
    coeff_num = if coeff == ""
        1
    else
        c = tryparse(Int, coeff)
        c !== nothing ? c : parse(Float64, coeff)
    end

    terms = String[]
    for comp in comps
        mc = _multinomial(order, comp)
        valid = true
        perturbed_factors = String[]
        for (idx, ord) in enumerate(comp)
            if ord == 0
                push!(perturbed_factors, tensor_factors[idx])
            else
                try
                    pi = perturb(tensor_factors[idx], ord)
                    if pi == "0"
                        valid = false
                        break
                    end
                    push!(perturbed_factors, pi)
                catch e
                    e isa ArgumentError || rethrow(e)
                    valid = false
                    break
                end
            end
        end
        valid || continue

        total = coeff_num * mc
        term_expr = join(perturbed_factors, " ")
        if total == 1
            push!(terms, term_expr)
        elseif total == floor(total)
            push!(terms, "$(Int(total)) $term_expr")
        else
            push!(terms, "$total $term_expr")
        end
    end
    isempty(terms) ? "0" : join(terms, " + ")
end

"""
Generate all compositions of `n` into `k` non-negative integer parts.

Returns compositions in descending order of the first element, so that
for order=1 the term with the first factor perturbed comes first (matching
the natural Leibniz convention).
"""
function _compositions(n::Int, k::Int)::Vector{Vector{Int}}
    result = Vector{Vector{Int}}()
    if k == 1
        push!(result, [n])
        return result
    end
    for first in n:-1:0
        for rest in _compositions(n - first, k - 1)
            push!(result, vcat([first], rest))
        end
    end
    return result
end

"""
Multinomial coefficient: ``n! / (k₁! k₂! ⋯ kₘ!)``.
"""
function _multinomial(n::Int, parts::Vector{Int})::Int
    return factorial(n) ÷ prod(factorial(ki) for ki in parts)
end

"""
    Simplify(expression::AbstractString) → String

Algebraic simplification of a tensor expression.

Iterates `Contract` followed by `ToCanonical` until the expression stops
changing (convergence), providing:

  - Metric contraction (index raising/lowering, self-trace → dimension)
  - Weyl-tracelessness and Einstein-trace physics rules
  - Index canonicalization and sign normalization
  - Like-term collection (sum simplification)
  - Bianchi identity reduction
  - Einstein tensor expansion

For example, `g^{ab}g_{ab}` is reduced to `n` (the manifold dimension) in
a single pass without requiring a prior `Contract` call.
"""
function Simplify(expression::AbstractString)::String
    current = strip(expression)
    max_iters = 20
    for _ in 1:max_iters
        contracted = Contract(current)
        canonical = ToCanonical(contracted)
        canonical == current && return canonical  # full pass produced no change → converged
        current = canonical
    end
    current
end

# ============================================================
# PerturbCurvature — first-order curvature perturbation formulas
# ============================================================

"""
    perturb_curvature(covd_name, metric_pert_name; order=1) → Dict{String,String}

Return the first-order perturbation formulas for the Riemann tensor, Ricci tensor,
Ricci scalar, and Christoffel symbol perturbation for the metric associated with
`covd_name`, using `metric_pert_name` as the first-order metric perturbation h_{ab}.

The formulas are returned in the system's CovD string notation using the manifold's
first four abstract index labels.  Index positions:
a = idxs[1], b = idxs[2], c = idxs[3], d = idxs[4]

## Standard GR perturbation theory (xPert conventions)

First-order Christoffel perturbation:
δΓ^a_{bc} = (1/2) g^{ad} (∇_b h_{cd} + ∇_c h_{bd} - ∇_d h_{bc})

First-order Riemann perturbation (fully covariant):
δR_{abcd} = ∇_c δΓ_{abd} - ∇_d δΓ_{abc}
(with all indices lowered using the background metric)

First-order Ricci perturbation:
δR_{ab} = ∇_c δΓ^c_{ab} - ∇_b δΓ^c_{ac}
= (1/2)(∇_c ∇_a h^c_b + ∇_c ∇_b h^c_a - □h_{ab} - ∇_a ∇_b h)

First-order Ricci scalar perturbation:
δR = g^{ab} δR_{ab} - R_{ab} h^{ab}

The returned dict has keys:
"Christoffel1" — δΓ expressed in CovD notation (mixed index)
"Riemann1"     — δR_{abcd} in CovD notation
"Ricci1"       — δR_{ab} in CovD notation
"RicciScalar1" — δR string formula (contracted Ricci)

All expressions use abstract index labels from the metric's manifold.
"""
function perturb_curvature(
    covd_name::Symbol, metric_pert_name::Symbol; order::Int=1
)::Dict{String,String}
    order == 1 || error("perturb_curvature: only order=1 is implemented")

    # Look up the metric
    metric_obj = get(_metrics, covd_name, nothing)
    isnothing(metric_obj) &&
        error("perturb_curvature: no metric registered for covd $covd_name")

    # Look up the perturbation tensor — it must be registered
    haskey(_tensors, metric_pert_name) ||
        error("perturb_curvature: perturbation tensor $metric_pert_name not registered")

    # Fetch manifold and its index labels
    manifold_sym = metric_obj.manifold
    manifold_obj = get(_manifolds, manifold_sym, nothing)
    isnothing(manifold_obj) && error("perturb_curvature: manifold $manifold_sym not found")

    idxs = manifold_obj.index_labels
    length(idxs) >= 4 ||
        error("perturb_curvature: manifold needs ≥ 4 index labels, got $(length(idxs))")

    # Short aliases for the abstract index labels (as strings).
    # Free indices: a(1), b(2), c(3), d(4).
    # Contraction dummy e: use 5th index if available, otherwise use the 4th
    # (since d is only free in Riemann but not in Ricci/Christoffel, reusing it
    # as a contraction dummy in those sub-expressions is valid).
    a = string(idxs[1])
    b = string(idxs[2])
    c = string(idxs[3])
    d = string(idxs[4])
    # Dummy index for index contractions (e.g. in Christoffel, Ricci trace slot)
    # Must not collide with free indices; use 5th label if available, else 4th.
    e = length(idxs) >= 5 ? string(idxs[5]) : d

    g = string(metric_obj.name)   # e.g. "Cng"
    h = string(metric_pert_name)  # e.g. "Pertg1"
    cd = string(covd_name)         # e.g. "Cnd"
    ricci = "Ricci" * cd         # e.g. "RicciCnd"
    rscalar = "RicciScalar" * cd

    # ── Christoffel perturbation δΓ^a_{bc} ────────────────────────────────
    # δΓ^a_{bc} = (1/2) g^{ae}(∇_b h_{ce} + ∇_c h_{be} - ∇_e h_{bc})
    # Free indices: a (up), b (down), c (down); dummy: e.
    christoffel1 = string(
        "(1/2)*",
        g,
        "[",
        a,
        ",",
        e,
        "](",
        cd,
        "[-",
        b,
        "][",
        h,
        "[-",
        c,
        ",-",
        e,
        "]]",
        " + ",
        cd,
        "[-",
        c,
        "][",
        h,
        "[-",
        b,
        ",-",
        e,
        "]]",
        " - ",
        cd,
        "[-",
        e,
        "][",
        h,
        "[-",
        b,
        ",-",
        c,
        "]]",
        ")",
    )

    # ── Riemann perturbation δR_{abcd} ────────────────────────────────────
    # Palatini (linearized Riemann) formula — second-derivative form:
    #   δR_{abcd} = (1/2)(∇_c ∇_a h_{bd} - ∇_c ∇_b h_{ad}
    #                     - ∇_d ∇_a h_{bc} + ∇_d ∇_b h_{ac})
    # Free indices: a,b (first pair), c,d (second pair) — all covariant.
    # No dummy needed here.
    riemann1 = string(
        "(1/2)(",
        cd,
        "[-",
        c,
        "][",
        cd,
        "[-",
        a,
        "][",
        h,
        "[-",
        b,
        ",-",
        d,
        "]]]",
        " - ",
        cd,
        "[-",
        c,
        "][",
        cd,
        "[-",
        b,
        "][",
        h,
        "[-",
        a,
        ",-",
        d,
        "]]]",
        " - ",
        cd,
        "[-",
        d,
        "][",
        cd,
        "[-",
        a,
        "][",
        h,
        "[-",
        b,
        ",-",
        c,
        "]]]",
        " + ",
        cd,
        "[-",
        d,
        "][",
        cd,
        "[-",
        b,
        "][",
        h,
        "[-",
        a,
        ",-",
        c,
        "]]]",
        ")",
    )

    # ── Ricci perturbation δR_{ab} ────────────────────────────────────────
    # de Donder / Lichnerowicz form (valid on any background):
    #   δR_{ab} = (1/2)(∇^c ∇_a h_{bc} + ∇^c ∇_b h_{ac} - □h_{ab} - ∇_a ∇_b h)
    # where h = g^{cd} h_{cd} and □ = g^{cd}∇_c∇_d.
    # Written with explicit metric raising:
    #   = (1/2)(g[c,e] cd[-e][cd[-a][h[-b,-c]]]
    #         + g[c,e] cd[-e][cd[-b][h[-a,-c]]]
    #         - g[c,e] cd[-c][cd[-e][h[-a,-b]]]
    #         - cd[-a][cd[-b][g[c,e] h[-c,-e]]])
    # Free indices: a,b. Dummies: c,e (c is free-slot dummy, e is raise dummy).
    # For the box term and trace term we need two summation dummies.
    # Use c and e where e = 5th index (or d if only 4 available).
    ricci1 = string(
        "(1/2)(",
        g,
        "[",
        c,
        ",",
        e,
        "] ",
        cd,
        "[-",
        e,
        "][",
        cd,
        "[-",
        a,
        "][",
        h,
        "[-",
        b,
        ",-",
        c,
        "]]]",
        " + ",
        g,
        "[",
        c,
        ",",
        e,
        "] ",
        cd,
        "[-",
        e,
        "][",
        cd,
        "[-",
        b,
        "][",
        h,
        "[-",
        a,
        ",-",
        c,
        "]]]",
        " - ",
        g,
        "[",
        c,
        ",",
        e,
        "] ",
        cd,
        "[-",
        c,
        "][",
        cd,
        "[-",
        e,
        "][",
        h,
        "[-",
        a,
        ",-",
        b,
        "]]]",
        " - ",
        cd,
        "[-",
        a,
        "][",
        cd,
        "[-",
        b,
        "][",
        g,
        "[",
        c,
        ",",
        e,
        "] ",
        h,
        "[-",
        c,
        ",-",
        e,
        "]",
        "]]",
        ")",
    )

    # ── Ricci scalar perturbation δR ──────────────────────────────────────
    # δR = g^{ab} δR_{ab} - R^{ab} h_{ab}
    # g[a,b] * ricci1 gives g^{ab}δR_{ab} (ricci1 already carries the 1/2 factor).
    # Background Ricci correction: R_{ac}g^{ab}h_b^c = R^{ab}h_{ab} (symmetric R,h).
    # Free indices: none (scalar). Dummies: a,b,c.
    ricci_scalar1 = string(
        g,
        "[",
        a,
        ",",
        b,
        "] ",
        ricci1,
        " - ",
        ricci,
        "[-",
        a,
        ",-",
        c,
        "] ",
        g,
        "[",
        a,
        ",",
        b,
        "] ",
        h,
        "[-",
        b,
        ",",
        c,
        "]",
    )

    Dict{String,String}(
        "Christoffel1" => christoffel1,
        "Riemann1" => riemann1,
        "Ricci1" => ricci1,
        "RicciScalar1" => ricci_scalar1,
    )
end

function perturb_curvature(
    covd_name::AbstractString, metric_pert_name::AbstractString; order::Int=1
)::Dict{String,String}
    perturb_curvature(Symbol(covd_name), Symbol(metric_pert_name); order=order)
end

export perturb_curvature

# ============================================================
# IBP — Integration By Parts
# ============================================================

"""
Simplify `expr` only if it contains no CovD-applied factors (patterns like
`CovD[-a][inner]`).  `_parse_monomial` truncates such factors at the first
bracket group, so `Simplify` would corrupt them.  A quick regex scan over
registered CovD names is sufficient; full factor parsing is not needed.
"""
function _safe_simplify(expr::AbstractString)::String
    for (covd_sym, _) in _metrics
        occursin(Regex(string(covd_sym) * raw"\[-\w+\]\["), expr) && return String(expr)
    end
    Simplify(expr)
end

"""
Split a multiplicative term body into individual factor strings.
Each factor is `Name[...]` or `CovD[-a][inner_expr]` (CovD has two bracket groups).
"""
function _split_factor_strings(term_body::AbstractString)::Vector{String}
    body = strip(term_body)
    factors = String[]
    i = firstindex(body)
    n = lastindex(body)
    while i <= n
        # skip whitespace between factors
        while i <= n && isspace(body[i])
            i = nextind(body, i)
        end
        i > n && break
        # Read identifier (name token)
        j = i
        while j <= n && (isletter(body[j]) || isdigit(body[j]) || body[j] == '_')
            j = nextind(body, j)
        end
        if j == i
            # Not an identifier character — skip
            i = nextind(body, i)
            continue
        end
        name_end = j  # exclusive end of name
        # Now consume all consecutive bracket groups
        groups = String[]
        k = name_end
        while k <= n
            # skip whitespace
            while k <= n && isspace(body[k])
                k = nextind(body, k)
            end
            k > n && break
            body[k] != '[' && break
            # consume matching bracket group
            depth = 0
            start_k = k
            while k <= n
                c = body[k]
                if c == '['
                    depth += 1
                elseif c == ']'
                    depth -= 1
                    if depth == 0
                        k = nextind(body, k)
                        break
                    end
                end
                k = nextind(body, k)
            end
            push!(groups, body[start_k:prevind(body, k)])
        end
        factor_str = body[i:prevind(body, name_end)] * join(groups)
        push!(factors, factor_str)
        i = k
    end
    factors
end

"""
Parse `covd_name[-der_idx][inner_expr]` from a factor string.
Returns a named tuple `(der_idx, inner)` or `nothing`.
"""
function _parse_covd_application(factor::AbstractString, covd::AbstractString)
    prefix = covd * "["
    startswith(factor, prefix) || return nothing
    fstr = factor
    # Find the end of the first bracket group (der_idx group)
    depth = 0
    i = firstindex(fstr) + length(prefix) - 1  # points to '['
    j = i
    while j <= lastindex(fstr)
        c = fstr[j]
        if c == '['
            depth += 1
        elseif c == ']'
            depth -= 1
            if depth == 0
                j = nextind(fstr, j)
                break
            end
        end
        j = nextind(fstr, j)
    end
    # fstr[i:prevind(fstr,j)] is the der_idx bracket group e.g. "[-ia]"
    der_bracket = fstr[i:prevind(fstr, j)]  # "[-ia]"
    # Strip outer brackets to get "-ia"
    der_idx_raw = strip(
        der_bracket[nextind(der_bracket, firstindex(der_bracket)):prevind(
            der_bracket, lastindex(der_bracket)
        )],
    )
    # Now consume inner bracket group
    k = j
    while k <= lastindex(fstr) && isspace(fstr[k])
        k = nextind(fstr, k)
    end
    k > lastindex(fstr) && return nothing
    fstr[k] != '[' && return nothing
    depth2 = 0
    start_inner = k
    while k <= lastindex(fstr)
        c = fstr[k]
        if c == '['
            depth2 += 1
        elseif c == ']'
            depth2 -= 1
            if depth2 == 0
                k = nextind(fstr, k)
                break
            end
        end
        k = nextind(fstr, k)
    end
    # Must have consumed entire string
    k <= lastindex(fstr) && return nothing
    inner_bracket = fstr[start_inner:prevind(fstr, k)]  # "[expr]"
    # Strip outer brackets
    inner = strip(
        inner_bracket[nextind(inner_bracket, firstindex(inner_bracket)):prevind(
            inner_bracket, lastindex(inner_bracket)
        )],
    )
    # Strip the leading '-' from der_idx to get the bare index label
    bare_idx = if startswith(der_idx_raw, "-")
        der_idx_raw[nextind(der_idx_raw, firstindex(der_idx_raw)):end]
    else
        der_idx_raw
    end
    return (der_idx=der_idx_raw, bare_idx=bare_idx, inner=String(inner))
end

"""
Check if bare index `idx` (e.g. "a") appears as a contracted (dummy) index inside `expr`.
"""
function _index_appears_in(expr::AbstractString, idx::AbstractString)::Bool
    any(
        p -> occursin(p, expr),
        ["[" * idx * ",", "[" * idx * "]", "," * idx * ",", "," * idx * "]"],
    )
end

"""
Extract leading coefficient from term body string.
Returns `(coeff::Rational{Int}, remaining_str)`.
Matches `(N/D) rest` or `N rest` (integer followed by whitespace). Otherwise coeff=1//1.
"""
function _extract_leading_coeff(body::AbstractString)
    s = String(strip(body))
    # Try rational: "(N/D) rest"
    m = match(r"^\((-?\d+)/(\d+)\)\s*(.*)"s, s)
    if m !== nothing
        num = parse(Int, something(m.captures[1]))
        den = parse(Int, something(m.captures[2]))
        return (num // den, String(strip(something(m.captures[3]))))
    end
    # Try integer followed by space: "N rest"
    m2 = match(r"^(-?\d+)\s+(.*)"s, s)
    if m2 !== nothing
        num = parse(Int, something(m2.captures[1]))
        return (num // 1, String(strip(something(m2.captures[2]))))
    end
    return (1 // 1, s)
end

"""
Format rational coefficient for positive printing.
"""
function _fmt_pos_coeff(c::Rational{Int})::String
    c == 1 // 1 && return ""
    denominator(c) == 1 && return "$(numerator(c)) "
    return "($(numerator(c))/$(denominator(c))) "
end

"""
Format (coeff, body) as a signed term string suitable for joining.
"""
function _term_string(c::Rational{Int}, body::AbstractString)::String
    body_s = String(body)::String
    if c == 1 // 1
        return body_s
    elseif c == -1 // 1
        return "-" * body_s
    elseif c > 0
        return _fmt_pos_coeff(c) * body_s
    else
        return "-" * _fmt_pos_coeff(-c) * body_s
    end
end

"""
Split expression into signed string terms. Returns `Vector{Tuple{Int, String}}` = [(sign, body), ...].
Splits on top-level `+` and `-`, tracking bracket depth.
"""
function _split_string_terms(expr::AbstractString)::Vector{Tuple{Int,String}}
    s = String(strip(expr))
    isempty(s) && return [(1, "0")]
    terms = Tuple{Int,String}[]
    depth = 0
    current = IOBuffer()
    current_sign = 1
    i = firstindex(s)
    n = lastindex(s)
    # Handle leading sign
    if i <= n && s[i] == '-'
        current_sign = -1
        i = nextind(s, i)
    elseif i <= n && s[i] == '+'
        current_sign = 1
        i = nextind(s, i)
    end
    while i <= n
        c = s[i]
        if c == '[' || c == '('
            depth += 1
            write(current, c)
        elseif c == ']' || c == ')'
            depth -= 1
            write(current, c)
        elseif depth == 0 && (c == '+' || c == '-')
            chunk = strip(String(take!(current)))
            if !isempty(chunk)
                push!(terms, (current_sign, chunk))
            end
            current_sign = c == '-' ? -1 : 1
            current = IOBuffer()
        else
            write(current, c)
        end
        i = nextind(s, i)
    end
    chunk = strip(String(take!(current)))
    if !isempty(chunk)
        push!(terms, (current_sign, chunk))
    end
    isempty(terms) && return [(1, "0")]
    terms
end

"""
Apply one IBP step to factors of a single term.
Returns `(new_coeff, new_body)` or `nothing` (no CovD found).
Returns `(0//1, "0")` for a pure total divergence.
"""
function _ibp_term_factors(
    factors::Vector{String}, coeff::Rational{Int}, covd::AbstractString
)
    # Find the first CovD factor
    covd_idx = findfirst(f -> startswith(f, covd * "["), factors)
    covd_idx === nothing && return nothing
    covd_factor = factors[covd_idx]
    parsed = _parse_covd_application(covd_factor, covd)
    parsed === nothing && return nothing
    der_idx = parsed.der_idx    # e.g. "-ia"
    bare_idx = parsed.bare_idx  # e.g. "ia"
    inner = parsed.inner        # inner expression

    # Remaining factors (all except this CovD)
    other_factors = [factors[k] for k in eachindex(factors) if k != covd_idx]

    if isempty(other_factors)
        # Pure divergence: covd[-a][expr_with_a_contracted]?
        if _index_appears_in(inner, bare_idx)
            return (0 // 1, "0")
        else
            # Not contracted — can't simplify (unusual), return unchanged as nothing
            return nothing
        end
    end

    # IBP: A * ∇_a B → -(∇_a A) * B, picking A = first non-CovD factor
    partner_idx = findfirst(f -> !startswith(f, covd * "["), other_factors)
    if partner_idx === nothing
        # All remaining are CovDs — take the first one
        partner_idx = 1
    end
    partner = other_factors[partner_idx]
    rest_others = [other_factors[k] for k in eachindex(other_factors) if k != partner_idx]

    # New CovD applied to the partner
    new_covd_factor = covd * "[" * der_idx * "][" * partner * "]"
    # New body = new_covd_factor * inner * rest_others
    new_factors_strs = String[]
    push!(new_factors_strs, new_covd_factor)
    push!(new_factors_strs, inner)
    append!(new_factors_strs, rest_others)
    new_body = join(filter(!isempty, new_factors_strs), " ")
    new_coeff = -coeff
    return (new_coeff, new_body)
end

"""
Join a vector of signed term strings into a sum expression.
Each element may start with `"-"` (negative) or not (positive).
Adjacent terms are separated by `" - "` or `" + "` as appropriate.
"""
function _join_term_strings(parts::Vector{String})::String
    isempty(parts) && return "0"
    out = IOBuffer()
    for (k, p) in enumerate(parts)
        if k == 1
            write(out, p)
        elseif startswith(p, "-")
            write(out, " - ", p[nextind(p, firstindex(p)):end])
        else
            write(out, " + ", p)
        end
    end
    String(take!(out))
end

"""
    IBP(expr, covd_name) → String

Integrate `expr` by parts with respect to `covd_name`. For each term:

  - Pure divergence `covd[-a][V[a]]`: dropped (→ 0)
  - Product `A * covd[-a][B]`: → `-(covd[-a][A]) * B` (mod total derivative)
  - Otherwise: unchanged
    Result is passed through Simplify.
"""
function IBP(expr::AbstractString, covd_name::AbstractString)::String
    terms = _split_string_terms(expr)
    result_terms = Tuple{Rational{Int},String}[]
    for (sign, body) in terms
        (coeff0, remaining) = _extract_leading_coeff(body)
        coeff = sign * coeff0
        factors = _split_factor_strings(remaining)
        ibp_result = _ibp_term_factors(factors, coeff, covd_name)
        if ibp_result === nothing
            # No CovD found — keep term unchanged
            push!(result_terms, (coeff, remaining))
        else
            (new_coeff, new_body) = ibp_result
            if new_coeff != 0 // 1
                push!(result_terms, (new_coeff, new_body))
            end
            # new_coeff == 0 means total divergence, drop the term
        end
    end
    isempty(result_terms) && return "0"
    raw = _join_term_strings([_term_string(c, b) for (c, b) in result_terms])
    _safe_simplify(raw)
end

function IBP(expr::AbstractString, covd::Symbol)::String
    IBP(expr, String(covd))
end

"""
    TotalDerivativeQ(expr, covd_name) → Bool

Return `true` iff `expr` is a total divergence (IBP drops it entirely).
"""
function TotalDerivativeQ(expr::AbstractString, covd_name::AbstractString)::Bool
    IBP(expr, covd_name) == "0"
end

function TotalDerivativeQ(expr::AbstractString, covd::Symbol)::Bool
    TotalDerivativeQ(expr, String(covd))
end

# ============================================================
# VarD — Variational (Euler-Lagrange) Derivative
# ============================================================

"""
Expand `covd[der_idx][f1 f2 ... fn]` via Leibniz product rule.
Returns a Vector of term strings, each with CovD applied to one factor.
"""
function _leibniz_covd(
    covd::AbstractString, der_idx::AbstractString, factors::Vector{String}
)::Vector{String}
    result = String[]
    for (i, f) in enumerate(factors)
        rest = [factors[k] for k in eachindex(factors) if k != i]
        new_covd = covd * "[" * der_idx * "][" * f * "]"
        parts = String[new_covd]
        append!(parts, rest)
        push!(result, join(filter(!isempty, parts), " "))
    end
    result
end

"""
Compute all EL contributions from a single term for variational derivative w.r.t. `field`.
Returns `Vector{Tuple{Rational{Int}, String}}` of `(coeff, body)` contributions.
"""
function _vard_term_contributions(
    factors::Vector{String},
    coeff::Rational{Int},
    field::AbstractString,
    covd::AbstractString,
)::Vector{Tuple{Rational{Int},String}}
    contributions = Tuple{Rational{Int},String}[]
    for (i, factor) in enumerate(factors)
        rest = [factors[k] for k in eachindex(factors) if k != i]
        rest_str = join(filter(!isempty, rest), " ")

        # Case 1: Direct field occurrence — factor starts with "field["
        if startswith(factor, field * "[")
            # Contribution: (+coeff, rest_str) or (+coeff, "1") if no rest
            body = isempty(rest_str) ? "1" : rest_str
            push!(contributions, (coeff, body))
            continue
        end

        # Case 2: covd[-a][field[...]] — first-order derivative
        parsed1 = _parse_covd_application(factor, covd)
        if parsed1 !== nothing && startswith(parsed1.inner, field * "[")
            # IBP: contribution is (-coeff, leibniz expansion applied to rest)
            # The EL term is -∇_a (rest) when field is ∇_a φ
            # i.e. we integrate by parts: -(∇_a rest)  → for each factor in rest
            der_bracket = covd * "[" * parsed1.der_idx * "]"
            if isempty(rest_str)
                # No other factors: contribution is trivially 0 (total div) — skip
                continue
            end
            rest_factors = _split_factor_strings(rest_str)
            leibniz_terms = _leibniz_covd(covd, parsed1.der_idx, rest_factors)
            for lt in leibniz_terms
                push!(contributions, (-coeff, lt))
            end
            continue
        end

        # Case 3: covd[-a][covd[-b][field[...]]] — second-order derivative
        if parsed1 !== nothing
            inner1 = parsed1.inner
            parsed2 = _parse_covd_application(inner1, covd)
            if parsed2 !== nothing && startswith(parsed2.inner, field * "[")
                # Two IBP steps → sign is +coeff
                # Apply outer Leibniz on rest, then wrap inner derivative
                der_outer = parsed1.der_idx
                der_inner = parsed2.der_idx
                inner_covd = covd * "[" * der_inner * "]"
                if isempty(rest_str)
                    # Only factor: ∇_a ∇_b φ — contribution is ∇_a ∇_b(1) = 0
                    continue
                end
                rest_factors = _split_factor_strings(rest_str)
                # Leibniz on rest with the outer derivative
                leibniz_terms = _leibniz_covd(covd, der_outer, rest_factors)
                for lt in leibniz_terms
                    # Wrap each leibniz term in the inner derivative
                    inner_lt_covd = covd * "[" * der_inner * "][" * lt * "]"
                    push!(contributions, (coeff, inner_lt_covd))
                end
                continue
            end
        end
    end
    contributions
end

"""
    VarD(expr, field_name, covd_name) → String

Euler-Lagrange derivative of Lagrangian `expr` w.r.t. field `field_name`.
Uses IBP to move derivatives off the field variation.
Result is simplified.
"""
function VarD(
    expr::AbstractString, field_name::AbstractString, covd_name::AbstractString
)::String
    terms = _split_string_terms(expr)
    all_contributions = Tuple{Rational{Int},String}[]
    for (sign, body) in terms
        (coeff0, remaining) = _extract_leading_coeff(body)
        coeff = sign * coeff0
        factors = _split_factor_strings(remaining)
        contribs = _vard_term_contributions(factors, coeff, field_name, covd_name)
        append!(all_contributions, contribs)
    end
    isempty(all_contributions) && return "0"
    raw = _join_term_strings([_term_string(c, b) for (c, b) in all_contributions])
    _safe_simplify(raw)
end

function VarD(expr::AbstractString, field::Symbol, covd::Symbol)::String
    VarD(expr, String(field), String(covd))
end

function VarD(expr::AbstractString, field::AbstractString, covd::Symbol)::String
    VarD(expr, field, String(covd))
end

function VarD(expr::AbstractString, field::Symbol, covd::AbstractString)::String
    VarD(expr, String(field), covd)
end
