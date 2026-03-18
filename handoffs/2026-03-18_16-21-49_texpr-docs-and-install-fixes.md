---
date: 2026-03-18T16:21:49-03:00
git_commit: 748a45b
branch: main
directory: /var/home/sasha/para/areas/dev/gh/sk/sxAct
issue: sxAct-ym5s, sxAct-9jxh
status: handoff
---

# Handoff: TExpr docs, getting-started overhaul, install instruction fixes

## Context

TExpr Stage 1 (typed expression layer) shipped last session with 128 Julia + 24 Python tests.
This session wrote the user-facing documentation for it and fixed install instructions across
the docs. The codebase is now in a fully documented, clean state with no in-progress work.

## Current Status

### Completed
- [x] **sxAct-ym5s** — `docs/src/guide/TExpr.md`: new user-facing typed API guide
- [x] **sxAct-9jxh** — `docs/src/getting-started.md`: Julia install section, typed API first, side-by-side comparison table
- [x] `docs/src/index.md`: Fast Track updated to typed syntax, link to TExpr guide
- [x] `docs/make.jl`: Guide section added with TExpr.md in nav
- [x] Post-review fixes (Rule of 5 pass): 13 findings resolved — code accuracy, broken anchor, private API call, LLM TL;DR admonitions, fail-state examples
- [x] **sxAct-c15s** (ticket created): track update of install instructions once packages are published to Julia General Registry / PyPI
- [x] Install instruction audit: Python notebook `!pip install xact-py` → git+https GitHub URL

### In Progress
- Nothing. Clean state.

### Planned (from `bd ready`)
- **sxAct-d0gf** (P2) — Colab demo notebook content (Julia + Python)
- **sxAct-rvzo** (P2) — Refactor sxAct to consume Elegua as external dependency (blocked on Elegua repo)
- **sxAct-c15s** (P3) — Update install instructions once xAct.jl is in registry and xact-py is on PyPI

## Critical Files

1. `docs/src/guide/TExpr.md` — new guide; covers @indices, tensor(), covd(), validation, Python, interop, architecture
2. `docs/src/getting-started.md` — overhauled; now leads with Julia install + typed API
3. `docs/src/index.md:13-33` — Fast Track updated to typed API syntax
4. `docs/make.jl:79` — Guide section added to nav
5. `packages/xact-py/src/xact/juliapkg.json` — `"path": "julia", "dev": true`; resolved via symlinks in dev, bundled via hatchling `force-include` in wheel builds
6. `packages/xact-py/pyproject.toml:21-28` — hatchling `force-include` bundles Julia src into wheel

## Recent Changes

- `docs/src/guide/TExpr.md` — new file (342 lines); full typed API guide with LLM TL;DR, 5 code examples, comparison table, architecture diagram, roadmap
- `docs/src/getting-started.md` — install section, LLM TL;DR, typed vs string comparison table, Python section improved
- `docs/src/index.md` — Fast Track code block + explanation updated; broken anchor fixed (`#2-` → `#4-reference-migration-rosetta-stone`)
- `docs/make.jl:79` — added `"Guide" => ["Typed Expressions (TExpr)" => "guide/TExpr.md"]`
- `notebooks/python/basics.qmd` + `.ipynb` + `docs/src/notebooks/basics_python.md` — PyPI install comment → git+https URL

## Key Learnings

1. **xact-py bundles Julia source in the wheel — no separate registry install needed**
   - `packages/xact-py/pyproject.toml` hatchling `force-include` copies `../../Project.toml` and `../../src` into `xact/julia/` inside the wheel
   - `juliapkg.json` `"path": "julia"` resolves to the bundled copy at install time
   - In the dev repo, `packages/xact-py/src/xact/julia/` is symlinks to repo root
   - So `pip install "git+https://...#subdirectory=packages/xact-py"` is fully self-contained

2. **Review found 3 code snippets with accuracy bugs (private API, undefined variables)**
   - `_to_string()` is private; user docs should use the typed overload directly (`CommuteCovDs(expr, ...)`)
   - Arithmetic and covd() snippets referenced undefined tensors `:S` and `:phi`
   - Always make code examples self-contained or explicitly note assumed setup state

3. **Anchor links break when section numbers change**
   - `index.md` had `#2-reference-migration-rosetta-stone`; section became #4 after this update
   - Fixed, but worth noting: Documenter.jl anchors include the section number prefix

## Open Questions

- [ ] Should `docs/src/guide/TExpr.md` Architecture section be moved to `docs/src/architecture.md` instead? Currently left in place (end of page) as it's useful context; low priority to move.
- [ ] xact-py PyPI publication timeline — depends on sxAct-v660 (Julia registry) and a separate PyPI decision

## Next Steps

1. **Colab demo notebook content** (sxAct-d0gf, P2)
   - Add substantive Julia + Python cells to the existing notebook stubs
   - `notebooks/julia/basics.qmd` and `notebooks/python/basics.qmd` are the sources

2. **Elegua dependency refactor** (sxAct-rvzo, P2)
   - Blocked on `elegua-7bx` and `elegua-8f5` in the Elegua repo
   - Do not start until Elegua tracer bullet passes

3. **Update install instructions when published** (sxAct-c15s, P3)
   - Julia: `Pkg.add(url=...)` → `Pkg.add("xAct")`
   - Python: `pip install git+https://...` → `pip install xact-py`
   - Files to update: `docs/src/installation.md`, `docs/src/getting-started.md` TL;DR, `notebooks/python/basics.qmd`, `notebooks/julia/basics.qmd`

## Artifacts

**New files:**
- `docs/src/guide/TExpr.md`
- `handoffs/2026-03-18_16-21-49_texpr-docs-and-install-fixes.md` (this file)

**Modified files:**
- `docs/src/getting-started.md`
- `docs/src/index.md`
- `docs/make.jl`
- `notebooks/python/basics.qmd` + `notebooks/python/basics.ipynb`
- `docs/src/notebooks/basics_python.md`

**Not committed:** nothing — clean working tree (beads backup files excluded)

## References

- TExpr design spec: `plans/2026-03-17-typed-expression-api.md`
- TExpr TDD spec: `plans/2026-03-17-texpr-tdd-spec.md`
- Tracking ticket for publish-day install updates: `sxAct-c15s`
- Memory: all project state in `bd memories` (beads) — run `bd prime` on session start
