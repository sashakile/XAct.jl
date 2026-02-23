"""sxAct adapter interface.

Each CAS backend (Wolfram, Julia, Python) is implemented as a subclass of
:class:`~sxact.adapter.base.TestAdapter`.
"""

from sxact.adapter.base import (
    AdapterError,
    EqualityMode,
    NormalizedExpr,
    TestAdapter,
    VersionInfo,
)

__all__ = [
    "AdapterError",
    "EqualityMode",
    "NormalizedExpr",
    "TestAdapter",
    "VersionInfo",
]
