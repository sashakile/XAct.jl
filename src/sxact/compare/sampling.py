"""Numeric sampling for expression comparison.

Substitutes random values for free variables and compares numeric results.
"""

import random
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sxact.oracle import OracleClient
    from sxact.oracle.result import Result


@dataclass
class Sample:
    """Result of a single numeric sample comparison."""

    substitution: dict[str, float]
    lhs_value: float | None
    rhs_value: float | None
    match: bool
    tolerance: float = 1e-10


def sample_numeric(
    lhs: "Result",
    rhs: "Result",
    oracle: "OracleClient",
    n: int = 10,
    seed: int = 42,
) -> list[Sample]:
    """Sample expressions numerically to check equivalence.

    Args:
        lhs: Left-hand side Result
        rhs: Right-hand side Result
        oracle: OracleClient for evaluation
        n: Number of samples
        seed: Random seed for reproducibility

    Returns:
        List of Sample results
    """
    variables = _extract_variables(lhs.repr) | _extract_variables(rhs.repr)

    if not variables:
        result = _evaluate_numeric_diff(lhs.repr, rhs.repr, {}, oracle)
        return [result] if result else []

    rng = random.Random(seed)
    samples: list[Sample] = []

    for _ in range(n):
        substitution = {var: rng.uniform(0.1, 10.0) for var in variables}
        result = _evaluate_numeric_diff(lhs.repr, rhs.repr, substitution, oracle)
        if result:
            samples.append(result)

    return samples


def _extract_variables(expr: str) -> set[str]:
    """Extract free variable names from an expression.

    Looks for single lowercase letters not inside brackets.
    Excludes common function names (Sin, Cos, etc.).
    """
    bracket_content = re.sub(r"\[[^\]]*\]", "", expr)

    pattern = r"\b([a-z])\b"
    matches = re.findall(pattern, bracket_content)

    excluded = {"e", "i"}
    return {m for m in matches if m not in excluded}


def _evaluate_numeric_diff(
    lhs_expr: str,
    rhs_expr: str,
    substitution: dict[str, float],
    oracle: "OracleClient",
    tolerance: float = 1e-10,
) -> Sample | None:
    """Evaluate the numeric difference between two expressions."""
    rules = ", ".join(f"{var} -> {val}" for var, val in substitution.items())
    if rules:
        eval_expr = f"N[({lhs_expr}) - ({rhs_expr}) /. {{{rules}}}]"
    else:
        eval_expr = f"N[({lhs_expr}) - ({rhs_expr})]"

    result = oracle.evaluate(eval_expr)

    if result.status != "ok" or not result.result:
        return None

    try:
        diff_value = float(result.result.strip())
        match = abs(diff_value) < tolerance
        return Sample(
            substitution=substitution,
            lhs_value=None,
            rhs_value=None,
            match=match,
            tolerance=tolerance,
        )
    except ValueError:
        return None
