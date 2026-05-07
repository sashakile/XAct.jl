---
date: "2026-05-07"
project: "add-cross-adapter-benchmark-suite"
sessions_analyzed: 0
type: reflection
---

Looking at the project context from the system reminders, CLAUDE.md, and git status to synthesize the reflection.

## Project-Specific AI Context
_Last reflected: 2026-05-07 · 1 session analyzed_

### Conventions
- This is **XAct.jl** — a Julia package (likely tensor algebra / GR domain, given recent "textbook GR regression tests" commit). Python tooling exists alongside Julia code and is invoked via `uv run`.
- Three-tool workflow is mandatory: **wai** (research/design), **bd** (issue tracking), **openspec** (specs/proposals). Run `wai status` first every session to orient.
- Issue creation must precede code writing. Use `bd create` before touching implementation.
- TDD cycle is non-negotiable: red → green → refactor. Refactoring tickets must be **separate** from feature tickets.

### Common Gotchas
- `wai` was just initialized (`chore: init wai workspace` is the most recent commit). The `.wai/projects/` directory is untracked — expect the workspace to be new and sparse; don't assume prior research artifacts exist.
- Never use `bd edit` — it opens `$EDITOR` (vim/nano) and blocks agents. Use `bd update <id> --field=value` inline flags instead.
- Do NOT use TodoWrite, TaskCreate, or markdown task files. All task tracking goes through `bd`.
- Run `wai search "<topic>"` before starting any research or ticket — avoid rediscovering documented patterns.

### Steps That Tend to Require Multiple Tries
- **Python tool invocation**: always `uv run pytest` / `uv run python`, never bare `python` or `.venv/bin/python`.
- **Session close**: must follow the full checklist — `git status` → `git add` → `git commit` → `git push`. Work is not done until pushed.

### Architecture Notes
- Two active work streams: **add-cross-adapter-benchmark-suite** (design phase, 0/18 tasks) and **unify-expression-parser** (implement phase, 18/24 tasks complete). The benchmark suite is in early design; the parser unification is nearly done.
- Project is post-v0.7.2 release. Recent GR regression tests suggest the test suite is expanding into physics validation, not just unit tests.
- `bd dolt push` syncs beads to remote — run it alongside `git push` at session end to keep issue state in sync.