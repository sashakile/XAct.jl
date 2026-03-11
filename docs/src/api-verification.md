# Verification API (sxact-py)

The `sxact` Python package is a specialized framework for verifying the mathematical correctness of `xAct.jl` against the Wolfram Language implementation.

## 1. Oracle Client

The `OracleClient` manages the connection to the Dockerized Wolfram Engine.

### OracleClient
`sxact.oracle.client.OracleClient(base_url="http://localhost:8765")`

- `health()`: Check if the server and Wolfram kernel are alive.
- `evaluate(expr)`: Send a plain Wolfram expression.
- `evaluate_with_xact(expr, context_id=None)`: Evaluate with xAct pre-loaded and optional context isolation.
- `evaluate_result(expr)`: Return a structured `Result` object.

## 2. Normalization Pipeline

Canonicalizes xAct output strings to ensure they can be compared regardless of dummy index naming or whitespace.

### normalize
`sxact.normalize.pipeline.normalize(expr)`

Applies:
1. Whitespace normalization.
2. Coefficient normalization (e.g., `2*x` -> `2 x`).
3. Dummy index canonicalization (`a, b` -> `$1, $2`).
4. Term ordering (lexicographic sort for sums).

## 3. Comparison Engine

Implements a multi-tier comparison strategy.

### compare
`sxact.compare.comparator.compare(lhs, rhs, oracle=None, mode=EqualityMode.FULL)`

- **Tier 1**: Normalized string equality (No oracle required).
- **Tier 2**: Symbolic difference check (`Simplify[lhs - rhs] == 0`) using the Wolfram Oracle.
- **Tier 3**: Numeric sampling (Probabilistic verification) for identities.

## 4. Property Testing

Tools for running property-based tests (e.g., verifying `R[a,b,c,d] == -R[b,a,c,d]` across random manifolds).

### sample_numeric
`sxact.compare.sampling.sample_numeric(expr, seed=42)`

Evaluates a symbolic expression at random numeric points to check for zero.
