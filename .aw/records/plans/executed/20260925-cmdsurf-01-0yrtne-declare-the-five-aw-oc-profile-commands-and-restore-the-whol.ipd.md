# IPD: Declare the five aw oc profile commands and restore the whole-CLI declaration test

- Date: 2026-09-25
- Kind: child
- Concern: The five `aw oc profile` leaves (`add`, `default`, `list`, `remove`, `show`) exist in the parser but have no `CommandDeclaration` in `command_surface.py`, so they carry no declared output-mode, mutation-gate or exit contract. The one test that proved every parser leaf is declared (`tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`) was deleted by the suite trim `19313eed`, so nothing catches this or the next undeclared command.
- Scope: IN: five declarations in `agent_workflows/command_surface.py`; one fast (not `slow`) behavior test asserting `command_surface.find_undeclared_leaves(cli._build_parser())` is empty; repair the CI step whose three named files are all absent, because leaving it green is what let this regression ship (review finding PR-705); repoint the stale comments and the stale `CONTRIBUTING.md` sentence that still name the deleted `test_cli_conformance_matrix.py`. OUT: changing `oc profile` behavior; restoring any deleted test other than the one whole-CLI declaration test; restoring `test_cli_quality_gates.py` / `test_cli_output_docs_rollout.py` (their goldens are a separate body of work, carried below).
- Scope-Paths: agent_workflows/command_surface.py, agent_workflows/cli.py, tests/test_command_surface_declarations.py, .github/workflows/tests.yml, CONTRIBUTING.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Set: cmdsurf
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 0yrtne
- From-Backlog: 4fe3al
- Blocks-Release: next

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 0yrtne verified (set cmdsurf, recovered after the parenthesized-actor refusal fixed in b47d7816).
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 8 findings PR-701..PR-708 all FIXED, 4 decisions D-1..D-4 recorded; review record written; added E-04/E-05 (repair the CI step, repoint the stale citations) and V-04..V-06; corrected the sibling plan's exit-0 claim to the measured exit 5; aw ipd lint --phase review-finalize conforming
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 4fe3al. Verified at HEAD that the five leaves are still undeclared (`find_undeclared_leaves(_build_parser())` returns exactly them) and that the guard test was deleted in 19313eed. Maintainer ruled 2026-09-25 to restore the whole-CLI declaration test (it checks behavior, not source).

## Goal

Every `aw` command has a declared output and exit contract again, and a fast test fails the moment a new parser leaf ships without one, in the bare suite AND in the CI job whose name claims to gate it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: declarations

- [x] E-01 Add `CommandDeclaration` entries for `oc profile list` and `oc profile show` in `command_surface.py` as `command_class="read"`. Model the OUTPUT fields on the nearest true analogue, NOT on `oc update-models` (which the original item named and which is a `mutation`, so it is the wrong model for a read leaf): both handlers call `select_output` then `get_renderer(...).emit` through `cli._oc_profile_out`, which is the `renderer_boundary` path. Use `agent_record_kind="result"`, `mutation_gate="none"`, `human_recipe="table"` for `list` (`cli._oc_profile_list` prints `term.format_table`) and `"detail"` for `show` (`cli._oc_profile_show` prints `wiz.preview_lines`).
  - `empty_error_renderer` IS DECIDED BY MEASUREMENT, NOT BY CLASS, and this is the one field an executor is likely to get wrong. `cli._oc_profile_list` calls `term.empty_result` on the no-profiles path (quote: `summary="no runner profiles configured"`), which is exactly what `shared_empty_result` denotes, so `list` declares `shared_empty_result` and `show` declares `renderer_boundary` (it has no empty state: an unknown name raises `ProfileNotFoundError` and exits 2). The restored test's deleted sibling `test_empty_error_renderer_classification_consistency` enforced an ALLOWLIST of `shared_empty_result` queries by NAME and is NOT restored by this plan, so nothing will check this for you.
  - `legacy_flags`: read them from the parser, do not guess, and EXCLUDE the four argparse/presentation flags no declaration in the inventory carries. Measured: `oc profile list` registers `-h/--help/--no-color/--color/--agent/--json`, and across all 141 existing declarations `-h`, `--help` and `--color` appear ZERO times while `--no-color` appears only on bare `aw`. So the correct value for both leaves is `("--agent", "--json")`.
  - Depends on: none
  - Expected outcome: both leaves disappear from `find_undeclared_leaves(_build_parser())`.
  - Execution state: performed

- [x] E-02 Add `CommandDeclaration` entries for `oc profile add`, `oc profile remove` and `oc profile default` as `command_class="mutation"`, `human_recipe="status"`, `agent_record_kind="result"`, `empty_error_renderer="renderer_boundary"` (none of the three has an empty state).
  - `mutation_gate` PER LEAF, measured from the handlers rather than assumed uniform, because these three genuinely differ and the vocabulary has a value for each: `add` is `"confirmation"` (`cli._oc_profile_add`'s noninteractive form REFUSES without `--yes`, quote: `"--yes is required for the noninteractive form"`, and the interactive form is the wizard's own confirmation); `remove` is `"confirmation"` (`cli._oc_profile_remove` refuses without a TTY unless `--yes`, quote: `"refusing to remove {name!r} without a TTY"`, and otherwise calls `cli._confirm`); `default` is `"none"` (`cli._oc_profile_default` takes no `--yes`, prompts for nothing, and writes immediately). Do NOT declare all three `"confirmation"` for symmetry: `mutation_gate` is a claim about what protects the write, and `default` has no such protection.
  - `legacy_flags` from the parser, minus the four presentation flags named in E-01. Measured: `add` -> `("--model", "--variant", "--oc-agent", "--replace", "--yes", "--set-default", "--agent", "--json")`; `remove` -> `("--clear-default", "--replacement", "--yes", "--agent", "--json")`; `default` -> `("--clear", "--agent", "--json")`.
  - `exit_contract` IS `(0, 1, 2)` FOR `add` AND `remove`, AND `(0, 2)` FOR `default`, and the `1` is not boilerplate: both `add` and `remove` have a real exit-1 path that a naive `(0, 2)` would misdeclare. Measured by driving the CLI with a temp `XDG_CONFIG_HOME`: the declined wizard returns 1 (`cli._oc_profile_add`, quote: `return 0 if result.saved else 1`) and a declined removal returns 1 (`cli._oc_profile_remove`, quote: `print("Nothing was changed.")`). `default` has no exit-1 path (measured: set -> 0, neither-name-nor-`--clear` -> 2). 26 of the 68 existing mutation declarations legitimately omit `1`, so neither shape is automatic; measure, then declare.
  - Depends on: E-01
  - Expected outcome: `find_undeclared_leaves(_build_parser())` returns an empty set.
  - Execution state: performed

### Task group 2: guard test

- [x] E-03 Recreate `tests/test_command_surface_declarations.py` with ONE fast test (no `slow` mark) asserting `find_undeclared_leaves(cli._build_parser()) == set()`, with a failure message that lists the undeclared leaves. Measured: importing `cli`, building the parser and running the check takes about 0.27s end to end, so it belongs in the default subset, unlike the deleted `slow`-marked version.
  - RESTORE ONLY THIS ONE TEST, and know what the other thirteen in the deleted file were, so the narrowness is a decision rather than an oversight. The deleted file held 14 tests; the other 13 (`test_empty_error_renderer_classification_consistency`, the alias byte-equivalence trio, the conflicting-format-flag set, the standalone-script classification, the field-validity sweep) are NOT restored here. That is the maintainer's ruling on this plan's scope, and the cost is recorded in Deferred with a carrier: the classification rule that would have checked E-01's `empty_error_renderer` choice is among them.
  - Depends on: E-02
  - Expected outcome: the test passes, and FAILS when any one of the five new declarations is removed.
  - Execution state: performed

### Task group 3: make the gate actually run

- [x] E-04 Repair the `output-conformance` CI job so it runs the restored test instead of collecting nothing. Locate it by its step name in `.github/workflows/tests.yml` (quote: `Run the output-conformance harness (E-01 matrix + E-02 gates + E-03 docs)`, in the job named `output-conformance`, around line 223). All three files that step names are ABSENT, so pytest exits 5 (`NO_TESTS_COLLECTED`). Replace the three-file list with `tests/test_command_surface_declarations.py` and add `--strict-markers`-independent protection against the same failure recurring: pass `-p no:cacheprovider` is NOT the fix; the fix is that the step must name only files that exist, and a missing file must fail rather than pass.
  - READ THE MEASUREMENT BEFORE CHANGING THE JOB NAME OR ITS MATRIX, because the honest diagnosis is narrower than "the gate is vacuous" and a sibling plan states the broader version. Measured three times at HEAD: the step's exact command exits **5**, not 0. Exit 5 is NONZERO, so the STEP FAILS and the job is red; it is not silently green. What is actually true, and is the real defect, is that the job was SUCCEEDING on every run before `19313eed` deleted the files (verified: run 35956980850, all six Python versions `success` on that step) and `19313eed` has not yet been exercised by a `tests.yml` run, so the breakage is real but UNOBSERVED rather than invisible. Do not repeat the claim that the step exits 0 and passes; it does not.
  - DO NOT RE-ADD the two other files to the step. `test_cli_quality_gates.py` and `test_cli_output_docs_rollout.py` depend on reviewed golden fixtures and are a separate body of work; naming a file this plan does not restore is what created this failure mode in the first place.
  - Depends on: E-03
  - Expected outcome: the step's command collects and passes the restored test; a deliberately misspelled filename in that step makes it FAIL rather than pass.
  - Execution state: performed

- [x] E-05 Repoint the five stale citations of the deleted `tests/test_cli_conformance_matrix.py`. FIND THEM BY GREP, not by line number, since E-01..E-04 shift offsets in these same files: `grep -rn --include='*.py' --include='*.md' test_cli_conformance_matrix .`. At review they sat in `cli._ViewerOrLeafSubParsersAction`'s docstring, the two `runs_sub` registration comments (Order 08's and Order 09's), `command_surface.COMMAND_INVENTORY`'s `runs analyze` comment (quote: `is asserted EMPTY by`) and its `oc integrate` comment (quote: `ALIAS_SAFE` DICT), plus `CONTRIBUTING.md`'s "Adding a CLI command" checklist (quote: `the conformance harness in`), which tells a contributor that an undeclared leaf "fails CI" via a file that does not exist. `agent_workflows.lane_containment` cites the RESTORED test by name (quote: `test_command_surface_declarations::test_zero_undeclared_parser_leaves`) and so becomes true again rather than stale; verify it, do not rewrite it. Where a comment cites a capability the restored test does NOT have (the `ALIAS_SAFE` live-equivalence dict), say the citation is to a DELETED test rather than silently redirecting it to one that cannot check that thing.
  - Depends on: E-03
  - Expected outcome: `grep -rn --include='*.py' --include='*.md' --include='*.yml' test_cli_conformance_matrix .` returns only intentional historical mentions (`CHANGELOG.md`), and every remaining citation names a file that exists.
  - Execution state: performed

- [x] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-04, E-05
  - Expected outcome: suite green; paste the summary line.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Every parser leaf needs a `CommandDeclaration` (`command_surface.CommandDeclaration`); `command_surface.find_undeclared_leaves` is the shipped detector. `CONTRIBUTING.md`'s "Adding a CLI command: the output-contract checklist" states the obligation for contributors.
- The maintainer's standing rule: tests that pin code STRUCTURE are removed. This test checks a behavioral property of the built parser (every reachable command has a declared contract), which is why it is restored and not treated as a structure pin.
- `command_surface.discover_parser_leaves` de-duplicates argparse ALIASES by object identity (its own docstring: "ALIASES ARE EXCLUDED"), so the `profiles`/`ls`/`rm` alias spellings do NOT surface as separate leaves and must NOT be declared. Measured: the undeclared set is exactly five entries, not eight.
- `command_surface.COMMAND_INVENTORY` declares LEAVES only; a family ROOT such as `oc profile` is never a leaf and must not be declared, or it registers as declaration/parser drift (its `runs list` comment: "a family ROOT is never a leaf"). Measured: the only declared-but-absent entry today is `prompts set`.
- `command_class` is not a label: `tests.conformance_matrix.required_scenarios` DERIVES each leaf's required conformance coverage from it, and a `mutation` demands a `success_preview` scenario a `read` does not. The harness that consumed it is deleted, so that derivation is currently inert, but the declaration is still the normative statement and a wrong class is a wrong contract.
- Declarations carry no `-h`/`--help`/`--color` in `legacy_flags`, and `--no-color` only on bare `aw` (measured across all 141 declarations). `legacy_flags` records the verb's OWN flag surface, not the shared presentation parent.

## Findings

All measured at HEAD `0c2e7970` unless stated. F-4 through F-8 were added at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `command_surface` | The five `oc profile` leaves are undeclared. | `find_undeclared_leaves(_build_parser())` -> `['oc profile add', 'oc profile default', 'oc profile list', 'oc profile remove', 'oc profile show']` |
| F-2 | MED | tests | The guard test was deleted, and no remaining test checks the whole CLI; only narrowed checks exist (`test_host_capability_extension.py`, `test_prompts_new.py`). | `git log --diff-filter=D -- tests/test_command_surface_declarations.py` -> `19313eed` |
| F-3 | LOW | comments | Comments in `cli.py` and `command_surface.py` still cite the deleted `test_cli_conformance_matrix.py`. | `grep -rn test_cli_conformance_matrix agent_workflows/` |
| F-4 | HIGH | the `output-conformance` job in `.github/workflows/tests.yml` | THE CI JOB THAT IS SUPPOSED TO CATCH AN UNDECLARED LEAF NAMES THREE FILES THAT NO LONGER EXIST, and leaving it is what lets the next undeclared leaf ship even after this plan lands. The precise behavior matters and is NOT what a sibling plan claims: the step exits **5** (`NO_TESTS_COLLECTED`), which is nonzero, so the step FAILS. It is broken-and-unobserved, not silently-green: it was `success` on all six Python versions in the last recorded run, and `19313eed` (which deleted the files) has not yet been exercised by a `tests.yml` run. | the step's exact command run 3 times -> `EXIT=5` each; `pytest.ExitCode.NO_TESTS_COLLECTED == 5`; `gh run view 35956980850` -> that step `success` on 3.9-3.14; `19313eed` dated 2026-09-24 17:13, after the newest recorded run (2026-09-24 04:45) |
| F-5 | MED | original E-01 | `oc update-models` IS THE WRONG MODEL FOR A READ LEAF: it is declared `command_class="mutation"`. Following it would copy a mutation's output shape onto `list`/`show`. | `get_declaration("oc update-models").command_class` -> `mutation` |
| F-6 | MED | original E-02 | `mutation_gate` IS NOT UNIFORM ACROSS THE THREE WRITERS, so "matching how each leaf actually confirms" needed the measurement rather than the instruction. `add` and `remove` refuse without `--yes`/TTY; `default` takes no `--yes`, prompts for nothing, and writes immediately. | `cli._oc_profile_add` (quote: `--yes is required for the noninteractive form`); `cli._oc_profile_remove` (quote: `refusing to remove`, then `cli._confirm`); `cli._oc_profile_default` (no confirmation path at all) |
| F-7 | MED | original E-01/E-02 (`legacy_flags`, `exit_contract`) | TWO FIELDS THE ITEMS DELEGATED TO "read them from the parser" HAVE ANSWERS THE PARSER ALONE DOES NOT GIVE. (a) The parser reports `-h/--help/--no-color/--color` on every leaf, and no declaration in the inventory carries them, so a literal read produces four wrong flags per leaf. (b) `exit_contract` is not in the parser at all: `add` and `remove` each have a real exit-1 path (a declined wizard, a declined removal) that a default `(0, 2)` would misdeclare, while `default` genuinely has none. | across 141 declarations: `-h`/`--help`/`--color` appear 0 times, `--no-color` only on bare `aw`; driven with a temp `XDG_CONFIG_HOME`: `show nope` -> 2, `default` (no args) -> 2, `remove` without `--yes` -> 2; `cli._oc_profile_add` and `cli._oc_profile_remove` each return 1 on a decline |
| F-8 | LOW | original E-03 scope | THE RESTORED FILE CARRIES 1 OF THE DELETED FILE'S 14 TESTS, and one of the 13 dropped (`test_empty_error_renderer_classification_consistency`) is precisely what would have checked E-01's `empty_error_renderer` choice. Narrowness is correct per the maintainer's ruling, but it must be recorded with its cost rather than left implicit. | `git show 19313eed^:tests/test_command_surface_declarations.py` -> 14 `def test_`, 285 lines |

## Proposed changes (ordered, validatable)

1. E-01: declare the two read leaves.
2. E-02: declare the three mutation leaves.
3. E-03: restore the whole-CLI guard as a fast test.
4. E-04: repair the CI step so the guard actually runs.
5. E-05: repoint the six stale citations.
6. E-06: bare suite.

## Deferred / out of scope (with reason)

- The OTHER 13 tests in the deleted `tests/test_command_surface_declarations.py`, notably `test_empty_error_renderer_classification_consistency` (which would have checked E-01's `empty_error_renderer` choice), the three alias byte-equivalence tests, and the conflicting-format-flag set (F-8). The maintainer ruled this plan restores the whole-CLI declaration test only.
  - Carrier-Declined: nothing is outstanding that this plan may claim. These are a separate restoration decision the maintainer has not made, and filing a carrier would assert an obligation nobody has accepted. Recorded here so the narrowness is visible and can be revisited.
- `tests/test_cli_quality_gates.py` and `tests/test_cli_output_docs_rollout.py`, the other two files the CI step named. They depend on reviewed golden fixtures and are a substantially larger restoration than this plan's one test.
  - Carrier-Declined: nothing is outstanding that this plan may claim, for the same reason as above. E-04 removes them from the CI step rather than leaving the step naming files nothing restores, so the step's claim becomes true instead of aspirational.
- Re-classifying `runs resume` from `mutation` to `read`, an existing misdeclaration in the same registry this plan edits.
  - Carrier: cldbus

## Scope check

- Over-scope: none. E-04 and E-05 were ADDED at review and are in scope on the plan's own terms: a plan whose goal is "a fast test fails the moment a new parser leaf ships without one" does not achieve that goal while the CI job meant to run it names three absent files, and the stale citations point a contributor at a test that does not exist.
- Under-scope: the other 12 tests deleted by `19313eed` from this file, and the two sibling harness files, are not restored; each needs its own case, and this plan restores only the one the maintainer ruled on. Both are recorded in Deferred with their cost stated.

## Required tests / validation

- `python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q` plus the removal mutation in V-03.
- The CI step's exact command, run locally, plus the misspelled-filename mutation in V-04.
- Bare `python3 -m pytest`.

## Spec / documentation sync

- No spec describes the `oc profile` leaves' declarations; the declaration registry is itself the contract, so no `.spec.md` is touched and none is declared in `Scope-Paths`.
- `CONTRIBUTING.md`'s "Adding a CLI command" checklist DOES describe the enforcement and is currently false (quote: `the conformance harness in`, naming a deleted file), so E-05 corrects it. That is documentation sync, not a spec amendment.

## Open questions

### OQ-01: Should the restored test be marked `slow` like the deleted one?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No, resolved from measurement: the check takes about 0.27s end to end (importing `cli`, building the parser, running `find_undeclared_leaves`), so it belongs in the default subset where it actually runs. The deleted version being `slow` is exactly why the regression went unnoticed.

### OQ-02: Should this plan repair the CI job, given that the job is not in the original scope?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: Yes, resolved at review from the plan's own stated goal rather than from preference. The Goal says "a fast test fails the moment a new parser leaf ships without one"; measured, the `output-conformance` step names three files that do not exist and so runs no test at all (exit 5), and the bare suite is the only thing that would run the restored test. Leaving the step is not neutral: it names `test_cli_conformance_matrix.py`, which this plan does not restore, so the step would stay broken while appearing to be the gate. Repair is two lines in one file, is verifiable locally by running the step's own command, and is the difference between the plan achieving its goal and only half achieving it. Recorded as decision D-3 in the review record. If the maintainer prefers the CI change to ride separately, E-04 can be dropped without affecting E-01..E-03, and this plan then delivers the test but not the gate that runs it in CI.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `python3 -c "from agent_workflows.cli import _build_parser; from agent_workflows.command_surface import find_undeclared_leaves; print(sorted(find_undeclared_leaves(_build_parser())))"` after this item, showing `list`/`show` absent; paste the two new declarations.
  - ALSO REQUIRED, because these are the two fields nothing will check for you (F-8): paste the line in `_oc_profile_list` that calls `term.empty_result` as the basis for `list` declaring `shared_empty_result`, and state in one line why `show` declares `renderer_boundary`. Paste `python3 -c "...get_declaration('oc profile list').legacy_flags..."` for both leaves and confirm no `-h`/`--help`/`--color`/`--no-color` appears.
  - Observed evidence: Verified empty find_undeclared_leaves; declarations added for oc profile list/show; term.empty_result cited; legacy flags confirmed without presentation flags.
    ```
    $ python3 -c "from agent_workflows.cli import _build_parser; from agent_workflows.command_surface import find_undeclared_leaves; print(sorted(find_undeclared_leaves(_build_parser())))"
    []
    ```
    New declarations in `agent_workflows/command_surface.py`:
    ```python
    CommandDeclaration(
        command="oc profile list",
        command_class="read",
        human_recipe="table",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="shared_empty_result",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 2),
    ),
    CommandDeclaration(
        command="oc profile show",
        command_class="read",
        human_recipe="detail",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 2),
    ),
    ```
    Basis for `empty_error_renderer`:
    Line in `_oc_profile_list` (`agent_workflows/cli.py:12351`):
    `term.empty_result(summary="no runner profiles configured", next_action=NextAction(command="aw oc profile add gem", description="create one with the model selector"))`
    Why `show` declares `renderer_boundary`: `show` has no empty state because an unknown profile name raises `ProfileNotFoundError` and exits 2 with the known-name list via `_oc_profile_error`.
    Legacy flags confirmation:
    ```
    $ python3 -c "from agent_workflows.command_surface import get_declaration; print('list:', get_declaration('oc profile list').legacy_flags); print('show:', get_declaration('oc profile show').legacy_flags)"
    list: ('--agent', '--json')
    show: ('--agent', '--json')
    ```
    Confirmed: no `-h`, `--help`, `--color`, or `--no-color` appears in either declaration.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the same one-liner printing `[]`; paste the three declarations and, for each, one line naming how its mutation gate was determined (the handler symbol and line read).
  - ALSO REQUIRED: `default` must be declared `mutation_gate="none"` while `add`/`remove` are `"confirmation"`; if all three came out the same, say why and cite the handler, because the measurement at review says they differ (F-6). DRIVE the exit contracts rather than asserting them: with a throwaway `XDG_CONFIG_HOME`, paste the observed exit code for a declined removal (expect 1) and for `oc profile default` with neither a name nor `--clear` (expect 2), and confirm each declared `exit_contract` contains exactly the codes observed plus the argparse-usage 2.
  - Observed evidence: Verified empty find_undeclared_leaves; declarations added for oc profile add/remove/default; mutation gates and exit contracts driven and verified.
    ```
    $ python3 -c "from agent_workflows.cli import _build_parser; from agent_workflows.command_surface import find_undeclared_leaves; print(sorted(find_undeclared_leaves(_build_parser())))"
    []
    ```
    Three declarations in `agent_workflows/command_surface.py`:
    ```python
    CommandDeclaration(
        command="oc profile add",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--model",
            "--variant",
            "--oc-agent",
            "--replace",
            "--yes",
            "--set-default",
            "--agent",
            "--json",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="oc profile remove",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="confirmation",
        empty_error_renderer="renderer_boundary",
        legacy_flags=(
            "--clear-default",
            "--replacement",
            "--yes",
            "--agent",
            "--json",
        ),
        exit_contract=(0, 1, 2),
    ),
    CommandDeclaration(
        command="oc profile default",
        command_class="mutation",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--clear", "--agent", "--json"),
        exit_contract=(0, 2),
    ),
    ```
    Mutation gate determination:
    - `add`: `cli._oc_profile_add` line 12249 (`--yes is required for the noninteractive form`) and line 12282 (`wiz.run_add_wizard` interactive prompt/confirmation).
    - `remove`: `cli._oc_profile_remove` line 12423 (`refusing to remove {name!r} without a TTY: pass --yes to confirm`) and line 12431 (`_confirm(term, f"Remove profile {name!r}?", False)`).
    - `default`: `cli._oc_profile_default` lines 12456-12488 takes no `--yes`, prompts for nothing, and writes directly via `rp.set_default_runner_profile`.
    Driven exit contracts with temp `XDG_CONFIG_HOME`:
    - Declined removal (driven via pty answering 'n'):
      Observed stdout: `Remove profile 'p1'? [y/N] Nothing was changed.`
      Observed exit code: 1
    - `oc profile default` without name or `--clear`:
      Observed stderr: `error: name a profile, or pass --clear to clear the default.`
      Observed exit code: 2
    Confirmed: declared exit contracts contain observed codes plus argparse usage (2): `add` (0, 1, 2), `remove` (0, 1, 2), `default` (0, 2).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q` passing; then remove the `oc profile show` declaration IN THE WORKTREE, paste the same run FAILING with `oc profile show` named in the message, and restore it.
  - Observed evidence: Test passes in 0.37s; mutation test with oc profile show removed fails as expected; passes again in 0.26s upon restoration.
    Passing test run:
    ```
    $ python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q
    .                                                                        [100%]
    1 passed in 0.37s
    ```
    Mutation failure with `oc profile show` removed from worktree:
    ```
    $ python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q
    F                                                                        [100%]
    =================================== FAILURES ===================================
    ______ CommandSurfaceDeclarationsTests.test_zero_undeclared_parser_leaves ______

    self = <tests.test_command_surface_declarations.CommandSurfaceDeclarationsTests testMethod=test_zero_undeclared_parser_leaves>

        def test_zero_undeclared_parser_leaves(self):
            """Require 0 undeclared leaves across _build_parser()."""
            parser = cli._build_parser()
            undeclared = find_undeclared_leaves(parser)
    >       self.assertEqual(
                undeclared,
                set(),
                f"Found undeclared parser leaves: {sorted(undeclared)}",
            )
    E       AssertionError: Items in the first set but not the second:
    E       'oc profile show' : Found undeclared parser leaves: ['oc profile show']

    tests/test_command_surface_declarations.py:24: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
    1 failed in 0.31s
    ```
    Restored `oc profile show` declaration and re-verified passing:
    ```
    $ python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -q
    .                                                                        [100%]
    1 passed in 0.26s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `output-conformance` step's exact command as it now reads in `tests.yml`, run locally, showing it COLLECTS AND PASSES the restored test (a `1 passed` line, not `no tests ran`). Then deliberately misspell the filename in the step, paste the run showing it FAILS, and restore it. State the exit code in both cases.
  - Do NOT accept `exit 0` as evidence the old step was broken: it exits 5. The claim to demonstrate is that the step now runs a real test, not that it changed from passing to failing.
  - Observed evidence: Exact command from tests.yml passes locally with 1 passed (exit 0); misspelled filename fails with no tests ran (exit 5).
    Exact command from `tests.yml` run locally:
    ```
    $ python3 -m pytest tests/test_command_surface_declarations.py
    .                                                                        [100%]
    1 passed in 2.34s
    ```
    Exit code: 0
    Deliberately misspelled filename mutation:
    ```
    $ python3 -m pytest tests/test_command_surface_declarations_misspelled.py
    no tests ran in 1.86s
    ```
    Exit code: 5
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `grep -rn --include='*.py' --include='*.md' --include='*.yml' test_cli_conformance_matrix .` showing only the intentional `CHANGELOG.md` history mention remains, and paste the rewritten `CONTRIBUTING.md` sentence. For the `command_surface.py:1793` `ALIAS_SAFE` comment, paste the new text and confirm it does not claim the restored test performs alias equivalence (it does not).
  - Observed evidence: Grep confirms all active citations repointed to test_command_surface_declarations.py; CONTRIBUTING.md checklist updated; ALIAS_SAFE comment clarifies deleted test capability.
    Grep output across repository:
    ```
    $ grep -rn --include='*.py' --include='*.md' --include='*.yml' test_cli_conformance_matrix .
    ./tests/conformance_matrix.py:6:- ``test_cli_conformance_matrix.py`` (E-01): enumerates EVERY parser leaf from
    ./CHANGELOG.md:58:- Added: a generated output-conformance harness (`tests/test_cli_conformance_matrix.py`, `tests/test_cli_quality_gates.py`, `tests/conformance_matrix.py`) that fails CI on any undeclared parser leaf and gates schema validity, human/agent fact parity, ANSI-free agent streams, deterministic bytes with reviewed goldens, ASCII-glyph accessibility fallback, truncation accounting, and per-leaf byte/token budgets.
    ```
    (Note: `tests/conformance_matrix.py:6` is the module docstring of the shared Order 05 harness retained for historical design reference and not in Scope-Paths; all 5 active stale citations in `cli.py`, `command_surface.py`, and `CONTRIBUTING.md` were repointed to existing files).
    Rewritten `CONTRIBUTING.md` sentence:
    ```markdown
    Every leaf command MUST honor the dual-audience output contract. Before you land a new leaf,
    walk this list (the declaration guard in `tests/test_command_surface_declarations.py` enforces it,
    and an undeclared leaf fails CI):
    ```
    Rewritten `command_surface.py:1793` `ALIAS_SAFE` comment:
    ```python
    # DELIBERATELY NOT IN AN ALIAS_SAFE DICT (a live-equivalence capability of the deleted
    # conformance harness, not the restored declaration guard): that live equivalence gate
    # drove READ-ONLY leaves, and this verb merges to main. The thin-alias proof is the rewrite
    # function plus the diff, not that gate.
    ```
    Confirmed: comment clearly states the capability belonged to the deleted conformance harness and does not claim the restored declaration guard performs alias equivalence.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence: Bare python3 -m pytest passed with 2209 passed, 1 skipped, 3 warnings in 39.04s.
    ```
    $ python3 -m pytest
    2209 passed, 1 skipped, 3 warnings in 39.04s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, in three stages that only work together: declare the leaves, restore the test that proves every leaf is declared, and make the CI job actually run it. Splitting the CI repair out would ship a guard that runs only in the bare suite while the job named "fail-closed" still names three absent files.

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. FIRST, five entries in the normative command-surface inventory. These are contract DECLARATIONS, not behavior: no `oc profile` verb changes what it does, but `command_class` is what a future conformance harness derives required coverage from (`tests/conformance_matrix.py:76-98`), so a wrong class would demand the wrong coverage later. SECOND, a change to a CI job called "fail-closed" (E-04), which review ADDED to scope and which the maintainer may legitimately want separately; OQ-02 records the reasoning and says E-04 can be dropped without touching E-01..E-03. THIRD, a deliberately NARROW restoration: 1 of the deleted file's 14 tests. The 13 not restored are listed in Deferred, and one of them is the only mechanical check on a field E-01 sets by hand.

Scope fence (a DECLARATION for reconciliation, not a stop directive): within `command_surface.py` only the five added `CommandDeclaration`s and the one stale comment at `:1793`/`:950`; within `cli.py` only the three stale comments at `:725`, `:2521`, `:2705` and NO parser or handler change; `tests/test_command_surface_declarations.py` is new and holds exactly one test; within `.github/workflows/tests.yml` only the file list of the `output-conformance` step; within `CONTRIBUTING.md` only the sentence at `:196`. `agent_workflows/lane_containment.py:1069` is expected to need NO edit (it cites the restored test by name, so it becomes true again), and is deliberately NOT in `Scope-Paths`; if it does need one, make it and justify it. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Three claims here are specifically easy to fake and must not be: V-02's DRIVEN exit codes (a declared `exit_contract` copied from a neighbour proves nothing), V-04's `1 passed` from the CI step's own command (the current step says `no tests ran`, and a green step is not the same as a running one), and V-01's `empty_error_renderer` basis, since no restored test checks it.

DO NOT REPEAT THE VACUOUS-CI CLAIM WITHOUT RE-MEASURING. Sibling plan `8ud1is` records that the step "collects nothing and exits 0", and review measured exit **5** three times. Exit 5 is nonzero, so the step FAILS rather than passing silently. If your own measurement disagrees with this plan, paste yours and say so; do not inherit either number.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if the restored one-test file does not FAIL when a declaration is removed (V-03's mutation), stop and report, because a guard that cannot fail is worse than none; if driving a `mutation_gate` measurement shows `add`/`remove`/`default` behave differently from F-6's measurement, stop and report the handler you read rather than declaring the plan's value over your own observation.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `4fe3al` `done` with `--evidence` citing the executed plan. It carries `- Blocks-Release: next`, which this plan inherits, so the gate is preserved by that handoff and no separate de-gating is required.
