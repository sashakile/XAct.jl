"""xact-test CLI entry point.

Usage::

    xact-test snapshot tests/ --output oracle/
    xact-test snapshot tests/ --output oracle/ --oracle-url http://localhost:8765

    xact-test run tests/
    xact-test run tests/ --oracle-mode=snapshot --oracle-dir=oracle/ --adapter=julia
    xact-test run tests/ --filter tag:smoke --format=json

    xact-test regen-oracle tests/ --oracle-dir oracle/
    xact-test regen-oracle tests/ --oracle-dir oracle/ --diff --yes
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Shared internal types
# ---------------------------------------------------------------------------

@dataclass
class _RunResult:
    """Outcome of a single test case within xact-test run."""

    file_id: str
    test_id: str
    status: str  # "pass", "fail", "error", "skip", "missing"
    actual: str | None = None
    expected: str | None = None
    message: str | None = None


# ---------------------------------------------------------------------------
# Subcommand: snapshot
# ---------------------------------------------------------------------------

def _cmd_snapshot(args: argparse.Namespace) -> int:
    from sxact.adapter.wolfram import WolframAdapter
    from sxact.adapter.base import AdapterError
    from sxact.runner.loader import load_test_file, LoadError
    from sxact.snapshot.runner import run_file
    from sxact.snapshot.writer import write_oracle_dir

    test_dir = Path(args.test_dir)
    output_dir = Path(args.output)

    if not test_dir.exists():
        print(f"error: test directory not found: {test_dir}", file=sys.stderr)
        return 1

    adapter = WolframAdapter(base_url=args.oracle_url, timeout=args.timeout)

    if not adapter._oracle.health():
        print(
            f"error: oracle not reachable at {args.oracle_url}\n"
            "       Start the oracle server before running snapshot generation.",
            file=sys.stderr,
        )
        return 1

    version = adapter.get_version()

    toml_files = sorted(test_dir.rglob("*.toml"))
    if not toml_files:
        print(f"warning: no .toml test files found in {test_dir}", file=sys.stderr)
        return 0

    print(f"Snapshotting {len(toml_files)} file(s) from {test_dir} → {output_dir}/")

    all_snapshots = []
    errors = 0

    for toml_path in toml_files:
        rel = toml_path.relative_to(test_dir)
        print(f"  {rel} ... ", end="", flush=True)

        try:
            test_file = load_test_file(toml_path)
        except LoadError as exc:
            print(f"LOAD ERROR: {exc}", file=sys.stderr)
            errors += 1
            continue

        try:
            file_snap = run_file(test_file, adapter)
            all_snapshots.append(file_snap)
            print(f"ok ({len(file_snap.tests)} tests)")
        except AdapterError as exc:
            print(f"ADAPTER ERROR: {exc}", file=sys.stderr)
            errors += 1
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            errors += 1

    write_oracle_dir(
        all_snapshots,
        output_dir,
        oracle_version=f"xAct {version.extra.get('xact_version', '1.2.0')}",
        mathematica_version=version.cas_version,
    )

    total = sum(len(f.tests) for f in all_snapshots)
    print(f"\nWrote {total} snapshot(s) to {output_dir}/")

    return 1 if errors else 0


# ---------------------------------------------------------------------------
# Subcommand: run
# ---------------------------------------------------------------------------

def _cmd_run(args: argparse.Namespace) -> int:
    from sxact.runner.loader import load_test_file, LoadError
    from sxact.adapter.base import AdapterError

    test_path = Path(args.test_path)
    if not test_path.exists():
        print(f"error: path not found: {test_path}", file=sys.stderr)
        return 1

    # Collect TOML files
    if test_path.is_file():
        toml_files = [test_path]
    else:
        toml_files = sorted(test_path.rglob("*.toml"))

    if not toml_files:
        print(f"warning: no .toml test files found under {test_path}", file=sys.stderr)
        return 0

    # Parse tag filter
    tag_filter: str | None = None
    for f in (args.filter or []):
        if f.startswith("tag:"):
            tag_filter = f[4:]
            break

    # Build adapter
    try:
        adapter = _make_adapter(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Live mode: verify oracle is reachable
    if args.oracle_mode == "live":
        from sxact.adapter.wolfram import WolframAdapter
        if isinstance(adapter, WolframAdapter) and not adapter._oracle.health():
            print(
                f"error: oracle not reachable at {args.oracle_url}\n"
                "       Start the oracle server before running in live mode.",
                file=sys.stderr,
            )
            return 1

    # Snapshot mode: load snapshot store
    store = None
    if args.oracle_mode == "snapshot":
        from sxact.snapshot.store import SnapshotStore
        oracle_dir = Path(args.oracle_dir)
        try:
            store = SnapshotStore(oracle_dir)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    # Run each file
    all_results: list[tuple[str, list[_RunResult]]] = []

    for toml_path in toml_files:
        try:
            test_file = load_test_file(toml_path)
        except LoadError as exc:
            all_results.append((str(toml_path), [_RunResult(
                file_id=str(toml_path),
                test_id="<load>",
                status="error",
                message=str(exc),
            )]))
            continue

        # Skip files where no tests match the tag filter
        if tag_filter:
            file_has_match = (
                tag_filter in test_file.meta.tags
                or any(tag_filter in tc.tags for tc in test_file.tests)
            )
            if not file_has_match:
                continue

        try:
            if args.oracle_mode == "live":
                results = _run_file_live(test_file, adapter, tag_filter)
            else:
                results = _run_file_snapshot(test_file, adapter, tag_filter, store)
        except AdapterError as exc:
            results = [_RunResult(
                file_id=test_file.meta.id,
                test_id="<adapter>",
                status="error",
                message=str(exc),
            )]
        except Exception as exc:
            results = [_RunResult(
                file_id=test_file.meta.id,
                test_id="<runner>",
                status="error",
                message=str(exc),
            )]

        all_results.append((str(toml_path), results))

    # Format output
    if args.format == "json":
        _print_json_run(all_results)
    else:
        _print_terminal_run(all_results)

    any_failure = any(
        r.status in ("fail", "error", "missing")
        for _, results in all_results
        for r in results
    )
    return 1 if any_failure else 0


# ---------------------------------------------------------------------------
# Subcommand: regen-oracle
# ---------------------------------------------------------------------------

def _interactive_review(new_snapshots, added, removed, changed, store):
    """Prompt for each changed/added snapshot; return filtered FileSnapshot list or None on quit."""
    import dataclasses

    revert_keys: set[tuple[str, str]] = set()  # keep old snapshot
    skip_keys: set[tuple[str, str]] = set()    # skip new addition
    accept_all = False

    for (meta_id, test_id), diff_lines in changed:
        if accept_all:
            continue
        print(f"\n--- {meta_id}/{test_id} [CHANGED] ---")
        for line in diff_lines:
            print(line)
        while True:
            try:
                ans = input("Accept change? [y]es/[n]o/[a]ll/[q]uit: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return None
            if ans in ("y", "yes"):
                break
            elif ans in ("n", "no"):
                revert_keys.add((meta_id, test_id))
                break
            elif ans == "a":
                accept_all = True
                break
            elif ans == "q":
                return None

    for meta_id, test_id in added:
        if accept_all:
            continue
        print(f"\n+++ {meta_id}/{test_id} [NEW]")
        while True:
            try:
                ans = input("Accept new snapshot? [y]es/[n]o/[a]ll/[q]uit: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return None
            if ans in ("y", "yes"):
                break
            elif ans in ("n", "no"):
                skip_keys.add((meta_id, test_id))
                break
            elif ans == "a":
                accept_all = True
                break
            elif ans == "q":
                return None

    from sxact.snapshot.runner import FileSnapshot
    result = []
    for file_snap in new_snapshots:
        accepted_tests = []
        for snap in file_snap.tests:
            key = (file_snap.meta_id, snap.test_id)
            if key in skip_keys:
                continue
            elif key in revert_keys:
                old = store.load(file_snap.meta_id, snap.test_id)
                if old is not None:
                    accepted_tests.append(old)
            else:
                accepted_tests.append(snap)
        if accepted_tests:
            result.append(dataclasses.replace(file_snap, tests=accepted_tests))
    return result


def _cmd_regen_oracle(args: argparse.Namespace) -> int:
    from sxact.adapter.wolfram import WolframAdapter
    from sxact.adapter.base import AdapterError
    from sxact.runner.loader import load_test_file, LoadError
    from sxact.snapshot.runner import run_file
    from sxact.snapshot.store import SnapshotStore
    from sxact.snapshot.writer import write_oracle_dir

    test_dir = Path(args.test_dir)
    oracle_dir = Path(args.oracle_dir)

    if not test_dir.exists():
        print(f"error: test directory not found: {test_dir}", file=sys.stderr)
        return 1
    if not oracle_dir.exists():
        print(f"error: oracle directory not found: {oracle_dir}", file=sys.stderr)
        return 1

    adapter = WolframAdapter(base_url=args.oracle_url, timeout=args.timeout)
    if not adapter._oracle.health():
        print(
            f"error: oracle not reachable at {args.oracle_url}\n"
            "       Start the oracle server before regenerating snapshots.",
            file=sys.stderr,
        )
        return 1

    store = SnapshotStore(oracle_dir)
    version = adapter.get_version()

    toml_files = sorted(test_dir.rglob("*.toml"))
    if not toml_files:
        print(f"warning: no .toml test files found in {test_dir}", file=sys.stderr)
        return 0

    print(f"Running {len(toml_files)} file(s) against live oracle...")

    new_snapshots = []
    errors = 0

    for toml_path in toml_files:
        rel = toml_path.relative_to(test_dir)
        print(f"  {rel} ... ", end="", flush=True)

        try:
            test_file = load_test_file(toml_path)
        except LoadError as exc:
            print(f"LOAD ERROR: {exc}", file=sys.stderr)
            errors += 1
            continue

        try:
            file_snap = run_file(test_file, adapter)
            new_snapshots.append(file_snap)
            print(f"ok ({len(file_snap.tests)} tests)")
        except AdapterError as exc:
            print(f"ADAPTER ERROR: {exc}", file=sys.stderr)
            errors += 1
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            errors += 1

    # ------------------------------------------------------------------
    # Diff: compare new vs existing
    # ------------------------------------------------------------------
    existing_keys = set(store.list_snapshots())
    new_keys = {(fs.meta_id, s.test_id) for fs in new_snapshots for s in fs.tests}

    added = []
    removed = sorted(existing_keys - new_keys)
    changed = []  # list of (key, diff_lines)
    unchanged = 0

    for file_snap in new_snapshots:
        for snap in file_snap.tests:
            key = (file_snap.meta_id, snap.test_id)
            old = store.load(file_snap.meta_id, snap.test_id)
            if old is None:
                added.append(key)
            elif old.normalized_output != snap.normalized_output:
                diff_lines = list(difflib.unified_diff(
                    old.normalized_output.splitlines(keepends=True),
                    snap.normalized_output.splitlines(keepends=True),
                    fromfile=f"{key[0]}/{key[1]} (old)",
                    tofile=f"{key[0]}/{key[1]} (new)",
                    lineterm="",
                ))
                changed.append((key, diff_lines))
            else:
                unchanged += 1

    total_changes = len(added) + len(removed) + len(changed)
    summary_parts = []
    if unchanged:
        summary_parts.append(f"{unchanged} unchanged")
    if changed:
        summary_parts.append(f"{len(changed)} changed")
    if added:
        summary_parts.append(f"{len(added)} new")
    if removed:
        summary_parts.append(f"{len(removed)} deleted")
    print(f"\n{', '.join(summary_parts) if summary_parts else 'No changes detected.'}")

    if total_changes == 0:
        return 0

    for meta_id, test_id in added:
        print(f"  + {meta_id}/{test_id}  [NEW]")
    for meta_id, test_id in removed:
        print(f"  - {meta_id}/{test_id}  [REMOVED]")
    for (meta_id, test_id), diff_lines in changed:
        print(f"  ~ {meta_id}/{test_id}  [CHANGED]")
        if args.diff:
            for line in diff_lines:
                print(f"    {line}")

    if args.dry_run:
        print("\n(dry-run: no files written)")
        return 1 if errors else 0

    print()
    if args.interactive:
        accepted_snapshots = _interactive_review(new_snapshots, added, removed, changed, store)
        if accepted_snapshots is None:
            print("Aborted.")
            return 1
        write_oracle_dir(
            accepted_snapshots,
            oracle_dir,
            oracle_version=f"xAct {version.extra.get('xact_version', '1.2.0')}",
            mathematica_version=version.cas_version,
        )
        total = sum(len(f.tests) for f in accepted_snapshots)
        print(f"Wrote {total} snapshot(s) to {oracle_dir}/")
        return 1 if errors else 0

    if not args.yes:
        try:
            answer = input("Overwrite oracle snapshots? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1
        if answer not in ("y", "yes"):
            print("Aborted.")
            return 1

    write_oracle_dir(
        new_snapshots,
        oracle_dir,
        oracle_version=f"xAct {version.extra.get('xact_version', '1.2.0')}",
        mathematica_version=version.cas_version,
    )

    total = sum(len(f.tests) for f in new_snapshots)
    print(f"Wrote {total} snapshot(s) to {oracle_dir}/")
    return 1 if errors else 0


# ---------------------------------------------------------------------------
# Subcommand: benchmark
# ---------------------------------------------------------------------------

_BASELINE_PATH = Path("benchmarks/baseline.json")


def _cmd_benchmark(args: argparse.Namespace) -> int:
    from sxact.benchmarks.runner import (
        BenchResult,
        RegressionResult,
        bench_test_case,
        check_regression,
        load_baseline,
        save_baseline,
        THRESHOLD_WARNING,
        THRESHOLD_FAIL,
        THRESHOLD_CRITICAL,
    )
    from sxact.runner.loader import load_test_file, LoadError

    adapter_name = args.adapter
    adapter = _make_adapter(args)

    baseline_path = Path(args.baseline)

    # --compare: run all available adapters, print table
    if args.compare:
        return _cmd_benchmark_compare(args, adapter_name, baseline_path)

    test_files_paths = sorted(Path(args.test_dir).rglob("*.toml"))
    if not test_files_paths:
        print(f"warning: no .toml test files found in {args.test_dir}", file=sys.stderr)
        return 0

    results: list[BenchResult] = []

    for toml_path in test_files_paths:
        try:
            test_file = load_test_file(toml_path)
        except LoadError as exc:
            print(f"LOAD ERROR {toml_path}: {exc}", file=sys.stderr)
            continue

        for tc in test_file.tests:
            tag_filter = args.tag
            if tag_filter and not _tc_matches_tag(tc.tags, test_file.meta.tags, tag_filter):
                continue

            print(f"  {test_file.meta.id}/{tc.id} ({adapter_name}) ... ", end="", flush=True)
            try:
                result = bench_test_case(
                    adapter,
                    test_file,
                    tc,
                    n_warmup=args.n_warmup,
                    n_measure=args.n_measure,
                    adapter_name=adapter_name,
                )
            except Exception as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                continue

            results.append(result)
            print(
                f"median={result.median_ms:.3f}ms  "
                f"p95={result.p95_ms:.3f}ms  "
                f"min={result.min_ms:.3f}ms  "
                f"max={result.max_ms:.3f}ms"
            )

    if not results:
        return 0

    if args.record:
        save_baseline(baseline_path, results)
        print(f"\nBaseline written to {baseline_path}")

    if args.check:
        baseline = load_baseline(baseline_path)
        if not baseline:
            print(f"warning: no baseline found at {baseline_path}; run with --record first", file=sys.stderr)
            return 0

        regressions = check_regression(results, baseline)
        had_fail = False
        for reg in regressions:
            if reg.level == "ok":
                continue
            label = reg.level.upper()
            print(
                f"{label:<8} {reg.adapter}/{reg.test_id}: "
                f"{reg.ratio:.1f}x ({reg.current_median_ms:.3f}ms vs baseline {reg.baseline_median_ms:.3f}ms)"
            )
            if reg.level in ("fail", "critical"):
                had_fail = True

        if had_fail:
            return 1

    return 0


def _cmd_benchmark_compare(args, primary_adapter_name: str, baseline_path: Path) -> int:
    """Run all available adapters on the test dir and print a comparison table."""
    from sxact.benchmarks.runner import bench_test_case, BenchResult
    from sxact.runner.loader import load_test_file, LoadError

    adapter_names = ["wolfram", "julia", "python"]
    adapter_results: dict[str, list[BenchResult]] = {}

    test_files_paths = sorted(Path(args.test_dir).rglob("*.toml"))
    if not test_files_paths:
        print(f"warning: no .toml test files found in {args.test_dir}", file=sys.stderr)
        return 0

    for name in adapter_names:
        try:
            adapter = _make_adapter_by_name(name, args)
        except Exception as exc:
            print(f"  skip {name}: {exc}")
            continue

        print(f"\nRunning {name} adapter...")
        adapter_results[name] = []

        for toml_path in test_files_paths:
            try:
                test_file = load_test_file(toml_path)
            except LoadError:
                continue

            for tc in test_file.tests:
                print(f"  {test_file.meta.id}/{tc.id} ... ", end="", flush=True)
                try:
                    result = bench_test_case(
                        adapter, test_file, tc,
                        n_warmup=args.n_warmup,
                        n_measure=args.n_measure,
                        adapter_name=name,
                    )
                    adapter_results[name].append(result)
                    print(f"median={result.median_ms:.3f}ms")
                except Exception as exc:
                    print(f"ERROR: {exc}")

    # Print cross-adapter table
    all_test_ids = sorted({r.test_id for rs in adapter_results.values() for r in rs})
    wolfram_map = {r.test_id: r for r in adapter_results.get("wolfram", [])}

    print("\n" + "=" * 70)
    print(f"{'test_id':<30} {'wolfram':>10} {'julia':>10} {'python':>10} {'j/w':>6} {'p/w':>6}")
    print("-" * 70)

    for tid in all_test_ids:
        row = f"{tid:<30}"
        wms = next((r.median_ms for r in adapter_results.get("wolfram", []) if r.test_id == tid), None)
        jms = next((r.median_ms for r in adapter_results.get("julia", []) if r.test_id == tid), None)
        pms = next((r.median_ms for r in adapter_results.get("python", []) if r.test_id == tid), None)

        row += f" {f'{wms:.3f}ms':>10}" if wms is not None else f" {'—':>10}"
        row += f" {f'{jms:.3f}ms':>10}" if jms is not None else f" {'—':>10}"
        row += f" {f'{pms:.3f}ms':>10}" if pms is not None else f" {'—':>10}"

        jw = f"{jms/wms:.1f}x" if jms is not None and wms else "—"
        pw = f"{pms/wms:.1f}x" if pms is not None and wms else "—"
        row += f" {jw:>6} {pw:>6}"
        print(row)

    print("=" * 70)
    return 0


def _make_adapter_by_name(name: str, args):
    """Create an adapter by explicit name, using args for URL/timeout."""
    oracle_url = getattr(args, "oracle_url", "http://localhost:8765")
    timeout = getattr(args, "timeout", 60)
    if name == "wolfram":
        from sxact.adapter.wolfram import WolframAdapter
        return WolframAdapter(base_url=oracle_url, timeout=timeout)
    elif name == "julia":
        from sxact.adapter.julia_stub import JuliaAdapter
        return JuliaAdapter()
    elif name == "python":
        from sxact.adapter.python_stub import PythonAdapter
        return PythonAdapter()
    else:
        raise ValueError(f"Unknown adapter: {name!r}")


# ---------------------------------------------------------------------------
# Run helpers
# ---------------------------------------------------------------------------

def _make_adapter(args: argparse.Namespace):
    """Instantiate the adapter specified by args.adapter."""
    name = getattr(args, "adapter", "wolfram")
    oracle_url = getattr(args, "oracle_url", "http://localhost:8765")
    timeout = getattr(args, "timeout", 60)

    if name == "wolfram":
        from sxact.adapter.wolfram import WolframAdapter
        return WolframAdapter(base_url=oracle_url, timeout=timeout)
    elif name == "julia":
        from sxact.adapter.julia_stub import JuliaAdapter
        return JuliaAdapter()
    elif name == "python":
        from sxact.adapter.python_stub import PythonAdapter
        return PythonAdapter()
    else:
        raise ValueError(f"Unknown adapter: {name!r}")


def _tc_matches_tag(tc_tags: list[str], file_tags: list[str], tag: str) -> bool:
    return tag in tc_tags or tag in file_tags


_REF_RE = re.compile(r"\$(\w+)")


def _sub_bindings(args: dict[str, Any], bindings: dict[str, str]) -> dict[str, Any]:
    def _sub(val: str) -> str:
        return _REF_RE.sub(lambda m: bindings.get(m.group(1), m.group(0)), val)

    return {k: _sub(v) if isinstance(v, str) else v for k, v in args.items()}


def _run_file_live(test_file, adapter, tag_filter: str | None) -> list[_RunResult]:
    """Run a test file in live mode using IsolatedContext."""
    from sxact.runner.isolation import IsolatedContext

    results: list[_RunResult] = []
    with IsolatedContext(adapter, test_file) as iso:
        for tc in test_file.tests:
            if tag_filter and not _tc_matches_tag(tc.tags, test_file.meta.tags, tag_filter):
                continue
            tr = iso.run_test(tc)
            results.append(_RunResult(
                file_id=test_file.meta.id,
                test_id=tc.id,
                status=tr.status,
                actual=tr.actual,
                expected=tr.expected,
                message=tr.message,
            ))
    return results


def _run_file_snapshot(test_file, adapter, tag_filter: str | None, store) -> list[_RunResult]:
    """Run a test file in snapshot mode, comparing against oracle snapshots."""
    from sxact.snapshot.compare import SnapshotComparator

    comparator = SnapshotComparator(store)
    results: list[_RunResult] = []

    ctx = adapter.initialize()
    try:
        # Run setup operations, building shared bindings
        bindings: dict[str, str] = {}
        for op in test_file.setup:
            resolved = _sub_bindings(op.args, bindings)
            res = adapter.execute(ctx, op.action, resolved)
            if op.store_as and res.repr:
                bindings[op.store_as] = res.repr

        for tc in test_file.tests:
            if tag_filter and not _tc_matches_tag(tc.tags, test_file.meta.tags, tag_filter):
                continue

            if tc.skip:
                results.append(_RunResult(
                    file_id=test_file.meta.id,
                    test_id=tc.id,
                    status="skip",
                    message=tc.skip,
                ))
                continue

            # Run test operations with per-test binding scope
            local = dict(bindings)
            last_res = None
            error_msg: str | None = None
            try:
                for op in tc.operations:
                    resolved = _sub_bindings(op.args, local)
                    last_res = adapter.execute(ctx, op.action, resolved)
                    if op.store_as and last_res.repr:
                        local[op.store_as] = last_res.repr
            except Exception as exc:
                error_msg = str(exc)

            if error_msg:
                results.append(_RunResult(
                    file_id=test_file.meta.id,
                    test_id=tc.id,
                    status="error",
                    message=error_msg,
                ))
                continue

            if last_res is None:
                results.append(_RunResult(
                    file_id=test_file.meta.id,
                    test_id=tc.id,
                    status="pass",
                ))
                continue

            cmp = comparator.compare(test_file.meta.id, tc.id, last_res)
            if cmp.passed:
                status, msg = "pass", None
            elif cmp.outcome == "missing":
                status, msg = "missing", cmp.details
            else:
                status, msg = "fail", cmp.details

            results.append(_RunResult(
                file_id=test_file.meta.id,
                test_id=tc.id,
                status=status,
                actual=cmp.actual_normalized,
                expected=cmp.expected_normalized,
                message=msg,
            ))
    finally:
        adapter.teardown(ctx)

    return results


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

_STATUS_LABEL = {
    "pass": "PASS",
    "fail": "FAIL",
    "error": "ERROR",
    "skip": "SKIP",
    "missing": "MISSING",
}


def _print_terminal_run(all_results: list[tuple[str, list[_RunResult]]]) -> None:
    passed = failed = skipped = errors = 0

    for file_path, results in all_results:
        print(file_path)
        for r in results:
            label = _STATUS_LABEL.get(r.status, r.status.upper())
            if r.status == "pass":
                passed += 1
                print(f"  {label:<8} {r.test_id}")
            elif r.status == "skip":
                skipped += 1
                suffix = f" ({r.message})" if r.message else ""
                print(f"  {label:<8} {r.test_id}{suffix}")
            else:
                if r.status in ("fail", "missing"):
                    failed += 1
                else:
                    errors += 1
                print(f"  {label:<8} {r.test_id}")
                if r.message:
                    for line in r.message.splitlines():
                        print(f"           {line}")

    total_files = len(all_results)
    parts = [f"{passed} passed"]
    if failed:
        parts.append(f"{failed} failed")
    if errors:
        parts.append(f"{errors} errors")
    if skipped:
        parts.append(f"{skipped} skipped")
    print(f"\n{', '.join(parts)} in {total_files} file(s)")


def _print_json_run(all_results: list[tuple[str, list[_RunResult]]]) -> None:
    passed = failed = skipped = errors = 0
    output_files = []

    for file_path, results in all_results:
        tests_out = []
        for r in results:
            if r.status == "pass":
                passed += 1
            elif r.status == "skip":
                skipped += 1
            elif r.status in ("fail", "missing"):
                failed += 1
            else:
                errors += 1

            t: dict[str, Any] = {"id": r.test_id, "status": r.status}
            if r.actual is not None:
                t["actual"] = r.actual
            if r.expected is not None:
                t["expected"] = r.expected
            if r.message is not None:
                t["message"] = r.message
            tests_out.append(t)

        output_files.append({"file": file_path, "tests": tests_out})

    out = {
        "summary": {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
        },
        "files": output_files,
    }
    print(json.dumps(out, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="xact-test",
        description="sxAct test harness CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- snapshot subcommand ---
    snap = subparsers.add_parser(
        "snapshot",
        help="Run test files against the live Wolfram oracle and save snapshots",
    )
    snap.add_argument("test_dir", help="Directory containing .toml test files")
    snap.add_argument(
        "--output",
        required=True,
        metavar="ORACLE_DIR",
        help="Output directory for oracle snapshots",
    )
    snap.add_argument(
        "--oracle-url",
        default="http://localhost:8765",
        metavar="URL",
        dest="oracle_url",
        help="Oracle HTTP server URL (default: http://localhost:8765)",
    )
    snap.add_argument(
        "--timeout",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Per-evaluation timeout in seconds (default: 60)",
    )
    snap.set_defaults(func=_cmd_snapshot)

    # --- run subcommand ---
    run = subparsers.add_parser(
        "run",
        help="Run test files and report pass/fail results",
    )
    run.add_argument(
        "test_path",
        help="Path to a .toml file or directory containing .toml files",
    )
    run.add_argument(
        "--oracle-mode",
        choices=["live", "snapshot"],
        default="live",
        dest="oracle_mode",
        help="Reference mode: live=WolframAdapter, snapshot=stored oracle (default: live)",
    )
    run.add_argument(
        "--adapter",
        choices=["wolfram", "julia", "python"],
        default="wolfram",
        help="Adapter under test (default: wolfram)",
    )
    run.add_argument(
        "--oracle-dir",
        default="oracle",
        metavar="ORACLE_DIR",
        dest="oracle_dir",
        help="Oracle snapshot directory for snapshot mode (default: oracle)",
    )
    run.add_argument(
        "--oracle-url",
        default="http://localhost:8765",
        metavar="URL",
        dest="oracle_url",
        help="Oracle HTTP server URL for live mode (default: http://localhost:8765)",
    )
    run.add_argument(
        "--timeout",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Per-evaluation timeout in seconds (default: 60)",
    )
    run.add_argument(
        "--filter",
        action="append",
        metavar="tag:<TAG>",
        help="Filter tests by tag (e.g. --filter tag:smoke). May be repeated.",
    )
    run.add_argument(
        "--format",
        choices=["terminal", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    run.set_defaults(func=_cmd_run)

    # --- regen-oracle subcommand ---
    regen = subparsers.add_parser(
        "regen-oracle",
        help="Regenerate oracle snapshots from the live oracle, showing a diff first",
    )
    regen.add_argument("test_dir", help="Directory containing .toml test files")
    regen.add_argument(
        "--oracle-dir",
        required=True,
        metavar="ORACLE_DIR",
        dest="oracle_dir",
        help="Existing oracle snapshot directory to update",
    )
    regen.add_argument(
        "--oracle-url",
        default="http://localhost:8765",
        metavar="URL",
        dest="oracle_url",
        help="Oracle HTTP server URL (default: http://localhost:8765)",
    )
    regen.add_argument(
        "--timeout",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Per-evaluation timeout in seconds (default: 60)",
    )
    regen.add_argument(
        "--diff",
        action="store_true",
        default=False,
        help="Show full unified diff for changed snapshots",
    )
    regen.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        dest="dry_run",
        help="Show diffs without writing any files",
    )
    regen.add_argument(
        "--interactive", "-i",
        action="store_true",
        default=False,
        help="Review each changed snapshot interactively (y/n/a/q)",
    )
    regen.add_argument(
        "--yes", "-y",
        action="store_true",
        default=False,
        help="Skip confirmation prompt and overwrite immediately",
    )
    regen.set_defaults(func=_cmd_regen_oracle)

    # --- benchmark subcommand ---
    bench = subparsers.add_parser(
        "benchmark",
        help="Layer 3: time test cases and track performance regressions",
    )
    bench.add_argument("test_dir", help="Directory containing .toml test files")
    bench.add_argument(
        "--adapter",
        default="wolfram",
        choices=["wolfram", "julia", "python"],
        help="Adapter to benchmark (default: wolfram)",
    )
    bench.add_argument(
        "--oracle-url",
        default="http://localhost:8765",
        metavar="URL",
        dest="oracle_url",
        help="Oracle HTTP server URL (default: http://localhost:8765)",
    )
    bench.add_argument(
        "--timeout",
        type=int,
        default=60,
        metavar="SECONDS",
        dest="timeout",
        help="Per-evaluation timeout in seconds (default: 60)",
    )
    bench.add_argument(
        "--n-warmup",
        type=int,
        default=10,
        metavar="N",
        dest="n_warmup",
        help="Warmup iterations (default: 10)",
    )
    bench.add_argument(
        "--n-measure",
        type=int,
        default=30,
        metavar="N",
        dest="n_measure",
        help="Measured iterations (default: 30)",
    )
    bench.add_argument(
        "--baseline",
        default=str(_BASELINE_PATH),
        metavar="PATH",
        help=f"Baseline JSON path (default: {_BASELINE_PATH})",
    )
    bench.add_argument(
        "--record",
        action="store_true",
        default=False,
        help="Record current run as new baseline",
    )
    bench.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Compare against baseline and fail if regression threshold exceeded",
    )
    bench.add_argument(
        "--compare",
        action="store_true",
        default=False,
        help="Run all available adapters and print cross-adapter comparison table",
    )
    bench.add_argument(
        "--tag",
        default=None,
        metavar="TAG",
        help="Filter tests by tag",
    )
    bench.set_defaults(func=_cmd_benchmark)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
