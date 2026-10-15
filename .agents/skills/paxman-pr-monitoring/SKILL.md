---
name: paxman-pr-monitoring
description: Use when monitoring an open pull request that is not yet merged and needs review triage, CI repair, and follow-up tracking. Triggers: monitor PR, PR not merged, check PR comments, address review feedback, fix failing CI, PR review follow-up, CodeRabbit comments.
---

# Paxman PR Monitoring

Monitor an existing open PR end-to-end: ensure you are on the right branch (via worktree if needed), triage all pending review comments, fix what is valid, repair failing CI, push the fixes, reply to deferred items on the PR thread, and record every deferred or newly discovered issue as a GitHub issue grouped for the next implementation batch.

## Overview

A PR that is not yet merged is **not done**. Reviews and CI are the source of truth — not the last commit message. This skill turns "the PR has comments / CI is red" into a deterministic loop:

**Worktree → Fetch → Triage → Fix → Verify → Commit/Push → Reply → Track**

No fix is applied without triage. No deferred concern is silently dropped — it gets a PR reply **and** a tracked issue.

## When to Use

- PR is open and `mergeable` but `mergeStateStatus` is `BLOCKED` / CI is failing
- User says `monitor PR 119`, `check PR comments`, `address review feedback`, `fix CI`, `PR not yet merged`, `what's left on the PR`
- CodeRabbit or a human reviewer left comments (including out-of-diff `consolidated_sites` blocks)
- PR was updated after the last review and needs a second pass
- You need to ensure deferred/skipped comments are tracked for `v0.4.0` / `vNext`

**When NOT to use:** PR is already merged/closed, no PR exists, or the task is to create a new PR (use `finishing-a-development-branch`). For a one-off review without fixes, use `paxman-oracle-review` or `thermo-nuclear-review`.

## Prerequisites

- `gh` CLI authenticated (`gh auth status` — use `gh-cli` skill for GitHub ops, never `curl`/`WebFetch` for GitHub)
- `uv` toolchain, `git` worktree support
- PR number or branch name (if omitted, infer from current branch via `gh pr view --json number,headRefName`)
- For CodeRabbit: expect `consolidated_sites` out-of-diff blocks inside comment bodies — they are still actionable

## Core Workflow

```
1. Locate PR & ensure worktree
     ↓
2. Fetch review comments + CI status (in parallel)
     ↓
3. Triage (valid vs invalid / in-scope vs deferred / duplicate)
     ↓
4. Address valid + relevant (code + tests, TDD)
     ↓
5. Investigate & fix failing CI (if any)
     ↓
6. Verify locally (ruff/pyright/pytest/coverage as needed)
     ↓
7. Commit & push to PR branch
     ↓
8. Reply on PR thread for every deferred/skipped valid comment + raise GitHub issue(s) grouped by version
     ↓
9. Record any newfound issues discovered during fixes as issues (grouped)
     ↓
10. Re-check PR mergeable + CI; leave summary comment
```

## Step 1 — Locate PR & Ensure Worktree

**Goal:** You are on the PR's branch, isolated from the current worktree.

```sh
# Infer PR if not given
gh pr view 119 --json number,headRefName,baseRefName,headRefOid,state,mergeable,mergeStateStatus --jq .

# Check current branch
git branch --show-current
git status --porcelain

# If current branch != PR head branch:
# Use a locked worktree (see using-git-worktrees skill)
git fetch origin <pr-head-branch>
git worktree add /tmp/opencode/<pr-head-branch>-pr<pr-number> origin/<pr-head-branch>
git worktree lock /tmp/opencode/<pr-head-branch>-pr<pr-number> --reason "pr-monitoring:<pr-number>"
cd /tmp/opencode/<pr-head-branch>-pr<pr-number>

# Else: stay on current worktree, but ensure it is up to date
git fetch origin
git status
```

- Never work on `dev`/`main` directly for PR fixes — use the PR branch or its worktree.
- If worktree already exists, reuse it (`git worktree list`), `git pull` inside it.

## Step 2 — Fetch Review Comments & CI Status

Fetch **both** in parallel — they are independent.

### 2a. Review comments (including out-of-diff)

CodeRabbit hides actionable items in `consolidated_sites` / `Also applies to:` blocks **inside** the comment body. You must parse the body, not just the `path`/`line` fields.

```sh
# Inline review comments (per-file)
gh api repos/<owner>/<repo>/pulls/<pr>/comments --paginate \
  --jq '.[] | {path: .path, line: .line, original_line: .original_line, body: .body, id: .id, user: .user.login}'

# Issue-level comments (walkthrough, summaries)
gh api repos/<owner>/<repo>/issues/<pr>/comments --paginate \
  --jq '.[] | {body: .body, user: .user.login, id: .id}'

# Reviews summary (to see which bots/humans commented)
gh api repos/<owner>/<repo>/pulls/<pr>/reviews --paginate \
  --jq '.[] | {user: .user.login, state: .state, body: .body}'

# Convenience
gh pr view <pr> --json comments,reviews --jq .
```

Collect for **every** comment:
- `path` + `line` (or `original_line`) — may be `null` for out-of-diff
- Full `body` — contains `consolidated_sites`, `Also applies to:`, `Proposed fix`, `Prompt for AI Agents`
- Author (`coderabbitai[bot]` vs human) — same triage bar, different reply tone
- Whether it was already addressed (see §3)

Persist raw bodies to a temp file for later reply threading.

### 2b. CI status

```sh
gh pr checks <pr> --json name,state,conclusion,link --jq .
gh pr view <pr> --json statusCheckRollup --jq '.statusCheckRollup[] | {name: .name, state: .state, conclusion: .conclusion}'
# For failing runs, drill in:
gh run list --branch <pr-head-branch> --limit 10 --json databaseId,conclusion,status,name --jq .
gh run view <run-id> --log-failed 2>&1 | tail -n 200
gh api repos/<owner>/<repo>/commits/<head-sha>/check-runs --jq '.check_runs[] | {name: .name, conclusion: .conclusion, output: .output.text[:2000]}'
```

Record: which checks failed, which are required for merge, and the log tail for each failure.

## Step 3 — Triage (Valid vs Deferred/Skipped)

No fix without triage. For **each** comment (including each `consolidated_sites` site), classify:

| Verdict | Criteria | What you do |
|---------|----------|-------------|
| **Fix now** | Valid, in-scope for this PR, reproduces against current code, aligns with `ARCHITECTURE.md` / `HOW_TO_ADD_NEW_CAPABILITY.md` / plan | Implement in §4 |
| **Deferred** | Valid but out-of-scope for this PR (nice-to-have, next-version concern, needs ADR, or would expand scope) | Keep list for §8 — reply + issue with `v0.4.0`/`vNext` label |
| **Skipped (invalid)** | Not reproducible, contradicts spec/ADR, stale (already fixed in a later commit `head...HEAD`), duplicate, or taste-only | Keep list for §8 — reply with brief reason, no issue |
| **Needs info** | Ambiguous, needs author clarification | Reply asking for clarification, do not fix yet |

Rules:
- Verify each finding against **current code** (`read` the cited lines). A comment may be stale if the file changed after the review's `headRefOid`.
- Treat `consolidated_sites` entries as separate findings — same triage per site.
- `CodeRabbit` nitpicks are not automatically invalid; assess severity vs project conventions (e.g. `__all__` shadowing `PEP 562` is a real bug even if marked `Minor`).
- Group duplicates: if 3 comments point to the same root cause (e.g. shared helper extraction), one fix + one issue group is enough.
- Keep a triage table (comment id / path:line / verdict / reason / grouped-issue id) — it feeds the PR reply and the issue bodies.

## Step 4 — Address Valid & Relevant

- Fix **only** `Fix now` items.
- Follow TDD: failing test first where a behavior change is involved; no skipped tests without justification.
- Keep changes minimal — one concern per hunk, no opportunistic refactors.
- Respect paxman invariants on every fix: `@dataclass(frozen=True, slots=True)` notation, `Contract` frozen without slots, `format_value()` sole presentation seam, no `output_format` in `rules/`, no `# type: ignore`/`# noqa` in `paxman/`, import-linter `capabilities` independence.
- Re-read the exact lines you will edit; base `oldString` on current file content (worktree).

## Step 5 — Investigate & Fix Failing CI

If any required check is `FAILURE` / `TIMED_OUT` / `CANCELLED`:

1. Pull the log tail (see §2b) and reproduce locally:
   - Lint/format: `uv run ruff check paxman/ tests/ tools/` + `uv run ruff format --check .`
   - Types: `uv run pyright`
   - Tests: `uv run pytest -q` (or the specific failing job's command from `.github/workflows/ci.yml`)
   - Coverage: `uv run pytest --cov=paxman --cov-report=term-missing --fail-under=95`
   - Import-linter: `uv run import-linter lint`
2. Fix the root cause (not the symptom). A `mergeable == MERGEABLE` but `mergeStateStatus == BLOCKED` with red checks is still blocked — fix the check, not the flag.
3. If CI failure is unrelated to this PR (e.g. pre-existing `tools/` E501 on `dev`), note it in the PR reply and in the triage table — do not touch unrelated files to green-wash CI.

## Step 6 — Verify Locally

Run the gates that the PR's CI runs (authoritative: `.github/workflows/ci.yml`):

```sh
uv run ruff check paxman/ tests/ tools/
uv run ruff format --check paxman/ tests/
uv run pyright
uv run import-linter lint
uv run pytest -q
# If coverage is required: uv run pytest --cov=paxman -q
```

- For a capability PR, also run `uv run pytest tests/capabilities/<name> -q` and the property/integration suites touched.
- Paste the tail of each gate into the final PR summary comment.

## Step 7 — Commit & Push

- Commit on the **PR branch** (worktree). One commit for all review fixes is preferred; split only if the fixes are logically independent and the PR history demands it.
- Message: `fix(<scope>): address PR #<n> review (CodeRabbit + CI)` with a bullet list of what was fixed and what was deferred (with issue numbers).
- Push to the PR's remote head:

```sh
git status --porcelain
git diff --stat
git add -A
git commit -m "fix(<scope>): address PR #<n> review ..."
git push origin HEAD:<pr-head-branch>
```

- If you are in a worktree, the push still updates the PR.

## Step 8 — Reply to Deferred/Skipped & Raise Issues

**Every** `Deferred` or `Skipped` valid comment must get **both** a PR thread reply and, for deferred, a GitHub issue.

### 8a. Reply on the PR thread

- Reply **on the specific review thread** when the comment has a `path`/`line` (so it threads):

```sh
gh api repos/<owner>/<repo>/pulls/<pr>/comments/<comment-id>/replies \
  -f body="Thanks — triaged as deferred for v0.4.0. Reason: … Tracked in #<issue>."
```

- For issue-level comments / walkthrough summaries, use:

```sh
gh pr comment <pr> --body "… summary of deferred items …"
# or for a specific issue comment thread:
gh api repos/<owner>/<repo>/issues/<pr>/comments -f body="…"
```

Template (deferred):
> Triaged as **deferred to `v0.4.0`** — valid concern, but out-of-scope for this PR because … . Tracked in #<issue> (grouped with …). Will be taken up as … .

Template (skipped/invalid):
> Skipped — … (e.g. already fixed in <commit>, not reproducible against current code at `path:line`, contradicts `ARCHITECTURE.md` §…, taste-only). No issue filed.

### 8b. Raise GitHub issues (grouped)

- Group deferred comments that share a root cause or can be implemented together (e.g. `__all__` + `components_valid` extraction = one issue; `iso6709` integer padding + `iso6709` fraction handling = one issue). One issue per group, not per comment.
- Create with the version label the user requested (e.g. `v0.4.0`):

```sh
gh issue create --title "<scope>: <deferred concern> (follow-up from PR #<n>)" \
  --label "v0.4.0" --label "followup" \
  --body "$(cat <<'EOF'
**Follow-up from PR #<n> (CodeRabbit/human)**

**Deferred valid comment(s):**
- `path:line` — <quote>
- `path:line` — <quote> (consolidated_sites)

**Why deferred:** …

**Suggested follow-up:**
- …

**References:** PR #<n> (commit <sha>), CodeRabbit comment <id>
EOF
)"
```

- Add the issue URL back into the PR reply for traceability.

## Step 9 — Record Newfound Issues

Any bug, gap, or debt you discover **while implementing the fixes** that was **not** in the PR comments must also be tracked — do not silently fix scope-creeping items, and do not silently drop them.

- If it can be fixed minimally within this PR's scope and is clearly a bug introduced by the PR, fix it now (still TDD, still minimal).
- Otherwise, treat it as deferred: group it with related deferred comments if it shares a theme, or create a standalone issue with `v0.4.0`/`vNext` as appropriate.
- Label and body same as §8b, with `**Newfound during PR #<n> fixes (not in review):**` header.

## Step 10 — Final PR Summary

Post a single summary comment on the PR:

- Triage table (id / verdict / reason / issue)
- CI status before/after, gates run locally
- Commit pushed (`<sha>`)
- Deferred issues created (`#<n>` with labels)

Re-check:

```sh
gh pr view <pr> --json mergeable,mergeStateStatus,headRefOid --jq .
gh pr checks <pr>
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Fixing without triage / fixing `or True` vacuous tests by deleting them | Triage first; strengthen the assertion to its intended expectation |
| Adding `__all__` with eager import that shadows PEP 562 lazy exports (`paxman/capabilities/__init__.py`) | Keep initializer minimal or use `TYPE_CHECKING` / lazy `__getattr__`; verify `from paxman.capabilities import <Name>` after change |
| Replying only on the PR summary comment instead of the specific review thread | Reply on the thread (`/pulls/.../comments/<id>/replies`) so the reviewer sees it in context |
| Creating one issue per comment instead of grouping | Group by implementation batch; one issue per coherent scope |
| Pushing to `dev`/`main` instead of the PR head branch | `git push origin HEAD:<pr-head-branch>` from the worktree |
| Running `curl`/`WebFetch` against GitHub | Use `gh` CLI (`gh pr view`, `gh api`) per `gh-cli` skill |
| Letting deferred concerns vanish without an issue | Every deferred valid comment gets a `v0.4.0` issue |

## References

- `gh-cli` skill — authenticated GitHub ops
- `using-git-worktrees` skill — isolated PR worktrees
- `paxman-oracle-review` / `thermo-nuclear-review` — for re-review after fixes
- `.github/workflows/ci.yml` — authoritative CI gate

## Source

Created 2026-09-02 for paxman-python PR monitoring (PR #119 CodeRabbit + merge-conflict + v0.3.1 follow-up). Covers CodeRabbit `consolidated_sites` out-of-diff, PEP 562 shadowing, `followup`+`v0.4.0` issue grouping, and newfound-issue tracking. No plugin required; file-based `~/.agents/skills/paxman-pr-monitoring/SKILL.md`.
