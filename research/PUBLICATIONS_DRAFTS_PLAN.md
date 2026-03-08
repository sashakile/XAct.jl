# Plan: Publication Drafting for Eleguá + Chacana

This plan organizes the drafting of two distinct academic papers based on the research strategies in `CHACANA_PUBLICATION_STRATEGY.md` and `PUBLICATION_STRATEGY.md`.

## 1. Paper Roadmap

| Title (Working) | Primary Target | Domain | Status |
| :--- | :--- | :--- | :--- |
| **Chacana: A Machine-Parseable Penrose Notation for the 21st Century** | SLE / Onward! / arXiv (Vision Paper) | Computer Science (PL) | **Drafting + Prototype** |
| **Eleguá: A Domain-Agnostic Orchestrator for Symbolic Verification** | CPC (Comp. Phys. Comm.) | Physics (Symbolics) | **Pending Benchmarks** |

---

## 2. Draft Structure: Chacana (The Language Paper)
**Focus**: The DSL, the Static Type System, and the Bridge Architecture.

### I. Introduction
*   **The Notation-Computation Gap**: How tensor calculus notation in physics is unified, but computational tools are fragmented.
*   **The Contribution**: A language-agnostic specification (TOML + Micro-syntax) with a novel static index type system.

### II. Related Work & Design Philosophy
*   **Literature Review**: Contrast Chacana's type system with existing "Array DSL" type systems (e.g., TACO, F#, Dex).
*   **Design Philosophy**: Separation of Notation from Implementation; the Andean "Chacana" Bridge concept.

### III. The Chacana Specification
*   **The Context (Γ)**: Manifolds, Tensors, and Metrics in TOML.
*   **The Micro-syntax**: Abstract indices, Spinors, and Exterior Algebra.
*   **The Perturbation Operator (@)**: Handling ε-expansions.

### IV. The Static Index Type System
*   **Typing Judgments**: Formal rules for contraction and free index invariance.
*   **Metric-Aware Validation**: How the type system prevents "Metric-less" contractions.
*   **Safety across Orders**: Verification of compatible index types in perturbation theory.

### V. Implementation & Portability
*   **Minimal Prototype**: Presenting `chacana-spec-py` (Parser + Type Checker) as evidence of feasibility.
*   **The ValidationToken (JSON AST)**: Proving 1:1 interchange between Python, Julia, and Rust.
*   **Case Study: Schwarzschild Metric**: Demonstrating AST consistency across languages (chosen for its complex index structure).

---

## 3. Draft Structure: Eleguá (The Infrastructure Paper)
**Focus**: The "Infrastructure of Trust" and the sxAct-to-Julia migration.

### I. Introduction
*   **The Migration Crisis**: The risk of mathematical drift when porting proprietary symbolic libraries (xAct) to open ecosystems.
*   **Eleguá**: A domain-agnostic orchestrator for proving mathematical parity.

### II. The Multi-Tier Verification Strategy
*   **Tier 1 (Wolfram xAct)**: The Ground Truth Oracle.
*   **Tier 2 (xAct-jl)**: The Mirror Oracle (Julia).
*   **Tier 3 (Chacana-jl)**: The Native Performance Engine.
*   **Snapshot-Only Mode**: Enabling Oracle-free verification for the open-source community via cached results.

### III. The 4-Layer Comparison Pipeline
*   Identity, Structural, Canonical (Butler-Portugal), and **Probabilistic Verification** (Numerical Jittered Sampling).
*   **Case Study: The First Bianchi Identity**: Chosen to demonstrate why symbolic normalization is often insufficient and why probabilistic sampling is a necessary mathematical fallback.

### IV. Isolation & Resilience
*   **The "Mathematica Problem"**: Solving symbol pollution via Context-level isolation and periodic kernel resets.
*   **Handling Large Payloads**: The Blob-Store reference-by-hash pattern for expressions >1MB.

### V. Results: Migrating the Butler Suite
*   **Benchmark Suite**: 82 Butler examples covering the full `xPerm` API.
*   **Metrics**: Execution Time (Mathematica vs. JIT Julia), Memory consumption, and Mathematical Parity rate.

---

## 4. Next Steps
1.  [ ] **Implement `chacana-spec-py` Prototype**: Build the parser + type checker to ground the "Meat" of the Chacana paper.
2.  [ ] **Draft Chacana Sections I, II, & IV** (Intro, Lit Review, and Type System).
3.  [ ] **Execute Butler Benchmarks**: Gather metrics for Eleguá Section V.
4.  [ ] **Formalize Probabilistic Sampling Error Bounds**: Define the success criteria for Layer 4 jittering.
