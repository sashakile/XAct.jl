"""Centralized registry of Julia function names used by the adapter.

All qualified Julia paths (e.g. ``XTensor.ToCanonical``) are defined here
so renaming or moving a Julia function requires changing only one place.
"""

# XTensor module functions
DEF_MANIFOLD = "XTensor.def_manifold!"
DEF_METRIC = "XTensor.def_metric!"
DEF_TENSOR = "XTensor.def_tensor!"
DEF_BASIS = "XTensor.def_basis!"
DEF_CHART = "XTensor.def_chart!"
DEF_PERTURBATION = "XTensor.def_perturbation!"

TO_CANONICAL = "XTensor.ToCanonical"
CONTRACT = "XTensor.Contract"
SIMPLIFY = "XTensor.Simplify"
COMMUTE_COVDS = "XTensor.CommuteCovDs"
SORT_COVDS = "XTensor.SortCovDs"
PERTURB = "XTensor.perturb"
PERTURB_CURVATURE = "XTensor.perturb_curvature"
PERTURBATION_ORDER = "XTensor.PerturbationOrder"
PERTURBATION_AT_ORDER = "XTensor.PerturbationAtOrder"
CHECK_METRIC_CONSISTENCY = "XTensor.CheckMetricConsistency"
IBP = "XTensor.IBP"
TOTAL_DERIVATIVE_Q = "XTensor.TotalDerivativeQ"
VARD = "XTensor.VarD"
TENSOR_Q = "XTensor.TensorQ"
COLLECT_TENSORS = "XTensor.CollectTensors"
ALL_CONTRACTIONS = "XTensor.AllContractions"
SYMMETRY_OF = "XTensor.SymmetryOf"
MAKE_TRACE_FREE = "XTensor.MakeTraceFree"

# xCoba functions
SET_BASIS_CHANGE = "XTensor.set_basis_change!"
CHANGE_BASIS = "XTensor.ChangeBasis"
GET_JACOBIAN = "XTensor.get_jacobian"
BASIS_CHANGE_Q = "XTensor.BasisChangeQ"
SET_COMPONENTS = "XTensor.set_components!"
GET_COMPONENTS = "XTensor.get_components"
COMPONENT_VALUE = "XTensor.ComponentValue"
CTENSOR_Q = "XTensor.CTensorQ"
TO_BASIS = "XTensor.ToBasis"
FROM_BASIS = "XTensor.FromBasis"
TRACE_BASIS_DUMMY = "XTensor.TraceBasisDummy"
CHRISTOFFEL = "XTensor.christoffel!"

# XInvar functions
RIEMANN_SIMPLIFY = "XTensor.RiemannSimplify"

# XCore / state management
RESET_STATE = "xAct.reset_state!()"
