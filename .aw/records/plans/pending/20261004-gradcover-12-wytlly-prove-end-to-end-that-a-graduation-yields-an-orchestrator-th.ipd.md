# IPD: Prove end to end that a graduation yields an orchestrator the runner accepts

- Date: 2026-10-04
- Kind: child
- Concern: Each child of Set `gradcover` proves its own surface, but the defect the Set exists to fix only shows across surfaces: a graduation run produced orchestrators that a later review run refused (2026-10-03). Nothing short of driving the real runner through graduate, then review, then orchestrate, over the same records, shows the surfaces agree. This is the Set's final cross-child measurement; the orchestrator `1f4faf` assigns it here rather than carrying it.
- Scope: IN: one integration test module that, inside a temp repository seeded with `--records-backend repository`, drives the real `aw oc run` entry point (in process, with the host turn and the probe replaced by scripted doubles through the existing injection seams) over a fixture backlog item through three runs: (A) graduate, where the scripted agent writes an orchestrator plus children, first with an uncovered whole-Set obligation and then, on the correction turn, with that obligation assigned to a child by id6; (B) `--action review` over the produced Set; (C) an orchestrate pass with the children marked `executed` by fixture; plus the refusal variant of (A) with the correction never made. Then the bare suite. OUT: any production code change; any real model call; changing any other test.
- Scope-Paths: tests/test_gradcover_end_to_end.py
- Item-Dependencies: executed:sbiv1j, executed:dalmk4, executed:5etev3, executed:nnsa2o, executed:24qw39, executed:26m1nb, executed:r2wa38, executed:qs00nc, executed:8mabmu
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 12
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: wytlly

## Workflow history
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 (all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-010. Fixed: Run C approves the orchestrator first, since a `reviewed` plan is not dispatched (PR-001); E-01 split into Runs A/B/C as E-01/E-06/E-07 (PR-002); probe injected by patching `ask_orchestrator_probe`, with the double's answer format and the scripted-judgement limit stated (PR-003); lane isolation kept on so preservation and integration are real (PR-004); probe counts reconciled (E-02 is 1 call, Run B counts the whole run) (PR-005); parity redefined as one inner code on three surfaces and one quote on five (PR-006); `IPD-REVIEW-ORCHESTRATOR-READY` observed as absence (PR-007); every exercised child declared in `- Item-Dependencies:` (PR-008); `--records-backend` convention corrected, OQ-01 threshold made concrete, both hosts covered (PR-009); V-items demand per-host concrete evidence, gate contract completed (PR-010).
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): wording updated for the maintainer ruling 2026-10-04 (coverage answer stored in the plan).

- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of orchestrator `1f4faf` (findings PR-002, PR-003): added `executed:5etev3` to `- Item-Dependencies:` because Runs B and C assert Order 04's behavior (no run-start probe on a review run; the retirement-time re-check) and Order 04 was not reachable through `sbiv1j` or `dalmk4`; added E-05/V-05, the cross-surface ONE PREDICATE parity check that the orchestrator's `## Cross-IPD validation` previously carried with no owner. This plan owns the orchestrator's Completion criteria 1, 2 and 13 (the authoring line below says 11, which is `jm27py`'s since Order 13 was added).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 12 of Set `gradcover`, the final child, owning the whole-Set measurement named in the orchestrator's Completion criteria 1, 2 and 11.

## Goal

Show, by driving the real runner over real records, that a graduation now either hands off a Set the next review and orchestrate runs accept with no further probe call, or fails visibly with the backlog item still `open` and the uncovered passage quoted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the success path

- [ ] E-01 Write the success scenario's graduation (Run A) in `tests/test_gradcover_end_to_end.py`, on BOTH hosts (`oc_runipd` and `agy_runipd`, one `subTest` each, the `_HOSTS` loop of `tests/test_backlog_production.py`). HARNESS (shared by every scenario in the file): seed a `git init` temp repository (the `_make_test_repo` pattern, with a `planned` fixture release record) holding one `open` backlog item (`Work-Kind: bug`, `Blocks-Release:` the fixture release), committed; drive each run through `mod.build_parser().parse_args([...])`, `mod.initialize_run(args)` and `mod.run_queue(run_dir, retry_incomplete=False)` WITH lane isolation left at its default (no `--no-isolate-worktree`, as `tests/test_spec_production.py` `test_quarantine_lane_preserved_on_failure` does), so integration and lane preservation are real; replace the host turn with `_patch_host_agent`'s pattern (`oc_runipd.run_opencode` / `agy_runipd.run_agy_turn`), writing into `kwargs["work_dir"]`; replace the probe by patching `runner_shared.ask_orchestrator_probe` with a counting double (`execute_item_core` passes no `asker`, which is why Order 06 `r2wa38` E-04 uses this seam), since the real spawn raises under pytest. THE PROBE DOUBLE answers in Order 02's format, decided from the excerpt it is handed: if the excerpt contains the unowned line it returns `ORCHESTRATOR: CONTAINS EXECUTIONS` then `QUOTE: <that line>` (the quote must occur in the excerpt, or Order 02's classifier discards it and the answer becomes `unknown`), otherwise `ORCHESTRATOR: CONTAINS NO EXECUTIONS`. That double makes the model's judgement scripted, so this test proves the PLUMBING across surfaces, not the model's named-owner credit (which Order 02's prompt carries); say so in the test's docstring. FIXTURE SET: the scripted first turn writes a conforming orchestrator (`- Kind: orchestrator`, Order 0, `- From-Backlog:` the item, a `## Child IPDs` table naming both children by id6, a checklist of typed child-tracking rows only, so `IPD-S407` passes) and two conforming children at `to-review` that each lint `conforming` at `author`, plus, in the orchestrator's `## Completion criteria` (a `PROBE_PROSE_SECTIONS` section, so it reaches the excerpt and the fingerprint), the line "the full suite passes after both children" naming no owner. Generate the fixture text with `aw ipd scaffold` output or a template asserted to lint `conforming` in the test's own setup, never a hand-guessed shape. The scripted correction turn rewrites that line to "the full suite passes after both children. Owner: `<child-2-id6>`" and commits nothing itself (the runner's production commit helper does). RUN A (`start <item> --action plan`): assert one correction turn spent (the `production-set-correction` event / `attempts[]` entry of Order 07); the first attempt's findings carried `BACKLOG-GRADUATE-SET` with the line quoted; the item ends `executed` in run state and the backlog item reads `- Status: graduated` on the integrated main tree; the orchestrator on main carries `- Coverage: pass`, `coverage_record.is_current(text)` is True, and its `## Workflow history` carries the `coverage pass` line; `git status --porcelain` on main is empty.
  - Depends on: none
  - Expected outcome: on both hosts, Run A completes as asserted with exactly 2 probe calls (the first attempt, and the edited text after correction).
  - Execution state: pending

- [ ] E-06 Write the success scenario's review run (Run B), on both hosts, continuing from E-01's Run A on the same fixture repository: `start <setid> --action review` over the produced Set. The scripted reviewer sets each plan `reviewed` by calling the REAL setter in process (`cli.main(["ipd", "set", "reviewed", <id6>, "--dir", <work_dir>, "--yes", "--message", ...])`), children first, editing no prose in the orchestrator's checked sections; assert ZERO probe calls over the WHOLE run (Order 04's run-start scoping and Order 07's post-review re-check both read the current record), every item's disposition is `reviewed`, the orchestrator reads `- Status: reviewed`, and no refusal with code `IPD-REVIEW-ORCHESTRATOR-READY` was recorded (that code exists only as a refusal, so its ABSENCE is the observable pass).
  - Depends on: E-01
  - Expected outcome: on both hosts, Run B makes 0 probe calls and leaves every plan of the Set `reviewed` with no `IPD-REVIEW-ORCHESTRATOR-READY` refusal.
  - Execution state: pending

- [ ] E-07 Write the success scenario's orchestrate run (Run C), on both hosts, continuing from E-06's Run B: move both children to `executed/` with `- Status: executed` by fixture (leaving the orchestrator's child table text unchanged), then approve the orchestrator with `aw ipd set approved <id6> --by-human --message ...` (a `reviewed` orchestrator is frozen `reviewed` and not dispatched without approval, `runner_shared.initial_queue_status`), and run `start <setid>`; assert the item's action is `orchestrate`, ZERO probe calls (run start and the `dispatch_orchestrator_item` re-check both read the current record), an `orchestrator-finalized` event, and the orchestrator under `executed/` reading `- Status: executed`.
  - Depends on: E-06
  - Expected outcome: on both hosts, Run C makes 0 probe calls and retires the orchestrator to `executed`.
  - Execution state: pending

### Task group 2: the refusal paths

- [ ] E-02 Write the refusal scenario on both hosts, using E-01's harness: Run A with `--retry-budget 1` and a correction turn that edits nothing in the orchestrator's checked sections, so the line is never fixed. Assert: exactly one correction turn (Order 07 `nnsa2o`: exactly `--retry-budget` turns); exactly ONE probe call (the correction left the fingerprint unchanged, so the recorded `fail` is reused, not re-asked); the item ends `fail-gate` and its recorded refusal code is `BACKLOG-GRADUATE-SET` with the line quoted in the reason; on the MAIN tree the backlog item still reads `- Status: open` and no plan with `- From-Backlog:` the item exists; the lane is preserved (`item["preserved_worktree"]` is a directory, the `lane_containment.LANE_PRESERVED_EVENT` (`worktree-preserved`) event is present) and its orchestrator carries a committed `- Coverage: fail` record whose `## Coverage findings` quotes the line; and the `aw runs` detail view of that run, rendered in process through `run_viewer` (the `--detail` path that prints `! refused [<code>]: <reason>`), contains the quoted line. Then, with `cli.main` in process and `--dir <preserved_worktree>`, run `aw backlog set graduated <item>` and `aw ipd set reviewed <orchestrator-id6> --yes --message ...` and assert each exits nonzero, writes nothing (file bytes unchanged), and names the quoted line or the orchestrator's coverage finding.
  - Depends on: E-01
  - Expected outcome: every refusal fires with the quoted line, the main tree is untouched, and no record claims the Set is ready.
  - Execution state: pending

- [ ] E-03 Write the resume scenario on both hosts: after E-02's refused run, bring the preserved lane's plans onto the fixture's main tree by merging the lane's `preserved_branch` into `main` with plain `git merge` in the fixture (simulating an earlier integrated handoff, the 2026-10-03 shape; the item stays `open`), then run Run A again as a new run whose FIRST turn (no correction needed) edits the existing orchestrator in place to name the owner. Assert: that turn's prompt contains Order 08's "Continue this handoff" section listing the existing orchestrator and its quoted finding; no `BACKLOG-GRADUATE-COUNT` finding; exactly one `- Set:` among the active plans whose `- From-Backlog:` names the item and the same three plan ids as before; exactly one probe call (the edited text); the item ends `executed` and the backlog item reads `- Status: graduated` on main with a current `- Coverage: pass` record in the orchestrator.
  - Depends on: E-02
  - Expected outcome: the resumed graduation continues the existing plans and succeeds, with one Set linked to the item.
  - Execution state: pending

### Task group 3: the whole suite

- [ ] E-04 Prove the scenarios can fail, then run the bare suite. MUTATION (temporary, never committed, never an edit to production source): inside the E-02 test, add a `mock.patch.object(production_checks, "backlog_graduate_set", return_value=[])` around Run A, run the file, paste E-02 FAILING (the graduation now succeeds: Order 06 filters `IPD-S408` out of the per-plan check, so nothing else refuses), then remove the patch and paste the file passing. Then run the bare suite and reconcile it against a baseline measured on a clean tree at this child's HEAD BEFORE the test file is added. Record the test file's wall time from `python3 -m pytest -o addopts="" tests/test_gradcover_end_to_end.py --durations=0` and apply OQ-01.
  - Depends on: E-03
  - Expected outcome: the mutation makes E-02 fail and its removal makes it pass; the bare suite shows no new failing node id against the baseline.
  - Execution state: pending

- [ ] E-05 Write the ONE PREDICATE parity scenario the orchestrator `1f4faf` assigns here: one fixture Set (an orchestrator and two children at `to-review`, all linting `conforming` at `author`) whose orchestrator's coverage record is pre-written with `coverage_record.write` (never a model call, and never a hand-written record, which `IPD-M112` refuses) as a FAIL with one quoted passage in `## Coverage findings`. Drive five surfaces over it and collect each one's output: (1) `aw ipd set reviewed <id6> --yes --message ... --agent` (subprocess); (2) `aw ipd lint --phase review-finalize --agent <plan>` (subprocess); (3) `aw check plans --agent` (subprocess); (4) a backlog production run (in process, E-01's harness) whose scripted agent writes exactly that Set into the lane and records the same FAIL with `coverage_record.write` there; (5) `runner_shared.dispatch_orchestrator_item` called in process on a copy whose children are moved to `executed/` by fixture, through the `make_run` state pattern of `tests/test_orchestrator_retirement.py` `DispatchRunCase`, with Order 04's `asker` parameter given a counting double. WHAT IS COMPARED, because the five surfaces do not share one outer code: surfaces (1) to (3) expose the shared function's inner finding codes (Order 05's `result` record carries each finding's `code`; Order 03 makes `IPD-S408` and `check.orchestrator-not-review-ready` report the same inner codes), so assert the SAME inner code and the SAME quote on those three; surfaces (4) and (5) carry their own surface code (`BACKLOG-GRADUATE-SET` in the refusal; `finalize-refused` with a detail of the form `retirement re-check refused: <subject>: <quote>; <remedy>`), so assert that code plus the SAME quote and the SAME finding subject (the orchestrator id6). Assert the probe double was called ZERO times on (4) and (5) (the recorded `fail` is current, so it is read, not re-asked); the inherited `PYTEST_CURRENT_TEST` makes any real spawn by a subprocess surface raise.
  - Depends on: E-01
  - Expected outcome: five refusals, one identical quote across all five, one identical inner finding code across the three surfaces that expose it, and the expected surface code on the other two; no surface passes the fixture.
  - Execution state: pending

## Project conventions discovered (Step 0)

- IN-PROCESS RUNNER TESTS WITH INJECTED HOSTS ARE THE ESTABLISHED PATTERN (`tests/test_backlog_production.py`, `tests/test_orchestrator_retirement.py`); the real spawn is refused under pytest by `_assert_probe_spawn_is_permitted`.
- SEED FIXTURES SO RECORDS LIVE IN THE FIXTURE REPOSITORY. The existing in-process runner tests (`tests/test_backlog_production.py` `_make_test_repo`, `tests/test_spec_production.py`) write records straight into `<tmp>/.aw/records/` of a `git init` repo and never run an install, so no `$HOME` placement can occur; follow that pattern. If the harness ever does run `aw install`/`aw setup`, pass `--records-backend repository` (a non-interactive install may otherwise place records under `$HOME` and make controls vacuous, `jei45f` F-07).
- LANE ISOLATION STAYS ON in the production scenarios: the existing graduation tests all pass `--no-isolate-worktree`, which removes the preserved lane and the integration this plan must observe; `tests/test_spec_production.py` `test_quarantine_lane_preserved_on_failure` is the precedent for the isolated shape.
- THE PROBE IS INJECTED BY PATCHING `runner_shared.ask_orchestrator_probe` for every in-process run, since `initialize_run_core` and `execute_item_core` pass no `asker`; `dispatch_orchestrator_item` gains `asker` in Order 04 and is given one directly in E-05.
- RUN THE SUITE BARE; do not pass `-n0`, an extra `-q`, or `-p no:randomly` (`AGENTS.md` execution contract).
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The incident spanned two runs: graduations (earlier runs, items now `graduated`) and review runs on 2026-10-03 (refused). Only a test that chains production, review and orchestrate over the same records reproduces that shape. | the 11 `graduated` items and the four refused run directories named in the orchestrator |
| F-02 | The injection seams exist: production turns use the host launcher the tests already replace; the probe takes `asker`/`runner`; retirement goes through `dispatch_orchestrator_item`. A full in-process run, however, cannot receive an `asker` (the run-start gate is called from `initialize_run_core` without one), so the run-level seam is a module-attribute patch of `runner_shared.ask_orchestrator_probe`, which `probe_orchestrator` resolves at call time. | `tests/test_backlog_production.py` `_patch_host_agent`; `runner_shared.probe_orchestrator` (`ask = asker if asker is not None else ask_orchestrator_probe`); `runner_shared.enforce_orchestrator_probe_gate`; precedent `tests/test_orchestrator_shape_gate.py` |
| F-03 | A `reviewed` orchestrator is not dispatched without approval: `runner_shared.initial_queue_status` freezes a `reviewed` plan whose action is not `review` as `reviewed`, so Run C must approve the orchestrator first. | `runner_shared.initial_queue_status` ("A plan with status 'reviewed' waiting for human approval is frozen 'reviewed'") |
| F-04 | The five parity surfaces do not share one outer code: the setter, lint and check expose the shared function's inner finding codes, production wraps them in `BACKLOG-GRADUATE-SET`, and retirement wraps them in `finalize-refused` with the quote in the detail. Parity is therefore one inner code on three surfaces and one quote on all five. | `26m1nb` E-01 (result record carries each finding's `code`); `qs00nc` E-06 ("the same finding codes as `IPD-S408`"); `r2wa38` E-01; `5etev3` E-02 |
| F-05 | `IPD-REVIEW-ORCHESTRATOR-READY` exists only as a refusal code (`nnsa2o` E-03 records it through `record_refusal`), so "passed" is observable only as its absence plus the plan reading `reviewed`. | `nnsa2o` E-03 |

## Proposed changes (ordered, validatable)

1. Success scenario across graduate (E-01), review (E-06) and orchestrate (E-07).
2. Refusal scenario with setter refusals (E-02).
3. Resume scenario over an integrated earlier handoff (E-03).
4. Mutation proof and bare suite (E-04).
5. Cross-surface parity of the one readiness predicate (E-05).

## Deferred / out of scope (with reason)

- A LIVE RUN AGAINST A REAL MODEL. Not reproducible and spends money; the scripted doubles exercise every code path a model answer reaches.
  - Carrier-Declined: tests must not spend tokens (`_assert_probe_spawn_is_permitted`)

## Scope check

- Over-scope: none. One test file.
- Under-scope: none; the Set's other surfaces are each proven by their own child. The spec-production twin (`SPEC-PLAN-SET`) is proven by `r2wa38`; this plan drives only the backlog path, which is the 2026-10-03 incident shape.

## Required tests / validation

- Baseline bare `python3 -m pytest` on a clean tree at this child's HEAD, failing node ids recorded.
- `python3 -m pytest -o addopts="" tests/test_gradcover_end_to_end.py -q --durations=0` pasted.
- The mutation run pasted.
- Bare `python3 -m pytest` after, `N passed` line pasted, reconciled against the baseline.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec or document edited. This plan measures the contract of `25kzda` 2.5b, 2.5d, 2.5e, 4.4, 4.9 and 5.5 and `77tr3o` R-13 as amended by Order 01. If a scenario cannot be made to pass because an executed child's behavior differs from its spec, do NOT weaken the assertion: record the gap as a failed V-item and file a corrective plan against the owning child.

## Open questions

### OQ-01: Should the end-to-end test be marked `slow`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: the repository has no numeric slow threshold (`pyproject.toml` defines the `slow` marker as "heavy subprocess/integration tests" with no time bound; `conftest.py` sets only hang guards, 60 s CPU and 240 s wall per test). So: leave the file in the default run so it guards every change, UNLESS any single test in it exceeds 30 s wall in the `--durations=0` measurement, in which case mark that test (not the file) `slow`. Record the measured times and the decision in V-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the Run A test passing on both hosts (subtest ids shown). Paste, per host, the probe double's call count (2), the recorded first-attempt finding (code `BACKLOG-GRADUATE-SET` and the quoted line), the correction-turn count (1) from `attempts[]` or the `production-set-correction` event, the run-state item status (`executed`), `grep -m1 '^- Status:'` on the backlog item in the MAIN tree (`graduated`), the orchestrator's three coverage fields plus its `coverage pass` history line from the main tree, and `git status --porcelain` on main (empty). Paste the fixture-conformance assertion (each fixture plan lints `conforming` at `author`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the refusal test passing on both hosts. Per host paste: the probe call count (1); the correction-turn count (1); the item status (`fail-gate`) and its recorded refusal code (`BACKLOG-GRADUATE-SET`) and reason containing the quoted line; the main-tree backlog item's `- Status: open`; the `preserved_worktree` path existing and the `worktree-preserved` event; the lane orchestrator's `- Coverage: fail` and its `## Coverage findings` bullet; the `run_viewer` detail line `! refused [BACKLOG-GRADUATE-SET]: ...` containing the quote; and both in-lane setter refusals' exit codes and output, with the before/after file digests showing nothing was written.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the resume test passing on both hosts. Per host paste: the merge of the preserved branch into the fixture's main; the resumed turn's prompt excerpt showing the "Continue this handoff" section naming the existing orchestrator; the run's findings list containing no `BACKLOG-GRADUATE-COUNT`; the set of `- Set:` values among active plans linking the item (exactly one) and their plan ids (the same three as before); the probe call count (1); and the backlog item's final `- Status: graduated` with the orchestrator's `- Coverage: pass`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the baseline bare `python3 -m pytest` summary measured BEFORE the file was added, with its failing node ids; the mutation run (the `backlog_graduate_set` patch in place) showing E-02's test FAILING and the reason, and the run after removing it passing; the file's `--durations=0` wall time and the OQ-01 decision taken; `rg -n "inspect\\.|import ast|getsource|read_text\\(.*agent_workflows" tests/test_gradcover_end_to_end.py` returning nothing. Then paste the BARE `python3 -m pytest` summary after, reconciled node id by node id against the baseline, `aw ipd lint` on this plan conforming, `aw sanitize --agent` clean, and `git diff --cached --name-only` listing only `tests/test_gradcover_end_to_end.py` (plus this plan file under a runner's finalize).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the parity test passing, then one line per surface: surface name, exit code, the code it reported (inner finding code for `aw ipd set`, `aw ipd lint`, `aw check plans`; `BACKLOG-GRADUATE-SET` for production; `finalize-refused` for retirement) and the quoted passage, showing the three inner codes identical and the quote identical on all five. Paste the probe double's call count on surfaces (4) and (5) (0). Paste one mutation run, made inside the test with `mock.patch` and never by editing production source, in which surface (4) or (5) skips the shared check (for example `production_checks.backlog_graduate_set` patched to return `[]`, or `orchestrator_readiness.review_readiness` patched inside `dispatch_orchestrator_item`'s call to return ready), showing the parity test FAILING, then the run after removing it passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the Run B test passing on both hosts. Per host paste: the probe double's call count over the whole run (0); each item's final disposition (`reviewed`); `grep -m1 '^- Status:'` on all three plans (`reviewed`); the run's recorded refusals list showing no `IPD-REVIEW-ORCHESTRATOR-READY`; and each in-process `aw ipd set reviewed` call's exit code (0, children before the orchestrator).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the Run C test passing on both hosts. Per host paste: the orchestrator's queued action (`orchestrate`); the probe double's call count over the whole run (0); the `orchestrator-finalized` event; and the orchestrator's path under `.aw/records/plans/executed/` with `grep -m1 '^- Status:'` reading `executed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Open questions: OQ-01 resolved. Scope fence: `tests/test_gradcover_end_to_end.py` is the declared surface; an edit outside it may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`); no production source may be changed to make a scenario pass (see Spec / documentation sync). Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. Commit only the paths you changed through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`. Depends on every implementing child of Set `gradcover` except `hm1h3l` (spec only, reached through the others) and `52opph`/`jm27py` (whose behavior is not exercised here): each is declared in `- Item-Dependencies:`.
