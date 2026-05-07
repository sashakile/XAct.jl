<!-- WAI:START -->
# Workflow Tools

This project uses **wai** to track the *why* behind decisions — research,
reasoning, and design choices that shaped the code. Run `wai status` first
to orient yourself.

Detected workflow tools:
- **wai** — research, reasoning, and design decisions
- **beads** — issue tracking (tasks, bugs, dependencies). CLI command: **`bd`** (not `beads`)
- **openspec** — specifications and change proposals (see `openspec/AGENTS.md`)

> **CRITICAL**: Apply TDD and Tidy First throughout — not just when writing code:
> - **Planning/task creation**: each ticket should map to a red→green→refactor cycle; refactoring tasks must be separate tickets from feature tasks.
> - **Design**: define the test shape (inputs/outputs) before designing the implementation.
> - **Implementation**: write the failing test first, then make it pass, then tidy in a separate commit.

> **When beginning research or creating a ticket**: run `wai search "<topic>"` to check for existing patterns before writing new content.

## Quick Start

1. `wai sync` — ensure agent tools are projected
2. `wai status` — see active projects, phase, and suggestions
3. `bd ready` — find available work items

When context reaches ~40%: stop and tell the user — responses degrade past
this point. Recommend `wai close` then `/clear` to resume cleanly.
Do NOT skip `wai close` — it enables resume detection.

## Detailed Instructions

Full workflow reference — session lifecycle, capturing work, command cheat
sheets, cross-tool sync, and PARA structure — lives in **`.wai/AGENTS.md`**.
Read it at the start of your first session or when you need detailed guidance.

Keep this managed block so `wai init` can refresh the instructions.

<!-- WAI:END -->

<!-- WAI:REFLECT:REF:START -->
## Accumulated Project Patterns

Project-specific conventions, gotchas, and architecture notes live in
`.wai/resources/reflections/`. Run `wai search "<topic>"` to retrieve relevant
context before starting research or creating tickets.

> **Before research or ticket creation**: always run `wai search "<topic>"` to
> check for known patterns. Do not rediscover what is already documented.
<!-- WAI:REFLECT:REF:END -->


<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# sxAct Claude Instructions

## Development Workflow

- **CRITICAL: follow TDD and Tidy First** for all implementation tasks.
    - **TDD (Test-Driven Development):** Write the test case *before* the implementation code. Ensure it fails first, then implement the fix/feature.
    - **Tidy First:** Before adding new functionality, perform any necessary cleanup or refactoring of the surrounding code to make the new change easier to implement and maintain.

## Commands

Always use `uv` to run Python tools:

```
uv run pytest tests/ ...
uv run python ...
```

Never invoke `.venv/bin/python` or `python` directly.
