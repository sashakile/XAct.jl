# Session Isolation Design

**Date:** 2026-03-26
**Status:** Implemented
**Location:** `src/XTensor.jl` (lines 266-450)

---

## 1. Problem

XTensor.jl originally stored all state (manifolds, metrics, tensors, etc.) in module-level
global dictionaries. This caused:

- **Test interference**: Tests that defined manifolds/metrics polluted subsequent tests.
- **No concurrent sessions**: Two independent computations could not coexist.
- **Fragile reset**: `reset_state!()` had to know about every global container.

## 2. Design

### 2.1 Session Struct

A `mutable struct Session` owns **all 22 mutable state containers**:

| Category | Containers | Count |
|----------|-----------|-------|
| Primary registries | manifolds, vbundles, tensors, metrics, perturbations, bases, charts, basis_changes, ctensors | 9 |
| Reverse-lookup indices | metric_name_index, parallel_deriv_index | 2 |
| Ordered lists | manifold_list, tensor_list, vbundle_list, perturbation_list, basis_list, chart_list | 6 |
| Physics support | traceless_tensors, trace_scalars, einstein_expansion | 3 |
| Identity framework | identity_registry | 1 |
| Hooks | validate_symbol_hook, register_symbol_hook | 1 |

A `generation::Int` counter increments on every `reset_session!` call, enabling
invalidation of caches that depend on session state.

### 2.2 Default Session & Backward Compatibility

```julia
const _default_session = Ref{Session}(Session())
```

The default session's dict objects are **shared** with the module-level globals
(`_manifolds`, `_tensors`, etc.), so existing code that reads globals transparently
reads the default session.

### 2.3 Kwarg Pattern

All `def_*!` functions, accessors, and predicates accept an optional keyword argument:

```julia
function def_manifold!(name, dim, indices; session::Session = _default_session[])
```

Callers that omit `session` get the default session (backward compatible).
Callers that pass an explicit session get full isolation.

### 2.4 Reset Semantics

- `reset_session!(s::Session)` — empties all 22 containers, increments generation.
- `reset_state!()` — convenience wrapper for `reset_session!(_default_session[])`.

## 3. Test Coverage

68 dedicated Session tests within `test/julia/test_xtensor.jl` verify:
- Isolation between sessions (definitions in one don't appear in another)
- Default session backward compatibility
- Reset clears all containers
- Generation counter increments
