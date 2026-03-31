## 1. Phase A — Error guard (eliminates silent data loss)
- [ ] 1.1 Add detection in `_parse_monomial`: after parsing `Name[indices]`, if next char is `[`, raise `error("CovD bracket syntax CD[...][...] is not supported by ToCanonical. Use SortCovDs/CommuteCovDs for covariant derivative expressions.")`
- [ ] 1.2 Add test: `ToCanonical("CD[-a][V[-b]]")` raises error (not silently drops)
- [ ] 1.3 Add test: `Contract("CD[-a][V[-b]]")` raises error
- [ ] 1.4 Verify existing CovD tests still pass (`SortCovDs`, `CommuteCovDs` use separate parser)
- [ ] 1.5 Verify all 567 XTensor + 4951 fuzz tests pass

## 2. Phase B — Unified AST
- [ ] 2.1 Define `TensorFactor`, `CovDFactor`, `FactorNode` types alongside existing `FactorAST`
- [ ] 2.2 Update `_parse_monomial` to produce `FactorNode` (recognize `Name[idx][operand]` → `CovDFactor`)
- [ ] 2.3 Update `_term_key_str` to serialize `CovDFactor` as `"CD[-a][V[-b]]"` format
- [ ] 2.4 Update `_serialize` / `_serialize_terms` to emit CovD bracket notation
- [ ] 2.5 Update `_canonicalize_term` to pass `CovDFactor` through (canonicalize inner operand only)
- [ ] 2.6 Rename all `FactorAST` references to `TensorFactor` (or alias for backward compat)
- [ ] 2.7 Update `TermAST` to use `Vector{FactorNode}`
- [ ] 2.8 Add tests: `ToCanonical("CD[-a][S[-b,-c]]")` preserves CovD, canonicalizes inner `S`
- [ ] 2.9 Add tests: round-trip `ToCanonical(ToCanonical("CD[-a][V[-b]]"))` is idempotent
- [ ] 2.10 Add fuzz tests: random CovD expressions survive ToCanonical round-trip
- [ ] 2.11 Verify all existing tests pass (zero regressions)

## 3. Phase C — Retire string-based CovD parser
- [ ] 3.1 Rewrite `SortCovDs` to parse via `_parse_expression` (unified AST) instead of `_extract_covd_chain`
- [ ] 3.2 Rewrite `CommuteCovDs` to use unified AST
- [ ] 3.3 Remove `_extract_covd_chain`, `_split_expression_terms`, and helpers
- [ ] 3.4 Verify all SortCovDs/CommuteCovDs tests pass with new parser backend
- [ ] 3.5 Verify full test suite: 567 XTensor + 4951 fuzz + 35 SortCovDs tests
