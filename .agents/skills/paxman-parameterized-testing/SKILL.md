---
name: paxman-parameterized-testing
description: "Run a black-box parameterized UX sweep for any paxman capability: generate ~100 mixed clean/garbage inputs with per-input expected outcomes, execute them through the public canonicalize() API across capability-relevant contracts, and report divergences as findings. Use after a capability lands (UX acceptance), before releases touching shared layers, or to pin MISSING-vs-INVALID splits. Capability-independent; no source modifications."
---

# Paxman Parameterized Testing

Black-box acceptance sweep through the **public API only** — act as a library user, not a developer. Distilled from the Timezone + UtcOffset UX experiment (100 inputs × 2 capabilities × 5 contracts = 1000 calls, `docs/development/reports/2026-09-14-timezone-utcoffset-ux.md`).

## When to Use

- After a capability lands and merges — UX acceptance before release.
- After kernel/engine/core changes — unit suites prove no regression; this proves the *experience* (status splits, error messages, flag behavior) still reads sanely on realistic input.
- When a MISSING-vs-INVALID split or contract-flag semantic needs pinning beyond unit vectors.
- To generate follow-up issues with executed evidence (subset gaps, message quality).

**When NOT to use:** instead of unit/property tests (this complements them); for performance benchmarking (see `benchmarks/harness.py`); when the capability has fewer than ~20 meaningful input shapes (a hand-written table is cheaper).

## Core Decision: Expected Results Are Required

Record the expected outcome **per input, at generation time**, derived from the capability's own spec (edge table, resolution map, guide statuses) — not observed from the run. Expectations are what turn telemetry into a test: a run passes iff every row matches, and any mismatch is either a bug or a spec correction with evidence.

Cost control (this stays cheap):
- Expectations come from tables that already exist — translating a row into `(input, status[, value])` triples is mechanical, not creative.
- Parametrize by **equivalence class**, not by input: one expectation rule covers a family (e.g. "all curated keys → SUCCESS self"), instantiated across members.
- Genuinely unknown probes are allowed but must be marked `"mode": "explore"` (no expectation; reported as observations, never failures). Cap explore rows at ~20% — a sweep that is mostly explore is telemetry, rename it honestly.

## Protocol

### 1. Generate inputs (~100 per capability, seeded RNG)
- ~55 clean: every §2.1 RECOGNIZE form × case variants × flags-relevant shapes (fold, links, labels, gated forms on AND off) + cross-family probes (sibling-domain inputs that must MISSING).
- ~45 garbage: empty/whitespace, prose, glued runs, paths, over/under-length, unknown keys, truncated shapes, unicode lookalikes, multi-mention strings, boundary punctuation.
- Record `{"input", "expect_status", "expect_value"?, "mode": "assert"|"explore", "why"}` per row as JSON. Seed the RNG and record the seed.

### 2. Choose contracts (capability-relevant only)
- Always: `default`, one flag-on variant per capability flag (`suppress_common_words`, each `include_*`), one `year=` that drops the authority rule, one bad-`output_format` (records the `ContractError` UX — message must name the legal set).
- Never: combinatorial explosion over `excluded_rules`/`pinned_rules` (unit-test territory).

### 3. Run (public API only)
- `register_all_shipped()` once; `canonicalize(text, contract)` per row. Catch `ContractError` / `MultipleMentionsError` / unexpected exceptions as outcomes (an unexpected exception type is a finding, not a crash — log the traceback).
- Disposable scripts live in `/tmp/opencode/`, never in the repo. No source, test, or config modifications — read-only except the report file.

### 4. Analyze (distributions, then diffs)
- Outcome distribution per contract (SUCCESS/INVALID/MISSING/error counts).
- **Diff contracts pairwise**: default-vs-flag must show *only* the flag's documented effect (e.g. suppress ≡ default where no common-word intersection exists); format variants must differ in rendering only.
- Check every `assert`-mode row against its expectation; triage mismatches into (a) implementation bug, (b) spec/table correction with executed evidence, (c) new follow-up issue.
- Report `explore` rows as observations, grouped by theme.

### 5. Report + clean up
- Save to `docs/development/reports/YYYY-MM-DD-<cap>-ux.md`: method (seed, counts, contracts), distribution table, findings (numbered, each with vectors + verdict), follow-up issues raised.
- Delete disposable scripts and data. The repo diff must show only the report file.

## Pass Bar

- 100% of `assert`-mode rows match (or each mismatch is dispositioned as bug/spec-fix/issue with evidence).
- Zero unexpected exception types.
- Zero wrong-SUCCESS (a wrong canonical value fails the sweep even if counts look healthy — spot-check values, not just statuses).
- Every follow-up has either a raised issue number or a written reason it needs none.

## Anti-Patterns

- Generating inputs from the implementation (reads the tables to predict success) instead of from the spec — that tests nothing.
- Asserting observed outputs post-hoc ("snapshot the run as expected") — launders bugs into baselines.
- Touching `paxman/`, `tests/`, or configs mid-sweep — invalidates the black-box stance; restart clean if tempted.
- Leaving scripts/data in the repo or /tmp — remove both; the report is the artifact.
