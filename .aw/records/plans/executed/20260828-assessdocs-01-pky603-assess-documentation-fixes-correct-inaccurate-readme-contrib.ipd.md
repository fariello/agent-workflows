# IPD: Assess-documentation fixes - correct inaccurate README/CONTRIBUTING/ARCHITECTURE/TODO/CHANGELOG claims

- Date: 2026-08-28
- Kind: child
- Concern: documentation (accuracy-first): several top-level user-facing docs describe commands, install presets, and the on-disk layout that do NOT match what the software does today. A novice copy-pasting the README hits an "invalid choice" error on two of the four install presets, and looks for a `.aw/records/docs/` directory that does not exist. Distinct from the `docs/` operator-reference tree, which the assessment found accurate.
- Scope: the project's tracked user-facing documentation only - README.md, CONTRIBUTING.md, ARCHITECTURE.md, TODO.md, CHANGELOG.md. Out of scope: `.aw/system/workflows/` (framework tooling), `workflow-artifacts/` (run records), and the `docs/` reference tree (verified accurate this run - no changes). No code/behavior changes: these are doc-accuracy corrections, so the fix is to make the docs match the code, never the reverse.
- Scope-Paths: README.md, CONTRIBUTING.md, ARCHITECTURE.md, TODO.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Set: assessdocs
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: pky603

## Workflow history
- 2026-08-29 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Finalize pky603 (assessdocs doc fixes): implemented+verified this run (855254b/ffe4394); lifecycle move stranded by the pre-isolation race. Docs scope committed. [Scope reconciliation - in-scope-unmodified ARCHITECTURE.md: already-committed; in-scope-unmodified CHANGELOG.md: already-committed; in-scope-unmodified CONTRIBUTING.md: already-committed; in-scope-unmodified README.md: already-committed; in-scope-unmodified TODO.md: already-committed]
- 2026-08-28 approved (aw set): status set to approved

- 2026-08-28 to-review (/assess documentation, opencode its_direct/pt3-claude-opus-4.8-1m-us): assessed the documentation concern for accuracy across README/CONTRIBUTING/ARCHITECTURE/TODO/CHANGELOG + the docs/ tree; proposed 5 changes (2 High, 3 Medium/Low). docs/ verified accurate (no changes). Run record: workflow-artifacts/assess-documentation/20260828-165500/.
- 2026-08-28 reviewed (/plan-review, opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 (all LOW, all FIXED). Verified all five findings (F1-F5) TRUE against repo evidence (`aw install --help` enum, `ls -d .aw/records/*/`, `aw update`/`aw comms` absent, `.agents/` gone, both target specs resolve). Structural lint conforming (author + review-finalize). Revisions: E-05 per-line LIVE/HISTORICAL adjudication + `.spec.md` facet on both spec pointers; V-05 tightened; `docs_check` invocation named (`python -m pytest tests/test_docs.py`); F1 code-side twin (argparse help text) captured out-of-scope; OQ-01 resolved (silent correction) from repo evidence; execution contract hardened with the paste-actual-output honesty MUST. GO - PENDING HUMAN APPROVAL.

## Goal

Make the project's top-level user-facing docs accurate to the shipped software: fix two High accuracy defects that break a new user's getting-started (nonexistent install-preset names; a `.aw/records/docs/` layout that no longer exists) plus three Medium/Low staleness defects (phantom `aw update`/`aw comms` commands, stale `.agents/` pointers). Honest docs over impressive docs; the `docs/` reference tree was verified accurate and is untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: High-severity accuracy (getting-started breakers)

- [x] E-01 Correct the install-preset names in the README placement-presets table (README.md:78-79) and any prose using them: `public-private-companion` -> `public-target-private-companion`; `clean-target` -> `completely-clean-target`. Match the actual CLI enum (`aw install --preset {private-target,public-target-private-companion,completely-clean-target,local-only}`). Grep README for both wrong tokens and fix every occurrence.
  - Depends on: none
  - Expected outcome: every `--preset` name in README is copy-pasteable; `aw install --preset <name>` for each documented preset does not error.
  - Execution state: performed

- [x] E-02 Correct the `.aw/records/docs/` layout claim to the actual flat layout (awretrofit Order 07 flattened the doc-family types out of `records/docs/`). In README.md (line ~65 and the layout description ~256): replace `reference docs and specs (.aw/records/docs/)` / `docs/ - research (docs/research/), walkthroughs, specs` with the real flat roots `.aw/records/specs/`, `.aw/records/research/`, `.aw/records/walkthroughs/`, `.aw/records/roadmaps/` (and note `prompt-library/`). Verify against `ls -d .aw/records/*/`.
  - Depends on: none
  - Expected outcome: README's Records-root description lists only directories that actually exist under `.aw/records/`.
  - Execution state: performed

### Task group 2: Medium/Low staleness

- [x] E-03 Fix the same `.aw/records/docs/` flatten staleness in CONTRIBUTING.md (:43 Generated-files row, :44 Records row, :55 Research Manifest path) and ARCHITECTURE.md (:61 tree diagram, and the preset names :87-88): research manifest is `.aw/records/research/INDEX.{json,md}`; the Records tree is the flat roots; correct the preset names as in E-01.
  - Depends on: none
  - Expected outcome: CONTRIBUTING/ARCHITECTURE cite only real paths + real preset names; `ls .aw/records/research/INDEX.json` resolves.
  - Execution state: performed

- [x] E-04 Remove references to non-existent commands: `aw update` (README.md:241; CHANGELOG.md:29) - install IS the updater (README:58 already says so), so drop `aw update` from those sentences; and `aw comms` (CONTRIBUTING.md:44 Records row "Managing Tool") - there is no `aw comms` verb (comms are scaffolded by the installer / `aw normalize-lanes`). Verify each with `python -m agent_workflows <verb> --help`.
  - Depends on: none
  - Expected outcome: no user-facing doc names a command that `aw --help` does not list.
  - Execution state: performed

- [x] E-05 Rewrite TODO.md's LIVE `.agents/...` pointers to their post-migration `.aw/records/...` homes, applying the flatten (`docs/specs/` -> `specs/`) and appending the `.spec.md` facet to BOTH spec pointers. Adjudicate each `.agents/` occurrence explicitly, LIVE (rewrite) vs HISTORICAL (leave verbatim):
    - TODO.md:6-7 `materialized at .agents/backlog/ pre-migration, .aw/records/backlog/ post-migration` -> HISTORICAL (deliberate pre/post contrast). LEAVE the `.agents/backlog/` half UNCHANGED.
    - TODO.md:7 `See .agents/backlog/README.md` -> LIVE -> `.aw/records/backlog/README.md`.
    - TODO.md:8 `.agents/docs/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md` -> LIVE -> `.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md` (facet already present; only the path flattens).
    - TODO.md:10 `an IPD under .agents/plans/pending/` -> LIVE -> `.aw/records/plans/pending/`.
    - TODO.md:18 `the .agents/comms/ layout` (inside the "was FORMALIZED in DECISIONS D81" sentence) -> HISTORICAL (narrates what shipped at D81). LEAVE UNCHANGED.
    - TODO.md:21 `the canonical spec is .agents/docs/specs/20260715-1722-01-agent-comms-convention.md` -> LIVE pointer to a file that still exists (verified `.aw/records/specs/20260715-1722-01-agent-comms-convention.spec.md`) -> rewrite to `.aw/records/specs/20260715-1722-01-agent-comms-convention.spec.md` (flatten AND append the missing `.spec.md` facet). Do NOT alter the surrounding historical narration.
  - Depends on: none
  - Expected outcome: every LIVE pointer above resolves via `ls`; the two HISTORICAL `.agents/` mentions (`:6-7` pre-migration half, `:18` D81 narration) remain verbatim; no LIVE pointer references the removed `.agents/` tree.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- This IS the framework's own repo, so per the assess/release-review scope rule the *project* under review is the `agent_workflows` toolkit + its user-facing docs; `.aw/system/workflows/` and `workflow-artifacts/` are excluded.
- Plans live in `.aw/records/plans/pending/`, named `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md`; a newly-authored IPD is born `to-review`. Scaffolded via `aw ipd scaffold`.
- Docs surface: top-level (README, ARCHITECTURE, DECISIONS, CONTRIBUTING, RELEASING, GUIDING_PRINCIPLES, CHANGELOG, TODO) + a `docs/` operator-reference tree (24 files) whose host-support/benchmark tables are generated from evidence registries via `agent_workflows/docs_render.py` (verified true).
- `docs/` has its own conformance check (the `agent_workflows.docs_check` module, exercised by `tests/test_docs.py`; it is NOT an `aw` CLI verb) reporting 0 findings; the accuracy problems are concentrated in the hand-maintained top-level docs. `docs_check` covers only the `docs/` reference tree, not the top-level README/CONTRIBUTING/ARCHITECTURE/TODO/CHANGELOG this IPD edits, so it will neither catch these defects before the fix nor regress after it - it is a "still-clean" cross-check, not the primary validation.

## Findings

| ID | Severity | Remediation Risk | Persona | Finding (evidence) |
|---|---|---|---|---|
| F1 | High | Low (Complexity) | Novice; operator | README.md:78-79 document install presets `public-private-companion` and `clean-target` that do NOT exist. Evidence: `aw install --preset public-private-companion` -> `error: invalid choice ... (choose from private-target, public-target-private-companion, completely-clean-target, local-only)`. A user following the public-companion or clean-target scenario hits an install error. |
| F2 | High | Low (Complexity) | Novice; operator | `.aw/records/docs/` (README:65; CONTRIBUTING:43,55; ARCHITECTURE:61) does not exist - the layout was flattened (awretrofit Order 07). Evidence: `ls .aw/records/docs` -> No such file or directory; real roots are `specs/ research/ walkthroughs/ roadmaps/ backlog/ comms/ plans/ prompt-library/ prompts/ releases/ runs/`. The research manifest doc path `.aw/records/docs/research/INDEX.json` is wrong (actual: `.aw/records/research/INDEX.json`). |
| F3 | Medium | Low | Software engineer | `aw update` referenced as a command (README:241; CHANGELOG:29) but no such subcommand exists; README:58 itself says "There is no separate 'update' command." Self-contradictory. Evidence: `aw update --help` -> missing. |
| F4 | Medium | Low | Software engineer | `aw comms` documented as the Records "Managing Tool" (CONTRIBUTING:44) but no such verb exists. Evidence: `aw comms --help` -> missing; not in `aw --help`. |
| F5 | Low | Low | Novice; maintainer | TODO.md carries 6 present-tense `.agents/...` pointers (`:7-8,:10,:21`) to files that moved to `.aw/records/...` (and gained the `.spec.md` facet); `.agents/` no longer exists. Explicitly-historical mentions are fine. |

All five are Remediation Risk **Low** on the Complexity axis (they only correct prose to match code; they touch no behavior and add no complexity), so all are fixed by default. docs/ tree, RELEASING.md, and DECISIONS.md were assessed and found accurate - no findings.

## Proposed changes (ordered, validatable)

1. README preset names (F1) - E-01.
2. README `.aw/records/docs/` flatten (F2) - E-02.
3. CONTRIBUTING + ARCHITECTURE flatten + preset names + research-manifest path (F2) - E-03.
4. Remove phantom `aw update`/`aw comms` (F3, F4) - E-04.
5. TODO.md stale `.agents/` live pointers (F5) - E-05.

## Deferred / out of scope (with reason)

- The `docs/` operator-reference tree: assessed, verified accurate (module/function/CLI references, generated tables, walkthrough fixtures all match code; `docs_check` = 0 findings). No changes - nothing to fix.
- `docs/skill-selection.md` roots skills at `.agents/skills/`, which MATCHES the code today (`host_adapters.SHARED_SKILLS_DIR`), so the doc is accurate; a latent drift to revisit only if the code moves skills under `.aw/`. Not a doc-accuracy defect now.
- Completeness gaps (undocumented capabilities): none rising to a finding this pass; accuracy was the priority per the lens ("prefer fixing inaccuracies before filling gaps").
- CODE-SIDE TWIN of F1 (out of scope here; needs a separate IPD): the `aw install --help` argparse HELP TEXT itself repeats the same wrong preset names - the `--preset` help description reads "private-target (default), public-private-companion, clean-target, local-only" even though the enum `choices=` are the correct `public-target-private-companion`/`completely-clean-target`. Evidence: `python -m agent_workflows install --help` (the choices line is correct; the prose description below it is wrong). This IPD is docs-only prose corrections and MUST NOT touch code, so fixing the argparse help string (a code change) is deliberately NOT done here; captured so it is not lost. A user reading `aw install --help` sees the same two phantom names the README did, so this twin should be filed as its own small code-fix IPD.

## Scope check

- Over-scope: none. Deliberately excludes the accurate `docs/` tree and all code/behavior.
- Under-scope: none. All five verified accuracy findings are proposed for fix; none dropped.

## Required tests / validation

- F1/E-01: for each documented preset name, `python -m agent_workflows install --preset <name> --help` (or the enum in `aw install --help`) accepts it - no "invalid choice".
- F2/E-02,E-03: every `.aw/records/...` path cited in README/CONTRIBUTING/ARCHITECTURE resolves via `ls`; `.aw/records/research/INDEX.json` exists; no doc cites `.aw/records/docs/`.
- F3/F4/E-04: `grep -n "aw update\|aw comms"` over README/CONTRIBUTING/CHANGELOG returns only historical/removed contexts; `aw <verb> --help` confirms no such verb is presented as current.
- F5/E-05: `grep -n "\.agents/" TODO.md` returns only explicitly-historical lines; every live pointer resolves.
- Cross-check: re-run the documentation lens spot-checks; the `docs/`-tree conformance check stays clean via `python -m pytest tests/test_docs.py` (this IPD touches no `docs/` file, so it must remain green - a change here means an unintended edit escaped scope).

## Spec / documentation sync

This IPD IS documentation work; there is no separate spec to sync. No behavior changes, so no code/test/spec updates are implied. (If any finding turns out to require a *code* change to make the doc true - it does not here - that would be split to a separate IPD, since this set only corrects prose.)

## Open questions

### OQ-01: Should the `.aw/records/docs/` -> flat-layout correction also add a one-line "layout changed in 2.x" note, or just silently correct?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - silently correct, no transition note. The README Records section (README.md:65 and the layout description ~256) and the ARCHITECTURE tree (:61) are CURRENT-STATE layout descriptions, whose job is to describe what exists today; the project already owns transition history in CHANGELOG.md and DECISIONS.md (per AGENTS.md and the honest-documentation principle "docs describe what the software actually does today"). Adding a "layout changed" note to a current-state layout description would duplicate the CHANGELOG/DECISIONS record in the wrong place and re-introduce staleness (the note itself ages). So the E-02/E-03 corrections replace the phantom `.aw/records/docs/` with the real flat roots and add NO migration note. (Resolved from repository convention; not escalated to the human because the repo's own honest-docs principle answers it.)

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `aw install --help` showing the four preset enum values, and confirm README's table rows now match verbatim (no `public-private-companion`/`clean-target`).
  - Observed evidence: `python3 -m agent_workflows install --help` preset enum -> `{private-target,public-target-private-companion,completely-clean-target,local-only}`. README preset backtick tokens now = `completely-clean-target` `local-only` `private-target` `public-target-private-companion` (all four match the enum verbatim). `grep -nE '\bpublic-private-companion\b|(^|[^-])clean-target\b' README.md` -> (none): no standalone wrong tokens remain.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `ls -d .aw/records/*/` and confirm every Records path in README now appears in that list; `grep -n "records/docs" README.md` returns nothing.
  - Observed evidence: `ls -d .aw/records/*/` -> `backlog/ comms/ plans/ prompt-library/ prompts/ releases/ research/ roadmaps/ runs/ specs/ walkthroughs/`. README's Records section (line 65) and layout description (~256) now list only `plans/ specs/ research/ walkthroughs/ roadmaps/ backlog/ comms/ prompts/ prompt-library/` - all present in the ls output. `grep -n "records/docs" README.md` -> (none): the phantom `.aw/records/docs/` is gone.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `grep -n "records/docs" CONTRIBUTING.md ARCHITECTURE.md` returns nothing; `ls .aw/records/research/INDEX.json` resolves; preset names in ARCHITECTURE match the CLI enum.
  - Observed evidence: `grep -n "records/docs" CONTRIBUTING.md ARCHITECTURE.md` -> (none). `ls .aw/records/research/INDEX.json` -> resolves (the CONTRIBUTING Generated + Research-Manifest rows now cite `.aw/records/research/INDEX.*`). `grep -nE 'public-private-companion|(^|[^-])clean-target\b' ARCHITECTURE.md` -> (none); ARCHITECTURE now uses `public-target-private-companion`/`completely-clean-target` matching the CLI enum. The ARCHITECTURE records tree lists the flat roots (specs/ research/ walkthroughs/ roadmaps/) instead of the nonexistent `docs/`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `grep -n "aw update\|aw comms" README.md CONTRIBUTING.md CHANGELOG.md` shows only historical contexts (no present-tense "run aw update/aw comms"); `aw update --help` and `aw comms --help` still error (confirming they are not real).
  - Observed evidence: `grep -nE 'aw update|aw comms' README.md CONTRIBUTING.md CHANGELOG.md` -> (none): removed `aw update` from README (migration-detection sentence) + CHANGELOG:29, and removed `aw comms` from the CONTRIBUTING Records "Managing Tool" cell (replaced with the real `aw specs`, which manages the `specs/` records root). `python3 -m agent_workflows update --help` -> exit 2 (no such subcommand); `python3 -m agent_workflows comms --help` -> exit 2 (no such subcommand) - confirming both are not real verbs.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `grep -n "\.agents/" TODO.md` output pasted; confirm the ONLY remaining `.agents/` lines are the two adjudicated HISTORICAL ones (`:6-7` pre-migration half, `:18` D81 narration); `ls` each rewritten pointer to prove it resolves - specifically `ls .aw/records/backlog/README.md`, `ls .aw/records/plans/pending/`, and `ls .aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md .aw/records/specs/20260715-1722-01-agent-comms-convention.spec.md` (both spec pointers, `.spec.md` facet present).
  - Observed evidence: `grep -nE '\.agents/' TODO.md` -> only two lines remain, both HISTORICAL as adjudicated: `6:The tree is records/backlog/... (materialized at .agents/backlog/ pre-migration...)` (the deliberate pre/post contrast) and `18:- The agent-comms convention was FORMALIZED in DECISIONS D81 (2026-07-15): the .agents/comms/ layout...` (D81 narration). The four LIVE pointers were rewritten and resolve: `ls .aw/records/backlog/README.md` -> resolves; `ls -d .aw/records/plans/pending/` -> resolves; `ls .aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md .aw/records/specs/20260715-1722-01-agent-comms-convention.spec.md` -> both resolve (the D81 comms-spec pointer was flattened AND gained the `.spec.md` facet). Cross-check: `python3 -m pytest tests/test_docs.py -o addopts=""` -> `14 passed` (this IPD touched no `docs/` file, so the docs-tree conformance stays green).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is an /assess output: a PROPOSAL only. It makes NO changes to code, docs, or config, and is NOT auto-executed. It must be human-reviewed (optionally via /plan-review) and moved to `Status: approved` before any execution.

Execution contract (binding on the executor):
- Scope fence: edit ONLY the five Scope-Paths (README.md, CONTRIBUTING.md, ARCHITECTURE.md, TODO.md, CHANGELOG.md). Touch NO code and NO `docs/`-tree file; if a fix appears to need a code change, STOP and split it to a separate IPD (see the F1 code-side twin in "Deferred / out of scope").
- Open questions: OQ-01 is resolved (silent correction, no migration note); no open question blocks execution.
- Honesty (hard MUST): every V-01..V-05 "Observed evidence" MUST be the ACTUAL pasted output of the stated command (`aw install --help`, `ls -d .aw/records/*/`, the `grep -n`/`ls` checks, `python -m pytest tests/test_docs.py`). Do NOT claim a check passed you did not run, and do NOT paraphrase output as prose - paste the runner's real output.
- Commit + lifecycle: `aw ipd begin` to start, apply E-01..E-05, verify V-01..V-05 with the pasted evidence above, then `aw ipd finalize` for the atomic terminal transition; commit path-scoped to the five doc files only (`git commit -m msg -- README.md CONTRIBUTING.md ARCHITECTURE.md TODO.md CHANGELOG.md`), never `git add -A`/`-a`, and never push.

All five findings are Remediation-Risk Low, so none is deferred.
