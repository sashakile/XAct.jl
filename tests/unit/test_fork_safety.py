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

"""Tests for fork-safety guard in xact.xcore._runtime.

Verifies that accessing the Julia runtime from a forked child process
raises a clear RuntimeError instead of silently producing wrong results.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_check_fork_safety_same_process():
    """_check_fork_safety() must NOT raise when PID has not changed."""
    import xact.xcore._runtime as rt

    orig_pid = rt._init_pid
    try:
        rt._init_pid = 12345
        with patch("xact.xcore._runtime.os.getpid", return_value=12345):
            # Should not raise
            rt._check_fork_safety()
    finally:
        rt._init_pid = orig_pid


def test_check_fork_safety_different_pid_raises():
    """_check_fork_safety() must raise RuntimeError when PID differs."""
    import xact.xcore._runtime as rt

    orig_pid = rt._init_pid
    try:
        rt._init_pid = 12345
        with patch("xact.xcore._runtime.os.getpid", return_value=99999):
            with pytest.raises(RuntimeError, match="fork"):
                rt._check_fork_safety()
    finally:
        rt._init_pid = orig_pid


def test_check_fork_safety_not_initialized():
    """_check_fork_safety() must NOT raise when _init_pid is None (not yet initialized)."""
    import xact.xcore._runtime as rt

    orig_pid = rt._init_pid
    try:
        rt._init_pid = None
        # Should not raise regardless of PID
        rt._check_fork_safety()
    finally:
        rt._init_pid = orig_pid


def test_error_message_suggests_alternatives():
    """The fork-safety error message should mention 'spawn' and 'threading'."""
    import xact.xcore._runtime as rt

    orig_pid = rt._init_pid
    try:
        rt._init_pid = 12345
        with patch("xact.xcore._runtime.os.getpid", return_value=99999):
            with pytest.raises(RuntimeError, match="spawn") as exc_info:
                rt._check_fork_safety()
            msg = str(exc_info.value)
            assert "threading" in msg
            assert "12345" in msg
            assert "99999" in msg
    finally:
        rt._init_pid = orig_pid


def test_get_julia_calls_fork_check():
    """get_julia() must call _check_fork_safety() before returning."""
    import xact.xcore._runtime as rt

    orig_jl = rt._jl
    orig_xcore = rt._xcore
    orig_pid = rt._init_pid
    try:
        rt._jl = MagicMock()
        rt._xcore = MagicMock()
        rt._init_pid = 12345

        with patch("xact.xcore._runtime.os.getpid", return_value=99999):
            with pytest.raises(RuntimeError, match="fork"):
                rt.get_julia()
    finally:
        rt._jl = orig_jl
        rt._xcore = orig_xcore
        rt._init_pid = orig_pid


def test_get_xcore_calls_fork_check():
    """get_xcore() must call _check_fork_safety() before returning."""
    import xact.xcore._runtime as rt

    orig_jl = rt._jl
    orig_xcore = rt._xcore
    orig_pid = rt._init_pid
    try:
        rt._jl = MagicMock()
        rt._xcore = MagicMock()
        rt._init_pid = 12345

        with patch("xact.xcore._runtime.os.getpid", return_value=99999):
            with pytest.raises(RuntimeError, match="fork"):
                rt.get_xcore()
    finally:
        rt._jl = orig_jl
        rt._xcore = orig_xcore
        rt._init_pid = orig_pid


def test_init_julia_records_pid():
    """_init_julia() must set _init_pid to the current PID on success."""
    import xact.xcore._runtime as rt

    orig_jl = rt._jl
    orig_xcore = rt._xcore
    orig_pid = rt._init_pid
    try:
        rt._jl = None
        rt._xcore = None
        rt._init_pid = None

        mock_main = MagicMock()
        mock_xact = MagicMock()
        mock_main.XAct = mock_xact
        mock_main.seval.return_value = None

        with patch.dict("sys.modules", {"juliacall": MagicMock(Main=mock_main)}):
            with patch("xact.xcore._runtime.os.getpid", return_value=42):
                rt._init_julia()

        assert rt._init_pid == 42, "_init_pid should be set to current PID after init"
    finally:
        rt._jl = orig_jl
        rt._xcore = orig_xcore
        rt._init_pid = orig_pid
