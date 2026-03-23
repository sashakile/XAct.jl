"""Tests for xact.xcore._runtime initialization safety (sxAct-ew7y).

Verifies that partial init failure does not leave the module in a
half-initialized state (_jl set, _xcore None).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_failed_init_resets_jl():
    """If xAct loading fails, _jl must be reset to None so retries work cleanly."""
    import xact.xcore._runtime as rt

    # Save originals
    orig_jl = rt._jl
    orig_xcore = rt._xcore

    try:
        # Reset state
        rt._jl = None
        rt._xcore = None

        mock_main = MagicMock()
        mock_main.seval.side_effect = RuntimeError("xAct load failed")

        with patch.dict("sys.modules", {"juliacall": MagicMock(Main=mock_main)}):
            with pytest.raises(ImportError):
                rt._init_julia()

        # After failure, _jl must be None (not half-set)
        assert rt._jl is None, "_jl should be None after failed init"
        assert rt._xcore is None, "_xcore should be None after failed init"
    finally:
        # Restore originals
        rt._jl = orig_jl
        rt._xcore = orig_xcore


def test_successful_init_sets_both():
    """On success, both _jl and _xcore must be set."""
    import xact.xcore._runtime as rt

    orig_jl = rt._jl
    orig_xcore = rt._xcore

    try:
        rt._jl = None
        rt._xcore = None

        mock_main = MagicMock()
        mock_xact = MagicMock()
        mock_main.xAct = mock_xact
        mock_main.seval.return_value = None

        with patch.dict("sys.modules", {"juliacall": MagicMock(Main=mock_main)}):
            rt._init_julia()

        assert rt._jl is not None
        assert rt._xcore is not None
    finally:
        rt._jl = orig_jl
        rt._xcore = orig_xcore
