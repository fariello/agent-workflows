# IPD: Phase 0: freeze state taxonomy + characterization and adversarial tests (forgetful-agent, missing-input, hook-bypass, protected-ref, nested-permission-deadlock)

- Date: 2026-08-28
- Kind: child
- Concern: Before any behavior changes, the wtiso migration needs a SAFETY NET. Research x03wgn Section 8 (Phase 0) requires that we (a) freeze the state taxonomy - assign every existing `.aw` state/run path a class, namespace, writer, retention rule, and migration owner per Section 2 - and (b) add characterization tests that PIN the CURRENT (partly broken) behavior of `aw oc run` / `aw agy run` plus the five adversarial tests from Section 7 (forgetful-agent-runs-no-tools, missing-input, hook-bypass, protected-ref mutation, nested-permission-deadlock). Today the runner puts absolute main-run paths in worker prompts (`oc_runipd.py:1469-1472`, emitted by `build_prompt` at `oc_runipd.py:1448`), copies the begin receipt into the lane (`sync_receipt_into_worktree`, `oc_runipd.py:470-484`), anchors receipts under worktree-relative `.aw/state` (`ipd_lifecycle.receipt_path_for`, `ipd_lifecycle.py:249-251`), keeps the lease table in memory (`worktree_lease.py:144-192`), and validates integration with a callback that returns `True` before the real merge (`agy_runipd.make_integration_validation_runner`, `agy_runipd.py:644-655`, the `return True` at `:653`). None of these are fixed here; this phase only DOCUMENTS the frozen taxonomy and CAPTURES current behavior as executable, falsifiable tests that later phases (02-06) must not regress and will flip from `xfail`/characterization to green.
- Scope: Phase 0 of the wtiso migration. Writes (1) ONE taxonomy document freezing every `.aw` state/run path's class/namespace/writer/retention/migration-owner, and (2) characterization + adversarial pytest modules. Changes NO production behavior: no edit to any `agent_workflows/*.py` runtime path. The adversarial tests are characterization/`xfail` tests that PIN current behavior and are referenced by name from later phases' V-items. Also introduces the shared stable-error-code / pure-gate library STUB (name + empty predicate surface) so Phases 2-5 have one import site; this phase asserts only that the stub exists and is importable, not that any rule is implemented.
- Scope-Paths: docs/wtiso-state-taxonomy.md, tests/test_wtiso_taxonomy_freeze.py, tests/test_wtiso_characterization.py, tests/test_wtiso_adversarial.py, agent_workflows/wtiso_gate.py
- Item-Dependencies: none
- Status: approved
- Set: wtiso
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 8zgybk
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Found and fixed a GREENWASH HOLE in the safety net itself (PR-004): E-06/E-07/E-08 each specified ONE test function marked `xfail(strict=True)` that also had to contain an assertion passing today. Verified experimentally that pytest scores a function as ONE outcome, so (a) the passing half is invisible (`1 xfailed` only), making V-06/V-07/V-08's "show it passed" unsatisfiable, and (b) a REGRESSION in the git-observability half still reports a green `xfailed`, masking exactly the failure this net exists to catch. Added a mandatory two-function splitting rule (`_now` unmarked + `_pinned_absent` strict-xfail), verified to give `1 passed, 1 xfailed` and to report `1 failed` on a planted regression. Corrected 10 stale `file:line` citations (PR-001): the plan cited research snapshot `8d1bcd5`, but oc_runipd.py has grown ~73-81 lines (prompt block 1388->1469, sync_receipt 462->470, run root 1089->1163, driver.lock 666->740, stall timeout 1556->1629, validation runner 640->644); all behavioral claims re-confirmed true against live code and all 11 corrected citations verified to resolve. Fixed a nonexistent API (PR-002): E-03 named `oc_runipd.build_execution_prompt`, which does not exist - the real builder is `build_prompt(item, state, run_dir, plan_path, recovery)` at :1448, verified to emit all three asserted tokens. Replaced an unfalsifiable gate (PR-003): "ZERO `xpassed`" can never fail under `strict=True` (an XPASS is reported as `failed` with `[XPASS(strict)]`), so the real signal is `failed == 0` AND `xfailed > 0`. Replaced a VACUOUS assertion (PR-005): E-07 asserted no `external_directory` allow exists in the runner source, but that string appears nowhere in the package, so it passes even after qyaime is fixed; retargeted to the actual root cause, bare `--auto` at :1719 with no permission config. Removed the self-referential Scope-Paths entry (PR-006), matching every executed plan and 4 of 6 siblings, since `aw ipd finalize` owns the plan file and the declared `pending/` path ceases to exist on finalize. Verified clean: `xfail(strict=True)` semantics, E-03/E-04/E-05 constructibility, `DEFAULT_STALL_TIMEOUT == 600.0`, the runner returning True for a non-empty diff, no release-gate drift (no From-Backlog), and the contract reproduced verbatim from bl9q3d.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Freeze the wtiso state taxonomy in a single durable document and lock the current runner behavior (including its known defects) behind characterization tests plus the five adversarial tests from research x03wgn Section 7, so every later migration phase has a falsifiable safety net that changes NO production behavior in this phase. This is the net the rest of the migration depends on: later phases flip these pinned tests from characterization/`xfail` to green.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: freeze the state taxonomy

- [ ] E-01 Write `docs/wtiso-state-taxonomy.md` freezing every existing `.aw` state/run path into the x03wgn Section 2 model: a row per artifact with columns class (product | control-authority | transaction | lane-evidence | reconstructible-cache), namespace (project | checkout | run | lane | attempt | transaction), canonical writer (worker | driver | user | tool), retention class (tracked-publish | local-retain | secret-local | discardable | unknown), and migration owner (the wtiso child id6 that relocates/repairs it). Include at minimum: begin receipt (`.aw/state/ipd-lifecycle/<id6>.receipt.json`, `ipd_lifecycle.py:249-251`), run tree (`.aw/records/runs/<run-id>/`, `oc_runipd.py:1163`), the copied-into-lane receipt (`oc_runipd.py:470-484`), the in-memory lease table (`worktree_lease.py:144-192`), the lane worktree (`.aw/worktrees/<id6>`), the run driver lock (`oc_runipd.py:740`), and the ledger store lock (`run_ledger_store.py`). Every row's migration-owner MUST be one of wtiso-01..07.
  - Depends on: none
  - Expected outcome: `docs/wtiso-state-taxonomy.md` exists with one classification table covering the enumerated paths, each row assigned all five attributes, citing the real file:line for each path.
  - Execution state: pending

- [ ] E-02 Add `tests/test_wtiso_taxonomy_freeze.py` that parses `docs/wtiso-state-taxonomy.md` and asserts the freeze is complete and legal: every row uses only the allowed enum values for class/namespace/writer/retention, every migration-owner is a real wtiso child id6 (`8zgybk,qcqhj7,rchpms,7p9n2v,58ha43,2c122z,1o4eif`), and every path the runner constructs today (`.aw/state/ipd-lifecycle`, `.aw/records/runs`, `.aw/worktrees`, `driver.lock`) appears at least once. A missing path or an illegal enum FAILS the test.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_wtiso_taxonomy_freeze.py -q` collects and passes; deleting a required row from the doc makes it fail.
  - Execution state: pending

### Task group 2: characterize current runner behavior

- [ ] E-03 Add `tests/test_wtiso_characterization.py::test_worker_prompt_names_main_run_paths` that calls the REAL prompt builder `oc_runipd.build_prompt(item, state, run_dir, plan_path, recovery)` (`oc_runipd.py:1448`; there is NO `build_execution_prompt` - verified at review, the only prompt builders are `build_review_prompt:1434`, `build_prompt:1448`, `build_verifier_prompt:1536`, `write_prompt:1603`) and ASSERTS the returned prompt TODAY contains the absolute external run-dir / outcome / report paths (the x03wgn defect: worker directed outside the lane). Call it with a minimal in-memory fixture - `item={"setid": ..., "id6": ..., "position": 1, "attempts": []}`, `state={"run_id": ...}`, a tmp `run_dir`, a tmp `plan_path`, `recovery=False` - which needs NO real repo, worktree, or subprocess (verified constructible at review). This PINS current behavior; Phase 1 (qcqhj7) will invert this assertion.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_wtiso_characterization.py -q -k prompt_names_main_run_paths` passes against current code; the test docstring names qcqhj7 as the phase that flips it.
  - Execution state: pending

- [ ] E-04 Add `tests/test_wtiso_characterization.py::test_receipt_is_copied_into_lane` that exercises `oc_runipd.sync_receipt_into_worktree(repo, worktree, id6)` (`oc_runipd.py:470-484`) with a fake main receipt and ASSERTS a duplicate receipt file appears at the worktree-relative `ipd_lifecycle.receipt_path_for(worktree, id6)` - PINNING the receipt-copy defect (x03wgn Section 7 "Receipt copied into lane"). Two PLAIN tmp directories suffice for `repo` and `worktree` (no real git worktree needed): write the source receipt to `ipd_lifecycle.receipt_path_for(repo, id6)` after `mkdir(parents=True)`, then call the function - verified at review to yield `<worktree>/.aw/state/ipd-lifecycle/<id6>.receipt.json`. Phase 4 (58ha43) removes the copy and will delete/flip this.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_wtiso_characterization.py -q -k receipt_is_copied_into_lane` passes; the test asserts the destination path resolves under the worktree, not a central control root.
  - Execution state: pending

- [ ] E-05 Add `tests/test_wtiso_characterization.py::test_integration_validation_returns_true_before_merge` that calls `agy_runipd.make_integration_validation_runner(state, run_dir, item)` and ASSERTS its returned `_runner(combined_diff, merged_files)` returns `True` unconditionally (`agy_runipd.py:644-655`, the bare `return True` at `:653`) even for a fabricated non-empty combined diff - PINNING x03wgn finding #6 (validation passes before the actual merged tree exists). Empty dict/`Path`/dict args suffice (the factory ignores them; verified at review: `make_integration_validation_runner({}, Path("."), {})("non-empty combined diff", ["changed.py"])` returned `True`). Phase 5 (2c122z) replaces it with real candidate-merge validation and will flip this.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_wtiso_characterization.py -q -k returns_true_before_merge` passes; the assertion is `self.assertTrue(runner("any diff", ["f"]))`.
  - Execution state: pending

### Task group 3: adversarial tests (guards the later phases rely on)

MANDATORY TEST-SPLITTING RULE (applies to every E-item in this group; added at review after a demonstrated greenwash hole). A guard has TWO halves: an assertion that MUST PASS TODAY (the observability/format half) and an assertion pinning a NOT-YET-BUILT driver guard. These MUST be TWO SEPARATE test functions, never one function carrying both:

- `test_<guard>_<observable>_now` - unmarked; MUST PASS today.
- `test_<guard>_<driverguard>_pinned_absent` - `@pytest.mark.xfail(strict=True, reason="... lands in <phase>")`.

WHY (verified experimentally at review, not theory): pytest evaluates a whole test function as ONE outcome. If both halves live in one `xfail(strict=True)` function, then (a) the passing half is INVISIBLE - the run reports only `1 xfailed`, so a V-item demanding proof the observability assertion passed cannot be satisfied; and worse (b) if the observability half later REGRESSES, the function still reports a green `xfailed`, silently masking the exact failure this safety net exists to catch. A one-function design is therefore itself a greenwash hole and violates contract rule 3. Splitting was verified to yield `1 passed, 1 xfailed`, and a planted regression in the passing half then correctly reported `1 failed, 1 xfailed`.

- [ ] E-06 Add TWO tests to `tests/test_wtiso_adversarial.py` per the splitting rule: (a) `test_forgetful_agent_git_observable_now` - a harness simulating an agent that edits a tracked file in a lane worktree, runs NO `aw` command, writes NO `outcome.json`, and exits 0, asserting real git state (`git status --porcelain` non-empty, or the working-tree/`base..HEAD` diff) still shows the edit, i.e. the driver COULD observe the work from git alone (UNMARKED, must pass today); and (b) `test_forgetful_agent_driver_report_pinned_absent` - `@pytest.mark.xfail(strict=True, reason="driver-observed OBSERVED state lands in rchpms/Phase 2")` asserting a driver-observed report was produced, which cannot hold until Phase 2. x03wgn Section 7 row "Agent forgets every custom AW tool" + Section 8 Phase 0 item 4.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_wtiso_adversarial.py -q -k forgetful_agent` reports exactly `1 passed, 1 xfailed` (the git-observability test passes VISIBLY as its own result; the driver-report test xfails), and ZERO failed.
  - Execution state: pending

- [ ] E-07 Add FOUR tests to `tests/test_wtiso_adversarial.py` per the splitting rule, two per guard: (a) `test_missing_input_token_format_now` (UNMARKED) asserts the `AW_MISSING_INPUT:<path>:<why>` token format from x03wgn Section 4 is parseable by the regex this Set will use, AND asserts the CURRENT launch reality that motivates qyaime: `oc_runipd` launches OpenCode with a bare `--auto` (`oc_runipd.py:1719`) and ships NO permission configuration - assert `"--auto" in <launch argv builder source>` and that the module source contains NO `OPENCODE_CONFIG_CONTENT`/`"permission"` key configuring `external_directory`. DO NOT assert merely that the string `external_directory` is absent from `agent_workflows/`: verified at review that this string appears NOWHERE in the package, so such an assertion is VACUOUSLY true and would still pass after the deadlock is fixed or the runner deleted - it proves nothing. (b) `test_missing_input_driver_denial_pinned_absent` - `xfail(strict=True, reason="AW_MISSING_INPUT deny/classify/resume lands in qcqhj7/Phase 1")`. (c) `test_hook_bypass_detectable_from_git_now` (UNMARKED) simulates `git commit --no-verify` on a forbidden staged path in a tmp repo and asserts the violation is still visible in `git show --name-only` (the driver can re-check what the hook skipped). (d) `test_hook_bypass_driver_rejection_pinned_absent` - `xfail(strict=True, reason="shared gate predicate lands in qcqhj7/rchpms")`.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_wtiso_adversarial.py -q -k "missing_input or hook_bypass"` reports exactly `2 passed, 2 xfailed` and ZERO failed.
  - Execution state: pending

- [ ] E-08 Add THREE tests to `tests/test_wtiso_adversarial.py` per the splitting rule: (a) `test_protected_ref_mutation_detectable_now` (UNMARKED) snapshots `git worktree list --porcelain` + `git for-each-ref` before/after a simulated stray ref write in a tmp repo and asserts the mutation is detectable by diffing the snapshots (x03wgn Section 4 "shared Git common directory mutated"; default mode = detection). (b) `test_nested_permission_only_stall_watchdog_now` (UNMARKED) asserts the CURRENT bound is the coarse stall watchdog only: `oc_runipd.DEFAULT_STALL_TIMEOUT == 600.0` (`oc_runipd.py:1629`; verified at review) and `killpg`/`getpgid` process-group cleanup exists (`oc_runipd.py:1639-1643`), while NO sub-second permission-deadline symbol is present (assert the module source matches no `permission_deadline`/`permission_timeout`/`PERMISSION_DEADLINE`; verified absent at review) - PINNING the x03wgn Section 6 / R10 / R11 gap. (c) `test_nested_permission_bounded_kill_pinned_absent` - `xfail(strict=True, reason="permission-event deadline lands in qcqhj7/Phase 1")` feeding a captured OpenCode event stream containing an unanswered CHILD-session `external_directory` ask and asserting a bounded permission-triggered kill, which cannot hold until Phase 1.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_wtiso_adversarial.py -q -k "protected_ref or nested_permission"` reports exactly `2 passed, 1 xfailed` and ZERO failed.
  - Execution state: pending

### Task group 4: seed the single shared gate library

- [ ] E-09 Add `agent_workflows/wtiso_gate.py` as the ONE pure predicate + stable-error-code library that Phases 2-5's hook / `aw lane status` / driver / finalize / integration will all import (x03wgn Section 8 Phase 0 item 5, Section 5 Layer 5 "one pure policy library with stable error codes"). This phase ships only the module skeleton: the stable error-code constants (e.g. `AW_GATE_SCOPE`, `AW_LIFECYCLE_ROLE`, `AW_MISSING_INPUT`) and empty/`NotImplementedError` predicate signatures with docstrings naming the owning phase. No rule logic is implemented here. Add a test in `tests/test_wtiso_taxonomy_freeze.py::test_gate_library_is_single_import_surface` asserting the module imports and exposes the named error-code constants.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_wtiso_taxonomy_freeze.py -q -k gate_library_is_single_import_surface` passes; `python3 -c "import agent_workflows.wtiso_gate"` exits 0.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Tests are `unittest`-style TestCase modules run under pytest, launched as `python3 -m agent_workflows.<mod>` with `PYTHONPATH` pinned to repo root; fixtures build a tmp repo `.aw/records/runs/<run-id>/{outcomes,sessions,prompts}` and a `state.json` (see `tests/test_oc_runipd.py:24-48`).
- The runner's run root is `repo/.aw/records/runs` (`oc_runipd.py:1163`); begin receipts live at `repo/.aw/state/ipd-lifecycle/<id6>.receipt.json` (`ipd_lifecycle.py:249-251`).
- Durable narrative docs go under `docs/` (existing `docs/architecture.md`, `docs/recovery.md`); the taxonomy doc joins them.
- `aw ipd lint --phase author <file>` is the structural gate; `--detail` shows advisory findings.
- Full suite runs `python3 -m pytest -p no:randomly -q` (per the orchestrator's V-01).

## Findings

Findings cite research doc `20260828-wtiso-00-x03wgn` and real file:line evidence.

CITATION BASIS (added at review): every `file:line` reference in this plan was RE-VERIFIED against the current working tree on 2026-08-29 and corrected where it had drifted. The research report cites the pinned snapshot `8d1bcd5` (its R1 references), and `agent_workflows/oc_runipd.py` has since grown by roughly 73-81 lines above most cited regions, so the research's raw line numbers no longer resolve (e.g. the prompt block moved 1388-1400 -> 1469-1472; `sync_receipt_into_worktree` 462 -> 470; the run root 1089 -> 1163; `driver.lock` 666 -> 740; `DEFAULT_STALL_TIMEOUT` 1556 -> 1629; the validation runner 640 -> 644). All BEHAVIORAL claims were re-confirmed true against live code. Cite SYMBOL NAMES as the primary anchor (they are stable) and treat line numbers as secondary: re-verify with `grep -n '<symbol>'` before relying on any number, since this file will keep moving as Phases 1-6 edit the same modules.

| # | x03wgn section | Finding | Real code evidence |
|---|---|---|---|
| F1 | Section 2 (state taxonomy, classification table) | Five artifact classes (product / control-authority / transaction / lane-evidence / reconstructible-cache) with per-artifact writer/namespace/retention must be frozen before any relocation. E-01/E-02 implement the freeze. | begin receipt `ipd_lifecycle.py:249-251`; run tree `oc_runipd.py:1163`; lease table `worktree_lease.py:144-192` |
| F2 | Section 8 Phase 0 item 2 (characterize current behavior) | The worker prompt names absolute external run/outcome/report paths, directing the worker outside its lane. E-03 pins it. | `oc_runipd.py:1469-1472` (`External run directory:`, `Required JSON outcome:`, `Driver report:`) |
| F3 | Section 7 "Receipt copied into lane" + Section 9 finding #2 | The begin receipt is copied into the lane worktree so two authorities can diverge. E-04 pins it. | `oc_runipd.sync_receipt_into_worktree` `oc_runipd.py:470-484`; call site `oc_runipd.py:2098` |
| F4 | Section 9 finding #6 (validation before merge) | Single-lane integration validation returns `True` before the real merged tree exists. E-05 pins it. | `agy_runipd.make_integration_validation_runner` `agy_runipd.py:644-655` (the `return True` at `:653`) |
| F5 | Section 7 "Agent forgets every custom AW tool" + Section 8 Phase 0 item 4 | A forgetful agent that runs no tools and writes no outcome.json still leaves observable git state; the driver-observed OBSERVED report does not yet exist (owned by rchpms). E-06 pins it (git-observable now, driver-report `xfail`). | run root/prompt path `oc_runipd.py:1469-1472`; no OBSERVED-from-git code present |
| F6 | Section 4 (missing-input recovery) + Section 5 Layer 5 (hook bypass) | The `AW_MISSING_INPUT:<path>:<why>` contract and the driver's independent re-check of `--no-verify` bypass do not exist yet; git state remains observable. E-07 pins both. | `--auto` launch `oc_runipd.py:1719`; no missing-input/gate predicate present |
| F7 | Section 4 (protected Git mutation) + Section 6 (permission deadlock) + R10/R11 | Only a 600s stall watchdog + `killpg` group cleanup exists; there is NO sub-second permission-event deadline parsing nested child asks. Protected-ref mutation is detectable only by explicit before/after snapshot, which the runner does not take. E-08 pins both gaps. | watchdog/`killpg` `oc_runipd.py:1639-1643` + the stall watchdog at `oc_runipd.py:1629`; DEFAULT_STALL_TIMEOUT `oc_runipd.py:1629` |
| F8 | Section 8 Phase 0 item 5 + Section 5 Layer 5 | One pure gate/predicate library with stable error codes must back hook + `aw lane status` + driver + finalize + integration so rules cannot drift. E-09 seeds the single import surface (skeleton only). | today no shared predicate module; hook/driver rules would be duplicated |

## Proposed changes (ordered, validatable)

1. `docs/wtiso-state-taxonomy.md` (E-01): the frozen classification table.
2. `tests/test_wtiso_taxonomy_freeze.py` (E-02, E-09): freeze completeness + legality checks, gate-library import surface check.
3. `tests/test_wtiso_characterization.py` (E-03, E-04, E-05): pin prompt paths, receipt copy, pre-merge validation.
4. `tests/test_wtiso_adversarial.py` (E-06, E-07, E-08): forgetful-agent, missing-input, hook-bypass, protected-ref, nested-permission-deadlock; each guard's not-yet-built driver side is `xfail(strict=True)` so it can never silently green.
5. `agent_workflows/wtiso_gate.py` (E-09): the single shared error-code + predicate skeleton (no rule logic).

## Deferred / out of scope (with reason)

- Any production behavior change to `oc_runipd.py` / `agy_runipd.py` / `ipd_lifecycle.py` / `worktree_lease.py` / `project_context.py` / `project_registry.py`: owned by Phases 1-6 (qcqhj7, rchpms, 7p9n2v, 58ha43, 2c122z, 1o4eif). Phase 0 only documents and pins.
- Implementing any gate PREDICATE rule inside `wtiso_gate.py`: E-09 ships only the error-code constants + signatures; rule bodies are owned by rchpms/qcqhj7 (that is why the module is seeded here, so there is exactly one import site to fill).
- The real-repo local-input inventory (x03wgn Section 8 Phase 0 item 3, "representative real repositories"): captured as OQ-01; a synthetic tmp-repo fixture is sufficient for the pinned tests, and the broad inventory is a data-gathering task better done alongside qcqhj7's input-manifest work.

## Scope check

- Over-scope: none. Every file in Scope-Paths is a doc, a test, the new shared-gate skeleton, or this IPD. No runtime code path is modified.
- Under-scope: none. All five adversarial tests from x03wgn Section 7 (forgetful-agent, missing-input, hook-bypass, protected-ref, nested-permission-deadlock) are present (E-06..E-08), the taxonomy freeze is complete (E-01/E-02), current behavior is characterized (E-03..E-05), and the single gate-library import surface is seeded (E-09). Green-path-only coverage is avoided: every adversarial test pins a real defect and `xfail`s the not-yet-built guard rather than asserting a false pass.

## Required tests / validation

- Per-item commands are in each V-item below; run each and paste ACTUAL stdout/stderr + exit code.
- Whole-phase gate: `python3 -m pytest tests/test_wtiso_taxonomy_freeze.py tests/test_wtiso_characterization.py tests/test_wtiso_adversarial.py -p no:randomly -q` must end in a summary line containing BOTH `passed` and `xfailed` and reporting **ZERO `failed`** and **ZERO `error`**, with exit code 0.
- HOW `strict=True` ACTUALLY REPORTS (verified experimentally at review; the earlier "ZERO `xpassed`" wording was unfalsifiable): under `xfail(strict=True)`, a guard that unexpectedly starts passing is reported as **`failed`** with an `[XPASS(strict)]` reason, NOT as `xpassed`. A strict run therefore NEVER prints `xpassed` at all, so "ZERO xpassed" was trivially satisfiable boilerplate. The real, falsifiable signal is `failed == 0` plus a nonzero `xfailed` count: `failed > 0` means either a genuine break or a guard that silently became real without its owning phase (grep the output for `XPASS(strict)` to distinguish). Additionally, `xfailed` must be nonzero - if `xfailed == 0` the pins have vanished and the safety net is gone.
- Expected phase-0 shape: 5 unmarked adversarial tests passing (E-06a, E-07a/c, E-08a/b) + 4 strict-xfail pins (E-06b, E-07b/d, E-08c), plus the taxonomy/characterization/gate-library tests.
- Structural gate: `aw ipd lint --phase author <this file>` reports conforming.

## Spec / documentation sync

- New doc `docs/wtiso-state-taxonomy.md` is the durable taxonomy freeze; no existing spec is edited. The `ipd-spec`/`ipd-structure-and-linting` specs are unaffected (this is a normal child IPD). N/A to change any spec Status.

## Open questions

### OQ-01: Should the real-repo local-input inventory (x03wgn Section 8 Phase 0 item 3) be gathered in this phase or deferred to Phase 1?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Deferred to Phase 1 (qcqhj7). Phase 0's pinning tests only need a synthetic tmp-repo lane (matching the existing `tests/test_oc_runipd.py` fixture style); the broad multi-repo inventory is input-manifest design data that qcqhj7 owns when it builds the minimal input manifest and `AW_MISSING_INPUT` contract. Recording it here avoids blocking the safety net on a data-gathering task.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `test -f docs/wtiso-state-taxonomy.md && grep -c '| ' docs/wtiso-state-taxonomy.md` prints a nonzero row count AND `grep -E 'ipd-lifecycle|records/runs|worktrees|driver.lock' docs/wtiso-state-taxonomy.md` returns each enumerated path at least once (exit 0). Paste the grep output showing the classification rows and the four cited paths.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest tests/test_wtiso_taxonomy_freeze.py -q -k "not gate_library" ` exits 0 and the summary line contains `passed`; then temporarily delete a required row from the doc and rerun, pasting the `FAILED ... required path .* missing` line proving the freeze check is falsifiable (restore the row after). Paste both runs' actual output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_wtiso_characterization.py -p no:randomly -q -k prompt_names_main_run_paths` exits 0 with `1 passed`; the test source calls `oc_runipd.build_prompt(...)` (NOT a nonexistent `build_execution_prompt`) and asserts the returned string contains `External run directory:` / `Required JSON outcome:` / `Driver report:` (the current-behavior tokens at `oc_runipd.py:1469-1472`). Paste the pytest summary line and the asserting `assertIn(...)` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest tests/test_wtiso_characterization.py -p no:randomly -q -k receipt_is_copied_into_lane` exits 0 with `1 passed`; the test calls `oc_runipd.sync_receipt_into_worktree` (`oc_runipd.py:470`) and asserts a receipt file exists at `ipd_lifecycle.receipt_path_for(worktree, id6)` AND that this path is under the worktree dir (not a central root), i.e. it resolves to `<worktree>/.aw/state/ipd-lifecycle/<id6>.receipt.json`. Paste the summary line and the two asserts.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_wtiso_characterization.py -p no:randomly -q -k returns_true_before_merge` exits 0 with `1 passed`; the test builds the runner from `agy_runipd.make_integration_validation_runner` (`agy_runipd.py:644`) and asserts `runner("non-empty combined diff", ["changed.py"]) is True` (the unconditional `return True` at `agy_runipd.py:653`). Paste the summary line and the `assertTrue`/`assertIs(..., True)` line.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest tests/test_wtiso_adversarial.py -p no:randomly -q -k forgetful_agent -rX` exits 0 with a summary of exactly `1 passed, 1 xfailed` and ZERO `failed` - the `1 passed` MUST be `test_forgetful_agent_git_observable_now` (its own visible result, per the splitting rule) and the `1 xfailed` MUST be `test_forgetful_agent_driver_report_pinned_absent`. Paste the summary line, the `-rX` XFAIL reason line naming rchpms/Phase 2, and the `git status --porcelain` non-empty assertion from the test source. FALSIFIABILITY CHECK (paste this too): temporarily break the git-observability assertion and rerun, showing it reports `1 failed` - proving a regression in the passing half surfaces loudly instead of hiding as a green `xfailed` (restore afterward).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest tests/test_wtiso_adversarial.py -p no:randomly -q -k "missing_input or hook_bypass" -rX` exits 0 with a summary of exactly `2 passed, 2 xfailed` and ZERO `failed`. Paste the summary line, the two `-rX` XFAIL reasons (naming qcqhj7/Phase 1 and qcqhj7/rchpms), the `AW_MISSING_INPUT:` regex assertion, the `git show --name-only` assertion for the `--no-verify` commit, and the `--auto`-without-permission-config assertion. NEGATIVE REQUIREMENT (state explicitly that it was honored): the missing-input test must NOT assert merely that the literal string `external_directory` is absent from `agent_workflows/` - that string is absent today, so such an assertion is vacuous and passes even after the deadlock is fixed.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `python3 -m pytest tests/test_wtiso_adversarial.py -p no:randomly -q -k "protected_ref or nested_permission" -rX` exits 0 with a summary of exactly `2 passed, 1 xfailed` and ZERO `failed`. Paste the summary line, the `-rX` XFAIL reason naming qcqhj7/Phase 1, the before/after ref-snapshot diff assertion, and the assertion that `oc_runipd.DEFAULT_STALL_TIMEOUT == 600.0` (`oc_runipd.py:1629`) with no `permission_deadline`/`permission_timeout`/`PERMISSION_DEADLINE` symbol present in the module source.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: `python3 -c "import agent_workflows.wtiso_gate as g; print(g.AW_GATE_SCOPE, g.AW_LIFECYCLE_ROLE, g.AW_MISSING_INPUT)"` exits 0 and prints the three stable error-code constants; and `python3 -m pytest tests/test_wtiso_taxonomy_freeze.py -q -k gate_library_is_single_import_surface` exits 0 with `1 passed`. Paste both outputs.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This child inherits the orchestrator's shared anti-greenwash execution contract VERBATIM (source of truth: orchestrator bl9q3d, section "The shared anti-greenwash execution contract"). It is reproduced here in full and must not be weakened:

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: until wtiso-03 lands, finalize may hit xmqv5l; if so, record substantially-complete honestly rather than forcing.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.

Phase-0-specific application of the contract:

- Because Phase 0 changes NO production behavior, the adversarial guards' not-yet-built driver sides are pinned with `@pytest.mark.xfail(strict=True, ...)` naming the owning later phase. `strict=True` means an `xpassed` (the guard silently became real without its owning phase) is a hard FAILURE - this is how the safety net proves it is still pinning the current defect, not falsely greening.
- Execution: fill the taxonomy doc + tests + gate skeleton, run each V-item command and paste its ACTUAL output, then `aw ipd lint --phase pre-transition` on this file.
- Commit ONLY the Scope-Paths files, path-scoped (`git commit -m msg -- docs/wtiso-state-taxonomy.md tests/test_wtiso_taxonomy_freeze.py tests/test_wtiso_characterization.py tests/test_wtiso_adversarial.py agent_workflows/wtiso_gate.py`); never `git add -A`; never push; never `--no-verify`. This plan file itself is NOT in Scope-Paths and MUST NOT be listed there (matching the Set's other children and every executed plan in this repo): `aw ipd finalize` owns the plan file, appending the history entry, setting terminal status, `git mv`ing it out of `pending/`, and making the lifecycle commit. Declaring the `pending/` path would also declare a path that ceases to exist the moment finalize moves it. Edit the plan's own E/V state normally during execution; just do not commit it yourself.
- Lifecycle move on completion: verify V-01..V-09 with pasted output, then `aw ipd finalize` this plan. Do NOT move to `executed/` unless every V-item passed with pasted evidence.
