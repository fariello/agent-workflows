# IPD: Run the coverage probe only where a run can retire an orchestrator, and again at retirement

- Date: 2026-10-04
- Kind: child
- Concern: `runner_shared.enforce_orchestrator_probe_gate` probes every queued orchestrator, chosen by `queued_orchestrator_targets`, which filters on `kind == "orchestrator"` and never on the item's action. A `review` action cannot retire anything (retirement happens only in `dispatch_orchestrator_item`, which both hosts call only for `action == "orchestrate"`), so on 2026-10-03 three `--action review` runs over 53 plans were refused before any turn, after a 3-minute probe and a 180-second unanswered prompt each, over 13 orchestrators none of which they could retire. Conversely, the run-start probe is the ONLY coverage check before retirement: an orchestrator edited by a child's turn during the run (an orchestrator review legitimately reads and edits children, per `classify_review_writes`) is retired on a verdict for text that no longer exists. Spec `25kzda` 2.5b as amended by Order 01 (A.1, A.2, A.5) requires both changes.
- Scope: IN: restrict the run-start gate's targets to queued orchestrators whose frozen action is `orchestrate`; announce, in one line, how many queued orchestrators were not probed because the run cannot retire them; call the Order 03 shared check `orchestrator_readiness.review_readiness(..., ask=True)` inside `dispatch_orchestrator_item` on the `ORCH_DISPATCH_RETIRE` path immediately before `ipd_lifecycle.retire_orchestrator`, turning a not-ready COVERAGE result (condition 4 only; conditions 1 to 3 stay with the existing retirement gates, OQ-02) into the existing `ORCH_REASON_FINALIZE_REFUSED` termination with the findings as detail; keep the override flag and phrase scoped to the run-start gate only. OUT: the probe's prompt and parser (Order 02); the readiness function itself (Order 03); the retirement predicate `evaluate_set_retirement` and the transition `retire_orchestrator` (unchanged); the shape gate `enforce_orchestrator_shape_gate` (unchanged; it still runs over every queued orchestrator because it is free and deterministic).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_orchestrator_probe_scope.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: executed:qs00nc
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 5etev3

## Workflow history
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-007..PR-011 (round 2, all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-007 to PR-011 (round 2). Fixed: retirement re-check refuses on coverage findings only, so a `superseded` child or a `pending/` child at `executed` no longer blocks retirement (`31y86f`; PR-007); dirty-plan ordering settled from Order 02's commit-at-write (PR-008); asker/runner seams for dispatch and host-argv test specified and demonstrated (PR-009); existing tests needing a record measured and named, stale "seed a verdict" wording replaced (PR-010); third mutation, test list and V-items reconciled (PR-011).
- 2026-10-05 to-review (aw set): returned to review after revision: maintainer ruling 2026-10-04 stores the coverage answer in the plan (25kzda 2.5e), resolving blocking OQ-03; every affected plan was rewritten to match
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): revised after review. Maintainer ruling 2026-10-04: the coverage answer is stored in the plan itself (`25kzda` 2.5e, Order 02's `coverage_record`), not in the gitignored 30-day cache. E-02's cache wording changed to the plan's record; the retirement-time write must be reconciled with `_assert_rollup_touched_only_owned_paths` (a dirty plan file refuses retirement), which E-02 now requires the executor to settle and record.
- 2026-10-04 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 (all fixed)

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-006. Fixed: probe host string is `oc`/`agy` passed from each loop, not the state's CLI identity (PR-001); existing retirement tests get seeded verdicts and are declared in scope (PR-002); refusal goes through the existing terminate tail with the shared remedy in the detail (PR-003); frozen retry budget passed (PR-004); action-filter soundness under `--full-auto` and the empty-target event specified (PR-005); could-not-ask and per-host cases, scope fence and honesty rule (PR-006).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 04 of Set `gradcover`. Implements spec `25kzda` 2.5b A.1, A.2 and A.5 and spec `77tr3o` R-12 as amended by Order 01 (B.1). The two changes ship together so no commit exists in which retirement is unchecked.

## Goal

Stop review runs being refused by a check that guards an outcome they cannot produce, and make every retirement re-check the orchestrator's current text instead of trusting an answer taken before the run's turns.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scope the run-start probe

- [ ] E-01 Give `queued_orchestrator_targets` a keyword `actions` filter (default `None` meaning all, so `enforce_orchestrator_shape_gate` is unchanged) and call it from `enforce_orchestrator_probe_gate` with `actions={"orchestrate"}`. The frozen action is the right key because the in-run `--full-auto` bridge in `execute_item_core` rewrites a promoted review item only to `execute`, never to `orchestrate` (the `item["action"] = "execute"` assignment after `set_plan_approved`), so no orchestrator becomes retirable mid-run without having been `orchestrate` at queue build; and queue build already promotes a `reviewed` orchestrator to `auto-approved` under `--full-auto` BEFORE `action_for` runs, so it is frozen `orchestrate` and is probed. Measured at review: `action_for('orchestrator', s)` is `undetermined`/`review`/`orchestrate`/`orchestrate`/`orchestrate` for `draft`/`to-review`/`reviewed`/`approved`/`auto-approved`. When the filtered target list is EMPTY, record the event with `probed: []`, `calls: 0` and the skipped field, and proceed without prompting. Emit one stderr line and one `orchestrator-probe-gate` event field naming the count and id6s of queued orchestrators NOT probed because their action is not `orchestrate`, so an operator can see they were deliberately skipped. Leave the could-not-ask, override and interactive-phrase behavior otherwise unchanged.
  - Depends on: none
  - Expected outcome: a run whose queued orchestrators are all `review` makes zero probe calls and is not refused by the coverage gate; a run with an `orchestrate` orchestrator still probes it; the event lists both the probed and the skipped id6s.
  - Execution state: pending

### Task group 2: re-check at retirement

- [ ] E-02 In `dispatch_orchestrator_item`, on the `ORCH_DISPATCH_RETIRE` branch, after `plan_path` is located and before `_lifecycle.retire_orchestrator` is called, call `orchestrator_readiness.review_readiness(repo, plan_path, ask=True, state=state, host=<host>)` (function-local import), passing `retry_budget=frozen_retry_budget(state)` through to the probe so the re-check uses the run's frozen budget. `<host>` is the `oc`/`agy` string `probe_argv` branches on, obtained per E-03. ONLY CONDITION 4 (COVERAGE) DECIDES HERE: the retirement re-check refuses on the result's coverage findings (absent or out-of-date record after asking, recorded `fail` quotes, could-not-ask, `unknown`) and IGNORES its condition 1 to 3 findings, because at this point those conditions are already enforced, differently and authoritatively, by the retirement gates: rows by `evaluate_set_retirement` (unauthored rows refuse), children by the same predicate's terminal allowlist `set_retirement_terminal_statuses` (`executed`, `superseded`, `not-executed`), and row conformance by `retire_orchestrator`'s `IPD-S407` gate. Applying 2.5d condition 2 here would REGRESS backlog `31y86f`: a Set with a deliberately `superseded` child is retirement-eligible (measured at review: `evaluate_set_retirement` returns `eligible=True` for a Set with one `superseded/` and one `executed/` child) but fails condition 2, whose ready list excludes `superseded`; and a child whose turn landed `- Status: executed` while still under `pending/` (the `test_reconsidered_then_retired_in_the_same_run_on_both_hosts` fixture) lints `IPD-S404`/`IPD-M105` at `author`. Select the coverage findings by the finding codes Order 03 assigns to condition 4 (one named constant set, defined beside `review_readiness` in `orchestrator_readiness` if Order 03 did not already export one; if it must be added there, record the out-of-scope edit with `--scope-reason`). When not ready, do NOT call `retire_orchestrator`; rewrite the decision to `ORCH_DISPATCH_TERMINATE` with `ORCH_REASON_FINALIZE_REFUSED` and a detail of the form `retirement re-check refused: <finding subject>: <quoted passage>; <shared remedy>; ...`, and let the EXISTING terminate tail write the refusal (it already calls `record_refusal` with `orchestrator_refusal_text(decision.reason)` and appends `orchestrator-deferred` with `terminated: True`); do not add a second `record_refusal` call. The existing `ORCH_REASON_FINALIZE_REFUSED` remedy says to retire "through `aw ipd finalize`", which does not fit this cause, so the detail itself carries the Order 03 shared remedy per finding (for could-not-ask, `aw ipd coverage <id6>`); leave the shared remedy constant unchanged. Treat could-not-ask as not ready (spec `25kzda` 2.5d UNAVAILABILITY). The item's status is whatever the existing terminate tail writes for `finalize-refused` today (`terminal_status`, default `fail-depend`), exactly as every other retirement refusal; the plan file stays in `pending/`; do not invent a new status.
  - Depends on: E-01
  - Dirty-plan ordering (settled at review from Order 02 `8mabmu` E-07, no executor choice left): when the re-check asks, `probe_orchestrator` writes the record AND makes its own path-scoped commit of the plan file before returning, so the plan is clean again when `retire_orchestrator` later runs `_assert_rollup_touched_only_owned_paths`; when the plan already had another party's uncommitted edit, `probe_orchestrator` writes nothing and the retirement is refused by that existing dirty-plan gate, which is correct. Do NOT add a second commit path here. If Order 02 as executed does not commit at write (check `coverage_record.write`'s `commit` behavior before editing), STOP and report, because the retirement would then always refuse after an ask.
  - Expected outcome: an orchestrator whose text changed during the run to add uncovered prose is not retired, its item carries a `Refusal` whose reason contains the new passage, and `retire_orchestrator` is never called; an unchanged orchestrator whose plan carries a current `- Coverage: pass` record is retired with zero model calls; a could-not-ask refuses and names `aw ipd coverage <id6>`.
  - Execution state: pending

- [ ] E-03 Make the host available to `dispatch_orchestrator_item` without forking it. Neither host loop passes a host today (`oc_runipd.run_queue` and `agy_runipd.run_queue` pass only `recovery_hint=...HOST_LABELS.dependency_block_recovery`), and run state's `host_capabilities.host` is `resolve_cli_host`'s CLI identity (`opencode`/`antigravity`), NOT the `oc`/`agy` string `probe_argv` branches on, so reading it as-is would send an agy run's re-check through the opencode argv. Add keyword-only `host: str | None = None`, `asker: Any = None` and `runner: Any = None` parameters to `dispatch_orchestrator_item` (the latter two passed straight through to `review_readiness` as test seams; no host loop passes them), pass `host="oc"` from `oc_runipd.run_queue` and `host="agy"` from `agy_runipd.run_queue` (the literals each module passes to `initialize_run_core`), and when `host` is `None` (an existing direct caller) map `state["host_capabilities"]["host"] == "antigravity"` to `agy`, else `oc`. Confirm the override flag `--allow-uncovered-orchestrator-work` does NOT bypass the retirement-time check (spec `25kzda` 2.5b A.5): the re-check must not read any field the run-start gate writes for the override.
  - Depends on: E-02
  - Expected outcome: both hosts reach the same re-check through the one shared function with the correct host string; an agy run's re-check composes the agy argv; a run started with the override flag still refuses a retirement whose re-check fails.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_orchestrator_probe_scope.py`, using the existing in-process `initialize_run` test pattern with an injected `asker` double: (a) a queue of one `review` orchestrator plus children makes zero asker calls and proceeds; (b) a queue with one `orchestrate` orchestrator calls the asker once; (c) the event records skipped id6s; (d) `dispatch_orchestrator_item` over a fixture Set whose children are all `executed` and whose orchestrator text was edited after a recorded pass (the edit adds uncovered prose to an allowlisted `PROBE_PROSE_SECTIONS` section, so the fingerprint changes) refuses retirement and records a refusal quoting the new passage; (e) the same with unchanged text retires with zero asker calls; (f) the override flag does not change (d); (g) a could-not-ask at retirement refuses and names `aw ipd coverage <id6>`; (h) both hosts' `run_queue` reach the re-check with their own host string; (i) a Set with one `superseded/` child and one `executed/` child and a current `pass` record still retires (the `31y86f` property; it fails if E-02 lets a condition 1 to 3 finding refuse). SEAMS, since neither `run_queue` nor today's `dispatch_orchestrator_item` takes an asker: E-03 adds keyword-only `asker=None, runner=None` to `dispatch_orchestrator_item`, passed through to `review_readiness`, which (d) to (g) and (i) use directly; (h) drives the real `run_queue` and patches `runner_shared.ask_orchestrator_probe` with a wrapper that calls the real function with a `runner` double recording `argv[0]` (demonstrated at review: with `host="agy"` the recorded token is `agy`, and `probe_argv(..., host="oc")` begins `opencode`). Fixtures for (d), (e), (g), (h), (i) write the coverage record into the fixture orchestrators with `coverage_record.write` (non-git fixtures: pass Order 02's no-commit option, or rely on its documented never-raises behavior on a failed commit, and record which); the real spawn raises under pytest (`_assert_probe_spawn_is_permitted`). Prove the test can fail by restoring the unfiltered target list (fails (a)), by removing the re-check call (fails (d)), and by letting every readiness finding refuse (fails (i)), pasting all three. EXISTING TESTS: `tests/test_orchestrator_retirement.py` reaches the RETIRE branch with only `retire_orchestrator` patched; after E-02 those paths ask the probe first and would raise `DriverError` under pytest. Measured at review by a dispatch spy over that file plus `test_oc_runipd.py`, `test_agy_runipd_cli.py`, `test_dependency_block_reporting.py`, `test_orchestrator_not_approved_reason.py`, `test_reaskscore_composed.py`, `test_action_table_runner_parity.py`, `test_run_viewer.py` and `test_driver_attestation_gate.py` (400 passed): exactly three tests reach the branch, all in `tests/test_orchestrator_retirement.py` (`test_reconsidered_then_retired_in_the_same_run_on_both_hosts`, `test_the_orchestrate_branch_SHORT_CIRCUITS_before_execute_item_on_both_hosts`, both retiring, and `test_each_cause_yields_a_DISTINCT_reason_and_a_detail_that_substantiates_it`, whose patched transition refuses). That list is context; RE-DERIVE it at execution with the bare suite (any `DriverError` naming the coverage probe is a test that needs a record). Make them pass WITHOUT changing what they assert, by writing a current `pass` coverage record into each fixture orchestrator in their setup, and record which tests were touched.
  - Depends on: E-03
  - Expected outcome: the new file passes; each of the three mutations fails its case; `tests/test_orchestrator_retirement.py` passes with its assertions unchanged; no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `--prepare-only` ALREADY SKIPS THE PROBE and announces it (the branch in `initialize_run_core` before `enforce_orchestrator_probe_gate`); the new skip announcement follows that wording style.
- BOTH HOSTS REACH THE GATE THROUGH ONE SEAM (`initialize_run_core`), and both call the same `dispatch_orchestrator_item`; the `pgq326` lesson recorded in `initialize_run_core` is that a decision computed but not dispatched on one host is a defect.
- THE RETIREMENT REFUSAL MUST NOT SPIN. `dispatch_orchestrator_item`'s docstring requires a refusal at retirement to TERMINATE, never RECONSIDER, because a structural refusal retried each iteration spins. The new re-check uses that branch.
- `runner_shared` HAS A PINNED MODULE-LEVEL IMPORT SET (`tests/test_lost_guard_census.py` `test_no_new_module_level_first_party_import_in_runner_shared`); the call into `orchestrator_readiness` must be function-local.
- THE PROBE'S HOST KEY IS `oc`/`agy`, NOT THE CLI IDENTITY. `initialize_run_core` passes `host` (`"oc"`/`"agy"`) to `enforce_orchestrator_probe_gate`, and `probe_argv` branches on `host == "agy"`; `state["host_capabilities"]["host"]` holds `resolve_cli_host`'s value (`opencode`/`antigravity`), measured at review.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The run-start target list ignores action. `queued_orchestrator_targets` skips an item only when `kind != "orchestrator"`; `enforce_orchestrator_probe_gate` probes every target. | the two function bodies |
| F-02 | Retirement happens only for `orchestrate`. Both `oc_runipd` and `agy_runipd` call `dispatch_orchestrator_item` only inside `if runnable.get("action") == "orchestrate":`. `action_for` returns `orchestrate` for an orchestrator at `reviewed`/`approved` and `review` at `to-review`. | the two host dispatch branches; `action_for('orchestrator', s)` measured for `draft`, `to-review`, `reviewed`, `approved` |
| F-03 | The 2026-10-03 cost per refused run: run created at 17:20, probe-gate event at 17:24 (about 3.5 minutes of probe calls over 3 or 4 orchestrators), then a 180-second unanswered prompt, then refusal. | `run-created` and `orchestrator-probe-gate` timestamps in the four run directories; the "(no answer in 180.0s; taking the automatic decision)" console text |
| F-05 | Existing retirement tests reach the real RETIRE branch with only `retire_orchestrator` patched and no coverage answer recorded; under pytest an un-injected probe raises `DriverError` (measured at review). | `patch.object(LC, "retire_orchestrator", ...)` sites in `tests/test_orchestrator_retirement.py`; `_assert_probe_spawn_is_permitted` |
| F-06 | Spec 2.5d's full readiness is STRICTER than retirement eligibility in two ways that matter at the RETIRE branch: condition 2 excludes `superseded`/`not-executed` children, which `evaluate_set_retirement` accepts (backlog `31y86f`); and it lints non-terminal-directory children at `author`, where a child whose `- Status: executed` sits under `pending/` errors (`IPD-S404`, `IPD-M105`). Hence E-02 refuses on coverage findings only. | measured at review in a temp fixture: `evaluate_set_retirement(...).eligible == True` for one `superseded/` plus one `executed/` child; `ipd_lint.lint_file(child, checkpoint="author")` on a `pending/` child at `- Status: executed` returns `error` with `IPD-S404` and `IPD-M105`; `set_retirement_terminal_statuses` returns `ipd_schema.TERMINAL` |
| F-04 | The retirement path trusts the run-start verdict. `dispatch_orchestrator_item`'s RETIRE branch calls `retire_orchestrator` directly after `decide_orchestrator_dispatch`; `retire_orchestrator` re-runs `orchestrator_row_conformance` (the `IPD-S407` gate) but never the coverage verdict. | the RETIRE branch; the "GATE: orchestrator row conformance (IPD-S407)" block in `retire_orchestrator` |

## Proposed changes (ordered, validatable)

1. Filter the run-start probe targets by action and announce the skipped ones (E-01).
2. Add the readiness re-check on the RETIRE branch, terminating with the existing finalize-refused reason (E-02).
3. Thread the host into the shared dispatch without forking, and keep the override off the retirement check (E-03).
4. Tests and mutation proof (E-04).

## Deferred / out of scope (with reason)

- SHORTENING THE 180-SECOND INTERACTIVE PROMPT TIMEOUT. A separate usability question; with this plan a review run no longer reaches the prompt at all.
  - Carrier-Declined: the measured symptom (review runs blocked) is removed; no remaining defect measured
- PROBING AT THE MOMENT AN ORCHESTRATOR'S REVIEW FINISHES. That is the `IPD-REVIEW-ORCHESTRATOR-READY` check, wired by Order 07 together with its correction turn.
  - Carrier: nnsa2o

## Scope check

- Over-scope: none. One shared production module (plus, only if Order 03 exported no condition-4 code set, one constant in `orchestrator_readiness.py`, justified with `--scope-reason`), a one-argument change in each host loop, one new test file, and coverage records written into the existing retirement test file's fixture orchestrators (with `coverage_record.write`).
- Under-scope: an `orchestrate` run over the 13 refused orchestrators is still refused at run start, correctly; Order 09 reopens them.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing, failing node ids recorded.
- `python3 -m pytest -o addopts="" tests/test_orchestrator_probe_scope.py tests/test_orchestrator_retirement.py tests/test_driver_attestation_gate.py tests/test_orchestrator_shape_gate.py tests/test_orchestrator_shape_composed.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_action_table_runner_parity.py tests/test_lost_guard_census.py -q` pasted.
- Three mutation runs pasted (E-04).
- A real `aw oc run --action review --prepare-only` is NOT sufficient evidence (prepare-only already skips the probe); instead paste case (a)'s event record from the test.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` 2.5b A.1, A.2, A.5 and `77tr3o` R-12 (B.1) as amended by Order 01. No spec edited here. The `AGENTS.md` paragraph "The runners own ordering, isolation, and orchestrators" describes when the gate runs; Order 11 updates it.

## Open questions

### OQ-01: Should the shape gate also be scoped to `orchestrate` items?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO. The shape gate (`enforce_orchestrator_shape_gate`) is deterministic, spends nothing, and runs before the run directory exists; a review run benefits from learning about a non-conforming row because the review can repair it (`r07vma` R5). The cost that motivated scoping the probe (minutes of model calls and a blocking prompt) does not apply.

### OQ-02: Which `review_readiness` findings refuse a retirement?

- Blocking: no
- Status: resolved
- Owner: reviewer (/plan-review round 2)
- Resolution or deferral rationale: RESOLVED: condition 4 (coverage) only. Spec `25kzda` 2.5b A.2 (as amended by Order 01) names the cause it closes, an orchestrator "edited by a child's turn after the run-start probe", and says a refusal carries "the quoted finding", which is the coverage answer; conditions 1 to 3 are enforced at retirement by `evaluate_set_retirement` and `retire_orchestrator`'s `IPD-S407` gate already. Refusing on condition 2 would regress backlog `31y86f` (F-06, measured). Order 01's A.6 CONSUMERS sentence lists "the retirement-time re-check" as a caller of the function without restricting which conditions decide; this plan reads that as "calls the function", which A.2's wording supports. A re-scope note in Order 01 records the reading so its executor can make the sentence explicit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `queued_orchestrator_targets` and `enforce_orchestrator_probe_gate`. Paste test (a)'s asker call count (0) and proceed result, test (b)'s call count (1), and test (c)'s event record showing `probed` and the new skipped field.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the RETIRE branch. Paste test (d)'s recorded refusal (code `finalize-refused`, reason containing the quoted passage), item status, and the `retire_orchestrator` spy's call count (0); test (e)'s `orchestrator-finalized` event with asker call count 0; test (g)'s refusal naming `aw ipd coverage <id6>`; and test (i)'s `orchestrator-finalized` event for the Set with a `superseded/` child, proving only coverage findings refuse here. State whether a condition-4 code set was exported by Order 03 or added (with its `--scope-reason`), and paste `coverage_record.write`'s commit behavior as checked before editing (the dirty-plan ordering prerequisite).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diffs in both host modules showing `host="oc"` and `host="agy"` passed to `dispatch_orchestrator_item`, and the new `host`/`asker`/`runner` parameters with the `None` host fallback. Paste test (h)'s recorded argv first token per host (`opencode` for oc, `agy` for agy), and test (f)'s output showing the override flag did not change the refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new file passing with its count; each of the three mutations (unfiltered targets, removed re-check, every finding refusing) failing its case and the revert passing; the list of existing tests in `tests/test_orchestrator_retirement.py` given a recorded coverage answer; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Scope fence: the five `- Scope-Paths:` are the declared surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. E-01 and E-02 must land in the same commit so retirement is never unchecked. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
