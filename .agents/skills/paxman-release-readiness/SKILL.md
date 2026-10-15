---
name: paxman-release-readiness
description: Use when preparing paxman-python for a release — triggers include "prepare release", "release readiness", "cut a release", "draft release notes", "audit docs for drift", "pre-release check", "ready to ship 0.x.y", "triage release issues", or producing a release readiness plan. Fires whenever a version bump or release candidate needs release-labelled GitHub issues triaged, the repo audited, the capability experiment run, and a readiness plan emitted before anything ships.
---

# Paxman Release Readiness Skill

> **Purpose:** turn "prepare the repo for release" into a deterministic, evidence-backed protocol that produces exactly three artifacts — a triage + drift audit + capability experiment report, comprehensive release notes, and an executable readiness plan — without touching a single line of production code. The plan is what gets executed afterward; this skill only observes, measures, triages, and plans.

## When to Use

- User says `prepare release 0.3.0`, `release readiness`, `pre-release audit`, `draft release notes`, `ready to ship?`, `cut a release candidate`, `triage the 0.3.0 issues`
- A milestone (e.g. `docs/development/MILESTONE.md`) is complete and a version needs stamping
- User asks whether the repo is release-ready or what stands between it and a tag

**Do NOT use for:** researching a new capability (`paxman-capability-research`), implementing plan tasks (use `test-driven-development` + `verification-before-completion`), or post-merge reviews.

## Hard Rules (Non-Negotiable)

1. **Read-only on shipped code.** You may run the pipeline, tests, benchmarks, and generators; you may NOT edit `paxman/`, `tests/`, `pyproject.toml`, or any shipped doc. Every fix goes into the readiness plan as a task. Permitted writes: `tmp/` scratch space (gitignored), the three artifacts below, GitHub issue labels/comments during Phase 1 triage (label + evidence comment only — never delete an issue, never close without a comment), and one tracker issue carrying the release label as the resumption reference for the exercise (checklist of finding IDs; all other GitHub writes stay triage-only).
2. **Evidence before claims.** Every drift finding cites file:line (or "absent from X"); every experiment row is reproducible from the saved script with the recorded seed; every issue verdict cites a reproduction command or an ADR/spec path. No "looks fine" without a command that proves it.
3. **Three artifacts, exact locations:**
   - Triage + drift audit + experiment report → `docs/development/reports/YYYY-MM-DD-release-<version>-experiment.md`
   - Release notes draft → `docs/development/reports/YYYY-MM-DD-release-notes-<version>.md`
   - Readiness plan → `docs/development/plans/YYYY-MM-DD-release-<version>-readiness-plan.md`
4. **Respect `docs/development/AGENTS.md`:** everything in `docs/development/` is ephemeral and must never be referenced by shipped docs/code. The release notes and plan must therefore be self-contained; final release notes get published out-of-band (GitHub Release / CHANGELOG.md — decided in the plan).
5. **Ground in repo conventions:** read `AGENTS.md` (root), `ARCHITECTURE.md`, `pyproject.toml` first. Use `uv run` for every command. Use the `gh-cli` skill for all GitHub issue operations. Semver governs the release number; the publish workflow's tag↔version safety check is the enforcement point.
6. **Determinism is a test, not an assumption:** the experiment runs the full corpus twice and requires byte-identical results (mirrors the project's deterministic-by-construction invariant).
7. **Escalate, don't guess, on judgment calls.** A P0 experiment mismatch that may be an intentional behavior change, a `wontfix` verdict that contradicts an ADR/spec, and the CHANGELOG.md adoption decision are all marked `needs-decision` in the plan and raised to the user — never silently classified.

---

## Phase 0 — Discovery (10 minutes)

1. **Resolve the release number.** Read `pyproject.toml` `version`. Ask the user only if the target differs (e.g. in-tree `0.2.0` but next release is `0.3.0`).
2. **Classify the delta.** `git log --oneline <last-tag>..HEAD` (tags: `git tag`). Map to semver: breaking surface → minor (pre-1.0) or major; new capability → minor; fixes → patch. Record mismatches between implied and declared version as a finding.
3. **Record repo state:** branch, short SHA, date (UTC `YYYY-MM-DD`), Python version, uv lock state (`uv lock --check`).
4. **Inventory the release surface** (everything that ships): `README.md`, `QUICKSTART.md`, `ARCHITECTURE.md`, `CONTEXT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `TESTING_STRATEGY.md`, `HOW_TO_ADD_NEW_CAPABILITY.md`, `HOW_TO_ADD_NEW_GRAMMAR.md`, `LICENSE.md`, `AGENTS.md` (root), `paxman/core/AGENTS.md`, `paxman/capabilities/AGENTS.md`, `tests/AGENTS.md` (`docs/development/AGENTS.md` stays excluded — ephemeral), `CHANGELOG.md`, `docs/adr/`, `docs/recipes/`, `docs/user/`, `docs_site/` (`versions.json`, `src/content/versions/`), `pyproject.toml` metadata, `paxman/py.typed`, all docstrings in `paxman/`, CLI help text, error messages, `paxman/capabilities/__init__.py` exports.
5. **Inventory release-labelled issues** (input to Phase 1): confirm the label convention (`gh label list` — version labels may be `<version>` or `v<version>`; the repo used the `v`-prefixed form in the v0.5.0 cycle, e.g. `v0.5.0` — still re-confirm, then use whichever exists and note the convention), then `gh issue list --state open --label <label> --json number,title,labels,body,assignees` and also scan for closed-since-last-tag issues carrying the label (they feed the release notes' Fixed section).

## Phase 1 — Release Issue Triage (GitHub)

**Goal:** every issue labelled for this release ends the phase in exactly one of: closed (`invalid`/`wontfix`/`duplicate`/`done`), or confirmed-open and scheduled as a plan task. No issue left unexamined.

For each open issue carrying the release label, triage in order:

| Verdict | Criteria | Action |
|---------|----------|--------|
| `invalid` | Not reproducible, not a real defect, or misunderstanding of documented behavior | Reproduce (or fail to) with a command; label `invalid`; comment with the reproduction evidence; close |
| `wontfix` | Real but out of scope, by-design (cite ADR/ARCHITECTURE section), or deferred past this release | Label `wontfix`; comment citing the ADR/spec path justifying it; close |
| `duplicate` | Same root cause as another tracked issue | Label `duplicate`; comment linking the canonical issue; close |
| `done` | Already implemented on HEAD | Verify with a runnable command or test (name it in the comment); comment with evidence; close |
| `open — in scope` | Still valid, still wanted for this release, NOT yet implemented | Leave labelled; record as finding `I1…I n` — these become **P0 implementation tasks** in the readiness plan (TDD per project convention) |

Rules:

- Check implementation status with code search (`codegraph_explore`/grep across `paxman/` and `tests/`) — never assume an issue is unimplemented because it's open.
- A `wontfix`/`invalid` judgment that contradicts an ADR, the spec, or the issue author's pushback → `needs-decision` (Hard Rule 7); do not close.
- Never relabel or close an issue you did not personally verify.
- Record the full triage table (issue #, verdict, evidence, action taken) in the experiment report (§ Triage) — it feeds both the plan and the release notes' Fixed section.
- Re-label leftovers: any issue still open and in scope but too large for this release gets its label moved to the next version (with a comment), per user confirmation.
- Closed-unmerged sweep: list PRs closed without merge to the release base since `<last-tag>`; file a `followup`-labelled issue for any deferred concern worth tracking, per user confirmation.

## Phase 2 — Drift Audit (docs + docstrings + artifacts, except `docs/development/`)

For each surface, check **drift** (contradicts the code), **incompleteness** (missing entries), and **missing** (artifacts that should exist but don't). Minimum checklist:

| # | Check | Method |
|---|-------|--------|
| 1 | README capability table vs shipped capabilities | `uv run python tools/generate_readme_table.py` → diff against `README.md`; also verify against `list_shipped_capabilities()` |
| 2 | CONTEXT.md Notation/table entries vs all shipped capabilities (derive the count via `list_shipped_capabilities()` — never hardcode) | one entry per capability, fields match `Notation` dataclasses |
| 3 | docs/user/ accuracy | each example runs; API signatures match docstrings (`docs/user/api-reference.md`, `capabilities/`, `concepts/`, `migration.md`); for each behavior-change PR since `<last-tag>`, the capability guide's Status table pins the changed vector |
| 4 | Docstring drift | sample every public symbol in `paxman/api/`, `paxman/core/`, `paxman/engine/` — signature/behavior vs docstring; stale version strings anywhere — grep for the in-tree version, the target version, AND the last tag (`grep -rn "<in-tree>\|<target>\|<last-tag>" --include="*.md" --include="*.py" paxman/ *.md docs/adr docs/user docs/recipes`) |
| 5 | Forbidden references | no shipped doc/code references `docs/development/`, plan files, or research reports (`docs/development/AGENTS.md` hard rule) |
| 6 | ADR statuses | `docs/adr/*.md` — Accepted/Superseded/Obsolete consistent with the code they govern; no ADR marked Proposed whose governing code has already merged (merged-but-Proposed is a P1) |
| 7 | Broken links + stale counts | all relative links in shipped docs resolve; hardcoded counts (capability total via `list_shipped_capabilities()`, "67 common words", test counts, test-layer count, `tests/AGENTS.md` property-exception list, `tools/regenerate_*.py` coverage, coverage claims) verified against reality — counts must be derived, never hardcoded |
| 8 | Packaging metadata | `pyproject.toml` description/keywords/classifiers/README rendering; `py.typed` present; LICENSE year |
| 9 | Missing artifacts | CHANGELOG.md `## [Unreleased]` entries cover the `<last-tag>..HEAD` delta (missing entries are the finding), SECURITY.md contact validity, benchmarks/README accuracy |
| 10 | Versioned docs snapshot (v0.3.2 incident 2026-09-03) | if `docs_site/versions.json` lists a new `vX.Y.Z`: every `.md` under `docs/user/vX.Y.Z/` must carry an explicit `slug: vX.Y.Z/<path>` override matching the prior version's convention exactly (v0.4.1 uses `slug: vX.Y.Z` for `index.md` and `slug: vX.Y.Z/<dir>/index` for section indexes, e.g. `v0.4.1/capabilities/index` — replicate, don't reinterpret); `docs_site/src/content/versions/vX.Y.Z.json` must exist and match the prior version's shape; `versions.json` entry `{slug, tag}` present. A plain copy without slug injection fails the docs build (`The slug "vX.Y.Z[/...]" specified in the Starlight sidebar config does not exist`) and the deployed site ships without the new version selector. Verify with `grep -L "^slug:" docs/user/vX.Y.Z/**/*.md` (expect no output) plus gate G8 |
| 11 | New-capability docs checklist | for each capability added since `<last-tag>`: per-capability guide under `docs/user/capabilities/` + chooser `index.md` row + `docs/user/concepts/capabilities.md` row + `docs/user/api-reference.md` output-format / flag / quick-lookup rows + `docs/user/citations.md` authority rows + `docs/user/glossary.md` entries + `docs/user/migration.md` section + README capability + contract tables + CONTEXT.md table/Notation entries + `AGENTS.md` counts |

Output: a drift table (finding ID, surface, severity P0/P1/P2, evidence, proposed fix). Findings get IDs `D1…Dn`.

## Phase 3 — Capability Experiment (the 100-row corpus, release-scoped)

**Goal:** exercise the capabilities this release actually touched through the real public API with the latest source build, across varied states and forms, and surface anything the unit suite's assumptions hide.

0. **Scope the experiment to capabilities changed since `<last-tag>`** — never all shipped capabilities by default:
   - Derive the affected set from `git diff --stat <last-tag>..HEAD -- paxman/`: any `paxman/capabilities/<Name>/` with changes is in scope (new capabilities especially).
   - Changes in `paxman/core/grammar/`, `paxman/engine/`, `paxman/core/domain.py`, or `paxman/shared_data/` affect every capability — in that case (and only then) the full shipped set is in scope.
   - Record the scope derivation (files → affected capabilities) in the report; an all-shipped scope with only capability-local diffs is a scope bug, not thoroughness.
1. **Scratch space:** create `tmp/release-experiments/<YYYY-MM-DD>-<version>/` (or the harness-provided scratch dir when one is supplied); ensure `tmp/` is in `.gitignore` (add if missing — the only .gitignore edit permitted, and it becomes a plan task if it wasn't there).
2. **Generator script** (`generate_corpus.py`, saved in the scratch dir): **≥100 rows total across the in-scope capabilities; minimum 6 rows per capability (one per state), remainder weighted toward each capability's richest form variants.** Determinism: use a fixed constant seed written into the script and the report (e.g. `SEED = 20260828` — never entropy- or time-derived; a corpus change bumps the seed deliberately). Per capability, cover the state × form matrix:
   - **States (all six, per capability):** valid canonical, valid variant (case/spacing/label/grouping), structurally invalid (bad checksum/length/charset), semantically invalid (valid shape, unknown country/code/tag), absent (unrelated text, empty string), two distinct mentions in one slice.
   - **Forms:** derive from each capability's grammar docs/tests — e.g. IBAN hyphenated/compact/spaced/lowercase, Email with display name, Phone E.164 vs national, Date prose vs ISO, Money symbol vs ISO code. Do not copy one capability's form set onto another.
   - Include the **expected status** column (`SUCCESS`/`INVALID`/`MISSING`/`AMBIGUOUS`) per row — the expectation table IS the test oracle.
3. **Runner script** (`run_experiment.py`): `register_all_shipped()` from the in-tree build (`uv run python …` from repo root), call `paxman.canonicalize` per row with the default contract, plus one non-default `output_format` for a fixed sample (every 5th SUCCESS row, deterministic, recorded); dump full JSON results (input, status, value, provenance, span).
4. **Run twice; require byte-identical output files** (determinism check). Diff → finding if not.
5. **Analyze:**
   - Status mismatch matrix: expected vs actual per row; every mismatch is a finding (`E1…En`) with row evidence. A mismatch that may be an intentional behavior change gets `needs-decision` (Hard Rule 7).
   - Distribution sanity: per in-scope capability, SUCCESS/INVALID/MISSING/AMBIGUOUS counts — a capability with 0 INVALID rows means the corpus is too soft; regenerate.
   - Provenance completeness: every SUCCESS carries citation/authority data.
   - `format_value` round-trip on all SUCCESS rows; CLI parity spot-check (`uv run python -m paxman --json <capability> <input>`) on ≥10 rows.
   - Cross-capability confusion: rows where the wrong capability claimed the input.
6. **Report:** write `docs/development/reports/YYYY-MM-DD-release-<version>-experiment.md` — sections: § Triage (Phase 1 table), § Drift Audit (Phase 2 table), § Experiment (methodology, seed, per-capability result tables, findings `E1…En`), § Gates (Phase 5 results), pointer to the scratch scripts.

## Phase 4 — Release Notes (comprehensive draft)

Write `docs/development/reports/YYYY-MM-DD-release-notes-<version>.md` from `git log <last-tag>..HEAD` + closed/triaged release-labelled issues + the audit/experiment evidence. Required sections:

- **Summary** — what this release is, in 3 sentences, user-facing.
- **Highlights** — capabilities/features added since last tag (e.g. Recognition Kernel, new capabilities, suppression flag).
- **Added / Changed / Fixed / Deprecated / Removed / Security** — Keep-a-Changelog categories, each entry user-facing with example where useful; `Fixed` entries link the closed issue numbers from Phase 1.
- **Breaking changes & migration** — pre-1.0 caveat language + `docs/user/migration.md` cross-check.
- **Quality dashboard** — test count, coverage %, benchmark deltas vs `benchmarks/baseline.json`, pyright/ruff clean status.
- **Install & upgrade** — `uv add paxman==<version>` / pip; Python version support.
- **Known limitations** — from experiment findings and `wontfix`/deferred issues that won't be fixed before release.

## Phase 5 — Additional Readiness Gates (run, record, plan)

Run these and record results in the experiment report (§ Gates); failures become plan tasks:

| # | Gate | Command |
|---|------|---------|
| G1 | Full quality gate | `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run import-linter lint && uv run pytest` |
| G2 | Coverage floor | `uv run pytest --cov=paxman -q` then coverage report ≥95 |
| G3 | Benchmark regression | `uv run python benchmarks/harness.py` vs `benchmarks/baseline.json` |
| G4 | Build + wheel smoke | `uv build`; inspect sdist/wheel (py.typed ships, no `docs/development/`, no `tests/`, no `tmp/`); install the wheel into a throwaway venv under the `tmp/` scratch dir → `paxman --list` + one canonicalize smoke |
| G5 | CLI smoke matrix | `python -m paxman` for each shipped capability (derive the list from `paxman --list`, cross-checked against `_SHIPPED`) (valid + invalid input), plus `--list`, `--json`, stdin |
| G6 | Publish dry-check | tag↔version parity logic in `.github/workflows/publish.yml` matches declared version; no secrets in dist |
| G7 | Dependency hygiene | `uv lock --check`; note any stale/vulnerable pins |
| G8 | Docs build + versioned routes (v0.3.2 incident 2026-09-03) | `cd docs_site && npm ci && npm run build`; must exit 0 with `dist/vX.Y.Z/` present for every `versions.json` entry and sitemap containing `/vX.Y.Z/` routes. Any `AstroUserError: The slug "vX.Y.Z..." ... does not exist` is a P0 finding (missing `slug:` frontmatter in the snapshot — see drift check 10) |

## Phase 6 — Readiness Plan (the deliverable)

Merge ALL findings (issues `I*`, drift `D*`, experiment `E*`, gates `G*`, `needs-decision` items) into `docs/development/plans/YYYY-MM-DD-release-<version>-readiness-plan.md`, following the house plan format (see `2026-08-26-adr0009-kernel-remediation.md`):

- **Header table:** Title, Date, Status (`Draft — for review`), Branch (suggest `release/<version>` — worktree per user convention), Findings source (the experiment report), Release target (the version), Related (release notes draft).
- **Findings → task mapping table** (like the ADR-0009 plan's R→task table).
- **Progress table** with per-task status/commit columns.
- **Tasks ordered:** P0 correctness (unimplemented release-labelled issues from Phase 1, experiment mismatches, gate failures — each with TDD and its issue number referenced) → P1 drift fixes → P2 docs/release-notes finalization (including CHANGELOG.md decision and version bump) → P3 tag/publish checklist. Each task: commit message, scoped verify command, `- [ ]` checkboxes, TDD required for any behavior fix.
- **Decisions section:** every `needs-decision` item with options and a recommendation — resolved by the user before the plan's status leaves `Draft`.
- **Ship checklist:** merge → tag `v<version>` → publish workflow → verify PyPI artifacts → GitHub Release from the finalized notes.

## What Not to Do

- Do not fix anything during the audit — findings only. Fixing without a plan task breaks traceability.
- Do not run the experiment against an installed paxman; always the in-tree build via `uv run` from repo root.
- Do not experiment on all shipped capabilities when the release touched only some — scope per Phase 3 step 0; conversely, do not shrink scope when `paxman/core/`/`paxman/engine/` changed (that touches everything).
- Do not hardcode the in-scope capability list — derive it from `git diff <last-tag>..HEAD`; a new capability landing in this release is automatically in scope.
- Do not let the corpus be all-valid: an oracle without INVALID/MISSING rows proves nothing.
- Do not copy another capability's form variants into the generator; read each capability's grammar/tests.
- Do not reference `docs/development/` paths from any shipped file when writing fixes.
- Do not close or relabel a GitHub issue without an evidence comment; do not mark `wontfix` against an ADR without flagging `needs-decision`.
- Do not snapshot versioned docs as a plain copy — every file under `docs/user/vX.Y.Z/` needs its explicit `slug: vX.Y.Z/<path>` override plus the `docs_site/src/content/versions/vX.Y.Z.json` + `versions.json` entries (v0.3.2 shipped without them and broke the docs build); always verify with drift check 10 + gate G8.

## Red Flags — STOP and Re-plan

- "Docs look fine, skipped the table diff" → every check needs a command's output as evidence.
- Experiment ran once, not twice → determinism is unverified; rerun.
- Seed not written into the script and report → corpus is not reproducible; fix before running.
- Experiment ran on all shipped capabilities while only capability-local dirs changed since `<last-tag>` → scope bug; re-derive per Phase 3 step 0.
- An open release-labelled issue was never triaged → Phase 1 is incomplete; go back.
- Plan saved with wrong filename convention → must be `YYYY-MM-DD-release-<version>-readiness-plan.md` in `docs/development/plans/`.
- You edited `paxman/` source during readiness → move the edit into a plan task and revert it.
- You silently resolved a `needs-decision` item → undo and ask the user.
- Versioned docs added without running the docs build (gate G8) → the v0.3.2 failure mode; snapshot is unverified until `npm run build` passes with `dist/vX.Y.Z/` present.

## Quick-Start Prompt (for the agent you invoke)

```
[CONTEXT]: paxman-python is being prepared for release <version> (pyproject currently <in-tree>). Branch <branch> @ <sha>. Release-labelled issues: <label>.
[GOAL]: Produce three artifacts — docs/development/reports/YYYY-MM-DD-release-<version>-experiment.md (issue triage + drift audit + 100-row capability experiment + gate results), docs/development/reports/YYYY-MM-DD-release-notes-<version>.md, and docs/development/plans/YYYY-MM-DD-release-<version>-readiness-plan.md.
[REQUEST]: Triage every open issue labelled <label> (invalid/wontfix/duplicate/done with evidence comments; unimplemented → plan tasks); read-only audit of all shipped docs/docstrings/artifacts (except docs/development/); deterministic 100+ row corpus through paxman.canonicalize in tmp/ scoped to capabilities changed since <last-tag> (core/engine changes ⇒ all capabilities) with expected-status oracle and fixed recorded seed, run twice; full gate sweep (lint/type/tests/coverage/benchmarks/build/CLI); synthesize findings I*/D*/E*/G* into the readiness plan. No source edits; GitHub changes limited to triage labels/comments.
```

---

*This skill is the release-side complement to `paxman-capability-research`: research inventories a domain before it ships; readiness proves everything that shipped is documented, consistent, and behaving.*
