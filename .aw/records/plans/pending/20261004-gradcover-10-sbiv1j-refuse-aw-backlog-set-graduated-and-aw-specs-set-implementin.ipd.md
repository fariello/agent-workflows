# IPD: Refuse aw backlog set graduated and aw specs set implementing while a handed-off plan is not ready

- Date: 2026-10-04
- Kind: child
- Concern: A backlog item may be set `graduated` by hand (or by an agent following the managed `AGENTS.md` instruction "set the item to `graduated`") with no check that the plans naming it in `- From-Backlog:` exist or are ready. `check_engine.evaluate_blocking_close`, the one predicate behind both `aw backlog set` spellings, treats `graduated` as always legitimate (its `bklgrad v58bvy E-03` branch returns ok for a gated item, and an ungated item falls through unchecked); the only Set-level check runs when the item reaches `done`. `aw specs set implementing` has the same gap for `- From-Spec:`. The maintainer stated on 2026-10-04 that a backlog item may be set `graduated` only when every plan it hands off to is complete, `to-review` or later, and lints, and that the system must report a partial graduation. Spec `77tr3o` R-13 (added by Order 01) requires it.
- Scope: IN: a predicate `evaluate_handoff_ready(repo, source_type, source_id6)` in `check_engine.py` that collects every active plan whose `- From-Backlog:` (or `- From-Spec:`) names the source and returns not-ready findings when there is none, when any is below `to-review` or fails lint at `author`, or when any orchestrator among them fails `orchestrator_readiness.review_readiness(..., ask=False)`; calling it from both `aw backlog set` spellings for a `graduated` target and from `aw specs set` for an `implementing` target, refusing with the shared rendering; a check rule `check.graduation-incomplete` (severity `error`) reporting every `graduated` backlog item and `implementing` spec whose handoff is not ready and whose graduation is on or after a new stamped cutover `graduation_ready` (older graduations are grandfathered, see E-04), with remedy "`aw backlog set open <id6>` and re-run graduation"; the cutover's registration in `config.py` and stamp in `.aw/config/project.json`; fixture updates to existing tests that graduate an item with no handoff (E-06); tests. OUT: the `done` close-legitimacy rules (unchanged); the production path (already gated by Order 06, which runs before its own setter call and so passes this check); a spec produced FROM a backlog item (it is a valid handoff target and is checked by spec status, not by this rule's plan logic).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/backlog.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/config.py, .aw/config/project.json, tests/test_handoff_ready_gate.py, tests/test_backlog.py, tests/test_backlog_gate_follows_status.py, tests/test_backlog_history_dedup_parity.py, tests/test_backlog_production.py, tests/test_backlog_transition_gate.py, tests/test_history_label_parity.py, tests/test_plan_transition_gate.py, tests/test_status_set.py
- Item-Dependencies: executed:52opph, executed:26m1nb, executed:r2wa38
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 10
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sbiv1j

## Workflow history
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 (all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-009. Fixed: `check.graduation-incomplete` judges only graduations on or after a new stamped cutover, because 88 of 189 `graduated` items have no active handoff (46 with no linked plan or spec at all, 42 whose plans are all terminal; measured) and an ungrandfathered `error` rule would turn CI red on the very day it lands; a handoff whose plans are all terminal is a COMPLETED handoff, not a missing one (PR-001); E-04's `aw check` real-tree claim restated to that population (PR-002); existing tests that set `graduated` with no handoff measured by a setter spy over the bare suite (24 tests in 9 files, 0 carriers) and new E-06 fixes their fixtures, declared in scope (PR-003); a `- Graduated-To:` Set and a terminal-only handoff counted as handoff evidence (PR-004); the setter refusal ordered before any write and reusing the existing exit/agent-record shape, with the shared renderer from `orchestrator_readiness` (PR-005); the production regression stated, including `test_case5b` whose outcome changes because the agent's own early `graduated` call is now refused (PR-006); `--gate-dir` honored for an isolated runner call (PR-007); dependencies on `26m1nb` and `r2wa38` declared (PR-008); gate contract (PR-009).
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): wording updated for the maintainer ruling 2026-10-04 (coverage answer stored in the plan).

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 10 of Set `gradcover`. Implements spec `77tr3o` R-13's source-side half. Ordered after Order 09 so the items Order 09 reopens are `open` before `check.graduation-incomplete` exists, keeping `aw check` green in CI.

## Goal

Make `graduated` (and spec `implementing`) mean what the maintainer defined: every handed-off plan exists, is ready for review, and lints, with any orchestrator among them passing the shared readiness check; refuse the status otherwise, and report any item that already claims it falsely.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the predicate

- [ ] E-01 Add `evaluate_handoff_ready(repo_root, source_type, source_id6)` to `check_engine.py`, returning a result with `ready` and a tuple of findings `(code, plan_id6, detail, remedy)`. A handoff plan is an active (non-terminal-directory) plan whose `- From-Backlog:` (for `backlog`) or `- From-Spec:` (for `spec`) names the source, read with the existing `_read_from_backlog`-style classifiers. A spec carrying `- From-Backlog:` also counts as a handoff for a backlog source and is ready when its status is `approved` or later. Findings: no handoff at all; a plan below `to-review`; a plan failing `ipd_lint.lint_file(..., checkpoint="author")`; an orchestrator failing `review_readiness(..., ask=False)` (its findings are included, quotes and all, rendered with that module's shared remedy data, never a second wording). A COMPLETED HANDOFF IS READY: when every linked plan sits in a terminal directory (`executed/`, `superseded/`, `not-executed/`) and at least one is `executed`, there is no active plan and that is not a finding (measured at review: 42 `graduated` items are exactly this). A source whose `- Graduated-To:` names a Set that resolves (any plan carrying it, per `releases.parse_graduated_to` and `check.graduated-to-dangling`'s rule) but whose plans carry no `- From-Backlog:` is judged by that Set's plans instead, so the older handoff link form is honored. Use the one-walk `_from_backlog_carrier_index` for the sweep in E-04 and `find_from_backlog_artifacts` only for a single item (the single-item contract is enforced by `tests/test_carrier_scan_single_item_contract.py`, so the check rule must not call the single-item scanner in a loop).
  - Depends on: none
  - Expected outcome: the predicate reports each of the four failure kinds on fixtures and `ready=True` for a fixture with a ready Set whose orchestrator carries a current coverage pass, for a completed (all-terminal, one executed) handoff, and for a `- Graduated-To:` Set handoff whose plans are ready.
  - Execution state: pending

### Task group 2: the consumers

- [ ] E-02 Call the predicate from both `aw backlog set` spellings (the `--status` path in `backlog.run_set` and the positional path in `status_set.apply_status_change` / `run_set_command` for backlog records) when the normalized target is `graduated` and the current status is not already `graduated`; on not-ready, refuse with exit 1, write nothing, and print the shared human rendering or the `aw.agent/v1` record listing each plan and finding with its remedy. Evaluate BEFORE any write and before the item file moves directories, at the same point as the existing `evaluate_blocking_close` call on each path, and reuse that refusal's output shape (its exit code and agent record kind) so both refusals read alike. When `--gate-dir` is given (the runner's isolated turn passes it, see `runner_shared` `--gate-dir` notes), evaluate against the tree the item file is in (`--dir`), where the produced plans are, NOT the gate tree, because the plans this check reads exist only in the lane until integration; record the choice in the evidence.
  - Depends on: E-01
  - Expected outcome: `aw backlog set graduated <item>` and `aw backlog set <item> --status graduated` both refuse on the same not-ready fixture with the same findings and leave the file bytes and location unchanged, and both succeed on a ready fixture; a `graduated -> graduated` same-status note is not checked.
  - Execution state: pending

- [ ] E-03 Call the predicate from `aw specs set` (both spellings) when the normalized target is `implementing` and the current status is `approved`; refuse the same way.
  - Depends on: E-02
  - Expected outcome: `aw specs set implementing <spec>` refuses on a fixture whose produced orchestrator has a `draft` child and succeeds on a ready one.
  - Execution state: pending

- [ ] E-04 Add `check.graduation-incomplete` (severity `error`) to `check_engine.py`, registered in the backlog and specs check families, reporting every `graduated` backlog item and every `implementing` spec whose handoff the predicate finds not ready, with observed/required/recovery fields (recovery: `aw backlog set open <id6>` then re-run graduation; for a spec, `aw specs set approved <path>` if legal, else name the plan to fix). GRANDFATHER BY A NEW CUTOVER, which is required, not optional: measured at review, 189 items are `graduated` and 88 have no active handoff (42 completed handoffs, ready by E-01; 46 with no linked plan or spec, of which 40 carry a resolving `- Graduated-To:` Set and 6 carry nothing), plus 1 whose only linked active plan is `draft` (`bmhoxe` -> `yqv6b7`), and spec `z7nbn1` is `implementing` with all six linked plans terminal; CI runs `aw check backlog` fail-closed. Register `graduation_ready` in `config.KNOWN_FEATURE_CUTOVERS` (the dict beside `release_gate_at_rest`, with the same "FEATURE INTRODUCTION date" comment) and stamp it into `.aw/config/project.json` `cutovers` with the date this plan lands; judge an item only when its LAST `graduated` history date (the newest `- <date> graduated` line, read with the same history helpers `_item_close_date` uses) is on or after the cutover, and a spec only when its `implementing` transition is. Re-derive the counts at execution.
  - Depends on: E-03
  - Expected outcome: `aw check backlog` reports a fixture `graduated` item, graduated after the cutover, whose orchestrator was set back to `draft`, and does not report the same fixture graduated before the cutover; on the real tree it reports nothing (every live item predates the cutover or has a ready handoff), and `aw check backlog` / `aw check specs` add no other finding; a warm `aw check backlog` grows by no more than 1 s over a pre-edit baseline (measured at review: 124 active linked plans lint at `author` in about 1.1 s, the carrier index walks in about 0.5 s, so lint only the post-cutover population).
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_handoff_ready_gate.py` driving the CLI as subprocesses over fixture repositories with coverage answers pre-written into the fixture orchestrators: each predicate failure kind; both backlog setter spellings refusing identically and writing nothing; both succeeding on a ready Set; the spec setter twin; the check rule reporting a drifted `graduated` item; and the production path still succeeding end to end (reuse one `tests/test_backlog_production.py` fixture with a ready Set) so the runner's own setter call is not refused; and an isolated (lane) production run graduating against plans that exist only in the lane (PR-007). Prove the tests can fail by making the predicate always ready and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation fails it; `tests/test_backlog_production.py`, `tests/test_spec_production.py` and the existing release-gate tests still pass.
  - Execution state: pending

- [ ] E-06 Repair the existing tests that graduate an item with no handoff, WITHOUT weakening what each asserts. MEASURED AT REVIEW by a spy on `evaluate_blocking_close` over the bare suite (`5080 passed`, 3 pre-existing failures unrelated): 24 tests in 9 files call the setter toward `graduated` with ZERO `From-Backlog` carriers, and would be refused: `tests/test_backlog.py` (1), `tests/test_backlog_gate_follows_status.py` (2), `tests/test_backlog_history_dedup_parity.py` (1), `tests/test_backlog_transition_gate.py` (4), `tests/test_history_label_parity.py` (3), `tests/test_plan_transition_gate.py` (1), `tests/test_status_set.py` (5), and in `tests/test_backlog_production.py` `TestBacklogProductionE08.test_case5b_agent_sets_graduated_before_handoff_commit`. That list is context; RE-DERIVE it with the same spy at execution. For each fixture-only case, add a ready linked `to-review` child plan (the `_write_conforming_plan` shape) to the fixture so the transition under test is still exercised. `test_case5b` asserts `BACKLOG-GRADUATE-LEGITIMACY` because the scripted agent sets the item `graduated` before writing its plan; after this plan that early setter call is REFUSED, the item stays `open`, and the runner's own gated transition proceeds, so the asserted outcome legitimately changes: update it to the new outcome (the agent's early call refused, item `graduated` by the runner) and name the before and after assertions in V-06. `tests/test_backlog_transition_gate.py`'s fence-edge tests assert that `open -> graduated` and `blocked -> graduated` relocate the file; keep those assertions with a ready fixture plan.
  - Depends on: E-02
  - Expected outcome: every listed test passes with its original assertion intact (except `test_case5b`, whose change is named); the spy re-run reports no `graduated` setter call with zero carriers outside tests that assert a refusal.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE PREDICATE BACKS BOTH SETTER SPELLINGS. `evaluate_blocking_close` is the precedent; `aw backlog set` forks on whether `--status` was passed, so a gate wired into one path fires for one spelling only (the comment above `decide_gate_default`'s call in `backlog.run_set` records exactly this hazard).
- CI RUNS `aw check backlog` FAIL-CLOSED (`.github/workflows/tests.yml`, step "aw check backlog (backlog conformance; fail closed)"); a new `error` rule must be green on the real tree when it lands, which Order 09's ordering ensures.
- CUTOVERS ARE STAMPED PER REPOSITORY (`config.resolve_cutover_date`, `sync_cutovers_on_install`; `.aw/config/project.json` `cutovers`), and an at-rest rule judges only records dated on or after its cutover (`check_release_gate_consistency`'s at-rest arm, `release_gate_at_rest`).
- THE SINGLE-ITEM CARRIER SCANNER MUST NOT BE CALLED IN A LOOP (`find_from_backlog_artifacts`; `tests/test_carrier_scan_single_item_contract.py`); a sweep uses `_from_backlog_carrier_index`.
- `- Graduated-To:` IS THE SOURCE-SIDE HANDOFF LINK (`.aw/records/backlog/README.md`), resolving if any plan in any directory carries the Set.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `graduated` is unconditionally legitimate. `evaluate_blocking_close`'s branch commented "`graduated` is EXPLICITLY legitimate for a release-gated item and drops nothing" returns `CloseVerdict(True, "ok", ...)` for a gated item; there is no lookup of `From-Backlog` plans for this target. | the quoted branch in `evaluate_blocking_close` |
| F-02 | The production path sets `graduated` through the same setter (`aw backlog set <id6> --status graduated --no-commit`), so after Order 06 it reaches the setter only with a ready Set and passes this gate; no production regression is expected, and E-05 proves it. | the setter argv in the backlog production branch of `execute_item_core` |
| F-04 | The corpus already holds many graduations the new rule would reject. 189 `graduated` items: 88 with no active handoff (42 all-terminal, 40 `Graduated-To` only, 6 nothing), 1 with a `draft` handoff plan; spec `z7nbn1` `implementing` with all linked plans terminal. | review scan with `_iter_plan_ipds`, `_iter_spec_records`, `backlog._iter_items` |
| F-05 | 24 existing tests graduate an item with no handoff and would be refused. | spy on `evaluate_blocking_close` over the bare suite |
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

- Over-scope: none. Four production modules (predicate, two setter paths, spec setter), the cutover registration and stamp, one new test file, and the existing test files whose fixtures graduate without a handoff.
- Under-scope: grandfathering, completed-handoff and `Graduated-To` handling, and the existing-test repair (E-06) added at review.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_handoff_ready_gate.py tests/test_backlog_production.py tests/test_spec_production.py tests/test_check_engine_release_gate.py tests/test_status_set.py -q` pasted.
- Mutation run pasted; the spy re-run pasted (E-06).
- On the real tree: `python3 -m agent_workflows check backlog` and `check specs` after the change, pasted, showing no `check.graduation-incomplete` finding.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `77tr3o` R-13 (source side) as amended by Order 01. The `.aw/records/backlog/README.md` description of `graduated` ("design handed off to a plan/spec") is now enforced and needs no wording change; Order 11 updates `AGENTS.md`.

## Open questions

### OQ-01: Should the setter ask the probe when no verdict is recorded?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO, as for `aw ipd set` (Order 05 OQ-01): the setter reads the coverage record in the plan and an absent or out-of-date one is a finding naming `aw ipd coverage <id6>`. The production path records the answer in the orchestrator before calling the setter, so the common path never hits this.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's diff and test output for the four failure kinds and the three ready cases (ready Set, completed handoff, `Graduated-To` Set).
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
  - Required evidence: paste the rule and cutover registration diffs and the `project.json` stamp; the fixture `aw check backlog` output reporting the post-cutover drifted item and not the pre-cutover twin; the real-tree `aw check backlog` / `aw check specs` before and after with no new finding; the re-derived population counts; and warm `time` of `aw check backlog` before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new file passing with its count; the production regression case passing; the mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the spy re-run's list before and after the repair; the diff of each repaired fixture; `test_case5b`'s before and after assertion; and the targeted run of the nine files passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Requires `52opph`, `26m1nb` and `r2wa38` executed first (and through them `qs00nc`); if `orchestrator_readiness.review_readiness` is absent, STOP and report. Scope fence: the declared `- Scope-Paths:` are the surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. Under a runner, the runner owns `aw ipd begin`/`aw ipd finalize`; by hand, run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-move the plan to `executed/`.
