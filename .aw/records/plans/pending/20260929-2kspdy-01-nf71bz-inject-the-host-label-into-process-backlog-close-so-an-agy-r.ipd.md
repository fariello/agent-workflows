# IPD: Inject the host label into process_backlog_close so an agy run stops claiming aw oc run closed the item

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared.process_backlog_close` builds the backlog-close message from the LITERAL host label `aw oc run`, and BOTH hosts run that one body, so an ANTIGRAVITY-driven run records a false provenance claiming an OpenCode run closed the item. The literal is the string `closed by aw oc run: IPD ` in `runner_shared.process_backlog_close` (one occurrence in all of `agent_workflows/`, measured at authoring). It lands in TWO durable, human-read sinks, not one: the backlog-close COMMIT (via the injected `commit_backlog_close`) and the item's own TRACKED `## Workflow history` line (via `close_backlog_item`, which passes it as `aw backlog set --message`). A maintainer auditing which runner closed an item is actively misled by both. It is a wrong answer rather than a slow one, which is why the carrying item is `bug` and gates the next release.
- Scope: IN: (a) add a default-free keyword-only `host_label: str` parameter to `runner_shared.process_backlog_close` and build the message from it; (b) bind each host's own value in the two one-line wrappers (`oc_runipd.process_backlog_close` -> `OC_HOST_LABELS.command`, `agy_runipd.process_backlog_close` -> `AGY_HOST_LABELS.command`), reading the value from the EXISTING `HostLabels.command` field rather than writing a fresh literal; (c) a new behavior test that drives the real shared function per host and asserts the label in the message actually reaching the closers, plus a no-default test. OUT: the four prose-only `oc` tokens the carrying item already cleared as correct (`queue_sort_key`, `run_order_rationale`, `render_runs_pointer`, `dependency_status_detailed`); any change to WHICH items close, to the close eligibility verdict, to the release-gate predicate, or to the lane-versus-main write tree; any change to `HostLabels` itself or to the other host-label call sites that are already correct; restoring the deleted `tests/test_runner_backlog_close.py` / `tests/test_runner_layering.py` (F-05).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_backlog_close_host_label.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 2kspdy
- Blocks-Release: next
- Set: 2kspdy
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: nf71bz

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 2kspdy. Authoring measurement RESOLVED the item's open conditional and CORRECTED two of its coordinates: the re-home it wondered about has already happened, so this item does carry the fix (F-02); the defect is now at `runner_shared.process_backlog_close`, NOT `oc_runipd.py:2007` (F-01); the shared function is already injection-shaped with three closers, so no lift is needed (F-03); and the two tests the item cites as precedent were DELETED, so the precedent survives only in code (F-05). The blast radius is also WIDER than the item states: the label reaches the item's tracked workflow history as well as the commit (F-04).
- 2026-09-29 draft (aw oc run): created.

## Goal

Make the backlog-close record name the runner that actually did the close. After this plan the host label is a parameter with NO DEFAULT, each host binds its own from the existing `HostLabels.command` descriptor, and a test proves an `agy` run writes `aw agy run` where it previously wrote `aw oc run`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the premise at the execution base

- [ ] E-01 Re-measure the defect where it actually lives now, because the carrying item's coordinate is stale (F-01) and a fix applied to the old address would be a no-op. Run `grep -rn "closed by aw" agent_workflows/ --include=*.py` and confirm EXACTLY ONE hit, inside `runner_shared.process_backlog_close`. Then confirm no host-label parameter exists anywhere in the chain and that the correct per-host values are already available as data:

  ```
  python3 -c "
  import inspect
  from agent_workflows import runner_shared as rs, oc_runipd, agy_runipd
  print('shared:', list(inspect.signature(rs.process_backlog_close).parameters))
  print('oc   :', list(inspect.signature(oc_runipd.process_backlog_close).parameters))
  print('agy  :', list(inspect.signature(agy_runipd.process_backlog_close).parameters))
  print('OC .command :', rs.OC_HOST_LABELS.command)
  print('AGY .command:', rs.AGY_HOST_LABELS.command)"
  ```

  - Depends on: none
  - Expected outcome: one literal hit in the shared body; NO `host_label` in any of the three signatures; and `.command` already reading `aw oc run` / `aw agy run`. STOP AND REPORT if the literal is absent or already parameterized: the defect would already be fixed and this plan's premise wrong.
  - Execution state: pending

### Task group 2: Make the label a parameter and bind it per host

- [ ] E-02 In `runner_shared.process_backlog_close`, add a keyword-only `host_label: str` with NO DEFAULT, placed beside the three existing injected closers (`run_checked`, `close_backlog_item`, `commit_backlog_close`), and build the message from it, replacing the literal `f"closed by aw oc run: IPD {item['id6']} executed "` with the interpolated label. Change NOTHING else about the message: the remainder (`({verdict.reason}); evidence {verdict.evidence}`) stays byte-identical, so an `oc` run's record is unchanged. Document in the docstring WHY there is no default, citing the established `integrate_lane_branch(..., host_label=)` precedent and the two durable sinks from F-04.
  - Depends on: E-01
  - Expected outcome: the shared body contains no `aw oc run` literal; `inspect.signature` shows `host_label` as KEYWORD_ONLY with no default, so a host that forgets to bind it raises `TypeError` at the call rather than silently misattributing.
  - Execution state: pending

- [ ] E-03 Bind each host's own label in its existing one-line wrapper, passing `host_label=runner_shared.OC_HOST_LABELS.command` in `oc_runipd.process_backlog_close` and `host_label=runner_shared.AGY_HOST_LABELS.command` in `agy_runipd.process_backlog_close`. Read the value from the `HostLabels` descriptor; do NOT write a fresh string literal in either wrapper, since a second copy of a value that already exists as data is how these two drifted in the first place. Keep both wrappers a SINGLE delegating `return runner_shared.<same name>(...)` statement so they remain the shape the shared-not-copied convention requires (F-03).
  - Depends on: E-02
  - Expected outcome: both wrappers still delegate in one statement and both now pass a label; no new string literal is introduced in either driver.
  - Execution state: pending

### Task group 3: Pin the behavior so it cannot regress

- [ ] E-04 Add `tests/test_backlog_close_host_label.py` with tests that exercise the REAL shared function per host (no source inspection, no substring search of production code): for each of `oc_runipd` and `agy_runipd`, call that host's `process_backlog_close` against a temp git repo holding a genuine open backlog item and a satisfying executed carrier, with the two closers replaced by recording fakes, then assert on the `message` argument each closer ACTUALLY received. Assert the `oc` host's message begins `closed by aw oc run:` and the `agy` host's begins `closed by aw agy run:`, and assert the two differ. Add one test asserting `host_label` has NO DEFAULT in the shared signature (via `inspect.signature`, which reads the live callable's contract rather than its source text) and one asserting the non-label remainder of the message is unchanged for the `oc` host, so the fix is proven not to have disturbed the existing record shape.
  - Depends on: E-03
  - Expected outcome: a test file that fails on the pre-fix code at the `agy` assertion and passes after, covering both sinks by asserting on what `close_backlog_item` and `commit_backlog_close` each received.
  - Execution state: pending

- [ ] E-05 Run the full suite BARE as `python3 -m pytest` and confirm no regression against the authoring baseline of `3246 passed, 2 skipped`. Pay specific attention to `tests/test_backlog_production.py` (which drives both hosts through the close path and is the most likely place a missing binding surfaces) and `tests/test_hostdedup_third_host.py` (whose test-defined third `HostLabels` is the standing argument for the no-default choice).
  - Depends on: E-04
  - Expected outcome: the suite is green with the new tests included and the count has risen by the number of tests E-04 adds; no pre-existing test needed modification.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A host-varying string reaching durable output is a PARAMETER supplied by the calling host, never a literal in shared code. The canonical precedent is `runner_shared.integrate_lane_branch`, whose `host_label` is KEYWORD_ONLY with NO DEFAULT (verified live via `inspect.signature`, reported `KEYWORD_ONLY default= NO DEFAULT`).
- The NO-DEFAULT choice is itself a documented convention, not a style preference. `runner_shared.HostLabels`'s class docstring states it has "NO DEFAULTS, on purpose", for the reason that a defaulted value "would misattribute in durable history which driver reconciled a scope, and that misattribution is invisible until someone audits the record". That reasoning describes THIS defect exactly.
- The two per-host values this plan needs already exist as data on that descriptor: `HostLabels.command` is documented as "The operator-facing command prefix, e.g. `aw oc run`", and reads `aw oc run` / `aw agy run` on the two live instances.
- Each host keeps a one-line wrapper that binds its own host-specific dependencies and delegates in a SINGLE statement to `runner_shared.<same name>`; a comment block above the four backlog-close wrappers in both drivers records that the structural single-statement shape is asserted on purpose and is a STRONGER claim than object identity.
- `process_backlog_close` is deliberately given its closers by injection rather than resolving them in shared globals, because in-tree tests patch `close_backlog_item` to spy on the gated setter's argv; a shared body resolving that name itself "would bypass every such patch, turning a fail-closed test green while the gate it guards went unexercised". A new host-label parameter follows that same established seam.
- Tests here must assert observable behavior, never code structure: no `inspect.getsource`, `ast`, regex, or substring search over production source (AGENTS.md, GUIDING_PRINCIPLES P16). Reading a signature with `inspect.signature` is a CONTRACT check on a live callable, not a source-text check, which is why E-04 uses it for the no-default assertion.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S COORDINATE IS STALE, and this is the one finding an executor must absorb before editing. The item reports the literal at `agent_workflows/oc_runipd.py:2007`. It is NOT there. The function was re-homed and the literal now lives in `runner_shared.process_backlog_close`, which is where the fix belongs; editing `oc_runipd` would change nothing. | `grep -rn "closed by aw" agent_workflows/ --include=*.py` returns exactly ONE hit, in `runner_shared.py`, and zero hits in `oc_runipd.py`. |
| F-02 | THE ITEM'S OPEN CONDITIONAL RESOLVES TO "THIS ITEM CARRIES THE FIX". The item ends by saying that if runnerlayer 02 (`1f7xno`) re-homes the function, the label becomes that plan's question, otherwise this item carries it. That plan IS executed, and the re-home DID happen, but it moved the body verbatim and left the literal intact. So the conditional is settled in this item's favor: the re-home did not fix it and nothing else will. | `1f7xno` is in `.aw/records/plans/executed/` with a `2026-09-23 executed` history line; the literal survives in the re-homed body per F-01. |
| F-03 | NO LIFT IS NEEDED, ONLY A PARAMETER. The shared function is ALREADY injection-shaped, taking `run_checked`, `close_backlog_item` and `commit_backlog_close` as keyword-only injected dependencies, and each host already has a one-line wrapper that binds them. The fix is therefore one added parameter and two added bindings, with no restructuring. | `inspect.signature(runner_shared.process_backlog_close)` reports `['run_dir', 'state', 'item', 'lane_repo', 'lane_handle', 'run_checked', 'close_backlog_item', 'commit_backlog_close', 'wrote_in']`; both host wrappers report `['run_dir', 'state', 'item', 'lane_repo', 'lane_handle']`. |
| F-04 | THE BLAST RADIUS IS WIDER THAN THE ITEM STATES: TWO DURABLE SINKS, NOT ONE. The item describes only the commit message. The SAME string is also passed to `close_backlog_item` as `aw backlog set --message`, which writes it into the item's own TRACKED `## Workflow history`. So the false label is committed to the record twice, and one of those copies is inside a tracked file that outlives any commit-message archaeology. | Proven by running the real setter against a scratch repo: `aw backlog set <id> --status done --message "closed by aw oc run: IPD abc123 executed (proof)"` produced the on-disk line `- 2026-09-29 set (aw backlog): closed by aw oc run: IPD abc123 executed (proof)` in the item file. |
| F-05 | THE CITED TEST PRECEDENT NO LONGER EXISTS, so an executor must not go looking for it. The item points at `tests/test_runner_shared.py::test_the_host_label_has_NO_DEFAULT_in_the_shared_function` and `test_each_runner_binds_its_OWN_host_label`, and at `tests/test_runner_layering.py` for the host-neutrality criterion. All three are GONE, deleted by the suite-trim commit. The no-default convention survives in the CODE (and in `HostLabels`'s docstring), not in a test, which is exactly why E-04 must add one. | `git log --diff-filter=D --name-only` shows commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted both `tests/test_runner_backlog_close.py` and `tests/test_runner_layering.py`; the two named test functions are absent from the current `tests/`. |
| F-06 | NOTHING TODAY PINS THE MESSAGE, which is why a one-string defect survived a re-home. No test in `tests/` asserts on the close message's content at all. | `grep -rn "closed by aw" tests/` returns no hit outside `tests/fixtures/` (where it appears only inside a recorded pre-move AST fingerprint, which pins the OLD body's shape and is not a behavior assertion). |
| F-07 | BINDING IN THE TWO WRAPPERS COVERS EVERY CALL PATH, so no internal caller is missed. All five in-module call sites reach the function through the INJECTED host wrapper rather than the module global: four enclosing functions take `process_backlog_close` as a parameter, and `execute_item_core` additionally re-binds it from the driver module with `getattr(driver_module, "process_backlog_close", ...)`. Only the two drivers call `runner_shared.process_backlog_close` directly, and each does so from its own wrapper. | AST walk over `runner_shared.py` shows the call sites enclosed by `finish_reintegrated_item`, `integrate_retired_lane`, `execute_item_core` and `perform_coordinator_backlog_close`, each with `injected_param=True`; `grep` for `runner_shared.process_backlog_close` outside `runner_shared.py` hits only `oc_runipd.py` and `agy_runipd.py`, one line each. |
| F-08 | A DEFAULT WOULD BE ACTIVELY UNSAFE, not merely untidy, because a THIRD host already constructs `HostLabels`. `tests/test_hostdedup_third_host.py` builds a `SCRIPTED_HOST_LABELS` descriptor and a standing test requires every `HostLabels` instance in `runner_shared` to be routable. A defaulted `host_label` would make a future third host silently inherit `aw oc run`, reproducing this exact bug with no failing test. | `SCRIPTED_HOST_LABELS = runner_shared.HostLabels(...)` at `tests/test_hostdedup_third_host.py:38`, consumed by `test_registry_closure_every_host_labels_routable_by_analytics`. |
| F-09 | THE BASELINE IS GREEN, so any failure during execution is attributable to this change. | `python3 -m pytest` at the authoring base: `3246 passed, 2 skipped, 3 warnings in 53.17s`. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/runner_shared.py`: add keyword-only `host_label: str` with NO DEFAULT to `process_backlog_close`, interpolate it into the close message in place of the `aw oc run` literal, and record the no-default rationale (F-04, F-08) in the docstring. (E-02)
2. `agent_workflows/oc_runipd.py`: pass `host_label=runner_shared.OC_HOST_LABELS.command` from the existing one-line wrapper. (E-03)
3. `agent_workflows/agy_runipd.py`: pass `host_label=runner_shared.AGY_HOST_LABELS.command` from the existing one-line wrapper. (E-03)
4. `tests/test_backlog_close_host_label.py`: new behavior tests per host asserting the message each closer actually received, plus the no-default contract test and an unchanged-remainder test for `oc`. (E-04)
5. Full bare suite run against the F-09 baseline. (E-05)

## Deferred / out of scope (with reason)

- The four prose-only `oc` tokens in `queue_sort_key`, `run_order_rationale`, `render_runs_pointer` and `dependency_status_detailed`: the carrying item measured them as correct (comment/docstring only, no executable effect). Touching them would be unmeasured churn.
  - Carrier-Declined: Nothing is owed, because there is no defect here to carry. The carrying backlog item MEASURED these four by stripping comments and docstrings from all 56 imported definitions and scanning the remainder: their `oc` tokens survive in PROSE ONLY and have no executable effect, so each is already correct. Filing an item would record four correct functions as outstanding work. Recorded here so a reviewer does not read the silence as a claim they were never examined.
- Restoring `tests/test_runner_backlog_close.py` and `tests/test_runner_layering.py` (F-05): that is suite-trim restoration work, a much larger job than a one-parameter fix, and it belongs to the same family as the other restoration items rather than being smuggled in here. OQ-01 records it.
  - Carrier: p7k57l
- Any change to close ELIGIBILITY (the verdict, the release-gate predicate, the lane-versus-main write tree): this plan changes only the LABEL in a message. The close decision is a separate and much higher-risk surface with its own fail-closed tests.
  - Carrier-Declined: This row records a PROHIBITION on this plan rather than a deferred defect, so nothing is owed. No finding in this plan measures a fault in the close-eligibility path; it behaves as specified and has its own fail-closed tests. Widening a one-string label fix into that surface is the risk this fence exists to prevent, and the prohibition is enforced inside this plan by the scope fence and by V-05's requirement that no pre-existing test be modified.
- Any change to `HostLabels` itself: the field this plan needs (`command`) already exists and already holds the right value per host.
  - Carrier-Declined: Nothing is owed, because the requirement is already met. F-01's live measurement shows `HostLabels.command` already reads `aw oc run` / `aw agy run` on the two host instances, which is precisely the data E-03 binds. There is no gap to carry; a future third host inherits the field by construction, and F-08 explains why the NO-DEFAULT choice is what protects it.

## Scope check

- Over-scope: none. The three production paths are the one shared definition plus the two host bindings, which F-07 shows is the minimum set that covers every call path; the fourth path is the new test.
- Under-scope: the fix does NOT retroactively correct records already written with the wrong label. Those are permanent history, committed and, per F-04, also written into tracked item files; rewriting them would mean editing an executed record, which the execution contract forbids. Any such record stays as it is and the fix is forward-only. No live artifact is left in a broken state by that choice.

## Required tests / validation

- The new per-host behavior tests in `tests/test_backlog_close_host_label.py`, which must be demonstrated FAILING on the pre-fix code at the `agy` assertion before the fix is applied (V-04).
- The full suite BARE (`python3 -m pytest`) against the F-09 baseline of `3246 passed, 2 skipped` (V-05).
- A live signature check that `host_label` is keyword-only with no default (V-02).

## Spec / documentation sync

N/A. No `.spec.md` governs the close message's host label, and no user-facing doc quotes it: the string is generated into a commit message and a workflow-history line, never documented as a contract. This plan declares no spec paths in `- Scope-Paths:` for that reason. The rationale lives in the code, in the amended `process_backlog_close` docstring (E-02).

## Open questions

### OQ-01: Should the two deleted test files be restored, and by whom?

- Blocking: no
- Status: open
- Owner: none
- Carrier: p7k57l
- Resolution or deferral rationale: DEFERRED to backlog item `p7k57l`, filed while authoring this plan, and deliberately not resolved here. F-05 measured that commit `19313eed` deleted `tests/test_runner_backlog_close.py` and `tests/test_runner_layering.py`, which is why this one-string defect could survive a re-home with a green suite (F-06). This plan closes the specific hole by pinning the close message's label (E-04), which is the part its own fence covers. Restoring the broader layering and shared-not-copied coverage is a much larger job in the suite-trim restoration family and must not be smuggled into a one-parameter bug fix. Not blocking, because this plan's own validation does not depend on it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual output of `grep -rn "closed by aw" agent_workflows/ --include=*.py` showing EXACTLY ONE hit and that it is in `runner_shared.py`, plus the actual stdout of the E-01 `python3 -c` block showing no `host_label` in any of the three signatures and `.command` reading `aw oc run` / `aw agy run`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual output of `python3 -c "import inspect; from agent_workflows import runner_shared as rs; p=inspect.signature(rs.process_backlog_close).parameters['host_label']; print(p.kind, 'NO DEFAULT' if p.default is inspect._empty else repr(p.default))"` showing `KEYWORD_ONLY NO DEFAULT`. Then paste `grep -rn "closed by aw" agent_workflows/ --include=*.py` showing the `aw oc run` literal is GONE from the shared body (the remaining hit, if any, must be the interpolated form). Also paste the actual `TypeError` from calling the shared function with the label omitted, proving it fails loudly rather than defaulting.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the actual stdout of a check that BOTH hosts pass a label and that neither wrapper introduces a new literal: `grep -n "host_label" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing each passes `runner_shared.<OC|AGY>_HOST_LABELS.command` (not a quoted string), and `grep -c "aw agy run\|aw oc run" ` over the two wrapper bodies showing no new string literal was added.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: FIRST demonstrate the test catching the live bug: with the E-02/E-03 changes stashed or reverted, run `python3 -m pytest tests/test_backlog_close_host_label.py -o addopts=""` and paste the actual FAILING output showing the `agy` assertion failing with `aw oc run` observed where `aw agy run` was expected. THEN restore the fix and paste the actual PASSING output of the same command with per-test counts. A test that passes both before and after has not proven anything and must be rewritten.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL final summary line of a BARE `python3 -m pytest` run (the `N passed` line, with no added flags), showing no failures and a passed count at or above the F-09 baseline of 3246 plus the tests E-04 added. Explicitly confirm `tests/test_backlog_production.py` and `tests/test_hostdedup_third_host.py` are among the passing tests and that no pre-existing test file was modified (`git diff --stat` over `tests/` should show only the new file).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: one new keyword-only parameter on one shared function, one changed f-string, two one-line bindings in the existing host wrappers, and one new test file. No close-eligibility logic, no gate predicate, no `HostLabels` change, and no existing test modified.

THREE AUTHORING CORRECTIONS TO THE BACKLOG ITEM THE APPROVER SHOULD KNOW, all measured rather than assumed. FIRST, the item's code coordinate is STALE: the literal is no longer in `oc_runipd.py` but in the re-homed `runner_shared.process_backlog_close` (F-01), so an executor following the item literally would edit the wrong file and change nothing. SECOND, the item's own open conditional is RESOLVED: runnerlayer 02 `1f7xno` did re-home the function, but it moved the body verbatim and left the literal, so this item carries the fix exactly as its last sentence anticipated (F-02). THIRD, the defect is WORSE than the item states: the false label reaches the item's tracked `## Workflow history` as well as the commit message (F-04, proven by running the real setter), so it is committed to the record twice.

WHY NO DEFAULT, since that is the one design decision here: it is the established convention rather than a preference, and `HostLabels`'s own docstring gives the reason this defect proves ("misattribution is invisible until someone audits the record"). It also has a concrete future payoff, because a third host descriptor already exists in the test suite and a default would let it silently inherit `aw oc run` with no failing test (F-08).

WHAT THIS DELIBERATELY DOES NOT DO, so the approver is not surprised. Records already written with the wrong label are NOT corrected; they are permanent history and rewriting them would mean editing executed records. The two deleted test files that let this survive a re-home are NOT restored (F-05, OQ-01); that is suite-trim restoration work, not a one-parameter fix.

GENUINE STOP CONDITIONS: E-01 finds the literal absent or already parameterized (the premise would be wrong), or the V-04 pre-fix run does NOT fail (the test would be proving nothing and must be rewritten). Neither is a scope question; both are conditions under which proceeding would record something false.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check passed that was not run. V-04 specifically requires demonstrating the new test FAILING before the fix. Author tests against observable behavior only: assert on the arguments the closers receive and on the live signature, never by reading production source with `inspect.getsource`, `ast`, or regex. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the four paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

Commit ONLY the paths in `- Scope-Paths:` through `aw commit nf71bz -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize nf71bz --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `2kspdy`; AFTER EXECUTION, and not before, set that item `done` with `--evidence` citing this executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `2kspdy` fails closed because the gate is handed to a carrier that has not shipped, so the item stays `graduated` until `aw ipd finalize` has moved this plan to `executed/`.
