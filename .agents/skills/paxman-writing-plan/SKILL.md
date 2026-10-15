---
name: paxman-writing-plan
description: "Use when you have a spec or requirements for a multi-step paxman task, before touching code. Creates a right-sized plan in docs/development/plans/YYYY-MM-DD-<slug>.md — hotfix, kernel, docs_site, or new capability. Triggers: write paxman plan, plan this fix, plan this capability, implementation plan. Replaces writing-plans for paxman (which is overkill for small fixes)."
---

# Paxman Writing Plan — Right-Sized

> **Why this exists:** `writing-plans` (171 lines, `docs/superpowers/plans/`, `superpowers:subagent-driven-development`, 2-5 min steps, code block per step) is overkill for paxman. A 1-line `E.164 MAX_WINDOW 32→64` fix generated 209 lines / 15 checkboxes / 14 steps with duplicated code — the agent spent longer *writing the plan* than fixing the code. This skill keeps the load-bearing parts and drops the ceremony. Synthesized from 39 existing paxman plans in `docs/development/plans/` (2026-08-30 e164-window-fix 209L, bic-grouped 299L, kernel-hardening 972L, versioned-docs 409L, bic-capability 1750L, money 5096L) and `HOW_TO_ADD_NEW_CAPABILITY.md` + `ARCHITECTURE.md`.

## Overview

Write a plan a capable paxman engineer can execute with zero interview. Right-sized by tier — **Small stays small** (80-250 lines), Large stays complete but not 5000 lines. Every plan is TDD, cites its sources, and is Momus-passable.

**Announce at start:** "I'm using the paxman-writing-plan skill to create the implementation plan."

**Save plans to:** `docs/development/plans/YYYY-MM-DD-<slug>.md` (paxman) or `.hermes/plans/YYYY-MM-DD-<slug>.md` (hermes). User preference overrides.

**Worktree:** If on a hotfix, the branch should already exist via `using-git-worktrees` from the latest tag (`git describe --tags --abbrev=0`, now `v0.2.1`) into `.worktrees/hotfix-*`. Don't create the worktree inside the plan.

## Classify First — Don't Plan Trivial Work

| Tier | When | Files touched | Plan? | Typical size |
|---|---|---|---|---|
| **Trivial** | typo, copy fix, 1-line config | 1 | **No plan file** — 3-bullet todo inline, do it | 0 lines |
| **Small** | hotfix, single issue (#65, #41, #99, #51) | 1-3 files + tests | Yes — lean | 80-300 lines, 2-3 tasks |
| **Medium** | kernel/docs_site, 2-4 issues (#87/#88/#68) | 3-8 files | Yes — with Background context | 350-1000 lines, 3-6 tasks |
| **Large** | new capability (IBAN/BIC/SI) or staged pipeline | 13+ files via `tools/new_capability.py` | Yes — full capability shape | 1200-2000 lines, 8-13 tasks |

If Classify is Trivial, **stop** — don't invoke `paxman-momus-review` either (suppressed).

## What Every Plan Keeps (non-negotiable)

1. **Header** — Goal / Architecture / Tech Stack / References (all with paths:lines).
2. **File Structure** — exact `Create:` / `Modify:` / `Test:` paths. No vague "update relevant files".
3. **TDD per task** — failing test first, then minimal fix, then green. One QA block per task.
4. **Paxman gates** — `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run import-linter lint && uv run pytest -q` (+ coverage 95) cited as final verify; parity suites named when kernel/grammar touched.
5. **No placeholders** — never `TBD`, `TODO`, `add appropriate handling`, `similar to Task N`.
6. **Type consistency** — signatures/names match across tasks; one `Notation` shape, one `Contract` shape.
7. **Provenance & invariants** — cite `HOW_TO_ADD_NEW_CAPABILITY.md`, `ARCHITECTURE.md`, `docs/adr/*`, `paxman/core/domain.py:Rule`, `paxman/engine/orchestrator.py` when relevant; note `frozen=True, slots=True` for Notations, `frozen=True` without slots for Contracts.

## What This Skill Drops (vs writing-plans)

- **2-5 minute micro-steps** → 2-4 meaningful steps per task (Write failing test → Implement → Verify). No `Run it to make sure it fails` as a separate checkbox per step; collapse to one `Run:` per task.
- **`Interfaces: Consumes/Produces` per task** → **only for Large** where Task N's output is Task N+1's input (notation → contract → grammar). Small/Medium: omit, or one-line `Depends on: Task 1`.
- **Code block per step** → one reference snippet or test name per task, not 5 duplicated `def test_...` blocks. Link to `paxman/capabilities/<Name>/` precedent instead of pasting 40 lines that will drift.
- **Commit per step + Expected: FAIL with "..."** → one commit per task, one `Expected: PASS` per verify. Don't prescribe `Expected: FAIL with "function not defined"` unless the failure mode is the point.
- **`docs/superpowers/plans/` + `superpowers:subagent-driven-development` header** → paxman paths + `tdd` + `verification-before-completion` + `paxman-momus-review` gate.
- **Scope Check sub-project split** → paxman already splits via `tools/new_capability.py` (13 files + wiring) and `MILESTONE.md`. Mention only if spec truly spans 2 capabilities.
- **Execution handoff choice** → single line: "Plan saved. Execute task-by-task via `tdd`; review with `paxman-momus-review` then `paxman-oracle-review`."

## Plan Document Header

Every plan MUST start with this header:

```markdown
# [Feature Name] Implementation Plan (issue #NN)

> **For workers:** Execute task-by-task via `tdd` + `verification-before-completion`. Review gate: `paxman-momus-review` (plan), `paxman-oracle-review` (after impl).

**Goal:** [One sentence — what canonicalizes, what status changes, what issue closes]

**Architecture:** [2-4 sentences — which grammar/rule/contract changes, which view/stage, why this approach, what is NOT changed]

**Tech Stack:** Python 3.11+, uv, ruff, strict pyright, import-linter, pytest (markers: unit/capability/integration/property), `paxman/core/grammar` stage or `paxman/capabilities/<Name>`.

**References:** Issue #NN, `paxman/capabilities/<Name>/grammar/...:L-L`, `paxman/core/grammar/...:L-L`, `HOW_TO_ADD_NEW_CAPABILITY.md` step, `docs/development/research/YYYY-MM-DD-*.md` §, `tests/capabilities/<name>/...`

**Branch:** `fix/<slug>` or `feature/<cap>` (hotfixes cut from `git describe --tags --abbrev=0`)

---
```

## File Structure

Before tasks, lock decomposition. Example:

```markdown
## File Structure

- Modify: `paxman/capabilities/Phone/grammar/e164_recognition.py` — `_E164_MAX_WINDOW` and comment
- Test: `tests/capabilities/phone/test_grammar.py` — spaced window guards (capability-layer)
- Docs: `CHANGELOG.md` — Fixed entry

No new modules; no `paxman/core` change (or: `paxman/core/grammar/scan_context.py` — `stripped_chars` flag).
```

For Large, list ALL 13 scaffolder files plus which ones you fill (notation, contract, capability, grammar, rule, data). Note generated data via `tools/regenerate_*_data.py --check`.

## Task Structure

### Small (hotfix) — 2-3 tasks

```markdown
### Task 1: Reproduce (#NN) — failing guard

**Files:** `tests/capabilities/<name>/test_grammar.py`

**Goal:** Prove the bug with a red test.

- [ ] Add failing test(s): `test_spaced_15_digit` (15 digits + 2/3-char gaps → 44/58 chars). Run: `uv run pytest tests/... -k test_spaced -v` → Expected: FAIL (0 matches due to max_window 32).

### Task 2: Fix — minimal change

**Files:** `paxman/capabilities/Phone/grammar/e164_recognition.py:32-38`

**Goal:** Raise window 32→64 with worst-case comment + `#65`.

- [ ] Change `_E164_MAX_WINDOW = 64` + comment showing `15 + 14*3 + 1 = 58`. Verify: `uv run pytest tests/... -k test_spaced -v` → PASS; `uv run pytest tests/capabilities/phone -q` → PASS.

### Task 3: Regression + changelog

**Files:** `CHANGELOG.md`

- [ ] Gate: `uv run ruff check paxman/ tests/ && uv run ruff format --check paxman/ tests/ && uv run pyright && uv run import-linter lint && uv run pytest -q` → all green, coverage ≥95.
```

One checkbox per task is valid for Small. Two if you need "write test" + "verify". Do NOT create 5 steps with `Step 1: Write...`, `Step 2: Run...`.

### Medium (kernel/docs) — 3-6 tasks, add Background

```markdown
## Background the implementer needs

### Current state (verbatim)

`paxman/core/grammar/engine_loop.py:119` does `if view_name == "idna":` … (paste the 5-line block, with line numbers).

### Design decisions (locked)

1. Flag name: `stripped_chars: str | None` on `View` … 2. Order: boundary re-check before trailing extension … etc.

### Task 1: `stripped_chars` flag on View / ScanContext / IDNAFold

**Files:** `paxman/core/grammar/scan_context.py`, `paxman/core/grammar/normalizers.py`, `tests/unit/test_kernel_stripped_chars.py` (create)

- [ ] Failing test: `test_idnafold_declares_stripped_chars` → FAIL (no attr). Implement: add field `stripped_chars: str | None = field(default=None)` + `ScanContext.view(..., stripped_chars=...)` + `IDNAFold.stripped_chars = "\t\n\r"`. Verify: `uv run pytest tests/unit/test_kernel_stripped_chars.py::test_idnafold -v` → PASS.
- [ ] Regression: `uv run pytest tests/unit -q` (or targeted). Commit: `fix(kernel): add stripped_chars flag (#87)`.
```

Medium keeps one Background block (verbatim + decisions) so the next engineer doesn't re-derive. Still 2-4 bullets per task, not 6 steps.

### Large (new capability) — 8-13 tasks, notation→contract→grammar→rules

Follow `HOW_TO_ADD_NEW_CAPABILITY.md` Step 0 first:

```bash
uv run python tools/new_capability.py <PackageName> --name <snake> --authority ... --spec-name ... --spec-url ... --publication-year ... --default-format ...
```

Then tasks map to the scaffolder's files:

```markdown
### Task 1: Notation — frozen+slots (AGENTS.md § Conventions)

**Files:** `paxman/capabilities/<Name>/notation.py`, `tests/capabilities/<name>/test_notation.py`

- [ ] Failing test: `test_frozen_slots_hash` → FAIL. Implement: `@dataclass(frozen=True, slots=True) class <Name>Notation: ...`. Verify: `uv run pytest tests/.../test_notation.py -v` → PASS.
```

Chain: Task 1 Notation → Task 2 Contract (DEFAULT/OFFERED) → Task 3 Authority tables → Task 4 Generator → Task 5 Grammar(s) → Task 6 Rules (one publication per file) → Task 7 `format_value()` seam → Task 8 Registration → Task 9 Cross-layer consistency → Task 10 Pipeline + determinism → … Docs counts. Each task still TDD + `paxman-momus-review`-passable QA.

Omit `Interfaces: Consumes/Produces` unless Task 5 truly imports `Notation` shape from Task 1 — then one line: `Depends on: Task 1 Notation`.

## No Placeholders

Never write: `TBD`, `TODO`, `implement later`, `fill in details`, `Add appropriate error handling`, `Write tests for the above` (without test name), `Similar to Task N`. Every task names the file, the test, and the `uv run` verify.

## Self-Review (lightweight, before saving)

Run yourself (no subagent dispatch):

1. **Spec coverage:** Each issue/requirement has a task? Any gap → add task.
2. **Placeholder scan:** `rg -n "TBD|TODO|fill in|appropriate" <plan>` → 0 hits.
3. **Type consistency:** `Notation` fields, `Contract` defaults, `Provenance` citation match across tasks?
4. **Momus gate (dry):** Would `paxman-momus-review` say OKAY? References exist? Each task startable? QA has tool+steps+expected? If REJECT, fix before handing off.

If you find a gap, fix inline — no re-review loop.

## Execution Handoff

After saving:

```
Plan saved to docs/development/plans/YYYY-MM-DD-<slug>.md — 3 tasks, ~220 lines.

Execute task-by-task via tdd (failing test first). After impl, run paxman-momus-review on the plan file, then paxman-oracle-review on the branch diff before PR handoff.

If Small (1-3 files) and trivial verification, inline execution is fine — don't dispatch 3 subagents for 3 tasks.
```

Do NOT offer `Subagent-Driven vs Inline` choice with REQUIRED SUB-SKILL boilerplate. For Large, suggest `dispatching-parallel-agents` or `subagent-driven-development` only if tasks are independent (notation/contract can parallelize).

## Sizing Heuristics from paxman/plans/

- **Small 209-351L** (e164 209, bic-grouped 299, scanner-right-gap 341, unicode-property 351) → 3 tasks × 12-16 checkboxes in old style = ~200L. New style → same tasks × 1-2 checkboxes = 120-200L, plan writes in ~1/3 time, same signal.
- **Medium 781-972L** (kernel-hardening 972, kernel-hardening-2 781) → 6 tasks × 42 checkboxes = verbose. New → 6 tasks × ~3 bullets + one Background block = 400-600L.
- **Large 1316-5096L** (iban 1245, bic 1750, si 2570, money 5096) → 13 tasks with full copy-pasted `def test_...` per task exploded. New → keep HOW_TO order but reference scaffolder + one test name per task, not full bodies — cap at ~2000L.

## Common Mistakes (and the fix)

| Mistake | Reality |
|---|---|
| 5 micro-steps per task with `Expected: FAIL with "function not defined"` | One `Run: uv run pytest ... -k test_name -v → FAIL/PASS` per task is enough. |
| Pasting 40-line `def test_...` per task that duplicates scaffolder stubs | Name the test and location: `tests/capabilities/bic/test_notation.py::test_frozen_slots` — reader opens the file. |
| `Interfaces: Consumes/Produces` on a 1-issue hotfix | Omit for Small; use only when tasks share types. |
| `docs/superpowers/plans/` + superpowers header | `docs/development/plans/` + `tdd` + momus/oracle gates — paxman convention per `docs/development/AGENTS.md`. |
| No Branch / no References | Momus will REJECT — always include issue #, file:line, ADR/research citation. |
| Plan generated 5000L for `money` capability | That's HOW_TO's 13 files × full bodies. In the plan, reference the scaffolder + one-line per file; bodies live in the branch, not the plan file. |

## References

- `writing-plans` (upstream, 171L, `docs/superpowers`) — used as anti-template.
- `HOW_TO_ADD_NEW_CAPABILITY.md` (62K), `HOW_TO_ADD_NEW_GRAMMAR.md`, `ARCHITECTURE.md` (3,554L), `AGENTS.md` (10K), `docs/adr/*`
- 39 paxman plans in `docs/development/plans/` — esp. `2026-08-30-e164-window-fix.md`, `2026-08-30-bic-grouped-display.md`, `2026-08-30-grammar-kernel-hardening.md`, `2026-08-30-versioned-docs.md`
- Gates: `paxman-momus-review` (plan executability), `paxman-oracle-review` (post-impl), `verification-before-completion`, `tdd`, `using-git-worktrees` (hotfix from tag), `dispatching-parallel-agents`
