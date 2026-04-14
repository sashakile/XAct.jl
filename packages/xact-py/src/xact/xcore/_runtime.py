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

"""Julia runtime singleton for xact.xcore.

Initialises the Julia runtime and loads xAct exactly once per process.
Thread-safe: concurrent first-calls block until initialisation completes.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_jl: Any = None
_xcore: Any = None
_init_pid: int | None = None


def _check_fork_safety() -> None:
    """Raise RuntimeError if the current process is a fork of the one that initialized Julia."""
    if _init_pid is None:
        return
    current_pid = os.getpid()
    if current_pid != _init_pid:
        raise RuntimeError(
            f"xact: Julia runtime was initialized in process {_init_pid} but is "
            f"being accessed from process {current_pid}. This typically happens "
            f"after os.fork() or multiprocessing with fork start method. juliacall "
            f"is not fork-safe and may produce incorrect results or crash. Use "
            f"threading, or multiprocessing with the 'spawn' start method instead."
        )


def get_julia() -> Any:
    """Return the juliacall Main module, initialising Julia if needed."""
    _check_fork_safety()
    _ensure_initialized()
    return _jl


def get_xcore() -> Any:
    """Return the Julia xAct module object, initialising Julia if needed."""
    _check_fork_safety()
    _ensure_initialized()
    return _xcore


def _ensure_initialized() -> None:
    global _jl, _xcore
    if _xcore is not None:
        return
    with _lock:
        if _xcore is None:
            _init_julia()


def _init_julia() -> None:
    global _jl, _xcore, _init_pid
    import juliacall

    jl = juliacall.Main

    # Attempt to load xAct. If juliapkg.json worked, it should be available.
    try:
        jl.seval("using XAct")
        # Only set globals after full success
        _jl = jl
        _xcore = jl.XAct
        _init_pid = os.getpid()
    except Exception:
        # Fallback for development if juliapkg hasn't resolved it yet,
        # or if we're running from source without a formal install.
        try:
            from xact._bridge import jl_escape

            julia_dir = (Path(__file__).parent.parent / "julia").resolve()
            if (julia_dir / "Project.toml").exists():
                escaped_dir = jl_escape(str(julia_dir))
                jl.seval(f'import Pkg; Pkg.activate("{escaped_dir}"; io=devnull)')
                xact_main = julia_dir / "src" / "XAct.jl"
                if xact_main.exists():
                    escaped_main = jl_escape(str(xact_main))
                    jl.seval(f'include("{escaped_main}")')
                    jl.seval("using .XAct")
                    # Only set globals after full success
                    _jl = jl
                    _xcore = jl.XAct
                    _init_pid = os.getpid()
                else:
                    raise ImportError(f"xAct.jl not found at {xact_main}")
            else:
                raise ImportError(
                    "xAct Julia package not found. Ensure juliapkg.json is respected "
                    "or Project.toml is present at root."
                )
        except ImportError:
            raise
        except Exception as exc:
            # Reset to clean state so retries don't see a half-initialized runtime
            _jl = None
            _xcore = None
            raise ImportError(f"Failed to load xAct Julia package: {exc}") from exc
