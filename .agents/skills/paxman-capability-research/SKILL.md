---
name: paxman-capability-research
description: Research a new Paxman capability to IBAN/BIC gold standard and emit a docs/development/research canonicalization report. Use when the user asks to research a capability, add a new domain, survey a standard/spec, or prepare a capability plan. Produces a primary-source, citation-backed report on par with 2026-08-22-iban and 2026-08-23-bic. Reports must inventory every human-written representation of the value — the taxonomy is capability-specific (for a hyphenated identifier like ORCID/ISBN/IBAN that is hyphenated / compact / space-grouped / URI-prefixed; for a tag/code/name domain like Language/Country/Currency it is BCP47 tag / bare code / display name / locale-underscore). Enumerate the actual set for the target domain, each with evidence and an explicit recognize-or-defer decision — ORCID's five forms are only one illustration, not the template.
---

# Paxman Capability Research Skill

> **Gold standard:** `docs/development/research/2026-08-22-iban-canonicalization.md` (IBAN, 832 lines, 100K) and `docs/development/research/2026-08-23-bic-canonicalization.md` (BIC, 810 lines, 91K). This skill exists to let you reproduce or exceed that bar for *any* new capability — ISSN-level provenance discipline, BIC-level grammar precision, IBAN-level algorithmic depth. Read this entire file before fetching a single URL.

## When to Use

- User says `research LEI`, `research ISIN`, `add UUID capability`, `what should we build next?`, `survey ORCID`, `canonicalize DOI`
- User points at `docs/development/MILESTONE.md` and asks what to research
- User wants a `docs/development/research/*.md` report for a new domain
- User wants a pre-implementation survey that will later become a `docs/development/plans/*.md` and a `tools/new_capability.py` scaffolding

**Also trigger for:** `capability research`, `new capability`, `paxman research`, `canonicalization research`, `survey a spec`, `how would we add X to paxman`.

If the capability name is not given, **discover it yourself** from `docs/development/MILESTONE.md` priority roadmap (pick the highest unbuilt entry) or from `paxman/capabilities/__init__.py` gap analysis.

## Hard Rules (Non-Negotiable)

1. **Primary sources only.** Every claim must trace to the spec publisher, the Registration Authority, the country-table owner, or the validator's source code. A blog post *about* ISO 13616 is not a source; `https://www.iso.org/standard/81090.html` is. Follow every claim back to the owner.
2. **No source-code or test modifications.** This is a research skill. You may read code, you may not edit `paxman/`, `tests/`, or `pyproject.toml`. Evidence basis must note the repo state (`git rev-parse --short HEAD` + branch).
3. **Cite or it did not happen.** Every table row, regex, length, charset, lifecycle value, and example must have a URL or a codebase path. Secondary sources (Wikipedia, BankValidor, blog posts) are allowed only as secondary and must be labeled.
4. **Match or exceed BIC/IBAN completeness.** Your report must be deliverable as a direct replacement for either precedent without loss of signal. If yours is shorter, you missed something.
5. **Save to `docs/development/research/YYYY-MM-DD-{kebab}-canonicalization.md`** — the same folder and naming convention as the precedents. Never save elsewhere unless the user explicitly overrides.
6. **Respect `docs/development/AGENTS.md`:** that folder is ephemeral, not shipped, may drift, may be removed, and must not be referenced by shipped code/docs. Do not create dependencies on it.
7. **Ground in Paxman conventions.** You must read and cite `HOW_TO_ADD_NEW_CAPABILITY.md`, `HOW_TO_ADD_NEW_GRAMMAR.md`, `ARCHITECTURE.md`, and at least the two immediate research precedents (`2026-08-21-issn-canonicalization.md`, `2026-08-22-iban-canonicalization.md`, `2026-08-23-bic-canonicalization.md`) before proposing anything.
8. **Inventory every written form.** A capability is recognized across its full human surface, not one display convention. Before proposing any grammar you must enumerate EVERY distinct written representation attested by the spec, an official schema, or ≥2 ecosystem validators — the taxonomy is capability-specific. For illustration, ORCID exists as hyphenated display (`0000-0002-1825-0097`), separator-free compact (`0000000218250097`), space-grouped print form (`0000 0002 1825 0097`), resolver URI (`https://orcid.org/…`), and label-prefixed prose (`ORCID: …`); ISBN exists as hyphenated vs compact; Language exists as BCP47 tag (`en-US`) vs bare code (`en`/`eng`) vs display name (`German`) vs locale-underscore (`fr_FR`). Discover the real set for YOUR capability — do not assume ORCID's five, do not copy Language's three. Each inventoried form carries evidence plus an explicit disposition: RECOGNIZE in the v1 grammar, DEFER to a community extension, or REJECT with written rationale. Silence is not a decision — an unhandled common form becomes a permanent MISSING blind spot in the shipped capability.

---

## Phase 0 — Discovery (5 minutes)

1. **Resolve the capability name.** If user gave `LEI`, `ISIN`, `UUID`, `DOI`, `ORCID`, etc., use it. If user said `find one` / `what's next`, read `docs/development/MILESTONE.md` and pick the highest-priority unbuilt capability that is not in `paxman/capabilities/__init__.py.__all__`. Confirm with the user if ambiguous.
2. **Normalize identifiers:** `CapabilityName` → `CapName` export alias, `capability_name` → `cap_name` registry name (lowercase, `si_unit` style for multi-word). Record both.
3. **Record repo state:** `branch`, `commit`, `date` (UTC `YYYY-MM-DD`) — this goes in the report header and evidence basis line, exactly like BIC's `Repo state: chores/pre-release-housekeeping @ d7737f0`.

---

## Phase 1 — Research Protocol (Primary-Source Survey)

You are a **primary-source surveyor**, not a summarizer. For the chosen capability, you must fetch and cite:

### A) Authoritative Spec & Lineage

- **ISO catalogue pages** (`iso.org/standard/*`) for every edition that matters. Record edition, publication date, ICS, TC/SC, status (`Published`/`Withdrawn`/`Confirmed`), what it cancels, and lifecycle per `ARCHITECTURE.md` (`active`/`withdrawn`/`superseded`). Build the **Lineage Table** (like BIC §5.1, IBAN §5.1) — at least 3 editions if the spec has lineage.
- **Registration Authority (RA) pages** — who is the RA, appointed when, duties, publication cadence (monthly, rolling, within N working days), and the RA's own directory/search/registration PDFs. For financial identifiers this is often SWIFT; for others it may be IANA, ISSN International Centre, GLEIF, etc.
- **Country / vocabulary authority** if the spec references ISO 3166-1, ISO 4217, CLDR, IANA subtag registry, etc. — record its maintenance agency and snapshot date.
- **Check-character / checksum spec** if any — the exact algorithm (MOD 97-10, MOD 11, Luhn, Verhoeff, etc.), with letter-expansion table (`A=10…Z=35`), piece-wise computation, and generation vs validation direction. If the domain has **no checksum** (like BIC), explicitly prove the negative ("BIC has no checksum, unlike IBAN, structure is all there is" with two independent sources).

### B) Ecosystem Validators (Real-World Evidence)

Fetch and quote at least 4 of these, with pattern/logic tables:

- `arthurdejong/python-stdnum` `stdnum/<cap>.py` (`clean` + regex + country/registry lookup)
- `validator.js` `is<Cap>.js` (regex + `CountryCodes.has` + edge-case fixes like `XK` issue 2045)
- Language-specific libs (`schwifty` for BIC, `iban-tools`/`js-iban` for IBAN, `isbnlib`, `lei` parsers, etc.)
- At least one taxonomy/reference site (`BankValidor`, `iban.com`, `codeswap.net`, `Genfy`, etc.) — labeled secondary

For each, extract the **exact regex** or lookup logic and put it in the `Real-world regex / validation snippets` table (IBAN §2.1 style, BIC §2.1 style).

### C) Recognition-Surface Survey — every way humans write the value (mandatory)

You are cataloguing a *surface*, not a format. Enumerate all distinct written representations before touching grammar design:

- **Spec & schema text:** structure sections, examples, XSD/JSON schema pattern facets, RA style guides — these define the official display form(s) and often hint at alternates.
- **Ecosystem validator strip logic:** python-stdnum's `clean = re.sub(...)`, validator.js preprocessing — the characters a validator removes are direct evidence of which separators/spacings occur in the wild.
- **Real-world carriers:** resolver URIs where the identifier has a resolver (e.g., `https://orcid.org/…` for ORCID, `https://doi.org/…` for DOI), prose labels where the domain uses them (e.g., `ORCID:`/`ISNI:`/`IBAN:`/`ISBN:`), print/paper grouping conventions, database and API dumps (compact runs) — the carrier set is capability-specific; ORCID's carriers are only an example, not the checklist.

Record per form: name | example | where attested (URL or path) | prevalence (canonical / official-display / common / rare) | structural deltas vs canonical (separators, case, prefix, length).

Assign every form exactly one Paxman disposition:

| Disposition | Meaning | Grammar mechanism |
|-------------|---------|-------------------|
| RECOGNIZE | folded into the shipped v1 grammar | optional group, alternation branch, or Pre-stage strip |
| DEFER | plausible but rare or lossy today | named candidate for `extra_grammars` community extension |
| REJECT | never valid input (truncated, OCR-mangled, homoglyph) | documented negative test |

Minimum bar: a form attested in the spec/schema or by ≥2 validators MUST appear in the inventory; every REJECT/DEFER needs a written rationale. This survey feeds §2.1 of the report, constrains the §4.2 pattern, and any recognition gap it exposes must become an Open Decision row (§13).

### D) Shipped Paxman Precedents

Explore the codebase (use `codegraph_explore`) and anchor every design choice to verbatim precedent:

- **ISBN / ISSN / Country / Phone / IBAN / BIC** — grammar strategy, notation shape, contract seam, rule publication split, `format_value` invariant, `single_value` semantics.
- Cite paths like `paxman/capabilities/ISBN/grammar/isbn13_recognition.py`, `paxman/engine/orchestrator.py:_dedup_spans`, `paxman/core/domain.py:Rule.__init_subclass__`.

If you cannot find the precedent by reading, you missed the exploration step — re-explore.

---

## Phase 2 — Report Structure (The Template)

Your report **must** follow this section order and heading hierarchy. It is the BIC/IBAN template, byte-for-byte in intent. Deviating breaks downstream planning (`docs/development/plans/*.md` expects these anchors).

```markdown
# {CAP} Canonicalization Research — paxman-python

**Date:** YYYY-MM-DD
**Scope:** Primary-source survey of the {CAP} standard (...), ecosystem canonicalization practices, and Paxman's grammar/rule/provenance architecture, to ground the design of a future `{CAP}` capability. No source code, tests, or configuration were modified.
**Evidence basis:** {list every primary source you fetched, plus ecosystem libs, plus shipped capabilities used as precedent}. Repo state: `{branch} @ {short-sha}` — engine owns per-grammar containment dedup, total recognition ordering, and `Capability.format_value()` presentational seam.
**Conventions grounding this report:** HOW_TO_ADD_NEW_CAPABILITY.md, HOW_TO_ADD_NEW_GRAMMAR.md, ARCHITECTURE.md, and the ISSN research precedent ... plus the IBAN/BIC precedents.

---

## Executive Summary

{CAP} is a {strong/weak} fit for a Paxman capability: it has {unambiguous/ambiguous} canonical form (**{compact description}**), a {stable/unstable} {single/multi}-part standard (**{spec} {edition}**, {date}, {status}, {publisher}) with {RA} as RA, a maintained authoritative {directory/registry} (**{name}**, {size}, {cadence}), and a well-understood human-readable presentation (**{grouped/paper/hyphenated}**, presentation-only). The domain mirrors Paxman's value proposition for {ISSN/ISBN/IBAN/BIC}: recognizing tolerant human surface, validating strictly against authority, returning canonical compact value with provenance. {Checksum sentence}.

Key findings that shape the design:
1. **Canonical form is ...** (regex, length, charset, presentation vs wire)
2. **One grammar vs N grammars, with gating rationale** (cross-grammar containment, semantics coalescing, feature-flag locus)
3. **Validation is ...-level** (PARSER vs LOOKUP_TABLE, checksum vs country lookup, valid vs country-valid vs issued)
4. **Branch/variant equivalence vs distinct identity** (XXX head office, IBAN paper groups, ISBN-10→13, etc.)
5. **Provenance is cleanly split** per HOW_TO_ADD_NEW_CAPABILITY.md Step 5 (one file per publication, one PUBLICATION constant, one Rule class per section)

Recommended file layout, rule set, notation, and contract are specified in §6, §10, §11. Open decisions and recommendations are in §13.

---
## 1. Target User

| Persona | Why they need {CAP} canonicalization | Typical context |
| ... | ... | ... |

**User-visible contract:** The caller supplies raw human text ... and a contract; Paxman returns one canonical {CAP} (or `MISSING`/`INVALID`/`AMBIGUOUS`) with citation. This mirrors {IBAN/BIC/ISSN} ergonomics, but the canonical default is **{compact form}**.

---
## 2. Shape of Input (Human Surface)

### 2.1 Recognition-surface inventory — every distinct written form (MANDATORY)

From the Phase 1C survey, list EVERY representation humans actually produce for THIS capability's value. Do not stop at the spec's display convention and do not copy another capability's taxonomy — the form set is domain-specific. For a hyphenated identifier (ORCID/ISBN/IBAN) interrogate at minimum wire/canonical, official display/paper, separator-free compact, alternative separator groupings (space/dot/slash), resolver-URI-prefixed, label-prefixed prose, case variants including check-character case, and regional display conventions. For a tag/code/name capability (Language/Country/Currency) interrogate tag vs bare code vs display name, locale-underscore variants, bilingual/terminology vs bibliographic codes, and prefix/suffix carriers. Discover; do not assume.

*Illustrative rows for a hyphenated-identifier-like capability (e.g., ORCID) — replace with the capability's actual written forms discovered in Phase 1C; do NOT copy these five if they don't apply. For Language/Country, the rows would instead be BCP47 tag / bare alpha-2 / bare alpha-3 / English name / localized name / locale-underscore.*

| Form | Example | Attested where | Prevalence | Paxman v1 decision | Grammar mechanism |
|------|---------|----------------|------------|--------------------|-------------------|
| Hyphenated display | ... | spec §X + XSD pattern facet | official display | RECOGNIZE | main pattern body |
| Separator-free compact | ... | stdnum `clean()`, DB/API dumps | common | RECOGNIZE or DEFER | alternation branch / Pre-strip |
| Space-grouped | ... | print corpora, style guides | occasional | RECOGNIZE or DEFER | separator class tolerance |
| URI/host-prefixed | ... | resolver links on the web | common | RECOGNIZE | optional host prefix |
| Labeled prose | ... | `XXX:` / `ID No:` conventions | common | RECOGNIZE | fused label [\s:-]+ |

A v1 that does NOT recognize a commonly attested form must state that explicitly here AND raise it as an Open Decision (§13) so downstream planners see the deliberate scope cut. Failure mode this prevents (ORCID illustration): a report that inventories only the hyphenated form while humans equally write `0000000218250097` and `0000 0002 1825 0097`; the equivalent for any capability is inventorying only the display form while alternative attested forms are silently ignored.

### 2.2 Wild variants — adversarial mutations of each inventoried form

Enumerated from spec, RA pages, corpora, and real validators; stress-test every §2.1 RECOGNIZE form:

| # | Category | Example Inputs | Recognition concern |
|---|----------|----------------|---------------------|
| 1 | Canonical compact | ... | Spec master form |
| ... | Lowercase / mixed case | ... | case-insensitive, .upper() |
| ... | Grouped / paper display | ... | presentation-only |
| ... | Label with colon/space/hyphen | ... | case-insensitive, [\s:-]+, span includes label |
| ... | Irregular whitespace | ... | \s tolerance or isalnum collapse |
| ... | Separators included | ... | hyphen/dot tolerance decision |
| ... | Head office / variant | ... | distinct vs equivalent |
| ... | With trailing annotation | ... | not swallow parenthetical |
| ... | Multiple per line | ... | 2+ matches |
| ... | Quoted / bracketed | ... | inside punctuation |
| ... | OCR / homoglyph | ... | strict charset, no autocorrection |
| ... | Over-long / under-long | ... | length guard, never 9/10/12 |
| ... | X-glued runs | ... | word-boundary guards |
| ... | Invalid country/code | ... | grammar claims, rule rejects |

**Real-world regex / validation snippets (ecosystem evidence):**

| Source | Pattern / Logic |
|--------|-----------------|
| ... | ... |

**Normalization contract (reuse ISBN/ISSN pattern):**
```python
compact = re.sub(r"[^A-Z0-9]", "", raw).upper()
# or stdnum: re.sub(r"[ \-]", "", raw).strip().upper()
# then validate: len + regex + country/registry lookup
```

### 2.3 What input is NOT a {CAP} mention
- {Sibling domains with length/charset disambiguation}
- Short runs, bare country codes, etc. — MISSING vs INVALID boundary (see §9)

### 2.4 Single-mention vs multi-mention input
Paxman resolves **one mention per `canonicalize()` call** (ARCHITECTURE.md, segmentation recipe; `docs/recipes/segmentation.md` ADR-0004). Two distinct mentions → `AMBIGUOUS` or `MultipleMentionsError` with `single_value=True`; identical values coalesce to `SUCCESS`.

---
## 3. Shape of Notation (Intermediate Representation)

### 3.1 Recommended notation — {compact plus structured decomposition}
```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class {CAP}Notation:
    """..."""
    field1: str
    field2: str
    compact: str
```

**Considered alternative — single field `compact` only:** ... However the decomposition is preferred because {1. spec indexes by field, 2. rule routing key, 3. branch/flag semantics}.

**Invariants the grammar enforces (before rules):**
- field1 is exactly N A-Z0-9 (uppercased from [A-Za-z0-9]) ...
- compact is N or M total, equals field1+field2+...

### 3.2 Why not carry spaces or labels in the notation
Spaces, grouping, and `BIC:`/`IBAN:` labels have **no lexical significance** for validity — presentation is `Capability.format_value()` only.

### 3.3 Why {field} is not a shape discriminator literal
{Free str validated by LOOKUP_TABLE against snapshot, not Literal — mirroring Country/ISIN precedent}

---
## 4. Grammar / Recognition Strategy

### 4.1 Strategy choice — Regex vs Lexicon
Per HOW_TO_ADD_NEW_GRAMMAR.md ..., {CAP} has distinctive fixed-width shape / finite vocabulary, so **Regex/Lexicon** is correct.

### 4.2 Reference pattern (adapted from ISSN and IBAN verbatim precedent)
ISSN precedent / IBAN precedent code blocks, then **Proposed {CAP} pattern (single grammar, staged pipeline):**
```python
import re
from paxman.capabilities.{CAP}.notation import {CAP}Notation
from paxman.core.grammar.boundary import BoundaryGuard
from paxman.core.grammar.pipeline import PipelineGrammar
from paxman.core.grammar.stages import RegexStage, StandardPre

_BIC_BODY = r"..."  # module-scope string, compiled by RegexStage
_CAP_PATTERN = BoundaryGuard.word_only().lookbehind + _BODY + BoundaryGuard.word_only().lookahead

def _notation(match: re.Match[str]) -> {CAP}Notation: ...

class {CAP}RecognitionGrammar(PipelineGrammar[{CAP}Notation]):
    name = "{cap}_recognition"
    semantics = "{cap}_recognition"
    single_value = True
    pre = StandardPre[{CAP}Notation](empty_guard=True)
    regex = RegexStage[{CAP}Notation](pattern=_PATTERN, notation_fn=_notation)
```
*Notes on fidelity vs ISSN/IBAN:* module-scope string, isalnum+upper stripping, (?ai:) ASCII guard, optional group guarantees only 8 or 11 never 9/10, word_only guards, label fused [\s:-]+, whitespace tolerance, PipelineGrammar vs bare Grammar. **Form-coverage traceability:** every §2.1 RECOGNIZE row maps to a concrete pattern element (group, branch, or pre-stage); every DEFER/REJECT row names the mechanism that would have handled it. A proposed pattern with no answer for an inventoried common form is incomplete.

**N vs M as one grammar vs two:** (Recommended) Single grammar with optional group — avoids cross-grammar containment spurious AMBIGUOUS. Alternative: two grammars with coalesced semantics.

### 4.3 Recognition pipeline contract (ARCHITECTURE.md)
- Grammar emits span-bearing RecognitionMatch, half-open [start,end), raw_text == text[start:end]
- RegexStage loops re.finditer, builds RecognitionMatch, Stages must not mutate text
- Engine owns within-grammar containment dedup (longer wins) and total recognition ordering
- Candidate dedup (value, recognition_rule, validation_rule) after validation

### 4.4 Guard boundaries against sibling grammars
| Grammar | Chars | Start | End guard |
|---------|-------|-------|-----------|
| {CAP} | ... | ... | ... |
| Sibling | ... | ... | ... |

### 4.5 Semantics affinity (HOW_TO_ADD_NEW_GRAMMAR.md, ARCHITECTURE.md Community Extensions)
- semantics = "{cap}_recognition" identity id, coalesce only if second grammar added

### 4.6 `single_value` — one mention per call vs batch processing
Recommendation: initial `single_value=True` (shipped precedent), segmentation path for batches, extra_grammars free-text variant with False if needed.

---
## 5. Provenance — the Authority that Validation Will Be Made Against

### 5.1 Authoritative spec & lineage

| Attribute | Finding |
|-----------|---------|
| Governing publisher | ... |
| Registration Authority | ... |
| Spec name | ... |
| Current edition | ... |
| Check character system | ... |
| Country code reference | ... |
| Related specs | ... |

**Structure (spec §):** verbatim structure quote + charset + examples
**Lineage table:** Edition | Date | Status | Note (at least 3 rows, back to first edition)
**Citation Details Table (for Provenance):** authority | spec_name | version | reference_url | lifecycle | publication_year | kind (every publication that will become a Rule file)

### 5.2 Rule / publication map (one file per publication — HOW_TO_ADD_NEW_CAPABILITY.md §5)
| Rule file | Module-level PUBLICATION (Provenance) | Rules in file | What it validates |
|-----------|----------------------------------------|----------------|-------------------|
| rules/iso_XXX_edYYYY.py | authority="...", specification_name="...", kind="...", reference_url="...", version="...", lifecycle="active", publication_year=... | Section X-... | Generic structure + checksum |
| rules/iso_3166_edYYYY.py (optional split) | ... | Section *-... | Country lookup |
| rules/swift_XXX_edYYYY.py (optional gated) | authority="...", kind="registry", reference_url="...", version="Rolling ..." | Section *-... | Registry membership, requires_features={"include_..."} |

Each Rule[BICNotation] subclass declares six enforced metadata attributes at class-definition time (Rule.__init_subclass__):

### 5.3 What each rule does vs does not own
- matches() validates strictly, never raises, Contract misconfigs caught in contract.__post_init__
- normalize() returns default compact form, never reads output_format, CI purity scan, same value across rules for dedup
- RuleStrategy choice: PARSER for structure/checksum, LOOKUP_TABLE for registry/country

### 5.4 Scope decision (the capability's analogue of IBAN §5.4 / BIC §5.4)
Whether country/registry validation is always-active vs gated — cost/benefit, staleness, per-country table size, always-active vs include_* flag.

### 5.5 Assignment / registration authority & Registry content
Network, RA + assigning institutions, record includes ..., cadence, mandatory registration data a–k

---
## 6. Presentation Seam — Contract & Capability

### 6.1 Contract (HOW_TO_ADD_NEW_CAPABILITY.md §7)
Every contract MUST inherit CapabilityContract (never Contract directly). @dataclass(frozen=True) without slots.

```python
from dataclasses import dataclass, field
from typing import ClassVar
from paxman.core.contract import CapabilityContract

@dataclass(frozen=True)
class {CAP}Contract(CapabilityContract):
    DEFAULT_OUTPUT_FORMAT: ClassVar[str] = "..."
    OFFERED_OUTPUT_FORMATS: ClassVar[frozenset[str]] = frozenset({...})
    capability_name: str = field(default="{cap}", init=False)
```

- DEFAULT_OUTPUT_FORMAT concrete string, OFFERED excludes default, resolved via resolve_output_format, create_contract() fixed keyword-only common block then capability-specific params
- Presentational-only invariant, output_format never in rules
- For {CAP}, offered formats model the interchange forms: | output_format | value example | Meaning |

### 6.2 Capability (HOW_TO_ADD_NEW_CAPABILITY.md §6)
```python
from paxman.core.capability import Capability
from paxman.core.domain import Grammar, Rule
from paxman.capabilities.{CAP}.notation import {CAP}Notation

class {CAP}Capability(Capability[{CAP}Notation]):
    name = "{cap}"
    def get_grammars(self) -> list[Grammar[{CAP}Notation]]: return [...]
    def get_rules(self) -> list[Rule[{CAP}Notation]]: return [...]
    @staticmethod
    def create_contract(...) -> {CAP}Contract: ...
    def format_value(self, value: str, output_format: str | None, notation: {CAP}Notation) -> str: ...
```

Registration via tools/new_capability.py

---
## 7. Validation — {levels}

### 7.1 Level 1 Generic structure, Level 2 Country/registry lookup, Level 3 Directory membership (gated)
Detailed algorithm, formal regex, worked examples, letter conversion table if checksum.

### 7.2 What makes {CAP} "valid" vs "country-valid" vs "issued/live-registered"
- valid (generic) — correct length/charset/checksum, always-active PARSER
- country-valid — generic plus country in registry, LOOKUP_TABLE always-active or gated
- issued/live-registered — actually present in RA directory, gated registry, determinism-by-snapshot

Like ISBN valid vs allocated, ISSN valid vs issued, IBAN valid vs country-valid.

---
## 8. Edge Cases

| # | Edge case | Expected resolution | Why |
|---|-----------|---------------------|-----|
| 1 | Lowercase | SUCCESS → compact | grammar folds upper |
| ... | Grouped spacing | SUCCESS | presentation-only |
| ... | Label present | SUCCESS, span includes label | fused pattern |
| ... | Head office / variant | Both SUCCESS distinct values | not coalesced |
| ... | Over-long / under-long | MISSING or INVALID | length guard |
| ... | Invalid country | INVALID with rule, SUCCESS w/o (false positive) | membership gate |
| ... | Test/passive flag | SUCCESS | informative only |
| ... | Embedded in sentence | SUCCESS with span | word-boundary guards |
| ... | Two distinct in one slice | AMBIGUOUS / MultipleMentionsError | segmentation |
| ... | Sibling confusion | MISSING | length discrimination |
| ... | Leading/trailing glue | MISSING | (?<!\w)/(?!\w) |
| ... | Quoted/bracketed | SUCCESS | inside punctuation |
| ... | Non-alphanum separators | MISSING | minimal v1 |
| ... | Invalid charset | MISSING | only A-Z0-9 plus label |
| ... | Country XK / edge | SUCCESS | ecosystem exception |
(Exhaust to 18 rows — mirror BIC §8 / IBAN §8)

---
## 9. Resolution-State Map (ARCHITECTURE.md Resolution Semantics)

| Input | Status | Why |
|-------|--------|-----|
| Valid (generic plus country) | SUCCESS → compact | single canonical via authority + lookup |
| Valid alternative spacing/case/label | SUCCESS (same compact) | presentation-only dedup |
| Invalid country/bad charset/wrong length | INVALID or MISSING | structural failure, rule rejects |
| No runs of required length | MISSING | no grammar recognized |
| Two distinct valid in one slice | AMBIGUOUS / MultipleMentionsError | single-slice ambiguity, use segmentation |
| XK / edge valid | SUCCESS | ecosystem exception |
| XX/ZZ invalid country | INVALID | membership claimed by lookup rule |
| Directory-gated input (if include_* true and not in directory) | INVALID | authority feature gating |
| Test/passive flag at pos N | SUCCESS | informative only |

---
## 10. Scaffolding & Repo Integration

### 10.1 Generated skeleton (tools/new_capability.py — HOW_TO_ADD_NEW_CAPABILITY.md Step 0)
```bash
uv run python tools/new_capability.py {CAP} --name {cap} --authority "..." --spec-name "..." --spec-url "..." --publication-year YYYY
```
Creates 13 files + one edit: paxman/capabilities/{CAP}/{notation,contract,capability,grammar/*,rules/*}, tests stubs, paxman/capabilities/__init__.py wiring. TODO(scaffold) markers guide replacement.

> Note: scaffolder single --spec-name covers one provenance. After scaffolding, add second provenance file manually or fuse.

### 10.2 Contract & grammar wiring
- get_grammars() returns [...], active_grammars omitted for initial design (base None), each grammar carries name *_recognition and non-empty semantics

### 10.3 Cross-cutting invariants (fail review if violated)
- No # type: ignore / # noqa / # pyright: ignore in paxman/ source
- No cross-capability imports (import only from paxman.core, import-linter enforced)
- No output_format token in any paxman/capabilities/*/rules/ module (source-scan)
- @dataclass(frozen=True, slots=True) notation; @dataclass(frozen=True) without slots contracts
- Deterministic by construction: same input + contract + library snapshot → same output

---
## 11. Recommended File Layout (mirrors ISSN and IBAN)

```
paxman/capabilities/{CAP}/
├── __init__.py
├── capability.py
├── contract.py
├── notation.py
├── grammar/
│   ├── __init__.py
│   └── {cap}_recognition.py
└── rules/
    ├── __init__.py
    ├── iso_XXX_edYYYY.py
    ├── iso_YYY_edYYYY.py  # country lookup or fused
    ├── swift_XXX_edYYYY.py # directory LOOKUP_TABLE (gated)
    └── data/                # only if registry layer adopted
        └── {cap}_directory.py  # snapshot frozenset/dict
```

Per-registry data module shape (parallel to ISBN rules/data/range_message.py):
```python
# rules/data/{cap}_directory.py
{DIRECTORY}: frozenset[str] | dict[str, dict[str, object]] = frozenset({...})
```

---
## 12. Test Strategy (mirrors HOW_TO_ADD_NEW_CAPABILITY.md and ISSN §9)

- Grammar tests: valid compact / variant inputs (lowercase, mixed case, label, multiple spaces, grouped, bare), multiple matches, incompatible format, empty, span invariants, name/semantics, boundary guard negatives — plus one positive vector per §2.1 RECOGNIZE form (whatever the capability's forms are — e.g., for ORCID: display/compact/spaced/URI/labeled; for Language: tag/code/name/underscore)
- Rule tests: generic structural rule valid/variant/invalid, normalize exact compact, provenance attributes, name/strategy conventions, leading positions preserved; country LOOKUP rule valid/invalid country, normalize agreement, strategy LOOKUP_TABLE, provenance kind specification; directory LOOKUP rule valid membership, requires_features gate, strategy LOOKUP_TABLE, kind registry
- Capability tests: notation frozen/hashable/slots, wiring counts, grammar/rule name conventions, format_value round-trips, create_contract factories
- Integration: MISSING/INVALID/SUCCESS/AMBIGUOUS or MultipleMentionsError, country gating, year temporal filtering, _clean_registry fixture, determinism/VersionStamp, span-bearing match, dedup
- Property tests (hypothesis): generate valid by picking country from COUNTRY_CODES + bank + location + branch → must canonicalize to itself; random strings → INVALID with high probability; grouped vs compact identical; format_value round-trip
- Consistency test: every shipped semantics covered by Rule.target_semantics, every registry entry's CC exercised
- Presentation purity: output_format source scan
- Real vectors: valid generic plus country, lowercase/case variants, label variants, grouped variants, invalid structure, invalid country, test/passive flag at pos N

---
## 13. Open Decisions (with recommendations)

| # | Decision | Recommendation | Rationale |
|---|----------|----------------|-----------|
| 1 | DEFAULT_OUTPUT_FORMAT — {options} | {default compact, grouped/paper offered} | wire vs human readability, presentational-only |
| 2 | Single grammar vs N grammars | Single {cap}_recognition initially, optional group; defer split to community extension with coalesced semantics | keeps surface minimal, avoids cross-grammar containment spurious AMBIGUOUS |
| 3 | Country lenience vs strict | Ship generic + country LOOKUP_TABLE as always-active; add directory LOOKUP_TABLE behind include_* False | mirrors valid vs country-valid split, cheap set membership |
| 4 | Grammar length strictness | Grammar enforces {N or M} exactly via optional group, never 9/10 | keeps grammar cheap and definitive |
| 5 | Case/space normalization in grammar vs rule | Grammar folds case and strips separators; rules validate upper alphanum only | syntax not semantics |
| 6 | Test/passive flag at pos N | Informative only, do not reject | routing hint not validity |
| 7 | Single PUBLICATION vs split | Either acceptable; recommend fused for v1, split for per-publication purity | fused keeps get_rules small |
| 8 | single_value for batch | True initially, segmentation for multi; offer extra_grammars variant with False | consistent with shipped precedent |
| 9 | Non-space separator tolerance | Grammar handles contiguous only; hyphens/dots in Pre or unsupported | spec allows only spaces in grouped display |
| 10 | Label span inclusion | Include label in raw_text span (fused regex), notation.compact label-free | mirrors ISSN/ISBN/IBAN |
| 11 | Which alternative written forms does v1 recognize (the full §2.1 inventory beyond the primary display form — the set is capability-specific; e.g., for ORCID compact/space-grouped/URI/labeled, for Language tag/code/name/underscore)? | RECOGNIZE every form attested by the spec or ≥2 validators unless recognition would be lossy/ambiguous; otherwise DEFER via extra_grammars, citing §2.1 | unhandled forms are permanent MISSING blind spots; discovering them post-ship costs a grammar rewrite |

---
## 14. Ambiguity Analysis (Paxman-specific)

- No inherent {CAP}-vs-{CAP} ambiguity — fixed structure eliminates positional ambiguity Date exhibits; two distinct in one slice is authorial choice, segmentation intended
- {CAP} vs non-{CAP} country is not lexical ambiguity — DEUTXXFF generic structure but not in country set is INVALID with rule, not competing value; without rule false SUCCESS; XK inclusion makes BANKXK22 SUCCESS
- {CAP} vs sibling length discrimination prevents cross-capability ambiguity — {CAP} N/M vs IBAN 15-34 vs ISIN 12 vs LEI 20 disjoint
- Branch/grouped vs compact is not ambiguity, distinct identity vs presentation
- Staleness is not ambiguity — determinism-by-snapshot, version in Provenance.version
- Flag semantics is not ambiguity — test vs passive still valid

---
## 15. URL Reference (authoritative, fetched YYYY-MM-DD)

| Claim | URL | Kind |
|-------|-----|------|
| ISO XXX:YYYY (Nth ed., current, Published) | https://www.iso.org/standard/XXXXX.html | primary |
| ... lineage withdrawn editions | ... | primary |
| RA overview / directory / search / registration | ... | primary |
| Country code authority | https://www.iso.org/iso-3166-country-codes.html | primary |
| ISSN/IBAN/BIC research precedent | docs/development/research/2026-08-XX-*.md | primary |
| Paxman scaffolder & conventions | HOW_TO_ADD_NEW_CAPABILITY.md, HOW_TO_ADD_NEW_GRAMMAR.md, ARCHITECTURE.md | primary |
| python-stdnum | https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/{cap}.py | primary |
| validator.js is{Cap} | https://github.com/validatorjs/validator.js/blob/master/src/lib/is{Cap}.js | primary |
| validator.js issue {XK fix} | https://github.com/validatorjs/validator.js/issues/... | primary |
| schwifty / ecosystem lib | https://github.com/mdomke/schwifty | primary/secondary |
| Paxman shipped precedent | paxman/capabilities/ISBN/grammar/ etc. + paxman/engine/orchestrator.py | primary |

---
## 16. Evidence Completion — Resolved

This report's {CAP}-specific authoritative evidence has been fetched and cited (YYYY-MM-DD):
- [x] ISO catalogue entry: {spec} (Nth ed., current, Published) superseding {prev} plus lineage; TC/SC; ICS; version lifecycle publication_year; citation anchored to spec §
- [x] RA and Directory provenance: authority, spec_name, kind registry, reference_url, version Rolling, lifecycle active
- [x] Structure: {length, charset, branch, flag semantics}
- [x] No checksum / checksum algorithm proved (whichever applies, with letter table and worked examples)
- [x] Country nuance: {country set equals ISO 3166-1 plus XK, subset, etc.}
- [x] Ecosystem regex consensus: generic + precise + stdnum + validator.js
- [x] Recognition-surface inventory complete (§2.1): every attested written form listed with evidence and a RECOGNIZE/DEFER/REJECT disposition — no silently unhandled form
- [x] Wild input shapes validated (§2.2) against spec + RA pages + corpora + validators
- [x] Label scope decision
- [x] Branch/XXX equivalence decision
- [x] Flag semantics decision
- [x] Directory liveness scope decision
File Layout / Rule provenance in §5.2 / §11 / §12 frozen for implementation (pending scaffolder invocation per HOW_TO_ADD_NEW_CAPABILITY.md Step 0).

---

## Appendix — What the Shipped ISBN, ISSN, Country and Phone Capabilities Teach {CAP} (verbatim precedent)

> The following precedent is **verbatim-sourced from the codebase** (not speculative) and anchors the proposal to what Paxman already ships.

Refer to `paxman/capabilities/ISBN/`, `ISSN`, `Country`, `Phone`, `IBAN` design notes plus `paxman/engine/orchestrator.py` and `paxman/core/domain.py` — see deep-dive summary in §4.2 / §5 / §6 above and the explore-verified notation, grammar, and rule excerpts. The four architectural lessons for {CAP}:
1. **Grammar strips, rule validates, capability formats.** ...
2. **One file per provenance, one class per section.** ...
3. **No `output_format` in rules, ever.** ...
4. **Single grammar with optional group avoids spurious AMBIGUOUS; cross-grammar containment is preserved.** ...

---

*Report saved to `docs/development/research/` (this directory) per MILESTONE guidance for {CAP}. It mirrors the structure, depth, and provenance discipline of `docs/development/research/2026-08-22-iban-canonicalization.md` and `docs/development/research/2026-08-23-bic-canonicalization.md` and the deeper ISBN precedent. For implementation, start from `tools/new_capability.py` scaffolder per HOW_TO_ADD_NEW_CAPABILITY.md Step 0.*

*Note: `docs/development/` is ephemeral per `docs/development/AGENTS.md` — not shipped, may drift, may be removed without notice, and must not be referenced by code or shipped docs.*
```

We covered the template — now the *how to hit it* part.

```

## Phase 3 — Quality Bar (What "Par or Above" Means)

Your report will be judged against BIC/IBAN on these axes. Do not submit until you pass:

- **Length & density:** 600–1000 lines, 60–110KB, 15–18 sections including appendix. BIC is 810 lines; IBAN is 832. Shorter is a miss.
- **Citation count:** 20+ primary URLs (ISO, RA, country authority, stdnum, validator.js, Schwifty-type libs) plus 5+ codebase paths, all fetched and dated. Every URL in §15 must have been fetched; never invent a URL.
- **Tables:** At least 8 formal tables (§1 personas, §2.1 representation inventory, §2.2 wild variants, snippets, §4.4 sibling guards, §5.1 lineage, §5.1 citation details, §5.2 rule map, §6.1 output_format, §8 edge cases, §9 resolution map, §13 open decisions, §15 URL reference). Copy the BIC markdown table syntax exactly.
- **Code blocks:** At least 5: notation dataclass, grammar PipelineGrammar with BoundaryGuard, contract CapabilityContract, capability Capability, Rule subclass template, and at least one normalization snippet. All must be `pyright`-clean in intent (frozen+slots notation, frozen without slots contract, frozenset target_semantics).
- **Wild variants:** Enumerate 14–18 categories (do not stop at 8). Include lowercase, grouped/paper, label, irregular whitespace, separators, head-office/branch, trailing annotation, multiple per line, quoted/bracketed, OCR/homoglyph, over-long/under-long, X-glued runs, invalid country — plus domain-specific ones.
- **Edge cases:** Exactly 18 rows, with Expected resolution (`SUCCESS`/`INVALID`/`MISSING`/`AMBIGUOUS` or `MultipleMentionsError`) and Why. Mirror BIC §8 style.
- **Resolution map:** 7–9 rows covering valid, variant, invalid, no runs, two distinct, XK-type edge, XX/ZZ invalid, directory-gated, flag semantics.
- **Open decisions:** 10 rows, each with Recommendation and Rationale, covering default format, grammar count, country lenience, length strictness, case normalization, flag semantics, publication split, single_value, separator tolerance, label span.
- **Ambiguity analysis:** 5 paragraphs, Paxman-specific, distinguishing true ambiguity from valid-vs-country-valid, length discrimination, presentation vs identity, staleness vs ambiguity, flag vs validity.
- **Evidence completion:** Checkbox list (§16) where every `x` corresponds to a section you actually completed. Do not check boxes you did not earn.

## Phase 4 — Execution Loop

1. **Explore first.** Fire 2–3 `explore` subagents in parallel: one for shipped capability precedent (`ISBN/ISSN/Country/Phone/IBAN/BIC` grammar/rule/capability patterns), one for the new capability's spec pages (ISO, RA, Wikipedia lineage), one for ecosystem validators (stdnum, validator.js, Schwifty analogues). Wait for their `<system-reminder>` before drafting — do not poll `background_output`.
2. **Fetch primary sources.** Use `webfetch` for every ISO catalogue page, RA page, and validator source file. Record the fetch date. If a fetch is blocked, escalate via `/ultimate-browsing` tier or note as `secondary` — never claim a primary claim from a secondary. While reading validator sources, extract their `clean()`/strip regexes verbatim — removed separators are direct evidence of alternative written forms; feed every discovery into the Phase 1C survey and the §2.1 inventory.
3. **Draft in order.** Write §0–§16 sequentially. Do not skip Executive Summary — it is the decision-maker's first read. Keep the **one file per publication** / **one Rule class per section** naming convention strict (`Section 5-bic-structure` style, `Section 4-iban-structure-mod97` style).
4. **Validate before saving.** Run `ruff check` / `pyright` mental check on all code blocks. Ensure no `output_format` appears in any `rules/` code block. Ensure `@dataclass(frozen=True, slots=True)` for notation and `@dataclass(frozen=True)` without slots for contracts. Ensure `target_semantics` and `requires_features` are `frozenset`.
5. **Save.** Write to `docs/development/research/YYYY-MM-DD-{cap}-canonicalization.md` (kebab, lowercase). Example: `2026-08-24-lei-canonicalization.md`. Overwrite only if the user confirms.
6. **Announce.** State the saved path, line count, citation count, and the 5 executive-summary findings in your final answer. Do not modify source code, tests, or configs.

## What Not to Do

- Do not invent specs or URLs. If you cannot fetch `iso.org/standard/XXXXX.html`, say so and use the closest primary you *did* fetch.
- Do not propose `slots=True` on contracts — incompatible with `CapabilityContract super().__post_init__`.
- Do not put authority data in `grammar/data/` or recognition keys in `rules/data/` — grammar/data serves grammars (keys), rules/data serves rules (authority mappings).
- Do not gate recognition on authority features or validation on input-shape features — two loci, two statuses: disabled grammar → `MISSING`, dropped rule → `INVALID`.
- Do not copy legacy `Section6_1` naming or `Phone/rules/common.py` patterns — they are flagged legacy exceptions via scoped `per-file-ignores`.

## Quick-Start Prompt (for the agent you invoke)

When the user says `research LEI`, your background agent's prompt should be:

```
[CONTEXT]: I'm researching {LEI} as a new Paxman capability. I need to match the IBAN/BIC gold standard so the report can directly seed a plan and a tools/new_capability.py scaffolding.
[GOAL]: Produce docs/development/research/YYYY-MM-DD-lei-canonicalization.md following the 16-section BIC/IBAN template with primary-source citations for every claim.
[DOWNSTREAM]: The report will unblock a plan agent that designs notation, grammar (PipelineGrammar + BoundaryGuard + StandardPre/RegexStage), contract (DEFAULT_OUTPUT_FORMAT/OFFERED_OUTPUT_FORMATS), rules (one file per publication, PARSER vs LOOKUP_TABLE), file layout, test strategy, open decisions, ambiguity analysis, and evidence completion.
[REQUEST]: Find: ISO 17442:2020 (and 2012) LEI structure, GLEIF RA and LEI Register (Level 1/Level 2), check digit via ISO 7064 MOD 97-10, real-world regex from python-stdnum/stdnum/lei.py and validator.js isLEI, schwifty-type LEI libs, and shipped Paxman precedent (ISBN/ISSN/Country/Phone/IBAN/BIC) for grammar/rule/provenance patterns. Enumerate every written representation this capability actually has — the set is domain-specific (for LEI illustration: official display, compact, space/dot-grouped, URI-prefixed, labeled prose; for your capability discover the real set) — with per-form evidence and a RECOGNIZE/DEFER/REJECT disposition. Skip tutorials, cite only primary sources, return evidence basis lines with URLs.
```

Fire that via `task(subagent_type="explore", run_in_background=true, ...)` and `task(subagent_type="librarian", run_in_background=true, ...)` in parallel.

## Reference Files to Read Before You Start

- `HOW_TO_ADD_NEW_CAPABILITY.md` (62KB spec — read first, §5 one file per publication, §7 contract, §10 test strategy)
- `HOW_TO_ADD_NEW_GRAMMAR.md` (strategy choice, PipelineGrammar vs bare Grammar, BoundaryGuard, semantics affinity)
- `ARCHITECTURE.md` (pipeline contract, determinism, VersionStamp, formatting seam, MISSING vs INVALID vs AMBIGUOUS)
- `docs/development/research/2026-08-23-bic-canonicalization.md` (your primary template — 810 lines)
- `docs/development/research/2026-08-22-iban-canonicalization.md` (checksum-depth complement — 832 lines)
- `docs/development/research/2026-08-21-issn-canonicalization.md` (concise single-grammar precedent)
- `docs/development/MILESTONE.md` (roadmap priority if user says "find one")
- `paxman/capabilities/__init__.py` (gap analysis: what is already shipped)
- `paxman/engine/orchestrator.py` (_dedup_spans longer-wins per grammar, _validate_affinity, single_value enforcement)
- `paxman/core/domain.py` (Rule.__init_subclass__ six attributes, Grammar.__init_subclass__ semantics)

---

*This skill is the distillation of two 100K research reports into a repeatable protocol. If your report does not look like them — same headings, same tables, same citation discipline, same code-block hygiene — you are not done.*
