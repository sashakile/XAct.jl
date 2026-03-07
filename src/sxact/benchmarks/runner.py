"""Layer 3 performance benchmark runner.

Times individual TOML test cases against a live adapter and reports
wall-clock statistics.  Supports baseline recording and regression
detection per the three-layer architecture spec.

Public API::

    from sxact.benchmarks.runner import bench_test_case, BenchResult

    result = bench_test_case(adapter, test_file, tc)
    print(result.median_ms)
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sxact.adapter.base import TestAdapter
    from sxact.runner.loader import TestCase, TestFile

# Default timing parameters (per spec §Layer 3)
N_WARMUP_DEFAULT = 10
N_MEASURE_DEFAULT = 30

# Regression thresholds (ratio vs Wolfram baseline)
THRESHOLD_WARNING = 5.0  # warn
THRESHOLD_FAIL = 10.0  # CI gate
THRESHOLD_CRITICAL = 50.0  # blocker


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class BenchResult:
    """Timing statistics for a single test case benchmark run."""

    test_id: str
    adapter: str
    n_warmup: int
    n_measure: int
    median_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BenchResult":
        return cls(**d)


# ---------------------------------------------------------------------------
# Core timing function
# ---------------------------------------------------------------------------


def bench_test_case(
    adapter: "TestAdapter[Any]",
    test_file: "TestFile",
    tc: "TestCase",
    *,
    n_warmup: int = N_WARMUP_DEFAULT,
    n_measure: int = N_MEASURE_DEFAULT,
    adapter_name: str = "wolfram",
) -> BenchResult:
    """Time *tc* by running it N times inside an :class:`IsolatedContext`.

    The adapter is initialized once; warmup runs are discarded.
    Timing covers only the :meth:`~IsolatedContext.run_test` call.

    Args:
        adapter:      Instantiated adapter (Wolfram, Julia, or Python).
        test_file:    Loaded :class:`TestFile` containing *tc*.
        tc:           The specific test case to benchmark.
        n_warmup:     Number of warmup iterations (not measured).
        n_measure:    Number of measured iterations.
        adapter_name: Label stored in the result (e.g. ``"wolfram"``).

    Returns:
        A :class:`BenchResult` with median, p95, p99, min, max in ms.
    """
    from sxact.runner.isolation import IsolatedContext

    with IsolatedContext(adapter, test_file) as ctx:
        for _ in range(n_warmup):
            ctx.run_test(tc)

        times: list[float] = []
        for _ in range(n_measure):
            t0 = time.perf_counter()
            ctx.run_test(tc)
            times.append((time.perf_counter() - t0) * 1_000)

    times_sorted = sorted(times)
    n = len(times_sorted)

    def _percentile(p: float) -> float:
        idx = int(p / 100 * (n - 1))
        return round(times_sorted[idx], 4)

    return BenchResult(
        test_id=tc.id,
        adapter=adapter_name,
        n_warmup=n_warmup,
        n_measure=n_measure,
        median_ms=round(statistics.median(times), 4),
        p95_ms=_percentile(95),
        p99_ms=_percentile(99),
        min_ms=round(min(times), 4),
        max_ms=round(max(times), 4),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Baseline I/O
# ---------------------------------------------------------------------------


def load_baseline(path: Path) -> dict[str, BenchResult]:
    """Load baseline JSON; returns mapping of ``"adapter/test_id"`` → result."""
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for entry in raw.get("benchmarks", []):
        r = BenchResult.from_dict(entry)
        out[_key(r.adapter, r.test_id)] = r
    return out


def save_baseline(path: Path, results: list[BenchResult]) -> None:
    """Write (or update) baseline JSON with the given results.

    Existing entries for the same adapter/test_id are replaced; others kept.
    """
    existing = load_baseline(path)
    for r in results:
        existing[_key(r.adapter, r.test_id)] = r

    data = {"benchmarks": [r.to_dict() for r in existing.values()]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _key(adapter: str, test_id: str) -> str:
    return f"{adapter}/{test_id}"


# ---------------------------------------------------------------------------
# Regression check
# ---------------------------------------------------------------------------


@dataclass
class RegressionResult:
    test_id: str
    adapter: str
    current_median_ms: float
    baseline_median_ms: float
    ratio: float
    level: str  # "ok", "warning", "fail", "critical"


def check_regression(
    current: list[BenchResult],
    baseline: dict[str, BenchResult],
    wolfram_baseline: dict[str, BenchResult] | None = None,
) -> list[RegressionResult]:
    """Compare *current* results against stored baseline.

    Also checks cross-adapter ratio vs. Wolfram if *wolfram_baseline* given.
    Returns a list of :class:`RegressionResult` for every benchmark.
    """
    results = []
    for r in current:
        base = baseline.get(_key(r.adapter, r.test_id))
        if base is None:
            continue
        if base.median_ms == 0:
            continue
        ratio = r.median_ms / base.median_ms
        level = _regression_level(ratio)
        results.append(
            RegressionResult(
                test_id=r.test_id,
                adapter=r.adapter,
                current_median_ms=r.median_ms,
                baseline_median_ms=base.median_ms,
                ratio=ratio,
                level=level,
            )
        )

    if wolfram_baseline:
        for r in current:
            if r.adapter == "wolfram":
                continue
            wkey = _key("wolfram", r.test_id)
            wb = wolfram_baseline.get(wkey)
            if wb is None or wb.median_ms == 0:
                continue
            ratio = r.median_ms / wb.median_ms
            level = _cross_adapter_level(ratio)
            results.append(
                RegressionResult(
                    test_id=r.test_id,
                    adapter=f"{r.adapter}/vs_wolfram",
                    current_median_ms=r.median_ms,
                    baseline_median_ms=wb.median_ms,
                    ratio=ratio,
                    level=level,
                )
            )

    return results


def _regression_level(ratio: float) -> str:
    if ratio >= THRESHOLD_CRITICAL:
        return "critical"
    if ratio >= THRESHOLD_FAIL:
        return "fail"
    if ratio >= THRESHOLD_WARNING:
        return "warning"
    return "ok"


def _cross_adapter_level(ratio: float) -> str:
    if ratio >= THRESHOLD_CRITICAL:
        return "critical"
    if ratio >= THRESHOLD_FAIL:
        return "fail"
    if ratio >= THRESHOLD_WARNING:
        return "warning"
    return "ok"
