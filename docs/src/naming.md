# Naming and product map

!!! info "LLM TL;DR"
    - `XAct.jl` is the repository
    - `XAct.jl` / `XAct` is the Julia package and module
    - `xact-py` is the Python package name
    - `xact` is the Python import
    - `sxact` is the verification framework
    - See [Branding and Upstream Relationship](branding.md) for the full strategy.

This page explains the names used across the project and how they relate to the upstream Wolfram xAct project.

## Name map

| Name | Kind | Meaning |
| :--- | :--- | :--- |
| **Wolfram xAct** | Upstream | The original tensor algebra suite for Mathematica (the inspiration for this port) |
| `XAct.jl` | Repository | The Git repository that contains the whole project |
| `XAct.jl` | Julia package | The Julia package users add to their environment |
| `XAct` | Julia module | The module imported with `using XAct` |
| `xact-py` | Python package | The distribution published to PyPI |
| `xact` | Python import | The Python module imported in user code |
| `sxact` | Verification | The Python tooling for TOML tests, oracle snapshots, and normalization |

## Use the right name in the right place

| If you are doing… | Use… |
| :--- | :--- |
| Cloning the repo | `XAct.jl` |
| Importing the Julia module | `using XAct` |
| Installing from PyPI | `pip install xact-py` |
| Importing in Python | `import xact` |
| Talking about the verification stack | `sxact` |

## Related pages

- [Home](index.md)
- [Installation](installation.md)
- [Getting Started](getting-started.md)
- [Python API](api-python.md)
