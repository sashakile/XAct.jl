# Python Public API (xact-py) Design

**Date:** 2026-03-26
**Status:** Implemented
**Location:** `packages/xact-py/src/xact/api.py`

---

## 1. Purpose

Provide a Pythonic interface to the Julia xAct.jl engine with **zero juliacall exposure**.
Users interact with Python classes and functions; all Julia internals (Symbol conversion,
Vector wrapping, juliacall imports) are hidden.

## 2. Handle Types

```python
class Manifold:
    """Wraps def_manifold!. Validates dim >= 1, >= 2 index labels."""

class Metric:
    """Wraps def_metric!. Auto-creates Riemann/Ricci/RicciScalar/Einstein/Weyl/Christoffel."""

class Tensor:
    """Wraps def_tensor!. Accepts symmetry as string (e.g. 'Symmetric[{-a,-b}]')."""

class Perturbation:
    """Wraps def_perturbation!. Links a perturbation tensor to its background."""
```

These are lightweight handles — they hold metadata (name, dim, indices) but do **not**
store Julia objects. All Julia calls go through the lazy bridge.

## 3. Expression Functions

All accept and return plain strings. Support TExpr round-trip.

| Function | Julia Equivalent |
|----------|-----------------|
| `canonicalize(expr)` | `ToCanonical` |
| `contract(expr)` | `Contract` |
| `simplify(expr)` | `Simplify` |
| `commute_covds(expr)` | `CommuteCovDs` |
| `sort_covds(expr)` | `SortCovDs` |
| `riemann_simplify(expr)` | `RiemannSimplify` |
| `collect_tensors(expr)` | `CollectTensors` |
| `all_contractions(expr, metric)` | `AllContractions` |
| `symmetry_of(expr)` | `SymmetryOf` |
| `make_trace_free(expr, metric)` | `MakeTraceFree` |
| `check_metric_consistency(metric)` | `CheckMetricConsistency` |
| `perturb(expr, order)` | `Perturb` |
| `perturb_curvature(metric, order)` | `PerturbCurvature` |
| `perturbation_order(tensor)` | `PerturbationOrder` |
| `perturbation_at_order(bg, order)` | `PerturbationAtOrder` |

## 4. Initialization Pattern

```python
_lock = threading.Lock()
_xAct = None

def _ensure_init():
    """Lazy, thread-safe Julia initialization. Called once on first use."""
```

Julia is loaded only when the first xact function is called, not at import time.
This avoids startup cost for users who only import the package for type checking.

## 5. CTensor Conversion

`_jl_to_list()` converts Julia arrays to Python lists using pure Python (no numpy
dependency). An optional fast path uses numpy when available.

## 6. Design Decisions

- **Lazy init**: Julia loaded on first use, not import time.
- **Thread-safe**: Global lock protects the singleton Julia bridge.
- **String-based**: Expressions are plain strings, not AST objects (TExpr wraps this).
- **No Julia leakage**: Users never see `juliacall`, `Symbol`, or `JuliaValue`.
- **Validation at boundary**: Inputs validated in Python before crossing to Julia.

## 7. Test Coverage

909 Python tests pass, covering all handle types and expression functions.
