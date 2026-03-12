# Python API Reference

!!! info "Project Profile for AI Agents (LLM TL;DR)"
    - **Distribution Name**: `xact-py`
    - **Import Name**: `import xact`
    - **Validation Framework**: `import sxact`
    - **Primary Purpose**: Python interface to `xAct.jl` and automated parity verification.
    - **Underlying Bridge**: `PythonCall.jl` and `juliacall`.
    - **Key Components**: `xact.xcore` (wrapper), `sxact.adapter` (verification engine).

This page describes the Python interface to the Julia `xAct.jl` core. The ecosystem is split into two packages (both included in the `xact-py` distribution):

1.  `xact`: The core library for tensor algebra.
2.  `sxact`: The testing and validation framework.

---

## 1. Core Wrapper (`xact`)

The `xact` package provides direct access to the Julia engines. It automatically manages the Julia runtime and the `xAct.jl` package using `juliapkg`.

### Low-level Symbol Access (`xact.xcore`)

Direct Python wrappers for the foundational functions in `XCore.jl`.

```python
from xact.xcore import validate_symbol, register_symbol

# Validate a name before definition to avoid collisions
validate_symbol("M")

# List all registered tensor names
from xact.xcore import x_tensor_names
print(x_tensor_names())
```

### High-Level API

The high-level Python API (e.g., `xact.Manifold("M", 4)`) is currently **in development**. For research use, we recommend using the Julia package `xAct.jl` directly.

---

## 2. Validation Framework (`sxact`)

The `sxact` package is used to prove mathematical parity between the new Julia implementation and the original Wolfram "Gold Standard."

### The Verification Adapter (`sxact.adapter`)

The `JuliaAdapter` is the primary way to interact with the Julia engine for testing purposes. It serializes commands into a standard format that can be compared against the Wolfram Oracle.

```python
from sxact.adapter.julia_stub import JuliaAdapter

# Initialize the Julia engine
adapter = JuliaAdapter()
adapter.initialize()

# Execute a command in the isolated test context
result = adapter.execute("def_manifold", {
    "name": "M",
    "dim": 4,
    "index_labels": ["a", "b"]
})
```

### Supported Adapter Commands

| Command | Description | Expects |
| :--- | :--- | :--- |
| `def_manifold` | Defines a new manifold. | `name`, `dim`, `index_labels` |
| `def_tensor` | Defines a new tensor. | `name`, `index_specs`, `manifold` |
| `def_metric` | Defines a metric tensor. | `signature`, `metric_str`, `cd_name` |
| `ToCanonical` | Canonicalizes an expression. | `expr` (string) |
| `Contract` | Contracts metric indices. | `expr` (string) |

---

## 3. Why the Split?

We separate the **computational wrapper** (`xact`) from the **verification logic** (`sxact`) to ensure that:

1.  **Lightweight Deployment**: Users who only need to perform tensor calculus don't need the heavy verification dependencies.
2.  **Infrastructure of Trust**: Developers can verify every change to the core engine against the Wolfram Oracle without polluting the core API.
3.  **Cross-Platform Parity**: The same `sxact` framework can be used to verify future implementations in other languages.

For more information on the verification architecture, see the [Architecture Guide](architecture.md).
