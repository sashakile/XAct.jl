# xAct Oracle Quirks

This document captures quirks, edge cases, and gotchas discovered while working with xAct through the Oracle HTTP server.

## Loading & Initialization

### xAct Load Time

- Loading xAct (`Needs["xAct\`xTensor\`"]`) takes **~2-3 seconds** on first call (persistent kernel)
- xAct is loaded once and reused across all `/evaluate-with-init` calls
- Subsequent calls complete in **~5-10ms** (kernel already initialized)
- Mark integration tests with `@pytest.mark.slow` to skip during normal development

### Index Naming

- xAct requires indices to be defined with the manifold: `DefManifold[M, 4, {a,b,c,d}]`
- Using undefined indices causes cryptic errors
- Indices are case-sensitive

## Output Format

### Unicode Characters

- xAct may output Greek letters as Unicode: `μ`, `ν` instead of `\[Mu]`, `\[Nu]`
- Normalization pipeline should handle both forms
- Example: `T[-μ,-ν]` and `T[-\[Mu],-\[Nu]]` should normalize identically

### Dummy Index Naming

- xAct generates internal dummy indices like `$1234` 
- These may appear in output even for simple expressions
- Normalization must canonicalize these to `$1, $2, ...`

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

### Metric Contraction

- Use `ContractMetric` explicitly; it's not automatic
- Order matters: `g[a,b] V[-b] // ContractMetric` ≠ `ContractMetric[g[a,b]] V[-b]`

## Comparator Implications

### Tier 1: Normalized Comparison

- Most xAct outputs differ only in dummy index naming
- Proper normalization catches ~80% of equality cases

### Tier 2: Symbolic Simplify

- `Simplify[(expr1) - (expr2)]` works for most algebraic expressions
- May timeout for complex tensor expressions
- xAct-specific simplification rules require xAct context

### Tier 3: Numeric Sampling

- Tensor expressions with free indices cannot be directly sampled
- Need to substitute concrete index values or use trace operations
- Fallback for expressions Simplify cannot handle

## Known Issues

### Session State

- The Oracle uses a **persistent Wolfram kernel** via WSTP (wolframclient)
- Tensor definitions persist across API calls within the same kernel session
- The kernel restarts automatically on timeout or error (xAct is reloaded)
- For test isolation, combine all setup in one expression to avoid conflicts with previous state

### Error Messages

- xAct errors are often unhelpful: `"Syntax error"`
- Check that all indices are defined before use
- Verify manifold dimensions match tensor rank

## Performance Tips

1. Batch related operations into single expressions
2. Use simpler test manifolds (dim 2-3) for unit tests
3. Skip slow tests during development: `pytest -m "not slow"`
4. The Oracle uses a persistent kernel - xAct loads once (~2s) and stays loaded
