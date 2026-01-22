# xAct Oracle Quirks

This document captures quirks, edge cases, and gotchas discovered while working with xAct through the Oracle HTTP server.

## Critical Issue: Symbol Context Pollution

### The Problem

When using wolframclient to evaluate expressions, **symbols are parsed in `Global`` context before xAct sees them**. This causes:

1. Tensors like `S[-a,-b]` become `Global`S[Times[-1, Global`a], ...]` instead of xAct tensor expressions
2. `ToCanonical` and other xAct functions don't recognize the expressions as tensors
3. Curvature tensors like `RiemannCD` are created in `Global`` context and not treated as proper xAct curvatures

### Evidence

```mathematica
(* After DefManifold[MZ, 4, {aZ,bZ,cZ,dZ}] and DefMetric[-1, gZ[-aZ,-bZ], CDZ] *)

Context[RiemannCDZ]       (* → "Global`" — wrong! Should be in xAct context *)
TensorQ[RiemannCDZ]       (* → False — not recognized as a tensor *)
MetricQ[gZ]               (* → True — this works *)
ManifoldQ[MZ]             (* → True — this works *)

(* Bianchi identity fails because RiemannCDZ isn't a proper xAct tensor *)
RiemannCDZ[-aZ,-bZ,-cZ,-dZ] + RiemannCDZ[-aZ,-cZ,-dZ,-bZ] + RiemannCDZ[-aZ,-dZ,-bZ,-cZ] // ToCanonical
(* → Returns unsimplified Plus[...] instead of 0 *)
```

### Root Cause

The wolframclient library parses Mathematica expressions in Python before sending them to the kernel. During parsing, any unqualified symbol like `RiemannCDZ` gets created in `Global`` context. Even though xAct's `DefMetric` creates curvature tensors, the symbol `RiemannCDZ` already exists in `Global`` by the time the expression is evaluated.

### Potential Solutions

1. **Per-test context isolation** (recommended by Oracle):
   - Wrap each evaluation in `Block[{$Context = "test$uuid`", $ContextPath = ...}, expr]`
   - Each test gets its own namespace
   - Requires passing context ID through API

2. **Use ToExpression with explicit context**:
   - Send expressions as strings and use `ToExpression[expr, InputForm, Hold]`
   - Evaluate in proper xAct context

3. **Pre-declare all symbols in xAct context before use**:
   - Before each test, explicitly declare symbols in xAct context
   - E.g., `Begin["xAct`xTensor`"]; symbols...; End[]`

4. **Kernel restart between tests**:
   - Slow but guaranteed clean
   - Loses xAct load time benefit (~2-3s per restart)

### Current Workaround

Use **unique symbol names per test** (M1, M2, M3, etc.) to avoid conflicts between tests. This works for simple cases but doesn't solve the context pollution issue.

## Loading & Initialization

### xAct Load Time

- Loading xAct (`Needs["xAct`xTensor`"]`) takes **~2-3 seconds** on first call (persistent kernel)
- xAct is loaded once and reused across all `/evaluate-with-init` calls
- Subsequent calls complete in **~5-10ms** (kernel already initialized)
- Mark integration tests with `@pytest.mark.slow` to skip during normal development

### Index Naming

- xAct requires indices to be defined with the manifold: `DefManifold[M, 4, {a,b,c,d}]`
- Using undefined indices causes cryptic errors
- Indices are case-sensitive
- **Do NOT use `N` as a manifold name** — it's Mathematica's built-in numeric conversion function

### Reserved Names to Avoid

- `N` — Mathematica's numeric conversion
- `I` — imaginary unit
- `E` — Euler's number
- `C` — used for constants in solutions
- `D` — derivative operator
- `O` — big-O notation

## Output Format

### Unicode Characters

- xAct may output Greek letters as Unicode: `μ`, `ν` instead of `\[Mu]`, `\[Nu]`
- Normalization pipeline should handle both forms
- Example: `T[-μ,-ν]` and `T[-\[Mu],-\[Nu]]` should normalize identically

### Dummy Index Naming

- xAct generates internal dummy indices like `$1234` 
- These may appear in output even for simple expressions
- Normalization must canonicalize these to `$1, $2, ...`

### FullForm vs InputForm

- wolframclient returns expressions in Python object form, converted via `str()`
- This produces FullForm-like output: `Times[-1, a]` instead of `-a`
- Comparisons must account for these format differences

## Tensor Operations

### DefTensor Syntax

```mathematica
(* Correct: indices with positions *)
DefTensor[T[-a,-b], M, Symmetric[{-a,-b}]]

(* Wrong: missing index positions *)
DefTensor[T[a,b], M, Symmetric[{a,b}]]  (* May silently fail *)
```

### ToCanonical Behavior

- `ToCanonical` returns the canonical form but may not simplify to zero
- For testing equality, use `ToCanonical[expr1 - expr2]` and check for `0`
- Sometimes `Simplify` is needed after `ToCanonical`
- **ToCanonical only works if tensors are properly registered with xAct** (see Context Pollution issue)

### Metric Contraction

- Use `ContractMetric` explicitly; it's not automatic
- Order matters: `g[a,b] V[-b] // ContractMetric` ≠ `ContractMetric[g[a,b]] V[-b]`

### DefMetric Functions

- `SignDetOfMetric[g]` — returns the sign of the metric determinant (-1 for Lorentzian)
- `SignatureOfMetric[g]` — throws `Hold[Throw[None]]` in some cases (may require explicit signature spec)
- Use `SignDetOfMetric` for testing metric properties

## Comparator Implications

### Tier 1: Normalized Comparison

- Most xAct outputs differ only in dummy index naming
- Proper normalization catches ~80% of equality cases
- **Currently broken due to context pollution** — tensors aren't recognized

### Tier 2: Symbolic Simplify

- `Simplify[(expr1) - (expr2)]` works for most algebraic expressions
- May timeout for complex tensor expressions
- xAct-specific simplification rules require xAct context
- **Currently broken due to context pollution**

### Tier 3: Numeric Sampling

- Tensor expressions with free indices cannot be directly sampled
- Need to substitute concrete index values or use trace operations
- Fallback for expressions Simplify cannot handle
- Works for scalar expressions (Sin[x]^2 + Cos[x]^2 == 1)

## Known Issues

### Session State

- The Oracle uses a **persistent Wolfram kernel** via WSTP (wolframclient)
- Tensor definitions persist across API calls within the same kernel session
- The kernel restarts automatically on timeout or error (xAct is reloaded)
- **Symbol pollution**: once a symbol is created in `Global``, it stays there

### Error Messages

- xAct errors are often unhelpful: `"Syntax error"`
- `Hold[Throw[None]]` indicates an internal xAct exception was caught
- Check that all indices are defined before use
- Verify manifold dimensions match tensor rank

### Tests That Currently Pass (8/11)

1. ✅ TestDefineManifold::test_define_manifold_returns_manifold_info
2. ✅ TestDefineManifold::test_manifold_dimension
3. ✅ TestDefineMetric::test_define_metric_with_signature (after fixing to use SignDetOfMetric)
4. ✅ TestSymmetricTensor::test_symmetric_tensor_swap_indices
5. ✅ TestToCanonical::test_tocanonical_reorders_indices
6. ✅ TestMetricContraction::test_metric_contraction_raises_index
7. ✅ TestRiemannTensor::test_riemann_exists_after_metric_definition
8. ✅ TestNumericSampling::test_numeric_evaluation_of_scalar_expression

### Tests That Currently Fail (3/11)

1. ❌ TestSymbolicEquality::test_symmetric_tensor_sum_equals_double — context pollution
2. ❌ TestAntisymmetricTensor::test_antisymmetric_tensor_swap_negates — context pollution  
3. ❌ TestBianchiIdentity::test_riemann_first_bianchi_structure — context pollution

## Performance Tips

1. Batch related operations into single expressions
2. Use simpler test manifolds (dim 2-3) for unit tests
3. Skip slow tests during development: `pytest -m "not slow"`
4. The Oracle uses a persistent kernel - xAct loads once (~2s) and stays loaded
5. Use unique symbol names per test to avoid protection errors

## Next Steps to Fix Context Pollution

The recommended approach is to implement **per-test context isolation**:

1. Add `context_id` parameter to `/evaluate-with-init` endpoint
2. Server wraps evaluation in `Block[{$Context = ctx, $ContextPath = ...}, expr]`
3. Pytest fixture generates unique context ID per test
4. All evaluations within a test use the same context ID

This allows:
- Multi-call tests (setup + lhs + rhs evaluations) to share state
- Complete isolation between tests
- No kernel restarts needed
- xAct symbols properly scoped
