# Documentation Plan for sxAct Migration Project

**Date:** 2026-01-22
**Version:** 1.0
**Status:** Draft

## 1. Overview

This document outlines the plan for creating comprehensive documentation for the sxAct migration project. The documentation will cater to three main audiences: end-users, contributors/developers, and project stakeholders.

The documentation will be written in Markdown and hosted alongside the code in the project's repository.

## 2. Documentation Structure

The documentation will be organized into three main categories:

### 2.1. User Documentation

This documentation is aimed at users who want to use the Julia package or the Python wrapper in their own projects.

*   **Installation Guide:**
    *   Instructions for installing the Julia package using `Pkg`.
    *   Instructions for installing the Python wrapper using `pip`.
    *   Details on dependencies and prerequisites (e.g., Julia version, Python version).

*   **Getting Started Guide:**
    *   A step-by-step tutorial that walks users through the basic functionality.
    *   Defining a manifold, tensors, and performing a simple calculation.
    *   Showcasing the differences between the Julia and Python APIs.

*   **User Guide:**
    *   In-depth explanation of core concepts (manifolds, tensors, indices, symmetries).
    *   Detailed guides for each of the main modules (`xCore`, `xPerm`, `xTensor`, etc.).
    *   Cookbook-style examples for common tasks (e.g., calculating curvature, working with perturbations).

*   **API Reference:**
    *   Automatically generated API documentation for both the Julia and Python libraries.
    *   For Julia, we will use `Documenter.jl`.
    *   For Python, we will use `Sphinx` or a similar tool.

### 2.2. Developer Documentation

This documentation is aimed at developers who want to contribute to the project.

*   **Contributor Guide (`CONTRIBUTING.md`):**
    *   Code of Conduct.
    *   Instructions for setting up the development environment.
    *   Coding style guide (e.g., Julia style guide, Black for Python).
    *   Pull request process.
    *   How to run the tests.

*   **Architectural Overview:**
    *   A high-level description of the project's architecture.
    *   The structure of the Julia core.
    *   The design of the Python wrapper and its interaction with the Julia core (e.g., using `PythonCall.jl`).
    *   Explanation of the three-layer testing architecture.

*   **Testing Framework Guide:**
    *   How to write new tests using the TOML format.
    *   How to run the tests against the different targets (Wolfram, Julia, Python).
    *   How to add new test cases and properties.
    *   How to update the oracle snapshots.

### 2.3. Project Documentation

This documentation provides general information about the project.

*   **README (`README.md`):**
    *   Project description and goals.
    *   Quick links to the documentation, installation guide, and contributing guide.
    *   A simple example to showcase the library's usage.
    *   Badges for CI status, code coverage, etc.

*   **Changelog (`CHANGELOG.md`):**
    *   A manually maintained log of changes for each release, following the Keep a Changelog format.

*   **Roadmap:**
    *   A high-level overview of the project's future plans and priorities.
    *   This could be part of the `README.md` or a separate file.

## 3. Tooling

*   **Markdown:** All documentation will be written in Markdown.
*   **`Documenter.jl`:** For generating the Julia API reference.
*   **`Sphinx`:** For generating the Python API reference.
*   **GitHub Pages:** For hosting the documentation website.

## 4. Implementation Plan

The documentation will be developed iteratively alongside the code.

1.  **Phase 1: Foundation (Sprint 1-2)**
    *   Create the initial `README.md` and `CONTRIBUTING.md` files.
    *   Set up the basic structure for the documentation website.
    *   Write the Installation Guide.

2.  **Phase 2: Core Documentation (Sprint 3-4)**
    *   Write the Getting Started Guide.
    *   Write the User Guide for `xCore`, `xPerm`, and `xTensor`.
    *   Set up the auto-generation of the API reference for the core modules.
    *   Write the Architectural Overview.

3.  **Phase 3: Comprehensive Documentation (Sprint 5-6)**
    *   Write the User Guide for the remaining modules.
    *   Complete the API reference for all modules.
    *   Write the Testing Framework Guide.
    *   Create the Changelog and Roadmap.

4.  **Phase 4: Review and Refine (Ongoing)**
    *   Continuously review and improve the documentation based on user feedback.
    *   Ensure the documentation stays up-to-date with the code.

## 5. Initial Issues

The following issues will be created in the issue tracker to kickstart the documentation effort:

*   **doc-001:** Create initial `README.md` and `CONTRIBUTING.md` files.
*   **doc-002:** Set up documentation website with GitHub Pages.
*   **doc-003:** Write Installation Guide.
*   **doc-004:** Write Getting Started Guide.
*   **doc-005:** Set up API reference generation for Julia and Python.
