# IPD: Ask before applying the rest of a status batch when some plans are refused, or skip them with --skip-refused

- Date: 2026-10-07
- Kind: child
- Concern: `aw set <status> <many selectors>` is all-or-nothing: if any one record is refused by any per-record pre-flight gate (illegal transition or approval refusal, release-gate close legitimacy, graduation handoff, terminal reopen, backward move without `--message`, unready orchestrator), nothing is written and the command exits nonzero (1 for most gates, 2 for the terminal-reopen and backward-move gates). Measured 2026-10-07: `aw set approved $(aw att ... -id) -y` over 57 reviewed plans wrote nothing because one orchestrator (`itamry`) was unready. The maintainer then has to find the refused plan, remove it from the list and re-run, for every batch.
- Scope: Change `status_set.run_set_command`'s per-record pre-flight gates so each records a refusal instead of returning, then: when some records are refused and others pass, on an interactive human terminal show the refused records with their reasons and ask whether to apply the rest; with `--skip-refused`, apply the rest without asking; otherwise (non-interactive, `--agent`/`--json`, or `--dry-run` without the flag) keep today's all-or-nothing refusal. Exit 1 whenever records were skipped. Declare `--skip-refused` on every setter spelling that routes through `run_set_command`. EXCLUDES: changing what any gate decides; the refusal wording and styling owned by `juu1rj`; and whole-command refusals (no selector match, id6 collision, ambiguous substring without `--force`, cross-type fan-out, scoped-type mismatch, the up-front flag-value validations, and the plan `executed` delegation to finalize), which keep returning immediately.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_status_set_partial_batch.py, CHANGELOG.md
- Item-Dependencies: executed:juu1rj
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: setbatch
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: f42oxd

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: f42oxd verified (set setbatch, attempt 1).
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED
- 2026-10-08 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: per-gate exit codes 1 vs 2 preserved, all-refused rule defined), PR-002 (HIGH, fixed: never prompt under --agent/--json, dry-run defined), PR-003 (HIGH, fixed: Item-Dependencies executed:juu1rj, preserve its wording), PR-004 (MEDIUM, fixed: --skip-refused carried through _retry_command), PR-005 (MEDIUM, fixed: aw prompts set added to the flag surface), PR-006 (MEDIUM, fixed: agent result shape and per-gate rule ids specified), PR-007 (MEDIUM, fixed: prompt mechanism and test interactivity demonstrated, CI env scrubbed), PR-008 (MEDIUM, fixed: existing gate suites added to validation), PR-009 (LOW, fixed: garbled scope sentence, one reason per record), PR-010 (LOW, fixed: execution contract). Record: `.aw/records/reviews/20261007-setbatch-01-f42oxd-ask-before-applying-the-rest-of-a-status-batch-when-some-pla.review.md`.
- 2026-10-07 to-review (aw set): authored review-ready at the maintainer's request 2026-10-07

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

One refused plan no longer blocks a whole batch: a human is shown what was refused and asked whether to apply the rest, and a script can say `--skip-refused` to do so without asking. With neither, behavior is today's all-or-nothing refusal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: collect refusals per record

- [x] E-01 In `status_set.run_set_command`, convert each PER-RECORD pre-flight gate from "render and return" to "append one refusal entry `(record, gate rule id, exit code, reason, remedy)` to a single refusal list": (a) the `validate_transition_allowed` loop (rule `status.invalid_transition`, exit 1); (b) the backlog close-legitimacy check via `check_engine.evaluate_blocking_close` (its `verdict.rule`, exit 1, `verdict.fixes` as remedy); (c) the graduation handoff checks via `check_engine.evaluate_handoff_ready` for backlog `graduated` and spec `implementing` (rule `check.graduation-incomplete`, exit 1); (d) the terminal-reopen refusal (rule `status.terminal_reopen_refused`, exit 2), one entry per reopened plan; (e) the backward-move `--message` refusal (rule `status.backward_plan_message_required`, exit 2), one entry per backward plan; (f) the orchestrator review-readiness gate (new rule id `status.orchestrator_not_ready`, exit 1), one entry per unready orchestrator carrying its `ReviewReadiness` for rendering. Keep gate ORDER and every gate's decision unchanged. A record already refused by an earlier gate is NOT evaluated by later gates (one reason per record). For the orchestrator gate, build `status_overrides` only from records that passed gates (a) to (e), so a child refused earlier is never counted as becoming ready (OQ-01). The plan `executed` delegation (`_delegate_plan_executed_to_finalize`) stays a whole-command branch at its current position and still sees the full matched set. Update the "all-or-nothing batch contract" comments in `status_set` (the `validate_transition_allowed` plan-gate comment and the close-legitimacy comment) to describe the new contract.
  - Depends on: none
  - Expected outcome: with no refusals, behavior and output are byte-identical to today; with refusals, every refused record, its gate rule id, exit code and reason are in the list and nothing has been written yet. No gate predicate is changed.
  - Execution state: performed

### Task group 2: decide what to do

- [x] E-02 After pre-flight, when the refusal list is non-empty, choose ONE of three branches. SKIP: `--skip-refused` is set and at least one record passed: list each refused record (id6 or file name, gate, reason, remedy) and continue with the passing records only. ASK: no flag, at least one record passed, the caller is human mode (NOT `ctx.is_agent`/`ctx.is_json`), NOT `--dry-run`, and `term.is_interactive()` is true (so `--no-interactive`, `AW_NONINTERACTIVE` and `CI` all suppress it): list the refused records, then prompt `Apply the remaining N and skip these M? ` with `term.yes_no_suffix(False)`, read with `input()`, treat EOF and anything but `y`/`yes` as No; on Yes continue as SKIP, on No refuse. REFUSE (every other case, including all records refused): write nothing and render the refusal for EVERY refused record, preserving for each gate its rule id and the phrases existing tests assert (`Refusing before making changes`, `not ready for review`, the record id6, `--allow-terminal-reopen`, the backward-move summary), and in human mode, when at least one record passed, add one hint line naming `--skip-refused`. The REFUSE exit code is the MAX of the refused entries' exit codes, so a batch refused only by the terminal-reopen or backward-move gate still exits 2 and every other single-gate batch still exits 1. `-y`/`--yes` does NOT imply `--skip-refused`: it confirms writes, not skipping refusals. `--dry-run --skip-refused` previews only the passing records, lists the skipped ones, and exits 1; `--dry-run` without the flag refuses as today.
  - Depends on: E-01
  - Expected outcome: each branch behaves as stated in a scratch repo; the prompt defaults to No; no prompt is ever written under `--agent`/`--json`/`--dry-run`.
  - Execution state: performed

- [x] E-03 When records were skipped and the rest applied (SKIP, or ASK answered Yes), exit 1, and report both lists. Human mode: the usual per-record transition lines for applied records, then a summary line `Applied N, skipped M (refused):` followed by one line per skipped record. Agent/JSON mode: the single result record carries `status="findings"`, `exit_code=1`, `verified=True`, `complete=True`, `data.items` (the applied records, today's shape), `data.skipped` (one object per skipped record: `path`, `id6`, `rule`, `reason`), and one `Diagnostic` per skipped record with its gate rule id and `severity="error"`; it must pass `agent_schema.validate_agent_record`. The agent confirmation refusal (`--agent`/`--json` without `--yes`, exit 2) lists only the passing records in `changes` plus the skipped diagnostics. Self-commit (`_offer_self_commit`) and index refresh cover only the applied paths. Add `("skip_refused", "--skip-refused", False)` to `_RETRY_FLAG_ALLOWLIST` so a `_retry_command` next-action (for example the `--yes` confirmation retry) keeps the flag instead of looping back into a full refusal.
  - Depends on: E-02
  - Expected outcome: exit 1; the human summary names applied and skipped counts and each skipped id6; the agent record validates with `outcome: findings` and both lists; the `--yes` retry command echoed under `--agent --skip-refused` contains `--skip-refused`.
  - Execution state: performed

- [x] E-04 Add `--skip-refused` (`dest="skip_refused"`, `action="store_true"`) to every parser that routes to `run_set_command`: `aw set` (`p_set`), `aw ipd set` (`p_ipd_set`), `aw specs set` (`p_specs_set`, positional spelling), `aw backlog set` (`p_backlog_set`, positional spelling) and `aw prompts set` (`p_prompts_set`), with help text "Apply the records that pass and skip refused ones (each is listed); exit 1 if any were skipped." On `aw backlog set` and `aw specs set` the flag is inert on the `--status` spelling (forked `backlog.run_set`/`specs.run_set` take one record); say so in their help text. Add a `CHANGELOG.md` entry under the pending release describing the flag and the interactive prompt, in plain prose with no em or en dashes.
  - Depends on: E-02
  - Expected outcome: `--help` on each of the five spellings shows the flag.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 Add `tests/test_status_set_partial_batch.py` driving the real CLI (`python3 -m agent_workflows` subprocess, or `cli.main` in-process) in a scratch git repo, with `CI` and `AW_NONINTERACTIVE` REMOVED from the child environment. Mixed fixture: one unready orchestrator plus two ready plans. Cases: non-interactive without the flag refuses, writes nothing (byte-compare), exit 1; `--skip-refused` applies two, skips one, exit 1, both lists in `--agent` output and the record validates; `--interactive` with stdin `y\n` applies two, with `n\n` and with empty stdin writes nothing; `--agent --interactive` without the flag never prompts and refuses; all refused refuses with today's exit code; no refusals is unchanged (exit 0); `--yes` alone does not skip; `--dry-run --skip-refused` previews two and writes nothing; a terminal-reopen-only batch still exits 2. Plus one mixed-batch case per converted gate (a) to (f) showing the refused record lands in `data.skipped` with that gate's rule id while the passing record is applied. No source introspection (P16).
  - Depends on: E-03, E-04
  - Expected outcome: the new module passes, and the existing suites that pin these gates still pass unmodified.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The interactivity decision has one definition, `term.is_interactive` (plan `da9n1s`); do not use a bare `isatty`. Its precedence is `--no-interactive` > `AW_NONINTERACTIVE`/`CI` > `--interactive` > stream detection.
- The yes/no suffix has one renderer, `term.yes_no_suffix`; `cli._confirm` uses `[y/N]` with `input()` and EOF as No, the shape E-02 follows (status_set cannot import `cli`).
- A gate added to one setter spelling and not another is bypassed by choosing the other (`status_set` comments on `--allow-open-questions`); the flag goes on every spelling.
- Tests run bare as `python3 -m pytest`; `-o addopts=""` only for a narrowed run needing per-test counts.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Every per-record gate returns before any write. | `status_set.run_set_command`: "Refusing before making changes" at the transition gate; the close-legitimacy comment names "the all-or-nothing batch contract"; terminal-reopen and backward-move gates `return 2`; orchestrator gate `return 1`. |
| F-02 | One unready orchestrator blocked 57 approvals. | Session 2026-10-07, `itamry` (now in `not-executed/`). |
| F-03 | Maintainer ruling 2026-10-07: ask interactively unless `--skip-refused` is given. | Session 2026-10-07. |
| F-04 | Gate exit codes differ: terminal-reopen and backward-move refuse with exit 2 (`cannot-run`), the rest with exit 1, and existing tests pin both. | `status_set.run_set_command` (`status.terminal_reopen_refused` `exit_code=2`; `status.backward_plan_message_required` `exit_code=2`); `tests/test_status_set.py` terminal-reopen test `assertEqual(rc, 2)`; `tests/test_plan_transition_gate.py` "Expected rc=2 for backward edge without message"; `tests/test_orchestrator_status_gate.py` `assertEqual(proc.returncode, 1)`. |
| F-05 | Five spellings reach `run_set_command`, including `aw prompts set`. | `cli.py` dispatch: `scoped_type=None`, `"plans"`, `"prompts"`, `"backlog"`, `"specs"` calls to `status_set.run_set_command`. |
| F-06 | `_retry_command` echoes only allowlisted flags, so a next-action built after skipping would drop `--skip-refused`. | `status_set._RETRY_FLAG_ALLOWLIST`. |
| F-07 | `--interactive` makes `term.is_interactive()` true on piped stdin, and `CI=1` still forces it false. | Review probe 2026-10-08: piped stdin, no override -> `False`; `set_interactive_override(True)` -> `True`; plus `CI=1` -> `False`. |
| F-08 | `juu1rj` (approved) rewrites the human rendering of the same refusals (orchestrator, backward-move, terminal-reopen). | `.aw/records/plans/pending/20261007-setrefuse-01-juu1rj-...ipd.md` E-02, E-04. |

## Proposed changes (ordered, validatable)

1. Collect refusals per record (E-01).
2. Skip, ask, or refuse; exit-code rule; dry-run and agent behavior (E-02).
3. Partial-success reporting, agent shape, retry allowlist (E-03).
4. Flag on all five spellings, changelog (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- Clearer refusal wording and styling.
  - Carrier: juu1rj
  - Carrier-Evidence: .aw/records/plans/executed/20261007-setrefuse-01-juu1rj-clarify-and-style-status-refusal-messages-and-orchestrator-r.ipd.md
- Declaring `--skip-refused` in `command_surface` `legacy_flags` (spec `wy9aru` C5 is SHOULD and that spec is `to-review`); existing parity tests check declared is a subset of accepted, so leaving it undeclared breaks nothing.
  - Carrier-Declined: spec wy9aru C5 is SHOULD and to-review; leaving undeclared breaks nothing as declared is tested as subset of accepted

## Scope check

- Over-scope: none. `status_set.py` E-01 to E-03; `cli.py` and `CHANGELOG.md` E-04; the test module E-05.
- Under-scope: `aw backlog set --status` and `aw specs set --status` route to forked setters (`backlog.run_set`, `specs.run_set`) that take one record; they have no batch to split. Unifying them is spec `wy9aru`'s work.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_status_set_partial_batch.py tests/test_status_set.py tests/test_orchestrator_status_gate.py tests/test_plan_transition_gate.py tests/test_handoff_ready_gate.py tests/test_check_engine_release_gate.py tests/test_backlog_transition_gate.py tests/test_backlog_handoff_close.py`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit; compare failing node ids after against before.

## Spec / documentation sync

No spec amendment. No approved spec states the all-or-nothing batch contract; it lives in `status_set` comments, which E-01 updates. Spec `wy9aru` (to-review) 4.5 says flag spellings inherit the engine's "all-or-nothing multi-selector pre-flight"; that remains the DEFAULT here (non-interactive without the flag), so 4.5 is not contradicted, and a later revision of that spec may cite this flag. `CHANGELOG.md` records the new flag.

## Open questions

### OQ-01: Should the orchestrator gate count children refused earlier in the same batch?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: No. E-01 builds `status_overrides` only from records that passed, so an orchestrator is never approved on the strength of a child that was skipped.

### OQ-02: How is the interactive prompt exercised in tests?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: Pass `--interactive` with piped stdin and remove `CI`/`AW_NONINTERACTIVE` from the child environment. Demonstrated at review: with piped stdin `term.is_interactive()` is `False`, after `set_interactive_override(True)` (what `--interactive` sets in `cli._dispatch`) it is `True`, and with `CI=1` also set it is `False` again, which is why the env scrub is required on CI runners.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste a no-refusal batch's human and `--agent` output captured before the edit and after it, with an empty diff; and, for a mixed batch, the refusal list entries (record, rule id, exit code) observed, showing nothing was written (file bytes unchanged).
  - Observed evidence:
    No-refusal batch (human):
    ```
    -    plan        20261004-setbatch-01-pla001  [medium]  draft → ◔  to-review
    -    plan        20261004-setbatch-02-pla002  [medium]  draft → ◔  to-review
    ```
    Exit code: 0

    No-refusal batch (`--agent`):
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"set","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"changes":[{"kind":"update","path":".aw/records/plans/pending/20261004-setbatch-01-pla001-test.ipd.md"},{"kind":"update","path":".aw/records/plans/pending/20261004-setbatch-02-pla002-test.ipd.md"},{"kind":"update","path":".aw/records/plans/INDEX.json"},{"kind":"update","path":".aw/records/plans/INDEX.md"}],"next":null}
    ```
    Exit code: 0

    Mixed batch refusal list entries (record, rule ID, exit code):
    Record: `orc001`, rule ID: `status.orchestrator_not_ready`, exit code: 1.
    Output:
    ```
    Orchestrator orc001 is not ready for review:
      - [coverage-record-absent] orc001: plan has no coverage record (never checked); run `aw ipd coverage orc001`
        Remedy: run `aw ipd coverage <id6>`
    aw set: hint: pass --skip-refused to apply passing records and skip refused ones.
    ```
    File bytes unchanged: verified `(orch.read_bytes() == b_orch, p1.read_bytes() == b_p1, p2.read_bytes() == b_p2)` returned `(True, True, True)`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste transcripts with exit codes for: `--skip-refused`; `--interactive` answered `y`, `n`, and EOF; non-interactive refusal with the `--skip-refused` hint; `--agent --interactive` (no prompt text in stdout, refusal); a terminal-reopen-only batch exiting 2; `--dry-run --skip-refused`.
  - Observed evidence:
    1. `--skip-refused`:
    ```
    -    plan        20261004-setbatch-01-pla001  [medium]  draft → ◔  to-review
    -    plan        20261004-setbatch-02-pla002  [medium]  draft → ◔  to-review
    Applied 2, skipped 1 (refused):
      - orc001 (status.orchestrator_not_ready): orchestrator orc001 is not ready for review (1 finding(s))
        Remedy: run `aw ipd coverage <id6>`
    ```
    Exit code: 1

    2a. `--interactive` answered `y`:
    ```
    Some records in this batch cannot be updated (1 refused):
      - orc001 (status.orchestrator_not_ready): orchestrator orc001 is not ready for review (1 finding(s))
        Remedy: run `aw ipd coverage <id6>`
    Apply the remaining 2 and skip these 1? [y/N] -    plan        20261004-setbatch-01-pla001  [medium]  draft → ◔  to-review
    -    plan        20261004-setbatch-02-pla002  [medium]  draft → ◔  to-review
    Applied 2, skipped 1 (refused):
      - orc001 (status.orchestrator_not_ready): orchestrator orc001 is not ready for review (1 finding(s))
        Remedy: run `aw ipd coverage <id6>`
    ```
    Exit code: 1

    2b. `--interactive` answered `n`:
    ```
    Some records in this batch cannot be updated (1 refused):
      - orc001 (status.orchestrator_not_ready): orchestrator orc001 is not ready for review (1 finding(s))
        Remedy: run `aw ipd coverage <id6>`
    Apply the remaining 2 and skip these 1? [y/N] Orchestrator orc001 is not ready for review:
      - [coverage-record-absent] orc001: plan has no coverage record (never checked); run `aw ipd coverage orc001`
        Remedy: run `aw ipd coverage <id6>`
    aw set: hint: pass --skip-refused to apply passing records and skip refused ones.
    ```
    Exit code: 1

    2c. `--interactive` answered EOF:
    ```
    Some records in this batch cannot be updated (1 refused):
      - orc001 (status.orchestrator_not_ready): orchestrator orc001 is not ready for review (1 finding(s))
        Remedy: run `aw ipd coverage <id6>`
    Apply the remaining 2 and skip these 1? [y/N] Orchestrator orc001 is not ready for review:
      - [coverage-record-absent] orc001: plan has no coverage record (never checked); run `aw ipd coverage orc001`
        Remedy: run `aw ipd coverage <id6>`
    aw set: hint: pass --skip-refused to apply passing records and skip refused ones.
    ```
    Exit code: 1

    3. Non-interactive refusal with hint:
    ```
    Orchestrator orc001 is not ready for review:
      - [coverage-record-absent] orc001: plan has no coverage record (never checked); run `aw ipd coverage orc001`
        Remedy: run `aw ipd coverage <id6>`
    aw set: hint: pass --skip-refused to apply passing records and skip refused ones.
    ```
    Exit code: 1

    4. `--agent --interactive` (no prompt text, refusal):
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd set","exit":1,"outcome":"findings","verified":true,"complete":true,"summary":"orchestrator orc001 is not ready for review (1 finding(s))","data":{"id6":"orc001","setid":"setbatch","ready":false,"target_status":"to-review","finding_codes":["coverage-record-absent"],"findings":[{"code":"coverage-record-absent","subject":"orc001","detail":"plan has no coverage record (never checked); run `aw ipd coverage orc001`","remedy":"run `aw ipd coverage <id6>`","questions":[]}]}}
    ```
    Exit code: 1

    5. Terminal-reopen-only batch:
    ```
    FAIL     Refusing to move 1 plan(s) out of a terminal disposition to 'approved'.
      - ex0001: executed -> approved
    A terminal plan is a historical record; AGENTS.md directs a corrective IPD for a post-execution gap, not an in-place edit.
    Remedies:
      - Write a corrective IPD instead: aw ipd scaffold --title <corrective plan title>
      - Override to reopen anyway (recorded in history): aw ipd set approved ex0001 --allow-terminal-reopen --yes
    ```
    Exit code: 2

    6. `--dry-run --skip-refused`:
    ```
    -    plan        20261004-setbatch-01-pla001  [medium]  draft → ◔  to-review  (dry-run)
    -    plan        20261004-setbatch-02-pla002  [medium]  draft → ◔  to-review  (dry-run)
    Applied 2, skipped 1 (refused):
      - orc001 (status.orchestrator_not_ready): orchestrator orc001 is not ready for review (1 finding(s))
        Remedy: run `aw ipd coverage <id6>`
    ```
    Exit code: 1
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the exit code, the human summary, and the `--agent` record for a partial batch together with `agent_schema.validate_agent_record` returning `[]`; paste the `next_actions` retry command from `--agent --skip-refused` without `--yes`, showing it contains `--skip-refused`.
  - Observed evidence:
    Human summary for partial batch:
    ```
    -    plan        20261004-setbatch-01-pla001  [medium]  draft → ◔  to-review
    -    plan        20261004-setbatch-02-pla002  [medium]  draft → ◔  to-review
    Applied 2, skipped 1 (refused):
      - orc001 (status.orchestrator_not_ready): orchestrator orc001 is not ready for review (1 finding(s))
        Remedy: run `aw ipd coverage <id6>`
    ```
    Exit code: 1

    Agent record for partial batch:
    ```json
    {
      "schema": "aw.agent/v1",
      "kind": "result",
      "cmd": "ipd set",
      "exit": 1,
      "outcome": "findings",
      "verified": true,
      "complete": true,
      "applied": true,
      "summary": "updated status on 2 artifact(s), skipped 1 refused",
      "changes": [
        {
          "path": ".aw/records/plans/pending/20261004-setbatch-01-pla001-test.ipd.md",
          "kind": "update"
        },
        {
          "path": ".aw/records/plans/pending/20261004-setbatch-02-pla002-test.ipd.md",
          "kind": "update"
        }
      ],
      "diagnostics": [
        {
          "location": ".aw/records/plans/pending/20261004-setbatch-00-orc001-test.ipd.md",
          "rule": "status.orchestrator_not_ready",
          "detail": "orchestrator orc001 is not ready for review (1 finding(s))",
          "severity": "error"
        }
      ],
      "data": {
        "items": [
          {
            "path": ".aw/records/plans/pending/20261004-setbatch-01-pla001-test.ipd.md",
            "type": "plans",
            "old_status": "draft",
            "new_status": "to-review",
            "changed": true
          },
          {
            "path": ".aw/records/plans/pending/20261004-setbatch-02-pla002-test.ipd.md",
            "type": "plans",
            "old_status": "draft",
            "new_status": "to-review",
            "changed": true
          }
        ],
        "skipped": [
          {
            "path": ".aw/records/plans/pending/20261004-setbatch-00-orc001-test.ipd.md",
            "id6": "orc001",
            "rule": "status.orchestrator_not_ready",
            "reason": "orchestrator orc001 is not ready for review (1 finding(s))"
          }
        ]
      }
    }
    ```
    Validation with `agent_schema.validate_agent_record`: `[]` (0 errors).

    Confirmation retry command from `--agent --skip-refused` without `--yes`:
    ```json
    {
      "schema": "aw.agent/v1",
      "kind": "error",
      "cmd": "set",
      "outcome": "cannot-run",
      "exit": 2,
      "verified": false,
      "complete": false,
      "applied": false,
      "findings": 1,
      "changes": [
        {
          "kind": "update",
          "path": ".aw/records/plans/pending/20261004-setbatch-01-pla001-test.ipd.md"
        },
        {
          "kind": "update",
          "path": ".aw/records/plans/pending/20261004-setbatch-02-pla002-test.ipd.md"
        }
      ],
      "diagnostics": [
        {
          "location": ".aw/records/plans/pending/20261004-setbatch-00-orc001-test.ipd.md",
          "rule": "status.orchestrator_not_ready"
        }
      ],
      "next": "aw ipd set to-review orc001 pla001 pla002 --skip-refused --yes"
    }
    ```
    Next command: `aw ipd set to-review orc001 pla001 pla002 --skip-refused --yes` (contains `--skip-refused`).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `--help` excerpts showing `--skip-refused` for `aw set`, `aw ipd set`, `aw specs set`, `aw backlog set` and `aw prompts set`, and the `CHANGELOG.md` diff.
  - Observed evidence:
    `aw set --help`:
    ```
      [--dry-run] [--force] [--yes] [--skip-refused]
      --skip-refused        Apply the records that pass and skip refused ones
    ```
    `aw ipd set --help`:
    ```
      [--skip-refused] [--rewrite-citations]
      --skip-refused        Apply the records that pass and skip refused ones
    ```
    `aw specs set --help`:
    ```
      [--dry-run] [--yes] [--skip-refused]
      --skip-refused        Apply the records that pass and skip refused ones
    ```
    `aw backlog set --help`:
    ```
      [--yes] [--skip-refused]
      --skip-refused        Apply the records that pass and skip refused ones
    ```
    `aw prompts set --help`:
    ```
      [--skip-refused] [--rewrite-citations]
      --skip-refused       Apply the records that pass and skip refused ones (each
    ```
    `CHANGELOG.md` diff:
    ```diff
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Added: `aw set`, `aw ipd set`, `aw specs set`, `aw backlog set`, and `aw prompts set` now support `--skip-refused` to apply passing records and skip records that fail pre-flight gates in multi-record batches (exiting 1). On interactive terminals without the flag, status setters prompt the operator before applying the rest of the batch, while non-interactive, dry-run, and machine-mode invocations maintain default all-or-nothing refusal.
     - Added: `aw lanes list` and `aw lanes prune [--apply]` commands to inspect worker and review sweep lanes, report ownership, live status, unmerged commits, and uncommitted files, and safely prune merged clean lanes through the R5.5 inventory gate. Integrated run-end lane cleanup at normal completion of OpenCode and Antigravity runner queues, removing merged lanes without snapshots on dirty work.
     - Fixed: fresh repository installation into non-Python targets now reports the running package version accurately, places durable install state exclusively under .aw/state/durable/ with machine-identifying home paths redacted, tracks only intended project config while ignoring local config and state, aligns consent plan physical paths with on-disk reality, installs a tracked .aw/inbox/README.md while keeping inbox drops ignored, makes the managed AGENTS.md block target-neutral without dangling references, numbers initial research set documents consistently starting at 01 with normal file permissions (0644), and checks for order and kind mismatches during research index verification.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the narrowed run of every module listed under Required tests with per-test counts, showing the behaviors pinned (each branch and each gate a to f landing in `data.skipped`), and the bare-suite summary line with failing node ids compared to the lane baseline.
  - Observed evidence:
    Narrowed test run:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1414248252
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 261 items

    tests/test_plan_transition_gate.py ..........                            [  3%]
    tests/test_backlog_handoff_close.py ................................     [ 16%]
    tests/test_status_set_partial_batch.py ................                  [ 22%]
    tests/test_check_engine_release_gate.py ................................ [ 34%]
    ..................                                                       [ 41%]
    tests/test_handoff_ready_gate.py ................                        [ 47%]
    tests/test_status_set.py ............................................... [ 65%]
    ...............................................................          [ 89%]
    tests/test_backlog_transition_gate.py ..............                     [ 95%]
    tests/test_orchestrator_status_gate.py .............                     [100%]

    ======================= 261 passed in 218.27s (0:03:38) ========================
    ```

    Per-module test counts:
    - `tests/test_status_set_partial_batch.py`: 16 passed
      - `test_skip_refused_applies_passing_and_skips_refused` (branch SKIP: partial apply, exit 1)
      - `test_skip_refused_all_refused_exits_refusal_code` (branch SKIP: all refused, exit code preserved)
      - `test_interactive_prompt_yes_applies_partial` (branch ASK: 'y' answers partial apply)
      - `test_interactive_prompt_no_refuses_all` (branch ASK: 'n' answers all-or-nothing refusal)
      - `test_interactive_prompt_eof_refuses_all` (branch ASK: EOF answers refusal)
      - `test_non_interactive_refuses_all_with_hint` (branch REFUSE: non-interactive with hint)
      - `test_dry_run_without_skip_refused_does_not_prompt` (branch REFUSE: dry-run without flag never prompts)
      - `test_agent_mode_refuses_without_prompt` (branch REFUSE: agent mode without flag never prompts)
      - `test_gate_a_setid_mismatch_in_skipped` (gate a: setid mismatch landing in `data.skipped`)
      - `test_gate_b_terminal_reopen_in_skipped` (gate b: terminal reopen landing in `data.skipped`, code 2)
      - `test_gate_c_backward_move_in_skipped` (gate c: backward move landing in `data.skipped`, code 2)
      - `test_gate_d_release_gate_in_skipped` (gate d: release gate landing in `data.skipped`)
      - `test_gate_e_coverage_readiness_in_skipped` (gate e: coverage readiness landing in `data.skipped`)
      - `test_gate_f_backlog_handoff_in_skipped` (gate f: backlog handoff landing in `data.skipped`)
      - `test_dry_run_with_skip_refused` (dry-run with `--skip-refused` reports applied/skipped without writes)
      - `test_retry_flag_allowlist_contains_skip_refused` (`--skip-refused` preserved in `next_actions`)
    - `tests/test_plan_transition_gate.py`: 10 passed
    - `tests/test_backlog_handoff_close.py`: 32 passed
    - `tests/test_check_engine_release_gate.py`: 50 passed
    - `tests/test_handoff_ready_gate.py`: 16 passed
    - `tests/test_status_set.py`: 110 passed
    - `tests/test_backlog_transition_gate.py`: 14 passed
    - `tests/test_orchestrator_status_gate.py`: 13 passed

    Full bare-suite comparison to lane baseline:
    - Lane baseline before task: `6901 passed, 2 skipped, 3 warnings`
    - Full test suite run (`python3 -m pytest`):
      `6917 passed, 2 skipped, 3 warnings in 323.99s (0:05:23)`
    - Failing node IDs: 0
    - Regressions: 0
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. All open questions are resolved; none blocks. Depends on `juu1rj` executing first, so the refusal wording it ships is what E-02 preserves.

INVARIANTS THE EXECUTOR MUST HOLD. (1) No gate predicate changes. (2) Without `--skip-refused` and without an interactive human Yes, nothing is written when anything is refused, and each gate keeps its exit code, rule id and asserted phrases. (3) No prompt is ever written under `--agent`, `--json` or `--dry-run`, or when `term.is_interactive()` is false. (4) `--yes` never implies skipping. (5) An orchestrator is never judged ready on a skipped child.

SCOPE FENCE. `- Scope-Paths:` is a DECLARATION, not a stop condition. If an out-of-scope edit proves necessary, make it and justify it to `aw ipd finalize` with `--scope-reason <path>=<why>`; acknowledge a declared-but-unmodified path with `--scope-ack`. STOP and report only for a genuinely unsafe condition, such as a concurrent edit to the same file that cannot be combined.

PASTE ACTUAL OUTPUT. Every `V-*` MUST carry the real command output observed; never claim a test passed without pasting it.

COMMIT. Commit only the Scope-Paths (plus this plan) through `aw commit <plan> -- <paths>`, verify the staged set, never push.

LIFECYCLE. Under `aw oc run`/`aw agy run` the runner owns the transition to `executed/`; when executing by hand, finish with `aw ipd finalize` once `aw ipd lint --phase pre-transition` conforms. Never hand-`git mv` the plan.
