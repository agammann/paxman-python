# Country code-lane narrowing implementation plan (PR1 — v0.6.0)

> **For workers:** Execute task-by-task via `tdd` + `verification-before-completion`. Review gate: `paxman-momus-review` (plan), `paxman-oracle-review` (after impl).

**Goal:** Stop the Country `alpha2_recognition` / `alpha3_recognition` / `numeric_recognition` grammars from claiming every 2-letter, 3-letter and 1–3-digit token in prose, so that only tokens that can actually resolve to an ISO 3166-1 code are claimed — while every currently-successful `canonicalize()` result is preserved byte-for-byte, and the ADR-0009 §16 common-word-suppression mechanism keeps working unchanged.

**Architecture:** Replace the three permissive shape regexes (`[A-Za-z]{2}`, `[A-Za-z]{3}`, `\d{1,3}`) with `LexiconMatcher` instances over **hand-maintained recognition key sets** in `paxman/capabilities/Country/grammar/data/`, mirroring the existing `Country/grammar/name_recognition.py` precedent (a vocabulary lexicon in `grammar/data/`, authority tables in `rules/data/`). The **rules are untouched** — `SectionAlpha2Codes` / `SectionAlpha3Codes` / `SectionNumericCodes` keep their `RuleStrategy.LOOKUP_TABLE` strategy, their provenance, and their normalisation. Nothing in `paxman/core` changes. The `numeric_recognition` lane keeps its zero-padding semantics (`"4"` → `"004"` → AF) by carrying the 1- and 2-digit forms in the key set.

**What this plan does NOT change (deliberately):**
- The **valid-code collisions** — `"and"` → AD, `"to"` → TO, `"by"` → BY, `"kg"` → KG. These are real ISO 3166-1 codes written in lowercase English. They are the class ADR-0009 §16 (`COMMON_WORDS` = "Google1000 ∩ ISO3166 α2/α3") exists to handle, they are already mitigated by `suppress_common_words=True`, and `tests/unit/test_b1_common_word_suppression.py` pins that remedy (`canonicalize("to and usa", suppress=True)` → `SUCCESS "US"`). **Narrowing them away would break ADR-0009 §16, the A0 whole-input exemption, the A1 all-common-words fallback, and the `suppressed_count` signal.** They stay; they get **documented** (Task 3).
- The `name_recognition` lane — already a vocabulary lexicon, already narrow.
- The `suppress_common_words` default (off), which is a project-wide convention (`AGENTS.md`).
- The cross-capability `scan()` noise (Domain 12, Language 5, Currency 3 mentions for one sentence) — a separate, larger architectural question, filed as a v1.0.0 follow-up (Task 3).

**Tech Stack:** Python 3.11+, uv, ruff, strict pyright, import-linter, pytest (markers: unit/capability/integration/property), `paxman/core/grammar/matchers/lexicon.py` (`LexiconMatcher`), `paxman/core/grammar/engine_loop.py` (`_VIEW_REGISTRY`).

**References:** Release audit `docs/development/reports/2026-10-22-release-0.6.0-experiment.md` (findings E3, E4, D12; decision N2), readiness plan `docs/development/plans/2026-10-22-release-0.6.0-readiness-plan.md` (tasks T3a/T3b/T3c), `paxman/capabilities/Country/grammar/name_recognition.py:33-57` (lexicon precedent), `paxman/capabilities/Country/grammar/alpha2_recognition.py:25-31`, `paxman/capabilities/Country/grammar/alpha3_recognition.py:23-30`, `paxman/capabilities/Country/grammar/numeric_recognition.py:24-31`, `paxman/capabilities/Country/rules/iso_3166_ed2024.py:52-177` (the three rules), `paxman/core/grammar/matchers/lexicon.py:44-129` (`LexiconMatcher`), `paxman/core/grammar/engine_loop.py:43-51` (`_VIEW_REGISTRY`), `paxman/core/grammar/engine_loop.py:149-163` (ADR §16 suppression), `paxman/core/grammar/data/common_words.py:37` (COMMON_WORDS size guard), `tests/unit/test_b1_common_word_suppression.py:58-88` (locked scan snapshots), `tests/capabilities/country/test_grammar.py:147-182` (numeric grammar pins), `docs/adr/0009-recognition-kernel.md` §10, §16, `paxman/core/grammar/boundary_spec.py` (`BoundarySpec.WORD`).

**Branch:** `fix/country-code-lexicon-narrowing` (cut from `dev` @ `08eedfc`)

---

## Background the implementer needs

### Current state (verbatim)

`paxman/capabilities/Country/grammar/alpha2_recognition.py:25-31`:

```python
_MATCHER = RegexMatcher(
    pattern=r"[A-Za-z]{2}",
    boundary=BoundarySpec.WORD,
    view=None,
    anchors=AnchorSet(),
    emit=_emit,
    suppressible=True,
)
```

`alpha3_recognition.py:23-30` is the same with `pattern=r"[A-Za-z]{3}"`; `numeric_recognition.py:24-31` uses `pattern=r"\d{1,3}"`.

All three scan the **raw text** (`view=None`) and claim *any* token of the right length. The rules then validate:

- `SectionAlpha2Codes` — `RuleStrategy.LOOKUP_TABLE`, `target_semantics={"alpha2_recognition"}`, accepts the token if it is in `ALPHA2_TO_ALPHA3` (250 entries: 249 ISO-assigned + the user-assigned `XK`).
- `SectionAlpha3Codes` — same shape over `ALPHA3_TO_ALPHA2` (250 entries).
- `SectionNumericCodes` — `matches()` zero-pads via `_normalize_key(value) = f"{int(value):03d}"` and accepts iff the padded form is in `NUMERIC_TO_ALPHA2` (249 entries).

### Why the current shape over-claims

Of the 676 two-letter shapes, **426 can never validate**. Of the 17,576 three-letter shapes, **17,326 can never validate**. Every one of them is still *claimed* — and `scan()` reports **claims**, not validated candidates (`paxman/engine/orchestrator.py:236` → `_recognitions_to_mentions(recognitions)`), so they surface as mentions.

Measured on `"Ship to the United States and Germany by 2026-01-15 for 50 boxes"` (`scan` with the default Country contract): **10 mentions, 2 real.** The 8 non-real split into:

| Token | Lane | Class |
|-------|------|-------|
| `the`, `for` | alpha-3 | **shape-only noise** — "THE"/"FOR" are not ISO 3166-1 codes |
| `01`, `15` | numeric | **shape-only noise** — "001"/"015" are unassigned |
| `to`, `and`, `by` | alpha-2/alpha-3 | **valid-code collision** — TO/AND/BY *are* codes (ADR §16 class) |
| `50` | numeric | valid — "050" is Bangladesh (zero-padded) |

The project already draws this line in its own test (`tests/unit/test_b1_common_word_suppression.py:43-46`):

```python
# not in intersection (shape-only noise, not valid-code collision)
assert "the" not in COMMON_WORDS
assert "of" not in COMMON_WORDS
```

**This plan removes the shape-only noise and leaves the valid-code collisions untouched.**

### Expected outcome (measured, not estimated)

| Text | Current mentions | After | Dropped |
|------|------------------|-------|---------|
| `"Ship to the United States of America, total 45.50 USD, weight 3.5 kg"` (the pinned `TEXT` in `test_b1_common_word_suppression.py:20`) | 9 | **4** | `the`, `45`, `USD`, `3`, `5` |
| `"Ship to the United States and Germany by 2026-01-15 for 50 boxes"` | 10 | **6** | `the`, `01`, `15`, `for` |

Surviving mentions in both cases are only real codes (`to`, `kg`, `50`, `and`, `by`) and real names. With `suppress_common_words=True` the code collisions are suppressed and only the genuine names remain.

**No successful `canonicalize()` result changes.** Every token that can validate is in the new key sets, so every `SUCCESS` is preserved. The only status change is `INVALID` → `MISSING` for tokens that could never validate — which is the *correct* status under the project semantics (`INVALID` = "recognised shape, no rule accepted it"; `MISSING` = "nothing claimed it").

### Design decisions (locked)

1. **Key sets live in `grammar/data/`, not `rules/data/`.** The grammar's copy is *recognition-only*; the rule keeps the authority table. This is the existing `Country/grammar/data/english_names.py` pattern — "This is recognition-only data … no token is mapped to a canonical country here. Validation rules own every token-to-country decision."
2. **The key sets are hand-maintained, not generated.** Neither Country data layer has a generator (`ls tools/ | grep -i country` → none); `rules/data/iso_3166_ed2024.py` is a hand-curated 2024 snapshot and `grammar/data/english_names.py` is hand-maintained. The new modules follow suit. **Do not add a generator in this PR** — that is separate work.
3. **The alpha-2/alpha-3 lanes scan the `casefolded` view** (`CaseFold()`, `_VIEW_REGISTRY["casefolded"]`), with **lowercased** keys, so `"US"`, `"us"`, `"Us"` all claim — exactly the set `[A-Za-z]{2}` claimed before. `CaseFold` is a pure lowercase with identity offsets for ASCII, so spans are unchanged. **The `country_normalized` view (`CountryNameFold`) must NOT be used** — it strips punctuation, so `"45.50"` folds to `"4550"` and the numeric lane would stop matching `"50"`.
4. **The numeric lane stays on `view=None`** (raw text). Its keys are digits, so no case fold is needed, and the raw view keeps `"45.50"` intact.
5. **The numeric key set carries the 1-, 2- and 3-digit forms** of every assigned M49 code (281 tokens), so the rule's zero-padding stays reachable: `"4"` → `"004"` → AF, `"04"` → `"004"` → AF, `"004"` → AF. The key set is exactly `{s : s matches \d{1,3} and int(s) is the int-value of an assigned M49 code}`.
6. **All three matchers keep `suppressible=True`** and `boundary=BoundarySpec.WORD`, so ADR-0009 §16 suppression and the A0 whole-input exemption behave exactly as before.
7. **`representation="trie"`** for all three (word-anchored, longest-first) — the same choice the Country name grammar makes. The trie only enters at word starts, which is strictly narrower than the old regex and is compensated by the identical `BoundarySpec.WORD` guard.
8. **The rules are not touched.** `SectionAlpha2Codes`, `SectionAlpha3Codes`, `SectionNumericCodes` keep their names, strategies, provenance and normalisation — the `recognition_revision` change is expected and desirable (the matcher digest changes).

## File Structure

- Create: `paxman/capabilities/Country/grammar/data/alpha2_codes.py` — `ALPHA2_CODE_KEYS: frozenset[str]` (250 lowercased alpha-2 codes, incl. `xk`)
- Create: `paxman/capabilities/Country/grammar/data/alpha3_codes.py` — `ALPHA3_CODE_KEYS: frozenset[str]` (250 lowercased alpha-3 codes)
- Create: `paxman/capabilities/Country/grammar/data/numeric_codes.py` — `NUMERIC_CODE_KEYS: frozenset[str]` (281 digit tokens, 1–3 digits)
- Modify: `paxman/capabilities/Country/grammar/data/__init__.py` — extend the module docstring to list the new code-key locales (the house pattern: the `__init__` documents, the grammar imports directly from the module — no re-export)
- Modify: `paxman/capabilities/Country/grammar/alpha2_recognition.py` — `RegexMatcher` → `LexiconMatcher` over `ALPHA2_CODE_KEYS`
- Modify: `paxman/capabilities/Country/grammar/alpha3_recognition.py` — `RegexMatcher` → `LexiconMatcher` over `ALPHA3_CODE_KEYS`
- Modify: `paxman/capabilities/Country/grammar/numeric_recognition.py` — `RegexMatcher` → `LexiconMatcher` over `NUMERIC_CODE_KEYS`
- Modify: `tests/capabilities/country/test_grammar.py` — pin the narrowed claim sets
- Modify: `tests/capabilities/country/test_capability.py` — pin the narrowed pipeline behaviour
- Modify: `tests/unit/test_b1_common_word_suppression.py` — re-pin the locked scan snapshots (9 → 4; 8 → 3)
- Modify: `tests/integration/test_scan_api.py` — re-pin any affected mention counts
- Modify: `docs/user/capabilities/country.md` — disclose the residual valid-code collisions; document the narrowed lanes
- Modify: `docs/user/migration.md` — add the "Unreleased — toward 0.6.0" behaviour-change entry
- Modify: `CHANGELOG.md` — `### Changed` entry under `[0.6.0]`

No `paxman/core` change. No `rules/` change. No new contract flag.

**Not touched by this PR:** the versioned docs snapshot `docs/user/v0.6.0/` does not exist on `dev` — it is created by the release PR (`release/0.6.0`, PR #198) from the updated `docs/user/`. The v0.6.0 snapshot is therefore regenerated as part of the release mechanics, **after** this PR merges (readiness-plan task T14), not here.

## Tasks

### Task 1: Key sets + narrowed grammar matchers

**Files:** the three new `grammar/data/` modules, the three grammar modules, `tests/capabilities/country/test_grammar.py`, `tests/capabilities/country/test_capability.py`

**Goal:** The three code lanes claim only tokens that can resolve to an ISO 3166-1 code.

- [ ] **Failing tests first** in `tests/capabilities/country/test_grammar.py`:
  - `test_alpha2_claims_only_iso_codes` — `Alpha2Grammar().recognize("the")` → `[]`; `recognize("and")` → one match (AND is a code); `recognize("US")` → one match; `recognize("us")` → one match; `recognize("xx")` → `[]` (XX is not assigned).
  - `test_alpha3_claims_only_iso_codes` — `Alpha3Grammar().recognize("the")` → `[]`; `recognize("for")` → `[]`; `recognize("and")` → one match; `recognize("usa")` → one match.
  - `test_numeric_claims_only_assigned_m49` — `NumericGrammar().recognize("01")` → `[]`; `recognize("15")` → `[]`; `recognize("840")` → one match; `recognize("004")` → one match; `recognize("4")` → one match (zero-pad form); `recognize("50")` → one match.
  - `test_alpha2_alpha3_claim_sets_match_the_iso_tables` — the recognised key sets equal the rule tables' code sets (guards against a key set drifting from the authority table).
  Run: `uv run pytest tests/capabilities/country/test_grammar.py -q` → Expected: FAIL (the shape regexes still claim `the` / `for` / `01` / `15`).
- [ ] **Implement** the three `grammar/data/` modules as hand-maintained key sets, lowercased for alpha-2/alpha-3, with a module docstring stating the recognition-only contract and the source (ISO 3166-1:2020 snapshot 2024, matching `rules/data/iso_3166_ed2024.py`). The numeric module derives its 1–3 digit forms from the 249 assigned M49 codes.
- [ ] **Implement** the matcher swap in the three grammar modules: `LexiconMatcher(tokens=…, boundary=BoundarySpec.WORD, view=…, anchors=AnchorSet(), emit=_emit, suppressible=True, representation="trie")`, with `view="casefolded"` for alpha-2/alpha-3 and `view=None` for numeric. Update each module docstring and the `Examples`/`Non-examples` class docstrings to match the new behaviour (the numeric one currently advertises `"4"` as an example — keep it, it still resolves).
- [ ] **Re-run** `uv run pytest tests/capabilities/country -q` → Expected: PASS, except the **scan-snapshot** tests in `tests/unit/test_b1_common_word_suppression.py` and `tests/integration/test_scan_api.py`, which are re-pinned in Task 2 (expected to fail here — that is the signal, not a defect).
- [ ] **Re-run** the audit corpus for the Country rows: `cd /tmp/opencode/rel060 && uv run python /tmp/opencode/release-0.6.0/experiments/run_experiment.py /tmp/opencode/release-0.6.0/experiments/run_pr1.json` → the Country rows must stay green except the three `country` corpus rows that asserted `INVALID` for `ZZ` (documented as "INVALID or MISSING") and the `hello world` row (documented `INVALID` → now `MISSING` because bare tokens are no longer claimed). **Re-baseline the corpus expectations for the Country rows in the same commit** and record the delta in the PR description.
- [ ] Commit: `fix(country): claim only ISO 3166-1 code tokens in the alpha-2/alpha-3/numeric lanes (E3, E4)`.

### Task 2: Re-pin the scan snapshots

**Files:** `tests/unit/test_b1_common_word_suppression.py`, `tests/integration/test_scan_api.py`

**Goal:** The locked scan snapshots reflect the narrowed claim sets. **This is a deliberate re-pin, not a behaviour regression** — the numbers below are the *measured* outcome of Task 1, and the reduction is the point of the change.

- [ ] `test_scan_off_snapshot_locked` — the pinned `TEXT` now yields **4** mentions, not 9: `to` (5,7), `United States of America` (12,36), `50` (47,49), `kg` (66,68). Update the assertion and the comment; keep the `(5,7)` and `(66,68)` span assertions. The dropped spans — `(8,11)` "the", `(44,46)` "45", `(50,53)` "USD", `(62,63)` "3", `(64,65)` "5" — must be asserted **absent**, so the narrowing is pinned in both directions.
- [ ] `test_scan_on_suppresses_common_words` — with `suppress_common_words=True` the count drops from 8 to **3**: the name mention plus the two surviving code collisions (`to` and `kg` are in `COMMON_WORDS`? — `to` is, `kg` is **not**; measure and pin the exact set). Keep the `(5,7) not in spans` assertion and the comment explaining that `the` is no longer claimed at all.
- [ ] `test_scan_whole_input_exempt` and `test_whole_input_exempt_variants` — verify the A0 whole-input exemption still holds for `"to"` / `"TO"` / `"  to  "` / `"to\n"` (the exemption is about *suppression*, and the token is still claimed).
- [ ] `test_scan_on_usd_remains_for_currency` — the Currency lane is untouched; confirm the count is unchanged (2).
- [ ] `tests/integration/test_scan_api.py` — re-pin any mention counts that shift.
- [ ] **Add** a regression test `tests/integration/test_country_pipeline.py::test_country_code_lanes_claim_only_valid_codes` asserting the end-to-end status change: `canonicalize("the")` → `MISSING` (was `INVALID`), `canonicalize("and")` → `SUCCESS "AD"` (unchanged — a valid code), `canonicalize("840")` → `SUCCESS "US"` (unchanged), `canonicalize("4")` → `SUCCESS "AF"` (unchanged — zero-padding preserved).
- [ ] Verify: `uv run pytest tests/unit/test_b1_common_word_suppression.py tests/integration/test_scan_api.py tests/integration/test_country_pipeline.py -q` → PASS.
- [ ] Commit: `test(country): re-pin the scan snapshots for the narrowed code lanes (E3, E4)`.

### Task 3: Docs — guide, migration note, CHANGELOG

**Files:** `docs/user/capabilities/country.md`, `docs/user/migration.md`, `CHANGELOG.md`

**Goal:** The residual valid-code collisions are disclosed (audit finding D12), and the narrowing is a documented behaviour change.

- [ ] `docs/user/capabilities/country.md` — add a **"Known collisions"** section (mirroring the "Known v1 overclaims" section `minor_planet.md` already uses) naming the residual class: *"The alpha-2 and alpha-3 lanes claim any ISO 3166-1 code written in lowercase, and some of those codes are ordinary English words — `and` → AD, `to` → TO, `by` → BY, `can` → CA, `per` → PE, `car` → CF, `mar` → MA, `ago` → AO, `usa` → US, plus the two-letter `as at be by cd co de do et id in is it la me my no pm re so st to`. Tokens that are **not** codes are no longer claimed at all (`the`, `for`, `01`, `15` → `MISSING`). Set `suppress_common_words=True` to suppress the collisions in prose; the whole-input exemption keeps a bare `and`/`can` recognised."*
- [ ] `docs/user/capabilities/country.md` — update the "What it recognizes" table: the alpha-2/alpha-3/numeric rows now say *code tokens only*, not *shapes*; add the alpha-3/numeric → alpha-2 canonical rows (audit finding D14).
- [ ] `docs/user/migration.md` — add the entry under "Unreleased — toward 0.6.0 (minor)": *"**Country — code lanes now claim only ISO 3166-1 code tokens.** Inputs that were previously recognised but could never resolve (`the`, `for`, `01`, `15`, `45`, `USD`, `3`, `5`) now return `MISSING` instead of `INVALID`. No successful resolution changes; the `INVALID` → `MISSING` shift affects only tokens that no authority could ever accept."*
- [ ] `CHANGELOG.md` — add a `### Changed` bullet under `[0.6.0]`: *"**Country — the alpha-2/alpha-3/numeric lanes claim only ISO 3166-1 code tokens (PR1).** Previously every 2-letter, 3-letter and 1–3-digit token in prose was claimed and then rejected by the validation rule (`INVALID`); now only tokens that can resolve to a code are claimed, so un-claimable tokens return `MISSING`. No successful resolution changes. The residual valid-code collisions (`and` → AD, `to` → TO) are unchanged and are handled by `suppress_common_words=True`."*
- [ ] Verify: `cd docs_site && npm run build` → exit 0. (The `v0.6.0` versioned snapshot is regenerated by the release PR, not here — see the File Structure note.)
- [ ] Commit: `docs(country): disclose the residual code collisions and the narrowed lanes (D12, D14)`.

### Task 4: Full gate + audit corpus re-run

**Files:** none (verification only)

- [ ] Full quality gate: `uv run ruff check paxman/ tests/ && uv run ruff format --check paxman/ tests/ && uv run pyright && uv run import-linter lint && uv run pytest -q` → all green.
- [ ] Coverage floor: `uv run pytest --cov=paxman --cov-report=term-missing -q && uv run coverage report --include="paxman/core/*,paxman/capabilities/*,paxman/engine/*,paxman/api/*" --fail-under=95` → ≥ 95.
- [ ] Kernel parity: `uv run pytest tests/property/test_grammar_stage_parity.py tests/property/test_kernel_delegation_parity.py tests/property/test_reentry_invariant.py -q` → PASS (the three country grammars are kernel-delegated; the delegation and re-entry properties must still hold).
- [ ] Audit corpus: re-run `run_experiment.py` twice and confirm the two dumps are byte-identical **except** `recognition_revision` (the known E1 finding) — and confirm the Country row count and the mismatch count are as expected.
- [ ] Re-run the CLI parity spot-check (`cli_parity.py`) — the Country rows must stay at parity.
- [ ] Commit (if the corpus expectations changed): `test(audit): re-baseline the Country corpus rows for the narrowed lanes (E3, E4)`.

## Final verify

After all four tasks: the full gate from Task 4, plus `uv run pytest -m "capability or integration or property or e2e" -q`. The `docs_site` build must exit 0 with `dist/v0.6.0/` present. The release-readiness audit's § Experiment findings E3 and E4 move from "open finding" to "fixed in PR1" — update `docs/development/reports/2026-10-22-release-0.6.0-experiment.md` and the release-notes draft accordingly (both are `docs/development/` artefacts, not shipped).

## Rollback

The change is confined to three grammar modules and three new data modules. If it must be reverted, `git revert` the Task 1 commit restores the shape regexes; no data migration, no contract change, no snapshot change is involved. The re-pinned snapshots in Task 2 would need reverting with it — they are in separate commits for exactly this reason.

## Risk register

| Risk | Mitigation |
|------|------------|
| The `country_normalized` view is used by mistake for the numeric lane (it folds `"45.50"` → `"4550"`, breaking the `"50"` claim) | Decision 3 and 4 state the view per lane explicitly; Task 1's `test_numeric_claims_only_assigned_m49` pins `"50"` is still claimed. |
| `CaseFold` is not offset-identity for non-ASCII | The alpha-2/alpha-3 lanes only ever match ASCII letters; `CaseFold` emits explicit maps when a fold changes length (`paxman/core/grammar/normalizers.py:227-254`), so the span still maps back correctly. |
| A code token that only resolves after zero-padding is dropped | The numeric key set carries the 1- and 2-digit forms (281 tokens, not 249); `test_numeric_claims_only_assigned_m49` pins `"4"`. |
| The `recognition_revision` changes | Expected — the matcher digest changes because the matcher changed. No test pins a specific revision value. |
| `scan()` mention counts shift in other test modules | Task 2 re-pins them; the full gate in Task 4 is the backstop. |
