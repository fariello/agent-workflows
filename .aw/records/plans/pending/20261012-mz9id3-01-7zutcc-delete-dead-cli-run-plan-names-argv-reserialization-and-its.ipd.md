# IPD: Delete dead cli._run_plan_names argv reserialization and its private normalizer loader

- Date: 2026-10-12
- Kind: child
- Concern: `agent_workflows/cli.py` still carries `_run_plan_names`, a hand-maintained argv reserializer for the `normalize_plan_names` script, plus the `cli._load_normalizer` helper that only it calls. The `plan-names` verb that dispatched to it was removed in awcmdsurf Order 05, so both are unreachable, and the stale passthrough list sits beside the live one whose drift caused `xym8g8`.
- Scope: Delete `cli._run_plan_names` and `cli._load_normalizer` (its sole caller is `_run_plan_names`), and repoint the stale "mirroring cli" docstring pointer in `check_engine._load_normalizer`, which becomes the only loader. No behavior change: nothing dispatches to either function.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: mz9id3
- Set: mz9id3
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7zutcc
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004

- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `mz9id3` (no `- Blocks-Release:` on the item, so none is inherited; `Work-Kind: chore` is inherited and correct because unreachable code cannot affect any user). At authoring HEAD `ebe34e463875923bcf19665a0ce7c29ce14ccef3`, `grep -rn "_run_plan_names" --include=*.py` matched only the `def` line, and `cli._load_normalizer` had exactly one caller, `_run_plan_names`. Authoring widened the item by one function: deleting `_run_plan_names` alone would leave `cli._load_normalizer` dead too. Every live consumer (`ipd_lint`, `tests/test_spec_id6_filenames.py`, `tests/test_walkthrough_id6.py`, `check_engine.check_names`) already uses `check_engine._load_normalizer`.

## Goal

Remove the unreachable `cli._run_plan_names` and its private loader `cli._load_normalizer`. This leaves one plan-name normalizer loader (`check_engine._load_normalizer`) and deletes a stale argv passthrough list that could drift unnoticed, which is the defect class behind `xym8g8`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-derive and delete

- [ ] E-01 At execution HEAD, record the HEAD sha. Re-derive the dead-code facts, and do not trust this plan's numbers. (1) `grep -rn "_run_plan_names" --include=*.py .` (excluding `.aw/worktrees`) matches only the `def _run_plan_names` line in `agent_workflows/cli.py`. (2) `grep -rn "_load_normalizer" --include=*.py .` shows that `cli._load_normalizer` is called only from `_run_plan_names`, and every other caller resolves `check_engine._load_normalizer`. (3) `grep -rn "plan-names\|plan_names" agent_workflows/cli.py` shows no argparse parser or `args.command` dispatch for `plan-names`, only the two "awcmdsurf Order 05 (hard cutover)" comments. (4) Nothing reaches the names dynamically or by mock: `grep -rn "getattr(cli\|\"_run_plan_names\"\|'_run_plan_names'\|\"_load_normalizer\"\|'_load_normalizer'\|cli\._run_plan_names\|cli\._load_normalizer" agent_workflows tests` finds no hit that targets `cli` (the string-literal alternatives also catch `mock.patch.object(cli, "_load_normalizer", ...)`, the pattern `tests/test_cli.py` uses for other private `cli` helpers). IF ANY FACT HAS CHANGED, meaning a live caller now exists, STOP AND REPORT instead of deleting.
  - Depends on: none
  - Expected outcome: HEAD sha and the four grep outputs are recorded, and each one confirms the function pair is unreachable.
  - Execution state: pending
- [ ] E-02 Delete `def _load_normalizer()` and `def _run_plan_names(args, term)` from `agent_workflows/cli.py`, including their docstrings and bodies, as one contiguous block. It sits between the end of `_run_plans`'s board rendering (`return 0`) and `def _run_leaks_configure`. Leave the two "awcmdsurf Order 05 (hard cutover)" comments in place, because they document the verb removal and not the deleted functions. If removing the block leaves an import in `cli.py` with no remaining use, remove that import too. `importlib.util` is imported locally inside `_load_normalizer`, so it is expected to leave with the block.
  - Depends on: E-01
  - Expected outcome: neither symbol exists in `cli.py`, and `python3 -c "import agent_workflows.cli as c; print(hasattr(c,'_run_plan_names'), hasattr(c,'_load_normalizer'))"` prints `False False`.
  - Execution state: pending
- [ ] E-03 In `agent_workflows/check_engine.py`, edit the docstring of `check_engine._load_normalizer`, whose sentence "mirroring cli.py:2890" points at a bare line offset in `cli.py` (stale twice over: `cli._load_normalizer` sits near `def _run_plans`'s end, not line 2890). That pointer now names deleted code, so reword it to say that this is the single loader for the shipped plan-name normalizer. Do not change the function body.
  - Depends on: E-02
  - Expected outcome: `grep -n "mirroring cli" agent_workflows/check_engine.py` returns nothing, and the function body is byte-identical apart from the docstring.
  - Execution state: pending

### Task group 2: Verify

- [ ] E-04 Validate the deletion by running the existing behavioral surfaces: the full fast suite BARE as `python3 -m pytest` (it includes the normalizer-loading tests `tests/test_spec_id6_filenames.py`, `tests/test_walkthrough_id6.py`, `tests/test_releases.py` and the CLI surface tests), plus `python3 -m agent_workflows check plans names` and `aw ipd lint <this plan>` to drive the surviving loader end-to-end. If anything fails, re-run the same selection at the base commit before blaming this change, and report the comparison.
  - Depends on: E-03
  - Expected outcome: the suite passes, and `check plans names` exits as it did at base.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Commit through `aw commit <plan> -- agent_workflows/cli.py agent_workflows/check_engine.py <this plan>`. Never stage with `git add -A`, and never push (AGENTS.md "Agent execution contract").
- Run the suite bare as `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` (AGENTS.md "Repository development contract").
- Do not add a test asserting that a symbol is absent. That would be a code-pinning test (GUIDING_PRINCIPLES P16). Removing dead code is validated by the existing behavioral suite still passing, plus the E-01 reachability evidence.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence | Effect |
|---|---|---|---|
| F-01 | `cli._run_plan_names` is unreachable. | At `ebe34e46`, `grep -rn "_run_plan_names" --include=*.py` matched only its `def`. `cli.py` has comments reading "the old `plan-names` verb was REMOVED" (parser) and "the plan-family + `list` + `plan-names` command dispatch was removed" (dispatch). | Safe to delete. |
| F-02 | `cli._load_normalizer` is dead once F-01 is removed. | Its only call site is `normalizer = _load_normalizer()` inside `_run_plan_names`. `ipd_lint` uses `_ce._load_normalizer()`, both tests use `ce._load_normalizer()`, and `check_engine.check_names` uses its own module-local `_load_normalizer`. | Delete it in the same change, since it is a duplicate loader. |
| F-03 | The surviving loader's docstring points at the deleted one. | `check_engine._load_normalizer` docstring: "Load the shipped plan-name normalizer layout-agnostically (source checkout AND installed wheel), mirroring cli.py:2890." Re-verified at review HEAD `e4ea59ef8`: `def _load_normalizer` in `cli.py` now sits immediately before `def _run_plan_names`, far from line 2890, so the offset was already stale (review PR-001). | Reword the docstring (E-03). |
| F-04 | `tests/test_releases.py` loads `normalize_plan_names.py` through its own `spec_from_file_location`, not through either helper. | `"npn_rel", root / "setup-repo" / "tools" / "normalize_plan_names.py"`. | Unaffected. Listed only so the executor does not chase it. |
| F-05 | Review re-verification at HEAD `e4ea59ef8`: (1) `_run_plan_names` matches only its own `def` in `cli.py`; (2) `_load_normalizer` callers are `normalizer = _load_normalizer()` inside `cli._run_plan_names`, `npn = _ce._load_normalizer()` in `ipd_lint`, `npn = _load_normalizer()` in `check_engine.check_names`, and the two tests via `ce._load_normalizer()`; (3) `plan-names` appears in `cli.py` only in the two "awcmdsurf Order 05" comments and inside `cli._load_normalizer`'s own body (`normalize_plan_names.py` path and module name), which leave with the block; (4) the dynamic/mock grep returns no hit on either name. `importlib.util` is imported only locally inside the deleted function. Baseline: `tests/test_spec_id6_filenames.py tests/test_walkthrough_id6.py tests/test_releases.py` -> `46 passed`; `check plans names` exit 0. | Review probes (PR-002). | Premise holds. |

## Proposed changes (ordered, validatable)

1. Re-derive reachability at execution HEAD (E-01, V-01).
2. Delete the two functions from `cli.py` (E-02, V-02).
3. Fix the stale docstring pointer in `check_engine.py` (E-03, V-03).
4. Run the full suite and the normalizer-driven commands (E-04, V-04).

## Deferred / out of scope (with reason)

- A mechanical `aw check` rule for flags dropped by argv reserialization stays with the follow-up that `xym8g8` filed. This plan removes one instance and does not add the rule.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- `setup-repo/tools/normalize_plan_names.py` and its own CLI `main(argv)` stay. The script is live, because `check_engine` and `ipd_lint` load it.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none. Deleting `cli._load_normalizer` goes past the item's literal wording, but it is the dead remainder of the same deletion (F-02).
- Under-scope: none. No other caller, test, or doc references either symbol (F-01, F-02). The executed plans that mention `_run_plan_names` are historical records and must not be edited.

## Required tests / validation

- The full fast suite, run bare as `python3 -m pytest`, passes (E-04 / V-04). This plan performs that validation itself and depends on no other child.
- `python3 -m agent_workflows check plans names` and `aw ipd lint <plan>` still run, which proves the surviving loader works end-to-end (E-04 / V-04).
- The E-01 grep evidence proves reachability (V-01).

## Spec / documentation sync

N/A. No spec, README, or user-facing doc names `_run_plan_names` or `cli._load_normalizer`. The `plan-names` verb removal is already documented by awcmdsurf Order 05. The only prose change is the internal docstring in E-03.

## Open questions

None. Repository evidence answered reachability (F-01, F-02).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste the execution HEAD sha and the verbatim output of all four E-01 greps. (1) must show exactly one `def _run_plan_names` hit. (2) must show that the only `cli.py` call to `_load_normalizer` is inside `_run_plan_names`. (3) must show no `add_parser("plan-names"` and no `args.command == "plan-names"` (hits inside `cli._load_normalizer`'s body on the `normalize_plan_names.py` path are expected and are removed with it). (4) must show no dynamic reference to `cli`. Any additional live caller makes this FAIL.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff --stat -- agent_workflows/cli.py`, which shows deletions only, and the `cli.py` hunk showing that both `def` blocks were removed. Also paste the output of `python3 -c "import agent_workflows.cli as c; print(hasattr(c,'_run_plan_names'), hasattr(c,'_load_normalizer'))"`, which must be `False False`, and of `grep -n "_run_plan_names\|_load_normalizer" agent_workflows/cli.py`, which must be empty.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste the `check_engine.py` diff hunk, which must touch only the `_load_normalizer` docstring lines, and the empty output of `grep -n "mirroring cli" agent_workflows/check_engine.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the actual final summary line of a bare `python3 -m pytest` run (`N passed`), with zero failures attributable to this change. If a failure appears, paste the base-commit comparison. Also paste the exit code and the last lines of `python3 -m agent_workflows check plans names` and of `aw ipd lint` on this plan. Both must run without an import or loader error, which demonstrates that `check_engine._load_normalizer` is still reached through `check_engine.check_names` and `ipd_lint`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). No open questions remain. The executor follows the agent execution contract: commit only the Scope-Paths files and this plan through `aw commit 7zutcc -- <paths>`, never `git add -A`, never push, and paste the ACTUAL runner output for every test claim. Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is justified at finalize with `--scope-reason`. E-01's stop (a live caller now exists) is a genuine prerequisite stop, not a scope stop. Lifecycle: once `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence, the plan moves to `executed/`: under `aw oc run` / `aw agy run` the runner owns that finalize, so do not run `aw ipd finalize` or `git mv` yourself; executed by hand, run `aw ipd finalize 7zutcc`. Never `git mv` the plan by hand.
