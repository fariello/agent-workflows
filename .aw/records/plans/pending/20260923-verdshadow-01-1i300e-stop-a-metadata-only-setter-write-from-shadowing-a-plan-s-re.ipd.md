# IPD: Stop a metadata-only setter write from shadowing a plan's real review verdict and silently un-approving it

- Date: 2026-09-23
- Kind: child
- Concern: A PURELY BOOKKEEPING WRITE CAN FLIP THE AUTO-APPROVE PREDICATE FROM TRUE TO FALSE ON A PLAN THAT HAS A POSITIVE REVIEW, AND I REPRODUCED THE WHOLE CHAIN AT HEAD `22cf67d9`. Backlog `da7w6n` (`high`, `Blocks-Release: next`) describes it as the composition of two shipped behaviors, neither a bug alone. FIRST, `status_set.apply_status_change` writes a history record for a FIELD-ONLY write, defaulting its text to `f"status set to {norm_status}"` and its actor to `"aw set"`, so `aw ipd set <same-status> <id6> --priority P` emits `- <date> reviewed (aw set): status set to reviewed` even though nothing transitioned. SECOND, `plan_readiness.is_review_history_entry` decides a record IS a review record by scanning its STATUS TOKEN for a review word, so that bookkeeping line qualifies.
  MEASURED, IN THREE STEPS, EACH PASTED IN THE FINDINGS. (1) `is_review_history_entry` returns True for `- 2026-09-22 reviewed (aw set): status set to reviewed`, identically to a real `/plan-review` record. (2) `newest_verdict` over a history holding a real positive review returns `('positive', <the real line>)`, and over the SAME history with the bookkeeping line prepended returns `(None, <the bookkeeping line>)`: the real verdict is shadowed. (3) With `- Readiness:` OMITTED, `is_plan_review_approved` returns True BEFORE the bookkeeping write and False AFTER it, on a plan whose only substantive record is an `APPROVE WITH REVISIONS APPLIED` review.
  STEP 3 IS WHY THIS IS `high` AND NOT A COSMETIC DUPLICATE OF `ycg597`. `AGENTS.md` REQUIRES a freshly authored plan to omit `- Readiness:` ("when AUTHORING, OMIT the field: absence is the correct state, it is silent, and it makes the gate fail closed"), and the fallback that reads history is exactly what a field-less plan depends on. So the four live plans `da7w6n` was found on are unharmed ONLY because each still carries an explicit `- Readiness: go-pending-approval` that the predicate consults first; that is benign-by-luck, and the luck runs out on every plan that follows the current authoring contract. The failure direction is the safe-looking one (a reviewed plan reads as unapproved), which means it wastes a review cycle rather than executing something unreviewed, but it does so INVISIBLY and it corrupts the provenance record while doing it.
  THE FAMILY IS FOUR ITEMS AND THEY DIVIDE CLEANLY, WHICH DECIDES THIS PLAN'S SCOPE. `ycg597` owns the DISCRIMINATOR (a tooled `aw set reviewed` line misread as a review record; the actor field already differs, `(aw set)` versus an agent/model string). `nwrb0j` is the same discriminator seen from the other side (a descope or re-check whose prose narrates `no-go` negates its own plan). `gv36a7` is a THIRD defect in the same reader (`newest_verdict` misreads a record as NEGATIVE when its verdict token is outside `VERDICTS` and its prose narrates a no-go). This plan owns what none of them covers: a field-only no-op write should not emit a review-shadowing record AT ALL.
  AND THE TWO SETTER PATHS ALREADY DISAGREE ABOUT A NO-OP, which is the cheap argument for fixing the writer rather than only the reader. `x6tk1u` (now `done`) records that the BACKLOG path DISCARDED an explicit `--message` on a same-status write, while the PLAN path writes a record even with no message at all. One setter, two opposite behaviors for the same situation.
- Scope: Make a metadata-only setter write incapable of being read as a review verdict. IN: (a) per OQ-01, either write NO history record when no status changed and no `--message` was supplied, or tag a bookkeeping record with an actor/status form no verdict reader can mistake for a review; (b) a regression test driving the measured three-step chain, including the `- Readiness:`-omitted auto-approve flip, since that is the consequence that makes this `high`; (c) reconcile the plan and backlog paths' no-op behavior so one setter has one rule. OUT: the DISCRIMINATOR fix in `plan_readiness.is_review_history_entry` (owned by `ycg597`, with `nwrb0j` as its other face) and the out-of-vocab NEGATIVE misread (`gv36a7`); this plan must not edit that reader, because two plans changing one predicate from opposite ends is how the two-readers-disagree class is created.
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py, tests/test_plan_readiness.py
- Item-Dependencies: none
- Status: to-review
- Set: verdshadow
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 1i300e
- From-Backlog: da7w6n
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `da7w6n`, whose `- Blocks-Release: next` is INHERITED. I reproduced all three steps of the chain at HEAD rather than trusting the filing, including the step that matters most: with `- Readiness:` omitted (the state `AGENTS.md` requires of a new plan), `is_plan_review_approved` goes True -> False across a metadata-only write.
  THE SCOPE BOUNDARY IS THE MAIN AUTHORING DECISION. Three sibling items (`ycg597`, `nwrb0j`, `gv36a7`) all want to change `plan_readiness`'s reader; this plan deliberately changes only the WRITER, so the four do not collide in one predicate. That is stated as a hard exclusion rather than a preference, because the defect class those three describe is precisely two readers disagreeing.
  I ALSO NOTED THE SETTER'S OWN INCONSISTENCY: `x6tk1u` (done) records the backlog path DISCARDING a `--message` on a same-status write while the plan path writes a record with no message at all, so "what does a no-op record" has two answers today and E-04 reconciles them.

## Goal

Make a field-only setter write leave a plan's review verdict exactly as it found it, so bookkeeping cannot un-approve a reviewed plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce the chain before changing the writer

- [ ] E-01 REPRODUCE ALL THREE STEPS AT YOUR HEAD, and do it before touching code, because the fix's shape depends on which step you choose to break.
  STEP 1: show `plan_readiness.is_review_history_entry` returns True for a bookkeeping line of the form `- <date> reviewed (aw set): status set to reviewed`. At authoring: True, identical to a real review record.
  STEP 2: show `newest_verdict` returns `('positive', <real line>)` for a history holding only a real review, and `(None, <bookkeeping line>)` once the bookkeeping line is prepended.
  STEP 3, THE ONE THAT MATTERS: build a plan file with `- Readiness:` ABSENT and show `is_plan_review_approved` returns True before the bookkeeping record and False after. If this step does NOT reproduce, the severity argument collapses and you must report that rather than proceeding as if it held.
  CONFIRM THE WRITER'S DEFAULTS: quote the line in `status_set.apply_status_change` that defaults the message to `status set to <status>` and the actor to `aw set`.
  - Depends on: none
  - Expected outcome: all three steps reproduced with pasted output, plus the writer's defaulting line quoted; any step that fails to reproduce reported explicitly rather than absorbed.
  - Execution state: pending

### Task group 2: fix the writer

- [ ] E-02 MAKE A FIELD-ONLY NO-OP WRITE UNABLE TO SHADOW A VERDICT, per OQ-01.
  DO NOT FIX THIS IN `plan_readiness`. That reader is owned by `ycg597`/`nwrb0j`/`gv36a7`, and three items already propose changing it; a fourth edit from this direction is how one predicate acquires two incompatible fixes. If you conclude the writer cannot be fixed alone, STOP and report that rather than reaching into the reader.
  DO NOT SILENTLY DROP A DELIBERATE `--message`. `x6tk1u` is a `done` bug whose whole content is that a same-status write DISCARDED an explicit message; "write nothing on a no-op" must therefore mean "when no message was supplied", or this fix re-creates a bug the repository already paid to fix. This is the single most important constraint on OQ-01's first option.
  IF YOU TAG INSTEAD OF SUPPRESSING, THE TAG MUST BE INVISIBLE TO THE VERDICT READER AS IT EXISTS TODAY, not as `ycg597` might leave it. A tag that only works after `ycg597` lands is a dependency this plan does not declare and must not assume.
  PRESERVE THE TRUTHFUL CASE: a REAL transition must still record normally, and a field-only write WITH a `--message` must still record the operator's prose. The target is the false-and-shadowing record, not all bookkeeping.
  - Depends on: E-01
  - Expected outcome: a field-only no-op write can no longer produce a record that `newest_verdict` reads as the newest review; an explicit `--message` is still recorded; a real transition is unchanged; `plan_readiness` untouched.
  - Execution state: pending

- [ ] E-03 FIX THE FALSE TEXT, INDEPENDENTLY OF THE SHADOWING. `da7w6n` measured that without `--message` the recorded text is "the outright false `status set to approved`" on a write that changed no status. Even if E-02 suppresses the record entirely in the no-message case, the default string remains reachable by any caller that supplies an actor but no message.
  A RECORD MUST NOT ASSERT A TRANSITION THAT DID NOT HAPPEN. That is the same forged-evidence principle `AGENTS.md` applies to attestations: a history line claiming `status set to approved` on a no-op is a false provenance claim, and provenance is the thing this whole family is about.
  - Depends on: E-01
  - Expected outcome: no code path can write a history record asserting a status change that did not occur; the message for a genuine transition is unchanged.
  - Execution state: pending

### Task group 3: one setter, one rule

- [ ] E-04 RECONCILE THE PLAN AND BACKLOG NO-OP BEHAVIORS so the setter has ONE rule. Today the plan path writes a record with no message while the backlog path historically discarded a supplied one (`x6tk1u`), which means "what does a no-op record" has two answers in one setter.
  MEASURE BOTH PATHS FIRST, since `x6tk1u` is `done` and its fix may already have unified them; if it has, say so and this item is a verification rather than a change.
  DO NOT UNIFY BY REGRESSING EITHER SIDE. The correct shared rule preserves a deliberate `--message` on both paths and writes no misleading record on neither.
  - Depends on: E-02, E-03
  - Expected outcome: both setter paths follow one documented no-op rule, verified by driving each; if `x6tk1u`'s fix already unified them, that is reported with evidence instead of a change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `AGENTS.md` REQUIRES A NEW PLAN TO OMIT `- Readiness:` ("absence is the correct state ... it makes the gate fail closed"), which is precisely the state in which this defect bites, because the history fallback is what a field-less plan depends on.
- NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD is the governing principle of this whole family: a history line whose status token reads as a review verdict is a machine-written assertion that a review happened. The writer must not manufacture one.
- HISTORY IS NEWEST-FIRST AND PREPENDED (`apply_status_change` documents it), which is exactly why a new bookkeeping line SHADOWS an older real review rather than sitting harmlessly beneath it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `status_set.apply_status_change` + `plan_readiness.newest_verdict` | A field-only bookkeeping record becomes the NEWEST review record and shadows the real verdict. | `newest_verdict` returned `('positive', <real review line>)` and, with the bookkeeping line prepended, `(None, '- 2026-09-22 reviewed (aw set): status set to reviewed')` |
| F-2 | BLOCKER | `plan_readiness.is_plan_review_approved` | With `- Readiness:` OMITTED (the state `AGENTS.md` requires of a new plan), a metadata-only write flips auto-approval True -> False on a plan holding an `APPROVE WITH REVISIONS APPLIED` review. | two fixture plans differing only by the bookkeeping line: `True` before, `False` after |
| F-3 | HIGH | `plan_readiness.is_review_history_entry` | The discriminator returns True for the bookkeeping line exactly as for a real `/plan-review` record, because it scans the STATUS TOKEN for a review word. | both lines -> `True` |
| F-4 | HIGH | `status_set.apply_status_change` | The default message asserts a transition that did not happen: `message = getattr(args, "message", None) or f"status set to {norm_status}"`, emitted even when nothing changed. | quoted from the live function |
| F-5 | MED (scope) | `ycg597`, `nwrb0j`, `gv36a7` | THREE sibling items all propose changing `plan_readiness`'s reader. This plan must change only the WRITER, or one predicate acquires four uncoordinated fixes, which is the very class those items describe. | the three items' own summaries |
| F-6 | MED | the two setter paths | `x6tk1u` (done) records the BACKLOG path discarding a supplied `--message` on a same-status write, while the PLAN path writes a record with none, so one setter has two no-op rules. | `x6tk1u`'s summary |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the discriminator, the shadowing, and the auto-approve flip at the executing HEAD.
2. E-02 stops a field-only no-op write producing a verdict-shadowing record, without touching `plan_readiness` and without dropping a deliberate `--message`.
3. E-03 removes the false `status set to <status>` assertion from any no-op path.
4. E-04 reconciles the plan and backlog no-op rules, or verifies `x6tk1u` already did.

## Deferred / out of scope (with reason)

- THE DISCRIMINATOR FIX (`ycg597`) AND ITS OTHER FACE (`nwrb0j`). Both change `is_review_history_entry`; the actor field already distinguishes `(aw set)` from an agent/model string, which is their fix and not this one's. Excluded to keep one predicate under one owner.
- THE OUT-OF-VOCAB NEGATIVE MISREAD (`gv36a7`). A third defect in the same reader; same reason.
- CHANGING WHAT A REAL TRANSITION RECORDS. Only the no-op and false-text cases are in scope; a genuine status change must keep its current record.
- THE BROADER QUESTION of whether history should carry machine bookkeeping at all. Worth deciding, but it is a records-model change affecting every artifact type, and it should be carried by a SUCCESSOR PLAN rather than folded in here or filed as a backlog item, since the measurement in this plan already establishes the need.

## Scope check

- Over-scope: `agent_workflows/plan_readiness.py` is deliberately NOT in `- Scope-Paths:` and must not be edited. `tests/test_plan_readiness.py` is listed only to ADD the F-2 regression assertion, not to change existing reader expectations.
- Under-scope: if OQ-01 resolves toward tagging, check whether any OTHER reader (for example a run-time readiness consumer) also scans the status token, and declare that file before editing rather than widening at finalize.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: `tests/test_status_set.py` and `tests/test_plan_readiness.py`.
- THE F-2 REGRESSION TEST IS MANDATORY AND MUST USE A `- Readiness:`-ABSENT FIXTURE. A test written against a plan that carries the field cannot fail, because the predicate consults the field first; that is exactly the benign-by-luck condition `da7w6n` describes, and a test with it present would be vacuous.
- Each new test must be demonstrated FAILING against pre-E-02 code and passing after.
- The existing approval-gate tests must stay green, proving the reader was not disturbed.

## Spec / documentation sync

- If OQ-01 changes what a no-op setter write records, that is operator-visible behavior for `aw set`/`aw ipd set` and should be documented where the setter's contract is described.
- No `.spec.md` edit is anticipated. If the no-op rule is specified in a spec governing the setter or the approval gate, declare that file in `- Scope-Paths:` before editing it, per the spec-amendment rule.

## Open questions

### OQ-01: Suppress the no-op record, or tag it unmistakably?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 requires one of the two and either removes the shadowing, so the plan terminates correctly either way. SUPPRESS (write nothing when no status changed and no `--message` was given) is simplest and cannot be misread by any reader present or future, but it MUST be conditioned on the absence of a message or it re-creates `x6tk1u`, and it loses the (weak) audit value of recording that a field was touched. TAG (record with an actor/status form no verdict reader accepts) keeps the audit trail and is the smaller behavioral change for existing callers, but its correctness depends on the CURRENT reader's parsing, so it needs a test proving the tagged line is not a review record TODAY rather than after `ycg597`. Recommend SUPPRESS-when-no-message, because it is robust to the three pending reader changes rather than entangled with them.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output for all three steps (discriminator True on the bookkeeping line; `newest_verdict` positive-then-None; `is_plan_review_approved` True-then-False with `- Readiness:` absent), plus the writer's defaulting line quoted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the F-1/F-2 chain re-run after the fix, pasted, showing `newest_verdict` still returns the REAL review and `is_plan_review_approved` stays True across a field-only write; plus a case proving an explicit `--message` is still recorded; plus confirmation by diff that `plan_readiness.py` is unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted proof that no path writes `status set to <status>` for a write that changed no status, and that a genuine transition's message is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: both setter paths driven on a same-status write with and without `--message`, output pasted, showing one consistent rule; or, if `x6tk1u` already unified them, the evidence showing that with no change made.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
