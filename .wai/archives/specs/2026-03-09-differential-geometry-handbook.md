# Specification: sxAct Handbook of Differential Geometry

**Date:** 2026-03-09
**Status:** DRAFT
**Target:** `docs/handbook/`

## 1. Objective & Audience
The **sxAct Handbook of Differential Geometry** serves as the definitive bridge between abstract mathematical theory and the high-performance Julia implementation of the `xAct` suite. It is designed to be both a mathematical reference and a developer's guide to the computational engine.

### Audience
*   **Physics Researchers:** Who need to understand how their analytical GR derivations map to `sxAct` code.
*   **Software Engineers:** Who understand the code but need the geometric intuition behind the tensor algebra and permutation group algorithms.
*   **Validators:** Who use the "Oracle" to prove parity between Wolfram and Julia.

---

## 2. Content Structure (The Five Pillars)

### Pillar I: The Geometric Foundation (`Def` Layer)
Maps "World Building" functions in `xAct` to the structural types in `XTensor.jl`.
*   **Manifolds & Vector Bundles:** The topology of `DefManifold`. Representation of `VBundles` (tangent spaces) in Julia.
*   **Abstract Index Notation:** The Penrose formalism. Managing index "slots" vs. component markers. Strategies for avoiding index collisions.
    *   *Example:* $v^a$ (Abstract slot label) vs. $v^i$ (Coordinate component $i \in \{1..n\}$).
*   **Metrics & Causal Structure:** Defining signatures (Lorentzian vs. Riemannian). How `DefMetric` auto-generates inverse metrics, determinants, and standard connections.

### Pillar II: The Permutation Engine (`XPerm` Layer)
Explains the group theory used to simplify tensors (the "Heart of the Machine").
*   **Slot Symmetries:** Representing $T_{ab} = T_{ba}$ as a permutation group element. Signed permutations for standard parity/antisymmetry (e.g., Riemann tensor).
*   **Graded Symmetry Note:** Distinction between `XPerm` signed permutations and the future `FieldsX` implementation for Grassmann-odd (fermionic) graded algebra.
*   **The Butler-Portugal Algorithm:** A step-by-step guide to how `sxAct` finds the "Canonical Representative" of a tensor expression using coset representatives.
*   **Schreier-Sims & BSGS:** Efficient storage and search of symmetry groups for high-rank tensors (Riemann, 3.5PN terms).

### Pillar III: Differential Calculus (`CovD` & Curvature)
The transition from algebra to calculus.
*   **Connections & Covariant Derivatives:** The Levi-Civita connection (metric compatible) and support for general connections.
*   **The Riemann & Ricci Tensors:** Deriving curvature from the commutator of covariant derivatives.
*   **Commutation Rules:** Implementing the identity $[\nabla_a, \nabla_b] v^c = R^c_{dab} v^d$ in the `CommuteCovDs` system.
*   **Bianchi Identities:** Using the first and second Bianchi identities for expression simplification and validation.
*   **Oracle Verification:** Every mathematical chapter concludes with a section demonstrating how its identities are validated against the Wolfram Oracle.

### Pillar IV: Specialized Physics Modules (Roadmap)
Roadmap for the extended libraries and their geometric foundations.
*   **Perturbation Theory (`xPert`):** Combinatorial logic of expanding $g_{\mu\nu}$ and curvature tensors around a background.
*   **Coordinate & Frame Calculus (`xCoba`):** Transitioning from abstract indices to concrete coordinate charts and non-coordinate bases (Tetrads/Frames).
*   **Variational Calculus (`xTras`):** Deriving field equations from actions using integration by parts (IBP) and variational derivatives (`VarD`).
*   **Spinors:** The 2-spinor formalism and the Newman-Penrose/GHP equations.

### Pillar V: The Validation Manual
*   **The Oracle Pattern:** Using Dockerized Wolfram Engines to verify Julia results.
*   **Elegua Orchestration:** Integration with the `Elegua` multi-tier test harness for system-wide conformance.
*   **Normalization & Comparison:** Writing "Conformant" test cases that prove mathematical correctness.
*   **Regression Suite:** Mapping `tests/xtensor/*.toml` to specific geometric identities.

---

## 3. Technical Implementation & Format
*   **Format:** Markdown-based (compatible with MkDocs/Material).
*   **Mathematical Rendering:** MathJax/KaTeX for LaTeX formulas.
*   **Automated Code Sync:** Use of `Literate.jl` or a markdown-include mechanism to pull live code snippets from `src/julia/` to ensure documentation parity.
*   **Interactive Examples:** Provision of `notebooks/` (Jupyter or Pluto.jl) corresponding to each handbook chapter.

## 4. Documentation Standards
*   **Theorem/Implementation Mapping:** Every mathematical identity (e.g., Ricci Scalar definition) must be accompanied by the `sxAct` function that computes it (`RicciScalarCD`).
*   **Complexity Notes:** For `XPerm` sections, include Big-O complexity notes for the canonicalization of different tensor types.
*   **Visuals:** Use TikZ or SVG diagrams to illustrate parallel transport, manifold charts, and light-cones.

## 5. Maintenance & Lifecycle
*   **Versioning:** The handbook must be versioned in sync with the `Project.toml` of `sxAct`.
*   **Documentation Testing Strategy:**
    *   Snippets are extracted via `Literate.jl`.
    *   A dedicated `tests/docs/` runner verifies all snippets against the `Oracle` to prevent mathematical drift.
    *   This runner is decoupled from the main `pytest` path to avoid blocking core logic development on documentation formatting errors.
*   **Contribution Policy:** New features in `XTensor.jl` (e.g., adding `LieD`) are considered "Incomplete" until the corresponding Handbook entry is drafted.

---

## 6. Appendix: Math-to-Code Quick Reference
A tabular mapping of standard `xAct` Wolfram commands to their `sxAct` Julia/Python equivalents.
*   **Scope:** Initial priority on `XCore`, `XPerm`, and `XTensor` foundational commands.
