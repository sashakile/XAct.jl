# TensorDSL Specification v0.1.0

**A cross-language notation for symbolic and numerical tensor calculus**

---

## 1. Introduction

### 1.1 Purpose

TensorDSL is a language-agnostic notation for expressing tensor algebra — from abstract index manipulation and covariant derivatives through to numerical evaluation on GPUs. It aims to replicate the full capabilities of xAct (the Mathematica tensor calculus suite) without being tied to Wolfram Language syntax or any single host language.

The notation is designed to be read and written by physicists, parsed by machines, and executed across Python, Julia, Rust, JavaScript, or any environment with a TOML parser and a string tokenizer.

### 1.2 Design principles

The design rests on five principles that emerged from surveying over 20 existing tensor systems:

**Principle 1: Separation of declarations from expressions.** Tensor metadata (symmetries, index types, derivative properties) is declared once in TOML tables and referenced many times in expressions. This mirrors the structure of a physics paper: you define your notation at the beginning, then use it throughout. It also prevents the brittleness that arises when metadata is embedded inside constructor calls (as in SymPy) or implicit in the host language (as in xAct).

**Principle 2: TOML for structure, strings for algebra.** TOML is exceptionally readable for flat and shallow-nested configuration — manifold dimensions, metric signatures, symmetry declarations, backend settings. But tensor expressions are inherently recursive trees (products of sums of derivatives of products...), where TOML's nesting becomes unwieldy. A compact string micro-syntax handles expressions, staying close to physics notation while remaining trivially parseable.

**Principle 3: Abstract and concrete indices as distinct types.** The single most common design failure in tensor libraries is conflating abstract indices (labels for tensor slots, denoting the tensor as a multilinear map) with concrete/component indices (integers labeling components in a basis). TensorDSL treats these as fundamentally different entities at the type level.

**Principle 4: Symmetry as first-class metadata.** Tensor symmetries are not optional annotations — they determine which simplifications are valid, how canonicalization works, and how many independent components exist. The spec provides readable shorthands (`sym`, `asym`, `riemann`, `tableau`) that expand internally to BSGS (Base and Strong Generating Set) representations compatible with the Butler-Portugal canonicalization algorithm.

**Principle 5: Backend neutrality.** The same `.toml` file targets symbolic engines (SymPy, Cadabra, xAct, SageMath) and numerical engines (NumPy, JAX, PyTorch, Julia) through backend configuration blocks, without changing any declaration or expression.


### 1.3 Architecture overview

TensorDSL uses a three-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Surface syntax                                │
│  ┌───────────────────┐  ┌────────────────────────────┐  │
│  │  TOML declarations │  │  String expression DSL     │  │
│  │  (manifolds,       │  │  R{^a _b _c _d} * g{^b ^d}│  │
│  │   tensors, rules)  │  │  T{^a _b ;c}              │  │
│  └───────────────────┘  └────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Abstract Syntax Tree (AST)                    │
│  Language-neutral tree of typed nodes:                   │
│  TensorNode, ProductNode, SumNode, DerivNode,           │
│  ScalarNode, ContractionNode                            │
│  Serializable to JSON for interchange.                  │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Backend targets                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │SymPy/    │ │einsum /  │ │LaTeX     │ │TACO /     │  │
│  │Cadabra   │ │NumPy/JAX │ │renderer  │ │codegen    │  │
│  │(symbolic)│ │(numerical│ │(display) │ │(compiler) │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────┘
```

A parser reads the TOML file, constructs the AST from expression strings, validates indices against declarations, and emits to one or more backends. The AST is the canonical intermediate form — it can be serialized to JSON for cross-process or cross-language interchange.


### 1.4 File extension and MIME type

TensorDSL specification files use the `.tensor.toml` extension (e.g., `schwarzschild.tensor.toml`). Plain `.toml` is also acceptable. The MIME type is `application/toml`.


### 1.5 Influences and prior art

TensorDSL draws on design patterns from the following systems:

- **xAct** (Mathematica): Butler-Portugal canonicalization algorithm, BSGS symmetry representation, abstract index architecture. The gold standard for symbolic tensor CAS.
- **Cadabra** (C++/Python): Property-declaration pattern (attaching metadata via `::` annotations), LaTeX-as-data-language philosophy, multi-term symmetry handling via Young projectors.
- **einsum** (NumPy/PyTorch/JAX): The de facto cross-library contraction notation. TensorDSL's string DSL extends einsum to support abstract indices and derivatives.
- **ITensor** (C++/Julia): Index-as-object pattern with identity, dimension, and type metadata. Automatic contraction by shared indices.
- **TACO** (MIT): Separation of expression language, format language, and schedule language — the principle that *what to compute*, *how data is stored*, and *how to compute* should be orthogonal.
- **CortexJS MathJSON**: JSON arrays as S-expressions for mathematical ASTs. TensorDSL's JSON serialization follows this convention.
- **HepLean** (Lean 4): Three-layer architecture (surface syntax → tensor trees → category-theoretic semantics) and formal verification of index notation.
- **SageManifolds** (SageMath): Component-level differential geometry with charts and frames.
- **OpenMath**: The `tensor1` content dictionary, which demonstrated the need for (and difficulty of) a standardized tensor interchange format.


### 1.6 Versioning policy

TensorDSL follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** version: breaking changes to syntax or semantics (e.g., changing the derivative ordering convention, removing a TOML table type, changing contraction rules).
- **MINOR** version: backward-compatible additions (e.g., new symmetry shorthands, new TOML table types, new AST node types).
- **PATCH** version: clarifications, typo fixes, and additional examples that do not change behavior.

The `[meta].version` field in a TOML file declares which spec version it conforms to. Parsers should check this field and refuse to process files with a higher MAJOR version than they support. Unknown TOML tables and unknown fields within known tables should be ignored with a warning (forward-compatibility).

**Extension convention:** vendor-specific or experimental fields should use the `x_` prefix (e.g., `x_custom_property = "value"`). Parsers must ignore `x_`-prefixed fields they do not recognize.

---

## 2. TOML declaration layer

The TOML file is organized into top-level table namespaces. Each namespace groups a specific kind of declaration. All namespaces are optional — a minimal file need only contain `[tensor.*]` entries. Parsers should emit a warning for files containing no tensor declarations, as such files are valid but not useful.

### 2.1 `[meta]` — File metadata

Describes the specification file itself. All fields are optional.

```toml
[meta]
version  = "0.1.0"               # Spec version this file conforms to
name     = "Schwarzschild perturbation theory"
authors  = ["Alice", "Bob"]
backend  = "symbolic"             # Default backend: "symbolic" | "numerical" | "both"
requires = "0.1.0"                # Minimum parser version required
```

| Field      | Type       | Default      | Description                              |
|------------|------------|--------------|------------------------------------------|
| `version`  | string     | `"0.1.0"`    | TensorDSL spec version this file targets |
| `name`     | string     | `""`         | Human-readable project name              |
| `authors`  | string[]   | `[]`         | List of author names                     |
| `backend`  | string     | `"symbolic"` | Default execution target                 |
| `requires` | string     | `"0.1.0"`    | Minimum parser version required          |


### 2.2 `[imports]` — Multi-file composition

Large projects can split declarations across multiple files using the imports table. Imported files provide base declarations that the current file can extend or override.

```toml
[imports]
base = ["gr_4d_standard.tensor.toml"]                  # base declarations
extra = ["spinor_conventions.tensor.toml"]              # additional declarations
```

| Field   | Type     | Required | Description                                         |
|---------|----------|----------|-----------------------------------------------------|
| `base`  | string[] | no       | Files whose declarations are loaded first            |
| `extra` | string[] | no       | Additional files loaded after base                   |

**Resolution order:** base files are loaded in array order, then extra files, then the current file. Later declarations override earlier ones with the same name. Index label pools are merged (union). Paths are relative to the importing file's directory.

**Conflict handling:** if two imported files declare the same tensor name with different symmetries, the later import wins and the parser emits a warning. To explicitly override an imported declaration, redeclare it in the current file.


### 2.3 `[manifold.<n>]` — Manifold declarations

A manifold is the geometric space on which tensors are defined. Each manifold declares its dimension and the abstract index labels that range over it.

```toml
[manifold.M]
dim       = 4
signature = [-1, 1, 1, 1]
indices   = ["a", "b", "c", "d", "e", "f", "g", "h"]

[manifold.S2]
dim     = 2
indices = ["θ", "φ"]

[manifold.internal]
dim     = 4
indices = ["I", "J", "K", "L"]     # can overlap with M if index_types differ
```

| Field       | Type     | Required | Description                                      |
|-------------|----------|----------|--------------------------------------------------|
| `dim`       | integer  | yes      | Dimension of the manifold                        |
| `signature` | int[]    | no       | Metric signature (e.g., `[-1,1,1,1]` for Lorentzian) |
| `indices`   | string[] | yes      | Pool of abstract index labels for this manifold  |

**Index label uniqueness:** Index labels must be unique within a single manifold's pool. Labels *may* overlap between different manifolds provided they belong to different `index_type` declarations. When an expression uses a label that belongs to multiple index types, disambiguation is required using type annotations (see §4.3.1). Unicode labels are permitted and encouraged for readability (e.g., `"θ"`, `"φ"`, `"α"`, `"β"`).


### 2.4 `[index_type.<n>]` — Index type declarations

An index type refines the manifold-level index pool with additional semantics: which metric raises and lowers these indices, their dimension, and optional properties like conjugation (for spinor indices).

```toml
[index_type.Lorentz]
manifold  = "M"
dim       = 4
metric    = "g"
values    = ["a", "b", "c", "d", "e", "f", "g", "h"]

[index_type.Spinor]
manifold  = "M"
dim       = 2
metric    = "epsilon"
values    = ["A", "B", "C", "D"]
conjugate = "SpinorBar"
```

| Field       | Type     | Required | Description                                        |
|-------------|----------|----------|----------------------------------------------------|
| `manifold`  | string   | yes      | Which manifold these indices range over             |
| `dim`       | integer  | yes      | Dimension (may differ from manifold for sub-bundles)|
| `metric`    | string   | no       | Name of the metric tensor for raising/lowering      |
| `values`    | string[] | yes      | Allowed index labels for this type                  |
| `conjugate` | string   | no       | Name of the conjugate index type (spinors)          |

When a metric is specified, the system knows how to raise and lower indices of this type. Without a metric, raising/lowering is forbidden — this correctly handles situations like SU(N) fundamental vs. conjugate representations where the two variances are linearly independent.


### 2.5 `[metric.<n>]` — Metric declarations

A metric tensor with its associated connection.

```toml
[metric.g]
index_type  = "Lorentz"
symmetry    = "symmetric"
signature   = [-1, 1, 1, 1]
derivative  = "nabla"
inverse     = "g_inv"              # optional: name for g^{ab}
```

| Field        | Type     | Required | Description                                  |
|--------------|----------|----------|----------------------------------------------|
| `index_type` | string   | yes      | Which index type this metric acts on          |
| `symmetry`   | string   | yes      | Must be `"symmetric"` for a metric            |
| `signature`  | int[]    | no       | Eigenvalue signs of the metric                |
| `derivative` | string   | no       | Name of the compatible covariant derivative   |
| `inverse`    | string   | no       | Name for the inverse metric tensor            |


### 2.6 `[derivative.<n>]` — Derivative operator declarations

Derivative operators with their algebraic properties.

```toml
[derivative.nabla]
type          = "covariant"
symbol        = "∇"
metric        = "g"
torsion_free  = true

[derivative.partial]
type   = "partial"
symbol = "∂"

[derivative.lie]
type   = "lie"
symbol = "£"

[derivative.exterior]
type   = "exterior"
symbol = "d"
```

| Field          | Type    | Required | Description                                          |
|----------------|---------|----------|------------------------------------------------------|
| `type`         | string  | yes      | `"covariant"`, `"partial"`, `"lie"`, or `"exterior"` |
| `symbol`       | string  | no       | Display symbol (for LaTeX rendering)                  |
| `metric`       | string  | no       | Metric this derivative is compatible with             |
| `torsion_free` | boolean | no       | If `true`, `∇_a ∇_b f = ∇_b ∇_a f` on scalars       |

When `type = "covariant"` and a metric is specified, the system automatically derives:

- **Metric compatibility**: `∇_c g_{ab} = 0`
- **Commutation rule**: `[∇_a, ∇_b] V^c = R^c_{dab} V^d`
- **Christoffel symbols** (when lowering to components)

When `torsion_free = true`, the torsion tensor vanishes and Christoffel symbols are symmetric in their lower indices.


### 2.7 `[tensor.<n>]` — Tensor declarations

The core of any TensorDSL file. Each tensor declares its index structure, symmetries, and optional metadata.

```toml
[tensor.R]
indices      = ["^a", "_b", "_c", "_d"]
symmetry     = "riemann(^a, _b, _c, _d)"
role         = "curvature"
derived_from = "nabla"

[tensor.Ric]
indices    = ["_a", "_b"]
symmetry   = "sym(_a, _b)"
definition = "R{^c _a _c _b}"

[tensor.RicciScalar]
indices    = []
symmetry   = "none"
definition = "g{^a ^b} * Ric{_a _b}"

[tensor.T]
indices    = ["_a", "_b"]
symmetry   = "sym(_a, _b)"
role       = "stress_energy"
properties = ["conserved"]
weight     = 0                     # tensor density weight
```

| Field          | Type     | Required | Description                                        |
|----------------|----------|----------|----------------------------------------------------|
| `indices`      | string[] | yes      | Slot structure with variance: `"^a"`, `"_b"`       |
| `symmetry`     | string   | yes      | Symmetry shorthand (see §3) or `"none"`            |
| `role`         | string   | no       | Semantic role: `"metric"`, `"curvature"`, etc.     |
| `definition`   | string   | no       | Defining expression in the string DSL              |
| `derived_from` | string   | no       | Which derivative operator generates this tensor    |
| `properties`   | string[] | no       | Algebraic properties: `"conserved"`, `"traceless"` |
| `traceless`    | boolean  | no       | If `true`, all traces vanish                       |
| `order`        | integer  | no       | Perturbation order (for perturbation theory)       |
| `weight`       | number   | no       | Tensor density weight (see §5.5)                   |

**Slot declarations vs. expression indices.** The `indices` array defines the **canonical slot ordering** — it specifies how many slots the tensor has and the natural variance of each slot. The labels within it (e.g., `"^a"`, `"_b"`) are *parameter names* used to reference slots in the `symmetry` and `definition` fields. They do **not** restrict which index labels may appear in expressions. In an expression, any label from the appropriate `index_type.values` pool may occupy any slot. For example, a tensor declared with `indices = ["^a", "_b"]` can appear in an expression as `T{^x _y}` — the parser matches by slot position, not by label name.

**Scalar tensors (rank 0).** Tensors with `indices = []` are scalars. In expressions, scalars appear as bare names without index blocks: `RicciScalar`, not `RicciScalar{}`. The parser distinguishes scalars from unknown identifiers by checking the tensor declarations. The empty-braces form `phi{}` is also accepted as an explicit scalar notation and is equivalent to bare `phi`.

**Variance flexibility.** The variance in the `indices` array defines the *natural* or *canonical* index positions of the tensor. Expressions may use the tensor with indices in different variance positions provided a metric is available for the relevant index type. For example, if `R` is declared with `indices = ["^a", "_b", "_c", "_d"]`, the expression `R{_a _b _c _d}` (all covariant) is valid because the first index has been lowered by the metric. The system implicitly inserts the metric contraction when evaluating.


### 2.8 `[chart.<n>]` — Coordinate chart declarations

Charts provide a bridge from abstract manifolds to concrete component calculations.

```toml
[chart.spherical]
manifold    = "M"
coordinates = ["t", "r", "theta", "phi"]

[chart.cartesian]
manifold    = "M"
coordinates = ["t", "x", "y", "z"]
```

| Field         | Type     | Required | Description                      |
|---------------|----------|----------|----------------------------------|
| `manifold`    | string   | yes      | Which manifold this chart covers |
| `coordinates` | string[] | yes      | Ordered coordinate names         |

The number of coordinates must equal the manifold dimension.


### 2.9 `[components.<n>]` — Concrete component values

Attaches numerical or symbolic component values to a tensor in a given chart.

```toml
[components.g_schwarzschild]
tensor     = "g"
chart      = "spherical"
format     = "diagonal"
values     = [
  "-(1 - 2*M/r)",
  "1/(1 - 2*M/r)",
  "r^2",
  "r^2 * sin(theta)^2",
]
parameters = { M = "mass" }

[components.g_minkowski]
tensor = "g"
chart  = "cartesian"
format = "dense"
values = [
  [-1, 0, 0, 0],
  [ 0, 1, 0, 0],
  [ 0, 0, 1, 0],
  [ 0, 0, 0, 1],
]
```

| Field        | Type              | Required | Description                                        |
|--------------|-------------------|----------|----------------------------------------------------|
| `tensor`     | string            | yes      | Which tensor these components belong to             |
| `chart`      | string            | yes      | In which coordinate chart                           |
| `format`     | string            | yes      | `"diagonal"`, `"dense"`, `"sparse"`, `"symbolic"`  |
| `values`     | array             | yes      | Component values (format depends on `format` field) |
| `parameters` | table             | no       | Named symbolic parameters used in values            |

Format types:

- `"diagonal"` — a flat array of diagonal entries; off-diagonal entries are zero.
- `"dense"` — a full n-dimensional array (nested arrays matching tensor rank).
- `"sparse"` — an array of `{indices = [...], value = ...}` entries specifying only nonzero components.
- `"symbolic"` — values are symbolic expression strings, evaluated by the backend.


### 2.10 `[expr.<n>]` — Named expressions

Named expressions serve as reusable definitions, equations, or identities within the file.

```toml
[expr.einstein_eq]
description = "Einstein field equations"
lhs = "G{_a _b}"
rhs = "8 * pi * T{_a _b}"

[expr.ricci_contraction]
description = "Ricci tensor as contraction of Riemann"
result = "R{^c _a _c _b}"

[expr.bianchi_second]
description = "Contracted second Bianchi identity"
identity = "G{_a _b ;^b} = 0"
```

| Field         | Type   | Required | Description                                      |
|---------------|--------|----------|--------------------------------------------------|
| `description` | string | no       | Human-readable description                       |
| `lhs`, `rhs`  | string | no       | Left and right sides of an equation               |
| `result`      | string | no       | A single expression (not an equation)             |
| `identity`    | string | no       | An identity that holds by construction (e.g., `= 0`) |
| `rule`        | string | no       | A rewrite or commutation rule                     |

Exactly one of `lhs`/`rhs`, `result`, `identity`, or `rule` should be present (beyond `description`). The `lhs`/`rhs` pair represents an equation; `result` represents a standalone expression; `identity` represents a relation that must vanish; `rule` represents a transformation.


### 2.11 `[rule.<n>]` — Rewrite rules

Rewrite rules define pattern-matching transformations that a symbolic backend can apply.

```toml
[rule.metric_compatibility]
description = "Metric compatibility of Levi-Civita connection"
pattern     = "g{_a _b ;_c}"
replacement = "0"
auto_apply  = true

[rule.bianchi_first]
description = "First Bianchi identity (algebraic)"
pattern     = "R{_a _b _c _d} + R{_a _c _d _b} + R{_a _d _b _c}"
replacement = "0"

[rule.leibniz]
description = "Leibniz rule for covariant derivative"
pattern     = "(A * B){;_c}"
replacement = "A{;_c} * B + A * B{;_c}"
auto_apply  = true

[rule.riemann_to_weyl]
description = "Decompose Riemann into Weyl + Ricci parts (4D)"
pattern     = "R{_a _b _c _d}"
replacement = """
  Weyl{_a _b _c _d}
  + (1/2) * (g{_a _c} * Ric{_b _d} - g{_a _d} * Ric{_b _c}
           - g{_b _c} * Ric{_a _d} + g{_b _d} * Ric{_a _c})
  - (1/6) * RicciScalar * (g{_a _c} * g{_b _d} - g{_a _d} * g{_b _c})
"""
```

| Field         | Type    | Required | Description                                            |
|---------------|---------|----------|--------------------------------------------------------|
| `description` | string  | no       | Human-readable description                             |
| `pattern`     | string  | yes      | Expression pattern to match (index names are wildcards)|
| `replacement` | string  | yes      | Replacement expression (or `"0"`)                      |
| `auto_apply`  | boolean | no       | If `true`, apply this rule automatically during simplification |
| `conditions`  | string[]| no       | Additional conditions for the rule to fire             |
| `direction`   | string  | no       | `"forward"` (default), `"backward"`, or `"both"`       |

Pattern indices are treated as wildcards: `R{_a _b _c _d}` matches any Riemann tensor regardless of concrete index labels. The matching respects tensor symmetries — a pattern `R{_a _b _c _d}` also matches `R{_b _a _c _d}` (up to sign) if Riemann antisymmetry is declared.

Multi-line replacement strings (using TOML's `"""` syntax) allow complex decompositions to remain readable.


### 2.12 `[backend.<n>]` — Backend configuration

Configure how the spec should be processed by different engines.

```toml
[backend.symbolic]
engine       = "sympy"
canonicalize = true
simplify     = "full"

[backend.numerical]
engine     = "numpy"
precision  = "float64"
gpu        = false
einsum_opt = "optimal"
```

| Field          | Type    | Required | Description                                          |
|----------------|---------|----------|------------------------------------------------------|
| `engine`       | string  | yes      | Target engine name                                   |
| `canonicalize` | boolean | no       | Enable Butler-Portugal canonicalization               |
| `simplify`     | string  | no       | Simplification level: `"none"`, `"basic"`, `"full"`  |
| `precision`    | string  | no       | Float precision: `"float32"`, `"float64"`, `"float128"` |
| `gpu`          | boolean | no       | Enable GPU acceleration                              |
| `einsum_opt`   | string  | no       | Contraction order strategy: `"greedy"`, `"optimal"`, `"auto"` |

Supported symbolic engines: `"sympy"`, `"cadabra"`, `"xact"`, `"sagemath"`, `"custom"`.
Supported numerical engines: `"numpy"`, `"jax"`, `"pytorch"`, `"julia"`, `"tensorflow"`, `"custom"`.

---

## 3. Symmetry system

### 3.1 Shorthand notation

Symmetries are declared as strings using a human-readable functional notation. The parser expands these into BSGS (Base and Strong Generating Set) representations internally.

| Shorthand                       | Meaning                                            | Generators                          |
|---------------------------------|----------------------------------------------------|-------------------------------------|
| `none`                          | No symmetry                                        | Identity only                       |
| `sym(i, j)`                     | Symmetric in slots i, j                            | `(i j) → +1`                       |
| `asym(i, j)`                    | Antisymmetric in slots i, j                        | `(i j) → -1`                       |
| `sym(i, j, k)`                  | Fully symmetric in three slots                     | `S_3` with sign `+1`               |
| `asym(i, j, k)`                 | Fully antisymmetric in three slots                 | `S_3` with sign `(-1)^π`           |
| `riemann(a, b, c, d)`           | Riemann monoterm symmetries                        | See below                           |
| `cyclic(i, j, k)`               | Cyclic symmetry: `T_{ijk} = T_{jki} = T_{kij}`    | `(i j k) → +1`                     |
| `hermitian(i, j)`               | Hermitian: `T_{ij} = T*_{ji}`                      | `(i j) → conjugate`                |
| `tableau([[i,k],[j,l]])`        | Young tableau symmetry                             | Young symmetrizer                   |
| `block_sym([i,j], [k,l])`       | Symmetric under exchange of index pairs            | `(ij)(kl) → +1`                    |
| `block_asym([i,j], [k,l])`      | Antisymmetric under exchange of index pairs        | `(ij)(kl) → -1`                    |

The `riemann(a, b, c, d)` shorthand encodes **only the monoterm symmetries** of the Riemann tensor:

- Antisymmetric in first pair: `R_{abcd} = -R_{bacd}`
- Antisymmetric in second pair: `R_{abcd} = -R_{abdc}`
- Symmetric under pair exchange: `R_{abcd} = R_{cdab}`
- These three generators yield 21 independent components in 4D (reduced from 256).

> **Important:** The first Bianchi identity (`R_{a[bcd]} = 0`, which further reduces independent components to 20 in 4D) is a **multi-term symmetry** and cannot be represented as BSGS generators. It must be declared separately as a rewrite rule in the `[rule.*]` section (see the `rule.bianchi_first` example in §2.11). This distinction between monoterm symmetries (handled by BSGS/canonicalization) and multi-term symmetries (handled by rewrite rules) is fundamental to the design.

### 3.2 Compound symmetries

Symmetries can be composed using `+` (intersection) for tensors with independent symmetries in different slot groups:

```toml
[tensor.C]
indices  = ["_a", "_b", "_c"]
symmetry = "asym(_a, _b) + none(_c)"
# C_{abc} = -C_{bac}, no constraint on third slot
```

### 3.3 Custom symmetries via generators

For symmetries not covered by shorthands, use explicit generators as a TOML sub-table:

```toml
[tensor.X]
indices = ["_a", "_b", "_c", "_d"]

[tensor.X.symmetry]
type = "custom"
generators = [
  { perm = [1, 0, 2, 3], sign = -1 },
  { perm = [0, 1, 3, 2], sign = -1 },
  { perm = [2, 3, 0, 1], sign =  1 },
]
```

Each generator is a permutation of slot positions (0-indexed) with a sign factor. The `perm` array maps each slot to its new position: `[1, 0, 2, 3]` swaps the first two slots. The `sign` gives the factor acquired under that permutation.

**Mapping between slot positions and named indices:** slot positions correspond to the order of the `indices` array in the tensor declaration. For `indices = ["_a", "_b", "_c", "_d"]`, position 0 = `_a`, position 1 = `_b`, position 2 = `_c`, position 3 = `_d`. The shorthand `riemann(_a, _b, _c, _d)` is equivalent to the custom generator set shown above.

The full symmetry group is generated by these elements — the parser computes the BSGS from the generators using the Schreier-Sims algorithm, which is needed by the Butler-Portugal canonicalization algorithm.

### 3.4 Internal representation: BSGS

All symmetry shorthands expand to a **Base and Strong Generating Set** (BSGS):

- **Base**: an ordered subset of slot positions `[b₁, b₂, ...]` such that only the identity fixes all base points.
- **Strong Generating Set (SGS)**: a set of generators `{g₁, g₂, ...}` with the property that for each base prefix `[b₁, ..., bₖ]`, the SGS contains generators for the pointwise stabilizer of `{b₁, ..., bₖ}`.

This representation enables polynomial-time canonicalization via the Butler-Portugal algorithm: given an expression with contracted (dummy) indices, the algorithm finds the lexicographically smallest representative of the double-coset `D·g·S`, where `S` is the slot symmetry group and `D` is the dummy-index permutation group.

Implementations should store the BSGS internally but never require users to write it directly — the shorthand system and generator declarations are always sufficient.

---

## 4. Expression DSL

### 4.1 Overview

The expression DSL is a compact string notation for tensor algebra. It is designed to be:

- Close to standard physics notation (LaTeX-like, but machine-parseable)
- Unambiguous (every character has exactly one interpretation)
- Host-language independent (no operator overloading, no macros)
- Expressible as a simple recursive-descent grammar

Expressions appear as string values in TOML fields (`definition`, `pattern`, `replacement`, `lhs`, `rhs`, `result`, `identity`, `rule`).

**Whitespace and comments:** expression strings are stripped of leading/trailing whitespace. Internal whitespace (spaces, tabs, newlines) is collapsed to single spaces during parsing. No comment syntax exists within expression strings — comments belong in the TOML layer using `#` syntax.

### 4.2 Tokens

The expression language has the following token types:

| Token            | Pattern             | Examples                     |
|------------------|---------------------|------------------------------|
| Tensor name      | `[A-Za-z_]\w*`      | `R`, `Ric`, `g`, `Weyl`     |
| Contra index     | `^` + label         | `^a`, `^mu`, `^A`           |
| Covar index      | `_` + label         | `_a`, `_mu`, `_A`           |
| Covar derivative | `;` + label or `;` + `^`/`_` + label | `;c`, `;_c`, `;^c` |
| Partial deriv    | `,` + label or `,` + `^`/`_` + label | `,c`, `,_c`         |
| Index block      | `{` ... `}`         | `{^a _b _c _d}`             |
| Multiply         | `*`                 |                              |
| Add              | `+`                 |                              |
| Subtract         | `-`                 |                              |
| Open paren       | `(`                 |                              |
| Close paren      | `)`                 |                              |
| Scalar literal   | number or fraction  | `3`, `1/2`, `8`, `-1`       |
| Named constant   | identifier          | `pi`, `RicciScalar`         |
| Equality         | `=`                 | (in equations and identities)|
| Commutator       | `[` ... `,` ... `]` | `[nabla{_a}, nabla{_b}]`    |

### 4.3 Index notation

Indices are written inside curly braces `{}` immediately after a tensor name, with no space between the name and the opening brace. Within the braces, indices are separated by spaces.

```
T{^a _b _c}          Three indices: one contravariant, two covariant
g{_a _b}             Metric tensor with two covariant indices
R{^a _b _c _d}       Riemann tensor (mixed variance)
delta{^a _b}         Kronecker delta
epsilon{_a _b _c _d} Levi-Civita tensor
phi                  Scalar field (rank 0) — no braces needed
phi{}                Scalar field — explicit empty braces (equivalent)
```

**Variance prefixes:**

| Prefix | Meaning          | Physics notation | LaTeX         |
|--------|------------------|------------------|---------------|
| `^`    | Contravariant    | upper index      | `T^{a}`       |
| `_`    | Covariant        | lower index      | `T_{a}`       |

Every index must carry an explicit variance prefix. There is no default variance.

#### 4.3.1 Type-annotated indices

When index labels are shared between multiple index types (e.g., a spacetime manifold and an internal gauge space both using `a, b, c, d`), disambiguation is required using a colon-separated type annotation:

```
T{^a:Lorentz _b:Lorentz} * A{^a:Gauge}     Unambiguous: different 'a' indices
F{_a:Gauge _b:Gauge}                         Gauge field strength
```

Type annotations are optional when index labels are unique across all declared index types. Parsers should emit an error when an ambiguous label is used without a type annotation.

### 4.4 Einstein summation convention

Repeated index names trigger automatic contraction (summation), provided one occurrence is contravariant and one is covariant:

```
R{^a _b _a _d}                   Contracts over 'a' → yields a rank-2 tensor
T{^a _b} * S{^b _c}              Contracts over 'b' → matrix-like product
g{^a ^b} * R{_a _c _b _d}        Contracts over both 'a' and 'b'
```

**Validation rules:**

- A contracted pair must have opposite variance (one `^`, one `_`).
- An index name appearing more than twice within a single non-parenthesized product is an error. Parenthesized sub-expressions define independent contraction scopes: in `(T{^a _b} * S{^b _a}) * V{^a _a}`, the name `a` appears four times but forms two separate valid contractions in two independent scopes.
- Free indices (appearing exactly once) must match across all terms of a sum.

### 4.5 Derivative indices

Covariant and partial derivatives are denoted by appending derivative indices after the tensor's regular indices, using `;` for covariant and `,` for partial.

> **⚠ Convention (read carefully):** Derivative indices are applied in **left-to-right order** — the leftmost derivative acts first (innermost), and each subsequent derivative wraps around the previous result:
>
> ```
> T{^a ;b ;c}    means    ∇_c( ∇_b( T^a ) )
>                              ^^^^^^^^^^^^
>                              ;b acts first (innermost)
>                         ^^^^^^^^^^^^^^^^^^^^^^^
>                         ;c acts second (outermost)
> ```
>
> This matches the convention that `T^a{}_{;b;c}` in written notation means "first differentiate by b, then by c," consistent with xAct's `CD[-c][CD[-b][T[a]]]` (where the outermost operator in the nested form corresponds to the rightmost index in the flat form).

Full examples:

```
T{^a _b ;c}                ∇_c T^a_b           (one covariant derivative)
T{^a _b ,c}                ∂_c T^a_b           (one partial derivative)
T{^a _b ;c ;d}             ∇_d(∇_c T^a_b)      (;c first, then ;d wraps)
f{;a ;b} - f{;b ;a}        [∇_b,∇_a]f = ∇_b(∇_a f) - ∇_a(∇_b f)
```

Derivative indices can carry explicit variance:

```
T{^a _b ;^c}               ∇^c T^a_b   (derivative index raised by metric)
T{^a _b ;_c}               ∇_c T^a_b   (same as ;c — covariant is default)
```

When variance is omitted on a derivative index (plain `;c`), it defaults to **covariant** — matching standard physics convention. The form `;^c` is syntactic sugar for a metric-raised derivative index: `∇^c T ≡ g^{cd} ∇_d T`. The derivative operator itself is always fundamentally covariant; the `^`/`_` on a derivative index controls only the variance of the resulting free index in the expression.


### 4.6 Products and sums

Tensor products are written with explicit `*` operators. Sums use `+` and `-`. Parentheses group sub-expressions.

```
R{^a _b _c _d} * g{^b ^d}                         Product with contraction
Ric{_a _b} - (1/2) * g{_a _b} * RicciScalar       Sum with scalar multiplication
(T{^a _b} + S{^a _b}) * V{^b}                     Parenthesized sum, then product
```

**Operator precedence** (highest to lowest):

1. Index attachment: `T{...}` (binds tightest)
2. Derivative: `;` and `,` within index blocks
3. Multiplication: `*`
4. Addition/subtraction: `+`, `-`
5. Equality: `=` (only in equations)

Parentheses override precedence as usual.

### 4.7 Scalars and constants

Scalar quantities (rank-0 tensors) appear as bare names or numeric literals:

```
8 * pi * T{_a _b}                Numeric literal times named constant
(1/2) * g{_a _b} * RicciScalar   Fraction times scalar field
-1 * h{_a _b}                    Negative sign via scalar
```

Fractions are written as `numerator/denominator` and should be parenthesized when used as coefficients: `(1/2) * T{...}`.

Named constants must be declared in the `[tensor.*]` section (with `indices = []` and `symmetry = "none"`) or recognized as built-in constants. Built-in constants are `pi`, `e`, `i` (imaginary unit), and `0`.

### 4.8 Commutator notation

Commutators of derivative operators use bracket syntax:

```
[nabla{_a}, nabla{_b}] V{^c} = R{^c _d _a _b} * V{^d}
```

This is syntactic sugar. The parser expands `[A, B] X` into `A * B * X - B * A * X` and then applies commutation rules.

> **TOML note:** square brackets `[` `]` inside TOML string values are safe — they are only special at the table-declaration level. However, TOML-aware editors may highlight them confusingly. If your editor struggles, use TOML literal strings (single quotes) for expressions containing brackets:
> `rule = '[nabla{_a}, nabla{_b}] V{^c} = R{^c _d _a _b} * V{^d}'`

### 4.9 Multi-line expressions

TOML's multi-line string syntax (`"""..."""`) allows complex expressions to be written readably:

```toml
[expr.linearized_ricci]
result = """
  (1/2) * (
    - h{_a _b ;^c ;_c}
    - h{^c _c ;_a ;_b}
    + h{_a ^c ;_b ;_c}
    + h{_b ^c ;_a ;_c}
  )
"""
```

Whitespace and newlines within expressions are insignificant (collapsed to single spaces during parsing).

### 4.10 Formal grammar (EBNF)

```ebnf
expression     = equation | term_list ;
equation       = term_list "=" term_list ;
term_list      = term ( ("+" | "-") term )* ;
term           = factor ( "*" factor )* ;
factor         = scalar | tensor_expr | "(" term_list ")" | commutator ;
tensor_expr    = name ( "{" index_list "}" )? ;     (* braces optional for scalars *)
index_list     = index ( " " index )* ;
index          = variance label type_annot? | deriv_index ;
variance       = "^" | "_" ;
type_annot     = ":" name ;                          (* e.g., ^a:Lorentz *)
deriv_index    = (";" | ",") variance? label type_annot? ;
label          = LETTER ( LETTER | DIGIT | "_" )* ;
name           = LETTER ( LETTER | DIGIT | "_" )* ;
scalar         = NUMBER | fraction | name ;
fraction       = NUMBER "/" NUMBER ;
commutator     = "[" term "," term "]" ;

(* Terminal classes *)
LETTER         = [A-Za-zα-ωΑ-Ω] | unicode_letter ;
DIGIT          = [0-9] ;
NUMBER         = "-"? DIGIT+ ("." DIGIT+)? ;
```

---

## 5. Semantics

### 5.1 Index validation

A well-formed expression must satisfy these rules:

1. **Declaration check.** Every tensor name must appear in a `[tensor.*]` or `[metric.*]` declaration, or be a built-in constant (`pi`, `e`, `i`, `0`).
2. **Arity check.** The number of non-derivative indices on a tensor must match its declared `indices` array length. Scalar tensors (`indices = []`) must appear with zero non-derivative indices.
3. **Type check.** Each index label must belong to a declared `index_type` whose `values` list includes that label. If a label belongs to multiple index types, a type annotation is required (see §4.3.1).
4. **Contraction check.** Every repeated index name within a contraction scope must appear exactly twice, with opposite variance (one `^`, one `_`). Parenthesized sub-expressions define independent contraction scopes.
5. **Free index check.** In a sum `A + B`, the set of free indices (names and variances) of `A` must equal that of `B`.
6. **Dummy index check.** Contracted (dummy) index names can be freely renamed without changing the expression's meaning (alpha-equivalence). Parsers should detect and permit this.

### 5.2 Metric operations

When a metric is associated with an index type, the following operations become available:

**Raising an index:** `g{^a ^b} * T{_b _c}` contracts over `b`, effectively computing `T^a{}_c`. The resulting tensor has one contravariant and one covariant index.

**Lowering an index:** `g{_a _b} * T{^b ^c}` contracts over `b`, computing `T_{a}{}^c`.

**Trace — metric-free case:** contracting a contravariant-covariant pair on the same tensor (`T{^a _a}`) is a metric-independent operation. This is the trace of a (1,1)-tensor and is well-defined without any metric — it is a coordinate-invariant scalar. No metric insertion is needed or performed.

**Trace — metric-dependent case:** contracting two indices of the same variance requires a metric. `T{_a _a}` (two covariant indices) is syntactic sugar for `g{^a ^b} * T{_a _b}` — the metric inverse is implicitly inserted. Similarly, `T{^a ^a}` (two contravariant) implies `g{_a _b} * T{^a ^b}`. These forms are only valid when a metric is declared for the relevant index type. Parsers should emit an error if same-variance contraction is attempted without a metric.

### 5.3 Derivative semantics

**Partial derivatives** (`T{^a _b ,c}` = `∂_c T^a_b`) obey:

- Linearity: `∂_c (αA + βB) = α ∂_c A + β ∂_c B`
- Leibniz rule: `∂_c (A · B) = (∂_c A) · B + A · (∂_c B)`
- Commutativity: `∂_a ∂_b = ∂_b ∂_a` (on smooth fields)

**Covariant derivatives** (`T{^a _b ;c}` = `∇_c T^a_b`) additionally satisfy:

- Metric compatibility: `∇_c g_{ab} = 0` (when `torsion_free` and metric-compatible)
- Non-commutativity: `[∇_a, ∇_b] V^c = R^c{}_{dab} V^d` (generates Riemann tensor)
- Generalized Leibniz rule on tensor products

### 5.4 Symmetry inheritance under differentiation

When a derivative acts on a tensor, the resulting expression inherits symmetries from the original tensor in the non-derivative slots, but gains no new symmetry relating the derivative index to any original slot.

For example, if `T{_a _b}` has `symmetry = "sym(_a, _b)"`, then `T{_a _b ;c}` (= `∇_c T_{ab}`) is still symmetric in `_a` and `_b`, but has no symmetry involving `_c`. The canonicalizer must be aware of this: it can freely swap `_a ↔ _b` but cannot move `_c`.

This rule applies recursively: `T{_a _b ;c ;d}` is symmetric in `_a, _b` but has no constraint on `_c` or `_d` (and in general `∇_c ∇_d T_{ab} ≠ ∇_d ∇_c T_{ab}` — their difference involves the Riemann tensor).

### 5.5 Tensor densities

The `weight` field on a tensor declaration specifies its tensor density weight. A tensor density of weight `w` transforms under coordinate changes with an extra factor of `|det(g)|^{w/2}`.

**Effect on covariant derivatives:** the covariant derivative of a tensor density of weight `w` acquires an additional connection term:

```
∇_c T^{a...}_{b...} (weight w) = ∂_c T^{a...}_{b...}
    + (standard Christoffel terms)
    - w * Γ^d_{dc} * T^{a...}_{b...}
```

In the current version (v0.1.0), the `weight` field is **informational**. Implementations that support automatic density corrections should document this capability. For maximum portability, users should handle density corrections via explicit rewrite rules rather than relying on automatic behavior.

### 5.6 Canonicalization

Canonicalization transforms a tensor expression into a unique normal form, enabling equality testing by comparison of canonical forms. The Butler-Portugal algorithm solves this as a double-coset problem.

Given an expression `T_{a₁...aₙ}`:

1. The **slot symmetry group** `S` is determined by the tensor's declared symmetries (BSGS).
2. The **dummy index group** `D` accounts for relabeling freedom of contracted indices.
3. The canonical form is the lexicographically minimal element of the double coset `D · g · S`.

The algorithm runs in polynomial time for practical tensor expressions (handling 100+ indices efficiently).

Canonicalization is invoked explicitly by a backend (e.g., `expr.canonicalize()`) or automatically when `auto_apply = true` on canonicalization rules.

### 5.7 Evaluation pipeline

The full pipeline from TOML to numerical result:

```
                              TOML file
                                 │
                            ┌────▼────┐
                            │  Parse  │
                            └────┬────┘
                                 │
                    ┌────────────▼────────────┐
                    │  AST (abstract indices)  │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
       ┌──────▼──────┐   ┌──────▼──────┐    ┌───────▼──────┐
       │ Canonicalize │   │ Apply rules │    │  Substitute  │
       │ (Butler-     │   │ (Bianchi,   │    │  components  │
       │  Portugal)   │   │  Leibniz)   │    │  (chart +    │
       └──────┬──────┘   └──────┬──────┘    │   values)    │
              │                  │           └───────┬──────┘
              └──────────┬───────┘                   │
                         │                           │
              ┌──────────▼──────────┐     ┌──────────▼──────────┐
              │  Simplified AST     │     │  Component arrays   │
              │  (symbolic result)  │     │  (numerical data)   │
              └──────────┬──────────┘     └──────────┬──────────┘
                         │                           │
                  ┌──────▼──────┐             ┌──────▼──────┐
                  │   LaTeX     │             │   einsum /  │
                  │   output    │             │   BLAS /    │
                  │             │             │   GPU exec  │
                  └─────────────┘             └─────────────┘
```

### 5.8 Diagnostic format

When a parser or validator encounters an error or warning, diagnostics should include:

- **TOML path**: the dotted table path where the error occurs (e.g., `tensor.R.symmetry`, `expr.einstein_eq.lhs`).
- **Expression location**: for errors within expression strings, the character offset (0-based) and length of the problematic span.
- **Severity**: `error` (blocks processing), `warning` (non-blocking but potentially incorrect), `info` (informational).
- **Code**: a machine-readable error code (e.g., `E001` for undeclared tensor, `E002` for arity mismatch, `W001` for unused declaration).

Example diagnostic output:

```
error[E004]: contracted index 'a' has same variance in both slots
  --> tensor.R, expr.bad_contraction.result, chars 4-15
  |  R{^a _b ^a _d}
  |     ^^     ^^  both contravariant
  = help: one occurrence must be ^a and the other _a
```

---

## 6. Abstract Syntax Tree (AST)

### 6.1 Node types

The parser produces a tree of typed nodes. Every implementation (Python, Julia, Rust, etc.) should provide equivalent node types.

| Node type         | Fields                                      | Description                          |
|-------------------|---------------------------------------------|--------------------------------------|
| `TensorNode`      | `name`, `indices: Index[]`                  | A single tensor with its indices     |
| `ProductNode`     | `factors: Node[]`                           | Tensor product (with contractions)   |
| `SumNode`         | `terms: Node[]`, `signs: int[]`             | Sum/difference of expressions        |
| `ScalarNode`      | `value: string`                             | Numeric or symbolic scalar           |
| `DerivativeNode`  | `operand: Node`, `kind`, `index: Index`     | Derivative applied to an expression  |
| `CommutatorNode`  | `left: Node`, `right: Node`, `operand: Node`| `[left, right] operand`              |

An `Index` carries four fields: `name: string`, `variance: Contra | Covar`, `deriv: None | Covariant | Partial`, and optionally `type: string` (the index type annotation, e.g., `"Lorentz"`).

### 6.2 JSON serialization

The AST can be serialized to JSON for cross-language interchange. The format follows the MathJSON convention of using JSON arrays as S-expressions, with the operator as the first element:

```json
{
  "declarations": {
    "index_types": [
      { "name": "Lorentz", "dim": 4, "metric": "g" }
    ],
    "tensors": [
      {
        "name": "R",
        "slots": [
          {"var": "contra", "type": "Lorentz"},
          {"var": "covar",  "type": "Lorentz"},
          {"var": "covar",  "type": "Lorentz"},
          {"var": "covar",  "type": "Lorentz"}
        ],
        "symmetry": {
          "type": "riemann",
          "bsgs": {
            "base": [0, 2],
            "generators": [
              {"perm": [1,0,2,3], "sign": -1},
              {"perm": [0,1,3,2], "sign": -1},
              {"perm": [2,3,0,1], "sign":  1}
            ]
          }
        }
      }
    ]
  },
  "expression": ["Contract",
    ["Product",
      ["Tensor", "R", [
        {"name":"a", "var":"contra"},
        {"name":"b", "var":"covar"},
        {"name":"c", "var":"covar"},
        {"name":"d", "var":"covar"}
      ]],
      ["Tensor", "g", [
        {"name":"b", "var":"contra"},
        {"name":"d", "var":"contra"}
      ]]
    ],
    {"pairs": [["b","b"], ["d","d"]]}
  ]
}
```

The JSON representation is intended for machine interchange only — humans write TOML and string expressions. Tools should provide bidirectional conversion: `toml2json` and `json2toml`.

---

## 7. Cross-language usage

> **Note:** The following examples illustrate the **intended API** for future implementations. A proof-of-concept Python parser (`tensor_dsl.py`) is available as a reference implementation; full-featured implementations for other languages are planned but not yet released.

### 7.1 Python

```python
# Proposed API — reference implementation available
from tensor_dsl import TensorSpec

spec = TensorSpec.from_toml("schwarzschild.tensor.toml")

# Parse and manipulate symbolically
expr = spec.parse("R{^a _b _c _d} * g{^b ^d}")
expr.canonicalize()
print(expr.to_latex())        # Ric^{a}{}_{d}

# Evaluate numerically
chart = spec.chart("spherical")
components = expr.to_components(chart, parameters={"M": 1.0})
print(components)             # numpy array
```

### 7.2 Julia

```julia
# Proposed API — not yet implemented
using TensorDSL

spec = load("schwarzschild.tensor.toml")

# Macro-based expression entry
@tensor spec R[^a, _b, _c, _d] * g[^b, ^d]

# Or string-based
expr = parse_expr(spec, "R{^a _b _c _d} * g{^b ^d}")
canonicalize!(expr)
to_einsum(expr)               # "abcd,bd->ac"
```

### 7.3 Rust

```rust
// Proposed API — not yet implemented
use tensor_dsl::TensorSpec;

let spec = TensorSpec::from_toml("schwarzschild.tensor.toml")?;
let expr = spec.parse_expr("R{^a _b _c _d} * g{^b ^d}")?;
let canonical = expr.canonicalize(&spec)?;
println!("{}", canonical.to_latex());
```

### 7.4 JavaScript / TypeScript

```typescript
// Proposed API — not yet implemented
import { TensorSpec } from 'tensor-dsl';

const spec = TensorSpec.fromTOML(fs.readFileSync('schwarzschild.tensor.toml', 'utf8'));
const expr = spec.parseExpr('R{^a _b _c _d} * g{^b ^d}');
console.log(expr.toJSON());    // JSON AST for interchange
console.log(expr.toLatex());   // LaTeX string
```

### 7.5 JSON interchange

Any TOML file can be losslessly converted to JSON for transport over APIs, storage in databases, or consumption by languages without TOML parsers:

```bash
# Using any TOML-to-JSON converter
toml2json schwarzschild.tensor.toml > schwarzschild.tensor.json
```

The JSON form is semantically identical. Round-tripping `TOML → JSON → TOML` preserves all information (comments and formatting are lost, as expected).

---

## 8. Comparison with existing systems

### 8.1 Syntax comparison

The same expression — contracting the Riemann tensor to get the Ricci tensor (`Ric_{bd} = R^a{}_{bad}`) — written in each system:

| System       | Syntax                                        | Notes                              |
|--------------|-----------------------------------------------|------------------------------------|
| **TensorDSL**| `R{^a _b _a _d}`                             | Self-contained, parseable          |
| xAct         | `RiemannCD[a, -b, -a, -d]`                   | Mathematica-specific               |
| Cadabra      | `R^{a}_{b a d}`                               | LaTeX-based, needs Python runtime  |
| SymPy        | `R(a, -b, -a, -d)`                            | Python-specific                    |
| einsum       | `einsum('abcd,ac->bd', R, g)`                  | Concrete only, no abstract indices |
| ITensor      | `R * delta`  (by shared Index objects)         | Julia-specific, no string syntax   |
| LaTeX        | `R^{a}{}_{bad}`                                | Display only, not computable       |
| OpenMath     | `<OMA><OMS cd="tensor1"...>...`               | Extremely verbose XML              |

### 8.2 Feature matrix

| Capability                      | TensorDSL | xAct | Cadabra | SymPy | einsum | ITensor | LaTeX |
|---------------------------------|-----------|------|---------|-------|--------|---------|-------|
| Abstract indices                | ✓         | ✓    | ✓       | ✓     | ✗      | partial | ✗     |
| Concrete indices                | ✓         | ✓    | ✓       | ✓     | ✓      | ✓       | ✗     |
| Symmetry declarations           | ✓         | ✓    | ✓       | ✓     | ✗      | ✗       | ✗     |
| Monoterm canonicalization       | ✓         | ✓    | ✓       | ✓     | ✗      | ✗       | ✗     |
| Multi-term identities           | ✓ (rules) | ✓    | ✓       | partial| ✗      | ✗       | ✗     |
| Covariant derivatives           | ✓         | ✓    | ✓       | partial| ✗      | ✗       | ✗     |
| Numerical evaluation            | ✓         | ✓    | ✗       | ✓     | ✓      | ✓       | ✗     |
| Language-agnostic               | ✓         | ✗    | ✗       | ✗     | partial| ✗       | ✓     |
| Serializable (JSON/TOML)        | ✓         | ✗    | ✗       | ✗     | ✗      | ✗       | ✗     |
| Multi-file composition          | ✓         | ✗    | ✗       | ✗     | ✗      | ✗       | ✗     |
| Human-writable                  | ✓         | ✓    | ✓       | ✓     | ✓      | ✓       | ✓     |

TensorDSL occupies the gap: more expressive than einsum (abstract indices, symmetries, derivatives), more portable than xAct/SymPy/Cadabra (language-neutral), more compact than OpenMath (human-writable), and computationally meaningful (unlike LaTeX).

---

## 9. Appendices

### A. Built-in symmetry expansion table

Slot positions correspond to the order of the `indices` array in the tensor declaration. For `indices = ["_a", "_b", "_c", "_d"]`: position 0 = `_a`, position 1 = `_b`, position 2 = `_c`, position 3 = `_d`.

| Shorthand                  | BSGS Base | Generators (perm, sign)                                                |
|----------------------------|-----------|------------------------------------------------------------------------|
| `sym(0, 1)`                | `[0]`     | `([1,0], +1)`                                                         |
| `asym(0, 1)`               | `[0]`     | `([1,0], -1)`                                                         |
| `sym(0, 1, 2)`             | `[0, 1]`  | `([1,0,2], +1)`, `([0,2,1], +1)`                                      |
| `asym(0, 1, 2)`            | `[0, 1]`  | `([1,0,2], -1)`, `([0,2,1], -1)`                                      |
| `riemann(0, 1, 2, 3)`     | `[0, 2]`  | `([1,0,2,3], -1)`, `([0,1,3,2], -1)`, `([2,3,0,1], +1)`              |
| `cyclic(0, 1, 2)`          | `[0]`     | `([1,2,0], +1)`                                                       |
| `block_sym([0,1], [2,3])`  | `[0]`     | `([2,3,0,1], +1)`                                                     |

### B. Reserved tensor names

The following names have special meaning and should not be used for user-defined tensors without matching semantics:

`delta` (Kronecker delta), `epsilon` (Levi-Civita symbol), `g` (metric, when used with a metric declaration), `R` (Riemann, when `role = "curvature"`), `Ric` (Ricci), `RicciScalar` (Ricci scalar), `G` (Einstein tensor), `Weyl` (Weyl tensor), `Christoffel` (connection coefficients).

These names are not hard-reserved — they can be redefined — but parsers may issue warnings if a tensor named `R` does not have Riemann symmetry, for example.

### C. Unicode index recommendations

For maximum readability in modern editors and terminals:

| Index type       | Recommended labels                         |
|------------------|--------------------------------------------|
| Spacetime (4D)   | `a b c d e f g h` or `μ ν ρ σ α β γ δ`   |
| Spatial (3D)     | `i j k l m n` or `α β γ`                  |
| Spinor           | `A B C D` (upper) / `Ȧ Ḃ Ċ Ḋ` (dotted)  |
| Internal (gauge) | `I J K L` or `a̲ b̲ c̲` (underlined)        |
| Frame/tetrad     | `â b̂ ĉ d̂` (hatted)                        |

ASCII fallbacks (`a-h`, `i-n`, `A-D`) are always valid.

### D. File structure summary

```toml
[meta]                    # File metadata and versioning (optional)
[imports]                 # Multi-file composition (optional)
[manifold.<n>]            # Manifold declarations
[index_type.<n>]          # Index type declarations
[metric.<n>]              # Metric declarations
[derivative.<n>]          # Derivative operator declarations
[tensor.<n>]              # Tensor declarations (core)
[chart.<n>]               # Coordinate chart declarations
[components.<n>]          # Concrete component values
[expr.<n>]                # Named expressions
[rule.<n>]                # Rewrite rules
[backend.<n>]             # Backend configuration
```

All sections are optional. A minimal valid file contains at least one `[tensor.*]` entry. Parsers should emit a warning for files with no tensor declarations.

### E. Conformance test cases

Implementations should pass the following test cases to be considered conformant. Each case specifies an input expression and the expected result.

**Positive cases (must parse and validate):**

```
E01: "R{^a _b _a _d}" with Riemann declaration
     → TensorNode with free indices [_b, _d], contracted pair (0,2)

E02: "R{^a _b _c _d} * g{^b ^d}"
     → ProductNode, einsum lowering: "abcd,bd->ac"

E03: "T{^a _b ;c}"
     → TensorNode with derivative index ;c (covariant)

E04: "T{^a _b ;c ;d}"
     → Two derivative indices, ;c applied first (inner), ;d second (outer)

E05: "Ric{_a _b} - (1/2) * g{_a _b} * RicciScalar"
     → SumNode with two terms, free indices [_a, _b] on both

E06: "phi" where phi declared with indices = []
     → ScalarNode (bare name, no braces needed)

E07: "phi{}" where phi declared with indices = []
     → ScalarNode (explicit empty braces, equivalent to E06)

E08: "T{^a:Lorentz _b:Gauge}" with overlapping label pools
     → TensorNode with type-annotated indices, no ambiguity error

E09: "(T{^a _b} * S{^b _a}) * V{^c _c}"
     → Valid: 'a' and 'b' contract in first scope, 'c' in second scope

E10: "R{_a _b _c _d}" where R declared as ["^a","_b","_c","_d"]
     → Valid: first index lowered by metric (variance flexibility)
```

**Negative cases (must produce errors):**

```
N01: "R{^a _b ^a _d}"
     → Error E004: contracted index 'a' has same variance (both contra)

N02: "T{^a _b} + S{^a _b _c}"
     → Error E005: free index mismatch in sum (rank 2 vs rank 3)

N03: "Unknown{^a _b}" with no declaration for "Unknown"
     → Error E001: undeclared tensor

N04: "R{^a _b}" where R declared with 4 indices
     → Error E002: arity mismatch (2 provided, 4 expected)

N05: "T{^a:FakeType _b}" with no index type "FakeType"
     → Error E003: unknown index type annotation
```

---

## 10. Changelog

### v0.1.0 (initial release)

- Initial specification covering: TOML declaration layer (13 table types), expression DSL with EBNF grammar, symmetry system with BSGS, AST node types, JSON serialization, evaluation pipeline, and cross-language usage examples.
- Proof-of-concept Python parser (`tensor_dsl.py`) available as reference implementation.

---

*TensorDSL specification v0.1.0. This document follows semantic versioning (§1.6). Proposed changes should be submitted as issues or pull requests to the specification repository. Breaking changes require a MAJOR version bump.*
