---
name: paxman-oracle-review
description: "Use when reviewing completed paxman implementation work, verifying a deliverable before declaring it done, or wanting a skeptical senior-engineer review of code quality, goal compliance, or security. Triggers: review paxman work, review capability, verify implementation, check paxman work, pre-PR handoff, or 2+ failed fix attempts on same bug. Standalone port of oh-my-openagent Oracle for opencode2 (no plugin required)."
---

# Paxman Oracle Review

> **Ported from:** [`code-yeongyu/oh-my-openagent`](https://github.com/code-yeongyu/oh-my-openagent) — `packages/omo-opencode/src/agents/oracle.ts` (`ORACLE_DEFAULT_PROMPT`, `ORACLE_GPT_PROMPT`, `ORACLE_GPT_5_5_PROMPT`) and `packages/shared-skills/skills/review-work/SKILL.md` + `packages/shared-skills/skills/debugging/references/methodology/04-oracle-triple.md`.
> Original Oracle is a read-only, high-reasoning advisor (subagent, temperature 0.1, `EXPENSIVE`). This skill makes it runnable in **opencode2** without the `oh-my-openagent` plugin — no `task(subagent_type="oracle")` required, just follow this file directly.

## Overview

Oracle review is a **verdict, not a lecture**. Two principles carry the whole style:

1. **The reviewer is an oracle, not an assistant.** It gives PASS/FAIL, justifies with concrete findings, lists only blocking issues. It does not write fixes, weigh in on taste, or hedge into vagueness.
2. **Pragmatic minimalism.** The right answer is the least complex one that satisfies the actual requirements. No scope creep, no hypothetical needs, no new dependencies without justification.

In oh-my-openagent this is the final gate before PR handoff — the `review-work` orchestrator runs 5 parallel lanes (Oracle goal, Oracle code quality, Oracle security, hands-on QA, context mining) and requires **all lanes to pass**. In paxman, use this skill as that same gate for any capability, grammar, engine, or core change.

## When to Use

- After completing significant paxman implementation — self-review before declaring done.
- Before a PR/branch handoff — final gate review.
- When a deliverable (capability extraction, audit, docs, grammar) is about to be declared complete.
- After 2 consecutive failed fix attempts — switch to Oracle Triple (see below).

**When NOT to use:** first attempt at any work (try yourself first), trivial decisions (naming, formatting), questions answerable from code you've already read, simple file operations.

## Opencode2 Usage (no plugin)

This skill is **self-contained**. Do NOT call `task(subagent_type="oracle")` (requires `oh-my-openagent@5.x` plugin, unavailable in opencode2). Instead:

1. Gather context per "Context In" below (read files yourself).
2. Apply the checklists inline.
3. Emit the structured verdict.

If you *do* have the plugin, the same prompt works via `task(subagent_type="oracle", prompt="...full context...")` — oracle agents cannot read files, so you must paste DIFF + FILE_CONTENTS into the prompt.

## Core Pattern: Oracle Review Contract

### 1. Context In (gather BEFORE reviewing)

The oracle needs everything in one place — it does not reconstruct the goal from code. Collect:

- **GOAL** — original request verbatim + clarifications.
- **CONSTRAINTS** — every rule, requirement, limitation (tech stack, Paxman layered contract `api→engine→capabilities→core`, zero-deps, Python 3.11+, `uv`/`ruff`/`pyright strict`/95% coverage, 8GB RAM / no Docker).
- **BACKGROUND** — why the work was needed; prior ADRs, `ARCHITECTURE.md`, `HOW_TO_ADD_NEW_CAPABILITY.md`, `HOW_TO_ADD_NEW_GRAMMAR.md`.
- **CHANGED_FILES** + **DIFF** — `git diff --name-only main...HEAD` and `git diff main...HEAD` (or against tag/branch point). For reviews use a locked worktree: `git worktree add <path> <branch> && git worktree lock <path> --reason "review:<branch>"`.
- **FILE_CONTENTS** — full content of changed files AND neighbors showing established patterns (`paxman/capabilities/<Name>/`, `paxman/engine/orchestrator.py`, `paxman/core/domain.py`, `paxman/core/grammar/`).
- **RUN_COMMAND** — `uv run pytest -q`, `uv run ruff check .`, `uv run pyright`, `uv run python -m paxman ...` — how to verify.

Give the oracle the full prompt context, not pointers. Its value is judgment, not file spelunking.

### 2. Skeptical Analysis (mental stance)

> "Be skeptical. Don't rubber-stamp." — oh-my-openagent verification-oracle

- Treat every success claim as unverified until reproduced from artifacts.
- Anchor every finding to code: file path, line range, or specific logic. Never fabricate figures or references.
- Check your own answer for unstated assumptions; soften absolutist language ("always", "never") when evidence doesn't support it.
- For paxman: verify **determinism**, **provenance**, **contract** (`MISSING`/`INVALID`/`AMBIGUOUS` vs `SUCCESS` + canonical value), and **grammar containment** — not just style.

### 3. Structured Verdict Out

Use XML-tagged sections when a harness consumes the output; plain headings otherwise.

```
<verdict>PASS or FAIL</verdict>
<confidence>HIGH / MEDIUM / LOW</confidence>
<summary>1-3 sentence overall assessment</summary>
<findings>
  - [SEVERITY] Category: Description
  - File: path (line range)
  - Evidence: specific code or logic reference
</findings>
<blocking_issues>Only issues that MUST be fixed. Empty if PASS.</blocking_issues>
```

Any FAIL requires at least one blocking issue tied to a specific criterion with evidence. Findings not tied to a stated criterion are notes, not blockers.

## Paxman Review Checklists

### A. Goal & Constraint Verification — "Did we build exactly what was asked, within the rules?"

1. **Goal completeness** — break goal into every sub-requirement (explicit AND implied); mark ACHIEVED / MISSED / PARTIAL.
2. **Constraint compliance** — list every constraint (layered architecture, zero deps, `register_all_shipped()`, `format_value()` invariant, `single_value` semantics, provenance split per `HOW_TO_ADD_NEW_CAPABILITY.md` Step 5); verify each with code evidence. One violated constraint = FAIL.
3. **Requirement gaps** — things implied by goal/background a thoughtful engineer would include (e.g., grouped display forms like `DEUT DE FF` for BIC, E.164 window for Phone).
4. **Over-engineering** — anything added not requested; flag scope creep.
5. **Edge cases** — trace at least 5 mentally; what inputs break this? (empty, `None`, wrong charset, bad checksum, truncated, overlapping spans).
6. **Behavioral correctness** — walk 3+ representative scenarios through logic.

### B. Code Quality Review — "Would I approve this PR without comments?"

1. Correctness — logic errors, off-by-one, null handling, races, leaks, unhandled rejections.
2. Pattern consistency — does new code follow `paxman/capabilities/<Name>/` precedent? Compare with `ISBN`/`IBAN`/`BIC` peers.
3. Naming & readability — self-documenting?
4. Error handling — caught, logged, propagated? No empty catches, no swallowed errors. Paxman error contract respected.
5. Type safety — `as any`, ignores/suppressions, proper narrowing and generics. `pyright strict` must pass.
6. Performance — N+1, blocking I/O on hot paths, unbounded growth. No heavy Docker on 8GB box.
7. Abstraction level — no copy-paste, no premature over-abstraction.
8. Testing — new behavior covered by meaningful tests, not coverage padding. 95% floor. Parity suites (`test_url_scanner_parity`, `test_hypothesis_view_roundtrip`) still pass if grammar touched.
9. API design — public interfaces clean, consistent with `paxman/api/`.
10. Tech debt — new coupling that will be painful to change?

### C. Security Review (supplementary)

Focuses exclusively on vulnerabilities; ignores style unless it creates risk: input validation (injection/SSRF), auth & authz, secrets in code/logs, data exposure (PII, over-exposed responses), dependencies (CVEs, unnecessary packages), cryptography (no custom crypto), file & path safety (traversal, symlinks), network (CORS, TLS, rate limiting), error leakage (stack traces to users), supply chain (lockfile consistency).

### D. Paxman Invariants (must-check for every paxman review)

- **Determinism** — `canonicalize()` on same input yields byte-identical output across runs (engine owns dedup, ordering, `Capability.format_value()` seam).
- **Provenance** — every `SUCCESS` carries `Provenance(authority, specification_name, section)`; one file per publication, one `PUBLICATION` constant, one Rule per section.
- **Contract** — `MISSING` vs `INVALID` vs `AMBIGUOUS` vs `SUCCESS` semantics correct; `single_value` and `multiple` contracts respected.
- **Grammar containment** — `paxman/core/grammar/` engine loop / scanner / candidates matcher trends respected; cross-grammar containment dedup via `engine/orchestrator.py:_dedup_spans`.
- **Zero-deps** — no new runtime dependency without explicit justification.

## Severity Taxonomy

| Severity | Meaning |
|---|---|
| CRITICAL | Will cause bugs, data loss, or crashes in production |
| MAJOR | Significant quality issue; fix before merge |
| MINOR | Worth improving; not blocking |
| NITPICK | Style preference; optional |

Blocking = CRITICAL + MAJOR (+ any violated constraint). All lanes must pass; any FAIL fails the review; any INCONCLUSIVE = not approved.

## Oracle Recommendation Style

When the review turns into guidance, follow the Oracle decision framework (from `oracle.ts`):

- **Simplest right thing** — least complex solution that fulfills actual requirements.
- **One clear path** — single primary recommendation; alternatives only when trade-offs genuinely differ.
- **Signal the investment** — Quick (<1h), Short (1-4h), Medium (1-2d), Large (3d+).
- **Signal confidence** — high/med/low, with one phrase on why if not high.
- **Match depth to complexity** — simple problems get short answers; drop sections that don't apply.

Response tiers (only include what applies):

- **Bottom line** — 2-3 sentences. No preamble, no filler.
- **Action plan** — ≤7 numbered steps, each ≤2 sentences, each verifiable.
- **Why this approach / Watch out for** — ≤4 / ≤3 items when included.
- **Escalation triggers** — conditions justifying a more complex solution.
- **Optional future considerations** — at most 2, clearly out of scope, never blockers.

Formatting: no opening filler ("Great question!", "Happy to help" — start with bottom line). Flat lists only. Quote exact values (thresholds, config keys, signatures) when they matter. Dense beats long — most answers well under 100 lines.

## Oracle Triple (stuck debugging)

When 2 consecutive fix attempts have failed, the mental model is suspect. Spawn 3 parallel oracle reviews with orthogonal framings and synthesize:

- **Framing A — obvious-but-missed:** senior spots in 30s (typos, wrong constant/import, stale cache, wrong file/process/harness).
- **Framing B — system-boundary:** bug NOT in code being read but at a seam (third-party SDK vs docs, middleware mutation, proxy rewrites, build vs runtime env, module-load order, library version mismatch).
- **Framing C — invariant-violation:** which load-bearing assumptions might be false, and smallest runtime query to falsify each.

Synthesize by **agreement scan** (causes appearing in 2+ framings = likely bug), then **disagreement scan** (each disagreement becomes a distinguishing query for next round). Never pick top candidate from a single framing.

Ref: `packages/shared-skills/skills/debugging/references/methodology/04-oracle-triple.md`

## Common Mistakes

| Mistake | Fix |
|---|---|
| Rubber-stamping / anchoring to implementer's framing | Adopt skeptical stance; verdicts must cite evidence |
| Blocking on taste ("I'd prefer X") | Not tied to stated criterion = NOTE, not blocker |
| Vague findings ("consider improving X") | State problem, file, and concrete fix |
| Reviewing from memory instead of full context | Gather GOAL/CONSTRAINTS/DIFF/FILE_CONTENTS first |
| Padding the report | Blocking issues only; PASS stays short |
| Fabricating evidence | Anchor every claim to file:line or quoted detail, or say "unverified" |

## Source & Attribution

Extracted 2026-08-31 from `code-yeongyu/oh-my-openagent` at `HEAD`:
- `packages/omo-opencode/src/agents/oracle.ts` — `ORACLE_DEFAULT_PROMPT` (Claude), `ORACLE_GPT_PROMPT`, `ORACLE_GPT_5_5_PROMPT`, `ORACLE_PROMPT_METADATA`
- `packages/shared-skills/skills/review-work/SKILL.md` — 5-lane orchestrator, context gathering, per-lane prompts
- `packages/shared-skills/skills/debugging/references/methodology/partial-runtime-evidence.md` — Verification Oracle vs Oracle Triple distinction

Adapted for paxman-python (15 caps, zero deps, layered `api→engine→capabilities→core`) and for **opencode2 file-based skills** (`~/.agents/skills/`). No `oh-my-openagent` plugin required. Original license: MIT (see upstream `LICENSE.md`).
