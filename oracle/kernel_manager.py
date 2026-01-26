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
        self, expr: str, timeout_s: int, with_xact: bool = False,
        context_id: str | None = None
    ) -> tuple[bool, str | None, str | None]:
        """
        Evaluate an expression.

        Args:
            expr: The Wolfram expression to evaluate.
            timeout_s: Timeout in seconds.
            with_xact: Whether to ensure xAct is loaded first.
            context_id: Optional unique context ID for isolation. When provided,
                wraps the expression in a Block that sets $Context to a unique
                namespace, preventing symbol pollution between tests.

        Returns (ok: bool, result: str|None, error: str|None)
        """
        with self._lock:
            self.ensure()

            # Wrap expression in context isolation if context_id provided.
            # We evaluate in xAct`xTensor` context so xAct functions properly
            # recognize tensor definitions. ToExpression delays parsing until
            # after Begin switches context, preventing Global` pollution.
            if context_id:
                # Escape the expression for embedding in a Mathematica string
                escaped_expr = expr.replace("\\", "\\\\").replace('"', '\\"')
                wrapped_expr = (
                    f'Begin["xAct`xTensor`"]; '
                    f'With[{{result$$ = ToExpression["{escaped_expr}"]}}, End[]; result$$]'
                )
            else:
                wrapped_expr = expr

            def _do_eval():
                if with_xact:
                    self._ensure_xact()
                return self._session.evaluate(wlexpr(wrapped_expr))

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
