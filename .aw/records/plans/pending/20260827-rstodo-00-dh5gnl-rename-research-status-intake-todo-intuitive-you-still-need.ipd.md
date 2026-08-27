# IPD: Rename research status intake -> todo (intuitive; you still need to do this)

- Date: 2026-08-27
- Kind: orchestrator
- Concern: The research status `intake` is opaque - it does not tell a reader "you still need to do this research" - and it is OVERLOADED (means both genuinely-unrun AND finished-but-unpromoted; e.g. this session's sk94i0/40g511 sat as `intake` despite being done + adopted). Graduated from backlog `sr47pt` (Set `researchtodo`); design/rationale in that item. Decision: rename `intake` -> `todo` ('Status: todo' unambiguously = the reader must act). New research lifecycle: `todo` -> `active` -> `reference`/`archive`. This Set is minted with a FRESH setid `rstodo` (NOT the source's `researchtodo`) per the graduation-link model (spec 4w7d6s): the child->source link is recorded as the front-matter field `From-Backlog: sr47pt` on this orchestrator (present + `aw check`-resolvable). The reciprocal `Graduated-To: rstodo` on the source backlog `sr47pt` is currently only in that item's workflow-history prose (the machine-readable field is owed once backlog `sjsoqq` builds the setid-uniqueness + graduation-link enforcement); this Set does not depend on that reciprocal field existing.
- Scope: Rename the `intake` status token to `todo` across the research contract + classification + CLI + index, and migrate the ~10 existing on-disk research docs, WITHOUT changing behavior (a `todo` research doc classifies READY/needs-attention exactly as `intake` does today). Two children: 01 renames the token in code (research_contract.py STATUSES/HOT_STATUSES:148-149, research_cmd.py creation defaults:189/244, attention_contract.py:231 + attention.py stale-reclass/color:176-228,485, research_index.py band + `## Needs addressing` header:185-195, research_archive.py docstrings/logic, cli.py:5994, term.py); 02 migrates on-disk docs `status: intake` -> `status: todo` + regenerates INDEX, with a backward-compatible read (accept legacy `intake` as an alias of `todo` during/after migration so nothing breaks mid-flight). COUPLING (not in scope here): the OVERLOAD fix (unrun vs done-but-unfiled) is spec 5tapom's tool-owned state-advancement; this rename fixes only the NAME. If 5tapom lands first/concurrently, `todo` should mean genuinely-not-started.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/cli.py, agent_workflows/term.py, .aw/records/research/, tests/
- Status: reviewed
- Set: rstodo
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: dh5gnl
- From-Backlog: sr47pt

## Workflow history
- 2026-08-27 reviewed (aw set): plan-review APPROVE WITH REVISIONS APPLIED: PR-001 E-01 precise + research_archive/comment coverage note; PR-002 From-Backlog:sr47pt added; PR-003 color-map compat-normalization-before-lookup; PR-004 execution contract; PR-005 V-01 concrete evidence; PR-006 softened Graduated-To prose

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Rename the research status `intake` -> `todo` (a name that says "you still need to do this") across code and the ~10 on-disk docs, behavior-preserving (a `todo` doc is READY/needs-attention exactly as `intake` is today), with a backward-compatible read during migration. Graduated from backlog sr47pt.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [ ] E-01 After children 01-02 execute, confirm the rename is complete and behavior-preserving. Specifically: (a) no LIVE `intake` token remains in code - i.e. no `intake` string literal used as a status VALUE (`STATUSES`/`HOT_STATUSES` members, `attention_contract` map keys, `attention.py`/`term.py` color-map keys, `research_index` band selector, `research_cmd` creation defaults, `cli.py` status choices, `research_archive.py` hot-state logic) except the single documented backward-compat READ alias that normalizes a parsed `intake` to `todo`; (b) any remaining `intake` occurrences are ONLY explanatory comments/docstrings that name the historical token (these are acceptable, or updated by child 01 where they describe current behavior - see the coverage note below); (c) all on-disk research docs read `todo` and `grep -rl '^status: intake' .aw/records/research/` returns nothing; (d) `aw attention` still classifies research `todo` as READY and a legacy `intake` value still classifies as READY (behavior unchanged); (e) the migrated docs keep their color band (the compat normalization runs BEFORE the color-map lookup, so a legacy `intake` does not fall through to no color); (f) `aw research index --check` is clean and the full suite is green.
  - Depends on: none
  - Expected outcome: a scoped grep (below) shows no live `intake` status VALUE except the compat alias; on-disk `^status: intake` count is 0; board classifies `todo` (and legacy `intake`) as READY with color preserved; `aw research index --check` clean; suite green.
  - Verification grep (records the exact command so "no live token" is falsifiable): `grep -rn "intake" agent_workflows/ | grep -vE "#|\"\"\"|compat|alias|legacy"` should surface only the intentional backward-compat normalization line; every other hit must be an explanatory comment/docstring.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

### Coverage note (fed to child 01 - close before E-01 can pass)

`research_archive.py` is in this Set's Scope-Paths and in child 01's Concern, but child 01's E-items (E-01..E-03) name only research_contract/research_cmd/attention_contract/attention/research_index/cli/term. Child 01 MUST also handle `research_archive.py`: it carries live `intake` references in its four-state-lifecycle docstring (`agent_workflows/research_archive.py:3,8`) and its hot-state STALE logic (`agent_workflows/research_archive.py:373`). If it participates in status VALUE comparison it must key on `todo` (via the normalized value); if it is purely descriptive prose it is updated to say `todo` so the docstring is honest. Likewise `attention.py` carries several `intake` references in comments/docstrings (the IPD h40usm reclass notes at :176-228 and the doctext at :198-203, plus :599) that describe current behavior and should be re-worded to `todo` so the code reads consistently. These are NOT the backward-compat alias and MUST NOT be left as stray live tokens. Until child 01 covers them, E-01(a)/(b) above cannot pass.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | p3o9je | Rename the `intake` token -> `todo` across research contract/classification/CLI/index/color | none |
| 02 | lpqy64 | Migrate the ~10 on-disk docs `intake` -> `todo` + regenerate INDEX; backward-compatible read | 01 |

Order 01 -> 02; orchestrator verifies. (Source link: front-matter `From-Backlog: sr47pt` on this orchestrator; the reciprocal `Graduated-To: rstodo` on `sr47pt` is in that item's history prose, machine-readable field owed to `sjsoqq`.)

## Completion criteria (the whole Set is done only when)

- The canonical token is `todo` (research_contract STATUSES/HOT_STATUSES); creation emits `todo`; attention/index/color/CLI use `todo` (01).
- All ~10 existing on-disk `status: intake` docs are `status: todo`; INDEX regenerated; a legacy `intake` value still reads as `todo` (backward-compat) so nothing breaks mid-migration (02).
- Behavior preserved: a `todo` research doc is classified READY/needs-attention identically to old `intake`; stale-reclass to PARKED still works.
- Full suite green.

## Cross-IPD validation

- No live `intake` token remains in code after both children (only the documented backward-compat alias).
- The attention classification for research is byte-identical in behavior (READY/PARKED/ACTIVE) before/after - only the token label changes.

## Deferred / out of scope (with reason)

- The intake OVERLOAD fix (unrun vs done-but-unfiled): spec 5tapom (tool-owned state advancement). This Set only renames the token.
- The uniform cross-type Priority field (backlog p9o1oo) and Summary field (ud28vy): separate.

## Scope check

- Over-scope: none.
- Under-scope: none (token rename + on-disk migration is the complete deliverable).

## Required tests / validation

Aggregate of children: contract/classification tests updated to `todo` + a compat test that legacy `intake` still classifies correctly (01); a migration test that on-disk `intake` docs become `todo` and INDEX regenerates (02); an attention behavior-parity assertion.

## Open questions

### OQ-01: Keep the `intake` backward-compat read alias permanently, or only through migration?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Pre-release, no external repos depend on `intake`, so a permanent alias may be unnecessary. Default: accept `intake` as an alias during migration + one release, then drop. Decide at implementation; behavior-parity tests cover both tokens meanwhile.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL output of each, and confirm it matches the expected result: (1) the scoped verification grep from E-01 (`grep -rn "intake" agent_workflows/ | grep -vE "#|\"\"\"|compat|alias|legacy"`) showing ONLY the intentional backward-compat normalization line; (2) `grep -rl '^status: intake' .aw/records/research/` returning nothing (empty); (3) `aw research index --check` printing a clean/pass result; (4) `aw attention` (or the research board view) showing at least one migrated doc as READY `todo`, and evidence (a targeted test or manual check) that a legacy `intake` value still classifies READY and keeps its color band; (5) the full test-suite run with its final pass line (e.g. the pytest summary) pasted verbatim. Do not mark V-01 done from the E-01 checkmark or from memory; only from this pasted output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Execution contract

- Human approval required before execution. This orchestrator authors no code; it coordinates children 01 (`p3o9je`) then 02 (`lpqy64`) and performs the whole-Set verification (E-01/V-01). Do not execute the children from this file; each child is approved and executed under its own gate.
- Resolved open questions: OQ-01 (alias lifetime) is non-blocking; default is to keep the `intake` backward-compat READ alias through migration + one release, then drop it in a follow-up. Its resolution is not a prerequisite to executing this Set.
- Scope fence: touch ONLY the Scope-Paths listed above. The `intake` OVERLOAD fix (unrun vs done-but-unfiled) is spec `5tapom`'s tool-owned state advancement and is explicitly OUT of scope here; if `5tapom` lands first or concurrently, `todo` should mean genuinely-not-started, but this Set only renames the token. Do not expand into priority/summary fields (backlog `p9o1oo`/`ud28vy`).
- Honesty (hard MUST): when reporting the suite or any command as passing, paste the ACTUAL runner output. Never claim a validation passed that was not run. V-01 is verified from pasted output, in a separate pass from the E-01 checkmark.
- Commit discipline: commit ONLY the files this Set changed, path-scoped (`git commit -m <msg> -- <path> ...`); never `git add -A`/`-a`/bare add; never push; never create tags or releases.
- Post-gate lifecycle move (NOT a checklist item; performed by the ipd-lifecycle gate after all E/V items are complete and validated): append a `## Workflow history` line recording execution, set terminal `Status: executed`, and `git mv` this orchestrator and both children from `pending/` to `.aw/records/plans/executed/` in a single path-scoped lifecycle commit. Do not move to `executed/` until `aw ipd lint --phase pre-transition` conforms and V-01 is verified with the pasted evidence above; otherwise STOP and report.
