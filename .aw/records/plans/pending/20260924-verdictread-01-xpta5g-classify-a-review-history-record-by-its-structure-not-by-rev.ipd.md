# IPD: Classify a review history record by its structure, not by review words in its prose

- Date: 2026-09-24
- Kind: child
- Concern: The review-verdict reader misclassifies history records in three ways, filed as backlog `ycg597`, `nwrb0j` and `gv36a7` (one defect class, one reader). `plan_readiness.is_review_history_entry` counts a record as a review when ANY token of its status/workflow middle is in `_REVIEW_WORDS` or starts with `/plan-review`, and `plan_readiness.newest_verdict` reads the newest such record, falling back to a negative-READINESS prose scan when no `VERDICTS` token is present. Reproduced at HEAD `cfc7f5c1` with in-memory plans passed to `newest_verdict` and `approval_refusals`: (a) `ycg597`: a tooled `- ... reviewed (aw set): status set to reviewed` line above a `/plan-review ... REJECT - NEEDS REPLAN` record returns polarity `None` and ZERO refusals, so the one un-overridable refusal is shadowed; (b) `nwrb0j`: a `- ... reviewed (oc/m): descope per maintainer order; readiness stays no-go` line above an `APPROVE WITH REVISIONS APPLIED` review returns `negative` and 1 refusal; (c) `gv36a7`: a real `/plan-review` record `REVIEWED - REVISIONS APPLIED; readiness advanced from no-go` (a token outside `VERDICTS`) returns `negative` and 1 refusal over an earlier `APPROVE`. The writer half of (a) shipped in `1i300e` (same-status setter lines are now tagged `same-status`), but every old-form line on disk, and every real transition line such as `to-review -> reviewed (aw set): status set to reviewed`, still qualifies.
- Scope: IN: (1) one structural classifier rule in `plan_readiness.is_review_history_entry` (which `history_has_review_record` and `newest_verdict` both consume); (2) `newest_verdict` returns `None` ("unknown") for a review record whose verdict is outside `VERDICTS`, and the negative-readiness prose fallback is removed from it; (3) one regression test per backlog item, each failing at HEAD; (4) updating the two shipped test fixtures that pin the old "bare setter line is a review record" behavior; (5) documenting in the plan-review and spec-review workflows that the history line leads with a closed-set verdict token and that a non-review act must not wear a review label. OUT: `history_verdict_approves` (the stricter auto-approve rule, deliberately separate, see its docstring), the structured `- Readiness:` path, and any rewrite of existing history records.
- Scope-Paths: agent_workflows/plan_readiness.py, tests/test_review_record_classifier.py, tests/test_spec_review_attestation.py, tests/test_oc_runipd.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/spec-review/spec-review.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: verdictread
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: xpta5g
- From-Backlog: ycg597
- Blocks-Release: next

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ycg597, nwrb0j, gv36a7; reproduced all three misreads at HEAD cfc7f5c1 and measured the candidate classifier over every tracked plan (0 verdict flips in pending/, 0 auto-approve flips anywhere, no flip to negative).

## Goal

Make the approval gate read a verdict only from a record that IS a review, identified by where `/plan-review` and `/spec-review` write it, so tooled lines and non-review acts can neither shadow nor forge a verdict, and an unrecognized verdict reads as unknown rather than as a rejection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Tests first

- [ ] E-01 Add `tests/test_review_record_classifier.py` with three tests built on in-memory plan text (no disk), each asserting through `plan_readiness.newest_verdict` AND `plan_readiness.approval_refusals`: `test_ycg597_tooled_line_does_not_shadow_a_reject` (history: `- 2026-09-10 reviewed (aw set): status set to reviewed` newest, then `- 2026-09-10 /plan-review (oc/m): REJECT - NEEDS REPLAN; PR-001`; expect `NEGATIVE`, the sourced entry contains `REJECT`, 1 refusal); `test_nwrb0j_review_word_label_on_a_non_review_act_is_not_a_verdict` (newest `- 2026-09-12 reviewed (oc/m): descope per maintainer order; readiness stays no-go`, then an `APPROVE WITH REVISIONS APPLIED` `/plan-review` record; expect `POSITIVE`, 0 refusals); `test_gv36a7_out_of_vocab_verdict_is_unknown_not_negative` (newest `- 2026-09-12 /plan-review (oc/m): REVIEWED - REVISIONS APPLIED; readiness advanced from no-go`, then `/plan-review ... APPROVE`; expect polarity `None`, sourced entry is the newest record, 0 refusals). Also add a pure table test of `is_review_history_entry` covering the rows listed under Proposed changes.
  - Depends on: none
  - Expected outcome: the three per-item tests FAIL at HEAD with the observed values quoted in the Concern.
  - Execution state: pending

### Task group 2: The classifier

- [ ] E-02 Rewrite `plan_readiness.is_review_history_entry` to the structural rule under Proposed changes (A: a `/plan-review` or `/spec-review` workflow label in the middle; B: a middle whose FIRST token is a review word AND whose message LEADS with a verdict-vocabulary word or names the review workflow in its first clause). Keep `_HISTORY_RECORD_PARTS_RE` unchanged (one parser, per its comment). Update the docstrings of `is_review_history_entry`, `history_has_review_record` and `newest_verdict` to state the rule and the measurement.
  - Depends on: E-01
  - Expected outcome: `test_ycg597_*` and `test_nwrb0j_*` pass.
  - Execution state: pending

- [ ] E-03 In `plan_readiness.newest_verdict`, delete the `negative_readiness_asserted(message)` fallback so a review record with no `VERDICTS` token returns `(None, candidate)`. Keep `negative_readiness_asserted` itself (it is a pure helper and removing it is out of scope), but correct any comment that says `newest_verdict` uses it.
  - Depends on: E-02
  - Expected outcome: `test_gv36a7_*` passes; the three per-item tests pass together.
  - Execution state: pending

- [ ] E-04 Update the shipped fixtures that pin the old behavior: in `tests/test_spec_review_attestation.py`, the `ENTRIES` row `reviewed (aw specs): status set to reviewed` flips to `False` with its `why` rewritten (a bare setter line is not a review, `ycg597`), and the `MESSAGES` row `status set to reviewed` expects `(None, "")`; in `tests/test_oc_runipd.py` `test_structured_readiness_field_decides_auto_approval`, replace the `p_field` history line with a real `/plan-review (opencode): APPROVE; PR-001` record so the fixture still exercises the field, not the forged-field refusal.
  - Depends on: E-03
  - Expected outcome: both files pass; no assertion is deleted, only the pinned-defect expectations change.
  - Execution state: pending

### Task group 3: Contract and measurement

- [ ] E-05 In `.aw/system/workflows/plan-review/plan-review.md` (after "Use the real agent/model name, or `unknown`.") and the matching line in `.aw/system/workflows/spec-review/spec-review.md`, add: the message MUST lead with exactly one verdict from the closed list; readiness words belong in `- Readiness:`, not in place of the verdict; a non-review act recorded while the plan is `reviewed` (descope, OQ answer, re-check) uses its own label (`re-scope`, `readiness re-check`) and never `reviewed` or `/plan-review`.
  - Depends on: E-02
  - Expected outcome: both workflow files carry the rule.
  - Execution state: pending

- [ ] E-06 Re-run the corpus measurement: for every tracked `.aw/records/plans/**/*.ipd.md`, compare HEAD-before versus after for `newest_verdict` polarity and `is_plan_review_approved`, using `git stash`-free comparison (import the pre-change function from `git show HEAD:agent_workflows/plan_readiness.py` into a scratch module under `/tmp`).
  - Depends on: E-03
  - Expected outcome: 0 flips in `pending/`, 0 auto-approve flips anywhere, no flip TO `negative`; the executed/superseded flips match the pre-measured shape (about 37, all from `None` or from a maintainer-attestation line).
  - Execution state: pending

- [ ] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: all pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One history parser: `_HISTORY_RECORD_PARTS_RE` comment says "do not add a third parser"; the rule reuses it.
- History is newest-first (`plan_readiness.extract_newest_history_entry` docstring).
- The machine readiness signal is the `- Readiness:` field; the workflow says "THE HISTORY-LINE PROSE IS NOT THE MACHINE SIGNAL" (`plan-review.md`, "Verdict and readiness").
- The workflow's prescribed review line is `- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>`.
- `tests/test_plan_readiness.py` no longer exists (removed in `19313eed`); new tests go in a new focused file.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

- F-1 The actor alone cannot be the discriminator: measured, many GENUINE reviews were recorded through the tool with `--message` (e.g. `reviewed (aw set): plan-review round 2: APPROVE WITH REVISIONS APPLIED; ...`, `reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO`). An `(aw set)` exclusion would hide those. So rule B keys on the message HEAD, which is the position the workflow assigns to the verdict, not on any word anywhere in the prose.
- F-2 The readiness fallback in `newest_verdict` currently decides 0 plans: measured over every tracked plan, no `NEGATIVE` result comes from it. Removing it costs no live refusal and removes mechanism (c).
- F-3 Candidate-rule probe (`/tmp/opencode/g2/probe-verdictread/r.py`): pending/ 0 verdict flips, 0 auto-approve flips; whole tree 37 flips (`None->positive` 17, `None->neutral` 8, `positive->neutral` 12). The 12 `positive->neutral` are plans whose newest "review" was `reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION ... not by an agent and not by a review`; the new rule correctly reads the actual review behind it. All are executed, and none flips to negative.
- F-4 The `readiness re-check` label (`plan_readiness.format_recheck_history_entry`) stays a non-review under both rules.

## Proposed changes (ordered, validatable)

The rule. A parsed record is a REVIEW record iff:
- A. its middle contains a workflow label `/plan-review` or `/spec-review` (optionally `/aw plan-review`, any suffix such as ` pass 2` or `-long`); or
- B. its middle's FIRST token is in `_REVIEW_WORDS` AND its message either begins with `APPROVE`, `REJECT` or `REVIEWED -`, or names `plan-review`/`spec-review` before its first `:` or `;`.

Classifier table (pinned by E-01): `reviewed (aw set): status set to reviewed` False; `reviewed (aw set): set Item-Dependencies to executed:76w6mq` False; `reviewed (oc/m): descope ...; readiness stays no-go` False; `readiness re-check (a/m): ...` False; `to-review (aw specs): ...` False; `/plan-review (a/m): REVIEWED - REVISIONS APPLIED; ...` True; `reviewed (oc): /spec-review round 1; APPROVE` True; `reviewed (aw specs): REJECT - RESUBMIT` True (a review with an unknown verdict, so `None`, as the shipped `MESSAGES` row already expects); `reviewed round 2 (a/m): APPROVE ...` True.

Unknown verdict: a review record whose message has no `VERDICTS` token yields `(None, record)`. It does not negate an earlier positive (no refusal), and it does not resurrect an older verdict either. The newest review still decides. Skipping it would let an older `REJECT` refuse a plan that a newer review had cleared, which is the "malformed review accepted as absent" route `ycg597` warns against.

## Deferred / out of scope (with reason)

- Aligning `history_verdict_approves` (the auto-approve prose rule) with this classifier. It reads the newest record of any kind and is deliberately stricter; changing it is a separate risk decision.
  - Carrier-Declined: deliberate non-goal; its docstring states the asymmetry is policy, and no defect in it is reported by these items.
- Rewriting existing history records. The reader fix makes old records read correctly, and `executed/` bodies must not be re-committed.
  - Carrier-Declined: not needed once the reader is fixed.

## Scope check

- Over-scope: none.
- Under-scope: none. `history_has_review_record` inherits the fix through `is_review_history_entry`, which is intended (a bare setter line must not attest a `- Readiness:` field either).

## Required tests / validation

The three per-item tests in `tests/test_review_record_classifier.py`, shown FAILING before E-02/E-03 and passing after; the updated fixtures in the two shipped test files; the corpus re-measurement; the bare suite.

## Spec / documentation sync

- `.aw/system/workflows/plan-review/plan-review.md` and `.aw/system/workflows/spec-review/spec-review.md` gain the history-line rule (E-05), which answers `gv36a7` scope item 2 (the vocabulary stays closed; the workflow says so) and `nwrb0j` scope item 1 (non-review labels documented).
- No `.spec.md` is amended: no spec under `.aw/records/specs/` names `is_review_history_entry` or `newest_verdict` (grep at HEAD returned nothing).

## Open questions

### OQ-01: Should `VERDICTS` also recognize readiness-style phrasings such as `REVIEWED - REVISIONS APPLIED`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default is NO: keep the closed four-token vocabulary, read anything else as unknown (E-03), and document the rule in the workflow (E-05). Widening the vocabulary is a public-contract change the maintainer may choose later without touching this classifier.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_review_record_classifier.py` run BEFORE E-02, showing the three per-item tests FAILED with the HEAD values (`None` for ycg597, `negative` for nwrb0j and gv36a7).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same command after E-02, showing `test_ycg597_*`, `test_nwrb0j_*` and the classifier table PASSED, with `test_gv36a7_*` still failing; paste the `git diff` of `is_review_history_entry`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the same command after E-03 showing all tests in the file passed, plus `grep -n "negative_readiness_asserted" agent_workflows/plan_readiness.py` showing no call inside `newest_verdict`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_spec_review_attestation.py tests/test_oc_runipd.py -k "recognized_as_reviews or sourced_from_the_review or structured_readiness_field"` showing all selected tests passed, and the diff hunks showing only the pinned rows changed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff --stat -- .aw/system/workflows/plan-review/plan-review.md .aw/system/workflows/spec-review/spec-review.md` and the added lines.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the probe's output lines: pending flips `{}`, auto-approve flips `0`, and the whole-tree flip histogram containing no `-> negative` key.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run, showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Commit through `aw commit xpta5g -- <paths>` limited to Scope-Paths; never push. When every V item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` and set backlog `ycg597`, `nwrb0j` and `gv36a7` to `done` citing this plan.
