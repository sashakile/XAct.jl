# sxAct — xAct Migration & Implementation
# Copyright (C) 2026 sxAct Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""xact-py: Python wrapper for the sxAct Julia core.

Example::

    import xact

    M = xact.Manifold("M", 4, ["a", "b", "c", "d", "e", "f"])
    g = xact.Metric(M, "g", signature=-1, covd="CD")
    T = xact.Tensor("T", ["-a", "-b"], M, symmetry="Symmetric[{-a,-b}]")

    xact.canonicalize("T[-b,-a] - T[-a,-b]")  # "0"
"""

__version__ = "0.3.0"

from xact.api import (  # noqa: E402, F401
    Manifold,
    Metric,
    Perturbation,
    Tensor,
    canonicalize,
    commute_covds,
    contract,
    dimension,
    ibp,
    perturb,
    reset,
    riemann_simplify,
    simplify,
    sort_covds,
    total_derivative_q,
    var_d,
)
from xact.expr import (  # noqa: E402, F401
    AppliedTensor,
    DnIdx,
    Idx,
    TensorHead,
    indices,
    tensor,
)

__all__ = [
    "Manifold",
    "Metric",
    "Tensor",
    "Perturbation",
    "canonicalize",
    "contract",
    "simplify",
    "perturb",
    "commute_covds",
    "sort_covds",
    "ibp",
    "total_derivative_q",
    "var_d",
    "riemann_simplify",
    "reset",
    "dimension",
    # Typed expression layer
    "Idx",
    "DnIdx",
    "TensorHead",
    "AppliedTensor",
    "indices",
    "tensor",
]
