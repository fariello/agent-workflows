# IPD: Triage and restore the residual behavioral coverage of the deleted tests/test_runner_backlog_close.py

- Date: 2026-10-12
- Kind: child
- Concern: Commit `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests") deleted `tests/test_runner_backlog_close.py` (2703 lines, 12 classes, 58 tests). Executed plan `1o7i7g` (backlog `p7k57l`) restored only its DELEGATION and HOST-INDEPENDENCE properties, in `tests/test_runner_delegation_and_host_independence.py`, and re-pointed the rest to this item because `xvp5vx`'s census plan `oyh28b` treated the file as owned by `p7k57l` and filed nothing for it. Nobody has since checked which of the remaining behavioral properties (the backlog-close decision and its fail-closed paths, the path-scoped close commit, the unclosed-item report and `aw runs` pointer, the shutdown report on SIGINT/SIGTERM with exit 130/143, signal-handler safety, the child-kill separation, and the working-tree and committed-tree integrity self-check) are still guarded. Authoring measured that several have NO live test at all (F-03). Separately, two comments in `agent_workflows/runner_shared.py` (and a twin in `agent_workflows/oc_runipd.py`) claim LIVE guards that do not exist: "`tests/test_runner_layering.py` now freezes" and "`tests/test_runner_shared.py::ReHomedHostNeutralNameTests` proves it" (F-05).
- Scope: IN: (a) recover the deleted file from `19313eed7^` and produce a per-test triage of all 58 tests into PIN (code/AST/text/census, stays deleted), COVERED (a named live test already asserts the outcome), or UNGUARDED; (b) mutation-test every candidate UNGUARDED property against the live tree to confirm it is really unguarded; (c) restore each confirmed-unguarded property as a BEHAVIORAL test in ONE new module, `tests/test_runner_backlog_close_behavior.py`, which drives real callables, real subprocesses and real git fixtures and asserts outputs, exit codes, files and ledger records; (d) prove each restored test is sensitive by a recorded mutation; (e) correct the two stale `runner_shared.py` guard citations and the `oc_runipd.py` twin into retirement statements; (f) re-point the one-line "tracked under backlog item yf1p8y" pointer in `tests/test_runner_delegation_and_host_independence.py` to the new module. OUT: any code, AST, text, caller-count or census pin (GUIDING_PRINCIPLES P16 and the `xvp5vx`/`pn7rw3`/`s4jctz`/`aced01` rulings); restoring `tests/test_runner_layering.py`; reading `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`; any change to an executable statement in any production module; the dangling-citation check rule (`j7daih`); the other dangling citations `65d5zf` (backlog `3tov52`) and `dtelfb` (backlog `046nys`) own.
- Scope-Paths: tests/test_runner_backlog_close_behavior.py, tests/test_runner_delegation_and_host_independence.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: yf1p8y
- Set: yf1p8y
- Order: 1
- Highest E allocated: 11
- Author: opencode Claude Opus
- Id: z2ugxc

## Workflow history

- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed.
- 2026-10-12 draft (opencode Claude Opus): created.
- 2026-10-12 to-review (opencode Claude Opus): Authored from backlog item `yf1p8y` (Work-Kind `chore`, Priority `low`, no `Blocks-Release`, so none is inherited or invented). Authoring recovered `tests/test_runner_backlog_close.py` from `19313eed7^`, enumerated its 12 classes and 58 tests, and grepped the live suite for each property's collaborators (F-02, F-03). It found the shutdown report, signal funnel, handler safety, and both integrity self-check queries have no live test outside the delegation guard. It also found that `1o7i7g`'s claim that "`backlog_item_paths_for_commit` has live coverage" is not true at HEAD `6245c7074`: no file under `tests/` names it (F-04). The final per-test verdict is left to E-02, so the executor re-measures it rather than trusting authoring's spot checks.

## Goal

Every behavioral outcome the deleted `tests/test_runner_backlog_close.py` asserted is either guarded again by a live behavioral test, or recorded as a code pin that stays deleted. Also, no comment in the runner modules claims a guard that does not exist.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Recover and triage

- [ ] E-01 RECOVER and CENSUS. Record the execution HEAD sha. Run `git show 19313eed7^:tests/test_runner_backlog_close.py > /tmp/opencode/yf1p8y-deleted.py` (a scratch copy OUTSIDE the repo, never committed), then list every `class` and `def test_` in it and confirm the count is 12 classes and 58 tests (F-01). Re-run the F-03 collaborator greps at HEAD: `rg -l '<symbol>' tests/` for `backlog_item_paths_for_id`, `backlog_item_paths_for_commit`, `emit_shutdown_report`, `register_signal_report`, `signal_report_callback`, `render_unclosed_report`, `render_runs_pointer`, `record_unclosed_backlog_items`, `backlog-items-left-open`, `backlog-close-integrity-violation`, `_SIGNAL_REPORT_DONE`. If a count differs from F-01, or a symbol listed as uncovered in F-03 now has a live test, mark that fact CORRECTED and carry the corrected fact into E-02.
  - Depends on: none
  - Expected outcome: the HEAD sha, the class/test census, and the collaborator grep output, each marked CONFIRMED or CORRECTED against F-01 and F-03.
  - Execution state: pending

- [ ] E-02 TRIAGE all 58 tests into exactly one verdict each and write the result as a table into the MODULE DOCSTRING of the new `tests/test_runner_backlog_close_behavior.py` (create the file with the docstring only at this step). The columns are: deleted class::test, the PROPERTY it asserted in one line, the VERDICT, and the EVIDENCE. The verdicts are: PIN (the test read source via `inspect`/`ast`/regex/substring, or asserted a census, caller count, object identity used as a structural proxy, or text; the evidence quotes the offending construct; it stays deleted); COVERED (the evidence names a live `tests/<file>::<test>` that asserts the same OUTCOME, and the executor has read that test's assertions, not just its name); DELEGATION-COVERED (covered by `1o7i7g`'s `tests/test_runner_delegation_and_host_independence.py`); or UNGUARDED-CANDIDATE. Classify by what the test ASSERTED, not by its docstring's "REPLACES" history: many deleted tests had already been rewritten from pins into behavioral spies on 2026-09-19, and those are behavioral. Treat the F-03 table as a starting hypothesis only.
  - Depends on: E-01
  - Expected outcome: a 58-row triage table in the new module's docstring, with every row carrying one of the four verdicts and concrete evidence.
  - Execution state: pending

- [ ] E-03 MUTATION-CONFIRM every UNGUARDED-CANDIDATE and every COVERED row whose evidence is a test in a different file. Do this through a restoring wrapper that records the `sha256` of the production file before the edit and rewrites the original bytes in a `finally`. For each one, apply ONE minimal mutation to the production behavior the property names. Examples: make `runner_shared.emit_shutdown_report` skip `record_unclosed_backlog_items`; drop `_SIGNAL_REPORT_DONE.set()`; make `backlog_item_paths_for_commit` return `[]`; delete the pre-loop `register_signal_report` call in `run_queue`; have `main`'s `except KeyboardInterrupt` return 1 instead of 143. Then run `python3 -m pytest -o addopts="" -q -n auto -m "not livecorpus" tests/` (fast AND `slow`-marked tests, because a guard could live in a slow module such as `tests/test_runner_stop_triggers_e2e.py`; `livecorpus` is excluded because its result depends on the corpus, not on the mutation) and record whether any test fails. To bound cost, a mutation may first be screened against the files that name the mutated symbol (`rg -l`), but a GREEN verdict must come from the full selection above. Run the baseline selection once unmutated first, and count as RED only node ids that are not already failing in that baseline. A COVERED row whose mutation leaves the suite green is RECLASSIFIED UNGUARDED. An UNGUARDED-CANDIDATE whose mutation turns the suite red is RECLASSIFIED COVERED, naming the failing test. Update the E-02 table and the per-row evidence accordingly. After each mutation, confirm the restored file's `sha256` equals the pre-mutation hash and that `git diff --quiet -- agent_workflows/` exits 0, so no mutation leaks into a commit. Never commit while a mutation is applied.
  - Depends on: E-02
  - Expected outcome: per mutated property, the mutation applied, the suite verdict (red with failing node ids, or green), the before/after `sha256` pair, and the final UNGUARDED set.
  - Execution state: pending

### Task group 2: Restore the confirmed-unguarded behavior

Each E-item below restores ONLY the rows E-03 left UNGUARDED in its group, as behavioral tests in `tests/test_runner_backlog_close_behavior.py` parametrized over BOTH host drivers (`oc_runipd`, `agy_runipd`) where the property is host-facing. Re-derive the assertions from the recovered file where they were behavioral, but drop every `inspect`, `ast`, `read_text()` of production source, `_code_only()` and `assertIn(<literal>, src)` construct. A group whose rows are all PIN or COVERED records "nothing to restore" with the triage row ids instead of writing tests.

- [ ] E-04 RESTORE the close-decision and fail-closed group (deleted classes `ReadsTheFromBacklogLink`, `ClosingRules`, `EarnedCloseGate`, `UsesTheGatedSetter`, plus the `SharedNotCopied.test_both_drivers_call_the_close_from_their_finalize_success_branch` row). For `ReadsTheFromBacklogLink`, the behavioral rows are: each driver's `parse_plan_file(...).from_backlog` reads the link and returns `None` without it; `build_dynamic_manifest` carries it; a REAL `initialize_run` with `prepare_only` freezes it onto the `state.json` queue entry (linked plan gets the id6, unlinked gets `None`, distinct `run_id` per host, because `new_run_id` is second-granular); and the placeholder values `-`, `none`, `unresolved` and empty read as no link. For the finalize-call row, drive a real `execute_item` turn to disposition `executed` with `process_backlog_close` patched to a spy and assert it is called exactly once per driver. Use scratch git repos built in `tempfile` directories (the recovered `_Repo` helper is the model, or reuse `tests/test_backlog_handoff_close` helpers `_make_scratch_repo`, `_write_backlog_item`, `_write_plan`, `_write_spec` as `tests/test_outer_close_spec_carrier.py` already does). Assert the `evaluate_backlog_close` verdict (`close`, `reason`), the item's on-disk location, and the recorded `backlog_close` dict. Cover each UNGUARDED rule of the two-carrier, no-carrier, already-done, and induced-failure kinds: an induced lookup failure, terminal-state read failure, or setter failure leaves the item file byte-identical and records a reason.
  - Depends on: E-03
  - Expected outcome: the restored tests for this group (or a "nothing to restore" note citing triage rows), each passing at HEAD.
  - Execution state: pending

- [ ] E-05 RESTORE the end-to-end close group (deleted class `ClosesEndToEnd`). Drive `process_backlog_close` on a real scratch git repo. Assert that the item moves to `done/` with evidence, that the commit is path-scoped (`git show --name-status HEAD` lists only the item's source and destination paths), that a co-worker's uncommitted edit to a DIFFERENT backlog item is neither committed nor reverted (its bytes and `git status --porcelain` entry are unchanged), and that the close is appended to the run's `events.jsonl`.
  - Depends on: E-03
  - Expected outcome: the restored tests for this group (or a "nothing to restore" note), each passing at HEAD.
  - Execution state: pending

- [ ] E-06 RESTORE the unclosed-report group (deleted class `UnclosedReport`). Call `render_unclosed_report`, `record_unclosed_backlog_items`, `emit_shutdown_report` and `render_runs_pointer` on constructed run state, and assert the following. Each open item is listed with its reason. A run with nothing outstanding prints no section. The `backlog-items-left-open` ledger record is written BEFORE the print, and survives when the print stream raises. A second `emit_shutdown_report` call prints nothing more. The pointer names the real run id and a verb the CLI really has (run `python3 -m agent_workflows runs --help` and assert exit 0). `main` invoked with `--json` on a prepared run emits stdout that `json.loads` parses, with no `aw runs` pointer in it. Reset `runner_shared._SIGNAL_REPORT_DONE` and `_SIGNAL_REPORT_STATE` in `setUp` and `addCleanup` so tests stay order-independent under `pytest-randomly`.
  - Depends on: E-03
  - Expected outcome: the restored tests for this group (or a "nothing to restore" note), each passing at HEAD and under randomized order.
  - Execution state: pending

- [ ] E-07 RESTORE the signal and shutdown group (deleted classes `ShutdownReportOnInterrupt` and the `SharedNotCopied` rows `test_both_drivers_emit_the_shutdown_report_on_normal_exit` and `test_an_interrupt_BEFORE_the_first_turn_still_reports`; its `expose`/`shared_not_copied` rows are DELEGATION-COVERED and its finalize-call row is E-04's). Use the recovered `_SIGNAL_SCRIPT` approach: spawn a REAL subprocess per driver, wait for `READY`, send a real `SIGINT` and a real `SIGTERM`, and assert exit 130 and 143 respectively, the unclosed item named on stderr, the `aw runs` pointer, and the `backlog-items-left-open` record in `events.jsonl`. For each driver's `main`, raise a real `KeyboardInterrupt` from the patched `run_queue` and assert the report goes to STDERR with exit 130. For the SIGTERM wiring row (`test_the_sigterm_funnel_is_wired_in_both_drivers_main`), call each driver's `main(["status", "--repo", <tmp>, "run-nope"])` with SIGTERM reset to `SIG_DFL` and assert the process's SIGTERM disposition afterwards is a callable Python handler (restore `SIG_DFL` in `addCleanup`). For the handler-safety property, invoke `signal_report_callback()()` with recording traps on `run_lock`, `locked_run` and `save_state`, resolved on whichever module exposes them, and assert none is reached AND the ledger file was written. For the child-kill separation, patch each driver's `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS` to sentinels, spy on `runner_shutdown.terminate_process`, and assert the sentinels arrive and the shutdown-report helpers are not reached. Cover the normal-exit report and the interrupt-before-first-turn report (`reconcile_interrupted` raising) on a real `run_queue` drain. CI runs on `windows-latest` as well, where `send_signal(SIGINT)` is not a console Ctrl-C and SIGTERM terminates without running a Python handler, so the real-signal subprocess tests carry `@pytest.mark.skipif(sys.platform == "win32", reason=...)` naming that limit; the `main` KeyboardInterrupt funnel test covers Windows. Each subprocess test sets a `communicate(timeout=30)` and kills the child on timeout so a hang cannot stall the suite. Mark a subprocess test `@pytest.mark.slow` only if E-10's measurement requires it.
  - Depends on: E-03
  - Expected outcome: the restored tests for this group (or a "nothing to restore" note), each passing at HEAD on both drivers.
  - Execution state: pending

- [ ] E-08 RESTORE the integrity self-check group (deleted classes `BacklogCloseIntegritySelfCheck`, `CommittedTreeBacklogCloseIntegritySelfCheck`). On real scratch git repos, assert the following for `runner_shared.backlog_item_paths_for_id`: a single claimant is returned alone, two claimants are both returned, an absent id returns `[]`, and every path is repo-relative. For `backlog_item_paths_for_commit`, build REAL commits that hold an addition-only duplicate (2 claimants) and a deletion-only vanish (0 claimants), and assert the returned lists. Assert that one claimant comes back alone, that an absent id and an invalid sha return `[]`, and that paths are repo-relative. Through `process_backlog_close`, assert that a close producing a committed duplicate writes a `backlog-close-integrity-violation` event with rule `attention.committed-duplicate`, a vanish writes `attention.committed-absent`, and a no-commit (lane) close writes neither.
  - Depends on: E-03
  - Expected outcome: the restored tests for this group (or a "nothing to restore" note), each passing at HEAD.
  - Execution state: pending

### Task group 3: Prove, correct, and run

- [ ] E-09 PROVE SENSITIVITY of every restored test by re-applying, through the same restoring wrapper, the E-03 mutation for its property and running ONLY `tests/test_runner_backlog_close_behavior.py`. Each restored test must FAIL under its mutation and PASS after byte-identical restoration (equal `sha256`). Any restored test that stays green under its mutation is strengthened until it fails, never deleted to make the count work. Then CORRECT the stale citations, editing comment text only. (a) In `runner_shared.py`, the re-homed-block banner sentence "which is what `tests/test_runner_layering.py` now freezes" states that the freezing import-table test was a code pin deleted in `19313eed7` that will not return. (b) The same banner's "`tests/test_runner_shared.py::ReHomedHostNeutralNameTests` proves it by comparing each definition's docstring-stripped AST fingerprint ..." states that the AST-fingerprint proof was a one-time move-time check, deleted in `19313eed7`, that `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json` is a retained historical capture no test reads, and that byte-identity was a property of the move commits (`13760db4a`..`edcbbe275`), not a live assertion. Keep the "Do NOT reformat" design guidance, reworded so it no longer appeals to a live proof. (c) Make the twin parenthetical in `oc_runipd.py` ("proven by AST fingerprint in `tests/test_runner_shared.py::ReHomedHostNeutralNameTests`") consistent with (b). (d) In `tests/test_runner_delegation_and_host_independence.py`, the docstring line "(which is tracked under backlog item yf1p8y)" names `tests/test_runner_backlog_close_behavior.py` as the carrier.
  - Depends on: E-04, E-05, E-06, E-07, E-08
  - Expected outcome: per restored test, a FAIL-under-mutation and PASS-after-restore pair with equal hashes; the four corrected passages; a post-edit `rg -n 'test_runner_layering|ReHomedHostNeutralNameTests' agent_workflows/` showing only retirement statements.
  - Execution state: pending

- [ ] E-10 MEASURE and RUN. (The comment-only AST proof is E-11.) Time `python3 -m pytest -o addopts="" -q -n auto tests/test_runner_backlog_close_behavior.py`. If the module adds more than 30 seconds to the bare suite, mark its subprocess-driven tests `@pytest.mark.slow` and record the numbers either way. Note honestly that CI's `-m slow` step in `.github/workflows/tests.yml` is ADVISORY (`continue-on-error: true`), so a slow-marked restored test is run in CI but does NOT gate; prefer keeping the tests fast (one subprocess per signal per driver) so they stay in the gating default selection. Run the module three times with `-o addopts="" -n auto` and three DIFFERENT explicit seeds via `-p randomly --randomly-seed=<n>` to rule out order dependence on the module-level signal-report registry. Finally, run the full fast suite BARE as `python3 -m pytest`, and attribute any failure by re-running the same node ids at the E-01 base commit.
  - Depends on: E-09
  - Expected outcome: the module wall time and slow-marker decision, three randomized green runs, and a bare-suite `N passed` summary with every failure attributed.
  - Execution state: pending

- [ ] E-11 PROVE the production edits are comment-only. Compare `ast.dump(ast.parse(src), include_attributes=False)` for `agent_workflows/runner_shared.py` and `agent_workflows/oc_runipd.py` at the E-01 HEAD (`git show <sha>:<path>`) and after the E-09 edit. Comments are not in the AST, so the dumps must be EQUAL. This is a one-off validation script under `/tmp/opencode/`, not a committed test. Also confirm `git diff --name-only <E-01 sha> -- agent_workflows/` lists only those two files.
  - Depends on: E-09
  - Expected outcome: EQUAL AST dumps for both production files, and no other production file changed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `GUIDING_PRINCIPLES.md` P16: tests assert observable outcomes; never read production source with `inspect`/`ast`/regex/substring, never assert caller counts or censuses, never pin text. Its "Verify test sensitivity with mutation" bullet ("A test is only valid if breaking the underlying behavior makes the test fail") is why E-03 and E-09 exist. The "Never weaken an assertion so it passes everywhere" bullet forbids hollowing a restored test that is hard to make pass.
- Maintainer rulings carried in backlog histories and quoted verbatim in executed plan `1o7i7g`'s Step 0 apply here. `pn7rw3`: "Code-pinning guards ... were deleted in the suite trim and will not be restored. Stale comments should simply remove references to them without seeking to restore code pins." `s4jctz`: "We do not test to make sure code does not change or pin imports." `aced01`: "We do not test to make sure text in a script or comment banner remains the same." And `xvp5vx` requires the audit to "strictly ignore tests that pinned code, AST, or text ... only genuine behavioral outcomes lacking coverage may be triaged".
- The ONE AST use in this plan (E-11) is a one-off validation that comment edits changed no executable statement, the same technique `1o7i7g` V-06 and `65d5zf` use; it is evidence in this plan, never a committed test.
- The shutdown-report registry (`_SIGNAL_REPORT_DONE`, `_SIGNAL_REPORT_STATE`) is module-level state in `runner_shared`, re-exported by object identity through `oc_runipd` (measured: `oc_runipd._SIGNAL_REPORT_DONE is runner_shared._SIGNAL_REPORT_DONE` is True; `agy_runipd` does not expose the attribute), so tests reset it on `runner_shared` itself.
- `terminate_process` and the `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS` constants are per-host in both drivers and delegate to `runner_shutdown.terminate_process` (measured by `hasattr`), which is what the child-kill separation property drives.
- Run the suite BARE (`python3 -m pytest`); `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; narrow with `-o addopts=""`, never `-n0` or `-p no:randomly`.
- Commit through `aw commit z2ugxc -- <paths>`; never push.

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The deleted file is recoverable and bounded: 2703 lines, 12 classes, 58 tests. | `git show 19313eed^:tests/test_runner_backlog_close.py \| wc -l` -> 2703; `grep -c "def test_"` -> 58; `grep -c "^class "` -> 12. Its deletion: `git log --diff-filter=D -- tests/test_runner_backlog_close.py` -> `19313eed7`. | E-01 recovers it into a scratch path; E-02 triages a known population. |
| F-02 | Many deleted tests were ALREADY behavioral, so the file is not a pure pin population. | Docstrings such as `test_the_callable_is_handler_safe` ("REPLACES four `assertNotIn` searches ... with RECORDING TRAPS on the real collaborators"), `test_the_child_kill_escalation_path_is_unchanged` (patches grace constants and spies on `runner_shutdown.terminate_process`), and `test_sigint_produces_the_report_and_exits_130` (real subprocess, real signal) drive real code. Others are genuine pins, e.g. `SharedNotCopied.test_the_implementation_is_shared_not_copied` (object identity, already DELEGATION-COVERED by `1o7i7g`). | E-02 classifies by what was ASSERTED, not by docstring history. |
| F-03 | Authoring spot checks found several properties have no live test outside the delegation guard. | At HEAD `6245c7074`, `rg -l` over `tests/`: `emit_shutdown_report`, `register_signal_report`, `signal_report_callback`, `render_unclosed_report`, `record_unclosed_backlog_items`, `unclosed_backlog_items` -> only `tests/test_runner_delegation_and_host_independence.py`, which checks identity and delegation, not output. `backlog_item_paths_for_id`, `backlog_item_paths_for_commit`, `committed-duplicate`, `committed-absent` -> only `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`. `tests/test_runner_stop_triggers_e2e.py` sends a real SIGTERM but asserts stop LEVEL 3, not the report or exit 143. PARTIALLY COVERED: the earned-close gate (`tests/test_outer_close_spec_carrier.py::...test_case_6_mixed_all_terminal_empty_earned_paths_refuses` asserts "this run executed none of its carriers"), the host-labelled close message (`tests/test_backlog_close_host_label.py`), the gated setter end to end (`tests/test_backlog_set_adapter.py::...test_runner_shared_close_backlog_item_end_to_end`), and the child reaper (`tests/test_oc_runipd.py::ChildTerminationTests`, which tunes grace constants on `oc_runipd` only). | Starting hypothesis for E-02; E-03 confirms by mutation. |
| F-04 | `1o7i7g`'s Deferred row says "`backlog_item_paths_for_commit` has live coverage". That is not true at HEAD. | Same `rg` as F-03: no file under `tests/` other than a fixture that no test reads names the function. | E-08 owns it. The executed plan's record is NOT edited (AGENTS.md: close a post-execution gap with new work, not an in-place edit). |
| F-05 | Two `runner_shared.py` comment claims cite tests that do not exist, plus one twin in `oc_runipd.py`. | `runner_shared.py` re-homed-block banner (heading "runnerlayer Order 02 (`1f7xno`), backlog `cnwy8g`: THE RE-HOMED HOST-NEUTRAL NAMES"): "which is what `tests/test_runner_layering.py` now freezes" and "`tests/test_runner_shared.py::ReHomedHostNeutralNameTests` proves it by comparing each definition's docstring-stripped AST fingerprint". `oc_runipd.py` comment above the re-homed imports: "proven by AST fingerprint in `tests/test_runner_shared.py::ReHomedHostNeutralNameTests`". `ls tests/test_runner_layering.py` -> absent; `rg ReHomedHostNeutralNameTests tests/` -> no hit; `git log -S 'ReHomedHostNeutralNameTests' -- tests/test_runner_shared.py` -> `13760db4a` (added), `19313eed7` (deleted). | E-09 corrects all three into retirement statements; the oc twin is in scope so the two drivers' comments do not contradict each other (same reasoning as `65d5zf` F-05). |
| F-06 | Neighbouring dangling-citation work is owned elsewhere and touches different sites. | Pending `65d5zf` (backlog `3tov52`) rewrites `_findings_block_reason`, `resolve_prior_lane` and `parse_plan_file` sites in `runner_shared.py`; `dtelfb` (backlog `046nys`) owns the `test_no_new_module_level_first_party_import_in_runner_shared` sites; `j7daih` (graduated) owns a general check rule. None names `test_runner_layering` or `ReHomedHostNeutralNameTests` (`rg` over `.aw/records/plans/pending/`). | No overlap in edited passages; no `Item-Dependencies` edge needed (each runs in its own worktree through the merge gate). |

## Proposed changes (ordered, validatable)

1. Recover the deleted file, census it, and re-measure the coverage greps (E-01).
2. Triage all 58 tests into PIN / COVERED / DELEGATION-COVERED / UNGUARDED-CANDIDATE in the new module's docstring (E-02).
3. Confirm the triage by mutation against the live suite (E-03).
4. Restore the confirmed-unguarded behaviors group by group in `tests/test_runner_backlog_close_behavior.py` (E-04 to E-08).
5. Prove each restored test fails under its mutation; correct the three stale guard citations and the delegation-guard pointer (E-09).
6. Measure runtime, check order independence, and run the bare suite (E-10); prove the production edits are comment-only (E-11).

## Deferred / out of scope (with reason)

- RESTORING ANY PIN ROW (source reads, AST walks, text assertions, censuses, structural single-statement checks, `tests/test_runner_layering.py`'s `CLASSIFICATION` and `FROZEN_OC_TO_AGY_IMPORTS`).
  - Carrier-Declined: Forbidden, not deferred: P16 and the `pn7rw3`/`s4jctz`/`aced01`/`xvp5vx` rulings say these "will not be restored". Nothing is owed. E-02 still lists each PIN row so a reviewer can see it was considered and rejected.
- A CHECK RULE THAT REJECTS SOURCE COMMENTS CITING NONEXISTENT TESTS, which would have caught F-05 mechanically.
  - Carrier: j7daih
- THE OTHER DANGLING TEST CITATIONS IN `runner_shared.py`, `agy_runipd.py` and `oc_runipd.py`.
  - Carrier: 3tov52
- THE `test_no_new_module_level_first_party_import_in_runner_shared` CITATIONS.
  - Carrier: 046nys
- CORRECTING `1o7i7g`'s "`backlog_item_paths_for_commit` has live coverage" sentence (F-04).
  - Carrier-Declined: `1o7i7g` is in `executed/`, whose recorded text may not be rewritten. The gap it describes is closed by E-08 instead, and this plan's F-04 records the correction. Nothing further is owed.

## Scope check

- Over-scope: none. The new test module is the deliverable. The three comment edits are the backlog item's explicit "ALSO OWNS" clause; the `oc_runipd.py` twin is included only so the two drivers do not contradict each other on the same claim. The one-line docstring change in `tests/test_runner_delegation_and_host_independence.py` re-points a pointer that names this item, which would dangle once the item graduates. No executable production statement changes, and E-11 proves it.
- Under-scope: the plan restores coverage of properties the deleted file asserted; it does not audit the backlog-close code for properties the deleted file NEVER asserted. A COVERED verdict rests on a live test in another file, which can be weakened later without this module noticing. That is inherent to deduplicating coverage and is the reason E-03 mutation-confirms each COVERED row instead of trusting test names. The runtime-demonstration items (real signals, real `run_queue` drains, real git commits) are produced by the tests E-05, E-07 and E-08 write, so each is reachable by construction.

## Required tests / validation

- `tests/test_runner_backlog_close_behavior.py` passes under the bare suite and under three randomized-order runs (E-04 to E-08, E-10).
- Every restored test fails under its recorded mutation and passes after byte-identical restoration (E-09).
- Every triage verdict of COVERED or UNGUARDED is backed by a mutation result (E-03).
- The AST dumps of `agent_workflows/runner_shared.py` and `agent_workflows/oc_runipd.py` before and after are EQUAL (E-11).
- A bare `python3 -m pytest` with its `N passed` summary pasted and any failure attributed against the base commit (E-10).

## Spec / documentation sync

N/A: no `.spec.md` is amended or listed in `Scope-Paths`. This plan restores tests for behavior that is already specified and shipped, and it changes no behavior. No user-facing doc describes these internal test guards. The only prose edits are code comments and one test docstring, which are internal.

## Open questions

### OQ-01: Should the restored tests live in a new module or be folded into existing test files that already partly cover the area?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED toward one new module, `tests/test_runner_backlog_close_behavior.py`, from repository precedent. `1o7i7g` restored its two properties into a single new module rather than scattering them, which keeps the triage table and the tests it justifies together, and gives the delegation guard's docstring pointer one place to land. The deleted filename is deliberately NOT reused: live comments in `oc_runipd.py` and `agy_runipd.py` cite `tests/test_runner_backlog_close.py` as DELETED in `19313eed`, and reviving that name would make those accurate historical statements read as live claims.

### OQ-02: Where does the triage record live, given that this plan must not grow a records artifact the item did not ask for?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED toward the new module's docstring (E-02), with the mutation evidence pasted in this plan's V-items. The docstring sits next to the tests it justifies, survives the plan's move to `executed/`, and is what a future reader of the module sees first. That matches how `tests/test_runner_delegation_and_host_independence.py` documents what it does and does not restore. A separate research record would duplicate it and could drift.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: The pasted execution HEAD sha; the pasted class/test census output of the scratch copy (12 classes, 58 tests or the corrected numbers); the pasted `rg -l` output for each of the eleven collaborator symbols; each fact marked CONFIRMED or CORRECTED against F-01 and F-03; `git status --porcelain` showing the scratch copy is not inside the repository.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The new module's docstring triage table quoted in full, with exactly 58 rows (or the E-01 corrected count) and one verdict per row. Every PIN row quotes the offending source-reading or census construct. Every COVERED row names a live `tests/<file>::<test>` with the assertion line quoted. A pasted count of rows per verdict.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: For every mutated property, the pasted diff of the mutation, the pasted pytest summary line under mutation (with failing node ids if red), and the pasted pre-mutation and post-restoration `sha256` of the mutated file, which must be equal. The final UNGUARDED set listed by triage row id, with every reclassification named.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: The pasted pytest output for this group's restored tests (node ids shown, PASSED), or the "nothing to restore" note with its triage row ids. A source excerpt of one restored induced-failure test showing it asserts the item file's bytes are unchanged and a reason is recorded.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: The pasted pytest output for this group's restored tests (PASSED), or the "nothing to restore" note. For the path-scoped-commit test, the asserted `git show --name-status` expectation quoted. For the co-worker test, the asserted unchanged bytes and porcelain entry quoted. These observations are produced by the tests this E-item writes, driving `process_backlog_close` on a real scratch repository.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: The pasted pytest output for this group's restored tests (PASSED), or the "nothing to restore" note. The pasted `python3 -m agent_workflows runs --help` exit status used by the pointer-verb test. A source excerpt showing the `setUp`/`addCleanup` reset of `runner_shared._SIGNAL_REPORT_DONE` and `_SIGNAL_REPORT_STATE`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: The pasted pytest output, for BOTH drivers, of the real-subprocess SIGINT (exit 130) and SIGTERM (exit 143) report tests, the `main` KeyboardInterrupt funnel test, the handler-safety trap test, the child-kill separation test, and the normal-exit and pre-first-turn report tests (PASSED), or the "nothing to restore" note for any row E-03 found covered. Each observation is produced by the subprocess or `run_queue` drain this E-item's tests drive.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: The pasted pytest output for the working-tree and committed-tree integrity tests (PASSED), or the "nothing to restore" note. A source excerpt showing the committed-tree fixtures are REAL `git` commits (addition-only duplicate and deletion-only vanish), not mocked `git_runner` output. The asserted `rule` values `attention.committed-duplicate` and `attention.committed-absent` quoted.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: For every restored test, a pasted run of ONLY `tests/test_runner_backlog_close_behavior.py` under its mutation showing that test FAILED, then a pasted passing run after restoration, with equal pre/post `sha256`. The four corrected passages quoted in full, none containing a present-tense claim that a test freezes, proves, or enforces. The pasted post-edit `rg -n 'test_runner_layering|ReHomedHostNeutralNameTests' agent_workflows/` output, with every hit inside a retirement statement.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: The pasted module wall time and the slow-marker decision. Three pasted randomized-order runs of the module, each green, with their `randomly` seeds shown. The bare `python3 -m pytest` summary line pasted verbatim, with any failure re-run at the E-01 base commit and attributed.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: The pasted AST-comparison script and its output printing EQUAL for `agent_workflows/runner_shared.py` and `agent_workflows/oc_runipd.py`, and the pasted `git diff --name-only <E-01 sha> -- agent_workflows/` listing only those two files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Task group 2 has five restore items over one new file, but each item covers one deleted-class family with its own fixtures (scratch repos, constructed state, real subprocesses, real commits), so each is one test surface. They are not split into separate plans because they share one triage (E-02/E-03) and one sensitivity proof (E-09); splitting would re-run the triage per plan.

Execute only after explicit human approval (`- Status: approved`). OQ-01 and OQ-02 are resolved; no open question remains. Scope fence: `- Scope-Paths:` declares every path this plan may change; an edit outside it must be justified at finalize via `--scope-reason`. Commit only the four `Scope-Paths` files through `aw commit z2ugxc -- <paths>`, never `git add -A`, never push, never while an E-03/E-09 mutation is applied, and keep the recovered deleted file in a scratch path outside the repository. Restore BEHAVIORAL outcomes only: if a property can only be asserted by reading source, it is a PIN and stays deleted. Change no executable statement in any production module; E-11's AST comparison is the proof. Every test claim MUST be backed by the ACTUAL pasted runner output; never claim a run you did not perform. Lifecycle: in a managed lane the runner owns `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd begin z2ugxc`, fill every `V-*`, confirm `aw ipd lint --phase pre-transition` conforms, then `aw ipd finalize z2ugxc`. Never hand-roll a `git mv` into `executed/`.
