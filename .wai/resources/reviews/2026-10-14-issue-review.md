# Issue tracker review — 2026-10-14

System: Beads. Base commit: `02c8cd970b2568fb045c8936cd858ab49822f5d3`.
Scope: 16 tickets — the seven findings from the repository evaluation, six related gap/decision tickets named in the follow-up, and three related duplicate/hosting tickets. The closed evaluation parent `sxAct-eifm` and regression-seed prerequisite `sxAct-ls80` were inspected as context, not counted as reviewed work items.
Source: `.wai/resources/reviews/2026-10-07-repository-evaluation.md`, issue bodies/acceptance fields/dependencies, current source, and `openspec/changes/add-cross-adapter-benchmark-suite/`.
Follow-up: `sxAct-8hof` tracks the readiness corrections. The 16 reviewed tickets were not edited during this review.

**Verdict: NEEDS_UPDATES.** The seven bug reproductions are useful, and most individual fixes are good behavioral slices. The issue set is not ready for unrestricted autonomous execution: duplicates disagree on APIs and verification, decision work is exposed as AFK, prerequisites are missing, and execution metadata is incomplete. Session isolation and normalization need narrower slices or explicit semantics before implementation.

Summary: **0 CRITICAL, 10 HIGH, 22 MEDIUM, 1 LOW** findings. Sixteen MEDIUM findings are per-ticket metadata omissions; the remaining 17 are content/dependency findings. Counts measure issue quality, not additional production bugs. Five content passes completed; convergence was not reached.

| Assessment | Rating |
|---|---|
| Slice quality | Good for the seven concrete bugs; Fair across the full set |
| Horizontal-ticket leakage | Low in the bug tickets; Moderate in benchmark task structure |
| AFK/HITL clarity | Poor |
| Clarity | Fair |
| Scope | Fair |
| Dependencies | Fair |
| Completeness | Poor for autonomous handoff |

## Pass 0 — mechanical pre-flight

`bd dep cycles --json` returned `[]`. The dependency graph and ready queue were inspected. The current source revision is the same as at the end of the original evaluation; this review does not claim new runtime verification.

Each row below is one **PRE-001 / MEDIUM** finding. `files` lists are absent on 14/16 tickets; `base_commit` is absent on 16/16. The two tickets with file metadata still require the anchor. Missing anchors mean the stale-touched / behind-head checks cannot run; do not label these tickets stale merely because they lack an anchor.

| Ticket | Missing metadata |
|---|---|
| sxAct-8jt0 | files, base_commit |
| sxAct-qbgk | files, base_commit |
| sxAct-1ord | files, base_commit |
| sxAct-vjc8 | files, base_commit |
| sxAct-vv9i | files, base_commit |
| sxAct-93jp | files, base_commit |
| sxAct-umyc | files, base_commit |
| sxAct-0s1h | files, base_commit |
| sxAct-m9vc | files, base_commit |
| sxAct-37ou | base_commit |
| sxAct-q3vr | base_commit |
| sxAct-a7cu | files, base_commit |
| sxAct-w9b2 | files, base_commit |
| sxAct-vgnm | files, base_commit |
| sxAct-vq14 | files, base_commit |
| sxAct-0fjj | files, base_commit |

The metadata-only shared-file check found no file assigned to three tickets. That result is incomplete because most file lists are missing; the content-level overlap is recorded below.

## Pass 1 — completeness and clarity

**CLRT-001 / HIGH — sxAct-0s1h, sxAct-vgnm.** Both identify `src/XInvar/InvarDB.jl`, which does not exist. Actual database loading is in `src/InvarDB.jl:567`; default lookup is in `src/XInvar.jl:2102`. The vgnm success example supplies only one argument to `RiemannSimplify`, whereas its current method at `src/XInvar.jl:1990` requires expression and metric, with declared geometry needed for a meaningful invariant. Replace the path and give a complete setup → first-use download → independently expected invariant example. Root-level `STRESS_FINDINGS.md` and `REVIEW.md` are also absent; use the checked-in evaluation as the portable source reference.

**CLRT-002 / HIGH — sxAct-m9vc, sxAct-0fjj.** The numeric-curvature tickets specify incompatible interfaces: output buffers and explicit Christoffel derivatives versus `riemann!(M,g)` and CTensor storage. Single-point metric values alone do not supply the needed derivatives. m9vc also names nonexistent `src/XCoba/Coba.jl`; the actual path is `src/XTensor/Coba.jl`. Define one API, index/sign convention, derivative-input layout and result representation. Correct 0fjj's parenthetical `Ricci = (1/2) g`: its own unit-sphere target is `Ricci = g`, scalar curvature 2, hence Einstein tensor zero. Add a nonzero Einstein target to avoid an all-zero implementation passing that part.

**CLRT-003 / MEDIUM — sxAct-q3vr.** Its scope says to wait for the version-ownership decision, but its “Blocked by” section says “None - can start immediately.” The actual graph correctly blocks it on sxAct-37ou. Replace the contradictory text and specify equality within the version groups chosen by the decision, rather than unconditionally making independently released distributions equal.

## Pass 2 — scope and tracer-bullet shape

**SCOPE-001 / HIGH — sxAct-0s1h ↔ sxAct-vgnm; sxAct-m9vc ↔ sxAct-0fjj.** Two duplicate implementation pairs describe the same user outcomes with differing priorities, APIs and tests. Choose a canonical issue for each outcome, merge useful acceptance criteria, transfer dependencies, then close the duplicates with explicit cross-references. Do not split curvature into separate Riemann-only, Ricci-only and Einstein-only layer tickets: a small metric-to-observable-curvature workflow is a better slice.

**SCOPE-002 / HIGH — sxAct-a7cu.** One ticket covers three core operations, approximately 115 internal call sites, derivative sorting/commutation, IBP/VarD, and a new Python session interface. This is too broad for one focused change. Make the parent a coordination item and define independently demonstrated slices: explicit Julia sessions for canonicalization/contraction/simplification, session-aware derivative/variational workflows, and Python session access. Every slice must prove that interleaving two differently configured sessions does not leak state; a Session-struct-only slice has no sufficient user value. Keep representation refactoring separate.

**SCOPE-003 / HIGH — sxAct-qbgk.** The ticket combines the concrete True/False bug with scalar/function argument identity, dummy scope, free-index equivalence and snapshot re-evaluation. The current AST contains generic leaves/nodes, not enough type information to infer arbitrary tensor arguments. Define the equivalence contract and required context before claiming general alpha-renaming. A small first slice can preserve Boolean/scalar identity through the comparator with a conservative fallback; typed dummy normalization and affected snapshot validation can follow under an explicit contract. Preserve the end-to-end comparison test in each slice.

**SCOPE-004 / MEDIUM — sxAct-vjc8.** “Account for density weights or reject unsupported ones” and “preserve raw change_basis ... if intended” leave observable behavior undecided. Define the first slice for ordinary weight-zero tensors and specify the unsupported-weight behavior; preserve the existing low-level matrix operation unless a separately approved public contract changes it. Record the forward-matrix convention and its dual transform before coding.

**SCOPE-005 / LOW — sxAct-1ord, sxAct-vjc8, sxAct-93jp, sxAct-m9vc, sxAct-0fjj.** All touch `src/XTensor/Coba.jl`; several share `test/julia/xtensor/test_core.jl`. Add co-modification notes and refresh against landed changes. Shared files alone do not justify a new architectural split or artificial blocking chain; these fixes have distinct observable outcomes.

Convergence after pass 2: new CRITICAL 0; new findings 5; previous-pass findings 3; estimated false-positive rate 10% (reviewer estimate, not measured). **ITERATE**.

## Pass 3 — dependencies and ordering

**DEP-001 / HIGH — sxAct-0s1h.** Its body says hosting is blocking, but it has no blocking dependency and appears in `bd ready`. The duplicate sxAct-vgnm correctly depends on the existing decision sxAct-vq14. Transfer that edge to the chosen canonical implementation ticket; do not create a second hosting-decision ticket.

**DEP-002 / HIGH — sxAct-umyc.** The title requires engine-derived curvature, but the body alternatively permits narrowing documentation until curvature exists. The graph only has a nonblocking discovered-from link, so it is ready despite the missing engine prerequisite. Choose one close condition: an immediately executable honesty correction, or a complete engine-backed regression blocked by the canonical numeric-curvature ticket. Keep the deferred outcome tracked if choosing the former.

Positive checks: sxAct-q3vr → sxAct-37ou and sxAct-vgnm → sxAct-vq14 are correctly represented; sxAct-m9vc's regression-seed prerequisite sxAct-ls80 is closed. Discovered-from links to the completed evaluation are provenance, not implementation blockers. Do not serialize all mathematical fixes behind the CI-gate fix merely because it is the first recommended priority.

Convergence after pass 3: new CRITICAL 0; new findings 2; previous-pass findings 5; estimated false-positive rate 10%. **ITERATE**.

## Pass 4 — plan and value alignment

**ALIGN-001 / HIGH — sxAct-vgnm.** It permits `@test_skip` when the artifact is unavailable, while its whole value proposition is reliable delivery to a fresh install. A required first-use delivery check cannot pass by skipping the download. Use deterministic local artifact tests for ordinary CI and a separately identified release/distribution gate that verifies the real artifact, checksum and known invariant without silent skips. State exactly which gate is mandatory for closure. Reconcile with sxAct-0s1h's stronger CI requirement.

**ALIGN-002 / MEDIUM — sxAct-m9vc.** Acceptance says existing F2 `@test_broken` markers will flip when the feature is implemented, but `test/julia/stress_test.jl:144` is unconditional `@test_broken false`. Require replacing the placeholder with a behavioral regression. The closed seed ticket does not prove this invariant already exists.

**ALIGN-003 / HIGH — sxAct-w9b2.** The issue is AFK/ready but says implementation requires proposal approval. The inspected project is still in design; neither the issue nor inspected project/proposal records supplies an approval reference. Record any existing approval or represent the unresolved gate explicitly. The 18 OpenSpec tasks group tests, runner, CLI, suite and validation horizontally; use a small end-to-end slice through existing TOML → runner → comparison output, then add independent scaling/stateful slices. Map each issue to exact OpenSpec task IDs. This finding does not assert that approval could not exist outside the inspected records.

The seven bugs correctly cite the checked-in evaluation and use discovered-from links. Their examples mostly define tests before implementation and say to tidy separately; retain those strengths.

Convergence after pass 4: new CRITICAL 0; new findings 3; previous-pass findings 2; estimated false-positive rate 10%. **ITERATE**.

## Pass 5 — executability and handoff

**EXEC-001 / HIGH — sxAct-37ou, sxAct-vq14, sxAct-q3vr.** The first two are human decisions exposed as AFK/ready: 37ou has both `afk` and `hitl`; vq14 has `afk` despite being explicitly HITL. q3vr also has both lanes. Keep decisions HITL, and make implementation AFK only once the contract is recorded while retaining the blocker until then. q3vr's public packaging/compatibility contract also warrants L rather than M under this skill's complexity rule. Complexity is scope/risk, not merely edited line count.

**EXEC-002 / MEDIUM — all seven new bug tickets.** They have neither lane nor complexity labels. I omitted these when filing them. Suggested classification after the scope fixes: 8jt0 AFK/M; 1ord and 93jp AFK/L; vv9i AFK/L; qbgk DESIGN/L until equivalence semantics are fixed; vjc8 DESIGN/L until variance/density boundaries are fixed; umyc depends on the chosen documentation-versus-curvature outcome. Do not mark a still-ambiguous design AFK merely by adding a test command.

**EXEC-003 / MEDIUM — all seven new bugs, plus sxAct-a7cu and sxAct-w9b2.** Descriptions give test ideas but lack copyable Meter commands, named regression coverage and explicit gate-preservation anti-goals. The words “pytest” and “Pkg.test CI” are not runnable commands. Retain exact numerical expectations and add commands that run the new regression and existing affected suite. For test/CI/normalization changes, prohibit satisfying the gate by skipping cases, weakening assertions, replacing oracle snapshots with target output, or returning universal zero/equality. Approval metadata on benchmark work must distinguish licensed manual validation from routine CI.

**EXEC-004 / MEDIUM — sxAct-m9vc, sxAct-q3vr, sxAct-0fjj, sxAct-a7cu.** These create tests or reshape source responsibilities but have no file-header acceptance criterion. Require Purpose/Responsibilities/Rationale headers on new source/test files and update headers where responsibilities change. Do not turn each narrow bug fix into a repository-wide header migration; config, lockfiles and documentation are excluded.

Convergence after pass 5: new CRITICAL 0; new findings 4; previous-pass findings 3; estimated false-positive rate 10%. **ITERATE / five-pass limit reached**. This report does not claim convergence.

## Concrete proposed tracker edits

These are recommendations, not applied ticket changes. Preserve unrelated labels and metadata. Choose canonical duplicate tickets before applying dependency changes; the commands below assume keeping sxAct-0s1h and sxAct-m9vc.

```sh
bd dep add sxAct-0s1h sxAct-vq14 --json
bd update sxAct-37ou --remove-label afk --add-label hitl --json
bd update sxAct-vq14 --remove-label afk --add-label hitl --json
bd update sxAct-q3vr --remove-label hitl --remove-label complexity:m --add-label complexity:l --json
bd update sxAct-8jt0 --add-label afk --add-label complexity:m --set-metadata 'files=[".github/workflows/test.yml"]' --set-metadata base_commit=02c8cd970b2568fb045c8936cd858ab49822f5d3 --json
```

The q3vr command preserves its existing AFK label and actual blocker; revise its contradictory body and record the release decision before treating it as schedulable. The 8jt0 file list must also include any gate helper/test files chosen during implementation. Use `--set-metadata` to update individual keys without replacing unrelated metadata. Revalidate before using the recorded base after future code changes.

For sxAct-umyc, add `bd dep add sxAct-umyc sxAct-m9vc --json` only if it retains the full engine-curvature completion condition. An immediate documentation correction should not inherit an unnecessary numerical-engine blocker.

Examples of acceptance additions:

- **8jt0:** all defined failing/error/malformed/missing-report fixtures produce nonzero gate exit status; a complete passing report produces zero; the explicitly supported post-test exit-139 case is covered. Test the same gate implementation invoked by CI. No broader ignoring of pytest failures.
- **1ord:** for `T=[1 2;3 4]`, the antisymmetrized components are exactly `[0 -1;1 0]`; incompatible free-index sets fail explicitly; existing component tests pass.
- **vjc8:** `V=W=[1,1]` pairing remains 2 under `diag(2,3)` to tolerance `1e-12`; include a nonsymmetric invertible matrix and the reverse transform, not only diagonal/orthogonal cases.
- **93jp:** crossed `reshape(1.0:16.0,2,2,2,2)` trace equals 34; adjacent/nested cases and existing component tests pass.
- **vv9i:** all four named suites appear in required execution; separately injecting one failure into each makes the job fail; no new blanket skips or relaxed assertions.

Existing-suite Meter starting points, to pair with each new focused regression and normal environment setup:

```sh
julia --project=. test/julia/test_xtensor.jl
uv run --frozen pytest tests/normalize/test_pipeline.py tests/unit/test_comparison_layers.py -q
uv run --frozen pytest tests/unit/test_runtime_init.py -q
julia --project=. -e 'using Pkg; Pkg.test()'
openspec validate add-cross-adapter-benchmark-suite --strict
```

These commands are proposed verification entry points, not newly executed test results. New test-file paths must be named when the tickets are rewritten, and the expected pre-fix failure must exercise the actual defect. A passing old suite alone cannot close a bug. The remaining implementation details and lane decisions belong in beads, not an independent Markdown task list.
