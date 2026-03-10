---
date: 2026-03-10T14:39:13-03:00
git_commit: 952fe02
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issues: sxAct-gys, sxAct-82d, sxAct-2za
status: handoff
---

# Handoff: P1 + three P2 milestones (perturb, GradedSymmetric, Simplify)

## Context

sxAct is a Julia/Python CAS for differential geometry that re-implements xAct
(Mathematica) in Julia, with a Python adapter for test orchestration. This
session worked through one P1 and three P2 issues using a subagent-per-task
pattern with Rule-of-5-Universal reviews and full fix cycles before each commit.

The project uses a TOML test runner (`uv run xact-test run --adapter julia
--oracle-mode snapshot --oracle-dir oracle <file.toml>`) and `oracle_is_axiom =
true` for all new tests (Julia adapter is ground truth). The adapter is
`src/sxact/adapter/julia_stub.py`; the core algebra is `src/julia/XTensor.jl`.

## Current Status

### Completed this session
- [x] **sxAct-gys** (P1): `perturb(expr, order)` Leibniz expansion
  — `src/julia/XTensor.jl:1693–1821`, `tests/xtensor/xpert_perturb.toml` (5 tests)
- [x] **sxAct-82d** (P2): `GradedSymmetric` symmetry type + `FermionicQ` predicate
  — `src/julia/XPerm.jl:1004`, `src/julia/XTensor.jl:194–198, 282–285`, `tests/xtensor/fieldsX_graded.toml` (6 tests)
- [x] **sxAct-2za** (P2): `Simplify` action + metric self-trace bug fix in `Contract`
  — `src/julia/XTensor.jl:1534, 1548–1566, 1834–1855`, `tests/xtensor/simplify.toml` (3 tests)
- [x] All three committed and pushed to `main`

### In Progress
- [ ] **sxAct-00d** (P2): xTensor Basis and Frame support (tetrads, non-coordinate bases)
  — claimed (`status=in_progress`) but NOT started; no code written yet

### Planned (next P2s by priority)
- [ ] sxAct-1sn (P2): xCore Symbol Registry (ValidateSymbol, Namespace)
- [ ] sxAct-hyy (P2): xPert Perturbation Orders (h@n indexing) — depends on sxAct-gys ✓
- [ ] sxAct-sz5 (P2): xPert Curvature Expansion formulas
- [ ] sxAct-8tf (P2): xTras Variational Derivatives (VarD)
- [ ] sxAct-8oa (P2): xTras Symbolic Integration By Parts (IBP)
- [ ] sxAct-3s3 (P2): Spinors/NP/GHP — **skip for now** (2-3 months scope, needs spinor index type)

## Critical Files

1. `src/julia/XTensor.jl:1693–1821` — `perturb()` implementation with Leibniz rule
2. `src/julia/XTensor.jl:1548–1566` — Metric self-trace fix in `_contract_one_metric`
3. `src/julia/XTensor.jl:1834–1855` — `Simplify()` function
4. `src/julia/XTensor.jl:194–198` — `FermionicQ` predicate
5. `src/julia/XTensor.jl:282–291` — `_parse_symmetry` regex (now includes `GradedSymmetric`)
6. `src/julia/XPerm.jl:1004` — `canonicalize_slots` GradedSymmetric → Antisymmetric dispatch
7. `src/sxact/adapter/julia_stub.py:117–134` — `_XTENSOR_ACTIONS` and `_DEFERRED_ACTIONS`
8. `src/sxact/adapter/julia_stub.py:67–83` — `_parse_symmetry` (GradedSymmetric → "Antisymmetric" for Tier 3)

## Recent Changes

- `src/julia/XTensor.jl` — perturb(), GradedSymmetric, FermionicQ, Simplify, self-trace fix
- `src/julia/XPerm.jl` — GradedSymmetric dispatch in canonicalize_slots, docstring
- `src/julia/tests/test_xtensor.jl` — GradedSymmetric testset (91 tests total, was 43)
- `src/sxact/adapter/julia_stub.py` — Perturb, Simplify actions; GradedSymmetric in _parse_symmetry
- `tests/xtensor/xpert_perturb.toml` — new (5 tests)
- `tests/xtensor/fieldsX_graded.toml` — new (6 tests)
- `tests/xtensor/simplify.toml` — new (3 tests)
- `tests/xtensor/contraction.toml` — removed skip from `metric_trace_is_dimension`
- `oracle/xtensor/xpert_perturb/` — 5 oracle snapshots
- `oracle/xtensor/fields_graded/` — 6 oracle snapshots
- `oracle/xtensor/simplify/` — 3 oracle snapshots
- `oracle/xtensor/contraction/metric_trace_is_dimension.*` — 1 oracle snapshot

## Key Learnings

1. **`perturb()` takes bare tensor names only**
   — Index decorations like `Cng[-a,-b]` must be stripped before registry lookup.
   Implementation at `src/julia/XTensor.jl:1779`: `replace(raw, r"\[.*\]$" => "")`.
   The bare-catch in the Leibniz product loop must be `e isa ErrorException || rethrow(e)`.

2. **`GradedSymmetric` = `Antisymmetric` for canonicalization**
   — Grassmann-odd tensors T[a,b] = -T[b,a] under index swap. Both XPerm dispatch
   and Python `_parse_symmetry` map GradedSymmetric → Antisymmetric. `FermionicQ`
   checks `t.symmetry.type == :GradedSymmetric` in `_tensors`.

3. **`Simplify` = `ToCanonical` — metric-trace reduction lives in `Contract`**
   — `g^{ab}g_{ab}` is reduced to `dim` by `_contract_one_metric` when it detects
   both factors are the same metric (`other_metric_obj.name == metric_obj.name`).
   Callers must call `Contract` before `Simplify` to get scalar evaluation.

4. **Oracle snapshot format for Assert-terminated tests**
   — Tests whose last operation is `Assert` produce `normalized_output = "True"` in
   their oracle snapshot, NOT the intermediate numeric result. The snapshot hash is:
   `sha256:{hashlib.sha256(json.dumps({"normalized_output":..., "properties":{}}, sort_keys=True).encode()).hexdigest()[:12]}`

5. **Pre-commit hook cycle**
   — `julia-format` reformats Julia files; `git add -u && git commit` again after failure.
   `mypy` requires explicit `frozenset[str]` annotation on class-level `frozenset()` literals.
   Always two commits needed when Julia files are new/changed.

6. **Snapshot generation when oracle_is_axiom = true**
   — No `xact-test snapshot` subcommand exists. Generate snapshots manually:
   compute hash via `uv run python -c "from sxact.snapshot.runner import compute_oracle_hash; print(compute_oracle_hash('VALUE', {}))"`,
   write `.json` and `.wl` files in `oracle/xtensor/<meta_id>/`.

## Open Questions

- [ ] sxAct-00d (Basis/Frame): What is the minimal API? WL xCoba uses `DefBasis`,
  `DefChart`, tetrad components `e^a_i`. Unclear if full coordinate chart is needed
  or just frame index bookkeeping.
- [ ] sxAct-hyy (h@n notation): How does `h@1` syntax translate to Julia? Likely
  `perturb(expr, 1)` plus index labeling convention. Needs design before coding.
- [ ] Should `Simplify` eventually call `Contract` internally, or keep the
  two-step caller responsibility? Current design documents the limitation.

## Next Steps

1. **Resume sxAct-00d: Basis/Frame support** [Priority: P2, NEXT]
   - Read xCoba paper (arXiv:0803.0862) for `DefBasis`/`DefChart` API
   - Minimal scope: register a "frame" (named basis), declare frame indices,
     allow `def_tensor!` with frame index type
   - Add `BasisQ`, `FrameQ` predicates; no full coordinate transform needed yet
   - TOML tests: `DefBasis`, `BasisQ`, frame index declaration

2. **sxAct-hyy: Perturbation Orders (h@n)** [Priority: P2]
   - Builds on sxAct-gys (perturb() now done)
   - h@n notation: `h@1` = first-order perturbation with indexing convention
   - Design: how does h@n map to `perturb(h, 1)` with index labels?

3. **Push to remote** — run `git push` at session start/end

## Artifacts

**New files:**
- `tests/xtensor/xpert_perturb.toml`
- `tests/xtensor/fieldsX_graded.toml`
- `tests/xtensor/simplify.toml`
- `oracle/xtensor/xpert_perturb/` (10 files: 5× .json + .wl)
- `oracle/xtensor/fields_graded/` (12 files: 6× .json + .wl)
- `oracle/xtensor/simplify/` (6 files: 3× .json + .wl)
- `oracle/xtensor/contraction/metric_trace_is_dimension.{json,wl}`

**Modified files:**
- `src/julia/XTensor.jl`
- `src/julia/XPerm.jl`
- `src/julia/tests/test_xtensor.jl`
- `src/sxact/adapter/julia_stub.py`
- `src/sxact/adapter/base.py`
- `src/sxact/runner/schemas/test-schema.json`
- `tests/schema/test-schema.json`
- `tests/xtensor/contraction.toml`

## References

- xAct FieldsX paper: arXiv:2008.12422 (Fröb 2020) — Grassmann-odd algebra
- xAct migration research: `research/XACT_MIGRATION_RESEARCH.md`
- Design spec: `specs/2026-03-06-xperm-xtensor-design.md`
- Previous handoff: `handoffs/2026-03-10_09-53-51_p1-milestones-complete.md`
