## ADDED Requirements

### Requirement: Unified Expression AST
The expression parser SHALL represent both flat tensor products and CovD application using a single AST type system (`TensorFactor` and `CovDFactor` as `FactorNode` union).

#### Scenario: Flat tensor product parsed correctly
- **WHEN** `_parse_expression("S[-a,-b] V[-c]")` is called
- **THEN** it returns a `TermAST` with two `TensorFactor` nodes: `S` with indices `["-a","-b"]` and `V` with index `["-c"]`

#### Scenario: CovD application parsed correctly
- **WHEN** `_parse_expression("CD[-a][V[-b]]")` is called
- **THEN** it returns a `TermAST` with one `CovDFactor` node: covd_name `:CD`, deriv_index `"-a"`, operand containing a `TensorFactor` for `V["-b"]`

#### Scenario: Nested CovD chain parsed correctly
- **WHEN** `_parse_expression("CD[-a][CD[-b][T[-c]]]")` is called
- **THEN** it returns a `TermAST` with one `CovDFactor` whose operand contains another `CovDFactor`, whose operand contains `TensorFactor` for `T["-c"]`

### Requirement: CovD Round-Trip Through ToCanonical
`ToCanonical` SHALL preserve CovD bracket structure and canonicalize the inner operand without dropping the derivative application.

#### Scenario: CovD expression survives ToCanonical
- **WHEN** `ToCanonical("CD[-a][S[-c,-b]]")` is called with `S` symmetric
- **THEN** the result is `"CD[-a][S[-b,-c]]"` (inner operand canonicalized, CovD preserved)

#### Scenario: ToCanonical is idempotent on CovD expressions
- **WHEN** `ToCanonical(ToCanonical("CD[-a][V[-b]]"))` is called
- **THEN** the result equals `ToCanonical("CD[-a][V[-b]]")`

### Requirement: CovD Detection Guard
Until the unified AST is fully implemented, the flat parser SHALL raise an explicit error when encountering CovD bracket syntax, rather than silently dropping the operand.

#### Scenario: Error on CovD in ToCanonical
- **WHEN** `ToCanonical("CD[-a][V[-b]]")` is called before Phase B is complete
- **THEN** an error is raised mentioning "CovD bracket syntax" and suggesting `SortCovDs`

#### Scenario: SortCovDs still works during transition
- **WHEN** `SortCovDs("CD[-b][CD[-a][V[-c]]]", :CD)` is called during any phase
- **THEN** it returns the correctly sorted result (unaffected by parser changes)

### Requirement: Single Parser Backend
After unification, `SortCovDs` and `CommuteCovDs` SHALL use `_parse_expression` (the unified parser) instead of the separate `_extract_covd_chain` / `_split_expression_terms` string-based parser.

#### Scenario: SortCovDs uses unified parser
- **WHEN** `SortCovDs` is called after Phase C
- **THEN** it parses the expression via `_parse_expression` into `TermAST` with `CovDFactor` nodes, not via `_extract_covd_chain`

#### Scenario: String-based CovD parser removed
- **WHEN** Phase C is complete
- **THEN** `_extract_covd_chain` and `_split_expression_terms` no longer exist in `Canonical.jl`
