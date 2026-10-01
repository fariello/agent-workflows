# IPD: Inject the host label into process_backlog_close so an agy run stops claiming aw oc run closed the item

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared.process_backlog_close` builds the backlog-close message from the LITERAL host label `aw oc run`, and BOTH hosts run that one body, so an ANTIGRAVITY-driven run records a false provenance claiming an OpenCode run closed the item. The literal is the string `closed by aw oc run: IPD ` in `runner_shared.process_backlog_close` (one occurrence in all of `agent_workflows/`, measured at authoring). It lands in TWO durable, human-read sinks, not one: the backlog-close COMMIT (via the injected `commit_backlog_close`) and the item's own TRACKED `## Workflow history` line (via `close_backlog_item`, which passes it as `aw backlog set --message`). A maintainer auditing which runner closed an item is actively misled by both. It is a wrong answer rather than a slow one, which is why the carrying item is `bug` and gates the next release.
- Scope: IN: (a) add a default-free keyword-only `host_label: str` parameter to `runner_shared.process_backlog_close` and build the message from it; (b) bind each host's own value in the two one-line wrappers (`oc_runipd.process_backlog_close` -> `OC_HOST_LABELS.command`, `agy_runipd.process_backlog_close` -> `AGY_HOST_LABELS.command`), reading the value from the EXISTING `HostLabels.command` field rather than writing a fresh literal; (c) a new behavior test that drives the real shared function per host and asserts the label in the message actually reaching the closers, plus a no-default test. OUT: the four prose-only `oc` tokens the carrying item already cleared as correct (`queue_sort_key`, `run_order_rationale`, `render_runs_pointer`, `dependency_status_detailed`); any change to WHICH items close, to the close eligibility verdict, to the release-gate predicate, or to the lane-versus-main write tree; any change to `HostLabels` itself or to the other host-label call sites that are already correct; restoring the deleted `tests/test_runner_backlog_close.py` / `tests/test_runner_layering.py` (F-05).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_backlog_close_host_label.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 2kspdy
- Blocks-Release: next
- Set: 2kspdy
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: nf71bz
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED, zero deferred, zero open. THE PLAN IS CORRECT AND I VERIFIED IT BY BUILDING IT at HEAD `5790526b`, rather than by reading it. Every E-01 premise reproduces exactly: `grep -rn "closed by aw" agent_workflows/ --include=*.py` returns ONE hit in `runner_shared.py` and zero in `oc_runipd.py`; no `host_label` in any of the three signatures; `.command` already reads `aw oc run` / `aw agy run`. I then APPLIED E-02 and E-03 as a trial patch and drove both hosts' real `process_backlog_close`: the literal left the package entirely, the signature reported `KEYWORD_ONLY NO DEFAULT`, omitting the binding raised `TypeError: process_backlog_close() missing 1 required keyword-only argument: 'host_label'`, the `oc` host wrote `closed by aw oc run:` and the `agy` host wrote `closed by aw agy run:`, and a bare suite passed `3371 passed, 2 skipped` with no pre-existing test modified. Patch reverted; nothing from it committed (F-10). I also CONFIRMED THE DEFECT AT THE MESSAGE LEVEL for the first time: at base, both hosts' `close_backlog_item` AND `commit_backlog_close` receive `closed by aw oc run:`, so F-04's two-sink claim is now observed rather than inferred (F-11). PR-001 (HIGH): E-04's fixture as specified would never have reached the message. `evaluate_backlog_close` applies the earned gate, so an open item plus an executed carrier returns `close=False` with "this run executed none of its carriers, so the close was not earned" and builds NO message; the test would have asserted on `None` and passed before and after. I hit this on the first probe; the working recipe (`item["last_plan_path"]` absolute, do NOT pre-set `earned_paths` because the function overwrites it) is now in E-04 with a mandatory `closed is True` guard, and V-04 now refuses a pre-fix failure whose cause is the fixture (F-12). PR-002 (MEDIUM): E-02 said to place the parameter "beside the three existing injected closers", but the keyword-only block ends with a DEFAULTED `wrote_in`; the shape I actually drove appends after it, and `wrote_in` is bound by no caller anywhere, so grouping a required parameter before it would misread. PR-003 (MEDIUM): F-09's baseline was stale by 125 tests in one day (`3246` authored, `3371` measured), and it sat in E-05's and V-05's acceptance bars; both now require the executor's own pre-edit measurement. PR-004 (MEDIUM): F-08 overstated its evidence, claiming `test_registry_closure_every_host_labels_routable_by_analytics` consumes `SCRIPTED_HOST_LABELS`; it discovers labels from `vars(runner_shared)` (yielding only the two real hosts) and names the descriptor in its docstring alone, while `test_pin_measured_turn_execution_limits` pins that a descriptor-only host cannot execute a turn at all. The no-default case is sound on the convention and the surviving `integrate_lane_branch` precedent, so the row is corrected rather than dropped. Also corrected: both drivers still cite the DELETED `tests/test_runner_backlog_close.py::SharedNotCopied` as the guard on the single-delegating-statement shape (zero hits in `tests/`), now recorded as under-scope and carried by `p7k57l`. PR-005: the gate gained the post-review status sentence, the feasibility paragraph, the review-corrections paragraph, and a stale-import warning. OQ-01 RESOLVED as already-answered: the carrier `p7k57l` is filed, `open`, and accurately scoped. Findings and decisions D-1..D-4 in `.aw/records/reviews/20260929-2kspdy-01-nf71bz-inject-the-host-label-into-process-backlog-close-so-an-agy-r.review.md`.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 2kspdy. Authoring measurement RESOLVED the item's open conditional and CORRECTED two of its coordinates: the re-home it wondered about has already happened, so this item does carry the fix (F-02); the defect is now at `runner_shared.process_backlog_close`, NOT `oc_runipd.py:2007` (F-01); the shared function is already injection-shaped with three closers, so no lift is needed (F-03); and the two tests the item cites as precedent were DELETED, so the precedent survives only in code (F-05). The blast radius is also WIDER than the item states: the label reaches the item's tracked workflow history as well as the commit (F-04).
- 2026-09-29 draft (aw oc run): created.

## Goal

Make the backlog-close record name the runner that actually did the close. After this plan the host label is a parameter with NO DEFAULT, each host binds its own from the existing `HostLabels.command` descriptor, and a test proves an `agy` run writes `aw agy run` where it previously wrote `aw oc run`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the premise at the execution base

- [x] E-01 Re-measure the defect where it actually lives now, because the carrying item's coordinate is stale (F-01) and a fix applied to the old address would be a no-op. Run `grep -rn "closed by aw" agent_workflows/ --include=*.py` and confirm EXACTLY ONE hit, inside `runner_shared.process_backlog_close`. Then confirm no host-label parameter exists anywhere in the chain and that the correct per-host values are already available as data:

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
  - Execution state: performed

### Task group 2: Make the label a parameter and bind it per host

- [x] E-02 In `runner_shared.process_backlog_close`, add a keyword-only `host_label: str` with NO DEFAULT, placed beside the three existing injected closers (`run_checked`, `close_backlog_item`, `commit_backlog_close`), and build the message from it, replacing the literal `f"closed by aw oc run: IPD {item['id6']} executed "` with the interpolated label. Change NOTHING else about the message: the remainder (`({verdict.reason}); evidence {verdict.evidence}`) stays byte-identical, so an `oc` run's record is unchanged. Document in the docstring WHY there is no default, citing the established `integrate_lane_branch(..., host_label=)` precedent and the two durable sinks from F-04.
  PLACE IT AFTER `wrote_in`, NOT BETWEEN THE CLOSERS, and the reason is mechanical rather than stylistic (review PR-002). The current keyword-only block ends `commit_backlog_close, wrote_in: str | None = None`, so inserting a NO-DEFAULT parameter before `wrote_in` is legal Python for keyword-only arguments but leaves a defaulted parameter reading as though it were part of the required injection group. Appending after `wrote_in` was the shape review actually drove end to end (both hosts, real function, correct labels, suite green), so it is the shape with evidence behind it. `wrote_in` is also NEVER BOUND by any caller today (measured: zero `wrote_in=` call sites anywhere in `agent_workflows/`), which is precisely why it must not be mistaken for a live injected dependency when reading the signature.
  - Depends on: E-01
  - Expected outcome: the shared body contains no `aw oc run` literal; `inspect.signature` shows `host_label` as KEYWORD_ONLY with no default, so a host that forgets to bind it raises `TypeError` at the call rather than silently misattributing. Review drove exactly this and measured `TypeError: process_backlog_close() missing 1 required keyword-only argument: 'host_label'`, so that is the expected text.
  - Execution state: performed

- [x] E-03 Bind each host's own label in its existing one-line wrapper, passing `host_label=runner_shared.OC_HOST_LABELS.command` in `oc_runipd.process_backlog_close` and `host_label=runner_shared.AGY_HOST_LABELS.command` in `agy_runipd.process_backlog_close`. Read the value from the `HostLabels` descriptor; do NOT write a fresh string literal in either wrapper, since a second copy of a value that already exists as data is how these two drifted in the first place. Keep both wrappers a SINGLE delegating `return runner_shared.<same name>(...)` statement so they remain the shape the shared-not-copied convention requires (F-03).
  - Depends on: E-02
  - Expected outcome: both wrappers still delegate in one statement and both now pass a label; no new string literal is introduced in either driver.
  - Execution state: performed

### Task group 3: Pin the behavior so it cannot regress

- [x] E-04 Add `tests/test_backlog_close_host_label.py` with tests that exercise the REAL shared function per host (no source inspection, no substring search of production code): for each of `oc_runipd` and `agy_runipd`, call that host's `process_backlog_close` against a temp git repo holding a genuine open backlog item and a satisfying executed carrier, with the two closers replaced by recording fakes, then assert on the `message` argument each closer ACTUALLY received. Assert the `oc` host's message begins `closed by aw oc run:` and the `agy` host's begins `closed by aw agy run:`, and assert the two differ. Add one test asserting `host_label` has NO DEFAULT in the shared signature (via `inspect.signature`, which reads the live callable's contract rather than its source text) and one asserting the non-label remainder of the message is unchanged for the `oc` host, so the fix is proven not to have disturbed the existing record shape.
  THE FIXTURE MUST EARN THE CLOSE, AND THIS IS THE ONE THING MOST LIKELY TO COST AN EXECUTOR A PASS (review PR-001). An item with an open status and an executed carrier is NOT sufficient: `evaluate_backlog_close` applies the E-04 earned gate, so a fixture that merely HAS an executed carrier returns `close=False` with `"this run executed none of its carriers, so the close was not earned (all carriers were already executed before this run)"`, and no message is ever built, so the test asserts on `None` and proves nothing. Review hit exactly this on the first attempt. THE WORKING RECIPE, driven end to end at review: set `item["last_plan_path"]` to the ABSOLUTE path of the executed carrier, which `collect_earned_paths` relativizes into the earned set; do NOT pre-set `item["earned_paths"]`, because `process_backlog_close` OVERWRITES it from `collect_earned_paths` before the verdict is taken. The queue item needs `id6`, `from_backlog`, and `last_plan_path`; the state needs `repo`, `run_id`, and `queue`. Assert the verdict actually closed (`item["backlog_close"]["closed"] is True`) BEFORE asserting on the message, so a future fixture drift fails loudly instead of silently asserting on `None`.
  PATCH THE CLOSERS ON THE HOST MODULE, NOT ON `runner_shared`. Each host wrapper passes its OWN `close_backlog_item` / `commit_backlog_close`, so `mock.patch.object(mod, "close_backlog_item", fake)` is what the injection seam is for (and is the reason the injection exists per the Step 0 convention); patching `runner_shared`'s copies would not be seen. Redirect stdout/stderr, because the success path prints a colored confirmation line.
  BEWARE A STALE-IMPORT FALSE NEGATIVE, recorded because review hit it and briefly mis-concluded the fix did not work. A probe script placed in a SUBDIRECTORY resolved `agent_workflows` from a DIFFERENT checkout (Python puts the script's own directory on `sys.path`, not the repo root), so it exercised unpatched code and reported `aw oc run` for both hosts after a correct fix. A test under `tests/` run through `python3 -m pytest` from the repo root does not have this problem; the warning exists for any ad-hoc probe an executor writes while iterating. Confirm `agent_workflows.__file__` points inside the working tree before believing a negative result.
  - Depends on: E-03
  - Expected outcome: a test file that fails on the pre-fix code at the `agy` assertion and passes after, covering both sinks by asserting on what `close_backlog_item` and `commit_backlog_close` each received. Review PRE-VERIFIED this is achievable: driving both hosts' real `process_backlog_close` with the recipe above produced `closed by aw oc run: ...` for BOTH hosts at base (the defect, reproduced at the message level for the first time) and `closed by aw oc run:` / `closed by aw agy run:` respectively after a trial fix.
  - Execution state: performed

- [x] E-05 Run the full suite BARE as `python3 -m pytest` and confirm no regression against a baseline MEASURED AT THE EXECUTION BASE, not against any number written in this plan. Pay specific attention to `tests/test_backlog_production.py` and `tests/test_hostdedup_third_host.py`, both of which drive both hosts and are the likeliest places a missing binding surfaces.
  MEASURE YOUR OWN BASELINE FIRST; THE AUTHORED ONE IS ALREADY WRONG (review PR-003). F-09 records `3246 passed, 2 skipped` from 2026-09-29. Re-measured at review one day later: `3371 passed, 2 skipped`, a rise of 125 from unrelated work. So take a bare run BEFORE the first edit, record that number, and require `>= baseline + <new tests>` against it. A plan-quoted absolute count is a live-artifact bar and cannot be one (the repository's own re-derivation convention).
  REVIEW ALREADY RAN THE SUITE AGAINST A TRIAL FIX AND IT WAS GREEN, which bounds the regression risk but does NOT substitute for this item: a trial patch is not the authored change, and no new test existed in that run. Result recorded in the review record so the executor can compare rather than re-discover.
  - Depends on: E-04
  - Expected outcome: the suite is green with the new tests included and the count has risen by the number of tests E-04 adds, measured against the executor's OWN pre-edit baseline; no pre-existing test needed modification.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A host-varying string reaching durable output is a PARAMETER supplied by the calling host, never a literal in shared code. The canonical precedent is `runner_shared.integrate_lane_branch`, whose `host_label` is KEYWORD_ONLY with NO DEFAULT (verified live via `inspect.signature`, reported `KEYWORD_ONLY default= NO DEFAULT`).
- The NO-DEFAULT choice is itself a documented convention, not a style preference. `runner_shared.HostLabels`'s class docstring states it has "NO DEFAULTS, on purpose", for the reason that a defaulted value "would misattribute in durable history which driver reconciled a scope, and that misattribution is invisible until someone audits the record". That reasoning describes THIS defect exactly.
- The two per-host values this plan needs already exist as data on that descriptor: `HostLabels.command` is documented as "The operator-facing command prefix, e.g. `aw oc run`", and reads `aw oc run` / `aw agy run` on the two live instances.
- Each host keeps a one-line wrapper that binds its own host-specific dependencies and delegates in a SINGLE statement to `runner_shared.<same name>`; a comment block above the four backlog-close wrappers in both drivers records that the structural single-statement shape is asserted on purpose and is a STRONGER claim than object identity.
- THAT COMMENT'S CITED ASSERTION NO LONGER EXISTS, and an executor must not go looking for it (added at review). Both drivers say the shape is asserted by `tests/test_runner_backlog_close.py::SharedNotCopied`; measured, `grep -rn SharedNotCopied tests/` returns ZERO hits and the only surviving mentions are four comments in `oc_runipd.py` (two), `agy_runipd.py`, and `runner_shared.py`. So the single-statement shape is a live CONVENTION with no enforcement, which is exactly why E-03 must preserve it by discipline and why backlog `p7k57l` carries its restoration. Adding a keyword argument keeps the wrapper a single `return` statement, so the convention is honored either way.
- The surviving host-label precedent that IS tested is `integrate_lane_branch`: `tests/test_runner_shared.py::test_a_clean_lane_still_integrates_and_carries_ITS_OWN_host_label` drives BOTH hosts and asserts the label POSITIVELY (this host's present) and NEGATIVELY (the other host's absent), keying off a `HOST_LABELS = {"oc_runipd": "aw oc run", "agy_runipd": "aw agy run"}` table. That test is the shape E-04 should imitate, including the negative assertion.
- `process_backlog_close` is deliberately given its closers by injection rather than resolving them in shared globals, because in-tree tests patch `close_backlog_item` to spy on the gated setter's argv; a shared body resolving that name itself "would bypass every such patch, turning a fail-closed test green while the gate it guards went unexercised". A new host-label parameter follows that same established seam.
- Tests here must assert observable behavior, never code structure: no `inspect.getsource`, `ast`, regex, or substring search over production source (AGENTS.md, GUIDING_PRINCIPLES P16). Reading a signature with `inspect.signature` is a CONTRACT check on a live callable, not a source-text check, which is why E-04 uses it for the no-default assertion.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S COORDINATE IS STALE, and this is the one finding an executor must absorb before editing. The item reports the literal at `agent_workflows/oc_runipd.py:2007`. It is NOT there. The function was re-homed and the literal now lives in `runner_shared.process_backlog_close`, which is where the fix belongs; editing `oc_runipd` would change nothing. | `grep -rn "closed by aw" agent_workflows/ --include=*.py` returns exactly ONE hit, in `runner_shared.py`, and zero hits in `oc_runipd.py`. |
| F-02 | THE ITEM'S OPEN CONDITIONAL RESOLVES TO "THIS ITEM CARRIES THE FIX". The item ends by saying that if runnerlayer 02 (`1f7xno`) re-homes the function, the label becomes that plan's question, otherwise this item carries it. That plan IS executed, and the re-home DID happen, but it moved the body verbatim and left the literal intact. So the conditional is settled in this item's favor: the re-home did not fix it and nothing else will. | `1f7xno` is in `.aw/records/plans/executed/` with a `2026-09-23 executed` history line; the literal survives in the re-homed body per F-01. |
| F-03 | NO LIFT IS NEEDED, ONLY A PARAMETER. The shared function is ALREADY injection-shaped, taking `run_checked`, `close_backlog_item` and `commit_backlog_close` as keyword-only injected dependencies, and each host already has a one-line wrapper that binds them. The fix is therefore one added parameter and two added bindings, with no restructuring. | `inspect.signature(runner_shared.process_backlog_close)` reports `['run_dir', 'state', 'item', 'lane_repo', 'lane_handle', 'run_checked', 'close_backlog_item', 'commit_backlog_close', 'wrote_in']`; both host wrappers report `['run_dir', 'state', 'item', 'lane_repo', 'lane_handle']`. Re-verified at review, identical. Review additionally measured the DEFAULTS, which matter for E-02's placement: `lane_repo`/`lane_handle`/`wrote_in` default to `None` while the three closers have NO DEFAULT, and `wrote_in` is bound by no caller anywhere in `agent_workflows/`. |
| F-04 | THE BLAST RADIUS IS WIDER THAN THE ITEM STATES: TWO DURABLE SINKS, NOT ONE. The item describes only the commit message. The SAME string is also passed to `close_backlog_item` as `aw backlog set --message`, which writes it into the item's own TRACKED `## Workflow history`. So the false label is committed to the record twice, and one of those copies is inside a tracked file that outlives any commit-message archaeology. | Proven by running the real setter against a scratch repo: `aw backlog set <id> --status done --message "closed by aw oc run: IPD abc123 executed (proof)"` produced the on-disk line `- 2026-09-29 set (aw backlog): closed by aw oc run: IPD abc123 executed (proof)` in the item file. |
| F-05 | THE CITED TEST PRECEDENT NO LONGER EXISTS, so an executor must not go looking for it. The item points at `tests/test_runner_shared.py::test_the_host_label_has_NO_DEFAULT_in_the_shared_function` and `test_each_runner_binds_its_OWN_host_label`, and at `tests/test_runner_layering.py` for the host-neutrality criterion. All three are GONE, deleted by the suite-trim commit. The no-default convention survives in the CODE (and in `HostLabels`'s docstring), not in a test, which is exactly why E-04 must add one. | `git log --diff-filter=D --name-only` shows commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted both `tests/test_runner_backlog_close.py` and `tests/test_runner_layering.py`; the two named test functions are absent from the current `tests/`. |
| F-06 | NOTHING TODAY PINS THE MESSAGE, which is why a one-string defect survived a re-home. No test in `tests/` asserts on the close message's content at all. | `grep -rn "closed by aw" tests/` returns no hit outside `tests/fixtures/` (where it appears only inside a recorded pre-move AST fingerprint, which pins the OLD body's shape and is not a behavior assertion). |
| F-07 | BINDING IN THE TWO WRAPPERS COVERS EVERY CALL PATH, so no internal caller is missed. All five in-module call sites reach the function through the INJECTED host wrapper rather than the module global: four enclosing functions take `process_backlog_close` as a parameter, and `execute_item_core` additionally re-binds it from the driver module with `getattr(driver_module, "process_backlog_close", ...)`. Only the two drivers call `runner_shared.process_backlog_close` directly, and each does so from its own wrapper. | AST walk over `runner_shared.py` shows the call sites enclosed by `finish_reintegrated_item`, `integrate_retired_lane`, `execute_item_core` and `perform_coordinator_backlog_close`, each with `injected_param=True`; `grep` for `runner_shared.process_backlog_close` outside `runner_shared.py` hits only `oc_runipd.py` and `agy_runipd.py`, one line each. |
| F-08 | A DEFAULT WOULD BE ACTIVELY UNSAFE, not merely untidy, because a THIRD host already constructs `HostLabels`. `tests/test_hostdedup_third_host.py` builds a `SCRIPTED_HOST_LABELS` descriptor, so a third host is a shape the suite already exercises, and a defaulted `host_label` would let such a host silently inherit `aw oc run`, reproducing this exact bug with no failing test. CORRECTED AT REVIEW (PR-004): the authored row claimed the routability test CONSUMES that descriptor, and it does not. `test_registry_closure_every_host_labels_routable_by_analytics` discovers labels by scanning `vars(runner_shared)`, which yields exactly `OC_HOST_LABELS` and `AGY_HOST_LABELS`; `SCRIPTED_HOST_LABELS` lives in the test module and is named in that test only inside its DOCSTRING. The third host is consumed by `test_initialize_run_core_succeeds_with_third_host_descriptor` instead, and `test_pin_measured_turn_execution_limits` pins that a descriptor-only host cannot execute a turn at all, so it never reaches `process_backlog_close` today. The no-default argument therefore rests on the CONVENTION (`HostLabels`'s own "NO DEFAULTS, on purpose" docstring and the `integrate_lane_branch` precedent) plus the third-host shape being a live fixture, NOT on a standing test that would fail. Stated precisely so the design decision is defended by what is true. | `SCRIPTED_HOST_LABELS = runner_shared.HostLabels(...)` at `tests/test_hostdedup_third_host.py`; measured `vars(runner_shared)` HostLabels instances = `[('OC_HOST_LABELS','oc_runipd'), ('AGY_HOST_LABELS','agy_runipd')]`, with `'scripted' not in` the discovered ids; AST scan shows the four test functions mentioning the descriptor. |
| F-09 | THE BASELINE IS GREEN, so any failure during execution is attributable to this change. THE NUMBER IS ALREADY STALE and must not be used as a bar (review PR-003): authored `3246 passed, 2 skipped`, re-measured one day later at review `3371 passed, 2 skipped, 3 warnings in 96.75s`, a rise of 125 from unrelated work. E-05 now requires the executor to measure its own pre-edit baseline. | `python3 -m pytest` at the authoring base: `3246 passed, 2 skipped, 3 warnings in 53.17s`; at the review base: `3371 passed, 2 skipped, 3 warnings in 96.75s`. |
| F-10 | Added at review. THE WHOLE FIX WAS DRIVEN END TO END AND IT WORKS, so the plan's feasibility is measured rather than argued. A trial patch applying E-02 (keyword-only `host_label` appended after `wrote_in`, literal interpolated) and E-03 (both wrappers binding `runner_shared.<OC\|AGY>_HOST_LABELS.command`) produced: the literal gone from `agent_workflows/` entirely; `inspect.signature` reporting `KEYWORD_ONLY NO DEFAULT`; `TypeError: process_backlog_close() missing 1 required keyword-only argument: 'host_label'` when the binding is omitted; the `oc` host's close message reading `closed by aw oc run:` and the `agy` host's `closed by aw agy run:` through the REAL function; and a bare suite of `3371 passed, 2 skipped` with no pre-existing test modified. The patch was reverted; nothing from it is committed. | Review's own driven measurement, recorded in the review record. |
| F-11 | Added at review. THE DEFECT HAS NEVER BEEN OBSERVED AT THE MESSAGE LEVEL BEFORE, which is why F-06's "nothing pins the message" matters more than it reads. Review drove both hosts' real `process_backlog_close` at base and captured the literal strings: BOTH hosts' `close_backlog_item` and `commit_backlog_close` received `closed by aw oc run: IPD pln999 executed (...)`. So the bug is confirmed by observation of the actual arguments reaching both durable sinks, not inferred from a `grep` for the literal. | Review probe: identical `close_message` and `commit_message` for `oc` and `agy`, both beginning `closed by aw oc run:`. |
| F-12 | Added at review. THE EARNED GATE IS THE FIXTURE TRAP E-04 MUST AVOID. `evaluate_backlog_close` requires the deciding carrier to be one THIS run produced, so a fixture holding an open item plus an executed carrier returns `close=False` with `"this run executed none of its carriers, so the close was not earned"` and builds NO message at all. Review hit this on the first probe attempt and the test would have asserted on `None`. The working shape is `item["last_plan_path"]` set to the carrier's absolute path (and NOT pre-setting `earned_paths`, which `process_backlog_close` overwrites from `collect_earned_paths`). | Measured: first probe returned that exact refusal reason with `close_message: None`; adding `last_plan_path` produced `closed: true` and a real message. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/runner_shared.py`: add keyword-only `host_label: str` with NO DEFAULT to `process_backlog_close`, placed AFTER `wrote_in`, interpolate it into the close message in place of the `aw oc run` literal, and record the no-default rationale (F-04, F-08) in the docstring. (E-02)
2. `agent_workflows/oc_runipd.py`: pass `host_label=runner_shared.OC_HOST_LABELS.command` from the existing one-line wrapper. (E-03)
3. `agent_workflows/agy_runipd.py`: pass `host_label=runner_shared.AGY_HOST_LABELS.command` from the existing one-line wrapper. (E-03)
4. `tests/test_backlog_close_host_label.py`: new behavior tests per host asserting the message each closer actually received (with the earned-gate fixture shape from F-12), plus the no-default contract test and an unchanged-remainder test for `oc`. (E-04)
5. Full bare suite run against a baseline the executor MEASURES at its own base, not against F-09's stale number. (E-05)

All five were driven end to end at review and worked (F-10), so this ordering is verified feasible rather than proposed.

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

- Over-scope: none. The three production paths are the one shared definition plus the two host bindings, which F-07 shows is the minimum set that covers every call path; the fourth path is the new test. Review re-verified the minimality claim: `runner_shared.process_backlog_close` is called from outside the module at exactly one line each in `oc_runipd.py` and `agy_runipd.py`, and `execute_item_core` re-binds the name from the driver module with `getattr(driver_module, "process_backlog_close", process_backlog_close)`, so both wrappers are on every path.
- Under-scope: the fix does NOT retroactively correct records already written with the wrong label. Those are permanent history, committed and, per F-04, also written into tracked item files; rewriting them would mean editing an executed record, which the execution contract forbids. Any such record stays as it is and the fix is forward-only. No live artifact is left in a broken state by that choice.
- Under-scope, stated rather than left implicit (review PR-004): this plan does NOT restore the enforcement for the single-delegating-statement convention that both drivers' comments still claim is asserted by a deleted test (`SharedNotCopied`, zero hits in `tests/`). E-03 honors the convention by discipline, and `p7k57l` carries the restoration. It also does not correct those four stale comment citations, which name a file that no longer exists; that is the same restoration work and touching it here would edit two of the highest-contention files for a prose fix.

## Required tests / validation

- The new per-host behavior tests in `tests/test_backlog_close_host_label.py`, which must be demonstrated FAILING on the pre-fix code at the `agy` assertion before the fix is applied (V-04).
- The full suite BARE (`python3 -m pytest`) against a baseline the executor MEASURES at its own base before editing (V-05). Do not use F-09's `3246`, which review re-measured as `3371` one day later.
- A live signature check that `host_label` is keyword-only with no default (V-02).

## Spec / documentation sync

N/A. No `.spec.md` governs the close message's host label, and no user-facing doc quotes it: the string is generated into a commit message and a workflow-history line, never documented as a contract. This plan declares no spec paths in `- Scope-Paths:` for that reason. The rationale lives in the code, in the amended `process_backlog_close` docstring (E-02).

## Open questions

### OQ-01: Should the two deleted test files be restored, and by whom?

- Blocking: no
- Status: resolved
- Owner: plan-review
- Carrier: p7k57l
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-30, AS ALREADY-ANSWERED RATHER THAN AS A NEW DECISION: YES they should be restored, NO not by this plan, and the "by whom" is already recorded on disk. Review verified the carrier exists and is accurate: `.aw/records/backlog/open/...p7k57l...` is `- Status: open`, `- Work-Kind: chore`, and its summary names both deleted files and both lost properties (the host-neutrality criterion and the single-delegating-statement shared-not-copied shape), citing `19313eed` as the deleting commit and this very defect as the cost already paid. So the question had no open residue: the deferral target is filed, this plan's `- Carrier: p7k57l` points at it, and `aw check` reports no dangling carrier. Left `- Blocking: no` because this plan's validation does not depend on it (E-04 supplies the one guard this fix needs). Review ADDED one measurement the question did not know: four comments in `oc_runipd.py` (two), `agy_runipd.py` and `runner_shared.py` still cite `tests/test_runner_backlog_close.py::SharedNotCopied` as the asserting test, and that grep returns zero hits, so the restoration carrier also owes those citations a correction; recorded in the Scope check as under-scope rather than folded in.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the actual output of `grep -rn "closed by aw" agent_workflows/ --include=*.py` showing EXACTLY ONE hit and that it is in `runner_shared.py`, plus the actual stdout of the E-01 `python3 -c` block showing no `host_label` in any of the three signatures and `.command` reading `aw oc run` / `aw agy run`.
  - Observed evidence: PASS. Exact single hit in `runner_shared.process_backlog_close` (`runner_shared.py:35674`) for literal `closed by aw oc run:`; live signature check shows no host_label in shared or host signatures; OC and AGY .command descriptors read 'aw oc run' and 'aw agy run'.
  - Result: pass
    ```
    $ grep -rn "closed by aw" agent_workflows/ --include=*.py
    agent_workflows/runner_shared.py:35674:        f"closed by aw oc run: IPD {item['id6']} executed "

    $ python3 -c "
    import inspect
    from agent_workflows import runner_shared as rs, oc_runipd, agy_runipd
    print('shared:', list(inspect.signature(rs.process_backlog_close).parameters))
    print('oc   :', list(inspect.signature(oc_runipd.process_backlog_close).parameters))
    print('agy  :', list(inspect.signature(agy_runipd.process_backlog_close).parameters))
    print('OC .command :', rs.OC_HOST_LABELS.command)
    print('AGY .command:', rs.AGY_HOST_LABELS.command)"
    shared: ['run_dir', 'state', 'item', 'lane_repo', 'lane_handle', 'run_checked', 'close_backlog_item', 'commit_backlog_close', 'wrote_in']
    oc   : ['run_dir', 'state', 'item', 'lane_repo', 'lane_handle']
    agy  : ['run_dir', 'state', 'item', 'lane_repo', 'lane_handle']
    OC .command : aw oc run
    AGY .command: aw agy run
    ```

- [x] V-02 validates E-02
  - Required evidence: paste the actual output of `python3 -c "import inspect; from agent_workflows import runner_shared as rs; p=inspect.signature(rs.process_backlog_close).parameters['host_label']; print(p.kind, 'NO DEFAULT' if p.default is inspect._empty else repr(p.default))"` showing `KEYWORD_ONLY NO DEFAULT`. Then paste `grep -rn "closed by aw" agent_workflows/ --include=*.py` showing the `aw oc run` literal is GONE from the shared body (the remaining hit, if any, must be the interpolated form). Also paste the actual `TypeError` from calling the shared function with the label omitted, proving it fails loudly rather than defaulting.
  - Observed evidence: PASS. Signature check confirms host_label is KEYWORD_ONLY NO DEFAULT; grep confirms literal is gone from agent_workflows/; calling with omitted label raises TypeError.
  - Result: pass
    ```
    $ python3 -c "import inspect; from agent_workflows import runner_shared as rs; p=inspect.signature(rs.process_backlog_close).parameters['host_label']; print(p.kind, 'NO DEFAULT' if p.default is inspect._empty else repr(p.default))"
    KEYWORD_ONLY NO DEFAULT

    $ grep -rn "closed by aw" agent_workflows/ --include=*.py
    (exit 1, no hits found)

    $ python3 -c "
    from pathlib import Path
    from agent_workflows import runner_shared as rs
    rs.process_backlog_close(
        Path('.'),
        {},
        {},
        run_checked=lambda *a, **k: '',
        close_backlog_item=lambda *a, **k: (0, ''),
        commit_backlog_close=lambda *a, **k: None,
    )"
    TypeError: process_backlog_close() missing 1 required keyword-only argument: 'host_label'
    ```

- [x] V-03 validates E-03
  - Required evidence: paste the actual stdout of a check that BOTH hosts pass a label and that neither wrapper introduces a new literal: `grep -n "host_label" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` showing each passes `runner_shared.<OC|AGY>_HOST_LABELS.command` (not a quoted string), and `grep -c "aw agy run\|aw oc run" ` over the two wrapper bodies showing no new string literal was added.
  - Observed evidence: PASS. Both wrappers delegate passing runner_shared.<OC|AGY>_HOST_LABELS.command; neither wrapper introduces a string literal.
  - Result: pass
    ```
    $ grep -n "host_label" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:620:# two neighbours, which need this host's `run_checked`/`host_label`). The `as <same-name>` FORM is
    agent_workflows/oc_runipd.py:1295:        host_label=runner_shared.OC_HOST_LABELS.command,
    agent_workflows/oc_runipd.py:1423:#   * `host_label` is the ONE value the two runners' `integrate_lane_branch` bodies actually differed
    agent_workflows/oc_runipd.py:1471:    OWN `host_label`, so the merge subject on main still reads `integrate(aw oc run): ...`.
    agent_workflows/oc_runipd.py:1474:    as it binds `host_label`. THE SIGNATURE IS DELIBERATELY UNCHANGED, and that is the point:
    agent_workflows/oc_runipd.py:1486:        host_label="aw oc run",
    agent_workflows/oc_runipd.py:1499:    ordering, the `host_label` merge subject) are the SAME code an execute integration runs; only the
    agent_workflows/oc_runipd.py:1513:        host_label="aw oc run",
    agent_workflows/oc_runipd.py:3350:        host_labels=runner_shared.OC_HOST_LABELS,
    agent_workflows/oc_runipd.py:3911:                host_labels=runner_shared.OC_HOST_LABELS,
    agent_workflows/agy_runipd.py:324:# need this host's `run_checked`/`host_label` and so keep wrappers). The `as <same-name>` form marks
    agent_workflows/agy_runipd.py:1526:# THE `host_label` BINDING BELOW IS THIS FILE'S WHOLE STAKE IN THE MOVE: the shared function gives it
    agent_workflows/agy_runipd.py:1609:        host_label=runner_shared.AGY_HOST_LABELS.command,
    agent_workflows/agy_runipd.py:1653:    `host_label`.
    agent_workflows/agy_runipd.py:1656:    exactly as it binds `host_label`, so this wrapper's SIGNATURE is unchanged and the shipped contract
    agent_workflows/agy_runipd.py:1665:        host_label="aw agy run",
    agent_workflows/agy_runipd.py:1676:    The agy twin of `oc_runipd.integrate_review_lane_branch`, binding THIS host's `host_label` so a
    agent_workflows/agy_runipd.py:1687:        host_label="aw agy run",
    agent_workflows/agy_runipd.py:2863:        host_labels=runner_shared.AGY_HOST_LABELS,
    agent_workflows/agy_runipd.py:3372:                host_labels=runner_shared.AGY_HOST_LABELS,

    $ sed -n '1277,1296p' agent_workflows/oc_runipd.py | grep -c -E "aw agy run|aw oc run"
    0

    $ sed -n '1591,1610p' agent_workflows/agy_runipd.py | grep -c -E "aw agy run|aw oc run"
    0
    ```

- [x] V-04 validates E-04
  - Required evidence: FIRST demonstrate the test catching the live bug: with the E-02/E-03 changes stashed or reverted, run `python3 -m pytest tests/test_backlog_close_host_label.py -o addopts=""` and paste the actual FAILING output showing the `agy` assertion failing with `aw oc run` observed where `aw agy run` was expected. THEN restore the fix and paste the actual PASSING output of the same command with per-test counts. A test that passes both before and after has not proven anything and must be rewritten. ALSO PASTE THE EARNED-GATE GUARD passing in both runs: the assertion that `item["backlog_close"]["closed"] is True` must hold in the PRE-FIX run too, because that is what distinguishes "the label is wrong" from "the fixture never reached the message" (F-12). A pre-fix failure whose cause is `close=False` and a `None` message does NOT satisfy this item; the pre-fix failure must be a label mismatch on a message that was actually built.
  - Observed evidence: PASS. Pre-fix run demonstrated the live bug failing on agy with 'closed by aw oc run:' while earned-gate guard passed; post-fix run passes all 4 tests.
  - Result: pass
    ```
    Pre-fix failure showing agy assertion failing with 'closed by aw oc run:' observed where 'closed by aw agy run:' was expected, and earned gate guard (item["backlog_close"]["closed"] is True) passing:
    $ python3 -m pytest tests/test_backlog_close_host_label.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1946914362
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_backlog_close_host_label.py FF.F                              [100%]

    =================================== FAILURES ===================================
    _________ test_shared_process_backlog_close_host_label_has_no_default __________
        def test_shared_process_backlog_close_host_label_has_no_default() -> None:
            sig = inspect.signature(runner_shared.process_backlog_close)
    >       assert "host_label" in sig.parameters, "host_label parameter must exist in runner_shared.process_backlog_close"
    E       AssertionError: host_label parameter must exist in runner_shared.process_backlog_close
    ________________________ test_agy_host_binds_agy_label _________________________
        ...
        # PR-001 / F-12: The earned-gate guard must pass.
        assert item.get("backlog_close", {}).get("closed") is True
        ...
        msg = close_messages[0]
    >   assert msg.startswith("closed by aw agy run:"), f"Expected msg to start with 'closed by aw agy run:', got: {msg}"
    E   AssertionError: Expected msg to start with 'closed by aw agy run:', got: closed by aw oc run: IPD pln999 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-test-01-pln999-plan.ipd.md); evidence .aw/records/plans/executed/20260929-test-01-pln999-plan.ipd.md
    _________________ test_host_messages_differ_between_oc_and_agy _________________
        ...
        assert oc_msgs[0].startswith("closed by aw oc run:")
    >   assert agy_msgs[0].startswith("closed by aw agy run:")
    E   AssertionError: assert False
    E    +  where False = 'closed by aw oc run: ...'.startswith('closed by aw agy run:')
    =========================== short test summary info ============================
    FAILED tests/test_backlog_close_host_label.py::test_shared_process_backlog_close_host_label_has_no_default
    FAILED tests/test_backlog_close_host_label.py::test_agy_host_binds_agy_label
    FAILED tests/test_backlog_close_host_label.py::test_host_messages_differ_between_oc_and_agy
    ========================= 3 failed, 1 passed in 0.39s ==========================

    Post-fix pass output:
    $ python3 -m pytest tests/test_backlog_close_host_label.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=2398914433
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items                                                             collected 4 items

    tests/test_backlog_close_host_label.py ....                              [100%]

    ============================== 4 passed in 1.64s ===============================
    ```

- [x] V-05 validates E-05
  - Required evidence: paste TWO bare `python3 -m pytest` summary lines with no added flags: the executor's OWN PRE-EDIT baseline, taken before the first change, and the post-change run, showing no failures and a passed count equal to that baseline plus the tests E-04 added. Do NOT compare against F-09's `3246`, which review re-measured as `3371` a day later; a plan-quoted absolute count is not a valid bar. Explicitly confirm `tests/test_backlog_production.py` and `tests/test_hostdedup_third_host.py` are among the passing tests and that no pre-existing test file was modified (`git diff --stat` over `tests/` should show only the new file).
  - Observed evidence: PASS. Baseline 3911 passed, post-change 3915 passed (+4 new tests from E-04); targeted tests passed (30 in 20.12s); git diff confirms only the new test was added.
  - Result: pass
    ```
    Pre-edit baseline:
    3911 passed, 2 skipped, 3 warnings in 143.32s (0:02:23)

    Post-change run:
    3915 passed, 2 skipped, 3 warnings in 121.45s (0:02:01)

    Targeted tests:
    $ python3 -m pytest tests/test_backlog_production.py tests/test_hostdedup_third_host.py
    30 passed in 20.12s

    Tests git diff:
    $ git diff --stat tests/
    (empty, no pre-existing tests modified)
    $ git status --short tests/
    ?? tests/test_backlog_close_host_label.py
    ```

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

`/plan-review` has run (see `## Workflow history` and the typed review record), so the `- Readiness:` field it wrote is the review's attestation; explicit human approval is still required before execution. The plan's one open question, OQ-01, is `- Blocking: no` and now `- Status: resolved`, so nothing is outstanding for a human to answer.

WHAT A HUMAN IS APPROVING: one new keyword-only parameter on one shared function, one changed f-string, two one-line bindings in the existing host wrappers, and one new test file. No close-eligibility logic, no gate predicate, no `HostLabels` change, and no existing test modified.

THE WHOLE FIX WAS DRIVEN END TO END AT REVIEW AND IT WORKS (F-10), so this is not a proposal whose feasibility is being taken on trust. A trial patch produced the literal gone from the package, `KEYWORD_ONLY NO DEFAULT` on the signature, a loud `TypeError` when a host omits the binding, `closed by aw oc run:` from the `oc` host and `closed by aw agy run:` from the `agy` host through the REAL function, and a green bare suite with no pre-existing test touched. The patch was reverted and nothing from it is committed.

THREE AUTHORING CORRECTIONS TO THE BACKLOG ITEM THE APPROVER SHOULD KNOW, all measured rather than assumed. FIRST, the item's code coordinate is STALE: the literal is no longer in `oc_runipd.py` but in the re-homed `runner_shared.process_backlog_close` (F-01), so an executor following the item literally would edit the wrong file and change nothing. SECOND, the item's own open conditional is RESOLVED: runnerlayer 02 `1f7xno` did re-home the function, but it moved the body verbatim and left the literal, so this item carries the fix exactly as its last sentence anticipated (F-02). THIRD, the defect is WORSE than the item states: the false label reaches the item's tracked `## Workflow history` as well as the commit message (F-04, proven by running the real setter), so it is committed to the record twice. Review CONFIRMED the defect at the message level for the first time (F-11): both hosts' closers demonstrably receive `closed by aw oc run:`.

FOUR REVIEW CORRECTIONS TO THE PLAN ITSELF. FIRST, F-08 overstated its own evidence: the third-host descriptor is NOT consumed by the routability test the plan cites (that test discovers labels from `vars(runner_shared)`, which yields only the two real hosts, and names `SCRIPTED_HOST_LABELS` in its docstring alone), so the no-default case rests on the documented convention plus the third-host fixture shape, not on a test that would fail. SECOND, the suite baseline in F-09 was already stale by 125 tests one day later, so E-05 and V-05 now require the executor to measure its own. THIRD, E-04's fixture as described would NOT have reached the message at all: the earned gate refuses a close whose carrier the run did not produce, so the test would have asserted on `None`; the working recipe is now in the item (F-12). FOURTH, both drivers' comments still cite a deleted test (`SharedNotCopied`) as the guard on the wrapper shape, which is recorded as under-scope and carried by `p7k57l`.

WHY NO DEFAULT, since that is the one design decision here: it is the established convention rather than a preference, and `HostLabels`'s own docstring gives the reason this defect proves ("misattribution is invisible until someone audits the record"). The tested in-repo precedent is `integrate_lane_branch`, whose `host_label` is KEYWORD_ONLY with no default and whose per-host binding IS pinned by a surviving both-hosts test. A third host descriptor also already exists as a fixture, so a default would be a latent repeat of this bug (F-08, as corrected).

WHAT THIS DELIBERATELY DOES NOT DO, so the approver is not surprised. Records already written with the wrong label are NOT corrected; they are permanent history and rewriting them would mean editing executed records. The two deleted test files that let this survive a re-home are NOT restored (F-05, OQ-01); that is suite-trim restoration work, not a one-parameter fix.

GENUINE STOP CONDITIONS: E-01 finds the literal absent or already parameterized (the premise would be wrong), or the V-04 pre-fix run does NOT fail (the test would be proving nothing and must be rewritten). Neither is a scope question; both are conditions under which proceeding would record something false. NOT A STOP CONDITION, added at review: a V-04 pre-fix run that fails because the fixture never earned the close (`closed: false`, message `None`) is a FIXTURE defect, not the demonstration V-04 asks for. Fix the fixture per F-12 and re-run; do not record it as the bug being caught.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check passed that was not run. V-04 specifically requires demonstrating the new test FAILING before the fix. Author tests against observable behavior only: assert on the arguments the closers receive and on the live signature, never by reading production source with `inspect.getsource`, `ast`, or regex. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. VERIFY YOUR INTERPRETER IS READING THIS TREE before trusting any negative result from an ad-hoc probe: review briefly mis-concluded the fix had failed because a probe script in a subdirectory imported `agent_workflows` from a different checkout (Python puts the script's directory on `sys.path`, not the repo root). Check `agent_workflows.__file__` when a result surprises you.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the four paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

Commit ONLY the paths in `- Scope-Paths:` through `aw commit nf71bz -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize nf71bz --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `2kspdy`; AFTER EXECUTION, and not before, set that item `done` with `--evidence` citing this executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `2kspdy` fails closed because the gate is handed to a carrier that has not shipped, so the item stays `graduated` until `aw ipd finalize` has moved this plan to `executed/`.
