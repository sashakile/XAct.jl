---
date: 2026-03-10T09:53:51-03:00
git_commit: 522e6ce
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-8pu, sxAct-8wv, sxAct-ljr, sxAct-938, sxAct-9gt
status: handoff
---

# Handoff: All 5 P1 Milestones Complete

## Context

All five P1-priority issues have been implemented and pushed in a single session using parallel subagents. The work touched `XPerm.jl`, `XTensor.jl`, `XCore.jl`, the Julia adapter (`julia_stub.py`), and the test/oracle infrastructure. The codebase is now in a clean state with all tests green.

Test baseline after this session: Julia XPerm 91/91, Julia XTensor 65/65, Python 544/544, 92 butler oracle tests pass, plus 51 new TOML oracle tests added.

## Current Status

### Completed
- [x] `sxAct-8pu` — `double_coset_rep` full Butler-Portugal algorithm (`src/julia/XPerm.jl:597-650`)
- [x] `sxAct-ljr` — AtomQ/SymbolName/NoPattern/SubHead/FindSymbols adapter integration (`src/sxact/adapter/julia_stub.py`)
- [x] `sxAct-8wv` — Multi-index sets: multi-manifold `def_tensor!` overload (`src/julia/XTensor.jl`) + adapter
- [x] `sxAct-938` — xPert background metric consistency: `def_perturbation!`, `check_metric_consistency`, `PerturbationQ` (`src/julia/XTensor.jl`)
- [x] `sxAct-9gt` — Young projectors: `YoungTableau`, `standard_tableau`, `row_symmetry_sgs`, `col_antisymmetry_sgs`, `young_projector` (`src/julia/XPerm.jl`)

### Planned (P2 open issues)
- [ ] `sxAct-kx9` — docs: Refactor directory structure to src/ layout and remove mkdocs
- [ ] `sxAct-bh8` — docs: Initialize standalone Julia project (docs/Project.toml)
- [ ] `sxAct-3et` — Epic: Unified Julia-Centric Documentation Overhaul
- [ ] `sxAct-82d` — FieldsX: Graded Symmetry for Fermions
- [ ] `sxAct-3s3` — Spinors: Newman-Penrose and GHP equations

## Critical Files

1. `src/sxact/adapter/julia_stub.py` — WL→Julia translation layer; most session changes landed here
2. `src/julia/XPerm.jl` — Butler-Portugal canonicalization + Young projectors (now ~1950 lines)
3. `src/julia/XTensor.jl` — Tensor algebra, xPert, multi-manifold support (~1600 lines)
4. `src/julia/XCore.jl` — Core utilities; `FindSymbols()` zero-arg overload added
5. `src/julia/tests/test_xperm.jl` — Julia unit tests (now 91, was 52)
6. `src/julia/tests/test_xtensor.jl` — Julia unit tests (now 65, was 49)

## Recent Changes

- `src/sxact/adapter/julia_stub.py` — Added `_bind_wl_atoms`, `_preprocess_wl_patterns`, `_preprocess_nopattern`, `_preprocess_subhead`, `_JULIA_KEYWORDS`, `_JULIA_BUILTINS`, `_WL_PATTERN_RE`; new actions `DefPerturbation`, `CheckMetricConsistency`; multi-manifold `def_tensor!` dispatch
- `src/julia/XPerm.jl` — Full `double_coset_rep` replacing stub; `YoungTableau` struct + 6 functions + WL-compat aliases
- `src/julia/XTensor.jl` — `PerturbationObj`, `def_perturbation!`, `check_metric_consistency`, `check_perturbation_order`, `PerturbationQ`; multi-manifold `def_tensor!` overloads
- `src/julia/XCore.jl` — `FindSymbols()` zero-argument method
- `src/sxact/adapter/base.py` — `DefPerturbation`, `CheckMetricConsistency` added to `supported_actions()`
- `src/sxact/runner/schemas/test-schema.json` + `tests/schema/test-schema.json` — `manifolds` field, `DefPerturbation`, `CheckMetricConsistency`, `CommuteCovDs` added to action schemas
- **New oracle snapshots**: `oracle/xcore/symbol_utils/` (13), `oracle/xperm/young_projectors/` (20), `oracle/xperm/multi_index_sets/` (8), `oracle/xtensor/xpert_background/` (10)
- **New TOML tests**: `tests/xperm/young_projectors.toml`, `tests/xperm/multi_index_sets.toml`, `tests/xtensor/xpert_background.toml`

## Key Learnings

### 1. Adapter preprocessing pipeline order matters

`_wl_to_jl` in `julia_stub.py` applies preprocessors in this order (as of this session):
```
_preprocess_apply_op → _preprocess_schreier_orbit → _preprocess_timing_destruct
→ _preprocess_subhead → _preprocess_wl_patterns → _preprocess_nopattern
→ [WL→Julia operator rewrites] → [backtick stripping]
```
`SubHead` must be handled before pattern stripping because `SubHead[f[x_]]` needs the `f` extracted while `x_` is still syntactically intact. `NoPattern` must come after pattern stripping so `NoPattern[x_]` resolves to `x` (bare symbol, no underscore).

### 2. `_bind_wl_atoms` is the key for unbound WL symbols

When WL code references bare symbols (e.g., `AtomQ[x]`, `f[x, y]`) that aren't defined in Julia, the adapter now calls `_bind_wl_atoms(jl, expr)` which:
- Scans the Julia expression string for lowercase identifiers that look like atoms
- Checks `isdefined(Main, :sym)` to avoid overwriting existing bindings (e.g., tensor/manifold objects)
- Pre-binds them as `Main.sym = :sym` (Julia Symbols) before evaluating the condition

This is called in both `_execute_assert` and `_execute_expr`. Without it, Julia raises `UndefVarError` for unbound names.

### 3. `SubHead` requires static head extraction

`SubHead[f[x]]` cannot be implemented as a Julia function call because `f` may be unbound. The preprocessor `_preprocess_subhead` statically extracts the outermost head using regex and replaces `SubHead[f[...]]` with `:f` at the Python level before Julia ever sees the expression.

### 4. WL CamelCase aliases for Julia snake_case functions

The `_wl_to_jl` adapter strips underscores (e.g., `row_symmetry_sgs` → `rowsymmetrysgs`). New Julia functions with underscores need WL-compat CamelCase aliases exported alongside. See `YoungTableau`-related aliases at the bottom of `XPerm.jl`:
```julia
const StandardTableau = standard_tableau
const RowSymmetrySGS = row_symmetry_sgs
const ColAntisymmetrySGS = col_antisymmetry_sgs
const YoungProjector = young_projector
const TableauFilling = tableau_filling
const TableauPartition = tableau_partition
```

### 5. `double_coset_rep` uses BFS Cayley graph enumeration

The full algorithm (replacing the stub at `XPerm.jl:597`):
1. Build transposition generators from each `dummy_group` (pairs of positions)
2. BFS over Cayley graph to enumerate all elements of dummy group D
3. For each `d ∈ D`, compute `right_coset_rep(compose(perm, d), sgs)`
4. Return the lexicographically minimum result

This is correct but potentially expensive for large dummy groups. For Tier 2 optimizations, consider Dimino's exact algorithm or lazy enumeration.

### 6. Multi-manifold `def_tensor!` uses `manifolds` (plural) key

The adapter checks for `manifolds` (array) before `manifold` (string) when dispatching `DefTensor`. The Julia overload signature:
```julia
def_tensor!(name::Symbol, index_specs::Vector{String}, manifolds::Vector{Symbol}; ...)
```
Validates each index label against the union of all listed manifolds' index sets. The first manifold is stored as primary.

### 7. Oracle snapshot hash formula

```python
import hashlib, json
canonical = json.dumps({"normalized_output": out, "properties": props}, sort_keys=True)
hash = f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:12]}"
```
For `"True"` output with empty properties: `sha256:7a834da09e03`.

## Open Questions

- [ ] `double_coset_rep` correctness for signed dummy groups (Lorentzian metric sign flip when swapping contravariant↔covariant) — current impl handles unsigned dummy transpositions only
- [ ] Young projectors not yet wired into `ToCanonical` — `young_projector` exists in XPerm but XTensor doesn't call it yet (needed for Invar)
- [ ] xPert `def_perturbation!` doesn't yet implement perturbation expansion rules (order 1/2 derivations) — only registry/metadata
- [ ] Multi-index set oracle snapshots (`oracle/xperm/multi_index_sets/`) use simple JSON format without `.wl` files — inconsistent with other oracle dirs

## Next Steps

1. **Wire Young projectors into ToCanonical** [Priority: HIGH — blocks Invar]
   - `XTensor.jl` `ToCanonical` needs to call `young_projector` for tensors with mixed-symmetry slots
   - Requires defining a tensor symmetry as a Young tableau, not just Sym/Antisym

2. **xPert perturbation expansion rules** [Priority: HIGH — blocks xPert milestone]
   - `def_perturbation!` currently only registers metadata
   - Need `perturb(expr, order)` that applies Leibniz rule to expand perturbations

3. **Fix multi_index_sets oracle to include .wl files** [Priority: LOW]
   - See `scripts/gen_butler_snapshots.py` for the pattern

4. **P2 docs issues** (`sxAct-kx9`, `sxAct-bh8`, `sxAct-3et`) [Priority: P2]
   - Directory restructure and Literate.jl documentation

## Artifacts

**New files:**
- `tests/xperm/young_projectors.toml`
- `tests/xperm/multi_index_sets.toml`
- `tests/xtensor/xpert_background.toml`
- `oracle/xcore/symbol_utils/` (13 JSON + 13 WL files)
- `oracle/xperm/young_projectors/` (20 JSON + 20 WL files)
- `oracle/xperm/multi_index_sets/` (8 JSON files, no WL)
- `oracle/xtensor/xpert_background/` (10 JSON + 10 WL files)

**Modified files:**
- `src/julia/XPerm.jl`
- `src/julia/XTensor.jl`
- `src/julia/XCore.jl`
- `src/julia/tests/test_xperm.jl`
- `src/julia/tests/test_xtensor.jl`
- `src/sxact/adapter/julia_stub.py`
- `src/sxact/adapter/base.py`
- `src/sxact/runner/schemas/test-schema.json`
- `tests/schema/test-schema.json`

## References

- Design spec: `specs/2026-03-06-xperm-xtensor-design.md`
- Previous handoff (butler suite completion): `handoffs/2026-03-09_09-44-21_butler-suite-100pct.md`
- Previous handoff (roadmap): `handoffs/2026-03-09_17-45-00_sxact-implementation-roadmap.md`
- beads issues: `bd show sxAct-8pu`, `bd show sxAct-8wv`, etc. (all now closed)
