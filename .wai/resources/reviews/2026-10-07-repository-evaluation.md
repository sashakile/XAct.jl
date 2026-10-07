# Repository value and implementation evaluation — 2026-10-07

Reviewed source revision: `f5fd1a87da9d88977043cd4d169a034130c9808d`.
Review issue: `sxAct-eifm`. This is an advisory evaluation; production code was not changed.

The repository offers a useful proposition: an accessible Julia tensor algebra engine, a Python interface, and an xAct-specific verification framework. There is substantial working implementation behind that proposition. However, the current evidence supports an experimental tool for independently checked calculations, not broad mathematical parity or dependable replacement of the Wolfram suite. The immediate priority should be correctness and the reliability of verification before additional modules or a major representation refactor.

The strongest current value is abstract tensor manipulation accessible from Julia and Python, with reusable oracle snapshots. Native Julia integration is an architectural benefit; superior performance is not established by this review. Existing same-adapter benchmark baselines measure regressions, not a competitive advantage against Wolfram or other systems. The cross-adapter benchmark proposal remains at 0/18 tasks.

## Implementation status

| Area | Evidence and assessment |
|---|---|
| XCore / XPerm | Real symbol and permutation infrastructure. All 156 assertions in the selected XPerm suite passed. The existing Young-symmetry issue `sxAct-l36k` remains in progress; this review does not establish general canonicalization correctness. |
| XTensor | Substantial definitions, canonicalization, contraction, derivatives, perturbation and utility implementations. Selected XTensor suites passed 616 assertions. String parsing remains the engine boundary, and session isolation is incomplete. |
| Typed expressions | Useful validated construction and typed results. Standalone suite passed 238 assertions. `src/TExpr.jl:955` serializes typed expressions into the string engine. These tests are absent from the standard Julia test entry point. |
| xCoba | Components, charts, basis changes and Christoffel computation exist. Three independent component-calculus defects were reproduced below. Numeric Riemann/Ricci/Einstein computation is still tracked as missing. Calling the whole module “ported” obscures these limits. |
| XInvar | Substantial engine and database parser. Default loading requires `resources/xAct/Invar` (`src/XInvar.jl:2102`), which has no tracked files or lazy artifact in this checkout. Real-database tests are conditional (`test/julia/test_xinvar.jl:2360`). Complete implementation phases do not imply out-of-box usability or full CI coverage. |
| Python wrapper | Public API and Julia bridge exist. `packages/xact-py/pyproject.toml:3` declares 0.8.0, while `packages/xact-py/src/xact/juliapkg.json:6` requests Julia XAct 0.7.1. This warrants the existing version-policy work; do not assume checkout tests prove the released install path. |
| Verification | Adapters, snapshots, normalization, comparison and benchmark infrastructure are substantial. The false-positive normalizer and ineffective Python CI gate undermine the strength of parity claims. Selected Python suites passed 377 tests. |
| Remaining upstream breadth | README already acknowledges partial xPert/xTras and absent Spinors, exterior calculus, harmonics and rich typesetting. These are capability gaps, not newly discovered implementation bugs. |

`README.md:74` describes the project as early adopter software and reports only author use. This is candid positioning. Its broader parity wording and `docs/src/status.md:3` “All core xAct modules ported” summary should be qualified by actual supported workflows, required assets, and independent verification. Test assertion counts are not a feature-parity denominator.

## Prioritized findings

### 1. P1 — Python CI can pass failed tests (`sxAct-8jt0`)

At `.github/workflows/test.yml:95`, pytest's exit status is discarded. Lines 98–100 read failure/error attributes from the XML root. Actual pytest JUnit XML uses a `<testsuites>` wrapper without those counts; counts reside on child `<testsuite>` elements.

A deliberately failing test produced a child with `failures="1"`, while the current gate calculated zero failures and zero errors. Ordinary assertion failures can therefore appear green. Aggregate child-suite counts and reject incomplete or empty reports; prove the gate rejects assertion failures and collection errors. Preserve any special teardown-crash handling only when a completed report establishes test success.

### 2. P1 — AST normalization declares unequal values equal (`sxAct-qbgk`)

`packages/sxact/src/sxact/normalize/passes.py:97` renames every alphabetic leaf as an index without checking its context. Reproductions:

```text
ast_normalize("True") == ast_normalize("False") == "$1"
ast_normalize("x") == ast_normalize("y") == "$1"
ast_normalize("f[x]") == ast_normalize("f[y]") == "f[$1]"
```

`compare_canonical` in `packages/sxact/src/sxact/elegua_bridge/comparison_layers.py:83` returns `TaskStatus.OK` for both True/False and x/y. This is an executable false positive in the sxact comparison layer, not an Elegua-core issue. The legacy normalizer also erases free-index ordering; comparisons of arbitrary tensors need a shared free-index correspondence.

Tests in `tests/normalize/test_pipeline.py:136` currently require a bare scalar-looking `x` to become `$1`, illustrating that some tests encode the problematic assumption. Restrict alpha-renaming to recognized dummy indices with valid scope; retain Boolean values, scalar names, function arguments and free-index identity. Add negative examples alongside positive renaming examples.

### 3. P1 — ToBasis loses free-index ordering across terms (`sxAct-1ord`)

`src/XTensor/Coba.jl:818` obtains each term's free labels, but lines 822–831 only compare counts and add arrays without permuting axes.

For a nonsymmetric matrix `T = [1 2; 3 4]`, `ToBasis("T[-a,-b] - T[-b,-a]", :C)` returns the zero matrix. Expected: `[0 -1; 1 0]`. This silently erases a nonzero antisymmetric tensor. Align every term to one common free-index order and reject incompatible free-index sets. Existing sum tests at `test/julia/xtensor/test_core.jl:1636` use matching index order and cannot detect this.

### 4. P1 — Basis changes ignore covariant/contravariant variance (`sxAct-vjc8`)

`src/XTensor/Coba.jl:314` applies the same forward matrix to every component slot. It does not consult the tensor's declared variance.

With vector `V=[1,1]`, covector `W=[1,1]`, and basis matrix `diag(2,3)`, their scalar pairing changes from 2 to 13. This violates invariance independently of any convention about which direction the basis matrix represents. Use mutually dual transforms for upper and lower slots; test nonorthogonal changes so transpose/inverse mistakes cannot hide. Existing raw matrix-transform tests do not establish tensor transformation correctness.

### 5. P1 — Four Julia suites are not run by standard CI (`sxAct-vv9i`)

`test/runtests.jl:784` includes the XPerm, XTensor, XInvar, docs and stress suites. Inspection of nested includes, workflows, scripts and justfile found no invocation of:

- `test/julia/test_texpr.jl`
- `test/julia/test_validation.jl`
- `test/julia/test_xtensor_fuzz.jl`
- `test/julia/test_xperm_properties.jl`

The standalone typed suite passes 238 assertions but does not protect the standard `Pkg.test()` job. Wire these into required execution, reconciling standalone module bootstrapping. A deliberately failing assertion in each suite should fail the required job. Do not count dormant test files as CI coverage.

### 6. P2 — Crossed rank-four traces throw (`sxAct-93jp`)

`src/XTensor/Coba.jl:944` remaps contracted axes using a single cumulative offset. With slots `[a,b,-c,-d]`, it chooses pairs `(1,3)` and `(2,4)`. After deleting the first pair, it computes `(0,2)` for the second pair.

`TraceBasisDummy` throws `arraysize: dimension out of range` for the reproduction below, where the expected scalar is 34. Track surviving original axes instead. The rank-four test at `test/julia/xtensor/test_core.jl:1753` only exercises adjacent pairs `(1,2),(3,4)`.

### 7. P2 — Two advertised textbook checks do not exercise the engine (`sxAct-umyc`)

At `test/julia/xtensor/test_textbook_gr_regressions.jl:77`, a locally defined Kretschmann formula is compared with the same formula. At line 83, a locally defined FLRW formula is evaluated without invoking XAct. Neither check can catch curvature-engine regressions.

The three Schwarzschild Christoffel checks above these lines do exercise the engine and are useful. Scope current claims accordingly; add independently targeted curvature checks when the missing numeric curvature path exists. Do not confuse evaluating a textbook formula with deriving it through the library.

## Existing gaps and tracking quality

Avoid duplicating the existing capability work:

- Invar asset delivery: `sxAct-0s1h`, `sxAct-vgnm`, and hosting decision `sxAct-vq14`.
- Numeric component curvature: `sxAct-m9vc` and `sxAct-0fjj`.
- Version ownership/metadata: `sxAct-37ou`, `sxAct-q3vr`.
- Session-aware core operations: in-progress `sxAct-a7cu`; `ToCanonical` and `Contract` still expose default-session operations in `src/XTensor/Canonical.jl:1380` and `src/XTensor/Contract.jl:18`.
- Independent properties and anti-zeroing: `sxAct-i2er`, `sxAct-8p82`, `sxAct-ew18`, `sxAct-96ry`.
- Cross-adapter benchmarking: `sxAct-w9b2`; OpenSpec 0/18 tasks.

Before this review, the tracker contained 79 open and 3 in-progress issues. Several duplicated capability tickets and stale descriptions reduce its usefulness as a completion measure. For example, the XTensor split ticket `sxAct-k8wd` and parser-overlap investigation `sxAct-vpgi` should be reconciled against the existing `src/XTensor/` split and parser proposal (18/24 tasks). This is a tracking observation, not a claim that all their acceptance criteria are complete.

The stress suite contains ten unconditional `@test_broken false` assertions (`test/julia/stress_test.jl`). These record known work but cannot automatically turn green when an implementation is fixed. Replace each placeholder with an executable behavioral expectation as its associated ticket is addressed.

## Validation performed and limits

Environment: Julia 1.12.5, existing Python 3.14 virtual environment. Julia used an isolated writable depot prefix with existing installed dependencies. No production fixes or edits to existing tests were made.

- XPerm, XTensor sub-suites and stress: **782 passed, 10 broken**. The broken results are existing unconditional placeholders.
- Standalone TExpr: **238 passed**.
- Python normalize, snapshot, compare, runner and translate suites: **377 passed, 7 skipped, 4 deselected**. Oracle/slow markers were excluded. One warning reported an unresolved `$res` reference in an Elegua isolation test.
- Independent counterexamples reproduced all three component defects, the AST comparator false positives and the Python CI gate false negative.
- An initial Python run lacked `.venv/bin` on PATH and had five CLI-not-found failures. Correcting PATH produced the passing result above; those were review-environment failures, not repository bugs.

This was a broad source review plus selected execution, not a full package release audit. Full `Pkg.test()` with Aqua/JET/formatting, the real Invar database suite, all Python runtime/integration tests, live Wolfram parity and clean published-package installation were not run. Registry availability, current external releases, and comparative market/performance claims were not verified. Existing local changes were left outside the review commit.

The review covered architecture, correctness, test assumptions, index-boundary cases and CI reliability. It found issues across these areas; this is not a claim of exhaustive convergence or mathematical certification.

## Reproduction snippets

Run this Julia snippet with `julia --project=.` from the repository. Observed outputs are described in findings 3, 4 and 6.

```julia
using XAct, LinearAlgebra
reset_state!()
def_manifold!(:M, 2, [:a,:b,:c,:d])
def_chart!(:C, :M, [1,2], [:x,:y])
def_tensor!(:T, ["-a","-b"], :M)
A = [1.0 2.0; 3.0 4.0]
set_components!(:T, A, [:C,:C])
@show ToBasis("T[-a,-b] - T[-b,-a]", :C).array A-transpose(A)

def_tensor!(:Q, ["a","b","-c","-d"], :M)
q = reshape(collect(1.0:16.0),2,2,2,2)
set_components!(:Q,q,[:C,:C,:C,:C])
@show sum(q[i,j,i,j] for i=1:2,j=1:2)
try
    @show TraceBasisDummy(:Q,[:C,:C,:C,:C]).array
catch e
    @show e
end

def_chart!(:D,:M,[1,2],[:u,:v])
set_basis_change!(:C,:D,[2.0 0.0; 0.0 3.0])
def_tensor!(:V,["a"],:M)
def_tensor!(:W,["-a"],:M)
set_components!(:V,[1.0,1.0],[:C])
set_components!(:W,[1.0,1.0],[:C])
@show dot(get_components(:V,[:C]).array,get_components(:W,[:C]).array)
@show dot(get_components(:V,[:D]).array,get_components(:W,[:D]).array)
```

Python comparison reproduction, using the installed workspace packages:

```python
from elegua.models import ValidationToken
from elegua.task import TaskStatus
from sxact.elegua_bridge.comparison_layers import compare_canonical
from sxact.normalize import ast_normalize

def token(s):
    return ValidationToken(adapter_id="review", status=TaskStatus.OK,
                           result={"repr": s, "type": "Expr"})

for a, b in [("True", "False"), ("x", "y"), ("f[x]", "f[y]")]:
    print(a, b, ast_normalize(a), ast_normalize(b),
          compare_canonical(token(a), token(b)))
```

For the CI reproduction, run a temporary pytest test containing `assert False` with `--junitxml=/tmp/failing.xml`. Inspect:

```python
import xml.etree.ElementTree as ET
root = ET.parse("/tmp/failing.xml").getroot()
print(root.tag, root.attrib)
print(int(root.get("errors", 0)) + int(root.get("failures", 0)))  # 0
print(root.find("testsuite").attrib)  # failures=1
```

## Recommended order of work

Repair the CI gate, activate dormant suites and make comparison reject unequal values first. Then fix the component-calculus defects using the independent counterexamples. Complete one real geometry workflow with independently known nonzero targets and negative tests, and deliver the Invar assets and coherent runtime versions. Reassess native-AST work against measured bottlenecks once the correctness baseline is trustworthy. These actions are tracked in beads; this report is evidence, not a second task tracker.
