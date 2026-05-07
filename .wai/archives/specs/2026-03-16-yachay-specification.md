> [!CAUTION]
> **EXTERNAL (2026-03-16)**: Implementation deferred to the [yachay](https://github.com/sashakile/yachay) repository.
> Schema files (`yachay-case.schema.json`, `yachay-manifest.schema.json`) remain in sxAct for reference.
> sxAct currently uses `InvarDB.jl` (Maple/Mathematica format parser) instead of Yachay JSON format.

> [!CAUTION]
> **EXTERNAL** (2026-03-16): Full implementation lives in the [yachay](https://github.com/sashakile/yachay) repository.
> Only the JSON schemas (`yachay-case.schema.json`, `yachay-manifest.schema.json`) are used in sxAct.
> InvarDB.jl currently uses its own Maple/Mathematica parser — Yachay format adoption is deferred.

# Yachay Specification v0.1.0
**The Knowledge Base for Riemann Tensor Identities**

---

## 1. Introduction

### 1.1 Purpose
**Yachay** is a language-agnostic, structured data format for storing pre-computed tensor identities and permutation bases. Its primary goal is to decouple the **Wolfram Invar database** from its Mathematica-specific file formats, enabling its use in Julia, Python, C++, and other environments via a standard JSON/TOML interface.

### 1.2 The "Identity Context"
In the Chacana ecosystem, **Yachay** provides the "Identity Context" (Ξ). While Chacana defines the *language* of expressions, Yachay provides the *theorems* used for simplification and canonicalization.

---

## 2. Directory Structure

A Yachay database is partitioned to ensure efficient loading and avoid monolithic file overhead.

```text
yachay-db/
├── manifest.toml         # Metadata, provenance, and global settings
└── data/
    ├── riemann/          # Standard Riemann invariants
    │   ├── 0_0.json      # Case: R^2 (degree 2, 0 derivs)
    │   ├── 1_1.json      # Case: R^2, D^1 R (degree 2, 2 derivs)
    │   └── ...
    └── dual/             # Dual (epsilon) invariants
        └── 4/            # Partitioned by dimension
            ├── 0_0.json
            └── ...
```

---

## 3. Global Manifest (`manifest.toml`)

The manifest defines the database's identity and the mathematical conventions it follows.

```toml
[meta]
name = "Standard Riemann Invariants"
version = "1.2.0"
source = "Wolfram xAct/Invar"
spec_version = "0.1.0"

[notation]
permutation = "images"  # 1-based "images" notation: [2, 1, 4, 3]
# Convention: Active mapping. If p[i] = j, the index at position i moves to position j.
coefficient = "rational" # Rational strings "num/den"
indexing = "1-based"    # Invariant IDs follow the source database.
# Note: JSON schemas apply to the parsed in-memory representation of this manifest.

[coverage]
dimension = 4           # Target spacetime dimension
max_degree = 7          # Max number of Riemann factors
max_order = 14          # Max total derivative order
steps = [1, 2, 3, 4, 5, 6]
```

---

## 4. Case Data Format (`case.json`)

Each case file contains the complete knowledge for a specific derivative/degree configuration.

### 4.1 Root Structure
| Field | Type | Description |
| :--- | :--- | :--- |
| `case` | string | The case identifier (e.g., `"0_2"`) |
| `degree` | integer | Number of Riemann factors |
| `deriv_orders` | array[int] | Sorted list of derivative orders |
| `total_indices` | integer | Total number of indices (degree * 4 + sum(deriv_orders)) |
| `basis` | object | Step 1: Permutation basis (images notation) |
| `rules` | object | Steps 2-6: Substitution rules (rational coefficients) |

### 4.2 Basis Object (`basis`)
Maps invariant indices to their canonical permutations.
```json
"basis": {
  "perms": {
    "1": [2, 1, 4, 3, 6, 5, 8, 7],
    "2": [3, 4, 1, 2, 7, 8, 5, 6]
  }
}
```

### 4.3 Rules Object (`rules`)
A map of reduction steps (cyclic, bianchi, etc.). Each step is a dictionary of `dependent_index: [[independent_index, "coeff"], ...]`.
```json
"rules": {
  "cyclic": {
    "step": 2,
    "identities": {
      "3": [[1, "1/1"], [2, "-1/1"]]
    }
  }
}
```

---

## 5. Implementation Requirements for Processors

1.  **Rational Precision**: Processors MUST use exact rational arithmetic (e.g., Julia `Rational{Int}`, Python `fractions.Fraction`) when applying rules.
2.  **Permutation Composition**: Processors MUST interpret permutations as **images notation** where `p[i]` is the image of position `i`.
3.  **Lazy Loading**: Processors SHOULD only load the specific case files required for the current expression to minimize memory footprint.
