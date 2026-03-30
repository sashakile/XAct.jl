"""
    XTensor

Abstract tensor algebra for the xAct/sxAct system.
Implements DefManifold, DefMetric, DefTensor, ToCanonical, and Contract.

Curvature tensors are auto-created by def_metric!.
Condition evaluation (Assert, Evaluate) is handled in the Python adapter layer.

Reference: specs/2026-03-06-xperm-xtensor-design.md
"""
module XTensor

#! format: off
import ..validate_identifier, ..validate_order
import ..validate_perm, ..validate_disjoint_cycles
#! format: on

include("XPerm.jl")
using .XPerm

using LinearAlgebra: det, inv

# ============================================================
# Exports
# ============================================================

# Type exports
export ManifoldObj, VBundleObj, TensorObj, MetricObj, IndexSpec, SymmetrySpec
export BasisObj, ChartObj

# State management
export reset_state!, Session, reset_session!

# Global registry collections (mutable; exported for MemberQ use in conditions)
export Manifolds, Tensors, VBundles, Perturbations, Bases, Charts

# Def functions
export def_manifold!, def_tensor!, def_metric!, def_perturbation!
export def_basis!, def_chart!

# Accessor functions
export get_manifold, get_tensor, get_vbundle, get_metric, get_basis, get_chart
export list_manifolds, list_tensors, list_vbundles, list_bases, list_charts

# Query predicates (Wolfram-named, used by _wl_to_jl translator)
export ManifoldQ, TensorQ, VBundleQ, MetricQ, CovDQ, PerturbationQ, FermionicQ
export BasisQ, ChartQ
export Dimension, IndicesOfVBundle, SlotsOfTensor
export VBundleOfBasis, BasesOfVBundle, CNumbersOf, PDOfBasis
export ManifoldOfChart, ScalarsOfChart
export MemberQ

# Symbol validation
export ValidateSymbolInSession, set_symbol_hooks!

# Canonicalization and contraction
export ToCanonical, Contract, CommuteCovDs, SortCovDs, Simplify

# Contract support
export SignDetOfMetric

# xPert background metric consistency
export check_metric_consistency, check_perturbation_order

# xPert perturbation order queries
export PerturbationOrder, PerturbationAtOrder
export perturb

# IBP and VarD
export IBP, TotalDerivativeQ, VarD

# xCoba coordinate transformations
export BasisChangeObj
export set_basis_change!, change_basis, Jacobian
export BasisChangeQ, BasisChangeMatrix, InverseBasisChangeMatrix

# xCoba component tensors (CTensor)
export CTensorObj
export set_components!, get_components, ComponentArray
export CTensorQ, component_value, ctensor_contract

# xCoba Christoffel symbols
export christoffel!

# xCoba ToBasis / FromBasis / TraceBasisDummy
export ToBasis, FromBasis, TraceBasisDummy

# Multi-term identity framework
export MultiTermIdentity, RegisterIdentity!

# xTras utilities
export CollectTensors, AllContractions, SymmetryOf, MakeTraceFree

# ============================================================
# Subfiles
# ============================================================

include("XTensor/Core.jl")
include("XTensor/Def.jl")
include("XTensor/Canonical.jl")
include("XTensor/Contract.jl")
include("XTensor/Pert.jl")
include("XTensor/Coba.jl")
include("XTensor/XTras.jl")

end  # module XTensor
