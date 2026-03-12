"""sxAct adapter interface.

Each CAS backend (Wolfram, Julia, Python) is implemented as a subclass of
:class:`~xact.adapter.base.TestAdapter`.
"""

from xact.adapter.base import (
    AdapterError,
    EqualityMode,
    NormalizedExpr,
    TestAdapter,
    VersionInfo,
)
from xact.adapter.julia_stub import JuliaAdapter
from xact.adapter.python_stub import PythonAdapter
from xact.adapter.wolfram import WolframAdapter

__all__ = [
    "AdapterError",
    "EqualityMode",
    "JuliaAdapter",
    "NormalizedExpr",
    "PythonAdapter",
    "TestAdapter",
    "VersionInfo",
    "WolframAdapter",
]
