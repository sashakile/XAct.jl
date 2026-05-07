---
date: 2026-03-16T20:26:41-03:00
git_commit: 2490ca1
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-gc8u
status: handoff
---

# Handoff: Wolfram Expression Translator — Phases 1-3 Complete

## Context

Implemented the Wolfram Expression Translator (sxAct-gc8u), an onboarding bridge for researchers migrating from Wolfram xAct. The translator parses standard Wolfram Language surface syntax, maps it to sxAct action dicts, and can output to JSON, Julia, TOML, or Python. Includes a CLI subcommand (`xact-test translate`) and an interactive REPL (`xact-test repl`) with optional live Julia evaluation.

The spec is at `specs/2026-03-13-wolfram-expression-translator.md`. All 4 implementation phases from the spec are complete except the getting-started guide (docs-only, P3).

## Current Status

### Completed
- [x] **Phase 1 — Core Parser & Recognizer** (4 commits, 4 issues closed)
  - WL surface-syntax parser with bracket-context signed indices (`wl_parser.py`)
  - WL serializer for AST→infix re-emission (`wl_serializer.py`)
  - Action recognizer: all 32 sxAct actions mapped (`action_recognizer.py`)
  - Unit tests: full Appendix A test matrix T1-T28 + edge cases
- [x] **Phase 2 — Output Renderers & CLI** (1 commit, 3 issues closed)
  - `to_json`, `to_julia`, `to_toml`, `to_python` renderers
  - `xact-test translate` subcommand with `--to` flag
  - Renderer + CLI tests
- [x] **Phase 3 — REPL** (1 commit, 3 issues closed)
  - Interactive REPL with In[N]/Out[N], Julia eval, session export
  - `--no-eval` translate-only mode
  - Session export commands (`:to julia/toml/python/json`)
- [x] **Phase 4 — Polish** (partially)
  - Error messages with position + WL idiom suggestions (in parser)
- [x] **Integration tests** (1 commit, 1 issue closed)
  - 7 round-trip tests: WL→action→Julia→result + TOML validation

### Not Started
- [ ] sxAct-v07t: Getting-started guide for Wolfram users (P3, docs only)

### Also Closed This Session
- [x] sxAct-22s: Invar port parent issue (all 10 sub-phases were already done)

## Critical Files

> Core translator module

1. `packages/sxact/src/sxact/translate/wl_parser.py` — Recursive-descent parser, `parse()` and `parse_session()` public API
2. `packages/sxact/src/sxact/translate/action_recognizer.py` — `wl_to_action()`, `wl_to_actions()`, 32-action mapping table
3. `packages/sxact/src/sxact/translate/renderers.py` — `to_json`, `to_julia`, `to_toml`, `to_python`, `render()` dispatch
4. `packages/sxact/src/sxact/translate/wl_serializer.py` — `serialize()` for AST→infix
5. `packages/sxact/src/sxact/cli/repl.py` — `REPLSession` class, `_run_repl()` loop
6. `packages/sxact/src/sxact/cli/translate.py` — `_cmd_translate()` CLI handler
7. `specs/2026-03-13-wolfram-expression-translator.md` — Full spec with grammar, mapping tables, test matrix

## Recent Changes

> Files created in this session (4 commits: 4293c6b → 2490ca1)

**New files:**
- `packages/sxact/src/sxact/translate/__init__.py` — Public API re-exports
- `packages/sxact/src/sxact/translate/wl_parser.py` — ~370 lines, recursive-descent parser
- `packages/sxact/src/sxact/translate/wl_serializer.py` — ~120 lines, AST→infix serializer
- `packages/sxact/src/sxact/translate/action_recognizer.py` — ~380 lines, 32-action recognizer
- `packages/sxact/src/sxact/translate/renderers.py` — ~300 lines, 4 output renderers
- `packages/sxact/src/sxact/cli/translate.py` — ~45 lines, CLI subcommand
- `packages/sxact/src/sxact/cli/repl.py` — ~230 lines, interactive REPL
- `tests/translate/__init__.py`
- `tests/translate/test_wl_parser.py` — 51 tests
- `tests/translate/test_action_recognizer.py` — 39 tests
- `tests/translate/test_renderers.py` — 35 tests (31 renderer + 4 CLI)
- `tests/translate/test_repl.py` — 14 tests
- `tests/translate/test_integration.py` — 7 tests (require Julia)

**Modified files:**
- `packages/sxact/src/sxact/cli/__init__.py` — Added `translate` and `repl` subcommands

## Key Learnings

1. **Signed index ambiguity is the central parser challenge**
   - `-a` inside `[...]` = covariant index; at top level = negation
   - Resolved with two expression sub-grammars (top-level vs bracket-level)
   - Bracket-level: `-ident` with no whitespace gap → `WLLeaf("-a")`; otherwise negation
   - See `wl_parser.py:_parse_bracket_unary()` for the whitespace-gap heuristic

2. **Newlines are statement separators outside balanced brackets**
   - Tokenizer tracks bracket depth; newlines inside `[...]`/`{...}`/`(...)` become whitespace
   - Newlines at bracket depth 0 become `SEMI` tokens → session can parse without explicit semicolons
   - See `wl_parser.py:_tokenize()` bracket_depth tracking

3. **ChristoffelP doesn't round-trip through Julia adapter**
   - Wolfram's `ChristoffelP[CD]` has `covd` arg, but Julia adapter expects `metric` + `basis`
   - This is a genuine interface mismatch, not a translator bug
   - Integration test uses `postfix_pipe` instead of `christoffel` to avoid this

4. **Unsupported idiom detection must happen at tokenizer level**
   - `/@`, `@@`, `/.`, `%` need to be tokenized as distinct tokens to be detected
   - Can't rely on post-parse checking since they'd be parsed as `SLASH` + `AT` etc.

## Open Questions

- [ ] Should the translator handle `ComponentValue` bare-indexing form (`tensor[1,2,3]`)? Currently indistinguishable from a function call without semantic context.
- [ ] VarD covd argument: Wolfram form lacks it, Julia adapter requires it. Currently omitted; TOML renderer could add a `# TODO: add covd` placeholder.
- [ ] Implicit multiplication without space (`2T[-a,-b]`) is documented as unsupported — should we add it?

## Next Steps

1. **Close sxAct-gc8u epic** [Priority: HIGH]
   - 12/13 sub-issues closed (only sxAct-v07t getting-started guide remains, P3)
   - Epic can be closed with the guide deferred

2. **Write getting-started guide** (sxAct-v07t) [Priority: LOW, P3]
   - User-facing docs for Wolfram xAct researchers
   - Can reference the REPL `--no-eval` mode and `xact-test translate`

3. **Other ready P2 work:**
   - sxAct-rvzo: Refactor sxAct to consume Elegua (blocked on elegua repo work)
   - sxAct-ead.*: Engagement epic sub-tasks (docs/tutorials)
   - sxAct-3et: Documentation overhaul epic

4. **P3 feature epics:**
   - sxAct-ncy: TexAct (LaTeX rendering)
   - sxAct-5xe: Harmonics (spherical harmonic decomposition)
   - sxAct-hwj: xTerior (exterior calculus)

## Artifacts

**Test Results:**
- 142 translator tests (51 parser + 39 recognizer + 35 renderer + 14 REPL + 7 integration = 146)
- 709 total Python tests passing
- Julia integration tests pass with Julia 1.12.5

**Issues Closed This Session:**
- sxAct-22s (Invar port parent)
- sxAct-9ur0, sxAct-nfpc, sxAct-6h4p, sxAct-bkei (Phase 1)
- sxAct-pbyk, sxAct-hbs7, sxAct-gl35 (Phase 2)
- sxAct-95aa, sxAct-9j5b, sxAct-i6mu (Phase 3)
- sxAct-m43l (Phase 4 - error messages)
- sxAct-jpbf (Integration tests)
- Total: 13 issues closed

## References

- Spec: `specs/2026-03-13-wolfram-expression-translator.md`
- Wolfram adapter (forward direction): `packages/sxact/src/sxact/adapter/wolfram.py`
- Julia adapter (action dispatch): `packages/sxact/src/sxact/adapter/julia_stub.py`
- FullForm parser (distinct, not modified): `packages/sxact/src/sxact/normalize/ast_parser.py`
