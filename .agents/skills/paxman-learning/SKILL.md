---
name: paxman-learning
description: Use when creating, editing, or publishing any lesson, reference page, exercise widget, or learning record inside paxman-python's learnings/ teaching workspace — e.g. "add lesson NNNN", "publish the next recognition-layer lesson", "wire a new interactive exercise into learnings/", updating the course index manifest, or fixing course housekeeping there. Do not use for teaching workspaces in other repos (use teach instead).
---

# Paxman Learning Workspace

## Overview

The repo `/home/leonidas/dev/nexusnv/paxman-python` has a stateful teaching workspace rooted at
`learnings/`, served statically by the user. This skill is the publication mechanics layer on top of
the global `teach` skill — **REQUIRED BACKGROUND:** understand `teach` first (mission grounding,
ZPD, fluency vs storage strength, asset reuse). Everything below encodes conventions already
established in that workspace so you never have to re-derive them from the files.

**Core principle:** `learnings/index.html`'s `COURSE.lessons` manifest is the single source of
truth. A lesson file without a manifest entry does not exist.

## Before authoring

1. Read `learnings/MISSION.md`, `learnings/NOTES.md`, `learnings/RESOURCES.md` (it pins exact source
   files & line numbers you'll cite), and every `learning-records/*.md`.
2. The next topic is the first `status:"planned"` row in the manifest — cross-check with NOTES.md's
   lesson arc and pick what fits the ZPD. Calibrate against prior debrief feedback in NOTES.md.

## Authoring rules

- File goes to `learnings/lessons/<NNNN>-<slug>.html`; zero-padded number increments from the
  highest existing. The slug MUST byte-match the slug you later put in the manifest (the index
  builds card URLs from it — mismatch = 404).
- Link `../assets/course.css`. Never inline styles/scripts a future lesson could share — extend
  `course.css` or add an `assets/*.js` widget instead. Widgets available:
  `span-picker.js` (`PaxmanTeach.spanPicker({mount, simulate, rounds:[{caption,text,targets,why}]})`;
  spans are half-open `[start,end)`, `targets: []` renders the "No matches here" button, `why`
  shows after correct rounds) and `answer-check.js` (`<input data-accept="a|b|c">` + optional
  `data-success`, wrapped in `.q-block`, graded on Enter).
- Every lesson: one tightly-scoped win tied to MISSION.md; an interactive feedback-loop exercise;
  retrieval-practice questions with same-word-count answers; a cited primary source (verify claims
  against actual repo sources before asserting them); a "ask your teacher" reminder; a next-up footer.
- Crumbs nav links BOTH `../index.html` and the relevant reference page(s).
- Only cite repo behavior that is true on disk right now; re-read source files rather than trusting
  memory of them.

## Publish checklist

1. Create/edit the lesson file under `learnings/lessons/`.
2. Flip its manifest row in `index.html` (`slug`, `title`, `blurb`, `status:"live"`); add/refine
   planned rows for future lessons. Blurbs/titles go through `innerHTML` — escape entities.
3. Update the previous lesson's "next-up" teaser into a real link if it promises this lesson.
   Href style differs by context: **between lesson pages use sibling-relative**
   `<a href="0002-views-and-offsets.html">` (both live in `lessons/`); the **index manifest uses
   the rooted form** `"lessons/" + n + "-" + slug + ".html"`. Copying the manifest form into a
   lesson page silently double-prefixes the path.
4. Verify all internal links resolve mechanically:

```bash
cd <repo>/learnings && python3 - <<'EOF'
import os, re
bad = []
for d, _, fs in os.walk("."):
    for f in fs:
        if not f.endswith(".html"):
            continue
        path = os.path.join(d, f)
        for l in set(re.findall(r'(?:href|src)="([^"#]+)"', open(path).read())):
            if l.startswith(("http", "mailto")):
                continue
            t = os.path.normpath(os.path.join(d, l))
            if not os.path.exists(t):
                bad.append(f"{path}: {l}")
print("\n".join(bad) or "ALL LINKS RESOLVE")
EOF
```

Also `node --check` any edited standalone JS assets. The index manifest is an *inline* script node
--check can't see — extract and validate it too:

```bash
python3 -c "import re;m=re.search(r'<script>(.*?)</script>', open('index.html').read(), re.S);open('/tmp/opencode/index_inline.js','w').write(m.group(1))" && node --check /tmp/opencode/index_inline.js
```

Smoke test: serve with `uv run python learnings/serve.py [--port N]` — that ALSO runs the
progress-capture endpoint (`POST /api/progress`), so verify capture still round-trips:
`curl -fs -X POST http://127.0.0.1:<port>/api/progress -H 'Content-Type: application/json' -d '{"schema":1,"lesson":"smoke","rounds":[],"retrieval":[],"exercise_complete":null}'`
expect `{"saved": …}` (delete the resulting file in learnings/progress afterwards). The user usually
serves port 8000 already — if so, don't start a second server there (EADDRINUSE); curl it or pick a
spare port like 8123. Any lesson whose widgets changed must be played end-to-end (or at minimum
round-trip a realistic schema-1 payload) before publishing, since exercise wiring is its own surface.
5. Commit atomically, with dirty-tree triage first: defect fixes to shared assets unrelated to this
   lesson get their own housekeeping commit; changes the lesson's exercise depends on (widget
   behavior, new CSS classes) go INTO the publish commit alongside lesson file + manifest flip +
   previous lesson's next-up edit. Never commit an unregistered orphan lesson.
   When ONE file mixes both categories (commonly `course.css`), split hunks with `git add -p`;
   if the hunks are entangled, follow coupling: classes hoisted out of a page's inline `<style>`
   travel with that page's fix, exercise-only additions travel with the publish commit.

## Housekeeping

- Learning records and glossary terms are added only for demonstrated learner understanding (debrief
  evidence) — never just because material was covered. Glossary entries carry `<span class="status-tag">L####</span>`.
- Keep NOTES.md's lesson arc marked `(built)` as lessons publish; record new user preferences there.
- Tiny defects discovered along the way (dead anchors, missing styles): fix immediately; anything
  larger becomes a separate change noted in NOTES.md.

## Common mistakes

| Mistake | Reality |
|---|---|
| Lesson created but manifest row still `planned` | Invisible on the served course home; the manifest is the contract |
| Slug drift between filename and manifest | Card URL built from manifest slug 404s |
| Inlining CSS/JS per lesson | Workspace convention is shared assets; duplication rots fast |
| Trusting remembered paxman behavior | Lessons claim "verified repo behavior" — re-read the cited source each time |
| Writing reference styles inline in HTML pages | Belongs in `course.css` (reference-doc furniture section) |
| Second server on port 8000 | The user persistently serves it; curl it or pick a spare port |
| Manifest-style href inside a lesson page | Double-prefix path — lesson-to-lesson links are sibling-relative |
| Skipping inline-script validation | A manifest syntax error kills every card on the course home |
