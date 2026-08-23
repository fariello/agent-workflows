# IPD: Fix agy_run.py False-ERROR on Sandboxed write_to_file Rejection

- Date: 2026-08-22
- Kind: child
- Concern: `agy_run.py` reports a turn as ERROR when Antigravity rejects a sandboxed `write_to_file` even though the intended write already landed via `run_command` and the work committed, making agy status untrustworthy.
- Scope: The turn-status classification in `tools/agy_run.py` and the execution/audit steering prompts under `tools/awphysical/`; no change to what the agent actually does to the repo.
- Status: draft
- Set: highpbacklog0822
- Order: 2
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: n5kvff

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog uhbdt1; false-ERROR observed executing backlog-medhigh-260819 Orders 01 + 07 (both ERROR-but-complete).

## Goal

Make agy turn status trustworthy: a benign, expected `write_to_file` rejection on a target-repo path (which Antigravity sandboxes to its brain dir) must not turn a successful, committed turn into ERROR.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Steer the agent away from the rejected path

- [ ] E-01 In the execution and audit preambles under `tools/awphysical/` (`agy-execution-preamble.md`, `agy-self-audit-prompt.md`, and the general variants), add an explicit instruction: write target-repo files via `run_command` ONLY; never call `write_to_file` on a target-repo path (it is sandboxed to the brain dir and will be rejected).
  - Depends on: none
  - Expected outcome: Gemini stops issuing the redundant `write_to_file` on repo paths, so the rejection stops occurring at the source.
  - Execution state: pending

### Material change 2: Treat the expected rejection as non-fatal

- [ ] E-02 In `tools/agy_run.py`, before `run_agy()` raises `ScriptError` on a non-SUCCESS terminal status (around `tools/agy_run.py:613-619`), classify a terminal status whose only failure is a `write_to_file` rejection on a target-repo path as NON-fatal when the run otherwise completed (exit 0 and the intended write is present), and downgrade it to SUCCESS-with-warning rather than ERROR.
  - Depends on: none
  - Expected outcome: an otherwise-successful turn whose sole error is the sandboxed `write_to_file` rejection reports SUCCESS (with a logged warning), not ERROR.
  - Execution state: pending

### Material change 3: Surface the downgrade honestly

- [ ] E-03 Emit a clear, non-silent warning when the downgrade in E-02 fires (which path was rejected, why it is benign, that the write landed via `run_command`), so the status change is auditable and a genuine `write_to_file` failure on a non-repo path is NOT downgraded.
  - Depends on: E-02
  - Expected outcome: the downgrade is logged and narrowly scoped; unrelated tool failures still surface as ERROR.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The runner is `tools/agy_run.py`; `tools/watch-agy.py` is only a log tailer.
- Steering prompts are durable markdown under `tools/awphysical/` loaded at `tools/agy_run.py:48-54` and assembled by `build_turn1_prompt()` (`:631-651`) / `build_turn2_prompt()` (`:653-670`).
- `run_agy()` raises `ScriptError` whenever `returncode != 0 or status != "SUCCESS"` (`tools/agy_run.py:615`); step ERROR mapping is `_progress_messages()` (`:483-488`, `"ERROR": "failed"`); terminal status parsed at `:466-473`, `:604-605`, `:613`.
- There is currently NO handling that distinguishes a benign/expected tool-call rejection from a genuine failure.

## Findings

Antigravity sandboxes `write_to_file` to its brain dir and rejects target-repo paths. Gemini correctly writes repo files via `run_command` but ALSO attempts `write_to_file` on the same path; the rejection makes the terminal status non-SUCCESS, and `run_agy` (`tools/agy_run.py:615`) turns any non-SUCCESS into a fatal ERROR (exit 0 but ERROR status), even though the work succeeded and committed. Two complementary fixes (prevent at the source + downgrade the benign case) make status trustworthy and are individually safe.

## Proposed changes (ordered, validatable)

1. Prompt steer: repo files via `run_command` only (E-01).
2. Narrow non-fatal classification of the sandboxed `write_to_file`-path rejection in `run_agy` (E-02).
3. A visible warning on downgrade, keeping genuine failures fatal (E-03).

The two fixes are belt-and-suspenders: E-01 stops the rejection occurring; E-02/E-03 make the runner robust if it still does.

## Deferred / out of scope (with reason)

- Replacing Antigravity's native tool sandbox or its `write_to_file` semantics: not ours to change.
- Broader agy status-model refactor: out of scope; this fix is narrow to the false-ERROR path.

## Scope check

- Over-scope: none.
- Under-scope: ensure the downgrade is keyed specifically to a target-repo-path `write_to_file` rejection, not any tool rejection, so real failures still fail.

## Required tests / validation

Add a unit test that feeds `run_agy`'s status-classification a synthetic terminal event representing a `write_to_file`-repo-path rejection with an otherwise-successful, committed run, and asserts SUCCESS-with-warning (not ERROR); and a companion test that a genuine tool failure (or a `write_to_file` failure on a non-repo path) still classifies as ERROR. Run the existing agy/tools test suite. Paste the actual test output.

## Spec / documentation sync

Update any agy runbook/preamble docs under `tools/awphysical/` to state the "repo writes via run_command only" rule; note the benign-rejection downgrade where the status model is documented.

## Open questions

### OQ-01: Do the two fixes both ship, or is the prompt steer alone sufficient?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: ship BOTH. The prompt steer (E-01) is best-effort (models may still emit the redundant call); the runner downgrade (E-02/E-03) is the robust guarantee. The backlog item explicitly offers both as the fix.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the four preamble files under `tools/awphysical/` contain the explicit "repo files via run_command only; never write_to_file on a target-repo path" instruction; quote the added lines.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the new unit test proving a sandboxed `write_to_file`-repo-path rejection on an otherwise-successful committed run classifies as SUCCESS-with-warning passes; paste the test output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a test proving a genuine tool failure (or `write_to_file` failure on a non-repo path) still classifies ERROR, and that the downgrade logs a visible warning; paste the test output and the warning text.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes (prevent, downgrade, surface) around one bug: the false-ERROR turn status.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved (ship both). `Depends on: none`.
2. Scope fence: touch only `tools/agy_run.py`, the preamble/audit prompt files under `tools/awphysical/`, and the corresponding tests under `tests/`. Do NOT change what the agent does to the repo, the commit flow, or the broader status model. If the fix seems to need a larger status-model change, STOP and report.
3. Honesty rule (hard MUST): when you report the agy/tools tests passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, make the path-scoped lifecycle commit, and set backlog `uhbdt1` to `done`.
