# IPD: Make the status-untooled remediation clear its own finding by writing a genuine transition record

- Date: 2026-09-26
- Kind: child
- Concern: `check.status-untooled` tells an operator who hand-edited a plan's `- Status:` to run `aw set <status> <id6>`, but that command can never clear the finding. The file on disk already carries the target status, so `status_set.apply_status_change` sees `old == target` and writes a `same-status` history token (or nothing at all when no `--message` is given), while `check_engine._has_matching_history_line` accepts only a token equal to the new status. Reproduced at HEAD `61ef21d8` in a scratch repo: hand-edit `to-review` -> `reviewed`, stage, `check_status_untooled` fires; `aw set reviewed aaa111 --yes --no-commit` reports `unchanged` and writes nothing; with `--message fix` it writes `- 2026-09-26 same-status (aw set): fix`; the finding persists in both cases.
- Scope: IN: in `status_set.apply_status_change`, when the target equals the on-disk status AND the record is a plan whose HEAD blob status differs, treat the change as a genuine transition from the HEAD status (write a `<status>` history token and the transition's default message) WHILE KEEPING the same-status duplicate suppression reachable on that path; outcome tests including a double-run idempotence test; the doctor remediation text and the ONE existing test that pins its current wording. OUT: relaxing `check_engine._has_matching_history_line`; non-plan record types; the approval-floor rules; the checker's own drift-detail wording.
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py, agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: executed:6k7xot
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mpghjn
- Blocks-Release: next
- Set: doctorhint
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9aqrzu

## Workflow history
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 8 findings PR-1101..PR-1108 all FIXED (2 HIGH), 4 decisions D-1..D-4 recorded; review record written. Reproduced F-1..F-3 and proved the fix premise (a real status token clears the finding). PR-1101 (HIGH): E-01's 'is_same_status = False' makes the duplicate suppression unreachable and duplicates history on every re-run, re-opening the 1i300e/vhbvwz defect (measured two identical records); rewritten to keep the flag and widen _write_history_anyway. PR-1102 (HIGH): the E-03 reword breaks a pinned assertion in tests/test_doctor.py, which was undeclared; path added. PR-1103: E-03's conditional resolved (both doctor strings require reverting, so the edit is mandatory). PR-1104: the gate claimed the plan was blocked on a question carrying Blocking: no and Status: resolved; corrected. Added E-05/V-05 for the ipd_lifecycle caller. aw ipd lint --phase review-finalize conforming; aw check plans clean for this plan.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mpghjn: implement option 2 (setter writes a genuine transition record when HEAD status differs); blocked on maintainer choice among three fixes (OQ-01).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Running the command `check.status-untooled` recommends clears the finding, while a true re-assertion of an unchanged status still writes only a `same-status` record and the checker stays strict.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: setter writes a genuine record for an untooled status

- [ ] E-01 In `status_set.apply_status_change`, after `is_same_status` is computed: if `is_same_status` and `rec.record_type == "plans"`, read the plan's status at HEAD (repo-relative path of `rec.path`; `check_engine._blob_text(repo_root, "HEAD", rel)` then `check_engine._status_meta(...)`, imported locally as `status_set` already does for `check_engine` elsewhere, or an equivalent single `git show HEAD:<rel>`). Only on this path, and only when git succeeds and yields a status that DIFFERS from the target, set `status_tag = norm_status` and `default_message = f"status set to {norm_status}"`, and record the fact in a NEW local flag (name it `untooled_transition`). On any git failure (not a repo, path untracked at HEAD, blob has no status), keep today's same-status behavior. Do not change the approval-line or gate-field logic; note that the `- Approval:` writer keys on `norm_status == "approved"` and NOT on `is_same_status`, so its text changes automatically with `message` (measured today: a same-status `approved` call writes `- Approval: <date>, recorded via aw ipd set: status unchanged (approved)`; after the change it reads `status set to approved`).
  - DO NOT SET `is_same_status = False`, WHICH IS WHAT THE PLAN ORIGINALLY SAID, AND DO NOT ADD A SEPARATE ESCAPE HATCH TO THE EARLY RETURN. Both would re-open a defect the repository already fixed. The mechanism, read at review: `is_dup = same_status_message_is_duplicate(...) if is_same_status else False` is evaluated MUCH LATER in the function than where the plan told you to flip the flag, and `should_write_history = not (is_same_status and is_dup)`. So flipping `is_same_status` at the top makes `is_dup` unconditionally `False` hundreds of lines later, the duplicate suppression becomes UNREACHABLE on exactly this path, and every re-run appends another identical record. Measured at review: two runs of the fix path produce two byte-identical `- 2026-09-27 reviewed (aw set): status set to reviewed` lines. That is the accumulating-duplicate-history defect plan `1i300e` (E-02/E-03) and `vhbvwz` exist to prevent, and `same_status_message_is_duplicate`'s own docstring names idempotent re-assertion as the case it protects.
  - THE CORRECT SHAPE, WHICH KEEPS ONE DEDUP DECISION: leave `is_same_status` TRUE so the existing `is_dup` call still runs (it compares the newest record's status token, date and message, and `same-status` matching is symmetric so a real `<status>` token compares correctly), then widen the two write decisions to admit the new path: `_write_history_anyway = (bool(_explicit_message) or untooled_transition) and not is_dup`, and `should_write_history = not (is_same_status and is_dup)` unchanged. Verified at review that this still clears the finding: the FIRST run writes the real token (`check_status_untooled` then reports `[]`) and a SECOND identical run is suppressed by the dedup (`same_status_message_is_duplicate(..., status="reviewed", date=<today>, message="status set to reviewed")` returns `True`), while a genuinely different `--message` is still recorded (returns `False`).
  - Depends on: none
  - Expected outcome: `aw set <status> <id6>` on a staged hand-edited plan writes `- <date> <status> (aw set): status set to <status>`; running it a SECOND time writes no duplicate.
  - Execution state: pending

- [ ] E-02 Add outcome tests to `tests/test_status_set.py` in a new class using a real temp git repo (init, config user, commit a plan at `to-review` with `Work-Kind`/`Priority`, `## Workflow history`): (a) hand-edit `- Status:` to `reviewed`, `git add`, assert `check_engine.check_status_untooled(repo)` reports `check.status-untooled`; run the setter for `reviewed` (via `status_set.run_set_command` with the same args the CLI builds, or `support.run_cli("set", "reviewed", "<id6>", "--yes", "--no-commit", cwd=repo)`); `git add`; assert the finding is gone and the newest history record's status token is `reviewed`. (b) True same-status: commit the plan at `reviewed` (HEAD == staged), run `aw set reviewed <id6> --message note`, assert the newest record's token is `same-status`. (c) Outside git (plain temp dir, no repo): same-status behavior unchanged. Outcomes only: assert findings and written history tokens, never source text.
  - ADD A FOURTH CASE (d), IDEMPOTENCE, WHICH IS THE ONE THAT GUARDS THE REGRESSION E-01 NOW AVOIDS: from case (a)'s post-fix state, run the SAME setter command again without committing, and assert the count of history records carrying the `<status>` token is still exactly ONE. Without this the wrong E-01 implementation passes every other case in this item while silently accumulating duplicate records, which is precisely how `1i300e`'s defect would return unnoticed.
  - ALSO ADD (e), THE TERMINAL-STATUS CASE, because it behaves differently today and the plan never mentioned it: hand-edit a committed `to-review` plan to `not-executed` (leaving the file in `pending/`), stage, then run the setter. Measured at review at HEAD: the file DOES relocate to `not-executed/` (so `path_changed` is true and a `same-status` record IS written even with no `--message`), the command still reports `unchanged`, and `check.status-untooled` STILL fires. Assert the finding clears after the fix and that the file lands in `not-executed/`. This is the case that proves F-1's "writes NOTHING" is specific to a status whose directory does not change.
  - Depends on: E-01
  - Expected outcome: five cases pass; (a) and (e) fail against the pre-change setter; (d) fails against the rejected `is_same_status = False` implementation.
  - Execution state: pending

- [ ] E-03 Doctor text: reword the `status-untooled` branch of `doctor.build_remediation`. THE CONDITIONAL IS ALREADY RESOLVED, at review, against the code 6k7xot actually shipped: BOTH strings make reverting REQUIRED, so this edit IS needed and `doctor.py` must NOT be `--scope-ack`ed. Measured verbatim: `summary_fix` reads "revert the hand edit and apply status change via '<cmd>' so an attributed history entry is appended", and `detailed_fix` reads "... revert the hand edit so the status returns to its previous value, then apply the change via '<cmd>' ...". 6k7xot's own E-04 says in as many words to "make `detailed_fix` state the two-step recovery ... revert the hand edit (so the status returns to its previous value), then apply the transition", so the revert wording is deliberate there and becomes false here. Reword both to say the finding clears by running `aw ipd set <status> <id6>` directly on the hand-edited plan, keeping `command=None` (unchanged: the id6 is best-effort via `_extract_record_id6` and the branch is deliberately advisory per 6k7xot's E-04).
  - YOU MUST ALSO UPDATE THE TEST THAT PINS THE OLD WORDING, and it is in a file the plan did not originally declare: `tests/test_doctor.py::DoctorRemediationTests::test_remediation_status_untooled` asserts `self.assertIn("revert the hand edit", rem.detailed_fix)`. Rewording `doctor.py` without editing that test FAILS THE SUITE, which would have been discovered only at E-04's bare run with the cause several items behind. `tests/test_doctor.py` is now in `- Scope-Paths:`. Change the assertion to pin the NEW contract (the fix names `aw ipd set` and does NOT require a revert), keep the `assertIsNone(rem.command)` assertion exactly as it is (6k7xot's advisory decision is not being reversed), and do not touch any other test in that file. Note `assertIn("aw ipd set", ...)` remains true either way and is therefore not the assertion that matters.
  - DO NOT REWORD THE CHECKER'S OWN DRIFT DETAIL. `check_engine.check_status_untooled` emits "... apply it via `aw set <status> <id6>` (or `aw ipd set <status> <id6>`) so the transition is attributed", which never mentioned reverting and becomes TRUE once E-01 lands. It is out of scope and needs no edit.
  - Depends on: E-01
  - Expected outcome: no doctor text contradicts the fixed behavior, and `tests/test_doctor.py` passes.
  - Execution state: pending

- [ ] E-04 Reproduce end to end in a scratch repo (the Concern's recipe) and run the bare suite.
  - Depends on: E-02, E-03
  - Expected outcome: drift before; exit 0 and drift gone after; bare suite green.
  - Execution state: pending

- [ ] E-05 CONFIRM THE TWO OTHER CALLERS OF `apply_status_change` ARE UNAFFECTED, by reasoning stated against the code and one narrowed test run, not by assumption. The callers are `status_set.run_set_command` (the CLI) and `ipd_lifecycle`'s finalize (`_ss.apply_status_change(wt_rec, "executed", coord.path, ns)`). Argue and show: (a) finalize passes target `executed` against a plan whose on-disk status is a pre-terminal value, so `is_same_status` is FALSE and the new branch is inert; and (b) finalize cannot reach it with a terminal status because the pre-transition gate refuses first ("carries Status ... which is already terminal; there is nothing to retire"). Then run `python3 -m pytest -o addopts="" tests/test_status_set.py tests/test_ipd_lifecycle.py -q` (or the lifecycle test module that exists) and paste the counts.
  - WHY THIS ITEM EXISTS RATHER THAN BEING ASSUMED: the new branch runs a `git show` inside a function that finalize calls inside a COORDINATOR WORKTREE, whose HEAD is not the caller's HEAD. If the branch ever did fire there it would read a different commit's status, so the claim that it cannot fire needs to be stated and checked rather than believed. Measured at review: `status_set` does not import `check_engine` at module level and `check_engine` does not import `status_set` at module level, so the local import E-01 prescribes introduces no cycle (this is also the gate's stop condition, and it is expected NOT to fire).
  - Depends on: E-01
  - Expected outcome: both callers demonstrably unaffected; the named test modules pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine.check_status_untooled` is commit-scoped: it compares the staged blob (`:0:`) with HEAD and only examines plans whose status changed in the commit.
- `status_set.apply_status_change` owns history writing; `same_status_message_is_duplicate` dedups same-status records (plans `vhbvwz`, `1i300e`).
- `check_status_untooled`'s docstring records an accepted efficacy ceiling: a hand edit that also writes a plausible history line is not caught. Option 2 does not move that ceiling.
- Tests assert OUTCOMES only (maintainer rule).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-4 measured at HEAD `61ef21d8` in a scratch repo (plan `aaa111`, committed `to-review`, hand-edited to `reviewed`, staged), and ALL FOUR RE-REPRODUCED AT REVIEW HEAD `25f790db` in fresh scratch repos: the hand-edit raises `check.status-untooled`; `aw set reviewed <id6> --yes --no-commit` prints `unchanged` and writes nothing (F-1); with `--message fix` it writes `- <date> same-status (aw set): fix` and the drift persists (F-2); a hand-edit to `approved` writes `- Approval: <date>, recorded via aw ipd set: status unchanged (approved)` (F-3). F-5 through F-10 were added at review.

THE FIX MECHANISM WAS ALSO PROVEN, not just the defect: writing a genuine `- <date> reviewed (aw set): status set to reviewed` line into the staged plan makes `check_status_untooled` return `[]`. So option 2 does clear the finding, which is the premise the whole plan rests on.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `status_set.apply_status_change` | With no `--message`, the recommended command writes NOTHING (reports `unchanged`), so the finding cannot clear. | `aw set reviewed aaa111 --yes --no-commit` -> `plan 20260926-demo-01-aaa111 [low] unchanged`; `check_status_untooled` still `['check.status-untooled']` |
| F-2 | MED | same | With `--message`, it writes a `same-status` record the checker rejects. | `- 2026-09-26 same-status (aw set): fix`; drift persists |
| F-3 | INFO | approval target | A same-status `approved` call writes an `- Approval:` line whose text says `status unchanged (approved)`. | scratch repo, hand-edit `reviewed` -> `approved`, `aw set approved aaa111 --yes --no-commit` |
| F-4 | INFO | backlog mpghjn | The item's reproduction says the command "exit 0 ... history written: same-status"; that is the `--message` case (F-2). Without a message nothing is written (F-1). Both leave the finding. | F-1, F-2 |
| F-5 | HIGH | `status_set.apply_status_change` (the ORIGINAL E-01 instruction) | SETTING `is_same_status = False` REINTRODUCES A FIXED DEFECT. `is_dup` is computed far below as `same_status_message_is_duplicate(...) if is_same_status else False`, so flipping the flag at the top makes the duplicate suppression unreachable on this path and every re-run appends another identical record: the accumulating-history defect `1i300e` (E-02/E-03) and `vhbvwz` exist to prevent. E-01 now keeps `is_same_status` true and widens `_write_history_anyway` instead. | Two runs of the fix path produced two byte-identical `- 2026-09-27 reviewed (aw set): status set to reviewed` records; with the dedup reachable, `same_status_message_is_duplicate(..., "reviewed", <today>, "status set to reviewed")` returns `True` for the second run and `False` for a different message |
| F-6 | HIGH | `tests/test_doctor.py::DoctorRemediationTests::test_remediation_status_untooled` | E-03's REWORD BREAKS A PINNED TEST IN AN UNDECLARED FILE. That test asserts `assertIn("revert the hand edit", rem.detailed_fix)`; `tests/test_doctor.py` was not in `- Scope-Paths:`, so the reword would have failed the bare suite at E-04 with the cause two items back. Path now declared and E-03 carries the instruction. | The assertion read verbatim; `grep -rn "revert the hand edit" agent_workflows/ tests/` -> two `doctor.py` sites and that one test |
| F-7 | MEDIUM | E-03's conditional | THE CONDITIONAL IS ALREADY DECIDABLE AND RESOLVES TO "EDIT REQUIRED", so leaving it conditional invited an executor to `--scope-ack` `doctor.py` and ship a contradiction. Both strings make reverting REQUIRED, and 6k7xot's E-04 says to write exactly that. | `summary_fix`: "revert the hand edit and apply status change via '<cmd>'"; `detailed_fix`: "revert the hand edit so the status returns to its previous value, then apply the change via '<cmd>'"; 6k7xot E-04's own wording |
| F-8 | MEDIUM | the plan's gate versus OQ-01 | SELF-CONTRADICTION: the gate says "THIS PLAN IS BLOCKED ON ONE HUMAN DECISION AND MUST NOT BE APPROVED OR EXECUTED" and cites "`OQ-01` (`- Blocking: yes`)", while OQ-01 carries `- Blocking: no` and `- Status: resolved` with a recorded maintainer answer. A reader trusting the gate would refuse to approve a plan whose blocker is answered. | The two lines read side by side in this file |
| F-9 | INFO | terminal-status hand-edit | THE "WRITES NOTHING" SYMPTOM IS STATUS-DEPENDENT, which F-1 did not say. A hand-edit to a status whose DIRECTORY differs (e.g. `not-executed`) makes `path_changed` true, so a `same-status` record IS written with no `--message` and the file relocates; the finding still persists. E-02 gains case (e). | Scratch repo: hand-edit `to-review` -> `not-executed`, stage, `aw set not-executed <id6> --yes --no-commit` -> reports `unchanged`, file moved to `not-executed/`, history gained `- <date> same-status (aw set): status unchanged (not-executed)`, drift still `['check.status-untooled']` |
| F-10 | INFO | backlog `mpghjn` recommendation | The item RECOMMENDED options (1) or (3); this plan implements (2), which the item described as "more faithful, but it needs a way to know the previous value, which is a git read the setter does not do". The plan's OQ-01 records the maintainer overriding that recommendation, so the divergence is attributed rather than accidental. Noted because the two documents disagree and a later reader will notice. | `mpghjn`'s "Candidate fixes" section; OQ-01's resolution text |

## Proposed changes (ordered, validatable)

1. E-01: untooled-transition path in the setter, with the duplicate suppression preserved.
2. E-02: outcome tests, including idempotence and the terminal-status case.
3. E-03: doctor text (required, not conditional) plus the one test that pins it.
4. E-04: end-to-end reproduction; bare suite.
5. E-05: confirm the finalize caller and the CLI caller are unaffected.

## Deferred / out of scope (with reason)

- Specs and backlog items with hand-edited statuses: `check_status_untooled` examines plans only.
  - Carrier-Declined: no checker fires for those types, so there is nothing to clear.

## Scope check

- Over-scope: none. `doctor.py` WILL be edited (E-03's conditional is resolved at review; F-7), so it is not a maybe and must not be acked.
- Under-scope: none remaining. Two gaps were found at review and are now IN scope rather than discovered at execution: `tests/test_doctor.py` (F-6, an existing assertion pins the wording E-03 changes) and E-05 (the finalize caller's behavior, which the plan asserted nothing about even though the new branch runs inside a coordinator worktree). E-02 gained two cases (idempotence, terminal status).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_status_set.py -v -k untooled` (five cases); `python3 -m pytest -o addopts="" tests/test_doctor.py -q`; the narrowed lifecycle run from E-05; the scratch-repo reproduction; bare suite. Test rule: outcomes only.

## Spec / documentation sync

N/A: no `.spec.md` specifies the same-status tag, and no `.spec.md` is in `- Scope-Paths:`. AGENTS.md says `aw set` records history on every transition, which this makes true for the untooled case. Two DOCSTRINGS become stale-by-omission rather than wrong and are deliberately left to the executor's judgement inside the declared files: `apply_status_change`'s own docstring describes the same-status behavior without the new untooled exception, and `check_status_untooled`'s docstring records an accepted efficacy ceiling that this change does NOT move (a hand edit that also writes a plausible history line is still uncaught). Updating `apply_status_change`'s docstring is in scope as part of editing that function; do not edit `check_engine`'s.

## Open questions

### OQ-01: Which of the three fixes should be used?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-26 BY THE MAINTAINER, who chose option 2 when asked directly (the agent had first resolved it from repository evidence; the maintainer confirmed). Supporting evidence: `check_engine._has_matching_history_line`'s docstring records an accepted efficacy ceiling of catching the careless hand-edit, and option 1 would let exactly that case pass after one no-op command, lowering the ceiling the rule was built to hold; option 3 leaves the remediation `aw doctor` prints permanently unable to work, which is the defect itself. Option 2 keeps the checker strict and makes the printed fix work, at the cost of one git read on the same-status path only, and is reversible. This plan implements option 2 because it keeps the checker strict. The three options, in plain words: (1) TEACH THE CHECKER to accept a `same-status` record as proof the status was tool-applied. Smallest change, but it weakens the check: a hand edit followed by any no-op `aw set` would pass. (2) MAKE THE SETTER NOTICE the hand edit: when you ask `aw set` for the status the file already has, but the last commit had a different status, record it as a real transition (`<status>` token). The checker stays strict; the cost is one `git show HEAD:<path>` on that one path only. (3) CHANGE ONLY THE ADVICE: tell operators to undo the hand edit and then run `aw set`. No code change, but the one-command fix stays impossible. RECOMMENDATION: option 2. If the maintainer picks (1) or (3), this plan is superseded and a new one written.

REVIEW NOTE (2026-09-26), recorded because this question's state is load-bearing twice over. FIRST, the fields are correct as they stand (`- Blocking: no`, `- Status: resolved`) and the plan's GATE contradicted them by claiming the plan was blocked on a `- Blocking: yes` question; the gate was corrected, not this question (F-8). SECOND, the chosen option diverges from what backlog `mpghjn` itself recommended ((1) or (3)), so the resolution rests entirely on the recorded maintainer answer; that divergence is now stated in the gate so the approving human is asked to confirm it rather than discovering it later (F-10). The supporting repository evidence cited above was re-read at review and holds: `_has_matching_history_line`'s docstring does record the accepted efficacy ceiling that option (1) would lower.
- Carrier: mpghjn

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `apply_status_change`; state which code path now runs `git show` and paste a grep showing it is inside the `is_same_status and record_type == "plans"` branch only.
  - THE DIFF MUST SHOW `is_same_status` IS NOT REASSIGNED, and must show the widened `_write_history_anyway` still carrying the `and not is_dup` term. Paste a grep for `is_same_status` across the function proving the only assignment is the original `old_status == norm_status...` one. This is the single most important line of evidence in the plan: the rejected implementation passes every behavioral assertion except idempotence (F-5).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_status_set.py -v -k untooled` showing all five cases passed; revert E-01 IN THE WORKTREE and paste cases (a) and (e) FAILING on the persisting `check.status-untooled` finding; restore.
  - ALSO paste case (d)'s actual record COUNT after the second setter run (it must be 1), and case (e)'s resulting file path under `not-executed/`. A statement that the count is one is not acceptable; paste the count.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `status-untooled` branch's `summary_fix` and `detailed_fix` strings BEFORE and AFTER, and the diff that reworded them. The "why they needed no change" alternative is REMOVED: review resolved the conditional and the edit is required (F-7).
  - ALSO paste the diff of `tests/test_doctor.py::test_remediation_status_untooled` showing the wording assertion updated and `assertIsNone(rem.command)` retained, plus that file's test run passing. A green `tests/test_doctor.py` without a diff to that test means `doctor.py` was not actually reworded.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the scratch-repo transcript: drift list before, the `aw set <status> <id6> --yes --no-commit` output and exit code, the newest history line, and the empty drift list after; paste the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the two-part argument with its code citations (finalize's target versus the plan's on-disk status; the pre-transition terminal refusal string), and the narrowed run of `tests/test_status_set.py` plus the lifecycle test module with their counts. Also paste the module-level import check showing no cycle exists.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OQ-01 IS ANSWERED AND THIS PLAN IS NO LONGER BLOCKED. The gate previously read "THIS PLAN IS BLOCKED ON ONE HUMAN DECISION AND MUST NOT BE APPROVED OR EXECUTED UNTIL IT IS ANSWERED" and cited "`OQ-01` (`- Blocking: yes`)", which CONTRADICTED OQ-01's own recorded state (`- Blocking: no`, `- Status: resolved`, maintainer chose option 2 on 2026-09-26). Corrected at review (F-8): the stale block notice is withdrawn, because a reader trusting it would refuse to approve a plan whose only blocker is already answered. The conditional retirement remains true and is retained: if the maintainer REVERSES to option (1) or (3), retire this plan as superseded rather than reworking it.

WHAT A HUMAN IS APPROVING. A behavior change in `aw set`/`aw ipd set` for plans only: re-applying the status a plan already has on disk, when the last commit had a different status, now records a real transition (`<status>` token, "status set to <status>", including an `approved` Approval line worded as a transition). A true re-assertion (HEAD equals disk) is unchanged. The checker is not relaxed. The duplicate-suppression behavior is PRESERVED, so running the command twice still writes one record (this was NOT true of the plan's original E-01 instruction; see F-5).

YOU ARE ALSO APPROVING A DIVERGENCE FROM THE SOURCE ITEM'S RECOMMENDATION, stated because the two documents disagree in the record. Backlog `mpghjn` recommended options (1) or (3) and described (2) as needing "a git read the setter does not do"; OQ-01 records the maintainer choosing (2) anyway when asked directly. The cost of (2) is exactly that git read, on the same-status plan path only. If the maintainer does not recall making that choice, do not approve: re-ask, because the whole plan is that answer (F-10).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above, which now include `tests/test_doctor.py` (F-6: an existing test pins the wording E-03 changes). Within `agent_workflows/status_set.py` only `apply_status_change`; within `agent_workflows/doctor.py` only the `status-untooled` branch of `build_remediation`; within `tests/test_doctor.py` only `test_remediation_status_untooled`. Expected to need NO edit, and named so reconciliation has something to check: `check_engine._has_matching_history_line` and `check_status_untooled` (including its drift-detail wording, which is already true once E-01 lands), `same_status_message_is_duplicate` (its behavior is RELIED ON, not changed), and `ipd_lifecycle` (E-05 shows the finalize caller is unaffected). Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). `doctor.py` must NOT be `--scope-ack`ed: E-03's conditional is resolved and the edit is required (F-7).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. THE CLAIM EASIEST TO FAKE HERE IS IDEMPOTENCE: a single run of the fix path looks correct under every other assertion in this plan while the rejected implementation silently duplicates history, so E-02 case (d) must paste the actual record COUNT after the second run, not a statement that it is one.

GENUINE STOP CONDITIONS: (1) if making the change requires `status_set` to import `check_engine` at module level and that creates an import cycle, stop and report rather than duplicating the blob/status readers (NOT expected to fire: measured at review, neither module imports the other at module level, and `status_set` already imports `check_engine` locally elsewhere); (2) if keeping `is_same_status` TRUE turns out to block the history write for a reason E-01's analysis missed, stop and report rather than falling back to `is_same_status = False`, which is the rejected shape that re-opens `1i300e`'s defect (F-5).

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `mpghjn` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
