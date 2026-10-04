# IPD: Refuse aw backlog set graduated and aw specs set implementing while a handed-off plan is not ready

- Date: 2026-10-04
- Kind: child
- Concern: A backlog item may be set `graduated` by hand (or by an agent following the managed `AGENTS.md` instruction "set the item to `graduated`") with no check that the plans naming it in `- From-Backlog:` exist or are ready. `check_engine.evaluate_blocking_close`, the one predicate behind both `aw backlog set` spellings, treats `graduated` as always legitimate (its `bklgrad v58bvy E-03` branch returns ok for a gated item, and an ungated item falls through unchecked); the only Set-level check runs when the item reaches `done`. `aw specs set implementing` has the same gap for `- From-Spec:`. The maintainer stated on 2026-10-04 that a backlog item may be set `graduated` only when every plan it hands off to is complete, `to-review` or later, and lints, and that the system must report a partial graduation. Spec `77tr3o` R-13 (added by Order 01) requires it.
- Scope: IN: a predicate `evaluate_handoff_ready(repo, source_type, source_id6)` in `check_engine.py` that collects every active plan whose `- From-Backlog:` (or `- From-Spec:`) names the source and returns not-ready findings when there is none, when any is below `to-review` or fails lint at `author`, or when any orchestrator among them fails `orchestrator_readiness.review_readiness(..., ask=False)`; calling it from both `aw backlog set` spellings for a `graduated` target and from `aw specs set` for an `implementing` target, refusing with the shared rendering; a check rule `check.graduation-incomplete` (severity `error`) reporting every `graduated` backlog item and `implementing` spec whose handoff is not ready, with remedy "`aw backlog set open <id6>` and re-run graduation"; tests. OUT: the `done` close-legitimacy rules (unchanged); the production path (already gated by Order 06, which runs before its own setter call and so passes this check); a spec produced FROM a backlog item (it is a valid handoff target and is checked by spec status, not by this rule's plan logic).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/backlog.py, agent_workflows/status_set.py, agent_workflows/specs.py, tests/test_handoff_ready_gate.py
- Item-Dependencies: executed:52opph
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 10
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sbiv1j

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 10 of Set `gradcover`. Implements spec `77tr3o` R-13's source-side half. Ordered after Order 09 so the items Order 09 reopens are `open` before `check.graduation-incomplete` exists, keeping `aw check` green in CI.

## Goal

Make `graduated` (and spec `implementing`) mean what the maintainer defined: every handed-off plan exists, is ready for review, and lints, with any orchestrator among them passing the shared readiness check; refuse the status otherwise, and report any item that already claims it falsely.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the predicate

- [ ] E-01 Add `evaluate_handoff_ready(repo_root, source_type, source_id6)` to `check_engine.py`, returning a result with `ready` and a tuple of findings `(code, plan_id6, detail, remedy)`. A handoff plan is an active (non-terminal-directory) plan whose `- From-Backlog:` (for `backlog`) or `- From-Spec:` (for `spec`) names the source, read with the existing `_read_from_backlog`-style classifiers. A spec carrying `- From-Backlog:` also counts as a handoff for a backlog source and is ready when its status is `approved` or later. Findings: no handoff at all; a plan below `to-review`; a plan failing `ipd_lint.lint_file(..., checkpoint="author")`; an orchestrator failing `review_readiness(..., ask=False)` (its findings are included, quotes and all).
  - Depends on: none
  - Expected outcome: the predicate reports each of the four failure kinds on fixtures and `ready=True` for a fixture with a ready Set and a recorded pass verdict.
  - Execution state: pending

### Task group 2: the consumers

- [ ] E-02 Call the predicate from both `aw backlog set` spellings (the `--status` path in `backlog.run_set` and the positional path in `status_set.apply_status_change` / `run_set_command` for backlog records) when the normalized target is `graduated` and the current status is not already `graduated`; on not-ready, refuse with exit 1, write nothing, and print the shared human rendering or the `aw.agent/v1` record listing each plan and finding with its remedy.
  - Depends on: E-01
  - Expected outcome: `aw backlog set graduated <item>` and `aw backlog set <item> --status graduated` both refuse on the same not-ready fixture with the same findings, and both succeed on a ready fixture.
  - Execution state: pending

- [ ] E-03 Call the predicate from `aw specs set` (both spellings) when the normalized target is `implementing` and the current status is `approved`; refuse the same way.
  - Depends on: E-02
  - Expected outcome: `aw specs set implementing <spec>` refuses on a fixture whose produced orchestrator has a `draft` child and succeeds on a ready one.
  - Execution state: pending

- [ ] E-04 Add `check.graduation-incomplete` (severity `error`) to `check_engine.py`, registered in the backlog and specs check families, reporting every `graduated` backlog item and every `implementing` spec whose handoff the predicate finds not ready, with observed/required/recovery fields (recovery: `aw backlog set open <id6>` then re-run graduation; for a spec, `aw specs set approved <path>` if legal, else name the plan to fix). Apply it to items whose status changed on or after the repository's stamped cutover only if the existing grandfathering pattern requires it; otherwise to all live items, and record which in the evidence.
  - Depends on: E-03
  - Expected outcome: `aw check backlog` reports a fixture `graduated` item whose orchestrator was set back to `draft`; on the real tree after Order 09, it reports nothing.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_handoff_ready_gate.py` driving the CLI as subprocesses over fixture repositories with pre-recorded probe verdicts: each predicate failure kind; both backlog setter spellings refusing identically and writing nothing; both succeeding on a ready Set; the spec setter twin; the check rule reporting a drifted `graduated` item; and the production path still succeeding end to end (reuse one `tests/test_backlog_production.py` fixture with a ready Set) so the runner's own setter call is not refused. Prove the tests can fail by making the predicate always ready and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation fails it; `tests/test_backlog_production.py`, `tests/test_spec_production.py` and the existing release-gate tests still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE PREDICATE BACKS BOTH SETTER SPELLINGS. `evaluate_blocking_close` is the precedent; `aw backlog set` forks on whether `--status` was passed, so a gate wired into one path fires for one spelling only (the comment above `decide_gate_default`'s call in `backlog.run_set` records exactly this hazard).
- CI RUNS `aw check backlog` FAIL-CLOSED (`.github/workflows/tests.yml`, step "aw check backlog (backlog conformance; fail closed)"); a new `error` rule must be green on the real tree when it lands, which Order 09's ordering ensures.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `graduated` is unconditionally legitimate. `evaluate_blocking_close`'s branch commented "`graduated` is EXPLICITLY legitimate for a release-gated item and drops nothing" returns `CloseVerdict(True, "ok", ...)` for a gated item; there is no lookup of `From-Backlog` plans for this target. | the quoted branch in `evaluate_blocking_close` |
| F-02 | The production path sets `graduated` through the same setter (`aw backlog set <id6> --status graduated --no-commit`), so after Order 06 it reaches the setter only with a ready Set and passes this gate; no production regression is expected, and E-05 proves it. | the setter argv in the backlog production branch of `execute_item_core` |
| F-03 | The managed `AGENTS.md` block tells agents to "set the item to `graduated`" as step (5) of acting on a backlog item, with no precondition. Order 11 adds the precondition to the text; this plan makes it enforced. | the "Acting on a backlog item" paragraph in `engine.py`'s managed block |

## Proposed changes (ordered, validatable)

1. Add the handoff-readiness predicate (E-01).
2. Gate both backlog setter spellings (E-02) and the spec setter (E-03).
3. Add `check.graduation-incomplete` (E-04).
4. Subprocess tests, a production regression case and a mutation proof (E-05).

## Deferred / out of scope (with reason)

- CHANGING `done` CLOSE LEGITIMACY. Its rules already require the handoff to be executed; unchanged.
  - Carrier-Declined: no defect measured in the `done` path
- AN OPT-IN PRE-COMMIT HOOK for hand edits of `- Status: graduated`. `check.graduation-incomplete` in CI is the portable authority, as `AGENTS.md` states for the existing close gate.
  - Carrier-Declined: the existing honest-limits rationale applies; CI is the authority

## Scope check

- Over-scope: none. Four production modules (predicate, two setter paths, spec setter) and one test file.
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_handoff_ready_gate.py tests/test_backlog_production.py tests/test_spec_production.py tests/test_check_engine_release_gate.py tests/test_status_set.py -q` pasted.
- Mutation run pasted.
- On the real tree: `python3 -m agent_workflows check backlog` and `check specs` after the change, pasted, showing no `check.graduation-incomplete` finding.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `77tr3o` R-13 (source side) as amended by Order 01. The `.aw/records/backlog/README.md` description of `graduated` ("design handed off to a plan/spec") is now enforced and needs no wording change; Order 11 updates `AGENTS.md`.

## Open questions

### OQ-01: Should the setter ask the probe when no verdict is recorded?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO, as for `aw ipd set` (Order 05 OQ-01): the setter reads the recorded verdict and an absent one is a finding naming `aw ipd coverage <id6>`. The production path records a verdict before calling the setter, so the common path never hits this.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's diff and test output for the four failure kinds and the ready case.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diffs at both setter paths; paste both spellings' refusal output on one fixture side by side (identical findings) and a file-bytes-unchanged assertion; paste both succeeding on the ready fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the spec setter diff and its refuse and succeed outputs.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the rule registration diff, the fixture `aw check backlog` output reporting the drifted item, and the real-tree `aw check backlog` / `aw check specs` output with no such finding. State whether the rule is grandfathered and why.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new file passing with its count; the production regression case passing; the mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
