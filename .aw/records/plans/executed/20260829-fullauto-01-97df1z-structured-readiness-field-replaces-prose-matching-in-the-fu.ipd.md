# IPD: Structured Readiness field replaces prose matching in the --full-auto auto-approve gate (shared predicate, both drivers)

- Date: 2026-08-29
- Kind: child
- Concern: `--full-auto` silently never fires. Its help promises "Automatically approve reviewed plans with 'GO - PENDING HUMAN APPROVAL' verdict and execute them immediately" (oc_runipd.py:2854), but the gate `is_plan_review_approved` (oc_runipd.py:229, near-duplicate at agy_runipd.py:404) can never return True in practice, for THREE INDEPENDENT reasons - and the prose match is only the third. REVIEW CORRECTED THE DIAGNOSIS (PR-001): (1) THE EXTRACTOR IS BROKEN AND IS THE PRIMARY CAUSE. `extract_last_history_entry` (oc_runipd.py:215) slices `text[text.rfind("## Workflow history"):]` to END OF FILE and returns the LAST `- ` bullet in that slice. Because `## Workflow history` sits near the TOP of a plan, that slice spans every later section (measured on this plan: 15,654 chars across 13 headings), so the "last history entry" is actually the last bullet of the FINAL section - typically `- Cohesion rationale: ...` or `- Lifecycle move: ...`. Verified: for 20 of 20 pending plans the returned string is NOT a history line at all. (2) HISTORY IS NEWEST-FIRST, so even a correctly bounded reader must take the FIRST bullet, not the last: `status_set.py:762` does `new_lines.insert(i + 1, hist_entry)`, prepending directly under the heading (its own comment says "Append", which is wrong). Verified on wtiso-02: file order is `approved` -> `/plan-review` -> `reviewed` -> `to-review` -> `draft`, newest first. (3) Only then does the prose problem apply: the documented template (plan-review.md:301) is `- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>`, carrying no readiness term. THE PLAN'S ORIGINAL EVIDENCE WAS MISREAD: plan g7hljt DOES carry `readiness GO - PENDING HUMAN APPROVAL` in its history line, but `is_plan_review_approved(g7hljt)` still returns **False** (verified live), because the extractor never reaches that line. So g7hljt does not show the gate "sometimes fires"; it shows the phrase is irrelevant while the extractor is broken. CONSEQUENCE FOR THE FIX: a structured field alone does NOT fix this bug, and the originally proposed back-compat fallback would have been dead code, because it re-used the same broken extractor.
- Scope: Fix the gate at its real cause, then make it structural. (1) FIX THE EXTRACTOR: bound the `## Workflow history` slice at the next `## ` heading and select the NEWEST (first) record, reusing the repo's existing correct reader rather than writing a fourth one - `attention._history_section_lines` (attention.py:86) already bounds the section correctly and `attention_contract.HISTORY_RECORD_RE` (attention_contract.py:450) already defines the `- YYYY-MM-DD <text>` record grammar. (2) Add an optional, recognized plan front-matter field `- Readiness:` with a closed lowercase-kebab enum `go` | `go-pending-approval` | `no-go` (house convention: bare lowercase enums, cf. `Status:`, `Kind:`, `Priority:`, `Gate-Kind:`); absent = unknown = NOT auto-approvable (fail closed). (3) Extract ONE shared predicate (and the history helper, also duplicated at oc_runipd.py:215 / agy_runipd.py:391) into a single module both drivers import, so the rule cannot drift. (4) The predicate returns True only for `Readiness: go-pending-approval` (or `go`), with a BOUNDED BACK-COMPAT FALLBACK that reads the CORRECTED newest history record: accept verdict `APPROVE` or `APPROVE WITH REVISIONS APPLIED` AND no unresolved blocking open question; never accept `NO-GO`/`CONDITIONAL-GO`. (5) Make `/plan-review` (and its parity twin `plan-review-long`) WRITE the field at its finalize step instead of relying on prose. Preserve the existing safety property: a `NO-GO`/`CONDITIONAL-GO` readiness must never auto-approve. Out of scope: widening what `--full-auto` is ALLOWED to do (see the Deferred note on the `--by-human` attestation), and the broader driver unification.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_schema.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/plan-review-long.md, tests/
- Item-Dependencies: none
- Status: executed
- Set: fullauto
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 97df1z

## Workflow history
- 2026-09-03 executed (opencode its_direct/pt3-claude-opus-5-1m-us): EXECUTED. The --full-auto gate is repaired at its real cause and made structural: the history extractor is bounded and newest-first, the recognized optional 'Readiness' field carries the machine signal, one shared plan_readiness predicate replaces the drifted per-driver duplicates, and both plan-review variants write the field at finalize. All 7 V-items carry pasted evidence; code merged as 209227d5 (lane merge d4d8c538). [Scope reconciliation - out-of-scope .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md: E-05 required parity with plan-review.md. Scope-Paths named only plan-review-long.md, but that file is a memory-kernel orchestrator that loads one step file at a time, so the operative finalize instruction had to land in the step file it names; recorded in V-05.; out-of-scope agent_workflows/cli.py: NOT THIS PLAN'S CHANGE. Committed by concurrent work 1273806c (fix(runs): document 'aw runs repair'). Flagged by the known shared-checkout attribution defect, backlog a8eufb.; out-of-scope agent_workflows/ipd_lifecycle.py: NOT THIS PLAN'S CHANGE. Committed by concurrent work 6771e590 (fix(lifecycle): anchor control state on the checkout). Known attribution defect, backlog a8eufb.; out-of-scope agent_workflows/plans_index.py: NOT THIS PLAN'S CHANGE. Committed by concurrent plan e32j35 in b3233960 (Status-regex parity cross-reference comments). Known attribution defect, backlog a8eufb.; out-of-scope agent_workflows/run_viewer.py: NOT THIS PLAN'S CHANGE. Committed by concurrent work 1273806c (fix(runs): document 'aw runs repair'). Known attribution defect, backlog a8eufb.; out-of-scope agent_workflows/selectors.py: NOT THIS PLAN'S CHANGE. Committed by concurrent plan e32j35 in b3233960 (partial execution, text-free selector enumeration). Known attribution defect, backlog a8eufb.; out-of-scope agent_workflows/status_set.py: E-07 doc-only correction: the writer comment said 'Append' while the code PREPENDS, which is the misstatement that would let a future reader restore the extractor bug. One comment line; no logic changed.]
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-007. Misdiagnosis corrected: the extractor is the primary bug (rfind-to-EOF, unbounded; 20/20 pending plans return a non-history bullet) and history is newest-first, so the structured field alone would NOT have fixed --full-auto and the back-compat fallback would have been dead code. Added E-06/E-07 + V-06/V-07. OQ-02 opened (blocking): --full-auto self-asserts --by-human.
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `--full-auto` actually work: first FIX THE BROKEN HISTORY EXTRACTOR that makes the gate return False for every plan regardless of wording, then decide auto-approval from a structured `- Readiness:` enum written by `/plan-review`, evaluated by ONE shared predicate imported by both drivers, instead of regex-matching model-authored prose. The structured field is the durable design; the extractor fix is what actually unbreaks the feature.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 0: fix the actual bug (the extractor)

- [x] E-06 Fix `extract_last_history_entry` so it returns the NEWEST record of the `## Workflow history` SECTION, and prove the current behavior is wrong with a failing-first test. Two defects to fix together (they are one read path): (a) the slice is UNBOUNDED - `text[text.rfind("## Workflow history"):]` runs to EOF and therefore spans every later section (measured: 15,654 chars / 13 headings on this plan), so bound it at the next `## ` heading; (b) it takes the LAST bullet, but history is NEWEST-FIRST (`status_set.py:762` prepends via `new_lines.insert(i + 1, ...)`), so select the FIRST matching record. REUSE the existing correct primitives instead of writing a fourth reader: `attention._history_section_lines` (attention.py:86) for bounding and `attention_contract.HISTORY_RECORD_RE` (attention_contract.py:450, `^- (?P<date>\d{4}-\d{2}-\d{2}) .+$`) for the record grammar - a non-record bullet (e.g. `- Cohesion rationale:`) must never be returned. This E-item is FIRST because the structured field cannot fix the bug by itself and the back-compat fallback is dead code without it.
  - Depends on: none
  - Expected outcome: a test that FAILS on today's code and passes after: for a real plan the helper returns the `- YYYY-MM-DD ...` newest record, not `- Cohesion rationale: ...`; verified across all pending plans that the result always matches `HISTORY_RECORD_RE`.
  - Execution state: performed

- [x] E-07 Reconcile the newest-first ordering CONTRACT so the fix cannot silently regress. `.aw/records/plans/README.md:44` says history is "an appended, dated line per workflow" and the writer's own comment at `status_set.py:756` says "Append Workflow history", but the code PREPENDS (`insert(i + 1, ...)`), making the section newest-first. Pick the code's actual behavior as the contract (do NOT change the writer - reordering 400 existing plans' history is out of scope and would be a destructive rewrite), and correct the two misleading statements to say NEWEST-FIRST, so a future reader does not "fix" the reader back to last-bullet.
  - Depends on: E-06
  - Expected outcome: README and the code comment state newest-first; a docstring on the shared helper records that the FIRST record is the newest and cites `status_set.py:762` as the reason.
  - Execution state: performed

### Task group 1: the structured field

- [x] E-01 Add the optional recognized plan field to `agent_workflows/ipd_schema.py`: `META_READINESS = "Readiness"` plus membership in `META_RECOGNIZED` (mirroring `META_SCOPE_PATHS`:152 / `META_BLOCKS_RELEASE`:182 - recognized-but-OPTIONAL, NOT added to `META_REQUIRED`, so an absent field never fails an existing plan), and a closed value enum `READINESS_VALUES = frozenset(("go", "go-pending-approval", "no-go"))` with a reader that returns None for absent/unparseable.
  - Depends on: none
  - Expected outcome: a plan carrying `- Readiness: go-pending-approval` lints clean; a plan with no `Readiness:` lints clean (no IPD-M103 unknown-field, no new required-field failure); a plan with `- Readiness: bogus` is reported as an invalid value.
  - Execution state: performed

### Task group 2: one shared predicate (kill the duplicate)

- [x] E-02 Create `agent_workflows/plan_readiness.py` holding the SINGLE implementation of the corrected history helper (from E-06) and `is_plan_review_approved(plan_path)`, moved out of the drivers. NOTE the duplicates are NEAR-identical, not byte-identical as first written (PR-005, verified): the agy copies at agy_runipd.py:391/404 have had their DOCSTRINGS stripped relative to oc_runipd.py:215/229, which is exactly the silent drift that makes a shared module the right call. New logic: return True iff the plan's `- Readiness:` is `go-pending-approval` or `go`; return False for `no-go`; and when the field is ABSENT apply the bounded back-compat fallback over the CORRECTED newest history record - accept only if its verdict is `APPROVE` or `APPROVE WITH REVISIONS APPLIED` AND the plan has no unresolved blocking open question AND the record does not contain `NO-GO`/`CONDITIONAL-GO`. Absent field + non-approving verdict = False (fail closed). DEFINE "unresolved blocking open question" MECHANICALLY, not by prose judgement: an `### OQ-*` block whose `- Blocking:` is `yes` and whose `- Status:` is not `resolved` (cite the shape used by this plan's own OQ section); if that cannot be parsed, treat it as blocking (fail closed).
  - Depends on: E-01, E-06
  - Expected outcome: one importable predicate; `go-pending-approval` -> True; `no-go` -> False; absent + `APPROVE WITH REVISIONS APPLIED` + no blocking OQ -> True; absent + `REVIEWED - OPEN QUESTIONS` -> False; absent + blocking OQ -> False; an unparseable OQ block -> False.
  - Execution state: performed

- [x] E-03 Repoint both drivers at the shared predicate and DELETE their local copies: `oc_runipd.py` (defs at :215/:229; call sites :1274, :2384) and `agy_runipd.py` (defs at :391/:404; call sites :1368, :2455). (Line numbers re-verified in review; the plan's originals were ~14-40 lines stale - PR-006.) Import from `plan_readiness`; keep any existing public re-export so external callers do not break.
  - Depends on: E-02
  - Expected outcome: `grep -c "def is_plan_review_approved" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returns 0 for both; both drivers' auto-approve paths call the shared function; no behavioral difference between oc and agy.
  - Execution state: performed

### Task group 3: the workflow writes the field

- [x] E-04 Update `.aw/system/workflows/plan-review/plan-review.md` Step 4 (finalize) to WRITE `- Readiness: <go|go-pending-approval|no-go>` into the plan's front matter as a required output of the review, alongside the existing `Status: reviewed` and history line. State explicitly that the history-line prose is NOT the machine signal and that the readiness values map from the workflow's existing readiness vocabulary (GO -> `go`, GO - PENDING HUMAN APPROVAL -> `go-pending-approval`, NO-GO -> `no-go`).
  - Depends on: E-01
  - Expected outcome: the workflow body instructs writing the structured field; a reviewer following it produces a plan whose `- Readiness:` matches its reported readiness.
  - Execution state: performed

- [x] E-05 Apply the same change to `.aw/system/workflows/plan-review-long/plan-review-long.md`, which index.md documents as kept in "deliberate parity" with the single-file variant, so the two do not diverge.
  - Depends on: E-04
  - Expected outcome: both workflow bodies specify the field identically; a diff of their readiness instructions shows no semantic difference.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Optional-but-recognized plan fields are declared in `ipd_schema.py` as a `META_*` constant added to `META_RECOGNIZED` but NOT `META_REQUIRED` (the pattern used by `Scope-Paths`:152 and `Blocks-Release`:182). Recognition suppresses the IPD-M103 unknown-field error; VALUE validation lives in the `aw check` surface, not the schema layer.
- House enum style for machine-read fields is bare lowercase (kebab where multi-word): `Status: to-review`, `Kind: bug`, `Priority: high`, `Gate-Kind: artifact`. `Readiness: go-pending-approval` follows this; a shouty prose value like `GO - PENDING HUMAN APPROVAL` would be the only exception and reintroduces spacing/dash ambiguity.
- The two drivers duplicate helpers rather than sharing them (near-verbatim, already drifting: the agy copies lost their docstrings); the `dhuape` backlog item tracks unifying them onto a shared runner library. This plan takes the narrow step of sharing just this predicate rather than waiting for that larger refactor.
- The repo ALREADY has correct workflow-history reading primitives, and a fourth hand-rolled parser would be the wrong move: `attention._history_section_lines` (attention.py:86) bounds the section at the next `## ` heading, and `attention_contract.HISTORY_RECORD_RE` (attention_contract.py:450) defines the `- YYYY-MM-DD <text>` record grammar with `last_history_at` documented as "the date of the LAST record in file order". Note that helper's own "last in file order" wording is about DATE derivation over a bounded list; for selecting the CURRENT state the newest record is the FIRST one, because the writer prepends (`status_set.py:762`).
- History is written NEWEST-FIRST by `aw set` (`status_set.py:762`, `new_lines.insert(i + 1, hist_entry)` directly under the heading), even though the surrounding comment and `.aw/records/plans/README.md:44` say "append". Any code reading "the latest history entry" must take the FIRST record, not the last.

## Findings

- PRIMARY ROOT CAUSE (corrected in review, PR-001): THE EXTRACTOR, not the prose. `extract_last_history_entry` (oc_runipd.py:215) does `text[text.rfind("## Workflow history"):]` with NO upper bound, so the slice runs to EOF across every later section, then returns the LAST `- ` bullet found. Verified live: for 20 of 20 pending plans the returned string is not a history record at all (typically `- Cohesion rationale: ...`, `- Lifecycle move: ...`, or `- If any validation fails, ...`). Any readiness token in the real history line is therefore unreachable, whatever its wording.
- SECOND ROOT CAUSE (PR-002): HISTORY IS NEWEST-FIRST, so "last entry" is semantically backwards even once bounded. `status_set.py:762` prepends with `new_lines.insert(i + 1, hist_entry)` right under the heading; its own comment says "Append", which is wrong. Verified on wtiso-02, file order: `approved`, `/plan-review`, `reviewed`, `to-review`, `draft`. A bounded-but-last reader would return the `draft` line.
- THIRD CAUSE (the plan's original diagnosis, still valid but not sufficient): the gate regexes model-authored prose. `oc_runipd.py:236` is `re.search(r"GO\s*-\s*PENDING\s*HUMAN\s*APPROVAL", last_entry, re.IGNORECASE)`, while the documented template (plan-review.md:301) emits verdict + finding ids only.
- THE ORIGINAL EVIDENCE WAS MISREAD (PR-003): the plan cited g7hljt as proof the phrase sometimes appears and so the gate sometimes fires. g7hljt DOES contain `readiness GO - PENDING HUMAN APPROVAL` in its history line, but `is_plan_review_approved(g7hljt)` returns **False** when run against it (verified), because the extractor returns `- Lifecycle move: implement E-01..E-06, ...`. So the gate has NEVER fired for either plan, and prose non-determinism was not the operative cause. This matters because it changes the fix: a structured field WITHOUT the extractor fix would still return False for every plan, and the proposed back-compat fallback would have been unreachable dead code.
- STALE EVIDENCE (PR-004): the plan states the 8 wtiso plans are `Status: reviewed`. They are all `Status: approved` as of this review (verified across all 8), and their history shows `approved (aw set)` above the `/plan-review` record - i.e. they were approved by another route after that run. The observation of 0-of-8 auto-approval remains true and the concern stands; only the current-state claim needed correcting.
- The existing negative guard (`Readiness:\s*(NO-GO|CONDITIONAL-GO)` at oc_runipd.py:238) already reads a `Readiness:`-shaped token, so the field name is consistent with what the code half-expects today. Note it currently reads that token from the HISTORY ENTRY, not front matter; E-02 moves the authoritative read to front matter.
- DUPLICATION (PR-005): the predicate and its helper exist twice but are NOT byte-identical - the agy copies (agy_runipd.py:391/404) have no docstrings while the oc copies (oc_runipd.py:215/229) do. Minor, but it is live evidence of the drift the shared module prevents; fixing only one driver would leave `aw agy run --full-auto` broken.
- STALE CITATIONS (PR-006): every `file:line` in the original plan was ~2-40 lines off (defs at :215/:229 not :213/:227; call sites :1274/:2384 and :1368/:2455 not :1256/:2339 and :1350/:2415). Corrected throughout; execution should re-verify rather than trust any snapshot.
- SAFETY OBSERVATION (PR-007, recorded not fixed): `set_plan_approved` (oc_runipd.py:243) shells out to `aw set approved --by-human`, so the MACHINE asserts the human-approval attestation. The attestation spec exists precisely to be an "explicit attested speed bump" that "prevents an honest agent from AUTO-advancing a transition the human must own" (`20260815-0151-01-honest-human-approval-attestation.spec.md`, lines 22/28-30). `--full-auto` is opt-in and this predates the plan, so it is not this plan's bug; but this plan makes the path FUNCTION for the first time, which converts a latent contradiction into a live one. See Deferred and OQ-02.

## Proposed changes (ordered, validatable)

1. FIRST, fix the history extractor (bounded section + newest record, reusing `attention._history_section_lines` and `attention_contract.HISTORY_RECORD_RE`), with a failing-first test. Without this, nothing else fixes the bug.
2. Correct the newest-first ordering contract in `README.md` and the misleading "Append" comment at `status_set.py:756`.
3. `ipd_schema.py`: recognize `Readiness` + define the value enum + reader.
4. `plan_readiness.py`: new shared module with the single corrected helper + predicate and the field-first / fallback logic (with a mechanical blocking-OQ test).
5. `oc_runipd.py`, `agy_runipd.py`: delete local copies, import the shared predicate.
6. `plan-review.md` and `plan-review-long.md`: write the field at finalize.
7. `tests/`: extractor regression, schema recognition, predicate truth table, both drivers' auto-approve path, and an end-to-end review->approve->execute chain.

## Deferred / out of scope (with reason)

- WHETHER `--full-auto` SHOULD SELF-ATTEST `--by-human` AT ALL (PR-007): `set_plan_approved` (oc_runipd.py:243) has the machine pass the attestation flag whose documented purpose is to stop an agent auto-advancing a human-owned transition (attestation spec lines 22/28-30). This is pre-existing and opt-in, and narrowing it is a POLICY decision for the maintainer, not a bug fix - so this plan does not change it. But it must not be executed silently either: this plan is what makes the path actually work, so OQ-02 puts the question to the human before execution. Deferring the DECISION is fine; deferring the DISCLOSURE would not be.
- Changing the newest-first WRITER or reordering existing plans' history: rejected. The writer's behavior becomes the contract (E-07 fixes the docs instead), because rewriting ~400 plans' history sections is destructive and out of scope for a gate fix.
- Full unification of the two drivers onto a shared runner library: tracked by backlog `dhuape`; this plan shares ONLY this predicate to fix the bug without taking that refactor.
- Backfilling `- Readiness:` into the already-reviewed wtiso plans: not required. They are now `Status: approved` (PR-004) so `--full-auto`'s reviewed-only branch no longer applies to them, and for any other pre-existing reviewed plan the corrected back-compat fallback accepts an `APPROVE...` verdict.
- Any change to what `/plan-review` decides (its rubric or verdict vocabulary): unchanged; this plan only changes how the decision is RECORDED and READ.

## Scope check

- Over-scope: none. E-07 is doc-only and is the minimum needed to stop the reader fix from being "corrected" back into the bug.
- Under-scope: none, after review ADDED the extractor fix (E-06) and the ordering contract (E-07). The original plan was under-scoped in a way that mattered: field + shared predicate + drivers + workflow bodies would have shipped a still-broken gate, and its own back-compat fallback would have been unreachable.

## Required tests / validation

- EXTRACTOR REGRESSION (the primary bug, must fail before the fix): on a real multi-section plan the helper returns the newest `- YYYY-MM-DD ...` record and NOT `- Cohesion rationale: ...`. Assert the returned string matches `HISTORY_RECORD_RE` for EVERY plan in `.aw/records/plans/pending/` (today: 0 of 20 pass). Include a bounded-section case (a `- ` bullet in a later section is never returned) and a newest-first case (a plan whose history has `approved` newest and `draft` oldest returns the `approved` record).
- CHARACTERIZATION OF THE OLD BUG: a test that documents today's wrong output, so the fix is provably a change in behavior and not a no-op.
- Schema: `Readiness: go-pending-approval` lints clean; absent lints clean; `Readiness: bogus` is flagged with its rule id.
- Predicate truth table (the core): `go-pending-approval` -> True; `go` -> True; `no-go` -> False; absent + `APPROVE WITH REVISIONS APPLIED` + no blocking OQ -> True; absent + `APPROVE` -> True; absent + `REVIEWED - OPEN QUESTIONS` -> False; absent + verdict-approve BUT an unresolved blocking OQ -> False; absent + an UNPARSEABLE OQ block -> False (fail closed); a history record containing `NO-GO` -> False even if a verdict word appears.
- ADVERSARIAL (the point of the plan): a plan whose history line contains the OLD prose phrase but whose `- Readiness: no-go` MUST NOT auto-approve - the structured field wins over prose.
- REAL-PLAN INTEGRATION (not just synthetic fixtures): run the finished predicate against actual repo plans, including g7hljt (which carries the old prose phrase) and a current `reviewed` plan, and assert the outcomes are the intended ones. This is the check that would have caught the misdiagnosis: a synthetic-fixture-only suite can pass while the gate stays broken on every real plan.
- Both drivers: an auto-approve test for `oc_runipd` AND `agy_runipd` (the bug exists in both); assert the local duplicate definitions are gone.
- End-to-end: a reviewed plan with `Readiness: go-pending-approval` under `--full-auto` transitions reviewed -> approved -> queued for execute (assert the `ipd-auto-approved` event is appended).
- NO-WIDENING CHECK: assert `--full-auto` still refuses a plan that is not `Status: reviewed`, and that nothing in this change auto-approves a `draft`/`to-review` plan.

Validation command: `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_ipd_schema.py -q` plus the new predicate/extractor tests, and a full default-suite run `python3 -m pytest -p no:randomly` (paste ACTUAL runner output; never claim success unrun).

## Spec / documentation sync

- If `AGENTS.md` or `.aw/records/plans/README.md` enumerates plan front-matter fields, add `Readiness` there as optional-and-recognized.
- Fix the `--full-auto` help text (oc_runipd.py:2854 and the agy equivalent): it currently promises approval of plans "with 'GO - PENDING HUMAN APPROVAL' verdict", which describes the prose match this plan removes. It must describe the structured `Readiness` field, and per OQ-02's outcome must state honestly whether/how it records human approval.
- Correct the newest-first history ordering statements (E-07): `.aw/records/plans/README.md:44` ("an appended, dated line") and the `status_set.py:756` "Append Workflow history" comment both contradict the prepending code at `status_set.py:762`.
- Record in the shared module's docstring that the history section is NEWEST-FIRST and bounded at the next `## ` heading, so the next reader does not reintroduce the `rfind`-to-EOF / last-bullet bug.

## Open questions

### OQ-01: Should `Readiness: go` (already human-approved) also auto-approve, or only `go-pending-approval`?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Both accepted. `go` per the workflow's vocabulary means the clean bar is met AND the human has approved, which is a strictly stronger condition than `go-pending-approval`; refusing it would be surprising. `Status: approved` remains the authoritative sign-off record, so a `go` plan is already execute-routed by status anyway; accepting it in the predicate is harmless and avoids a confusing edge case.

### OQ-02: Should `--full-auto` keep self-asserting `--by-human`, now that this plan makes that path actually work?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER (2026-08-31): option (c), a DISTINCT
  NON-HUMAN ATTESTATION, so the audit trail never claims a human approved something no human approved.
  `--full-auto` must NOT shell out to `aw set approved --by-human`.
  THE PRECEDENT ALREADY EXISTS AND MUST BE REUSED, NOT REINVENTED (verified in-tree): `auto-approved`
  is a shipped sibling status in `ipd_schema.READY_TO_EXECUTE` (`ipd_schema.py:250`), documented at
  `:248` as recording "an automated clear, NOT human" approval, and `:337` enforces that
  `auto-approved` does NOT carry the human `Approval:` field. `.aw/records/plans/README.md` states the
  same and adds that it is "used for low-complexity mechanical correctives (D65)" and must be "set only
  by an automated checker, never by an executor fast-tracking its own work". So the honest transition
  for `--full-auto` is `reviewed -> auto-approved`, which is already legal
  (`ipd_schema.py:540` lists it in the status vocabulary) and already means exactly this. Do NOT invent
  a parallel `--by-full-auto` flag if reusing `auto-approved` plus its automated-actor provenance
  suffices; check that first and record which you did.
  BROADER REQUIREMENT THE MAINTAINER ADDED, and it is larger than this plan: the eventual goal is a
  CONFIGURABLE, ARGUMENT-OVERRIDABLE policy for how far automation may advance an artifact along the
  WHOLE pipeline - `backlog -> backlog-review -> graduate to IPD -> to-review -> reviewed -> approved ->
  executed` - where the configuration decides, per transition, what conditions still permit moving
  forward. The worked example given: is it acceptable to advance with an unanswered open question that
  the "try harder before refusing" rule (D148) could not resolve into a strong recommendation? Other
  such conditions belong in the same policy rather than being hardcoded per verb.
  SCOPE RULING FOR THIS PLAN: implement only the honest attestation (no false `--by-human`). Do NOT
  build the general policy engine here; it spans every lifecycle verb and deserves its own spec. Filed
  as backlog `rxya25` (lifecycle-automation-policy) so the requirement is not lost, and note in this plan's history that
  `--full-auto` is the first consumer of a policy that does not exist yet, so its behavior is
  hardcoded-but-honest until that lands.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest tests/test_ipd_schema.py -q` output showing new cases pass: a plan with `- Readiness: go-pending-approval` is conforming; a plan with NO `Readiness:` is conforming (proving optional, no IPD-M103 and no required-field failure); a plan with `- Readiness: bogus` is reported invalid with its rule id. Plus pasted `grep -n "META_READINESS\|READINESS_VALUES" agent_workflows/ipd_schema.py` showing the constant and the closed enum, and that `META_READINESS` appears in `META_RECOGNIZED` but NOT in `META_REQUIRED`.
  - Observed evidence: PASS. 65 tests green; the three schema cases proven through `ipd_lint.check_metadata` (recognized value clean, absent clean, `bogus` -> IPD-M104); `META_READINESS` in `META_RECOGNIZED`, not in `META_REQUIRED`. Detail:
    - `python3 -m pytest tests/test_ipd_schema.py tests/test_plan_readiness.py::SchemaFieldTests -o addopts="" -p no:randomly` (a bare `-q` would compound with the configured one into `-qq` and suppress the summary line; `-o addopts=""` is the sanctioned way to get per-test counts):
```
tests/test_ipd_schema.py ............................................... [ 72%]
............                                                             [ 90%]
tests/test_plan_readiness.py ......                                      [100%]

============================== 65 passed in 0.47s ==============================
```
    - The three required schema cases, exercised against a REAL plan body (this plan) through `ipd_lint.check_metadata`, which is the surface that reports IPD-M103/IPD-M104:
```
Readiness: go-pending-approval -> CONFORMING (no metadata diagnostics)
Readiness: bogus             -> ['IPD-M104: Readiness: unrecognized readiness value (expected one of go, go-pending-approval, no-go)']
ABSENT                       -> CONFORMING (no metadata diagnostics)
```
      So: the recognized value lints clean (no IPD-M103 unknown-field), an ABSENT field lints clean (proving OPTIONAL: no required-field failure), and `bogus` is reported invalid WITH its rule id.
    - RECORDED DEVIATION on WHERE the enum check lives. The plan pointed at the `Priority`/`Work-Kind` precedent, where the schema only RECOGNIZES the field and `aw check` validates the value. Here the value check sits in `ipd_schema.validate_metadata` instead, and the distinguishing reason is vocabulary OWNERSHIP: `backlog.PRIORITIES`/`backlog.KINDS` are owned by ANOTHER module, so their checks live where that shared vocab is imported (which is what stops a fork), whereas `READINESS_VALUES` is defined in `ipd_schema` itself, exactly like the `Kind` and `Status` enums already validated a few lines above it. This also keeps the change inside the declared Scope-Paths fence (no `check_engine.py` edit was needed). Fail-closed behavior does not depend on this diagnostic either way: an unrecognized value is already refused by `read_readiness` -> `is_plan_review_approved`. No existing plan carries `Readiness:`, so the corpus cannot be mass-failed by it (verified: `grep -rn "^- Readiness:" .aw/records/plans/` returned nothing before this change).
    - `grep -n "META_READINESS\|READINESS_VALUES" agent_workflows/ipd_schema.py`:
```
232:META_READINESS = "Readiness"
234:READINESS_VALUES: FrozenSet[str] = frozenset(("go", "go-pending-approval", "no-go"))
254:        META_READINESS,
314:    Returns one of ``READINESS_VALUES`` for a recognized value, and None when the field is ABSENT or
329:    return value if value in READINESS_VALUES else None
365:    readiness = fields.get(META_READINESS)
366:    if readiness is not None and readiness.strip().lower() not in READINESS_VALUES:
```
      Line 254 is inside the `META_RECOGNIZED` frozenset construction; `META_REQUIRED` (line 129) is unchanged and does NOT contain it. Asserted mechanically as well, in `test_readiness_is_recognized_but_not_required` (`assertIn(S.META_READINESS, S.META_RECOGNIZED)` plus `assertNotIn(S.META_READINESS, S.META_REQUIRED)`), so a future edit that made it required would fail the suite rather than pass a text search. The reader returning None for absent/unparseable is covered by `test_reader_returns_none_for_absent_and_for_unparseable`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted output of the new predicate truth-table test (name the file, e.g. `tests/test_plan_readiness.py`) covering EVERY row: `go-pending-approval`->True, `go`->True, `no-go`->False, absent+`APPROVE WITH REVISIONS APPLIED`+no blocking OQ->True, absent+`APPROVE`->True, absent+`REVIEWED - OPEN QUESTIONS`->False, absent+approving-verdict-but-unresolved-blocking-OQ->False, absent+UNPARSEABLE OQ block->False, and a history record containing `NO-GO`->False. MUST include the ADVERSARIAL row: a plan whose history line contains the old `GO - PENDING HUMAN APPROVAL` prose but carries `- Readiness: no-go` returns False (structured field beats prose). MUST ALSO include the REAL-PLAN rows (not only synthetic fixtures): run the predicate against `g7hljt` (carries the old prose phrase; today returns False because of the extractor bug) and against a current `reviewed` repo plan, and assert the intended outcomes - this is the check that catches a fix that works on fixtures but not on real plans. Paste the pass summary line.
  - Observed evidence: PASS. 19 tests green in `tests/test_plan_readiness.py`, covering every required truth-table row plus the adversarial row and the real-plan rows. One deviation, recorded below, TIGHTENS the gate. Detail:
    - File: `tests/test_plan_readiness.py`. `python3 -m pytest tests/test_plan_readiness.py::PredicateTruthTableTests tests/test_plan_readiness.py::RealPlanIntegrationTests tests/test_plan_readiness.py::NoWideningTests -o addopts="" -p no:randomly -v`:
```
tests/test_plan_readiness.py::PredicateTruthTableTests::test_absent_field_with_approve_with_revisions_applied_is_approvable PASSED [  5%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_absent_field_with_approving_verdict_and_resolved_blocking_oq_is_approvable PASSED [ 10%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_absent_field_with_approving_verdict_but_blocking_open_question_is_refused PASSED [ 15%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_absent_field_with_open_questions_verdict_is_refused PASSED [ 21%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_absent_field_with_plain_approve_is_approvable PASSED [ 26%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_absent_field_with_unparseable_open_question_fails_closed PASSED [ 31%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_adversarial_structured_field_beats_old_prose PASSED [ 36%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_go_is_approvable PASSED [ 42%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_go_pending_approval_is_approvable PASSED [ 47%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_history_record_naming_conditional_go_is_refused PASSED [ 52%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_history_record_naming_no_go_is_refused_even_with_a_verdict_word PASSED [ 57%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_missing_history_and_missing_field_fails_closed PASSED [ 63%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_no_go_is_refused PASSED [ 68%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_structured_go_wins_over_a_negative_prose_record PASSED [ 73%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_unreadable_path_fails_closed PASSED [ 78%]
tests/test_plan_readiness.py::PredicateTruthTableTests::test_unrecognized_readiness_value_fails_closed PASSED [ 84%]
tests/test_plan_readiness.py::RealPlanIntegrationTests::test_g7hljt_carries_the_old_prose_and_is_now_read_correctly PASSED [ 89%]
tests/test_plan_readiness.py::RealPlanIntegrationTests::test_predicate_over_every_pending_plan_never_raises_and_respects_no_go PASSED [ 94%]
tests/test_plan_readiness.py::NoWideningTests::test_predicate_does_not_read_status PASSED [100%]

============================== 19 passed in 0.15s ==============================
```
    - ROW-BY-ROW against the required table, each row a named test above: `go-pending-approval` -> True; `go` -> True; `no-go` -> False; absent + `APPROVE WITH REVISIONS APPLIED` + no blocking OQ -> True; absent + `APPROVE` -> True; absent + `REVIEWED - OPEN QUESTIONS` -> False; absent + approving verdict but UNRESOLVED BLOCKING OQ -> False; absent + UNPARSEABLE OQ block -> False; a history record containing `NO-GO` -> False even though a verdict word is present; and its `CONDITIONAL-GO` sibling -> False.
    - ADVERSARIAL row present, and it is the plan's whole point: `test_adversarial_structured_field_beats_old_prose` builds a plan whose history line carries the OLD `Readiness: GO - PENDING HUMAN APPROVAL` prose while its front matter carries `- Readiness: no-go`, and asserts False. Its mirror `test_structured_go_wins_over_a_negative_prose_record` proves the field also wins in the permissive direction, so the field is genuinely authoritative rather than merely an extra veto.
    - REAL-PLAN rows (not fixtures): `test_g7hljt_carries_the_old_prose_and_is_now_read_correctly` runs against the actual in-tree `g7hljt` and asserts the extractor now returns a genuine `HISTORY_RECORD_RE` record and NOT the `- Lifecycle move: ...` bullet it returned pre-fix; it also asserts the old `GO - PENDING HUMAN APPROVAL` prose IS present in that file, which is the evidence that the phrase was never the operative cause. `test_predicate_over_every_pending_plan_never_raises_and_respects_no_go` runs the finished predicate over EVERY plan in `.aw/records/plans/pending/` (35 files, including the current `reviewed`/`approved` corpus), asserting it never raises and never clears a `no-go`.
    - MECHANICAL blocking-OQ definition, not a prose judgement: `has_unresolved_blocking_question` applies the same test the shipped pre-execution gate uses (`ipd_lint.check_checkpoint`: an `### OQ-*` block with `- Blocking: yes` and `- Status:` not `resolved`) and treats an UNPARSEABLE block as blocking. The negative control `test_absent_field_with_approving_verdict_and_resolved_blocking_oq_is_approvable` proves the check is not vacuously always-blocking, which is what would have made the other two rows meaningless.
    - ONE DEVIATION FROM THE PLAN AS WRITTEN, and it TIGHTENS the gate. The plan said to fall back to prose "when the field is ABSENT", which would treat an out-of-vocab value as absence. Implemented instead as a THIRD case that refuses OUTRIGHT with no fallback: a corrupt value means the review DID try to record a readiness and we cannot tell what it meant, so falling back to prose could clear a plan whose author meant `no-go`. Execution-contract rule 6 ("absent or unrecognized `Readiness` ... must never auto-approve") requires this reading. It was caught by writing the test first: `test_unrecognized_readiness_value_fails_closed` FAILED against the first implementation (`AssertionError: True is not false`) and drove the fix, rather than being noticed afterwards.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted `grep -c "def is_plan_review_approved\|def extract_last_history_entry" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing `0` for BOTH files (local duplicates deleted; baseline is 1 each, at oc :215/:229 and agy :391/:404), plus a grep showing both import from `plan_readiness`. Plus pasted `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q` output with an auto-approve test present and passing for EACH driver (name the two test functions), proving the fix is not oc-only. ALSO include the END-TO-END chain: a plan with `Status: reviewed` and `- Readiness: go-pending-approval` processed under `--full-auto` transitions `reviewed -> approved -> queued(execute)`, asserting the `ipd-auto-approved` event is appended to the run's `events.jsonl`; and paste a full default-suite run `python3 -m pytest -p no:randomly` summary line showing green.
  - Observed evidence: PASS. Local duplicates deleted (grep 0/0) and object identity asserted for both drivers; per-driver auto-approve tests green (205 passed); end-to-end chain asserts the `ipd-auto-approved` event and the HONEST `auto-approved` transition. Full-suite numbers and the zero-regression differential are reported honestly below. Detail:
    - `grep -c "def is_plan_review_approved\|def extract_last_history_entry" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` (baseline was 1 each):
```
agent_workflows/oc_runipd.py:0
agent_workflows/agy_runipd.py:0
```
    - Both drivers import the shared module (`grep -n "from agent_workflows.plan_readiness import" -A 3`):
```
agent_workflows/oc_runipd.py:60:from agent_workflows.plan_readiness import (
agent_workflows/oc_runipd.py-61-    extract_newest_history_entry,
agent_workflows/oc_runipd.py-62-    is_plan_review_approved,
agent_workflows/oc_runipd.py-63-)
--
agent_workflows/agy_runipd.py:60:from agent_workflows.plan_readiness import (
agent_workflows/agy_runipd.py-61-    extract_newest_history_entry as extract_newest_history_entry,
agent_workflows/agy_runipd.py-62-)
agent_workflows/agy_runipd.py:63:from agent_workflows.plan_readiness import is_plan_review_approved
```
      Stronger than a grep, and deliberately so: `test_is_plan_review_approved_is_the_shared_predicate_not_a_local_copy` asserts OBJECT IDENTITY (`assertIs`) for BOTH drivers against `plan_readiness.is_plan_review_approved`, and asserts `extract_last_history_entry` no longer exists on either module. A future re-added local copy therefore FAILS the suite instead of quietly passing a text search. `oc_runipd.__all__` re-exports both names so any external caller that imported them from the driver keeps working.
    - PER-DRIVER auto-approve tests, because the bug existed in BOTH and a fix proven only on oc would leave `aw agy run --full-auto` dead. oc: `AllSelectorAndFullAutoTests.test_structured_readiness_field_decides_auto_approval` and `AllSelectorAndFullAutoTests.test_set_plan_approved_uses_auto_approved_and_never_by_human`. agy: `AgyFullAutoApprovalTests.test_structured_readiness_decides_and_prose_does_not` and `AgyFullAutoApprovalTests.test_set_plan_approved_uses_auto_approved_and_never_by_human`. `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_ipd_schema.py tests/test_plan_readiness.py -o addopts="" -p no:randomly`:
```
tests/test_agy_runipd_cli.py ....................                        [ 55%]
tests/test_ipd_schema.py ............................................... [ 78%]
............                                                             [ 83%]
tests/test_plan_readiness.py .................................           [100%]

============================= 205 passed in 17.47s =============================
```
    - END-TO-END chain, in `test_full_auto_reviews_approves_and_executes_plan` (a real subprocess `start --full-auto` against a fake opencode): the plan moves `to-review` -> reviewed by the turn (whose fake reviewer now writes `- Readiness: go-pending-approval` and PREPENDS its history record, matching what E-04 instructs and what `aw set` actually does) -> cleared -> `queued(execute)` -> `executed`, with `attempts[0].action == "review"` and `attempts[1].action == "execute"`. The test asserts `ipd-auto-approved` appears in the run's `events.jsonl`, that `item["auto_approved"]` is set, and - per OQ-02 - that the resulting plan text contains `auto-approved` and does NOT contain `--by-human`.
    - HONEST-ATTESTATION deviation from the V-item's literal `reviewed -> approved` wording, required by OQ-02's maintainer resolution: the transition is `reviewed -> auto-approved`. `auto-approved` is the SHIPPED sibling ready-to-execute tier (`ipd_schema.py:250`, documented at `:248` as recording an automated clear NOT human approval, and forbidden from carrying the human `Approval:` field at `:337`), and `ipd_lifecycle._PLAN_STATUS_RANKS` already ranks it 3 alongside `approved`, so execution routing is unchanged and `reviewed -> auto-approved` is already a legal forward step. Checked first and recorded as OQ-02 instructed: reusing `auto-approved` plus an automated-actor provenance string SUFFICED, so NO `--by-full-auto` flag was invented. The general configurable per-transition automation policy the maintainer also described is deliberately NOT built here (it spans every lifecycle verb; tracked as backlog `rxya25`); `--full-auto` is its first consumer and stays hardcoded-but-honest until that lands.
    - FULL-SUITE run, reported honestly rather than as a bare green line. Bare `python3 -m pytest` in this lane reports `32 failed, 4011 passed, 3 skipped, 4 xfailed in 35.13s`. NONE of those failures are caused by this change, proven by a stash-and-rerun differential (same command, change stashed vs applied), which found ZERO tests failing only WITH the change:
```
=== REGRESSIONS (only after) ===
=== counts (before / after) ===
54
32
```
      The before-count is HIGHER only because the 22 new `test_plan_readiness.py` tests cannot exist while the change is stashed. The 32 are environmental to running INSIDE a driver-managed lane: the driver exports `AW_EXECUTION_ROLE=worker`, which the lifecycle-role guard refuses (`test_driver_own_process_is_not_worker_role` literally asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"`, failing with `AssertionError: 'worker' == 'worker'`), and `tests/test_run_viewer.py` requires run directories under the cwd. Re-run with the lane marker cleared, `env -u AW_EXECUTION_ROLE -u AW_PIN_KEEP_ROOT python3 -m pytest` gives `15 failed, 4028 passed, 3 skipped, 4 xfailed in 34.08s`, and all 15 are the pre-existing `tests/test_run_viewer.py` set (e.g. `test_discover_run_dirs` fails at `assertTrue(len(runs) > 0)` because the lane has no run dirs). The same differential over the cleaned environment again shows zero regressions. Claiming an unqualified green would have been false, so the actual numbers plus the differential are recorded instead.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `grep -n "Readiness" .aw/system/workflows/plan-review/plan-review.md` showing the finalize step instructs writing `- Readiness: <go|go-pending-approval|no-go>` into the plan front matter, together with the stated mapping from the workflow's readiness vocabulary and an explicit statement that the history-line prose is NOT the machine signal.
  - Observed evidence: PASS. `plan-review.md` Step 4 now instructs writing the field, with the mapping table and the explicit statement that history-line prose is NOT the machine signal. Detail:
    - `grep -n "Readiness" .aw/system/workflows/plan-review/plan-review.md`:
```
377:### Write the structured `Readiness` field (REQUIRED output of the review)
383:- Readiness: <go | go-pending-approval | no-go>
388:| Readiness you report | Field value |
521:Verdict describes review outcome. Readiness is separate.
531:Readiness (human approval is a SEPARATE step from the review verdict; a reviewed,
```
      The new subsection sits INSIDE Step 4 (Finalize state and commit), between the `Status: reviewed` instruction and the `## Workflow history` template, so it is on the path a reviewer actually walks rather than in an appendix. Lines 521/531 are the PRE-EXISTING readiness vocabulary, unchanged, per the plan's out-of-scope note that the rubric and verdict vocabulary are not touched.
    - The mapping is stated as a table, exactly as the plan requires: `GO` -> `go`, `GO - PENDING HUMAN APPROVAL` -> `go-pending-approval`, `NO-GO` -> `no-go`.
    - The prose disclaimer is explicit and capitalized in the body: "THE HISTORY-LINE PROSE IS NOT THE MACHINE SIGNAL. Automation reads this field and only this field; whatever readiness wording appears in the history line is for humans." It also states the CONSEQUENCE of omission ("a consumer that finds no field FAILS CLOSED and treats the plan as not cleared"), so a reviewer cannot read the field as optional-and-neutral and silently strand a clean plan.
    - Also added there, carrying E-07's corrected contract into the workflow a reviewer reads: a note that the history section is NEWEST-FIRST (a new record goes directly under the heading), so the workflow's own "Append or update" template cannot be misread as licensing a bottom-append.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted `grep -n "Readiness" .aw/system/workflows/plan-review-long/plan-review-long.md` showing the identical instruction, plus a short diff/comparison of the two files' readiness instructions demonstrating no semantic divergence (parity is documented in `.aw/system/workflows/index.md`).
  - Observed evidence: PASS. Parity holds: the two readiness instructions differ in exactly one line, and only in each file's internal cross-reference. Detail:
    - `grep -n "Readiness" .aw/system/workflows/plan-review-long/plan-review-long.md`:
```
90:- the structured `- Readiness: <go | go-pending-approval | no-go>` front-matter field is written
```
      NOTE ON PLACEMENT, which the V-item's literal wording did not anticipate: the long variant is a MEMORY-KERNEL ORCHESTRATOR that deliberately loads one step file at a time ("Do not load all step files at once"), so putting the operative finalize instruction in the orchestrator would contradict its own design. The instruction therefore lives in the step file the orchestrator names for finalize, and the orchestrator's Completion checklist carries the REQUIREMENT (line 90) so the run cannot be called complete without it. Both files were edited. `grep -n "Readiness" .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`:
```
140:### Write the structured `Readiness` field (REQUIRED output of the review)
146:- Readiness: <go | go-pending-approval | no-go>
151:| Readiness you report | Field value |
196:Readiness (human approval is a SEPARATE step from the review verdict; a reviewed,
```
      Line 196 is the pre-existing readiness vocabulary (Section 4), unchanged.
    - PARITY, demonstrated by diffing the two readiness instructions directly, `diff <(sed -n '377,398p' .aw/system/workflows/plan-review/plan-review.md) <(sed -n '140,161p' .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md)`:
```
10c10
< Map it from the readiness vocabulary you already use below:
---
> Map it from the readiness vocabulary in Section 4:
```
      Exactly ONE line differs, and only in the internal cross-reference each file needs (the single-file variant states its vocabulary further down the same file; the long variant's lives in its Section 4). The field name, the three enum values, the mapping table, and the "THE HISTORY-LINE PROSE IS NOT THE MACHINE SIGNAL" rule are byte-identical, so there is no semantic divergence and the deliberate parity documented in `.aw/system/workflows/index.md` is preserved.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: THE FAILING-FIRST PROOF, pasted in both directions: (a) the new extractor test run against the PRE-FIX code showing it FAILS (paste the failure, naming the test), and (b) the same test passing after. Plus a pasted loop over every `.aw/records/plans/pending/*.ipd.md` asserting the returned entry matches `HISTORY_RECORD_RE` for ALL of them (baseline measured in review: 0 of 20 matched, returning `- Cohesion rationale: ...` and similar). Plus the newest-first assertion on a plan whose history is `approved` newest / `draft` oldest (e.g. wtiso-02), showing the `approved` record is returned, not the `draft` one. Plus evidence the shared primitives were REUSED, not re-implemented: a grep showing the import of `_history_section_lines`/`HISTORY_RECORD_RE` (or their relocated equivalents) rather than a fourth hand-rolled parser.
  - Observed evidence: PASS. Failing-first proven in both directions (8 of 10 FAIL pre-fix, 8 of 8 pass post-fix); 35/35 pending plans now yield a real history record (0/35 before); newest-first confirmed on wtiso-02; shared primitives reused, not re-implemented. Detail:
    - (a) THE FAILING-FIRST PROOF. The new `ExtractorTests` were run against the PRE-FIX algorithm, reproduced verbatim from the shipped `oc_runipd.extract_last_history_entry` (`text[text.rfind("## Workflow history"):]` then `bullets[-1]`), with ONLY the read function swapped and the test bodies untouched. 8 of 10 FAIL:
```
FAIL: test_newest_first_selection
AssertionError: 'approved' not found in '- 2026-08-28 draft (opencode/test): created.'

FAIL: test_returns_newest_bounded_history_record_not_a_later_section_bullet
AssertionError: Regex didn't match: '^- \d{4}-\d{2}-\d{2} ' not found in '- Cohesion rationale: one concern (a trailing bullet in the FINAL section, which the broken'

FAIL: test_section_is_bounded_at_the_next_h2
AssertionError: '- 2099-12-31 a bullet that even LOOKS like a record' != '- 2026-08-29 reviewed (aw set): status set to reviewed'

FAIL: test_every_pending_plan_yields_a_real_history_record
AssertionError: ... : 35/35 plans misread
  ('20260828-wtiso-00-bl9q3d-...ipd.md', '- Cohesion rationale: one architecture (adopt x03wgn); children are strictly-ordered phases ...')

FAIL: test_g7hljt_carries_the_old_prose_and_is_now_read_correctly
AssertionError: unexpectedly None      # HISTORY_RECORD_RE did not match the returned bullet

Ran 10 tests in 0.039s
FAILED (failures=8)
PRE-FIX RESULT: failures=8 errors=0 run=10
```
      The two defects are separately visible, which matters because fixing only one would leave the gate broken: `test_section_is_bounded_at_the_next_h2` fails on the UNBOUNDED slice (it returned a LATER section's bullet), and `test_newest_first_selection` fails on LAST-vs-FIRST (it returned the `draft` record instead of the `approved` one). The 2 tests that pass pre-fix do so by design: one is the characterization test that ASSERTS the old behavior, the other an absent-history case where both algorithms coincide.
    - (b) THE SAME TESTS PASSING AFTER, `python3 -m pytest tests/test_plan_readiness.py::ExtractorTests -o addopts="" -p no:randomly -v`:
```
tests/test_plan_readiness.py::ExtractorTests::test_absent_history_section_returns_none PASSED [ 12%]
tests/test_plan_readiness.py::ExtractorTests::test_characterizes_the_old_broken_behavior PASSED [ 25%]
tests/test_plan_readiness.py::ExtractorTests::test_empty_history_section_returns_none PASSED [ 37%]
tests/test_plan_readiness.py::ExtractorTests::test_every_pending_plan_yields_a_real_history_record PASSED [ 50%]
tests/test_plan_readiness.py::ExtractorTests::test_newest_first_selection PASSED [ 62%]
tests/test_plan_readiness.py::ExtractorTests::test_non_record_bullets_inside_history_are_skipped PASSED [ 75%]
tests/test_plan_readiness.py::ExtractorTests::test_returns_newest_bounded_history_record_not_a_later_section_bullet PASSED [ 87%]
tests/test_plan_readiness.py::ExtractorTests::test_section_is_bounded_at_the_next_h2 PASSED [100%]

============================== 8 passed in 0.10s ===============================
```
    - THE PENDING-CORPUS SWEEP, measured directly against the SHIPPED code before the fix (the plan's review measured 0 of 20; the tree now holds 35 plans):
```
NON-RECORD: 20260828-wtiso-00-bl9q3d-worktree-isolation- -> - Cohesion rationale: one architecture (adopt x03wgn); children are st
NON-RECORD: 20260829-fullauto-01-97df1z-structured-readi -> - Cohesion rationale: one concern (make the auto-approve decision corr
NON-RECORD: 20260829-rununify-00-5e4sb6-unify-the-two-ho -> - Density advisories (`IPD-Z602`) fire on E-02 and E-03 at the review-
NON-RECORD: 20260901-wslayout-05-30jug9-add-aw-layout-cl -> - Cohesion rationale: not required
matched=0 non_record=35 total=35
```
      (4 representative offender lines of the 35 the run printed.) The post-fix state is not a one-off measurement but a standing assertion: `test_every_pending_plan_yields_a_real_history_record` loops EVERY `.aw/records/plans/pending/*.ipd.md` and requires `HISTORY_RECORD_RE` to match for all of them, so 35 of 35 now match and any regression re-breaks the suite.
    - NEWEST-FIRST on the exact plan the V-item names (wtiso-02, whose file order is `approved` newest / `draft` oldest):
```
PLAN: 20260828-wtiso-02-qcqhj7-phase-1-stop-the-deadlock-and-silent-loss-in-lane-only-worke.ipd.md
NEWEST RECORD RETURNED: - 2026-08-29 approved (aw set): status set to approved
```
      The `approved` record is returned, not the `draft` one a bounded-but-last reader would have given.
    - SHARED PRIMITIVES REUSED rather than a fourth hand-rolled parser, `grep -n "_history_section_lines\|HISTORY_RECORD_RE" agent_workflows/plan_readiness.py`:
```
56:from agent_workflows.attention import _history_section_lines
57:from agent_workflows.attention_contract import HISTORY_RECORD_RE
109:    for line in _history_section_lines(text):
111:        if HISTORY_RECORD_RE.match(candidate):
```
      The entire reader is those two borrowed primitives plus a first-match loop, so section bounding and the record grammar have exactly one definition each in the repo and a change to either propagates here automatically.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Pasted `grep -n -i "newest\|append" .aw/records/plans/README.md agent_workflows/status_set.py` showing the README history sentence and the `status_set.py` comment now say NEWEST-FIRST rather than "appended"/"Append", plus the shared helper's docstring stating that the FIRST record is the newest and citing `status_set.py:762` (the `insert(i + 1, ...)` prepend) as the reason. Confirm by pasted diff that the WRITER's behavior was NOT changed (docs-only fix).
  - Observed evidence: PASS. README and the `status_set.py` comment now say NEWEST-FIRST (two further stale 'append' claims also found and fixed); the shared helper's docstring records the reason and cites `status_set.py:799`; the diff proves the WRITER is unchanged (docs-only). Detail:
    - `grep -n -i "newest-first" .aw/records/plans/README.md agent_workflows/status_set.py agent_workflows/plan_readiness.py`:
```
.aw/records/plans/README.md:54:(assess, plan-review, ...), so you can see the path a plan took. The section is NEWEST-FIRST: each
.aw/records/plans/README.md:127:   record a `## Workflow history` line, newest-first). The supported way to perform this transition
agent_workflows/status_set.py:520:    Apply the status change on disk, recording workflow history (NEWEST-FIRST: the record is
agent_workflows/status_set.py:786:    # Write the Workflow history record. NEWEST-FIRST, NOT appended: the `insert(i + 1, ...)` below
agent_workflows/plan_readiness.py:11:2. THE HISTORY SECTION IS BOUNDED AND NEWEST-FIRST, and the shipped reader honored neither.
```
      The README's "an appended, dated line per workflow" is gone, replaced by an explicit newest-first statement that also tells a reader to take the FIRST record and bound the section at the next `## ` heading. The `status_set.py` comment that said "Append Workflow history" now says NEWEST-FIRST and explains the `insert(i + 1, ...)` prepend. TWO FURTHER stale "append" claims about history, beyond the two the plan named, were found by the same grep and corrected: the README's terminal-transition step 5 (line 127) and `apply_status_change`'s own docstring (line 520). Correcting them is the whole point of the E-item; a leftover "append" is exactly what would invite a future reader to restore the bug.
    - The shared helper's docstring records the reason and cites the writer:
```
    The FIRST record is the newest: ``aw set`` prepends each new record directly under the heading
    (``status_set.py:799``, ``new_lines.insert(i + 1, hist_entry)``), so the section is newest-first
    despite the word "append" that used to appear in its comment and in the plans README. Do NOT
    "fix" this to return the last record; that is the bug this function replaced.
```
      The citation is `status_set.py:799`, re-verified against the current file (`grep -n "insert(i + 1, hist_entry)"` reports `799`); the plan's `:762`/`:791` were stale snapshots.
    - WRITER UNCHANGED, proven by the complete `git diff agent_workflows/status_set.py`: both hunks are a docstring and a comment, no executable line is touched, and `new_lines.insert(i + 1, hist_entry)` is untouched:
```
@@ -517,7 +517,8 @@ def apply_status_change(
-    (docstring) Apply the status change to the artifact on disk, appending workflow history and moving file if needed.
+    (docstring) Apply the status change on disk, recording workflow history (NEWEST-FIRST: the record is
+    PREPENDED under the `## Workflow history` heading, not appended) and moving the file if needed.
@@ -782,7 +783,14 @@ def apply_status_change(
-    # Append Workflow history
+    # Write the Workflow history record. NEWEST-FIRST, NOT appended: the `insert(i + 1, ...)` below
+    # PREPENDS the new record directly under the `## Workflow history` heading, so the FIRST record
+    # in the section is the most recent one. ...
     hist_entry = f"- {today} {norm_status} ({actor}): {message}"
```
      No existing plan's history was reordered (docs-only fix, as the plan's out-of-scope note requires).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make the auto-approve decision correct, structured, and single-sourced); the E-items are ordered sub-steps of that single fix (fix the extractor -> pin the ordering contract -> add the field -> shared predicate -> driver adoption -> workflow writes it). E-06 leads because it is the actual bug; E-07 is the doc-only guard that stops it regressing.

Execution contract:

1. Open questions: OQ-01 resolved; **OQ-02 is BLOCKING and OPEN** - do NOT execute until the maintainer decides the `--by-human` self-attestation question, because the chosen option changes what `set_plan_approved` may do and what the provenance message must say. Execution additionally requires explicit human approval (`Status: approved`).
2. Scope fence: touch ONLY `agent_workflows/plan_readiness.py` (new), `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/ipd_schema.py`, `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/plan-review-long.md`, `tests/`, and - for E-07's doc-only correction - `.aw/records/plans/README.md` plus the comment at `agent_workflows/status_set.py:756`. Do NOT change the history WRITER's insert behavior, do NOT reorder any existing plan's history, do NOT undertake the broader driver unification (backlog `dhuape`), do NOT change the plan-review rubric or verdict vocabulary, and do NOT backfill the field into existing reviewed plans. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or this orchestrator, and do NOT reimplement a rule another plan owns.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output for the named commands; never claim success you did not run. A V-item whose command was not executed stays `Result: pending`.
4. FAILING-FIRST RULE for E-06 (HARD MUST): the extractor test must be shown FAILING against the pre-fix code before the fix is applied, and passing after. A fix whose test passes both before and after has not demonstrated it fixed anything - and this bug specifically hid behind tests that never exercised a real multi-section plan.
5. REAL-PLAN RULE: validate the finished predicate against actual repo plans, not only synthetic fixtures. The original diagnosis went wrong precisely because the failing behavior only shows up on real plan structure.
6. Fail-closed rule: absent or unrecognized `Readiness`, an unparseable open-question block, or any read error must never auto-approve. If you cannot make a case decide safely, make it return False and record why - never widen the gate to make a test pass.
7. NO WIDENING: this plan makes an existing gate WORK; it must not expand what the gate is allowed to approve. `Status: reviewed` remains a precondition, and `--full-auto` stays opt-in and default-False.
8. Shared checkout: other agents are working in this repo concurrently. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); verify the staged set with `git diff --cached --name-only` first; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
9. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.
