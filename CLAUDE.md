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
