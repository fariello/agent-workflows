# IPD: Make the status-untooled remediation clear its own finding by writing a genuine transition record

- Date: 2026-09-26
- Kind: child
- Concern: `check.status-untooled` tells an operator who hand-edited a plan's `- Status:` to run `aw set <status> <id6>`, but that command can never clear the finding. The file on disk already carries the target status, so `status_set.apply_status_change` sees `old == target` and writes a `same-status` history token (or nothing at all when no `--message` is given), while `check_engine._has_matching_history_line` accepts only a token equal to the new status. Reproduced at HEAD `61ef21d8` in a scratch repo: hand-edit `to-review` -> `reviewed`, stage, `check_status_untooled` fires; `aw set reviewed aaa111 --yes --no-commit` reports `unchanged` and writes nothing; with `--message fix` it writes `- 2026-09-26 same-status (aw set): fix`; the finding persists in both cases.
- Scope: IN: in `status_set.apply_status_change`, when the target equals the on-disk status AND the record is a plan whose HEAD blob status differs, treat the change as a genuine transition from the HEAD status (write a `<status>` history token and the transition's default message); outcome tests; doctor remediation text only if 6k7xot left it claiming the one-command fix cannot work. OUT: relaxing `check_engine._has_matching_history_line`; non-plan record types; the approval-floor rules.
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py, agent_workflows/doctor.py
- Item-Dependencies: executed:6k7xot
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: mpghjn
- Blocks-Release: next
- Set: doctorhint
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9aqrzu

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mpghjn: implement option 2 (setter writes a genuine transition record when HEAD status differs); blocked on maintainer choice among three fixes (OQ-01).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Running the command `check.status-untooled` recommends clears the finding, while a true re-assertion of an unchanged status still writes only a `same-status` record and the checker stays strict.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: setter writes a genuine record for an untooled status

- [ ] E-01 In `status_set.apply_status_change`, after `is_same_status` is computed: if `is_same_status` and `rec.record_type == "plans"`, read the plan's status at HEAD (repo-relative path of `rec.path`; `check_engine._blob_text(repo_root, "HEAD", rel)` then `check_engine._status_meta(...)`, imported locally as `status_set` already does for `check_engine` elsewhere, or an equivalent single `git show HEAD:<rel>`). Only on this path, and only when git succeeds and yields a status that DIFFERS from the target, set `is_same_status = False`, `status_tag = norm_status`, `default_message = f"status set to {norm_status}"`. Because the file content may not otherwise change, the early `if not content_changed and not path_changed and not _write_history_anyway: return` would skip the history write: make that return also not fire when this untooled-transition path was taken. On any git failure (not a repo, path untracked at HEAD, blob has no status), keep today's same-status behavior. Do not change the approval-line or gate-field logic beyond what `is_same_status = False` already implies; record in the plan's finalize notes what the `approved` target writes (measured today: a same-status `approved` call writes `- Approval: <date>, recorded via aw ipd set: status unchanged (approved)`; after the change it should read `status set to approved`).
  - Depends on: none
  - Expected outcome: `aw set <status> <id6>` on a staged hand-edited plan writes `- <date> <status> (aw set): status set to <status>`.
  - Execution state: pending

- [ ] E-02 Add outcome tests to `tests/test_status_set.py` in a new class using a real temp git repo (init, config user, commit a plan at `to-review` with `Work-Kind`/`Priority`, `## Workflow history`): (a) hand-edit `- Status:` to `reviewed`, `git add`, assert `check_engine.check_status_untooled(repo)` reports `check.status-untooled`; run the setter for `reviewed` (via `status_set.run_set_command` with the same args the CLI builds, or `support.run_cli("set", "reviewed", "<id6>", "--yes", "--no-commit", cwd=repo)`); `git add`; assert the finding is gone and the newest history record's status token is `reviewed`. (b) True same-status: commit the plan at `reviewed` (HEAD == staged), run `aw set reviewed <id6> --message note`, assert the newest record's token is `same-status`. (c) Outside git (plain temp dir, no repo): same-status behavior unchanged. Outcomes only: assert findings and written history tokens, never source text.
  - Depends on: E-01
  - Expected outcome: three cases pass; (a) fails against the pre-change setter.
  - Execution state: pending

- [ ] E-03 Doctor text: read the `status-untooled` branch of `doctor.build_remediation` as 6k7xot left it. If its `summary_fix`/`detailed_fix` states or implies that `aw set <status> <id6>` cannot clear the finding (for example "the one-command fix does not work", or that reverting first is REQUIRED), reword it to say the finding clears with `aw ipd set <status> <id6>` (or `aw set`), keeping `command=None` (the id6 is still not derivable from the Drift in every case). If it only describes the revert-then-set recovery as one valid option without claiming the direct command fails, leave `doctor.py` unchanged and `--scope-ack` it at finalize.
  - Depends on: E-01
  - Expected outcome: no doctor text contradicts the fixed behavior.
  - Execution state: pending

- [ ] E-04 Reproduce end to end in a scratch repo (the Concern's recipe) and run the bare suite.
  - Depends on: E-02, E-03
  - Expected outcome: drift before; exit 0 and drift gone after; bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine.check_status_untooled` is commit-scoped: it compares the staged blob (`:0:`) with HEAD and only examines plans whose status changed in the commit.
- `status_set.apply_status_change` owns history writing; `same_status_message_is_duplicate` dedups same-status records (plans `vhbvwz`, `1i300e`).
- `check_status_untooled`'s docstring records an accepted efficacy ceiling: a hand edit that also writes a plausible history line is not caught. Option 2 does not move that ceiling.
- Tests assert OUTCOMES only (maintainer rule).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8` in a scratch repo (plan `aaa111`, committed `to-review`, hand-edited to `reviewed`, staged).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `status_set.apply_status_change` | With no `--message`, the recommended command writes NOTHING (reports `unchanged`), so the finding cannot clear. | `aw set reviewed aaa111 --yes --no-commit` -> `plan 20260926-demo-01-aaa111 [low] unchanged`; `check_status_untooled` still `['check.status-untooled']` |
| F-2 | MED | same | With `--message`, it writes a `same-status` record the checker rejects. | `- 2026-09-26 same-status (aw set): fix`; drift persists |
| F-3 | INFO | approval target | A same-status `approved` call writes an `- Approval:` line whose text says `status unchanged (approved)`. | scratch repo, hand-edit `reviewed` -> `approved`, `aw set approved aaa111 --yes --no-commit` |
| F-4 | INFO | backlog mpghjn | The item's reproduction says the command "exit 0 ... history written: same-status"; that is the `--message` case (F-2). Without a message nothing is written (F-1). Both leave the finding. | F-1, F-2 |

## Proposed changes (ordered, validatable)

1. E-01: untooled-transition path in the setter.
2. E-02: outcome tests.
3. E-03: doctor text, conditionally.
4. E-04: end-to-end reproduction; bare suite.

## Deferred / out of scope (with reason)

- Specs and backlog items with hand-edited statuses: `check_status_untooled` examines plans only.
  - Carrier-Declined: no checker fires for those types, so there is nothing to clear.

## Scope check

- Over-scope: none. `doctor.py` is declared because E-03 may edit it; it is acked if not.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_status_set.py -v -k untooled`; the scratch-repo reproduction; bare suite. Test rule: outcomes only.

## Spec / documentation sync

N/A: no `.spec.md` specifies the same-status tag; AGENTS.md says `aw set` records history on every transition, which this makes true for the untooled case.

## Open questions

### OQ-01: Which of the three fixes should be used?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-26 BY THE MAINTAINER, who chose option 2 when asked directly (the agent had first resolved it from repository evidence; the maintainer confirmed). Supporting evidence: `check_engine._has_matching_history_line`'s docstring records an accepted efficacy ceiling of catching the careless hand-edit, and option 1 would let exactly that case pass after one no-op command, lowering the ceiling the rule was built to hold; option 3 leaves the remediation `aw doctor` prints permanently unable to work, which is the defect itself. Option 2 keeps the checker strict and makes the printed fix work, at the cost of one git read on the same-status path only, and is reversible. This plan implements option 2 because it keeps the checker strict. The three options, in plain words: (1) TEACH THE CHECKER to accept a `same-status` record as proof the status was tool-applied. Smallest change, but it weakens the check: a hand edit followed by any no-op `aw set` would pass. (2) MAKE THE SETTER NOTICE the hand edit: when you ask `aw set` for the status the file already has, but the last commit had a different status, record it as a real transition (`<status>` token). The checker stays strict; the cost is one `git show HEAD:<path>` on that one path only. (3) CHANGE ONLY THE ADVICE: tell operators to undo the hand edit and then run `aw set`. No code change, but the one-command fix stays impossible. RECOMMENDATION: option 2. If the maintainer picks (1) or (3), this plan is superseded and a new one written.
- Carrier: mpghjn

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `apply_status_change`; state which code path now runs `git show` and paste a grep showing it is inside the `is_same_status and record_type == "plans"` branch only.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_status_set.py -v -k untooled` showing the three cases passed; revert E-01 IN THE WORKTREE and paste case (a) FAILING on the persisting `check.status-untooled` finding; restore.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `status-untooled` branch's `summary_fix` and `detailed_fix` strings as found after 6k7xot, and either the diff that reworded them or the sentence stating why they needed no change.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the scratch-repo transcript: drift list before, the `aw set <status> <id6> --yes --no-commit` output and exit code, the newest history line, and the empty drift list after; paste the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS BLOCKED ON ONE HUMAN DECISION AND MUST NOT BE APPROVED OR EXECUTED UNTIL IT IS ANSWERED. `OQ-01` (`- Blocking: yes`) asks the maintainer to choose among three fixes; the plan implements option 2. If (1) or (3) is chosen, retire this plan as superseded.

WHAT A HUMAN IS APPROVING once OQ-01 is answered with option 2. A behavior change in `aw set`/`aw ipd set` for plans only: re-applying the status a plan already has on disk, when the last commit had a different status, now records a real transition (`<status>` token, "status set to <status>", including an `approved` Approval line worded as a transition). A true re-assertion (HEAD equals disk) is unchanged. The checker is not relaxed.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if making the change requires `status_set` to import `check_engine` at module level and that creates an import cycle, stop and report rather than duplicating the blob/status readers.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `mpghjn` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
