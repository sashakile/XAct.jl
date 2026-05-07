# Branding and Relationship to Upstream xAct

This document records the naming and branding strategy for XAct.jl and its relationship to the upstream Wolfram xAct project.

## The Decision: Keep XAct.jl

Following an external review of the project's positioning for JOSS (Journal of Open Source Software), the project team (AI and human) decided to retain the name **XAct.jl**.

### Rationale

1.  **Community Convention**: It is a standard practice in the Julia ecosystem to name ports or interfaces to existing libraries as `LibraryName.jl`.
2.  **Discoverability**: Users searching for "xAct in Julia" or "Julia xAct" are most likely to find and identify the project if it shares the name of the original engine.
3.  **Intent**: The project's goal is to provide a high-fidelity port of the xAct algorithms. Using the same name (with the `.jl` suffix) accurately reflects this intent.

## Disambiguation Strategy

To avoid confusion between this Julia implementation and the original Wolfram Mathematica package, the following disambiguation rules are applied across all documentation, papers, and code:

1.  **Explicit Naming**:
    *   Refer to the original as **Wolfram xAct** or **upstream xAct**.
    *   Refer to this project as **XAct.jl** or **the Julia port**.
2.  **Prominent Subtitles**: README and documentation landing pages must include a subtitle or tagline identifying the project as a "Julia port" or "Julia implementation".
3.  **The "What is What?" Map**: Maintain a consistent mapping table in the README and Docs that explicitly contrasts Wolfram xAct with XAct.jl components.
4.  **Citations**: Always cite the original xAct papers (e.g., Martín-García 2008) and acknowledge the original authors in the introductory sections of all major documentation and papers.

## Mapping Table

| Name | Kind | Role |
| :--- | :--- | :--- |
| **Wolfram xAct** | Upstream Project | The original tensor algebra suite for Mathematica |
| **XAct.jl** | Repository / Package | The native Julia tensor algebra engine |
| **xact-py** | Python Package | The PyPI distribution of the Python wrapper |
| **xact** | Python Import | The Python API for users |
| **sxact** | Verification Stack | Tooling for parity testing against the Wolfram oracle |

## Future Considerations

If a rename is ever required for legal or community-clarity reasons, the project will adopt the name **sxAct** (derived from "Simulated/Symbolic xAct" or "sasha's xAct"), but XAct.jl remains the primary brand for the current release phase.
