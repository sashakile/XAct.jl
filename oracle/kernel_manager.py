"""Persistent Wolfram kernel manager using WSTP via wolframclient."""

import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wlexpr

INIT_SCRIPT = "/oracle/init.wl"


class KernelManager:
    """Manages a persistent Wolfram kernel with xAct pre-loaded."""

    def __init__(self):
        self._lock = threading.RLock()
        self._session: WolframLanguageSession | None = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._kernel_path = shutil.which("WolframKernel")
        self._xact_loaded = False

    def start(self):
        """Start the kernel and load xAct."""
        if not self._kernel_path:
            raise RuntimeError(
                "WolframKernel not found on PATH; set an explicit kernel path."
            )
        self._session = WolframLanguageSession(kernel_path=self._kernel_path)
        self._session.start()
        self._xact_loaded = False

    def _ensure_xact(self):
        """Load xAct if not already loaded."""
        if not self._xact_loaded and self._session is not None:
            self._session.evaluate(wlexpr(f'Get["{INIT_SCRIPT}"]'))
            self._xact_loaded = True

    def ensure(self):
        """Ensure kernel is running."""
        if self._session is None:
            self.start()

    def stop(self):
        """Stop the kernel."""
        if self._session is not None:
            try:
                self._session.terminate()
            except Exception:
                pass
            finally:
                self._session = None
                self._xact_loaded = False

    def restart(self):
        """Restart the kernel."""
        self.stop()
        self.start()

    def evaluate(
        self, expr: str, timeout_s: int, with_xact: bool = False
    ) -> tuple[bool, str | None, str | None]:
        """
        Evaluate an expression.

        Returns (ok: bool, result: str|None, error: str|None)
        """
        with self._lock:
            self.ensure()

            def _do_eval():
                if with_xact:
                    self._ensure_xact()
                return self._session.evaluate(wlexpr(expr))

            fut = self._executor.submit(_do_eval)
            try:
                result = fut.result(timeout=timeout_s)
                return True, str(result), None
            except FuturesTimeout:
                self.restart()
                return (
                    False,
                    None,
                    f"Evaluation timed out after {timeout_s}s (kernel restarted)",
                )
            except Exception as e:
                self.restart()
                return False, None, f"{type(e).__name__}: {e} (kernel restarted)"
