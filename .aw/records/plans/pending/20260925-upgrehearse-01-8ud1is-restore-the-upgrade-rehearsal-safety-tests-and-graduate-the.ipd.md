# IPD: Restore the upgrade-rehearsal safety tests and graduate the harness to an aw command

- Date: 2026-09-25
- Kind: child
- Concern: `tools/aw_upgrade_test.py` rehearses an upgrade in a sandbox copy of a real repo. Its four safety invariants (never write to the source, never push, never touch the real inventory, never delete anything but its own sandbox) lost their tests when `tests/test_aw_upgrade_test.py` was deleted in `19313eed`. The harness is also still a loose script rather than an `aw` command.
- Scope: IN: restore the deleted test file IN FULL (37 tests, all passing at review; maintainer ruling 2026-09-25); decide the shipped sandbox-root default against the two constraints review measured; then move the logic into the package behind a thin re-exporting `tools/` shim, register `aw upgrade-test` preserving the `--json` mechanism its restored `CliTests` pins, and declare its seven leaves. OUT: new rehearsal features; the synthetic-baseline rehearsal the source item defers; repairing the vacuous output-conformance CI step or restoring the two deleted declaration tests (plan `0yrtne` owns the whole-CLI test).
- Scope-Paths: tools/aw_upgrade_test.py, agent_workflows/upgrade_rehearsal.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_aw_upgrade_test.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- Set: upgrehearse
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 8ud1is
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved
- From-Backlog: u27q6g

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 10 findings PR-601..PR-610 all FIXED, 6 decisions D-1..D-6 recorded; review record written; aw ipd lint --phase review-finalize conforming
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog u27q6g. Verified at HEAD: the tool exists (1370 lines) and `aw upgrade-test` does not; the deleted test file's 13 safety-invariant tests still pass against today's tool (run in place from tests/). Maintainer ruled 2026-09-25 to restore those tests.

## Goal

The rehearsal harness's safety guarantees are tested again, and it is a first-class, documented `aw` command.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: safety tests first

- [ ] E-01 Restore `tests/test_aw_upgrade_test.py` from `19313eed^` IN FULL, all ten classes and 37 tests, not a safety-only subset. Measured at review by restoring the file verbatim and running it: `37 passed in 2.52s`, and `-k SafetyInvariant` gives `13 passed, 24 deselected`. So the whole file passes against today's tool, and the helpers it needs (`support.REPO_ROOT`, `git`, `init_repo`, `load_module`) all still exist.
  - Depends on: none
  - Expected outcome: 37 tests in the default suite, including the four `SafetyInvariant*` classes.
  - WHY IN FULL, correcting the original item's plan to drop `InspectionTests`, `SandboxCreationTests`, `ProbeAndObservationTests`, `CliTests` and `NoRunRehearsalTests` as pinning "incidental behavior": review read them and they are BEHAVIOR tests in temp directories, not structural pins. `CliTests` is the load-bearing case: `test_the_json_flag_is_honored_on_either_side_of_the_subcommand` pins a MEASURED regression in which a subparser's own `--json` default clobbered the value the top-level flag had already set, so `--json list` parsed to False and silently emitted human output to a caller that asked for machine output. That is the EXACT contract E-04 rewrites. Dropping those tests would remove the only guard on the work this plan does, in the same commit that does it. `InspectionTests` likewise pins the version/layout precedence every rehearsal report's claims rest on (a dual-layout repo must report the version it upgraded TO, not FROM).
  - The one test that needs an edit rather than a verbatim restore is `test_default_sandbox_root_is_computed_not_hardcoded`, which does `Path(TOOL).read_text()` and asserts the literal `DEFAULT_SANDBOX_ROOT = Path(` is absent. After E-03 moves the logic, that reads the SHIM and the assertion becomes vacuous. Point it at the package module in E-03, not here: in E-01 it must still read the tool and pass.
  - Execution state: pending

### Task group 2: graduate

- [ ] E-02 Decide and record the DEFAULT SANDBOX ROOT for a non-maintainer, which the source item `u27q6g` names as open work ("a shipped version should prefer the state root or a temp dir") and which E-01's restored tests CONSTRAIN in a way the original plan did not account for. Resolve it in the plan (see OQ-02) and write the resolution into this item before touching code; do not pick one while editing.
  - Depends on: E-01
  - Expected outcome: one named default, with the two constraints it must satisfy stated.
  - THE TWO CONSTRAINTS, both measured at review. FIRST, a restored SAFETY test asserts the shape: `test_default_sandbox_root_is_computed_not_hardcoded` requires `computed.name == SANDBOX_ROOT_NAME` AND `computed.parent.name == "tmp"`. A bare `tempfile.gettempdir()/aw-upgrade-tests` FAILS that parent assertion, so the original E-04 as worded would have broken a test E-01 restores, in the same plan. SECOND, and more important, the current nesting is a SAFETY MECHANISM, not an accident: `default_sandbox_root`'s docstring states that a sandbox placed directly under a discovery search root would be found as a managed repo and could be swept into a later `aw install all`, which is invariant 3, and the `tmp/` level exists because the immediate-children scan cannot reach it. Any new default must preserve that property or state why it no longer applies (a system temp dir is not a search root, so it is outside discovery for a different reason; say so rather than assuming it).
  - Measured, so the item is not justified on a false premise: `aw sanitize --agent` is CLEAN at HEAD (`findings:0`, exit 0), and `default_sandbox_root` is already COMPUTED with an `AW_UPGRADE_TEST_ROOT` override and carries a docstring saying a literal would be what the leak-sanitizer rejects. So there is NO tracked-file leak to fix. The real defect is narrower and is about a non-maintainer: the default assumes a configured search root exists and falls back to `Path.home()`, so a fresh user with no config gets `~/tmp/aw-upgrade-tests` in their home rather than a temp location. State the concern that way.
  - Execution state: pending

- [ ] E-03 Move the harness logic into `agent_workflows/upgrade_rehearsal.py`, leaving `tools/aw_upgrade_test.py` as a thin delegating shim, following the shipped precedent the source item names: `tools/pwatch.py` (35 lines) over `agent_workflows/pwatch.py` (1051), which adds the repo root to `sys.path`, imports the package module, RE-EXPORTS every non-dunder attribute, and delegates `main`. The re-export is load-bearing here, not stylistic: the restored tests reach internals through `load_module("aw_upgrade_test", TOOL)` and call `uat.<name>` for many private helpers, so a shim that only delegates `main` breaks them.
  - Depends on: E-02
  - Expected outcome: one implementation; `python3 tools/aw_upgrade_test.py --help` still works; the restored tests pass unchanged except the one noted below.
  - Point `test_default_sandbox_root_is_computed_not_hardcoded`'s `read_text` at `agent_workflows/upgrade_rehearsal.py` in this item, since after the move the shim no longer contains the code the assertion is about. Keep the assertion, do not delete it: it is the only mechanical guard against a future hardcoded default.
  - Apply E-02's decided default in this item (it is a one-line change to `default_sandbox_root`), and update the two restored assertions about its shape if and only if E-02's resolution changes that shape. Changing a safety test's expectation is permitted here ONLY because E-02 records the decision and its reason; do not relax an assertion to make a convenient default pass.
  - Execution state: pending

- [ ] E-04 Register `aw upgrade-test` in `cli._build_parser` with the same subcommands (`list`, `new`, `sandboxes`, `probe`, `env`, `clean`), dispatch in `main`, and support `--agent`/`--json` per the dual-audience output contract (exit 0 clean / 1 findings / 2 cannot-run).
  - Depends on: E-03
  - Expected outcome: `python3 -m agent_workflows upgrade-test --help` works; each subcommand parses; `--json` is honored on EITHER side of the subcommand.
  - PRESERVE THE `--json` MECHANISM E-01's `CliTests` pins, and read that table before wiring the flag: the tool declares `--json` on a SHARED PARENT parser with `store_const` and `default=None`, precisely so that a value set by the top-level flag is not clobbered by a subparser applying its own default last. A concrete `default=False` on either side reintroduces the measured regression silently. If the repository's standard output-mode helper sets a concrete default, that is a genuine conflict to REPORT rather than to resolve by weakening the restored test.
  - Execution state: pending

- [ ] E-05 Add a `CommandDeclaration` to `command_surface.COMMAND_INVENTORY` for `upgrade-test` and each of its six leaves, with the class/recipe/gate fields the existing declarations use for a comparable read/mutation pair (`list`/`sandboxes`/`probe`/`env` are reads, `new` is a mutation, `clean` is a mutation with a dry-run default, which the tool already implements).
  - Depends on: E-04
  - Expected outcome: none of the seven new leaves appears in `find_undeclared_leaves(_build_parser())`.
  - DO NOT CLAIM THE SET BECOMES EMPTY, which the original E-03 asserted. Measured at review: `find_undeclared_leaves` returns FIVE entries today (`oc profile add|default|list|remove|show`), so it is not empty at baseline and this plan cannot make it so. Those five are owned by pending plan `0yrtne` (Set `cmdsurf`), which declares them and restores the whole-CLI declaration test. Assert only the delta this plan owns: the seven new leaves are absent from the set, and the set's OTHER members are unchanged (still exactly those five, unless `0yrtne` has landed first).
  - ALSO BE HONEST ABOUT WHAT ENFORCES THIS TODAY, because the original plan's safety argument rested on a gate that does not run. `tests/test_command_surface_declarations.py` and `tests/test_cli_conformance_matrix.py` were BOTH deleted in `19313eed`, the same commit that removed the upgrade-test file. The CI job that names them still exists (`.github/workflows/tests.yml`, "Run the output-conformance harness") and is VACUOUS: all three files it lists are absent, so pytest collects nothing and the step exits 0. Verified at review. So an undeclared leaf added today fails NOTHING. Do not repair that CI step or restore those two files here (out of scope, and `0yrtne` owns the whole-CLI test); just do not rely on a gate that is not running, and make V-05 check the leaf set directly.
  - Execution state: pending

### Task group 3: verification

- [ ] E-06 Run the bare suite (`python3 -m pytest`, no added flags) and paste the actual summary line.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: 0 failed, and any failure named as pre-existing with evidence from the base commit or as new.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A parser leaf SHOULD carry a `CommandDeclaration`, but nothing enforces it today: both `tests/test_command_surface_declarations.py` and `tests/test_cli_conformance_matrix.py` were deleted in `19313eed`, and the CI step naming them collects nothing and exits 0. Pending plan `0yrtne` (Set `cmdsurf`) restores the whole-CLI test and declares the five `oc profile` leaves.
- `find_undeclared_leaves` is NOT empty at baseline (five entries), so a plan may only assert the delta it owns. `tests/test_prompts_new.py` sets the precedent explicitly, with a comment that the suite-wide test "is RED at baseline for other verbs" and an assertion scoped to its own leaf.
- The graduation shape is established by `tools/pwatch.py` (35 lines over a 1051-line package module): add the repo root to `sys.path`, import the package module, RE-EXPORT every non-dunder attribute, delegate `main`.
- Only `agent_workflows` is packaged (`pyproject.toml` `packages = ["agent_workflows"]`), so nothing under `tools/` reaches an installed user. That, not tidiness, is why graduation is what makes the harness available to the end users the source item names.
- The restored tests reach internals via `load_module("aw_upgrade_test", TOOL)` and call many private helpers off it, which is why the shim's attribute re-export is a correctness requirement rather than a nicety.

## Findings

F-1 through F-3 were measured by the author at HEAD `0c2e7970` and all three reproduce at review HEAD `b6155ed0`. F-4 through F-9 were measured at `/plan-review` (2026-09-25), several by RESTORING the deleted file and running it rather than by reading it.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | tests | The four safety invariants are untested since `19313eed`. | `git log --diff-filter=D -- tests/test_aw_upgrade_test.py` -> `19313eed` |
| F-2 | INFO | tests | The restored invariant tests still pass against today's tool. | run in place from `tests/`: `13 passed` |
| F-3 | LOW | cli | No `aw upgrade-test` command exists. | `python3 -m agent_workflows upgrade-test` -> invalid choice |
| F-4 | MEDIUM | the deleted test file | THE WHOLE FILE PASSES, NOT JUST THE SAFETY SUBSET, so the plan's proposal to drop 24 of 37 tests discards working coverage rather than dead weight. Restored verbatim and run at review: `37 passed in 2.52s`; `-k SafetyInvariant` -> `13 passed, 24 deselected`. All four helpers it imports from `tests/support.py` still exist. | two pytest runs at review on the file recovered from `19313eed^` |
| F-5 | HIGH | original E-01 (drop `CliTests`) vs original E-03 (rewrite the output contract) | THE PLAN WOULD DELETE THE ONLY GUARD ON ITS OWN RISKIEST CHANGE, IN THE SAME COMMIT THAT MAKES IT. `CliTests::test_the_json_flag_is_honored_on_either_side_of_the_subcommand` pins a MEASURED regression: a subparser applying its own `--json` default LAST clobbered the value the top-level flag had already set, so `--json list` parsed to False and silently emitted human output to a caller that asked for machine output. The table varies the flag's SIDE and the SUBCOMMAND precisely because the flag is inherited from a shared parent, so the bug was reintroducible one subcommand at a time. E-03 rewrites exactly that contract. Calling these tests "incidental" is what makes the combination dangerous. | read the `JSON_FLAG` table and its five rows' stated reasons in the recovered file |
| F-6 | HIGH | original E-04 vs E-01's restored safety test | E-04 AS WORDED WOULD BREAK A SAFETY TEST THIS PLAN RESTORES, and would also weaken invariant 3. `test_default_sandbox_root_is_computed_not_hardcoded` (a `SafetyInvariantThree` test) asserts `computed.name == SANDBOX_ROOT_NAME` AND `computed.parent.name == "tmp"`; a bare `tempfile.gettempdir()/aw-upgrade-tests` fails the second. More importantly the `tmp/` nesting is a SAFETY MECHANISM: `default_sandbox_root`'s docstring states a sandbox directly under a discovery search root would be found as a managed repo and could be swept into a later `aw install all`, and the extra level is what the immediate-children scan cannot reach. The plan names no constraint and no test interaction. | read the restored test's two assertions and `default_sandbox_root`'s docstring |
| F-7 | LOW | original E-04's justification | THE STATED JUSTIFICATION IS ALREADY SATISFIED, so the item was defended on a false premise while the real defect went unnamed. `aw sanitize --agent` is CLEAN at HEAD (`findings:0`, exit 0), `default_sandbox_root` is already COMPUTED with an `AW_UPGRADE_TEST_ROOT` override, and its docstring says a literal is "exactly what the leak-sanitizer rejects". There is no tracked-file leak and no "fixed maintainer path". The genuine defect is narrower: with no configured search root the function falls back to `Path.home()`, so a fresh non-maintainer gets `~/tmp/aw-upgrade-tests` in their home. Measured here: it resolves under the maintainer's home because this machine HAS a search root. | `aw sanitize --agent` -> clean; driving `default_sandbox_root()` -> a path under `$HOME/tmp`; the function's own fallback branch |
| F-8 | MEDIUM | original E-03's expected outcome | `find_undeclared_leaves` IS NOT EMPTY AND THIS PLAN CANNOT MAKE IT SO, so the acceptance criterion is unsatisfiable as written and an executor would either report a false pass or chase five leaves it does not own. Measured: five entries (`oc profile add|default|list|remove|show`), owned by pending plan `0yrtne`. The correct criterion is a DELTA, which is the precedent `tests/test_prompts_new.py` already sets in a comment saying the suite-wide test "is RED at baseline for other verbs". | `find_undeclared_leaves(_build_parser())` -> 5 entries; `0yrtne`'s Scope-Paths and concern |
| F-9 | MEDIUM | `.github/workflows/tests.yml` output-conformance step | THE GATE THE PLAN'S SAFETY ARGUMENT LEANS ON DOES NOT RUN. The step names three test files, ALL absent (`test_cli_conformance_matrix.py` and `test_cli_quality_gates.py` and `test_cli_output_docs_rollout.py`); pytest collects nothing and the step exits 0. So an undeclared leaf added today fails nothing at all. Recorded rather than fixed: repairing it is out of scope and `0yrtne` owns the whole-CLI test, but the plan must not rely on it. | running the step's exact command at review: no tests collected, `EXIT=0`; `test -f` on all three -> MISSING |

## Proposed changes (ordered, validatable)

1. E-01: restore the deleted test file IN FULL (37 tests), keeping the `--json` and version-precedence guards (F-4, F-5).
2. E-02: decide the shipped sandbox-root default against the two measured constraints (F-6, F-7).
3. E-03: move the logic into the package behind a re-exporting shim, and apply E-02's default.
4. E-04: register `aw upgrade-test`, preserving the `--json` shared-parent mechanism.
5. E-05: declare the seven leaves, asserting only this plan's delta (F-8, F-9).
6. E-06: bare suite.

## Deferred / out of scope (with reason)

- REPAIRING the vacuous output-conformance CI step, and restoring `tests/test_command_surface_declarations.py` / `tests/test_cli_conformance_matrix.py` (F-9).
  - Carrier-Evidence: .aw/records/plans/executed/20260925-cmdsurf-01-0yrtne-declare-the-five-aw-oc-profile-commands-and-restore-the-whol.ipd.md
  - Note: satisfied by plan `0yrtne` (executed 2026-09-25), which restored `tests/test_command_surface_declarations.py` (the whole-CLI declaration test) and repointed the CI output-conformance step at it; the carrier was re-pointed from the now-terminal plan to its evidence so the obligation stays resolvable.
- The SYNTHETIC BASELINE rehearsal (install an old git tag into a throwaway repo, then upgrade it with current code, giving arbitrary version pairs and a CI-runnable upgrade test), which the source item `u27q6g` records as "the other half of this".
  - Carrier: u27q6g
- New rehearsal features of any kind.
  - Carrier-Declined: nothing is outstanding. This plan restores coverage and relocates existing behavior; no feature was identified as missing, so there is no obligation to carry. The source item's own deferred work is carried separately above.

## Scope check

- Over-scope: E-04's original leak justification was traceable to no live defect (F-7: the sanitizer is clean and the default is already computed), and its remedy would have violated a safety invariant (F-6). The item survives with a re-stated concern and its constraints; the false justification is removed.
- Under-scope: four gaps closed. The 24 non-safety tests are now restored rather than discarded (F-4), with the `--json` regression guard called out as load-bearing for E-04 (F-5); the sandbox-root default is now a recorded DECISION with two named constraints instead of a one-line assumption (F-6, OQ-02); the declaration criterion is now a delta rather than an unsatisfiable absolute (F-8); and the fact that nothing currently enforces leaf declarations is stated so the plan does not lean on it (F-9).

## Required tests / validation

- `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q`, expected `37 passed` (the count measured at review; re-derive rather than assume, since E-03 edits one test).
- `python3 -m pytest tests/test_json_and_exitcodes.py tests/test_layout.py -o addopts="" -q`. REQUIRED because E-04 and E-05 touch `cli.py` and `command_surface.py`, which those files exercise; a run scoped to the restored file alone would not.
- The leaf-set delta check in V-05, run directly rather than through CI (F-9: the CI step that would catch it does not run).
- Bare `python3 -m pytest`.

## Spec / documentation sync

No spec describes the rehearsal harness and this plan amends none, so it declares no spec edit and the runners' spec-edit announcement should report none.

The source item `u27q6g` frames graduation as making the harness available to END USERS, and review confirmed the mechanism: `pyproject.toml` declares `packages = ["agent_workflows"]`, so nothing under `tools/` ships in the wheel and an installed user cannot reach the harness today at all. That is the substantive reason E-03 and E-04 matter, and it belongs in the record because it is stronger than "tidier".

If a user-facing docs page enumerates `aw` commands, add `upgrade-test` as part of E-04. Review did not verify that such a page exists; the executor must check and report either the edit or its absence rather than silently skipping it.

## Open questions

### OQ-01: Restore the tests before or after moving the code?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Before, resolved from the maintainer's 2026-09-25 ruling that the safety tests come back: restoring them first means the move in E-03 is checked by the very tests that guard it. REINFORCED at review, and the ordering turned out to be load-bearing in a way the plan did not state: the restored tests CONSTRAIN two later items (a safety test pins the sandbox-root shape E-02/E-03 change, and `CliTests` pins the `--json` mechanism E-04 rewires), so restoring first is what makes those constraints visible before the code moves rather than after.

### OQ-02: What should the shipped default sandbox root be for a user with no configured search root?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP the current derivation when a search root exists, and change ONLY the no-search-root fallback from `Path.home()` to `tempfile.gettempdir()`, preserving the `tmp/<SANDBOX_ROOT_NAME>` shape in both branches. Resolved from repository evidence rather than asked, because the repository fixes both ends of the range. The original E-04 (always use the system temp dir) is REJECTED on two measurements: it FAILS the restored safety assertion `computed.parent.name == "tmp"`, and it discards a real safety property, since `default_sandbox_root`'s docstring records that the extra `tmp/` level exists so a sandbox is not discovered as a managed repo and swept into a later `aw install all` (invariant 3). Doing nothing is also rejected: the source item `u27q6g` item 5 names this as open work, and the fallback genuinely puts sandboxes in a fresh user's HOME. The chosen change is the minimum that satisfies the item, keeps both restored assertions true unchanged, and preserves the invariant-3 nesting. This is REVERSIBLE: the value is one expression behind an env override, and a maintainer who prefers the state root can change it without touching anything else. Note for the executor: if the maintainer instead wants the STATE ROOT (the item's other suggestion), that is a legitimate alternative but it changes the shape the two restored assertions pin, so it must be decided by the human and recorded here before E-03 runs, not chosen mid-edit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the restored file's full class list with the test count per class, and `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` showing `37 passed`. Then paste `-k SafetyInvariant` showing `13 passed, 24 deselected`, which is what proves the 24 non-safety tests are actually PRESENT rather than quietly dropped (the defect F-4 and F-5 exist to prevent). If the count is not 37, name which tests were omitted and why, per item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the decision as written into the item, and paste BOTH constraints demonstrated rather than asserted: the two assertions in `test_default_sandbox_root_is_computed_not_hardcoded` quoted from the restored file, and `default_sandbox_root`'s docstring sentence about a sandbox under a search root being swept into `aw install all`. A decision recorded without its constraints is what F-6 measured going wrong.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff stat; `python3 tools/aw_upgrade_test.py --help` working through the shim; the restored tests passing against the package module; and `python3 -c "from tests.support import load_module; m=load_module('aw_upgrade_test','tools/aw_upgrade_test.py'); print(hasattr(m,'default_sandbox_root'), hasattr(m,'search_roots'))"` printing `True True`, which proves the shim RE-EXPORTS internals rather than only delegating `main` (without that the restored tests cannot reach `uat.<helper>`). Also paste the resolved default with no `AW_UPGRADE_TEST_ROOT` set and with a fake empty config, showing E-02's fallback in effect.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m agent_workflows upgrade-test --help` and one `--help` per subcommand. Then paste the `--json` matrix DRIVEN through the new parser, all five rows of `CliTests::JSON_FLAG`: `--json list`, `list --json`, `--json probe x`, `probe x --json` each yielding True, and `list` yielding the falsy default. This is the regression F-5 names, and a passing `CliTests` on the OLD parser does not prove the NEW registration preserved it, so drive both.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -c "from agent_workflows.command_surface import find_undeclared_leaves; from agent_workflows.cli import _build_parser; print(sorted(find_undeclared_leaves(_build_parser())))"`. Assert the DELTA, not emptiness: none of the seven `upgrade-test` leaves appears, and the remaining members are exactly the five `oc profile` entries measured at review (or fewer, if `0yrtne` landed first, in which case say so). Do NOT paste `[]` as the expected result; F-8 measured that it is unreachable by this plan. Also paste `python3 -m agent_workflows sanitize --agent` exiting 0 with no finding in the new or moved files.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the tests guard the move; restoring them first is what makes the graduation safe, and review measured that this is literally true rather than rhetorical (a restored safety test pins the sandbox-root shape E-02/E-03 change, and the restored `CliTests` pins the `--json` mechanism E-04 rewires). Six items, one concern: restore the coverage, then relocate and register the harness under it.

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING, and it is more than the title implies. FIRST, a new public `aw` command: the harness becomes shipped surface (`pyproject.toml` packages only `agent_workflows`, so today no installed user can reach it), which means its behavior becomes something users depend on and the toolkit supports. SECOND, a change to where sandboxes are created by default for anyone with no configured search root (OQ-02), on a tool whose job is to COPY REPOSITORIES and DELETE DIRECTORIES; that is why the sandbox root is treated here as a safety decision rather than a path preference. THIRD, roughly 1,800 lines of test file returning to the default suite. The maintainer may legitimately prefer the state root over a temp dir in OQ-02; that choice changes assertions two restored tests make, so it must be decided before E-03 runs rather than mid-edit.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `tests/test_aw_upgrade_test.py` is restored whole, with exactly one edit (repointing the `read_text` assertion in E-03); `tools/aw_upgrade_test.py` is reduced to a re-exporting shim; `agent_workflows/upgrade_rehearsal.py` is new and receives the moved logic plus E-02's one-line default change; within `cli.py` only the new `upgrade-test` parser registration and its `main` dispatch; within `command_surface.py` only the seven added `CommandDeclaration`s. No other file is expected to change. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

EXPLICITLY NOT IN SCOPE, each recorded in Deferred with a carrier: repairing the vacuous output-conformance CI step or restoring the two deleted declaration tests (carried by plan `0yrtne`, which owns the whole-CLI test and the five `oc profile` leaves); the synthetic-baseline rehearsal (carried by item `u27q6g`); and any new rehearsal feature.

CONCURRENCY NOTE, not a stop condition: pending plan `0yrtne` also edits `cli.py` and `command_surface.py`. The runners isolate each item in its own worktree and return changes through the merge-and-revalidate gate, so overlap is not a hazard and this plan declares no `Item-Dependencies` edge on it. The one visible coupling is V-05's expected leaf set, which legitimately differs depending on whether `0yrtne` landed first; V-05 says to report which.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Two claims in this plan are specifically easy to fake and must not be: V-01's `13 passed, 24 deselected` split, which is the evidence that the non-safety tests were not quietly dropped, and V-04's five-row `--json` matrix driven through the NEW parser, since a passing `CliTests` against the old parser proves nothing about the new registration.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the restored file does NOT reach 37 passed at E-01, stop and report which tests fail rather than deleting them to go green, because a failure there is evidence the tool changed since `19313eed` and that is a finding about the tool; if the repository's standard output-mode helper requires a concrete `--json` default that reintroduces the clobber `CliTests` pins, stop and report the conflict rather than relaxing the restored test; if E-02's chosen default cannot satisfy both restored assertions and the invariant-3 nesting, stop and put the choice to the maintainer rather than weakening an assertion.

Commit through `aw commit <plan> -- <paths>`, path-scoped, never `git add -A`, never push. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which the RUNNER owns when it executes this plan in a lane and which the executor otherwise performs with `aw ipd finalize`, never with a raw `git mv`. Then set backlog item `u27q6g` `done` with `--evidence` citing the executed plan ONLY if its deferred synthetic-baseline half is separately carried; otherwise leave it open for that half and say so. It carries no `- Blocks-Release:`, so no gate handoff is required.
