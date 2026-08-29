# IPD: Structured Readiness field replaces prose matching in the --full-auto auto-approve gate (shared predicate, both drivers)

- Date: 2026-08-29
- Kind: child
- Concern: `--full-auto` silently never fires. Its help promises "Automatically approve reviewed plans with 'GO - PENDING HUMAN APPROVAL' verdict and execute them immediately" (oc_runipd.py:2854), but the gate `is_plan_review_approved` (oc_runipd.py:229, near-duplicate at agy_runipd.py:404) can never return True in practice, for THREE INDEPENDENT reasons - and the prose match is only the third. REVIEW CORRECTED THE DIAGNOSIS (PR-001): (1) THE EXTRACTOR IS BROKEN AND IS THE PRIMARY CAUSE. `extract_last_history_entry` (oc_runipd.py:215) slices `text[text.rfind("## Workflow history"):]` to END OF FILE and returns the LAST `- ` bullet in that slice. Because `## Workflow history` sits near the TOP of a plan, that slice spans every later section (measured on this plan: 15,654 chars across 13 headings), so the "last history entry" is actually the last bullet of the FINAL section - typically `- Cohesion rationale: ...` or `- Lifecycle move: ...`. Verified: for 20 of 20 pending plans the returned string is NOT a history line at all. (2) HISTORY IS NEWEST-FIRST, so even a correctly bounded reader must take the FIRST bullet, not the last: `status_set.py:762` does `new_lines.insert(i + 1, hist_entry)`, prepending directly under the heading (its own comment says "Append", which is wrong). Verified on wtiso-02: file order is `approved` -> `/plan-review` -> `reviewed` -> `to-review` -> `draft`, newest first. (3) Only then does the prose problem apply: the documented template (plan-review.md:301) is `- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>`, carrying no readiness term. THE PLAN'S ORIGINAL EVIDENCE WAS MISREAD: plan g7hljt DOES carry `readiness GO - PENDING HUMAN APPROVAL` in its history line, but `is_plan_review_approved(g7hljt)` still returns **False** (verified live), because the extractor never reaches that line. So g7hljt does not show the gate "sometimes fires"; it shows the phrase is irrelevant while the extractor is broken. CONSEQUENCE FOR THE FIX: a structured field alone does NOT fix this bug, and the originally proposed back-compat fallback would have been dead code, because it re-used the same broken extractor.
- Scope: Fix the gate at its real cause, then make it structural. (1) FIX THE EXTRACTOR: bound the `## Workflow history` slice at the next `## ` heading and select the NEWEST (first) record, reusing the repo's existing correct reader rather than writing a fourth one - `attention._history_section_lines` (attention.py:86) already bounds the section correctly and `attention_contract.HISTORY_RECORD_RE` (attention_contract.py:450) already defines the `- YYYY-MM-DD <text>` record grammar. (2) Add an optional, recognized plan front-matter field `- Readiness:` with a closed lowercase-kebab enum `go` | `go-pending-approval` | `no-go` (house convention: bare lowercase enums, cf. `Status:`, `Kind:`, `Priority:`, `Gate-Kind:`); absent = unknown = NOT auto-approvable (fail closed). (3) Extract ONE shared predicate (and the history helper, also duplicated at oc_runipd.py:215 / agy_runipd.py:391) into a single module both drivers import, so the rule cannot drift. (4) The predicate returns True only for `Readiness: go-pending-approval` (or `go`), with a BOUNDED BACK-COMPAT FALLBACK that reads the CORRECTED newest history record: accept verdict `APPROVE` or `APPROVE WITH REVISIONS APPLIED` AND no unresolved blocking open question; never accept `NO-GO`/`CONDITIONAL-GO`. (5) Make `/plan-review` (and its parity twin `plan-review-long`) WRITE the field at its finalize step instead of relying on prose. Preserve the existing safety property: a `NO-GO`/`CONDITIONAL-GO` readiness must never auto-approve. Out of scope: widening what `--full-auto` is ALLOWED to do (see the Deferred note on the `--by-human` attestation), and the broader driver unification.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_schema.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/plan-review-long.md, tests/
- Item-Dependencies: none
- Status: reviewed
- Set: fullauto
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 97df1z

## Workflow history
- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-007. Misdiagnosis corrected: the extractor is the primary bug (rfind-to-EOF, unbounded; 20/20 pending plans return a non-history bullet) and history is newest-first, so the structured field alone would NOT have fixed --full-auto and the back-compat fallback would have been dead code. Added E-06/E-07 + V-06/V-07. OQ-02 opened (blocking): --full-auto self-asserts --by-human.
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `--full-auto` actually work: first FIX THE BROKEN HISTORY EXTRACTOR that makes the gate return False for every plan regardless of wording, then decide auto-approval from a structured `- Readiness:` enum written by `/plan-review`, evaluated by ONE shared predicate imported by both drivers, instead of regex-matching model-authored prose. The structured field is the durable design; the extractor fix is what actually unbreaks the feature.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 0: fix the actual bug (the extractor)

- [ ] E-06 Fix `extract_last_history_entry` so it returns the NEWEST record of the `## Workflow history` SECTION, and prove the current behavior is wrong with a failing-first test. Two defects to fix together (they are one read path): (a) the slice is UNBOUNDED - `text[text.rfind("## Workflow history"):]` runs to EOF and therefore spans every later section (measured: 15,654 chars / 13 headings on this plan), so bound it at the next `## ` heading; (b) it takes the LAST bullet, but history is NEWEST-FIRST (`status_set.py:762` prepends via `new_lines.insert(i + 1, ...)`), so select the FIRST matching record. REUSE the existing correct primitives instead of writing a fourth reader: `attention._history_section_lines` (attention.py:86) for bounding and `attention_contract.HISTORY_RECORD_RE` (attention_contract.py:450, `^- (?P<date>\d{4}-\d{2}-\d{2}) .+$`) for the record grammar - a non-record bullet (e.g. `- Cohesion rationale:`) must never be returned. This E-item is FIRST because the structured field cannot fix the bug by itself and the back-compat fallback is dead code without it.
  - Depends on: none
  - Expected outcome: a test that FAILS on today's code and passes after: for a real plan the helper returns the `- YYYY-MM-DD ...` newest record, not `- Cohesion rationale: ...`; verified across all pending plans that the result always matches `HISTORY_RECORD_RE`.
  - Execution state: pending

- [ ] E-07 Reconcile the newest-first ordering CONTRACT so the fix cannot silently regress. `.aw/records/plans/README.md:44` says history is "an appended, dated line per workflow" and the writer's own comment at `status_set.py:756` says "Append Workflow history", but the code PREPENDS (`insert(i + 1, ...)`), making the section newest-first. Pick the code's actual behavior as the contract (do NOT change the writer - reordering 400 existing plans' history is out of scope and would be a destructive rewrite), and correct the two misleading statements to say NEWEST-FIRST, so a future reader does not "fix" the reader back to last-bullet.
  - Depends on: E-06
  - Expected outcome: README and the code comment state newest-first; a docstring on the shared helper records that the FIRST record is the newest and cites `status_set.py:762` as the reason.
  - Execution state: pending

### Task group 1: the structured field

- [ ] E-01 Add the optional recognized plan field to `agent_workflows/ipd_schema.py`: `META_READINESS = "Readiness"` plus membership in `META_RECOGNIZED` (mirroring `META_SCOPE_PATHS`:152 / `META_BLOCKS_RELEASE`:182 - recognized-but-OPTIONAL, NOT added to `META_REQUIRED`, so an absent field never fails an existing plan), and a closed value enum `READINESS_VALUES = frozenset(("go", "go-pending-approval", "no-go"))` with a reader that returns None for absent/unparseable.
  - Depends on: none
  - Expected outcome: a plan carrying `- Readiness: go-pending-approval` lints clean; a plan with no `Readiness:` lints clean (no IPD-M103 unknown-field, no new required-field failure); a plan with `- Readiness: bogus` is reported as an invalid value.
  - Execution state: pending

### Task group 2: one shared predicate (kill the duplicate)

- [ ] E-02 Create `agent_workflows/plan_readiness.py` holding the SINGLE implementation of the corrected history helper (from E-06) and `is_plan_review_approved(plan_path)`, moved out of the drivers. NOTE the duplicates are NEAR-identical, not byte-identical as first written (PR-005, verified): the agy copies at agy_runipd.py:391/404 have had their DOCSTRINGS stripped relative to oc_runipd.py:215/229, which is exactly the silent drift that makes a shared module the right call. New logic: return True iff the plan's `- Readiness:` is `go-pending-approval` or `go`; return False for `no-go`; and when the field is ABSENT apply the bounded back-compat fallback over the CORRECTED newest history record - accept only if its verdict is `APPROVE` or `APPROVE WITH REVISIONS APPLIED` AND the plan has no unresolved blocking open question AND the record does not contain `NO-GO`/`CONDITIONAL-GO`. Absent field + non-approving verdict = False (fail closed). DEFINE "unresolved blocking open question" MECHANICALLY, not by prose judgement: an `### OQ-*` block whose `- Blocking:` is `yes` and whose `- Status:` is not `resolved` (cite the shape used by this plan's own OQ section); if that cannot be parsed, treat it as blocking (fail closed).
  - Depends on: E-01, E-06
  - Expected outcome: one importable predicate; `go-pending-approval` -> True; `no-go` -> False; absent + `APPROVE WITH REVISIONS APPLIED` + no blocking OQ -> True; absent + `REVIEWED - OPEN QUESTIONS` -> False; absent + blocking OQ -> False; an unparseable OQ block -> False.
  - Execution state: pending

- [ ] E-03 Repoint both drivers at the shared predicate and DELETE their local copies: `oc_runipd.py` (defs at :215/:229; call sites :1274, :2384) and `agy_runipd.py` (defs at :391/:404; call sites :1368, :2455). (Line numbers re-verified in review; the plan's originals were ~14-40 lines stale - PR-006.) Import from `plan_readiness`; keep any existing public re-export so external callers do not break.
  - Depends on: E-02
  - Expected outcome: `grep -c "def is_plan_review_approved" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returns 0 for both; both drivers' auto-approve paths call the shared function; no behavioral difference between oc and agy.
  - Execution state: pending

### Task group 3: the workflow writes the field

- [ ] E-04 Update `.aw/system/workflows/plan-review/plan-review.md` Step 4 (finalize) to WRITE `- Readiness: <go|go-pending-approval|no-go>` into the plan's front matter as a required output of the review, alongside the existing `Status: reviewed` and history line. State explicitly that the history-line prose is NOT the machine signal and that the readiness values map from the workflow's existing readiness vocabulary (GO -> `go`, GO - PENDING HUMAN APPROVAL -> `go-pending-approval`, NO-GO -> `no-go`).
  - Depends on: E-01
  - Expected outcome: the workflow body instructs writing the structured field; a reviewer following it produces a plan whose `- Readiness:` matches its reported readiness.
  - Execution state: pending

- [ ] E-05 Apply the same change to `.aw/system/workflows/plan-review-long/plan-review-long.md`, which index.md documents as kept in "deliberate parity" with the single-file variant, so the two do not diverge.
  - Depends on: E-04
  - Expected outcome: both workflow bodies specify the field identically; a diff of their readiness instructions shows no semantic difference.
  - Execution state: pending

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

- Blocking: yes
- Status: open
- Owner: human (maintainer)
- Resolution or deferral rationale: OPEN - a policy decision the repository cannot answer, and it must be answered BEFORE execution because this plan is what turns the contradiction from latent into live. Facts established in review: `set_plan_approved` (oc_runipd.py:243) shells out to `aw set approved --by-human`, i.e. the MACHINE asserts the human-approval attestation. The attestation spec's stated purpose is the opposite - an "explicit attested speed bump" that "prevents an honest agent from AUTO-advancing a transition the human must own", with attributed provenance (`20260815-0151-01-honest-human-approval-attestation.spec.md`:22, 28-30). Today the contradiction is inert because the gate never fires (verified: False for every plan tested). After this plan it will fire, so `--full-auto` becomes a working path by which an agent records "a human approved this" when no human did. Note the guard rails that remain either way: `--full-auto` is opt-in and defaults to False (oc_runipd.py:2853), it only acts on plans already at `Status: reviewed`, and the readiness field is written by the reviewing agent. The options are (a) ship as-is, treating `--full-auto` as the human's standing, opt-in delegation of approval, and say so in the help text and the recorded provenance message; (b) keep auto-EXECUTE but drop auto-APPROVE, so `--full-auto` runs only plans a human already approved (this narrows the feature and may defeat its purpose); (c) add a distinct non-human attestation (e.g. `--by-full-auto`) so the audit trail never claims human approval, which is the most honest but touches the attestation contract and its spec. The reviewer will not choose: (b) and (c) change a documented safety contract, and (a) is an explicit acceptance of risk. Whichever is chosen, the recorded provenance message MUST make the mechanism visible rather than reading as a human sign-off.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest tests/test_ipd_schema.py -q` output showing new cases pass: a plan with `- Readiness: go-pending-approval` is conforming; a plan with NO `Readiness:` is conforming (proving optional, no IPD-M103 and no required-field failure); a plan with `- Readiness: bogus` is reported invalid with its rule id. Plus pasted `grep -n "META_READINESS\|READINESS_VALUES" agent_workflows/ipd_schema.py` showing the constant and the closed enum, and that `META_READINESS` appears in `META_RECOGNIZED` but NOT in `META_REQUIRED`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted output of the new predicate truth-table test (name the file, e.g. `tests/test_plan_readiness.py`) covering EVERY row: `go-pending-approval`->True, `go`->True, `no-go`->False, absent+`APPROVE WITH REVISIONS APPLIED`+no blocking OQ->True, absent+`APPROVE`->True, absent+`REVIEWED - OPEN QUESTIONS`->False, absent+approving-verdict-but-unresolved-blocking-OQ->False, absent+UNPARSEABLE OQ block->False, and a history record containing `NO-GO`->False. MUST include the ADVERSARIAL row: a plan whose history line contains the old `GO - PENDING HUMAN APPROVAL` prose but carries `- Readiness: no-go` returns False (structured field beats prose). MUST ALSO include the REAL-PLAN rows (not only synthetic fixtures): run the predicate against `g7hljt` (carries the old prose phrase; today returns False because of the extractor bug) and against a current `reviewed` repo plan, and assert the intended outcomes - this is the check that catches a fix that works on fixtures but not on real plans. Paste the pass summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `grep -c "def is_plan_review_approved\|def extract_last_history_entry" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing `0` for BOTH files (local duplicates deleted; baseline is 1 each, at oc :215/:229 and agy :391/:404), plus a grep showing both import from `plan_readiness`. Plus pasted `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q` output with an auto-approve test present and passing for EACH driver (name the two test functions), proving the fix is not oc-only. ALSO include the END-TO-END chain: a plan with `Status: reviewed` and `- Readiness: go-pending-approval` processed under `--full-auto` transitions `reviewed -> approved -> queued(execute)`, asserting the `ipd-auto-approved` event is appended to the run's `events.jsonl`; and paste a full default-suite run `python3 -m pytest -p no:randomly` summary line showing green.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `grep -n "Readiness" .aw/system/workflows/plan-review/plan-review.md` showing the finalize step instructs writing `- Readiness: <go|go-pending-approval|no-go>` into the plan front matter, together with the stated mapping from the workflow's readiness vocabulary and an explicit statement that the history-line prose is NOT the machine signal.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `grep -n "Readiness" .aw/system/workflows/plan-review-long/plan-review-long.md` showing the identical instruction, plus a short diff/comparison of the two files' readiness instructions demonstrating no semantic divergence (parity is documented in `.aw/system/workflows/index.md`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: THE FAILING-FIRST PROOF, pasted in both directions: (a) the new extractor test run against the PRE-FIX code showing it FAILS (paste the failure, naming the test), and (b) the same test passing after. Plus a pasted loop over every `.aw/records/plans/pending/*.ipd.md` asserting the returned entry matches `HISTORY_RECORD_RE` for ALL of them (baseline measured in review: 0 of 20 matched, returning `- Cohesion rationale: ...` and similar). Plus the newest-first assertion on a plan whose history is `approved` newest / `draft` oldest (e.g. wtiso-02), showing the `approved` record is returned, not the `draft` one. Plus evidence the shared primitives were REUSED, not re-implemented: a grep showing the import of `_history_section_lines`/`HISTORY_RECORD_RE` (or their relocated equivalents) rather than a fourth hand-rolled parser.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Pasted `grep -n -i "newest\|append" .aw/records/plans/README.md agent_workflows/status_set.py` showing the README history sentence and the `status_set.py` comment now say NEWEST-FIRST rather than "appended"/"Append", plus the shared helper's docstring stating that the FIRST record is the newest and citing `status_set.py:762` (the `insert(i + 1, ...)` prepend) as the reason. Confirm by pasted diff that the WRITER's behavior was NOT changed (docs-only fix).
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make the auto-approve decision correct, structured, and single-sourced); the E-items are ordered sub-steps of that single fix (fix the extractor -> pin the ordering contract -> add the field -> shared predicate -> driver adoption -> workflow writes it). E-06 leads because it is the actual bug; E-07 is the doc-only guard that stops it regressing.

Execution contract:

1. Open questions: OQ-01 resolved; **OQ-02 is BLOCKING and OPEN** - do NOT execute until the maintainer decides the `--by-human` self-attestation question, because the chosen option changes what `set_plan_approved` may do and what the provenance message must say. Execution additionally requires explicit human approval (`Status: approved`).
2. Scope fence: touch ONLY `agent_workflows/plan_readiness.py` (new), `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/ipd_schema.py`, `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/plan-review-long.md`, `tests/`, and - for E-07's doc-only correction - `.aw/records/plans/README.md` plus the comment at `agent_workflows/status_set.py:756`. Do NOT change the history WRITER's insert behavior, do NOT reorder any existing plan's history, do NOT undertake the broader driver unification (backlog `dhuape`), do NOT change the plan-review rubric or verdict vocabulary, and do NOT backfill the field into existing reviewed plans. If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output for the named commands; never claim success you did not run. A V-item whose command was not executed stays `Result: pending`.
4. FAILING-FIRST RULE for E-06 (HARD MUST): the extractor test must be shown FAILING against the pre-fix code before the fix is applied, and passing after. A fix whose test passes both before and after has not demonstrated it fixed anything - and this bug specifically hid behind tests that never exercised a real multi-section plan.
5. REAL-PLAN RULE: validate the finished predicate against actual repo plans, not only synthetic fixtures. The original diagnosis went wrong precisely because the failing behavior only shows up on real plan structure.
6. Fail-closed rule: absent or unrecognized `Readiness`, an unparseable open-question block, or any read error must never auto-approve. If you cannot make a case decide safely, make it return False and record why - never widen the gate to make a test pass.
7. NO WIDENING: this plan makes an existing gate WORK; it must not expand what the gate is allowed to approve. `Status: reviewed` remains a precondition, and `--full-auto` stays opt-in and default-False.
8. Shared checkout: other agents are working in this repo concurrently. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); verify the staged set with `git diff --cached --name-only` first; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
9. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.
