"""HTTP client for the Wolfram Oracle server."""

from dataclasses import dataclass
from typing import Literal, Optional

import requests

from sxact.normalize import normalize
from sxact.oracle.result import Result


@dataclass
class EvalResult:
    """Legacy result from evaluating a Wolfram expression.

    Deprecated: Use Result from sxact.oracle.result instead.
    """

    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    timing_ms: Optional[int] = None


class OracleClient:
    """Client for communicating with the Wolfram Oracle HTTP server."""

    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url.rstrip("/")

    def health(self) -> bool:
        """Check if the oracle server is healthy."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200 and resp.json().get("status") == "ok"
        except requests.RequestException:
            return False

    def evaluate(self, expr: str, timeout: int = 30) -> EvalResult:
        """Evaluate a Wolfram expression."""
        try:
            resp = requests.post(
                f"{self.base_url}/evaluate",
                json={"expr": expr, "timeout": timeout},
                timeout=timeout + 5,
            )
            data = resp.json()
            return EvalResult(
                status=data.get("status", "error"),
                result=data.get("result"),
                error=data.get("error"),
                timing_ms=data.get("timing_ms"),
            )
        except requests.RequestException as e:
            return EvalResult(status="error", error=str(e))

    def evaluate_with_xact(self, expr: str, timeout: int = 60) -> EvalResult:
        """Evaluate a Wolfram expression with xAct pre-loaded."""
        try:
            resp = requests.post(
                f"{self.base_url}/evaluate-with-init",
                json={"expr": expr, "timeout": timeout},
                timeout=timeout + 5,
            )
            data = resp.json()
            return EvalResult(
                status=data.get("status", "error"),
                result=data.get("result"),
                error=data.get("error"),
                timing_ms=data.get("timing_ms"),
            )
        except requests.RequestException as e:
            return EvalResult(status="error", error=str(e))

    def evaluate_result(self, expr: str, timeout: int = 30) -> Result:
        """Evaluate an expression and return a full Result envelope."""
        try:
            resp = requests.post(
                f"{self.base_url}/evaluate",
                json={"expr": expr, "timeout": timeout},
                timeout=timeout + 5,
            )
            data = resp.json()
            status_raw = data.get("status", "error")
            status: Literal["ok", "error", "timeout"] = (
                "ok" if status_raw == "ok" else
                "timeout" if status_raw == "timeout" else
                "error"
            )
            raw_result = data.get("result", "")
            return Result(
                status=status,
                type=data.get("type", "Expr"),
                repr=raw_result,
                normalized=normalize(raw_result) if raw_result else "",
                properties=data.get("properties", {}),
                diagnostics={"execution_time_ms": data.get("timing_ms")},
                error=data.get("error"),
            )
        except requests.Timeout:
            return Result(
                status="timeout",
                type="",
                repr="",
                normalized="",
                error="Request timed out",
            )
        except requests.RequestException as e:
            return Result(
                status="error",
                type="",
                repr="",
                normalized="",
                error=str(e),
            )
