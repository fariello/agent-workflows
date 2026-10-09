# IPD: Let an agent propose a gate, tool or approach change and land that one record on main

- Date: 2026-10-07
- Kind: child
- Concern: When an executing agent concludes it cannot finish without a gate, an `aw` tool or the approach changing, nothing durable captures that. Measured 2026-10-07: the outcome file's `defect_report` findings carry only `what`/`where`, are stored in the gitignored run directory, and nothing reads them (`runner_shared.defect_report_record` docstring admits the reader "is unscoped"); an agent told to run `aw backlog new` produces an item that reaches main only if the lane merges, and in the stuck case the lane usually does not. So the maintainer cannot see the proposal and the agent has no sanctioned alternative to editing the gate itself.
- Scope: Add a structured `proposal` field to the execute outcome file; have the runner validate it and file it as a tracked record (a pending plan for a small fix with no behavior change, a backlog item for everything else) on main through a coordinator worktree, independent of whether the lane merges; then stop that item as `needs-human` with dependents skipped and independent items continuing; and surface it in the run summary. EXCLUDES the fix-it message text (Order 03), every new retry class (Orders 04 to 07), and spec `6kwd2e`'s mid-run question pause.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_run_proposal_channel.py, CHANGELOG.md
- Item-Dependencies: executed:tb6lw3
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tha7a6
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. E-03 named a gate answer (`needs-human`) and a nonexistent status (`dependency-not-met`) as item statuses: now `fail-gate` + `awaiting-human-decision` refusal + `NEEDS_INPUT_KEY` (exit 3), dependents via `cascade_dependency_blocked`; E-02 now takes `integration_lock` (the cited performer does not); untrusted proposal text bounded, path-validated and front-matter-neutralized; scaffold/backlog arguments and draft placeholders specified; Blocks-Release inheritance corrected to the AGENTS.md rule; tests on both hosts; CHANGELOG split to E-06; gate contract added. Review record `.aw/records/reviews/20261007-fixfirst-02-tha7a6-let-an-agent-propose-a-gate-tool-or-approach-change-and-land.review.md`.
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An agent that believes a gate, tool or approach must change can say so in its outcome file, and the runner turns that into a tracked plan or backlog item on main that the maintainer sees in `aw attention`, without the agent being authorized to make the change and without dirtying main.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the field and its validation

- [ ] E-01 In `agent_workflows/runner_shared.py`, define the outcome-file `proposal` field and a pure validator beside `validate_defect_report`. Shape: `{"kind": "gate-change" | "tool-defect" | "different-approach", "blocked_by": <what refused or failed, verbatim>, "why": <why the cause cannot be fixed within scope>, "proposed_change": <what should change>, "paths": [<repo-relative paths it would touch>], "size": "small" | "material"}`. The validator never raises, returns a verdict naming each missing or malformed key, and treats an absent field as "no proposal". Add the field to the execute prompt's outcome schema next to `defect_report`.
  - Depends on: none
  BOUND AND SANITIZE, because the field is UNTRUSTED agent text that the runner will write into a tracked record on main (the same posture AGENTS.md requires for inbox and inter-agent payloads). The validator must: cap each string key's length (state the cap; one screen, e.g. 2000 characters for `why`/`proposed_change`, 500 for `blocked_by`) and mark a longer value malformed rather than truncating silently; reject `kind`/`size` values outside the enums; require every `paths` entry to be a repo-relative path with no `..` segment, no leading `/`, and no glob, and mark the proposal malformed otherwise; and expose a sanitized form in which any line that would parse as a front-matter bullet (a line starting `- ` followed by `<Key>:`, e.g. `- Status:`, `- Readiness:`, `- Id:`, `- Blocks-Release:`) is neutralized (for example indented or quoted) so the proposal text can never set a field on the record it lands in.
  - Expected outcome: a valid proposal, a malformed one (each of: missing key, bad enum, over-length string, `..` path, absolute path) and an absent one each return the documented verdict; a valid proposal whose `why` contains `- Status: approved` yields sanitized text in which that line is not a front-matter bullet; the execute prompt names the field and its keys.
  - Execution state: pending

### Task group 2: land the record on main without the lane

- [ ] E-02 Add a coordinator performer that files a valid proposal as ONE tracked record on main, reusing the shape of `perform_coordinator_backlog_close`: a throwaway worktree cut from main's current tip, the record written by the real tool (`aw backlog new ... --apply`, or `aw ipd scaffold` plus the proposal text for `size: small`), committed there with hooks running, and published with `git merge --ff-only` (`ipd_lifecycle.land_worktree_commit`, as that function does). `perform_coordinator_backlog_close` does NOT take the repository integration lock; this performer MUST, by wrapping the build-commit-land attempt in `runner_shared.integration_lock` (re-resolving main's tip INSIDE the lock, as `integrate_under_repository_lock` does), so it cannot race this driver's or a peer driver's lane publish. A lock timeout is treated as a refused publish (below), never as permission to write without it. Bound the raced-tip retries as that function does. On a refused or exhausted publish, keep the record in the run directory and say so in the summary rather than writing to main any other way.
  CLASSIFY BY SIZE: `small` becomes a pending plan in its own Set with `Status: draft` (a human must review it; the runner never authors a `to-review` plan on an agent's say-so); everything else becomes an `open` backlog item. The runner cannot verify "no behavior change", so `small` is only the agent's claim and the draft status is what keeps it honest. Supply every argument the tools require rather than leaving placeholders the runner cannot resolve: `aw backlog new --summary --priority --work-kind --apply` (priority and work-kind inherited from the proposing item); `aw ipd scaffold --set <new setid> --order 1 --title --priority --work-kind --apply`, then append the sanitized proposal text (E-01) as the plan's body. A scaffolded draft keeps its `TODO` and `Item-Dependencies: unresolved` placeholders; that is correct for a draft and must not be "completed" by the runner. Both records carry the run id, the item id6, the kept lane branch, and the SANITIZED `blocked_by`, all as body text and never as front-matter fields the runner invents. RELEASE GATE: when the proposing item carries `- Blocks-Release:`, pass the same value (`--blocks-release`); when the new record's work-kind is `bug` and the item carries no gate, pass `--blocks-release next` (AGENTS.md "Every live bug gates the next release"). Write NOTHING the runner did not validate: `paths` are recorded as text, never added to any `Scope-Paths:`.
  - Depends on: E-01
  - Expected outcome: in a scratch repo, a proposal from an item whose lane is NOT merged lands as exactly one commit on main containing exactly one new record; `aw check` reports no `error` for that record (draft placeholders are advisory); main's worktree is clean afterwards; a raced tip is rebuilt; a held integration lock makes the publish wait and, on timeout, refuse; a refused publish leaves main untouched and the record in the run directory; an injected `- Status: approved` line in `why` does not change the record's `- Status:`.
  - Execution state: pending

### Task group 3: stop the item, continue the run

- [ ] E-03 When the outcome carries a valid proposal, or when a fix-it budget is exhausted and the last turn carried one, stop the item WITHOUT a new status token. `needs-human` is a GATE ANSWER (`runner_shared.GATE_ANSWER_NEEDS_HUMAN`), not an item status, and `runner_shutdown.KNOWN_ITEM_STATUSES` is closed. So, mirroring the shipped integration-gate `needs-human` path in `execute_item_core`: set a refusing terminal status from the existing vocabulary (`fail-gate`, stated in the code with its reason), record the stop through `render_stream.record_refusal` with code `GATE_ANSWER_NEEDS_HUMAN_CODE` (`awaiting-human-decision`) and a remedy naming the filed record's id6 and path, AND set `NEEDS_INPUT_KEY` on the queue entry so `run_exit_code` reports exit 3 (human input required) rather than 1. Keep its lane branch, let `cascade_dependency_blocked` mark its dependents with the runner's existing `dependency-blocked`/`fail-depend` status (the runner has no `dependency-not-met` status; do not invent one), and continue independent items. Do NOT integrate the lane. If the proposal could not be filed (E-02 refused), the remedy says so and names the run-directory copy.
  - Depends on: E-02
  - Expected outcome: a three-item run where item A proposes, C depends on A, and B is independent ends with A `fail-gate` carrying an `awaiting-human-decision` refusal and `needs_input` set, C dependency-blocked with no session, B executed, the run exiting 3, A's lane branch present, A's lane commits absent from main, and the proposal record present on main.
  - Execution state: pending

- [ ] E-04 Surface proposals in the run summary on both hosts: list each first, with the record's path and id6, `blocked_by`, and the command to view it. Wire it in `render_stream` beside the existing `awaiting-human-decision` remedy.
  - Depends on: E-03
  - Expected outcome: the end-of-run summary for the E-03 run names the proposal record path and id6 at the top.
  - Execution state: pending

### Task group 4: tests and changelog

- [ ] E-05 Add `tests/test_run_proposal_channel.py` driving the real runner with a scripted host (the `fake_opencode` pattern in `tests/test_silent_turn_observability.py`) on BOTH `aw oc run` and `aw agy run` for: a valid `material` proposal (backlog item on main), a valid `small` proposal (draft plan on main), a malformed proposal (no record, item handled as today), an injection attempt (front-matter line in `why`; record status unchanged), a raced tip, a held integration lock, and the three-item continuation of E-03. No source introspection (no `inspect`, `ast`, or reading production source).
  - Depends on: E-04
  - Expected outcome: the module passes; each case asserts on files on main, git log, item status and summary text.
  - Execution state: pending

- [ ] E-06 Add a `CHANGELOG.md` entry (user-facing prose: no em or en dashes) stating that an agent can now propose a gate, tool or approach change, that the runner files it as a draft plan or open backlog item on main, and that the proposing item stops for a human decision while the run continues.
  - Depends on: E-04
  - Expected outcome: one new entry under the unreleased section.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Coordinator writes to main go through a throwaway worktree and `--ff-only` (`perform_coordinator_backlog_close`, `ipd_lifecycle._finalize_transaction`), never into the shared checkout.
- `runner_shutdown.KNOWN_ITEM_STATUSES` is closed; reuse a token rather than invent one.
- Tests drive the runner and assert on outcomes (GUIDING_PRINCIPLES P16).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Existing problem reports have no durable home and no reader. | `runner_shared.defect_report_record` stores into the queue item; `.aw/.gitignore` ignores run directories; no reader in `run_viewer`, `render_stream`, `attention` or `run_cli` (survey 2026-10-07). |
| F-02 | A mechanism already lands one record on main atomically, independent of the lane, which answers the maintainer's question "use the same lane but merge just the record". | `runner_shared.perform_coordinator_backlog_close`: writes in a coordinator worktree, commits with hooks, publishes with `git merge --ff-only`, classifies OK / REFUSED / RACED. Merging only part of the LANE branch is not possible without cherry-picking a lane commit whose parent is unmerged work, so the record is written fresh on main's tip instead. |
| F-03 | An agent-filed backlog item is stranded when its lane does not merge. | Backlog paths are outside the scope allowlist and ride only an integrated lane (survey 2026-10-07; example `p9ag41` reached main only because its lane merged). |
| F-04 | `needs-human` already exists as a gate answer with a render code and a summary remedy. | `runner_shared.GATE_ANSWER_NEEDS_HUMAN`; `render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE = "awaiting-human-decision"`. |
| F-05 | Maintainer ruling 2026-10-07: a small fix with no material functional impact becomes a plan; everything else a backlog item; the item stops needs-human and the run continues. | Session 2026-10-07. |

| F-06 | (review) `needs-human` is a gate answer, not an item status; the shipped `needs-human` path records a refusal with `awaiting-human-decision` on an existing status, and the runner's dependent status is `dependency-blocked`, not `dependency-not-met`. | `runner_shared.GATE_ANSWERS` docstring; `runner_shutdown.KNOWN_ITEM_STATUSES` (no `needs-human`); `execute_item_core` integration-gate branch `record_refusal(item, code=GATE_ANSWER_NEEDS_HUMAN_CODE, ...)`; `cascade_dependency_blocked` "It does NOT introduce `dependency-not-met`"; `NEEDS_INPUT_KEY` comment "a human-gated run now emits 3 rather than 1". |
| F-07 | (review) The cited coordinator performer does not take the repository integration lock. | `perform_coordinator_backlog_close` uses `commit_lock.coordinator_worktree` and `ipd_lifecycle.land_worktree_commit` only; `integrate_under_repository_lock` is where `integration_lock` is taken. |
| F-08 | (review) `aw ipd scaffold` requires `--set`, `--order`, `--priority` and writes `Item-Dependencies: unresolved` and `TODO` placeholders into a `draft`. | `ipd_authoring.build_skeleton` "- Status: draft", "- Item-Dependencies: unresolved", "- Scope-Paths: TODO". |

## Proposed changes (ordered, validatable)

1. Field and validator (E-01).
2. Coordinator performer landing one record on main (E-02).
3. `needs-human` stop with continuation (E-03).
4. Summary surfacing (E-04).
5. Tests on both hosts (E-05).
6. Changelog (E-06).

## Deferred / out of scope (with reason)

- Pausing a run to ask a human mid-run. That is spec `6kwd2e`; this plan stops one item and continues.
  - Carrier-Declined: spec `6kwd2e` is itself the carrier; nothing here defers its work.

## Scope check

- Over-scope: none. `runner_shared.py` by E-01 to E-03, both host modules by E-03 (re-export and wiring), `render_stream.py` by E-04, the test module by E-05, `CHANGELOG.md` by E-06.
- Scope fence: `- Scope-Paths:` is a declaration. If execution genuinely needs another file, edit it and justify it at finalize (`--scope-reason`); acknowledge a declared but unmodified path with `--scope-ack`.
- Under-scope: the message that tells agents to use this field is Order 03.

## Required tests / validation

- `python3 -m pytest tests/test_run_proposal_channel.py -o addopts=""`.
- Bare `python3 -m pytest`, with the failing node IDs recorded in the lane before any edit and compared after (review measured `6625 passed, 2 skipped` at HEAD `383ebc1ee`; re-derive).
- `aw check` on the scratch repo after a proposal lands (no `error` on the new record).

## Spec / documentation sync

Spec `25kzda` group (b) "agent proposal" is written by Order 01; this plan implements it and edits no spec. `CHANGELOG.md` records the user-visible effect.

## Open questions

### OQ-01: Should a `small` proposal land as `draft` or `to-review`?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: `draft`. A `to-review` plan must be review-ready (AGENTS.md), and the runner cannot vouch for an agent's proposal text; `draft` keeps a human in the loop and costs one `aw ipd set to-review`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session showing the validator's verdict for a valid, an absent, and each malformed case (missing key, bad enum, over-length, `..` path, absolute path), the sanitized text for a `why` containing `- Status: approved`, and the execute-prompt excerpt naming the field.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the scratch-repo transcript: `git log --oneline -2`, `git show --stat HEAD` (one new file) and `git status --short` on main after a proposal from an unmerged lane; the new record's front matter showing its `- Status:` and inherited `- Blocks-Release:`; `aw check` output on the scratch repo; and the raced, held-lock and refused cases with main's tip before and after each.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the three-item run's final item statuses and A's recorded refusal (code and remedy), the run's exit code, `git branch --list 'aw/lane/*'`, and `git branch --contains <A's lane tip>` showing main is not listed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the end-of-run summary text showing the proposal first.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module run with per-test counts (both hosts visible in the test ids), and the bare-suite summary line with before and after failing node IDs.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `CHANGELOG.md` diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Execute only after `tb6lw3` has executed (`- Item-Dependencies:`).

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push. Tests that publish to main do so in a scratch repo only, never in this checkout.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
