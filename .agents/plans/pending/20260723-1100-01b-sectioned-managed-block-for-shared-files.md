# IPD: sectioned managed-block mechanism for shared instruction files (aw:block + per-directive sections)

- Date: 2026-07-23
- Concern: per-directive consent + identifiability inside shared instruction files (AGENTS.md, and when present CLAUDE.md/GEMINI.md) - replace the monolithic managed block with individually marked, individually updatable/removable directive sections
- Scope: replace the single `AGENT-WORKFLOWS:BEGIN/END` monolithic block with the decided sectioned marker scheme (`aw:block` wrapper + openers-only `aw:<slug>` sections, per-file comment syntax), including legacy-marker CONVERT-not-append migration and the native CLAUDE.md/GEMINI.md mirror path; wire per-section identity/consent/drift to the manifest from IPD 01. Product code + tests + docs. DEPENDS ON IPD 01 (the manifest + hash-drift model). Split from IPD 01 this session because it is a large, high-regression rewrite of shipped code with its real CONSUMERS being IPDs 02 (untracked directive) and 05 (interactive-questions AGENTS.md half).
- Status: to-review
- Set: install-safety-and-ownership
- Order: 1.5
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-23 created via SPLIT from IPD 20260723-1100-01 (opencode its_direct/pt3-claude-opus-4.8-1m-us): during execution of IPD 01 (post-approval), paused at the STOP-and-report gate - IPD 01 bundled the moderate manifest/hash-drift foundation with this large, high-regression monolithic-to-sectioned block rewrite that has no consumer in IPD 01 itself. Per maintainer decision, split the block rewrite here. Carries the former IPD-01 Step 2 (sectioned parser/writer) and Step 4 (legacy + native-mirror migration) and findings M5-M8. Depends on IPD 01's manifest. NOT yet reviewed at its new scope.

## Goal

Replace the single monolithic `AGENT-WORKFLOWS:BEGIN/END` block in shared instruction files with the decided sectioned marker scheme, so each agent-workflows directive is an INDIVIDUALLY identifiable, updatable, removable, and consent-able section, and per-section identity/consent/drift are tracked in the IPD-01 manifest by slug + normalized hash. Convert existing monolithic blocks (and the CLAUDE.md/GEMINI.md mirror) in place with no human-visible change and reinstall idempotence, recognizing but not re-emitting the legacy format.

Why it matters: today the block is all-or-nothing (`agents_pointer_block`/`merge_pointer_block`/`update_agents_pointer`), so a user cannot accept some directives and decline others, and an upgrade re-stamps the whole block. The token-economy + per-directive-consent work (research 2317; IPDs 02, 05) needs per-section granularity. This IPD provides the sectioning MECHANISM those consumers require.

## Marker scheme (decided with the maintainer, this session)

- Outer wrapper `<!-- aw:block -->` ... `<!-- /aw:block -->`; inner sections use OPENERS ONLY, `<!-- aw:<slug> -->`; a section runs from one opener to the next opener, or to `/aw:block`, or to EOF. No per-section close tags.
- Markers render in the target file's OWN comment syntax: bare `<!-- aw:... -->` in Markdown; `#`-prefixed `# <!-- aw:... -->` in `#`-comment config files (`.gitignore`, YAML, TOML). One logical construct, per-file-syntax rendering.
- Forgiving parse WITH the existing fail-safe preserved: missing `/aw:block` -> EOF close + drift flag; duplicate/ambiguous/mangled markers -> do NOT destructively rewrite; append or report (mirrors today's `merge_pointer_block` malformed behavior, `engine.py:1221-1222`).
- Never rely on host comment-stripping for correctness (markers are literal bytes on every host; only Claude Code is documented to drop HTML comments from context).
- Per-section identity/consent/drift live in the IPD-01 manifest keyed by slug + normalized-content hash, never on marker adjacency.
- GENERAL POLICY: every agent-workflows-managed block in a shared config file carries the `aw:block` markers in that file's comment syntax + a short "DO NOT REMOVE, deliberate" rationale (IPD 02 ships the first `#`-comment instance in `.gitignore`).

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| M2 | HIGH | Medium | adopter | consent / behavior | The AGENTS.md block is monolithic all-or-nothing; a user cannot accept some directives and decline others, and an upgrade re-stamps the whole block, risking silently (re)adding behavior the user did not want. | `engine.py:105-106`, `agents_pointer_block` `:582`, `update_agents_pointer` `:1211` |
| M4 | MEDIUM | Low | maintainer | token economy | The monolithic block inlines all directive prose, paid every turn; per-directive sections are the groundwork so directive BODIES can move to owned files (done per-directive later). | research 2317; `agents_pointer_block` inlines prose |
| M5 | MEDIUM | Medium | adopter | anti-regression (native mirror) | The block is mirrored into CLAUDE.md/GEMINI.md when present (`update_agents_pointer` loops `NATIVE_AGENT_FILES` `:1264-1294`); the sectioning + migration MUST cover that mirror path or those files keep old monolithic markers and drift. | `engine.py:1264-1294`, `NATIVE_AGENT_FILES` `:104` |
| M6 | HIGH | Medium | maintainer | backward-compat (marker change) | Changing the marker constants from `AGENT-WORKFLOWS:BEGIN/END` to `aw:block` means a repo with OLD markers, run through a matcher counting NEW markers, gets a SECOND block appended (duplicate). Legacy detection MUST run FIRST and convert-not-append; legacy is recognized but never re-emitted (maintainer decision). | `merge_pointer_block` `:1172-1208` (counts `AGENTS_BEGIN`); `:105-106` |
| M7 | LOW | Low | maintainer | safety fail-safe | The existing `merge_pointer_block` fail-safe (malformed/ambiguous markers -> append rather than destructive regex over user text) must be preserved in the new sectioned parser. | `engine.py:1221-1222`, `:1198-1200` |
| M8 | MEDIUM | Low | maintainer | anti-regression (tests) | Existing tests pin: literal `<!-- AGENT-WORKFLOWS:BEGIN -->` in AGENTS/CLAUDE/GEMINI, idempotent count==1, user-prose-before-block preserved, malformed-marker append (count 2), and `remove_agents_pointer` strips only the block. These are the characterization set for the risky refactor. | `tests/test_installer.py:636-698`, `tests/test_comms.py:145` |

## Proposed changes (ordered, validatable; checkpointed)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | M2,M7 | Implement the sectioned managed-block parser + writer per the marker scheme above: parser returns the `aw:block` region + ordered `aw:<slug>` sections (opener-to-next-opener/`/aw:block`/EOF); writer renders wrapper + openers-only, in the target file's comment syntax. Forgiving parse with the fail-safe (M7): missing `/aw:block` -> EOF close + drift flag; duplicate/ambiguous/mangled markers -> append/report, never destructive. Foreign text before the first opener / after the block preserved untouched. | `agent_workflows/engine.py` (+ new parse/render helpers) | Medium | parser correct on well-formed + degenerate (missing close, duplicate, empty, foreign text); writer round-trips; per-file-syntax rendering; fail-safe on mangled markers |
| 2 | M2 | Replace the monolithic internals (`agents_pointer_block`/`merge_pointer_block`/`update_agents_pointer`/`remove_agents_pointer`) with the sectioned mechanism while keeping the SAME external install/uninstall entry points and the manifest wiring from IPD 01. Per-section consent + drift consult the IPD-01 manifest by slug+hash (declined -> not written tombstone; accepted-unchanged -> update; drift -> preserve + report). | `agent_workflows/engine.py` | Medium | install writes sections; declined section not written; drift preserved; uninstall strips sections/block only; manifest records per-section slug+hash |
| 3 | M6,M5 | LEGACY migration, mandatory legacy-first: recognize the old `AGENT-WORKFLOWS:BEGIN/END` pair and CONVERT it in place to `aw:block` + `aw:<slug>` (e.g. `aw:pointer`) with no content loss and NO duplicate block; apply the same conversion to CLAUDE.md/GEMINI.md when present (M5). Legacy markers recognized on install AND uninstall, never re-emitted. Regenerate this repo's AGENTS.md to the new form; confirm verbatim round-trip of the human-visible text. | `agent_workflows/engine.py`, `AGENTS.md` (regenerated) | Medium | old-block repos (AGENTS + CLAUDE/GEMINI) convert in place, no content loss, NO duplicate; this repo's AGENTS.md human-visible text unchanged; reinstall idempotent (empty diff) |
| 4 | M2,M5,M6,M7,M8 | Tests: parser/writer (well-formed, missing close, duplicate/mangled fail-safe, empty, foreign text, per-file syntax); per-section consent/drift via the manifest; legacy convert-not-append INCLUDING the CLAUDE/GEMINI mirror; reinstall idempotence (empty diff); and the M8 characterization set (`test_installer.py:636-698`, `test_comms.py:145`) consciously updated to the new markers with human-visible content unchanged. | `tests/test_installer.py`, `tests/test_comms.py`, `tests/test_manifest.py` | Medium | full suite green; legacy-convert + native-mirror + fail-safe covered; golden invariant "reinstall = empty diff" holds; paste actual output |
| 5 | M2 | Docs/decision sync: DECISIONS entry (pin at execution) for the sectioned-block model + marker scheme + legacy-convert rule; CHANGELOG 1.3.0; update the IPD-01 manifest README to describe sections. | `DECISIONS.md`, `CHANGELOG.md`, manifest README | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| The interactive-questions `aw:ask-user` section + owned directive body + per-directive prompt | Low | scope | Consumer of this mechanism; the interactive-questions IPD's AGENTS.md half. | IPD 05, after this. |
| The untracked-safety `.gitignore` managed block (first `#`-comment instance) | Low | scope | Consumer of this mechanism; IPD 02. | IPD 02, after this. |
| Host-adapter tier expansion (`.agents/skills/`, other host rules/hooks) | Medium | complexity | The research's larger roadmap; independent of the core sectioning primitive. | Separate IPD(s). |

## Scope check

- Over-scope: none - the sectioned parser/writer + monolithic replacement + legacy/native migration + tests + docs. The manifest itself is IPD 01; the ask-user/untracked directives are their own IPDs.
- Under-scope: MUST cover the CLAUDE/GEMINI native mirror (M5); MUST detect legacy markers and convert-not-append (M6); MUST preserve the malformed/ambiguous fail-safe (M7); MUST keep human-visible AGENTS.md content unchanged and reinstall idempotent; MUST consciously update the M8 characterization tests; MUST consult the IPD-01 manifest for per-section consent/drift (never marker adjacency).

## Required tests / validation

- Section mechanism: parser on well-formed multi-section, missing `/aw:block` (drift-flagged, not rewritten), duplicate/mangled markers (fail-safe append/report), empty/absent block, foreign text preserved, per-file-syntax rendering; writer round-trip; slug ordering stable.
- Consent/drift (via IPD-01 manifest): declined slug not written; accepted-unchanged updated; drift preserved + reported.
- Migration/idempotence: old monolithic repo (AGENTS + CLAUDE/GEMINI mirror) converts, no content loss, NO duplicate; reinstall empty diff; this repo's AGENTS.md human-visible text unchanged.
- Characterization (M8): `test_installer.py:636-698` and `test_comms.py:145` pinned then consciously updated to the new markers, human-visible content unchanged.
- Full suite `python -m pytest -q` GREEN; paste ACTUAL output. `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- DECISIONS (sectioned-block model + marker scheme + legacy-convert), CHANGELOG 1.3.0, the manifest README (sections). Cross-reference research 2317/2241.

## Open questions

- OQ1 (order relative to consumers): this IPD (01b) is sequenced right after IPD 01 and before its consumers (02, 05). Confirm 02/05 should reference this mechanism rather than each rebuilding sectioning. Lean: yes, single mechanism here (P8). Confirm at review.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. DEPENDS ON IPD 01 (manifest) being executed first.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. Never clobber user drift or lose human-visible content in migration.

CHECKPOINTED EXECUTION: (1) sectioned parser/writer + tests (characterization of current block behavior FIRST); (2) monolithic replacement + manifest wiring + tests; (3) legacy + native migration + idempotence; (4) full suite + characterization updates; (5) docs. Re-run the full suite at each checkpoint; pause and report if scope grows.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1.
2. On human approval (and after IPD 01 executed), set `Status: approved` (+ `Approval:`), execute in checkpoints, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
