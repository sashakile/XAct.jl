---
date: "2026-05-07"
project: "unify-expression-parser"
sessions_analyzed: 0
type: reflection
---

## Project-Specific AI Context
_Last reflected: 2026-05-07 · 1 session analyzed_

### Conventions
- **XAct.jl** is a Julia package in the GR/tensor algebra domain. Python tooling is a secondary concern; always invoke via `uv run` (never bare `python`).
- Three-tool workflow is mandatory: **wai** (research/design decisions), **bd** (issue tracking), **openspec** (specs/proposals). Run `wai status` at session start to orient — it surfaces active projects, phases, and suggestions in one call.
- Issue creation precedes code. `bd create` before touching implementation, always.
- TDD is non-negotiable: red → green → refactor in that order. Refactoring tickets must be **separate** from feature tickets — not bundled.
- `wai search "<topic>"` before any research or ticket creation to avoid rediscovering documented patterns.

### Common Gotchas
- **Never use `bd edit`** — opens `$EDITOR` (vim/nano) and blocks the agent. Use inline flags: `bd update <id> --title/--description/--notes/--design`.
- Do NOT use TodoWrite, TaskCreate, or markdown files for task tracking. All tracking goes through `bd`.
- `.wai/` workspace is new (initialized in commit `05a9a6a`). The `.wai/projects/` directory is untracked — do not assume prior research artifacts exist; verify with `wai status` or `ls`.
- 58 of 75 open beads issues are in `ready` state — run `bd ready` before creating new issues to avoid duplicating existing work.
- `openspec/AGENTS.md` must be read before any proposal, spec, or architecture-level change. Check it whenever the work sounds ambiguous or touches new capabilities.

### Steps That Tend to Require Multiple Tries
- **Session close**: full checklist is required — `git status` → `git add` → `git commit` → `git push` **and** `bd dolt push`. Work is not done until both git and beads are pushed.
- **Python tool invocation**: always `uv run pytest tests/ ...`, never `.venv/bin/python` or bare `python`.
- **Parallel issue creation**: when creating multiple issues, use parallel subagents — sequential `bd create` calls are slower than necessary.

### Architecture Notes
- Two active work streams with distinct phases: **unify-expression-parser** is in implement phase at 75% complete (18/24 tasks); **add-cross-adapter-benchmark-suite** is in early design at 0/18. Treat them differently — the parser unification is nearly done and should be driven to close; the benchmark suite needs design work before any implementation tickets.
- Project is post-v0.7.2. Recent commits added textbook GR regression tests, indicating the test suite is expanding into physics-domain validation beyond pure unit tests. New tests should follow this pattern where applicable.
- `bd dolt push` is a separate sync step from `git push` — both are required at session end to keep issue state and code in sync with remotes.