# xAct Language-Agnostic Test Framework Design (TOML Version)

**Date:** 2026-01-08
**Version:** 1.0
**Status:** Design Document

## Overview

Create TOML-based test specifications that can be executed against:
- **Oracle:** Wolfram xAct (ground truth)
- **Implementations:** Python, Julia

Focus on **xCore, xPerm, xTensor** with regression tests extracted from documentation notebooks.

## Project Context

**xAct** is a comprehensive tensor algebra and differential geometry package for Wolfram Language with:
- 36,064 lines of Wolfram Language code
- 15 packages covering tensor algebra, differential geometry, and General Relativity
- Performance-critical C code for permutation algorithms (xPerm)

**Migration Goals:**
- Port xAct functionality to Python and Julia
- Create language-agnostic test framework
- Enable oracle testing against Wolfram xAct
- Performance comparison across implementations

**Scope Decisions:**
- Packages: xCore, xPerm, xTensor (core trio)
- Languages: Python, Julia
- Test format: TOML (over YAML for explicitness)
- Oracle: Wolfram xAct as ground truth
- Coverage: Regression test suite from documentation notebooks

---

## 1. Test File Format (TOML)

### Directory Structure

```
tests/
├── schema/
│   └── test-schema.json          # JSON Schema validation
├── core/
│   ├── manifolds.toml            # Manifold definition tests
│   ├── tensors.toml              # Tensor definition tests
│   └── indices.toml              # Index manipulation tests
├── perm/
│   ├── canonicalization.toml     # ToCanonical tests
│   ├── symmetries.toml           # Symmetry handling
│   └── permutations.toml         # xPerm algorithm tests
├── geometry/
│   ├── metrics.toml              # Metric tensors
│   ├── curvature.toml            # Riemann, Ricci, Einstein
│   └── covariant-derivatives.toml
├── integration/
│   └── full-workflows.toml       # Multi-step calculations
└── benchmarks/
    ├── performance.toml          # Timed operations
    └── memory.toml               # Memory profiling tests
```

### Test Case Schema

```toml
# tests/core/manifolds.toml
version = "1.0"
package = "xTensor"
category = "core"
description = "Basic manifold and tensor definitions"

# Global setup run once before all tests
[[setup]]
action = "DefManifold"
store_as = "manifold_M"

[setup.args]
name = "M"
dimension = 4
indices = ["a", "b", "c", "d"]

# ============================================================================
# Test Case 1: Define rank-2 symmetric tensor
# ============================================================================

[[tests]]
id = "tensor_basic_001"
name = "Define rank-2 symmetric tensor"
tags = ["tensor", "definition", "symmetric"]
difficulty = "basic"

[[tests.operations]]
action = "DefTensor"
store_as = "tensor_T"

[tests.operations.args]
name = "T"
indices = ["-a", "-b"]
manifold = "$manifold_M"  # Reference from setup
symmetry = "Symmetric[{-a, -b}]"

[[tests.operations]]
action = "Evaluate"
expression = "T[-a, -b]"
store_as = "result"

[tests.expected]
type = "Tensor"
expression = "T[-a, -b]"

[tests.expected.symmetry]
type = "Symmetric"
slots = ["-a", "-b"]

[tests.expected.properties]
rank = 2
manifold = "M"

[tests.oracle]
commands = """
DefManifold[M, 4, {a, b, c, d}]
DefTensor[T[-a, -b], M, Symmetric[{-a, -b}]]
T[-a, -b]
"""
output_file = "oracle/tensor_basic_001.wl"
expected_hash = "sha256:abc123..."

# ============================================================================
# Test Case 2: Contract indices in tensor product
# ============================================================================

[[tests]]
id = "index_contraction_001"
name = "Contract indices in tensor product"
tags = ["contraction", "index-manipulation"]
dependencies = ["tensor_basic_001"]

[[tests.operations]]
action = "DefTensor"
store_as = "tensor_S"

[tests.operations.args]
name = "S"
indices = ["-a"]
manifold = "$manifold_M"

[[tests.operations]]
action = "ContractIndices"
expression = "T[-a, -b] * S[a]"
store_as = "result"

[tests.expected]
expression = "T[-LI[1], -b] S[LI[1]]"
simplified = "ContractedExpr[-b]"

[tests.metrics]
max_execution_time_ms = 100
max_memory_mb = 50
```

### Key TOML Format Features

1. **Explicit Typing**: TOML is strongly typed (strings, integers, floats, booleans, dates)
2. **Array of Tables**: `[[tests]]` for multiple test cases
3. **Nested Tables**: `[tests.expected]` for hierarchical data
4. **Multi-line Strings**: `"""..."""` for Wolfram code blocks
5. **Comments**: `#` for inline documentation

---

## 2. Canonicalization Tests (xPerm)

Critical for correctness:

```toml
# tests/perm/canonicalization.toml
version = "1.0"
package = "xPerm"
category = "canonicalization"
description = "Critical canonicalization algorithm tests"

[[setup]]
action = "DefManifold"
[setup.args]
name = "M"
dimension = 4
indices = ["a", "b", "c", "d", "e", "f"]

[[setup]]
action = "DefMetric"
[setup.args]
signdet = -1
metric = "g[-a,-b]"
covd = "CD"
symbols = [";", "∇"]

# ============================================================================
# First Bianchi Identity
# ============================================================================

[[tests]]
id = "canonical_riemann_001"
name = "Canonicalize Riemann tensor identity"
tags = ["canonicalization", "riemann", "critical"]

[[tests.operations]]
action = "ToCanonical"
store_as = "result"
expression = """
RiemannCD[a, -b, -c, -d] +
RiemannCD[c, -d, -a, -b] +
RiemannCD[d, -a, -b, -c]
"""

[tests.expected]
expression = "0"
canonical = true

[[tests.validation]]
assert_zero = true

[[tests.validation]]
symmetry_check = "Riemann"

[tests.performance]
operation = "canonicalization"
metric = "execution_time_ms"
baseline_wolfram = 45
threshold_factor = 5.0  # Allow 5x slower than Wolfram

[tests.oracle]
commands = """
Needs["xAct`xTensor`"]
DefManifold[M, 4, {a,b,c,d,e,f}]
DefMetric[-1, g[-a,-b], CD, {";", "∇"}]
ToCanonical[
  RiemannCD[a, -b, -c, -d] +
  RiemannCD[c, -d, -a, -b] +
  RiemannCD[d, -a, -b, -c]
]
"""
```

---

## 3. Performance Benchmark Format

```toml
# tests/benchmarks/performance.toml

[benchmark_suite]
name = "xAct Core Operations"
warmup_iterations = 5
measured_iterations = 100

# ============================================================================
# Benchmark: Tensor contraction scaling
# ============================================================================

[[benchmarks]]
id = "bench_contraction_scaling"
name = "Tensor contraction scaling"

[benchmarks.parameters]
num_indices = [2, 4, 6, 8, 10]

[[benchmarks.operations]]
action = "GenerateTensor"
rank = "$num_indices"
random_symmetry = true

[[benchmarks.operations]]
action = "ContractAll"

[[benchmarks.metrics]]
name = "execution_time"
unit = "milliseconds"
aggregation = "median"

[[benchmarks.metrics]]
name = "memory_peak"
unit = "megabytes"
aggregation = "max"

[[benchmarks.metrics]]
name = "num_terms_before"
unit = "count"

[[benchmarks.metrics]]
name = "num_terms_after"
unit = "count"

[benchmarks.reporting]
plot = "scaling_curve"
regression_model = "polynomial_degree_2"
```

---

## 4. Test Harness Architecture

### Per-Language Structure

```
harness/
├── common/
│   ├── loader.py              # TOML parser (tomllib/tomli)
│   ├── validator.py           # JSON Schema validation
│   └── comparator.py          # Result comparison logic
├── wolfram/
│   ├── runner.py              # Execute via wolframclient
│   ├── oracle_generator.py   # Generate ground truth
│   └── serializer.py          # Wolfram → JSON conversion
├── python/
│   ├── runner.py              # Python xTensor implementation
│   ├── adapter.py             # Map TOML actions to Python API
│   └── __init__.py
├── julia/
│   ├── runner.jl
│   ├── adapter.jl
│   └── Project.toml           # Julia also uses TOML!
└── cli.py                      # Main test runner
```

### TOML Loader (Python Example)

```python
# harness/common/loader.py
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from pathlib import Path
from typing import Dict, List

class TestLoader:
    """Load and parse TOML test files."""

    def load_test_file(self, path: Path) -> Dict:
        """Load a single TOML test file."""
        with open(path, 'rb') as f:
            return tomllib.load(f)

    def load_test_suite(self, directory: Path) -> List[Dict]:
        """Load all TOML files from a directory."""
        tests = []
        for toml_file in directory.rglob("*.toml"):
            tests.append(self.load_test_file(toml_file))
        return tests

    def validate_schema(self, test_data: Dict) -> bool:
        """Validate against JSON Schema."""
        # Implementation using jsonschema library
        pass
```

---

## 5. Complete Example: Schwarzschild Metric

```toml
# tests/integration/schwarzschild.toml
version = "1.0"
description = "Schwarzschild metric curvature calculation"
reference = "Wald, General Relativity (1984), Eq. 6.1.8"

# ============================================================================
# Setup: Define manifold and metric
# ============================================================================

[[setup]]
action = "DefManifold"
[setup.args]
name = "M"
dimension = 4
indices = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]

[[setup]]
action = "DefChart"
[setup.args]
chart = "chart"
manifold = "M"
coords_indices = [0, 1, 2, 3]
coords_names = ["t[]", "r[]", "θ[]", "φ[]"]

[[setup]]
action = "DefMetric"
[setup.args]
signdet = -1
metric = "g[-a,-b]"
covd = "CD"

# ============================================================================
# Test: Schwarzschild Ricci scalar vanishes
# ============================================================================

[[tests]]
id = "schwarzschild_ricci_scalar"
name = "Schwarzschild Ricci scalar vanishes"
tags = ["integration", "GR", "schwarzschild", "critical"]

[[tests.operations]]
action = "SetMetricComponents"
components = """
g[{0,0}] = -(1 - 2M/r)
g[{1,1}] = 1/(1 - 2M/r)
g[{2,2}] = r^2
g[{3,3}] = r^2 Sin[θ]^2
"""

[[tests.operations]]
action = "ComputeChristoffel"
store_as = "christoffel"

[[tests.operations]]
action = "ComputeRiemannTensor"
store_as = "riemann"

[[tests.operations]]
action = "ComputeRicciScalar"
store_as = "ricci_scalar"

[[tests.operations]]
action = "Simplify"
expression = "$ricci_scalar"
store_as = "result"
[tests.operations.assumptions]
constraints = ["r > 2M", "M > 0"]

[tests.expected]
expression = "0"
reason = "Schwarzschild is vacuum solution"

[[tests.validation]]
assert_zero = true

[[tests.validation]]
[tests.validation.numerical_check]
tolerance = 1e-12
[tests.validation.numerical_check.parameters]
M = 1.0
r = 10.0
θ = 1.0

[tests.performance]
baseline_wolfram_ms = 850
max_memory_mb = 200
complexity = "high"

[tests.oracle]
commands_file = "oracle/schwarzschild.wl"
```

---

## 6. CLI Interface

```bash
# Run all tests against Wolfram (generate oracle)
./harness/cli.py run --target wolfram --output oracle/

# Run Python tests against oracle
./harness/cli.py run --target python --compare oracle/

# Run specific test file
./harness/cli.py run --target julia --file tests/perm/canonicalization.toml

# Filter by tags
./harness/cli.py run --target python --tags contraction,critical

# Performance benchmarks
./harness/cli.py bench --targets wolfram,python,julia --output results/

# Validate all TOML files
./harness/cli.py validate tests/

# Generate HTML report
./harness/cli.py report --input results/ --output report.html
```

---

## 7. Wolfram Oracle Generation

### Workflow

1. **Parse TOML**: Extract `oracle.commands`
2. **Execute in Wolfram**:
   ```python
   from wolframclient.evaluation import WolframLanguageSession

   session = WolframLanguageSession()
   session.evaluate('Needs["xAct`xTensor`"]')
   result = session.evaluate(oracle_commands)
   ```
3. **Serialize Result**: Convert to JSON-compatible format:
   ```python
   {
     "expression": "T[-a, -b]",
     "full_form": "Tensor[T, {-a, -b}]",
     "properties": {
       "Rank": 2,
       "Symmetry": "Symmetric[{1, 2}]",
       "DependenciesOf": ["M"]
     },
     "hash": "sha256:..."
   }
   ```
4. **Store**: `oracle/test_id.json`

### Comparison Logic

```python
def compare_results(oracle, implementation):
    """Compare implementation result against oracle."""
    checks = []

    # 1. Exact string match (canonical form)
    if oracle["expression"] == implementation["expression"]:
        checks.append(("exact_match", True))

    # 2. Structural equivalence (same term structure)
    elif equivalent_structure(oracle["full_form"], implementation["full_form"]):
        checks.append(("structural_match", True))

    # 3. Property match (rank, symmetry, etc.)
    checks.append(("properties",
                   oracle["properties"] == implementation["properties"]))

    # 4. Numerical tolerance (for component tests)
    if "numeric_value" in oracle:
        checks.append(("numeric",
                       abs(oracle["numeric_value"] - impl["numeric_value"]) < 1e-10))

    return all(passed for _, passed in checks)
```

---

## 8. Notebook Extraction Strategy

### Target Files

- `resources/xAct/xTensor/xTensorTests.nb`
- `resources/xAct/Documentation/English/*.nb`

### Extraction Pipeline

```python
# extractor.py
import nbformat
from wolframclient.serializers import export

def extract_tests_from_notebook(nb_path):
    """Convert Wolfram notebook to TOML test cases."""
    nb = nbformat.read(nb_path, as_version=4)
    tests = []

    for cell in nb.cells:
        if cell.cell_type == 'code':
            # Parse Input/Output pairs
            input_code = cell.source
            expected_output = cell.outputs[0] if cell.outputs else None

            # Identify test patterns
            if is_test_cell(input_code):
                test = {
                    'id': generate_id(input_code),
                    'operations': parse_operations(input_code),
                    'expected': parse_output(expected_output),
                    'oracle': {'commands': input_code}
                }
                tests.append(test)

    return tests

def is_test_cell(code):
    """Heuristic: contains DefManifold, DefTensor, or assertion patterns."""
    return any(keyword in code for keyword in
               ['DefManifold', 'DefTensor', 'ToCanonical', '==='])
```

### Manual Curation

After extraction:
1. Review auto-generated tests
2. Add tags (`basic`, `critical`, `edge-case`)
3. Add expected metrics (execution time from Wolfram baseline)
4. Group related tests
5. Add descriptive names

---

## 9. Performance Comparison Report

### Output Format (JSON)

```json
{
  "timestamp": "2026-01-08T10:30:00Z",
  "test_suite": "xAct Core",
  "implementations": {
    "wolfram": {"version": "14.3.0"},
    "python": {"version": "0.1.0", "sympy": "1.12"},
    "julia": {"version": "0.1.0", "julia": "1.12.3"}
  },
  "results": [
    {
      "test_id": "canonical_riemann_001",
      "metrics": {
        "execution_time_ms": {
          "wolfram": 45,
          "python": 187,
          "julia": 62
        },
        "memory_mb": {
          "wolfram": 12,
          "python": 28,
          "julia": 15
        },
        "compilation_overhead_ms": {
          "wolfram": 0,
          "python": 0,
          "julia": 3200
        }
      },
      "correctness": {
        "python": "PASS",
        "julia": "PASS"
      }
    }
  ],
  "summary": {
    "total_tests": 150,
    "python": {"passed": 142, "failed": 8, "avg_speedup": 0.24},
    "julia": {"passed": 148, "failed": 2, "avg_speedup": 0.73}
  }
}
```

### Visualization

Generate:
- Speedup bar charts (by operation type)
- Memory usage comparison
- Correctness percentage by category
- Scaling curves (problem size vs time)

---

## 10. Advantages of TOML Over YAML

1. **Less Ambiguous**: No issues with `on`, `off`, `yes`, `no` being interpreted as booleans
2. **Better Multi-line Strings**: Triple quotes `"""..."""` are clearer than YAML's `|` or `>`
3. **Explicit Types**: No guessing if `1.0` is a float or string
4. **Native Python Support**: `tomllib` in Python 3.11+, `tomli` for earlier versions
5. **Julia Compatible**: Julia's `Pkg.toml` ecosystem already uses TOML
6. **Better for Configuration**: TOML was designed for config files, not serialization
7. **No Indentation Hell**: More forgiving with whitespace
8. **Comments Are First-Class**: `#` comments are clearer

---

## 11. Python Requirements

```toml
# pyproject.toml
[project]
name = "xact-harness"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "wolframclient>=1.4.0",
    "tomli>=2.0.0; python_version < '3.11'",  # TOML parser
    "jsonschema>=4.0.0",                       # Schema validation
    "click>=8.0.0",                            # CLI framework
    "rich>=13.0.0",                            # Pretty terminal output
    "numpy>=1.24.0",
    "pandas>=2.0.0",                           # Results analysis
    "matplotlib>=3.7.0",                       # Plotting
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

---

## 12. Julia TOML Support

Julia has native TOML support via `TOML.jl` (in standard library):

```julia
# harness/julia/loader.jl
using TOML

struct TestCase
    id::String
    name::String
    operations::Vector{Dict}
    expected::Dict
end

function load_test_file(path::String)::Dict
    return TOML.parsefile(path)
end

function load_test_suite(directory::String)::Vector{Dict}
    tests = []
    for file in readdir(directory, join=true)
        if endswith(file, ".toml")
            push!(tests, load_test_file(file))
        end
    end
    return tests
end
```

---

## 13. Implementation Roadmap

### Phase 1: Foundation (Week 1)
1. Define JSON Schema for TOML test format
2. Create Python TOML loader with validation
3. Implement Wolfram oracle runner
4. Write 10-15 manual TOML test cases

### Phase 2: Extraction (Week 2)
5. Write notebook → TOML extractor
6. Extract tests from xTensorTests.nb
7. Curate and organize tests by category
8. Generate full oracle database

### Phase 3: Harness (Week 3)
9. Build Python test runner
10. Build Julia test runner (with TOML.jl)
11. Implement comparison logic
12. Add performance benchmarking

### Phase 4: Validation (Week 4)
13. Run full test suite
14. Analyze failures and discrepancies
15. Generate comparison reports
16. Document findings

---

## 14. Open Questions for Implementation

1. **Symbolic Expression Representation**:
   - How to handle language-specific ASTs?
   - Universal intermediate representation?
   - Suggestion: Use string canonical form + properties dict

2. **Dummy Index Handling**:
   - Different languages rename dummies differently
   - Need equivalence checker beyond string matching

3. **Performance Baseline Drift**:
   - Should oracle include timing data?
   - How to handle machine-specific variance?
   - Suggestion: Store percentile ranges, not point estimates

4. **Failure Taxonomy**:
   - Wrong result vs timeout vs crash vs not-implemented
   - Need granular error reporting

5. **Incremental Implementation**:
   - How to mark tests as "expected fail" during development?
   - Skip vs XFAIL (expected failure)?

---

## 15. Performance Metrics

Track all requested metrics:

1. **Execution Time**: Wall-clock time for operations (median over runs)
2. **Compilation/Startup Overhead**: Package load time + JIT compilation (Julia)
3. **Memory Usage**: Peak RAM and allocation patterns
4. **Symbolic Simplification Depth**:
   - Number of terms before/after canonicalization
   - Reduction factor for simplification effectiveness

---

## 16. Test Coverage Strategy

**Approach**: Regression test suite extracted from documentation notebooks

**Priority Operations** (all covered equally):
- Index manipulation (contraction, raising/lowering, dummy renaming)
- Canonicalization (ToCanonical via Butler-Portugal algorithm)
- Curvature tensors (Riemann, Ricci, Einstein)
- All core features from xCore, xPerm, xTensor

**Extraction Sources**:
- xTensorTests.nb
- xTensorDoc.nb
- xPermDoc.nb
- xCobaDoc.nb
- Example notebooks (ButlerExamples.nb, etc.)

---

## Summary

This design provides:
- ✅ Language-agnostic TOML format
- ✅ Wolfram oracle for ground truth
- ✅ Comprehensive metrics (time, memory, startup, simplification depth)
- ✅ Regression test extraction from notebooks
- ✅ Focus on xCore/xPerm/xTensor
- ✅ Python + Julia targets
- ✅ Explicit, unambiguous syntax via TOML
- ✅ Native support in target languages

The framework enables systematic migration validation and performance comparison across implementations while maintaining mathematical correctness through oracle testing.
