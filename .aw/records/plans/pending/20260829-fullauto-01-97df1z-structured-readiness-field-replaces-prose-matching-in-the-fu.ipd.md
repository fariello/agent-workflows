# IPD: Structured Readiness field replaces prose matching in the --full-auto auto-approve gate (shared predicate, both drivers)

- Date: 2026-08-29
- Kind: child
- Concern: `--full-auto` silently never fires. Its help promises "Automatically approve reviewed plans with 'GO - PENDING HUMAN APPROVAL' verdict and execute them immediately", but the gate `is_plan_review_approved` (oc_runipd.py:227, byte-identical copy at agy_runipd.py:402) decides by REGEX-MATCHING MODEL-AUTHORED PROSE in the plan's last `## Workflow history` line: `re.search(r"GO\s*-\s*PENDING\s*HUMAN\s*APPROVAL", last_entry)`. The plan-review workflow's documented history template (plan-review.md:300 region) is `- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>` - the VERDICT only, with no readiness term. OBSERVED 2026-08-29: a run of `aw oc run jolfpj wtiso --full-auto --no-isolate-worktree` reviewed all 8 wtiso plans to `Status: reviewed` with verdict `APPROVE WITH REVISIONS APPLIED`, and 0 of 8 auto-approved because none of the 8 history lines contained the readiness phrase (verified: `grep -ciE "GO *- *PENDING *HUMAN *APPROVAL"` on each last entry -> 0). The same workflow DID emit `readiness GO - PENDING HUMAN APPROVAL` for plan g7hljt earlier the same day, so the phrase's presence is non-deterministic prose. A machine gate keyed on free prose cannot be relied on.
- Scope: Replace the prose match with a STRUCTURED field. (1) Add an optional, recognized plan front-matter field `- Readiness:` with a closed lowercase-kebab enum `go` | `go-pending-approval` | `no-go` (house convention: bare lowercase enums, cf. `Status:`, `Kind:`, `Priority:`, `Gate-Kind:`); absent = unknown = NOT auto-approvable (fail closed). (2) Extract ONE shared predicate (and the `extract_last_history_entry` helper it uses, also duplicated at oc_runipd.py:213 / agy_runipd.py:389) into a single module both drivers import, so the rule cannot drift - the drivers currently carry byte-identical copies. (3) The predicate returns True only for `Readiness: go-pending-approval` (or `go`), with a BOUNDED BACK-COMPAT FALLBACK for plans reviewed before this change: accept verdict `APPROVE` or `APPROVE WITH REVISIONS APPLIED` in the last history entry AND no unresolved blocking open question; the fallback never accepts `NO-GO`/`CONDITIONAL-GO`. (4) Make `/plan-review` (and its parity twin `plan-review-long`) WRITE the field at its finalize step instead of relying on prose. Preserve the existing safety property: a `NO-GO`/`CONDITIONAL-GO` readiness must never auto-approve.
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_schema.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/plan-review-long.md, tests/
- Item-Dependencies: none
- Status: to-review
- Set: fullauto
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 97df1z

## Workflow history
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `--full-auto` actually work by deciding auto-approval from a structured `- Readiness:` enum written by `/plan-review`, evaluated by ONE shared predicate imported by both drivers, instead of regex-matching model-authored prose in a history line.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the structured field

- [ ] E-01 Add the optional recognized plan field to `agent_workflows/ipd_schema.py`: `META_READINESS = "Readiness"` plus membership in `META_RECOGNIZED` (mirroring `META_SCOPE_PATHS`:152 / `META_BLOCKS_RELEASE`:182 - recognized-but-OPTIONAL, NOT added to `META_REQUIRED`, so an absent field never fails an existing plan), and a closed value enum `READINESS_VALUES = frozenset(("go", "go-pending-approval", "no-go"))` with a reader that returns None for absent/unparseable.
  - Depends on: none
  - Expected outcome: a plan carrying `- Readiness: go-pending-approval` lints clean; a plan with no `Readiness:` lints clean (no IPD-M103 unknown-field, no new required-field failure); a plan with `- Readiness: bogus` is reported as an invalid value.
  - Execution state: pending

### Task group 2: one shared predicate (kill the duplicate)

- [ ] E-02 Create `agent_workflows/plan_readiness.py` holding the SINGLE implementation of `extract_last_history_entry(text)` and `is_plan_review_approved(plan_path)`, moved out of the drivers (currently byte-identical duplicates: `extract_last_history_entry` at oc_runipd.py:213 and agy_runipd.py:389; `is_plan_review_approved` at oc_runipd.py:227 and agy_runipd.py:402). New logic: return True iff the plan's `- Readiness:` is `go-pending-approval` or `go`; return False for `no-go`; and when the field is ABSENT apply the bounded back-compat fallback - accept only if the last history entry's verdict is `APPROVE` or `APPROVE WITH REVISIONS APPLIED` AND the plan has no unresolved blocking open question AND the entry does not contain `NO-GO`/`CONDITIONAL-GO`. Absent field + non-approving verdict = False (fail closed).
  - Depends on: E-01
  - Expected outcome: one importable predicate; `go-pending-approval` -> True; `no-go` -> False; absent + `APPROVE WITH REVISIONS APPLIED` + no blocking OQ -> True; absent + `REVIEWED - OPEN QUESTIONS` -> False; absent + blocking OQ -> False.
  - Execution state: pending

- [ ] E-03 Repoint both drivers at the shared predicate and DELETE their local copies: `oc_runipd.py` (defs at :213/:227; call sites :1256, :2339) and `agy_runipd.py` (defs at :389/:402; call sites :1350, :2415). Import from `plan_readiness`; keep any existing public re-export so external callers do not break.
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
- The two drivers duplicate helpers verbatim rather than sharing them; the `dhuape` backlog item tracks unifying them onto a shared runner library. This plan takes the narrow step of sharing just this predicate rather than waiting for that larger refactor.

## Findings

- ROOT CAUSE: `is_plan_review_approved` gates on prose. `oc_runipd.py:234` is `re.search(r"GO\s*-\s*PENDING\s*HUMAN\s*APPROVAL", last_entry, re.IGNORECASE)` against `extract_last_history_entry(text)`. The plan-review history template emits verdict + finding ids only, so the phrase is absent unless the model volunteers it.
- EVIDENCE OF THE FAILURE: after the 2026-08-29 run, all 8 wtiso plans are `Status: reviewed` with last entries of the form `/plan-review (...): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. ...`; a `grep -ciE "GO *- *PENDING *HUMAN *APPROVAL"` over each last entry returns `0` for all 8. Zero auto-approved, zero executed.
- EVIDENCE THE PROSE IS NON-DETERMINISTIC: plan g7hljt (ocsync), reviewed by the same workflow the same day, DID carry `readiness GO - PENDING HUMAN APPROVAL` in its history line. Same instructions, different output - which is exactly why prose must not be load-bearing.
- The existing negative guard (`Readiness:\s*(NO-GO|CONDITIONAL-GO)` at oc_runipd.py:236) already reads a `Readiness:`-shaped token, so the field name is consistent with what the code half-expects today.
- DUPLICATION: the predicate and its helper exist twice, byte-identical. Fixing only one driver would leave `aw agy run --full-auto` broken; hence the shared-module step.

## Proposed changes (ordered, validatable)

1. `ipd_schema.py`: recognize `Readiness` + define the value enum + reader.
2. `plan_readiness.py`: new shared module with the single predicate + helper and the new field-first / fallback logic.
3. `oc_runipd.py`, `agy_runipd.py`: delete local copies, import the shared predicate.
4. `plan-review.md` and `plan-review-long.md`: write the field at finalize.
5. `tests/`: schema recognition, predicate truth table, both drivers' auto-approve path, and an end-to-end review->approve->execute chain.

## Deferred / out of scope (with reason)

- Full unification of the two drivers onto a shared runner library: tracked by backlog `dhuape`; this plan shares ONLY this predicate to fix the bug without taking that refactor.
- Backfilling `- Readiness:` into the 8 already-reviewed wtiso plans: not required, because the back-compat fallback (E-02) accepts their `APPROVE WITH REVISIONS APPLIED` verdict. A backfill would be cosmetic.
- Any change to what `/plan-review` decides (its rubric or verdict vocabulary): unchanged; this plan only changes how the decision is RECORDED and READ.

## Scope check

- Over-scope: none.
- Under-scope: none (field + shared predicate + both drivers + both workflow bodies + tests is the complete fix; anything less leaves one driver or one workflow variant broken).

## Required tests / validation

- Schema: `Readiness: go-pending-approval` lints clean; absent lints clean; `Readiness: bogus` is flagged with its rule id.
- Predicate truth table (the core): `go-pending-approval` -> True; `go` -> True; `no-go` -> False; absent + `APPROVE WITH REVISIONS APPLIED` + no blocking OQ -> True; absent + `APPROVE` -> True; absent + `REVIEWED - OPEN QUESTIONS` -> False; absent + verdict-approve BUT an unresolved blocking OQ -> False; a history entry containing `NO-GO` -> False even if a verdict word appears.
- ADVERSARIAL (the point of the plan): a plan whose history line contains the OLD prose phrase but whose `- Readiness: no-go` MUST NOT auto-approve - the structured field wins over prose.
- Both drivers: an auto-approve test for `oc_runipd` AND `agy_runipd` (the bug exists in both); assert the local duplicate definitions are gone.
- End-to-end: a reviewed plan with `Readiness: go-pending-approval` under `--full-auto` transitions reviewed -> approved -> queued for execute (assert the `ipd-auto-approved` event is appended).

Validation command: `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_ipd_schema.py -q` plus the new predicate tests, and a full default-suite run `python3 -m pytest -p no:randomly` (paste ACTUAL runner output; never claim success unrun).

## Spec / documentation sync

- If `AGENTS.md` or `.aw/records/plans/README.md` enumerates plan front-matter fields, add `Readiness` there as optional-and-recognized.
- Note in the `--full-auto` CLI help that auto-approval reads the structured `Readiness` field (so the help stops describing a prose match).

## Open questions

### OQ-01: Should `Readiness: go` (already human-approved) also auto-approve, or only `go-pending-approval`?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Both accepted. `go` per the workflow's vocabulary means the clean bar is met AND the human has approved, which is a strictly stronger condition than `go-pending-approval`; refusing it would be surprising. `Status: approved` remains the authoritative sign-off record, so a `go` plan is already execute-routed by status anyway; accepting it in the predicate is harmless and avoids a confusing edge case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `python3 -m pytest tests/test_ipd_schema.py -q` output showing new cases pass: a plan with `- Readiness: go-pending-approval` is conforming; a plan with NO `Readiness:` is conforming (proving optional, no IPD-M103 and no required-field failure); a plan with `- Readiness: bogus` is reported invalid with its rule id. Plus pasted `grep -n "META_READINESS\|READINESS_VALUES" agent_workflows/ipd_schema.py` showing the constant and the closed enum, and that `META_READINESS` appears in `META_RECOGNIZED` but NOT in `META_REQUIRED`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted output of the new predicate truth-table test (name the file, e.g. `tests/test_plan_readiness.py`) covering EVERY row: `go-pending-approval`->True, `go`->True, `no-go`->False, absent+`APPROVE WITH REVISIONS APPLIED`+no blocking OQ->True, absent+`APPROVE`->True, absent+`REVIEWED - OPEN QUESTIONS`->False, absent+approving-verdict-but-unresolved-blocking-OQ->False, and a history entry containing `NO-GO`->False. MUST include the ADVERSARIAL row: a plan whose history line contains the old `GO - PENDING HUMAN APPROVAL` prose but carries `- Readiness: no-go` returns False (structured field beats prose). Paste the pass summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `grep -c "def is_plan_review_approved\|def extract_last_history_entry" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing `0` for BOTH files (local duplicates deleted), plus a grep showing both import from `plan_readiness`. Plus pasted `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q` output with an auto-approve test present and passing for EACH driver (name the two test functions), proving the fix is not oc-only. ALSO include the END-TO-END chain: a plan with `Status: reviewed` and `- Readiness: go-pending-approval` processed under `--full-auto` transitions `reviewed -> approved -> queued(execute)`, asserting the `ipd-auto-approved` event is appended to the run's `events.jsonl`; and paste a full default-suite run `python3 -m pytest -p no:randomly` summary line showing green.
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


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make the auto-approve decision structured and single-sourced); the E-items are ordered sub-steps of that single fix (field -> shared predicate -> driver adoption -> workflow writes it).

Execution contract:

1. Open questions: OQ-01 resolved; execution requires explicit human approval.
2. Scope fence: touch ONLY `agent_workflows/plan_readiness.py` (new), `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/ipd_schema.py`, `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/plan-review-long.md`, and `tests/`. Do NOT undertake the broader driver unification (backlog `dhuape`), do NOT change the plan-review rubric or verdict vocabulary, and do NOT backfill the field into existing reviewed plans. If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output for the named commands; never claim success you did not run. A V-item whose command was not executed stays `Result: pending`.
4. Fail-closed rule: absent or unrecognized `Readiness` must never auto-approve. If you cannot make a case decide safely, make it return False and record why - never widen the gate to make a test pass.
5. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push; never `--no-verify`.
6. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.
