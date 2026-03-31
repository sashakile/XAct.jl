## Context

XTensor's expression parser was built for flat tensor products (`T[-a,-b] V[-c]`).
CovD support was added later via a separate regex-based string parser because the
existing `FactorAST(name, indices)` had no slot for an operand, and refactoring would
have touched every function in the canonicalization pipeline.

This created two parallel parsers: one AST-based (for canonicalization) and one
string-based (for CovD sorting). The flat parser silently drops CovD operands.

## Goals / Non-Goals

- **Goal**: Single AST that represents flat products AND CovD application
- **Goal**: `ToCanonical("CD[-a][V[-b]]")` round-trips correctly (or errors explicitly)
- **Goal**: `SortCovDs`/`CommuteCovDs` use the same AST as `ToCanonical`
- **Non-Goal**: Full CovD canonicalization inside `ToCanonical` (that's a separate feature)
- **Non-Goal**: Changing the string syntax — `CD[-a][V[-b]]` remains the format

## Decisions

### AST node design

Extend `FactorAST` to a sum type:

```julia
# A factor is either a plain tensor or a CovD application
struct TensorFactor
    tensor_name::Symbol
    indices::Vector{String}
end

struct CovDFactor
    covd_name::Symbol
    deriv_index::String
    operand::Vector{FactorNode}  # the expression being differentiated
end

const FactorNode = Union{TensorFactor, CovDFactor}

struct TermAST
    coeff::Rational{Int}
    factors::Vector{FactorNode}
end
```

**Why Union over abstract type**: Julia's Union-splitting gives zero-overhead dispatch
for small unions. An abstract type hierarchy adds method table complexity for no benefit
with only 2 variants.

**Alternative considered**: Keep `FactorAST` flat and represent CovD as a special
tensor with a metadata field. Rejected because it would require every consumer of
`FactorAST` to check for the special case, which is what we're trying to eliminate.

### Parser changes

`_parse_monomial` currently stops when it sees `[` after `]` (not a letter). The fix:
after parsing `Name[indices]`, check if the next character is `[`. If so, recursively
parse the bracketed content as the operand of a `CovDFactor`.

### Migration strategy

Phase the change:

1. **Phase A** (guard): Add a check in `_parse_monomial` — if `]` is followed by `[`,
   raise an error: "CovD bracket syntax not supported in this context. Use SortCovDs."
   This eliminates silent data loss immediately.

2. **Phase B** (AST): Introduce `TensorFactor`/`CovDFactor`/`FactorNode`. Update
   `_parse_monomial` to produce them. Update `_canonicalize_term`, `_serialize`, and
   `_term_key_str` to handle both variants. `ToCanonical` passes CovD factors through
   unmodified (canonicalizes the non-CovD parts only).

3. **Phase C** (unify): Rewrite `SortCovDs`/`CommuteCovDs` to parse via the unified
   AST instead of `_extract_covd_chain`. Retire the string-based parser.

## Risks / Trade-offs

- **Risk**: Changing `FactorAST` breaks every function that pattern-matches on it.
  Mitigation: Phase A (error guard) ships first and is zero-risk. Phase B uses
  `TensorFactor` as a drop-in for `FactorAST` so existing code needs only a rename.

- **Risk**: CovD operands create nested AST — serialization, key-hashing, and
  coefficient collection must handle recursive structure.
  Mitigation: `_term_key_str` already uses string serialization; extending it to
  serialize CovD brackets is straightforward.

- **Trade-off**: Phase B makes `ToCanonical` "CovD-aware" (passes through without
  canonicalizing derivatives) but doesn't canonicalize CovD ordering — that stays
  in `SortCovDs`. This is intentional: CovD canonicalization involves Riemann
  correction terms and is a distinct algorithm.

## Open Questions

- Should `Contract` and `Simplify` attempt to contract through CovD brackets
  (e.g., `g^{ab} CD[-a][V[-b]]` → `CD^{a}[V[-a]]`)? Probably yes, but this
  can be deferred to a follow-up.
