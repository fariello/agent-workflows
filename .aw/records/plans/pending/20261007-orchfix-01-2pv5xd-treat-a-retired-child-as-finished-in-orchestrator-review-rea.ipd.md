# IPD: Treat a retired child as finished in orchestrator review readiness

- Date: 2026-10-07
- Kind: child
- Concern: Retiring a child plan (`aw ipd set superseded|not-executed <child>`) leaves its orchestrator unapprovable until a human edits the orchestrator's `## Child IPDs` table, and the refusal does not say so. Measured 2026-10-07: after `62pkkg` was retired `not-executed`, `aw set approved itamry` refused with `[child-status-not-ready] 62pkkg: child 62pkkg has status 'not-executed' (must be to-review, reviewed, approved, auto-approved, or executed)` and the remedy "bring the child to `to-review`", which is impossible for a retired plan and wrong advice. (Corrected at review 2026-10-08: the orchestrator is NOT permanently stuck. Demonstrated in a scratch repo through `review_readiness`: with the retired child's row present, `child-status-not-ready` fires; with that row removed from the table, condition 2 passes and only the coverage record remains to refresh. So the missing piece is a correct remedy, and whether a retired row may also stay in place is OQ-02.) The cause: `orchestrator_readiness._READY_CHILD_STATUSES` admits `executed` but not the two retirement statuses, although the runner's own retirement predicate already treats every `ipd_schema.TERMINAL` status as having ended a child's participation (`runner_shared` "Every child `Status:` that ENDS its participation in a Set", derived from `ipd_schema.TERMINAL`). Separately, nothing updates the orchestrator when a child is retired, so its `## Child IPDs` table and checklist keep naming the child as live work.
- Scope: (1) Make orchestrator review readiness treat a child under a retirement directory with `Status: superseded` or `not-executed` as finished, exactly as it treats `executed`, and say so in its finding text when such a child is present; (2) when `aw ipd set superseded|not-executed` retires a child, append a dated `## Workflow history` line to its orchestrator naming the retired child, and print a hint naming the orchestrator; (3) amend spec `25kzda` Section 2.5d condition 2 to match. EXCLUDES rewriting the orchestrator's child table or checklist automatically (prose a human or review owns), changing retirement or coverage rules, and the refusal-message styling owned by plan `juu1rj`.
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/status_set.py, tests/test_orchestrator_readiness.py, tests/test_orchestrator_child_retired.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: reviewed
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Spec: 25kzda
- Set: orchfix
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2pv5xd
- Readiness: no-go

## Workflow history
- 2026-10-08 reviewed (aw set): REVIEWED - OPEN QUESTIONS; see /plan-review record
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (HIGH, open: OQ-02 blocking, a retired row kept in place keeps a stale coverage pass current), PR-002..PR-008 fixed. Record: .aw/records/reviews/20261007-orchfix-01-2pv5xd-treat-a-retired-child-as-finished-in-orchestrator-review-rea.review.md Round 1.
- 2026-10-07 to-review (aw set): authored review-ready at the maintainer's request 2026-10-07

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Retiring a child plan never strands its orchestrator: the orchestrator stays approvable and retirable, and its own history says which child was retired and when.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: readiness

- [ ] E-01 In `agent_workflows/orchestrator_readiness.review_readiness`, treat a child whose `- Status:` is `superseded` or `not-executed` AND which sits in the matching terminal directory (`run_selection_policy.is_in_terminal_directory`) as ready without linting, the same way the `executed` branch does. Derive the accepted set from `ipd_schema.TERMINAL` rather than spelling the three statuses again, so it cannot drift from the runner's retirement predicate. A retirement status OUTSIDE its terminal directory stays a finding. "Matching" means the path contains the segment `/<status>/` (for example `/not-executed/` for `not-executed`), not merely any `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` member, so a `superseded` status under `not-executed/` or `reusable/` stays a finding.
  - GATED ON OQ-02 (blocking). As written this item accepts a retired child's row IN PLACE, which leaves the orchestrator's `- Coverage: pass` record current although that pass was given while the retired child was still counted as covering work (F-05). Execute this item only in the shape OQ-02's answer selects: option A adds the coverage-input change described there; option B replaces this item with "do not accept a retired row; route it to the remedy in E-02".
  - Depends on: none
  - Expected outcome: an orchestrator whose children are one `reviewed` and one `not-executed` (in `not-executed/`) is ready under the OQ-02 option chosen (under option A, only after its coverage record has been refreshed for the changed input); one with a `not-executed` status in `pending/` is not, and neither is one with `superseded` under `not-executed/`.
  - Execution state: pending

- [ ] E-02 Give a child in a terminal status its own finding code and remedy, and surface retired children as an informational note. (1) Add a new stable code, for example `CODE_CHILD_TERMINAL = "child-terminal-status"`, used whenever a child's status is in `ipd_schema.TERMINAL` but E-01 does not accept it, with its OWN `REMEDIES` entry. A distinct code is required, not a per-finding remedy string, because `runner_shared`'s continue-handoff builder re-reads the remedy BY CODE (`remedy = _orch_readiness.REMEDIES.get(rf.code, rf.remedy)`), so a context-specific `remedy=` on a `CODE_CHILD_STATUS` finding would be overwritten there with the to-review advice (F-07). The remedy text, per spec `r07vma` R7, states the invariant, forbids deleting the checklist, and names the legitimate edits: remove or reassign the retired child's row in the orchestrator's `## Child IPDs` table, assign any work it owned to another child by id6 or add a child for it, then run `aw ipd coverage <id6>`; for a terminal status in the wrong directory, re-run `aw ipd set <status> <child-id6>` so the file lands in its terminal directory. `REMEDY_CHILD_STATUS` keeps its current text for non-terminal statuses, which is correct for them and is pinned by `test_condition_2_child_status_draft`. (2) When at least one child is accepted as retired (only under OQ-02 option A), carry an informational note naming each such child on a new DEFAULTED trailing field of `ReviewReadiness` (for example `notes: tuple[str, ...] = ()`), rendered by `render_human` after the findings and by `render_agent` in its `data`, and never counted as a finding, so it never blocks. A trailing defaulted NamedTuple field is compatible with every existing constructor call; no caller unpacks the tuple positionally (checked at review). Plan `juu1rj` (approved) also edits `render_human`; add the note lines without changing its header or signature, so the two plans compose in either order.
  - Depends on: E-01
  - Expected outcome: a terminal-status child that is not accepted yields `child-terminal-status` with the new remedy on the human surface, in the agent record and in the runner continue-handoff text; a draft child still yields `child-status-not-ready` with the unchanged remedy; under option A the accepted case carries the note.
  - Execution state: pending

### Task group 2: retirement updates the orchestrator

- [ ] E-03 In `agent_workflows/status_set.run_set_command`, after `apply_status_change` has moved a plan to `superseded` or `not-executed`, find its Set's orchestrator with `runner_shared.read_set_membership` and, when the retired plan is a NON-orchestrator member of that Set (decide by membership and `SetMember.is_orchestrator`, not by `- Kind: child`, because legacy children carry no `Kind:` bullet), prepend `- <date> same-status (aw set): child <id6> retired <status>: <message>` under the orchestrator's `## Workflow history`. There is no reusable history-append function today: the insertion is inline in `apply_status_change` ("`new_lines.insert(i + 1, hist_entry)`"), so extract it into one private helper that both call, rather than writing a second copy. Add the orchestrator's path to `touched_paths` so `_offer_self_commit` commits both files together, and add it to the agent-mode `changes`. Emit the hint (orchestrator id6, and that its child table may need an edit, quoting the E-02 remedy) as a `term` line in human mode and as a `NextAction` in the agent/JSON `CommandResult`, never as a bare `print`, so `--agent` stdout stays one record. SKIP the write, and say so in the hint, when: the Set has no orchestrator; the orchestrator is itself terminal; the orchestrator is itself in this command's `matched_records` (a whole-Set retirement); or the orchestrator file has uncommitted changes in the worktree or index (`git status --porcelain -- <path>` non-empty), because committing it would sweep a co-worker's in-progress edits into this commit (AGENTS.md shared-checkout rule). Retiring two children of one Set in one command writes one line per child. The line is not a review record (`plan_readiness.is_review_history_entry` is False for a `same-status` middle) and history is outside the coverage fingerprint, so it changes no verdict and forces no re-probe.
  - Depends on: none
  - Expected outcome: retiring a child in a scratch repo leaves one new history line on its orchestrator, both files in one commit under `--commit`, and the hint on stdout (human) or in `next_actions` (agent); retiring a plan with no Set, or one whose orchestrator is dirty, changes the orchestrator not at all and the dirty case says why.
  - Execution state: pending

### Task group 3: spec and tests

- [ ] E-04 Amend spec `25kzda` Section 2.5d to match the OQ-02 answer and record it with `aw specs note`; the spec stays `approved`. Under option A: condition 2 reads that a child carrying `executed`, `superseded` or `not-executed` in its matching terminal directory is ready without being linted, AND Section 2.5e states how a retired row reaches the coverage input. Under option B: condition 2 keeps its status list and gains one sentence that a retired child's row is not ready and is resolved by editing the orchestrator's table. Either way the EVERY REFUSAL paragraph names the new `child-terminal-status` code.
  - Depends on: E-01, E-02
  - Expected outcome: Section 2.5d (and 2.5e under option A) describe exactly what the code does; `aw specs check` conforms.
  - Execution state: pending

- [ ] E-05 Add `tests/test_orchestrator_child_retired.py` and extend `tests/test_orchestrator_readiness.py` driving the real functions and `aw ipd set` in a scratch repo: retired child accepted; retired status in the wrong directory refused; the note and corrected remedy; retirement appends the orchestrator history line and commits both files; the dirty-orchestrator, whole-Set and no-Set skips; the agent-mode hint as a `next_action`; the runner continue-handoff text carrying the new remedy; then, under option A, `aw ipd set approved <orchestrator>` succeeds after `aw ipd coverage` refreshes the record and refuses while the pre-retirement record is still current (under option B, it succeeds after the row is removed). Every test drives real functions or the CLI and asserts on outputs, exit codes and files; no source introspection (AGENTS.md P16).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: both modules pass, and the bare suite adds no failure relative to the lane baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- One predicate, several consumers: `review_readiness` feeds `aw ipd set`, `aw ipd lint` (`IPD-S408`), `aw check plans` and the runner (spec `25kzda` 2.5d CONSUMERS), so one fix covers all of them.
- Spec edits are declared in `- Scope-Paths:` (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Review readiness refuses a retired child and prints impossible advice. | Session 2026-10-07: `aw set approved ...` printed `child 62pkkg has status 'not-executed' (must be to-review, reviewed, approved, auto-approved, or executed)` with "Remedy: bring the child to `to-review`". `orchestrator_readiness._READY_CHILD_STATUSES = frozenset({"to-review", "reviewed", "approved", "auto-approved", "executed"})`. |
| F-02 | The runner already treats every terminal status as finishing a child. | `runner_shared` set-retirement predicate docstring: "Every child `Status:` that ENDS its participation in a Set ... DERIVED from `ipd_schema.TERMINAL`"; `RETIRED_PLAN_STATUSES = frozenset({"superseded", "not-executed"})`. |
| F-03 | Spec 2.5d condition 2 lists only `executed` as the terminal ready status. | Spec `25kzda` Section 2.5d, condition 2. |
| F-04 | Retiring a child writes nothing to its orchestrator. | `status_set.run_set_command` moves and edits only the matched records. |
| F-05 | (review) The coverage probe counts a child listed in the table as COVERING the work assigned to it, whatever that child's status. | `runner_shared.PROBE_PROMPT_TEMPLATE`: "WORK ASSIGNED TO A NAMED CHILD IS COVERED ... a child listed in the `### Child IPDs table` section ... is COVERED and must not be quoted". The probe input is `child_table_rows` plus E-item text plus prose (`runner_shared` payload keys `child_table_rows`, `e_items`, `prose_sections`) and carries no child status, so retiring a child changes neither the input nor the fingerprint, and a `- Coverage: pass` recorded before retirement stays current. |
| F-06 | (review) Removing the retired child's row already clears condition 2 today. | Scratch-repo run of `review_readiness` (helpers from `tests/test_orchestrator_readiness.py`): with the row, `[('child-status-not-ready', 'chd002', "child chd002 has status 'not-executed' ..."), ('coverage-record-absent', ...)]`; with the row removed, only `coverage-record-absent`. |
| F-07 | (review) The runner re-derives a finding's remedy from its code. | `runner_shared` continue-handoff: `remedy = _orch_readiness.REMEDIES.get(rf.code, rf.remedy)`, so only a distinct code can carry a distinct remedy to that surface. |

## Proposed changes (ordered, validatable)

1. Accept retired children (E-01).
2. Note and corrected remedy (E-02).
3. Orchestrator history line on retirement (E-03).
4. Spec amendment (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- Rewriting the orchestrator's child table and checklist automatically. They are reviewed prose with reasons attached; a tool editing them would rewrite text a review signed off. The history line and hint make the edit visible; review owns it.
  - Carrier-Declined: no defect remains once a retired child no longer blocks readiness; the table edit is editorial.
- Refusal message styling and target-aware wording.
  - Carrier: juu1rj

## Scope check

- Over-scope: none. `orchestrator_readiness.py` E-01, E-02; `status_set.py` E-03; the spec E-04; tests E-05.
- Under-scope: corrected at review. The coverage input (F-05) was missed; under OQ-02 option A it must be added to `- Scope-Paths:` (`agent_workflows/runner_shared.py`) before execution, which is part of answering OQ-02. The dirty-orchestrator guard and agent-mode hint in E-03 were added.

## Required tests / validation

- `python3 -m pytest tests/test_orchestrator_readiness.py tests/test_orchestrator_child_retired.py tests/test_orchestrator_retirement.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit; record the failing node ids before and after, and the bar is an empty after-minus-before set.
- `aw ipd lint --phase pre-transition --agent <this plan>` conforming; `aw specs check` conforming; `aw sanitize --agent` exit 0.

## Spec / documentation sync

THIS PLAN AMENDS spec `25kzda` Section 2.5d condition 2, declared in `- Scope-Paths:`. Why: the condition contradicts the runner's own retirement predicate (F-02), and every consumer of `review_readiness` is reviewed against that text.

## Open questions

### OQ-01: Should a retired child also stop counting toward the orchestrator's coverage question?

- Blocking: no
- Status: resolved
- Owner: reviewer (opencode its_direct/pt3-claude-opus-5.5-1m-us)
- Resolution or deferral rationale: CORRECTED AT REVIEW 2026-10-08. The original answer ("any work assigned only to it already reads as uncovered") is false: the probe treats work assigned to any child listed in the table as covered and is never told the child's status, and retiring the child changes neither the probe input nor the fingerprint (F-05). So a retired child's row keeps counting as coverage. What to do about that is a design decision with a safety consequence, raised as OQ-02.

### OQ-02: May a retired child's row stay in the orchestrator's table and count as ready, and if so how does coverage learn of the retirement?

- Blocking: yes
- Finding: PR-001
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN. E-01 as authored makes a retired row ready in place. Combined with F-05, an orchestrator whose `- Coverage: pass` was recorded while the child was live stays approvable, and the runner can retire it to `executed`, while work assigned only to the retired child was never performed: the lost-work case the coverage gate exists to stop. Two bounded options. A: keep E-01 and add the child's terminal status to the coverage input for retired rows only (for example annotating the row in `child_table_rows`' probe payload and telling the probe a retired child covers nothing), which changes the fingerprint of only the affected orchestrators and forces one re-probe for each; adds `runner_shared.py` to scope and amends spec 2.5e. B: drop E-01's acceptance; a retired row stays a finding with the E-02 remedy (remove or reassign the row, reassign its work, re-run coverage), which is how the orchestrator becomes approvable today (F-06), and the spec's condition 2 list stays. Reviewer leaning: B. It is smaller, it changes no LLM-gate input, and it makes the human look at the work the retired child owned. The plan's original H1 ("... and drop it from the child table") suggests the maintainer may have wanted a table edit, which B asks a human to make and the Scope excludes automating.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` (or scratch-script) session printing `review_readiness(...).ready` and each finding's `(code, subject)` for: the accepted case under the chosen OQ-02 option (under A, both before and after `aw ipd coverage` refreshes the record); `not-executed` under `pending/`; and `superseded` under `not-executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `render_human` and `render_agent` output for a terminal-status child that is not accepted, showing `child-terminal-status` and the new remedy; the remedy as it appears in the runner continue-handoff text built from the same finding; a draft child still showing `child-status-not-ready` with the unchanged remedy; and, under option A, the rendered note.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: in a scratch repo, paste the orchestrator's new history line, `git show --stat HEAD` listing both files after `aw ipd set not-executed <child> --commit`, and the human hint line; the `--agent --yes` record showing the hint in `next_actions` and stdout parsing as one JSON record; and the three skip cases (no Set, dirty orchestrator, whole-Set retirement) each leaving the orchestrator byte-unchanged, with `git diff` empty for it and the hint saying why.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the spec diff (Section 2.5d, and 2.5e under option A), the new workflow-history line written by `aw specs note`, and the `aw specs check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_orchestrator_readiness.py tests/test_orchestrator_child_retired.py tests/test_orchestrator_retirement.py` with per-test counts, the bare `python3 -m pytest` summary line, and the before and after failing node-id sets showing nothing new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution, and OQ-02 (blocking) must be answered first; the answer decides the shape of E-01, E-02's note and E-04, and under option A adds `agent_workflows/runner_shared.py` to `- Scope-Paths:`.

Execution contract: commit only the Scope-Paths through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. This is a shared checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`. Paste the ACTUAL runner output into each V-item; a summary you did not produce is not evidence. The Scope-Paths are a declaration: an out-of-scope edit that turns out necessary is made and then justified with `--scope-reason` at finalize, not a reason to stop. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every V-item carries observed evidence. Under `aw oc run` / `aw agy run` the RUNNER owns the terminal transition, so do not run `aw ipd finalize` yourself; a hand execution runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-edit `- Status:` and never `git mv` into `executed/`.
