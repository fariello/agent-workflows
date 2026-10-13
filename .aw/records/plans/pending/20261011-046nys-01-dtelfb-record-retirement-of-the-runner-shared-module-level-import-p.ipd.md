# IPD: Record retirement of the runner_shared module-level import pin in code comments

- Date: 2026-10-11
- Kind: child
- Concern: `agent_workflows/runner_shared.py` and `agent_workflows/ipd_lint.py` cite `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared` as a LIVE guard that pins `runner_shared`'s module-level first-party imports to exactly `render_stream` + `runner_profiles`. That test was an AST-over-source code pin; it was deleted from the file by `80db6750c` ("test: delete 366 tests that pinned code structure instead of behaviour") and the whole file was deleted by `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests"). Measured at authoring HEAD `d2a511511`: `rg -n test_no_new_module_level_first_party_import_in_runner_shared agent_workflows/` -> 7 sites in `runner_shared.py` and 1 in `ipd_lint.py`; `ls tests/test_orchestrator_probe_cache.py` -> absent. Six of the seven `runner_shared` sites (and the `ipd_lint` site) still assert the pin enforces, refuses, or "breaks a shipped test", which is false. The seventh (inside `should_color`'s docstring) was already corrected by `x3zno3`/`z8ddk0` but misattributes the deletion to `19313eed` alone.
- Scope: Comment and docstring prose only, in the two production files that cite the retired pin. Each site is rewritten to state that the pin was a code pin retired under `GUIDING_PRINCIPLES` P16 (`80db6750c`) and will not return, while preserving the import-discipline convention and its real reason (a module-level import changes the import graph for both host drivers). No executable statement, constant, signature, or test changes.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lint.py, .aw/records/plans/pending/20261011-046nys-01-dtelfb-record-retirement-of-the-runner-shared-module-level-import-p.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: 046nys
- Set: 046nys
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: dtelfb
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004. Re-verified at HEAD 63464df34: 7+1 sites, guard absent, 80db6750c retiring commit, AST import set {render_stream, runner_profiles}, RUN_TYPE_CHOICES equality True with no test.

- 2026-10-12 draft (opencode): created.
- 2026-10-11 to-review (opencode): authored from backlog `046nys`; sites measured at HEAD `d2a511511`.

## Goal

Make every comment that cites `test_no_new_module_level_first_party_import_in_runner_shared` say the truth: the pin was a code-structure test retired under P16 in `80db6750c` and will not be restored, and the module-level first-party import discipline in `runner_shared` is a reviewed convention that still holds in fact but is not mechanically enforced.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before editing

- [x] E-01 Re-measure the citation population, the test's absence, and the invariant at execution HEAD. Run (a) `rg -n 'test_no_new_module_level_first_party_import_in_runner_shared' agent_workflows/` and record each site with its enclosing symbol; (b) `ls tests/test_orchestrator_probe_cache.py` and `rg -n 'def test_no_new_module_level_first_party_import_in_runner_shared' tests/` (expect only the fixture string inside `tests/test_lost_guard_census.py`, which is a classifier fixture and not the guard); (c) `git log --oneline -S 'def test_no_new_module_level_first_party_import_in_runner_shared' -- tests/` to confirm `80db6750c` as the retiring commit; (d) an AST walk of `runner_shared.py`'s top-level `Import`/`ImportFrom` nodes listing the first-party modules, expected `{agent_workflows.render_stream, agent_workflows.runner_profiles}`. If (d) shows any additional module-level first-party import, STOP: the comments would then describe a convention the file violates, which needs its own plan.
  - Depends on: none
  - Expected outcome: 8 sites (7 + 1) listed, guard absent, retiring commit confirmed, invariant holds; any count drift recorded and attributed.
  - Execution state: performed

- [x] E-02 Record the suite baseline at execution HEAD with a BARE `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`) and `python3 -m pytest tests/test_ipd_lint.py -o addopts=""`, plus `git rev-parse --short HEAD`.
  - Depends on: E-01
  - Expected outcome: two summary lines (and any failing-test names) recorded as this plan's own pre-edit baseline.
  - Execution state: performed

### Task group 2: rewrite the citations

- [x] E-03 Rewrite the four `runner_shared.py` sites that justify a FUNCTION-LOCAL import or a lazy computation by the pin: (a) the hostdedup `li44r9` comment above the `render_stream` import ("`runner_shutdown` and `platform_lock` are reached through FUNCTION-LOCAL imports"); (b) the runnerlayer `1f7xno` comment inside the `render_stream` import list ("the shipped guard ... pins this module's module-level first-party imports"); (c) the `lane_plan_is_terminal` comment above `from agent_workflows import run_selection_policy as _rsp` ("its module-level first-party imports are PINNED"); (d) the `edge_satisfied` comment above the function-local `run_selection_policy` import ("a module-level first-party import here is REFUSED by"). Each rewrite keeps the mechanism and its real reason (an import at module scope changes the import graph for every host driver; function-local is this module's established convention), replaces the enforcement claim with: the former pin `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared` was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the convention is held by review rather than by a test. For (a), also drop the closing "no guard re-base" clause, which presupposes a live guard. For (b), preserve the statement that extending the existing `render_stream` statement leaves the module SET unchanged, reworded as a convention rather than a guard constraint, AND reword the immediately following sibling comment in the same import list ("The two renderers `announce_run_order` closes over ... leaves the pinned MODULE SET unchanged"), which does not repeat the test name but refers back to the same pin, so it says the module SET is unchanged under the convention.
  - Depends on: E-02
  - Expected outcome: none of (a)-(d), nor the `announce_run_order` sibling comment, asserts a live guard; each names the retirement and `80db6750c`; each still states the convention and its reason.
  - Execution state: performed

- [x] E-04 Rewrite the two `runner_shared.py` sites that justify a MODULE-LEVEL constant or helper shape by the pin, plus the corrected `should_color` docstring: (a) the `RUN_TYPE_CHOICES` doc-comment ("SPELLED HERE RATHER THAN IMPORTED ... a standing repository constraint"): restate the reason as the convention, and ALSO correct that block's second false claim, "TIED TO THEIR AUTHORITY BY TEST: `test_the_type_vocabulary_is_the_policy_modules_own` asserts this tuple EQUALS `run_selection_policy.SPEC_TYPE_ORDER`", because that test was deleted in `19313eed7` and `rg -n RUN_TYPE_CHOICES tests/` finds nothing; the replacement must say the equality is maintained by hand and that no test currently asserts it (measured equal at authoring); (b) the `set_retirement_terminal_statuses` doc-comment ("COMPUTED LAZILY ... pins that set to `render_stream` plus `runner_profiles`"); (c) the `should_color` docstring's parenthetical, which already says no live guard enforces the rule but attributes the deletion to `19313eed` only: amend it to name `80db6750c` as the retiring commit (P16 code pin) and state it will not return, keeping its existing honest wording otherwise.
  - Depends on: E-03
  - Expected outcome: all seven `runner_shared.py` sites state the retirement; the `RUN_TYPE_CHOICES` block no longer claims a test ties the tuple to its authority.
  - Execution state: performed

- [x] E-05 Rewrite the `ipd_lint.py` site in the "WHY IT LIVES HERE" paragraph above `ORCH_ROW_NOT_TYPED` (the comment that says the test "asserts that by SET EQUALITY, so the import a new module would need there breaks a shipped test"). Keep the OQ-01 reasoning (a new module would need a module-level import in `runner_shared`, which the convention forbids; `runner_shared` already reaches `ipd_lint` function-locally) and replace the "breaks a shipped test" claim with the retirement statement (code pin retired under P16 in `80db6750c`, will not return; the convention is held by review).
  - Depends on: E-04
  - Expected outcome: `ipd_lint.py` no longer claims a shipped test enforces the import set; the placement reasoning survives.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" and `GUIDING_PRINCIPLES` P16 forbid restoring an AST-over-source test; the retired test parsed `Path(rs.__file__).read_text()` with `ast.parse` (visible in `git show 80db6750c -- tests/test_orchestrator_probe_cache.py`), so it is exactly such a pin and the remedy is prose, not a new test.
- Precedent wording: executed plan `9vtas9` (`gia5i7`, the `NoRunnerImportTests` family in the same file) and the `should_color` docstring already use "deleted in `<commit>`; no live guard currently enforces this". This plan follows that shape and adds the "retired under P16, will not return" statement the backlog item asks for.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Suite is run BARE (`python3 -m pytest`); narrowed runs clear defaults with `-o addopts=""`.

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | MEDIUM | `rg -n test_no_new_module_level_first_party_import_in_runner_shared agent_workflows/` -> 7 hits in `runner_shared.py` (hostdedup `li44r9` comment, runnerlayer `1f7xno` comment, `should_color` docstring, `lane_plan_is_terminal`, `RUN_TYPE_CHOICES` doc-comment, `set_retirement_terminal_statuses` doc-comment, `edge_satisfied`) and 1 in `ipd_lint.py` ("WHY IT LIVES HERE" paragraph); `ls tests/test_orchestrator_probe_cache.py` -> absent | The backlog item's count (7 + 1) verifies exactly at authoring HEAD `d2a511511`. |
| F-02 | MEDIUM | `git log --oneline -S test_no_new_module_level_first_party_import_in_runner_shared -- tests/` -> `80db6750c` (removed the def), `19313eed7` (removed the file), plus `0f2edb760` (`oyh28b` census fixture) | The pin was retired as a code pin by `80db6750c`; the existing `should_color` wording attributes it to `19313eed` alone, which is the file deletion, not the retirement. E-04(c) corrects the attribution. |
| F-03 | MEDIUM | AST walk of `runner_shared.py` top-level imports -> `{agent_workflows.render_stream, agent_workflows.runner_profiles}` | The invariant the pin asserted still holds in fact, so the rewrite states an unenforced but true convention, not an abandoned one. |
| F-04 | LOW | `RUN_TYPE_CHOICES` doc-comment cites `test_the_type_vocabulary_is_the_policy_modules_own`; `git log -S` on that name -> `19313eed7`; `rg -n RUN_TYPE_CHOICES tests/` -> nothing; runtime check `tuple(RUN_TYPE_CHOICES) == tuple(SPEC_TYPE_ORDER)` -> `True` | A second dead-guard claim sits inside a block E-04 must rewrite anyway; leaving it would keep the block asserting a test tie that does not exist. It is fixed in place (same precedent as `9vtas9` F-07). |
| F-05 | LOW | `runner_shared.py` `_read_kind`-area docstring: "a rule enforced by `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`"; that class is absent (deleted in `19313eed7`) | Same property, different dead symbol, in a separate paragraph not citing this item's test. Deferred to `3tov52`, which owns dangling test-symbol citations in this file. |
| F-06 | LOW | `tools/lost_guard_census.py` and `tests/test_lost_guard_census.py` mention the name as a classifier fixture | Not citations of a live guard; they correctly use the name as a known code-pin example. No change. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: re-measure sites, absence, retiring commit, and invariant; record suite baselines. No file changes.
2. E-03: rewrite the four function-local-import justifications in `runner_shared.py`.
3. E-04: rewrite the `RUN_TYPE_CHOICES` and `set_retirement_terminal_statuses` doc-comments and amend the `should_color` docstring attribution; strike the dead `test_the_type_vocabulary_is_the_policy_modules_own` tie in the same block.
4. E-05: rewrite the `ipd_lint.py` placement rationale.

## Deferred / out of scope (with reason)

- The `TheRowWalkIsSharedWithTheRetirementGate` "rule enforced by" citation in `runner_shared.py` (F-05). Different dead symbol in a separate paragraph; owned by the open backlog item for dangling test-symbol citations.
  - Carrier: 3tov52
- Restoring the pin or writing any replacement AST/source-reading guard. Forbidden by `AGENTS.md` and `GUIDING_PRINCIPLES` P16; the backlog item states the pin "will not return".
  - Carrier-Declined: two repository-wide contracts forbid the work, so a carrier would invite a prohibited test.
- The `tools/lost_guard_census.py` / `tests/test_lost_guard_census.py` fixture mentions (F-06).
  - Carrier-Declined: there is no defect; they name the test as a code-pin example, which is accurate.

## Scope check

- Over-scope: none. Comment and docstring edits only in the two declared production files; the `RUN_TYPE_CHOICES` dead-test fix sits inside a block this plan must rewrite anyway (F-04). V-05 proves no executable change by AST comparison.
- Under-scope: one sibling dead citation (F-05) is deliberately left to `3tov52`; after this plan the import discipline has no mechanical guard, which is the recorded P16 decision, not an oversight.

## Required tests / validation

No test is authored (P16). Validation: (a) every edited passage is quoted in full and a re-run of E-01(a) shows each surviving mention of the test name sits in a retirement statement naming `80db6750c`; (b) the invariant is re-checked after the edit; (c) an AST comparison of both files before/after with docstrings stripped prints EQUAL; (d) a bare `python3 -m pytest` and `python3 -m pytest tests/test_ipd_lint.py -o addopts=""` show the same failing-test set as E-02's baselines and no lower passed count.

## Spec / documentation sync

N/A with reason: no spec describes `runner_shared`'s import discipline or this test (`rg -n test_no_new_module_level .aw/records/specs/` returns nothing), so `- Scope-Paths:` declares no `.spec.md`. No user-facing doc or CHANGELOG entry: internal implementation comments only, no behavior change.

## Open questions

### OQ-01: Should the citations be removed outright, or kept as a retirement record?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the backlog item itself, which asks that "the comments should be updated to state that the pin was retired and will not return". So the test name is KEPT at each site inside an explicit retirement statement (naming `80db6750c` and P16) rather than deleted, which also matches the precedent wording already used in `should_color`'s docstring.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of each of the four E-01 commands (a)-(d) with the exact command line, each stated explicitly as present or absent; the site list with enclosing symbols; the module-level first-party import set printed by the AST walk. Any count differing from 7 + 1 is stated and attributed to a commit. If (d) shows an extra import, this item FAILS and the plan stops.
  - Observed evidence:
    (a) Exact command line: `rg -n 'test_no_new_module_level_first_party_import_in_runner_shared' agent_workflows/`
    Pasted output:
    ```
    agent_workflows/ipd_lint.py
    1795:# test_no_new_module_level_first_party_import_in_runner_shared` asserts that by SET EQUALITY, so the

    agent_workflows/runner_shared.py
    167:# `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    202:    # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    359:    `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    1856:    # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`,
    14273:#: test_no_new_module_level_first_party_import_in_runner_shared` pins this module's module-level
    18582:#: `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    43053:        # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`,
    ```
    Status: 8 sites present (7 in `runner_shared.py`, 1 in `ipd_lint.py`), count matches 7 + 1 exactly with no drift.
    Site list with enclosing symbols:
    1. `runner_shared.py:167`: module scope, hostdedup `li44r9` comment above `from agent_workflows.render_stream import (`
    2. `runner_shared.py:202`: module scope, runnerlayer `1f7xno` comment inside `from agent_workflows.render_stream import (...)`
    3. `runner_shared.py:359`: function `should_color` docstring
    4. `runner_shared.py:1856`: function `lane_plan_is_terminal` comment above `from agent_workflows import run_selection_policy as _rsp`
    5. `runner_shared.py:14273`: module scope, `RUN_TYPE_CHOICES` doc-comment
    6. `runner_shared.py:18582`: function `set_retirement_terminal_statuses` doc-comment
    7. `runner_shared.py:43053`: function `edge_satisfied` comment above function-local `from agent_workflows.selectors import read_front_matter_status as _read_status`
    8. `ipd_lint.py:1795`: module scope, section comment block `The typed child-tracking row` above `ORCH_ROW_NOT_TYPED`

    (b) Exact command line: `ls tests/test_orchestrator_probe_cache.py 2>&1 || true; rg -n 'def test_no_new_module_level_first_party_import_in_runner_shared' tests/ || true`
    Pasted output:
    ```
    ls: cannot access 'tests/test_orchestrator_probe_cache.py': No such file or directory
    tests/test_lost_guard_census.py
    39:def test_no_new_module_level_first_party_import_in_runner_shared(self):
    ```
    Status: `tests/test_orchestrator_probe_cache.py` is ABSENT; guard definition is ABSENT from tests (`tests/test_lost_guard_census.py:39` is a classifier fixture string, not the guard).

    (c) Exact command line: `git log --oneline -S 'def test_no_new_module_level_first_party_import_in_runner_shared' -- tests/`
    Pasted output:
    ```
    0f2edb760 work(oyh28b): Build a reproducible lost-guard census over the two suite-trim commits and triage only the behavioral gaps
    80db6750c test: delete 366 tests that pinned code structure instead of behaviour
    b816200c7 feat(orchprobe): cache an orchestrator probe verdict against a content digest (8tgg6g)
    ```
    Status: `80db6750c` confirmed as the retiring commit that deleted the test definition.

    (d) Exact command line:
    ```sh
    python3 -c "
    import ast
    from pathlib import Path

    tree = ast.parse(Path('agent_workflows/runner_shared.py').read_text(encoding='utf-8'))
    module_level = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or '').startswith('agent_workflows'):
            module_level.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('agent_workflows'):
                    module_level.append(alias.name)
    flat = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'agent_workflows':
            flat.extend(f'agent_workflows.{a.name}' for a in node.names)
    found = {m for m in module_level if m != 'agent_workflows'} | set(flat)
    print(sorted(found))
    "
    ```
    Pasted output:
    ```
    ['agent_workflows.render_stream', 'agent_workflows.runner_profiles']
    ```
    Status: Module-level first-party import set is exactly `{'agent_workflows.render_stream', 'agent_workflows.runner_profiles'}`. Invariant holds; no additional imports present.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted summary line of the bare `python3 -m pytest` (with an explicit statement that no flags were added), pasted summary line of `python3 -m pytest tests/test_ipd_lint.py -o addopts=""`, and the `git rev-parse --short HEAD` output; stated as this lane's own baseline.
  - Observed evidence:
    (1) Bare `python3 -m pytest` (no flags added, no `-n0`, no extra `-q`, no `-p no:randomly`):
    Summary output:
    ```
    FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository
    1 failed, 7715 passed, 4 skipped, 3 warnings in 722.70s (0:12:02)
    ```
    Failing test: `tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository` (builtins.open spy caught concurrent file write under xdist; passed when run isolated).
    (2) `python3 -m pytest tests/test_ipd_lint.py -o addopts=""`:
    Summary output:
    ```
    ======================== 76 passed in 161.14s (0:02:41) ========================
    ```
    (3) `git rev-parse --short HEAD`:
    Output:
    ```
    04ef67656
    ```
    Lane baseline recorded at `04ef67656`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the four rewritten passages (a)-(d) and the reworded `announce_run_order` sibling comment QUOTED IN FULL, each with a one-line note naming the preserved design point; each must visibly name the retirement, `80db6750c`, P16 or "code pin", and "will not return" (or equivalent), and must not contain "PINNED", "pinned MODULE SET", "REFUSED by", "pins this module's", "shipped guard", or "guard re-base" as a live claim.
  - Observed evidence:
    (a) `runner_shared.py` lines 163-171 (hostdedup `li44r9` comment above `render_stream` import):
    ```python
    # hostdedup Order 01 (`li44r9`): `runner_shutdown` and `platform_lock` are reached through
    # FUNCTION-LOCAL imports in the lock/reaper bodies below, NOT at module scope, even though both are
    # provably cycle-free from here (their own top-level first-party imports are stdlib plus
    # `platform_lock`). The reason is an established convention rather than a cycle, because an import
    # added here changes the import graph for EVERY host driver. The former pin
    # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    # was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the
    # convention of restricting module-level first-party imports to `render_stream` + `runner_profiles`
    # is held by review rather than by a test. The function-local form is this module's own convention
    # in twenty-plus places, so the lift needs no new precedent.
    ```
    Preserved design point: function-local import in lock/reaper bodies avoids changing the import graph for host drivers.

    (b) `runner_shared.py` lines 201-211 (runnerlayer `1f7xno` comment inside `render_stream` import list):
    ```python
        # runnerlayer Order 02 (`1f7xno`), backlog `cnwy8g`: the two renderers the re-homed
        # `report_run_spec_edits` closes over. They are ADDED TO THE EXISTING `render_stream` statement
        # rather than imported from a new module, deliberately: by convention, this module restricts its
        # module-level first-party imports to EXACTLY `render_stream` + `runner_profiles`. The former pin
        # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
        # was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so
        # this convention is held by review rather than by a test. The convention constrains the MODULE
        # SET, not the name count, so extending a statement that already names `render_stream` leaves the
        # module set unchanged.
    ```
    Preserved design point: adding imported symbols to the existing `render_stream` import statement leaves the module set unchanged under the convention.

    (sibling) `runner_shared.py` lines 220-224 (`announce_run_order` sibling comment):
    ```python
        # The two renderers `announce_run_order` closes over, added by the same batch and under the same
        # rule: extending a statement that already names `render_stream` leaves the module SET unchanged
        # under the convention.
    ```
    Preserved design point: extending an existing import from `render_stream` preserves the module set under the convention.

    (c) `runner_shared.py` lines 1858-1864 (`lane_plan_is_terminal` comment):
    ```python
        # FUNCTION-LOCAL, per this module's own convention: an import added at module scope changes the
        # import graph for EVERY host driver. The former pin
        # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
        # was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the
        # convention of restricting module-level first-party imports to exactly `render_stream` +
        # `runner_profiles` is held by review rather than by a test.
    ```
    Preserved design point: `run_selection_policy` is imported function-locally to avoid altering the module-level import graph.

    (d) `runner_shared.py` lines 43060-43070 (`edge_satisfied` comment):
    ```python
            # THE READER IS IMPORTED FUNCTION-LOCALLY, in the same form its two sibling uses in this module
            # already take (`reconcile_disposition` and the lane predicate both do exactly this). In
            # `oc_runipd` this body resolved a MODULE-LEVEL `_read_status`; `runner_shared` has no such
            # global, and an import added at module scope changes the import graph for every host driver.
            # The former pin
            # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
            # was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so
            # the convention of restricting module-level first-party imports to exactly `render_stream` plus
            # `runner_profiles` is held by review rather than by a test. The function-local form is this
            # module's documented route for a first-party dependency.
    ```
    Preserved design point: permissive reader `_read_status` is imported function-locally, consistent with sibling callers and avoiding module-scope graph changes.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the three rewritten passages (a)-(c) QUOTED IN FULL; for (a), pasted `rg -n 'RUN_TYPE_CHOICES|test_the_type_vocabulary' tests/` output (expected no match) and a pasted runtime equality check of `RUN_TYPE_CHOICES` vs `run_selection_policy.SPEC_TYPE_ORDER`, with the comment's new claim matching what was measured; for (c), the docstring names `80db6750c`.
  - Observed evidence:
    (a) `runner_shared.py` lines 14277-14287 (`RUN_TYPE_CHOICES` doc-comment):
    ```python
    #: SPELLED HERE RATHER THAN IMPORTED, and the reason is an established repository convention rather than a
    #: preference: an import added at module scope changes the import graph for EVERY host driver. The former
    #: pin `tests/test_orchestrator_probe_cache.py::
    #: test_no_new_module_level_first_party_import_in_runner_shared` was a code pin retired under
    #: `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the convention of restricting
    #: module-level first-party imports to EXACTLY `render_stream` + `runner_profiles` is held by review
    #: rather than by a test; `run_selection_policy.SPEC_TYPE_ORDER` cannot be read at module scope, and a
    #: function-local import cannot build a module-level tuple either. The values are written out here and
    #: the equality with `run_selection_policy.SPEC_TYPE_ORDER` is maintained by hand (measured equal; no
    #: test currently asserts it, as the former test `test_the_type_vocabulary_is_the_policy_modules_own`
    #: was deleted in `19313eed7`).
    ```
    Check `rg -n 'RUN_TYPE_CHOICES|test_the_type_vocabulary' tests/`:
    (No matches found)
    Runtime equality check:
    ```sh
    python3 -c "
    from agent_workflows import runner_shared, run_selection_policy
    print('runner_shared.RUN_TYPE_CHOICES:', runner_shared.RUN_TYPE_CHOICES)
    print('run_selection_policy.SPEC_TYPE_ORDER:', run_selection_policy.SPEC_TYPE_ORDER)
    print('Equal:', tuple(runner_shared.RUN_TYPE_CHOICES) == tuple(run_selection_policy.SPEC_TYPE_ORDER))
    "
    ```
    Output:
    ```
    runner_shared.RUN_TYPE_CHOICES: ('ipd', 'spec', 'backlog', 'prompt', 'research', 'release', 'walkthrough')
    run_selection_policy.SPEC_TYPE_ORDER: ('ipd', 'spec', 'backlog', 'prompt', 'research', 'release', 'walkthrough')
    Equal: True
    ```

    (b) `runner_shared.py` lines 18588-18596 (`set_retirement_terminal_statuses` doc-comment):
    ```python
    #: COMPUTED LAZILY THROUGH A FUNCTION, not at import time, because `ipd_schema` is first-party and this
    #: module avoids adding module-level first-party imports that alter the import graph for host drivers.
    #: The former pin
    #: `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    #: was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the
    #: convention of restricting module-level first-party imports to `render_stream` plus `runner_profiles`
    #: is held by review rather than by a test. Every other first-party dependency here arrives
    #: function-locally, so this follows the module's existing route.
    def set_retirement_terminal_statuses() -> frozenset[str]:
    ```

    (c) `runner_shared.py` lines 358-364 (`should_color` docstring):
    ```python
        THE IMPORT IS FUNCTION-LOCAL DELIBERATELY, because an import added at module level changes the
        import graph for BOTH host drivers. A function-local import is this module's established
        convention for a first-party dependency (`ipd_lint`/`ipd_schema`/`ipd_lifecycle`/`worktree_lease`
        all arrive that way), kept here as a convention (the historical guard
        `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
        was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c`, with the file deleted in
        `19313eed7`, and will not return; no live guard currently enforces this).
    ```
    Docstring explicitly names `80db6750c` as retiring commit and states the pin will not return.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (1) the rewritten `ipd_lint.py` paragraph QUOTED IN FULL; (2) post-edit `rg -n 'test_no_new_module_level_first_party_import_in_runner_shared' agent_workflows/` output with each hit shown to sit in a retirement statement; (3) an AST comparison of `agent_workflows/runner_shared.py` and `agent_workflows/ipd_lint.py` against `git show HEAD:<path>` with module/class/function docstrings stripped, `ast.dump(..., include_attributes=False)`, printing EQUAL for both (the script pasted); (4) the E-01(d) invariant re-run post-edit; (5) suite parity: bare `python3 -m pytest` and `python3 -m pytest tests/test_ipd_lint.py -o addopts=""` summary lines pasted, with the set of FAILING tests identical by name to V-02's baseline and the passed count not lower (a collected count is an artifact of test organization, not the bar); any difference attributed to a named intervening commit after re-baselining.
  - Observed evidence:
    (1) Rewritten `ipd_lint.py` lines 1792-1798 QUOTED IN FULL:
    ```python
    # WHY IT LIVES HERE rather than in a new shared module (this plan's OQ-01, resolved from repository
    # evidence). `runner_shared` keeps EXACTLY `{render_stream, runner_profiles}` as its module-level
    # first-party imports by convention. The former pin `tests/test_orchestrator_probe_cache.py::
    # test_no_new_module_level_first_party_import_in_runner_shared` was a code pin retired under
    # `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return; the convention is held by review
    # rather than by a test, so adding a new module import in `runner_shared` would violate that reviewed
    # convention. `runner_shared` already reaches `ipd_lint` through function-local imports in four places,
    # which is how a runner reaches this.
    ```
    (2) Post-edit `rg -n -C 2 'test_no_new_module_level_first_party_import_in_runner_shared' agent_workflows/` output:
    ```
    agent_workflows/ipd_lint.py
    1793-# evidence). `runner_shared` keeps EXACTLY `{render_stream, runner_profiles}` as its module-level
    1794-# first-party imports by convention. The former pin `tests/test_orchestrator_probe_cache.py::
    1795:# test_no_new_module_level_first_party_import_in_runner_shared` was a code pin retired under
    1796-# `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return; the convention is held by review
    1797-# rather than by a test, so adding a new module import in `runner_shared` would violate that reviewed

    agent_workflows/runner_shared.py
    166-# `platform_lock`). The reason is an established convention rather than a cycle, because an import
    167-# added here changes the import graph for EVERY host driver. The former pin
    168:# `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    169-# was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the
    170-# convention of restricting module-level first-party imports to `render_stream` + `runner_profiles`
    --
    202-    # rather than imported from a new module, deliberately: by convention, this module restricts its
    203-    # module-level first-party imports to EXACTLY `render_stream` + `runner_profiles`. The former pin
    204:    # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    205-    # was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so
    206-    # this convention is held by review rather than by a test. The convention constrains the MODULE
    --
    360-    convention for a first-party dependency (`ipd_lint`/`ipd_schema`/`ipd_lifecycle`/`worktree_lease`
    361-    all arrive that way), kept here as a convention (the historical guard
    362:    `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    363-    was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c`, with the file deleted in
    364-    `19313eed7`, and will not return; no live guard currently enforces this).
    --
    1858-    # FUNCTION-LOCAL, per this module's own convention: an import added at module scope changes the
    1859-    # import graph for EVERY host driver. The former pin
    1860:    # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    1861-    # was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the
    1862-    # convention of restricting module-level first-party imports to exactly `render_stream` +
    --
    14278-#: preference: an import added at module scope changes the import graph for EVERY host driver. The former
    14279-#: pin `tests/test_orchestrator_probe_cache.py::
    14280:#: test_no_new_module_level_first_party_import_in_runner_shared` was a code pin retired under
    14281-#: `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the convention of restricting
    14282-#: module-level first-party imports to EXACTLY `render_stream` + `runner_profiles` is held by review
    --
    18589-#: module avoids adding module-level first-party imports that alter the import graph for host drivers.
    18590-#: The former pin
    18591:#: `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    18592-#: was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so the
    18593-#: convention of restricting module-level first-party imports to `render_stream` plus `runner_profiles`
    --
    43063-        # global, and an import added at module scope changes the import graph for every host driver.
    43064-        # The former pin
    43065:        # `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    43066-        # was a code pin retired under `GUIDING_PRINCIPLES` P16 in `80db6750c` and will not return, so
    43067-        # the convention of restricting module-level first-party imports to exactly `render_stream` plus
    ```
    All 8 hits sit in explicit retirement statements citing `80db6750c` and stating the pin will not return.

    (3) AST comparison against `git show HEAD:<path>` with docstrings stripped:
    Script:
    ```python
    import ast
    import subprocess

    def strip_docstrings(node):
        for n in ast.walk(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (n.body and isinstance(n.body[0], ast.Expr) and
                    isinstance(n.body[0].value, ast.Constant) and
                    isinstance(n.body[0].value.value, str)):
                    n.body = n.body[1:]
        return node

    for path in ['agent_workflows/runner_shared.py', 'agent_workflows/ipd_lint.py']:
        head_src = subprocess.check_output(['git', 'show', f'HEAD:{path}'], text=True)
        with open(path, 'r', encoding='utf-8') as f:
            curr_src = f.read()
        head_tree = strip_docstrings(ast.parse(head_src))
        curr_tree = strip_docstrings(ast.parse(curr_src))
        head_dump = ast.dump(head_tree, include_attributes=False)
        curr_dump = ast.dump(curr_tree, include_attributes=False)
        status = 'EQUAL' if head_dump == curr_dump else 'DIFFERENT'
        print(f'{path}: {status}')
    ```
    Output:
    ```
    agent_workflows/runner_shared.py: EQUAL
    agent_workflows/ipd_lint.py: EQUAL
    ```

    (4) E-01(d) invariant re-run post-edit:
    Output:
    ```
    ['agent_workflows.render_stream', 'agent_workflows.runner_profiles']
    ```

    (5) Suite parity post-edit:
    - Bare `python3 -m pytest`:
      ```
      7716 passed, 4 skipped, 3 warnings in 697.02s (0:11:37)
      ```
      Failing tests: 0 (the flaky `InspectionVerbTests.test_the_verbs_write_nothing_to_the_repository` from the baseline passed; no failing tests remain; passed count 7716 is not lower than baseline 7715).
    - `python3 -m pytest tests/test_ipd_lint.py -o addopts=""`:
      ```
      ======================== 76 passed in 62.75s (0:01:02) =========================
      ```
      Passed count 76 equals baseline 76.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

The plan must not execute before explicit human approval recorded through `aw ipd set approved`.

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. `- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. Commit only the declared paths through `aw commit <plan> -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push. Verify the staged set with `git diff --cached --name-only` before committing. HONESTY RULE: you MUST paste the ACTUAL command output for every measurement and suite claim; a claimed pass with no output does not satisfy a `V-*` item. The one STOP condition is E-01(d) showing a module-level first-party import beyond `render_stream` + `runner_profiles`; a drifted site count is expected and is narrowed, not a stop. If a site's comment block is concurrently changed in a way that cannot be safely combined, stop and report.

POST-GATE LIFECYCLE MOVE. After every `V-*` passes with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is tooled: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run start with `aw ipd begin <plan>` before any edit and finish with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`; under a runner the executor must NOT run `aw ipd finalize` itself. Sibling plan `65d5zf` (`3tov52`) also declares `agent_workflows/runner_shared.py` but owns disjoint sites (it excludes this test's citations), so no ordering edge is needed. Never `git mv` the plan or hand-edit `- Status:`. Backlog `046nys` carries no `- Blocks-Release:`, so no gate is inherited; this plan is its sole carrier.
