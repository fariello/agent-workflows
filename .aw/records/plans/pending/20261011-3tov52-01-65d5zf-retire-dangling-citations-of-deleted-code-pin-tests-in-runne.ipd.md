# IPD: Retire dangling citations of deleted code-pin tests in runner comments

- Date: 2026-10-11
- Kind: child
- Concern: Comments and docstrings in `agent_workflows/runner_shared.py`, `agent_workflows/agy_runipd.py` (and the byte-for-byte twin paragraph in `agent_workflows/oc_runipd.py`) cite tests that no longer exist as if they were LIVE guards: `tests/test_review_findings_cascade.py::SharedPredicateTests` (a source-substring table, deleted with the file in `19313eed7`), `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` (a substring guard, folded into `SharedPredicateTests` by `d27e5eac8`, then deleted with it), `tests/test_runner_stop_triggers.py` (whose `_shim_set` read the inline `subcommands` set off `main`'s AST, earlier by regex; file deleted in `19313eed7`), and `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate` plus the import-count baseline in the same file (file deleted in `19313eed7`). Measured at authoring HEAD `31c16869b`: `ls tests/test_review_findings_cascade.py tests/test_runner_stop_triggers.py tests/test_orchestrator_probe_cache.py` -> all three absent.
- Scope: Comment, docstring, and test-docstring prose only. Each cited deleted test is rewritten into a retirement statement (what it asserted, that it was deleted in which commit, that the source-reading form is a code pin that will not return under `GUIDING_PRINCIPLES` P16, and that the property is now held by review). The design reasoning each comment carries is preserved. No executable statement, constant, signature, import, or test assertion changes.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py, tests/test_agy_runipd_cli.py, .aw/records/plans/pending/20261011-3tov52-01-65d5zf-retire-dangling-citations-of-deleted-code-pin-tests-in-runne.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 3tov52
- Set: 3tov52
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: 65d5zf
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004

- 2026-10-12 draft (opencode): created.
- 2026-10-11 to-review (opencode): authored from backlog `3tov52`; sites measured at HEAD `31c16869b`.

## Goal

Make every runner comment that cites a deleted code-pin test say the truth: the test is gone (named commit), its source-reading form will not return under P16, and the invariant it guarded is held by review (or, where a behavioral replacement is wanted, by the follow-up backlog item `2ohbkj`), so a reader never trusts a guard that does not exist.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before editing

- [x] E-01 Re-measure the citation population and the facts the rewrites will assert, at execution HEAD. Run (a) `rg -n 'test_review_findings_cascade|test_runner_stop_triggers\.py|test_runner_stop_triggers\b|TheRowWalkIsSharedWithTheRetirementGate|re-measured in' agent_workflows/runner_shared.py agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py tests/test_agy_runipd_cli.py` and record each hit with its enclosing symbol (exclude `test_runner_stop_triggers_e2e`, which exists); (b) `ls tests/test_review_findings_cascade.py tests/test_runner_stop_triggers.py tests/test_orchestrator_probe_cache.py` (expect all absent); (c) `git log --oneline -S 'class SharedPredicateTests' -- tests/`, `git log --oneline -S 'def test_no_runner_to_runner_import' -- tests/`, `git log --oneline -S 'class TheRowWalkIsSharedWithTheRetirementGate' -- tests/`, `git log --oneline -S 'def _shim_set' -- tests/` to confirm the deleting commits (expected `19313eed7`, `d27e5eac8`, `19313eed7`, `19313eed7`); (d) an AST read of the inline `subcommands` set in `oc_runipd.main` and `agy_runipd.main` (expected both equal to `{start, resume, status, report, stop, integrate, audit, -h, --help}`). If (d) shows the two sets DIFFER, STOP: the comments would then describe an invariant the code violates, which is a bug needing its own plan.
  - Depends on: none
  - Expected outcome: the site list below (F-01..F-03) reproduced, or any drift recorded and attributed; deleting commits confirmed; the two shim sets equal.
  - Execution state: performed

- [x] E-02 Record this lane's suite baseline with a BARE `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`), plus `python3 -m pytest tests/test_agy_runipd_cli.py tests/test_oc_runipd.py -o addopts=""` and `git rev-parse --short HEAD` (this is the BASE commit V-06's AST comparison and V-07's parity check refer to).
  - Depends on: E-01
  - Expected outcome: the pre-edit FAILED node-id set of each run recorded as the baseline (sets by node id; the pass counts are context only, because load-sensitive nodes carried by `wc5c5e` vary run to run).
  - Execution state: performed

### Task group 2: rewrite the citations

- [x] E-03 Rewrite the three `runner_shared.py` sites: (a) the `_findings_block_reason` docstring sentence "`agy_runipd` keeps the NAME bound (a re-export) because `tests/test_review_findings_cascade.py::SharedPredicateTests` asserts the attribute exists ...": keep that the re-export exists and that both hosts still call one shared predicate, and state that `SharedPredicateTests` (a source-substring code pin) was deleted in `19313eed7`, will not return under P16, and nothing currently requires the name to stay bound; (b) the `resolve_prior_lane` docstring clause "without `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` having to be satisfied on a technicality": keep the point that the lift removed a runner-to-runner import, and state the substring guard was retired (`d27e5eac8` folded it into `SharedPredicateTests`, deleted in `19313eed7`), so the no-runner-to-runner-import rule is held by review; (c) the `parse_plan_file` docstring "WHY THE `selectors` IMPORT IS FUNCTION-LOCAL" paragraph's "a rule enforced by `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`": replace with a statement that no live test enforces the function-local convention (the cited class, deleted in `19313eed7`, was a row-walk spy test and never enforced imports), keeping the measured import-graph reasoning intact. Do NOT touch the separate `test_no_new_module_level_first_party_import_in_runner_shared` sites, which plan `dtelfb` (backlog `046nys`) owns.
  - Depends on: E-02
  - Expected outcome: none of (a)-(c) asserts a live guard; each names the deleting commit; each still states the design point.
  - Execution state: performed

- [x] E-04 Rewrite the three non-shim `agy_runipd.py` sites: (a) the module comment above `from agent_workflows.runner_shared import (_findings_block_reason ...)` ("the cross-driver API-symmetry contract asserted by `tests/test_review_findings_cascade.py::SharedPredicateTests` requires this module to CARRY the attribute ... That test's second half ... was RE-BASED onto `runner_shared`"): state the contract test was a source-substring code pin deleted in `19313eed7` that will not return, keep the re-export as harmless compatibility, and drop the present-tense "requires"/"still refuses" claims; (b) the `enforce_dependency_preflight` docstring mention of `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import`: keep the history, add that the guard itself no longer exists (retired as above); (c) the `parse_plan_file` import-block comment "56 -> 53, re-measured in `tests/test_orchestrator_probe_cache.py`": keep the measured numbers, add that the re-measuring test (an exact oc-to-agy import-count baseline) was deleted with that file in `19313eed7`, so the count is a historical measurement, not a live assertion.
  - Depends on: E-03
  - Expected outcome: no `agy_runipd.py` non-shim comment claims a live test; history and numbers preserved.
  - Execution state: performed

- [x] E-05 Rewrite the implicit-start shim comment in `agy_runipd.main` above `subcommands = {`: replace "THE TWO DRIVERS' SETS MUST STAY IDENTICAL: `tests/test_runner_stop_triggers.py` regexes `subcommands = \{(.*?)\}` out of BOTH source files, so a one-sided edit here is exactly the divergence that guard exists to catch", "Added in lockstep with the oc twin and with the inline copy in `tests/test_runner_stop_triggers.py`, which pins all three equal", "a test asserts the bare form is not rewritten (in both drivers)", and "(a test pins the two sets against each other)" with: the sets MUST still stay identical and every hazardous verb MUST still be listed (the misfire reasoning is kept verbatim); the structural guard that read this set from source was a code pin deleted in `19313eed7` that will not return under P16, and the behavioral `stop` not-rewritten tests were deleted in the same commit; `integrate` alone is still driven through the real `main` in this driver's tests (`tests/test_agy_runipd_cli.py`, the `agy_runipd.main(["integrate", ...])` calls), which exercises its not-rewritten path, while `stop` and `audit` have no such coverage; restoring that coverage is tracked by backlog `2ohbkj`; until then lockstep of the two sets is held by review. Do not claim a live test for `stop`, `audit` or set equality, and do not deny the surviving `integrate` coverage.
  - Depends on: E-04
  - Expected outcome: the agy shim comment asserts no live test and points at `2ohbkj`; every reason a verb is listed survives.
  - Execution state: performed

- [x] E-06 Make the identical edit in the twin shim comment in `oc_runipd.main` (the "KEEP THIS AS AN INLINE SET LITERAL. `test_runner_stop_triggers` asserts structurally, by regexing ..." paragraph, "the two sets must stay IDENTICAL because the structural test regexes both source files", "pins this set against the agy copy AND against the inline copy in `tests/test_runner_stop_triggers.py`", "a test asserts the bare form is not rewritten (in both drivers)", and the `integpath-04` sentence "A test asserts the bare form is not rewritten, in both drivers, and a third assertion pins this set against the agy copy AND against the inline copy"), applying E-05's rule about `integrate` (still driven through the real `main` in `tests/test_oc_runipd.py`, e.g. `driver.main(["integrate", "mm6wuz"])`) versus `stop`/`audit` (no live coverage, `2ohbkj`). The KEEP-INLINE instruction was justified ONLY by the deleted guard; reword it to say the inline literal is kept for symmetry with the agy twin and because no test now constrains its form, without changing the code. This is the same paragraph as E-05's in the twin driver; editing only one would leave the two drivers' comments contradicting each other.
  - Depends on: E-05
  - Expected outcome: the oc shim comment matches the agy one in substance and asserts no live test.
  - Execution state: performed

- [x] E-07 Rewrite the `tests/test_agy_runipd_cli.py::AgyVerbosityFlagTests` class docstring clause "both drivers' sets were changed together because `tests/test_runner_stop_triggers.py` regexes both source files" to say the sets were changed together to keep the drivers identical (the regexing guard was deleted in `19313eed7`). Docstring only; no assertion changes.
  - Depends on: E-06
  - Expected outcome: no test docstring cites the deleted file as a live guard.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" and `GUIDING_PRINCIPLES` P16 forbid restoring a test that reads production source (`inspect`, `ast`, regex, substring). `SharedPredicateTests` (`git show 80db6750c:tests/test_review_findings_cascade.py`, its `CLAIMS` table of required/forbidden substrings) and `_shim_set` (`git show 19313eed7^:tests/test_runner_stop_triggers.py`, `ast.parse(inspect.getsource(module.main))`) are exactly such pins, so the remedy is prose, not a new structural test.
- The behavioral half of the deleted stop-trigger file (`_stop_is_not_rewritten`, which called `module.main(["stop", ...])` and asserted no run directory appeared) WAS legitimate coverage. Its loss is a separate concern; filed as backlog `2ohbkj` at authoring so the rewritten comments can point at a live carrier rather than at nothing.
- Precedent wording: sibling plan `dtelfb` (backlog `046nys`) and the `should_color` docstring use "deleted in `<commit>`; no live guard currently enforces this". This plan follows that shape.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Suite is run BARE (`python3 -m pytest`); narrowed runs clear defaults with `-o addopts=""`.

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | MEDIUM | `rg -n test_review_findings_cascade agent_workflows/` -> `runner_shared._findings_block_reason` docstring, `runner_shared.resolve_prior_lane` docstring, the `agy_runipd` module comment above the `_findings_block_reason` re-export, `agy_runipd.enforce_dependency_preflight`; `ls tests/test_review_findings_cascade.py` -> absent; `git log -S 'class SharedPredicateTests'` -> `19313eed7` (deletion); `git log -S 'def test_no_runner_to_runner_import'` -> `d27e5eac8` (folded into the table) | Four sites claim a live source-substring contract that has not existed since `19313eed7`. The agy module comment even says the test "still refuses a runner that reimplements the severity comparison". |
| F-02 | MEDIUM | `rg -n test_runner_stop_triggers agent_workflows/ tests/test_agy_runipd_cli.py` (excluding `_e2e`) -> two passages in `agy_runipd.main`'s shim comment, two in `oc_runipd.main`'s, one in `AgyVerbosityFlagTests`; `ls tests/test_runner_stop_triggers.py` -> absent; deletion `19313eed7` | Both shim comments justify KEEP-INLINE and lockstep by a structural guard that is gone, and both say "a test asserts the bare form is not rewritten", which is now false: `rg -n 'main\(\["(stop\|audit)"' tests/` -> no match (only `integrate` is still driven through `main`). |
| F-03 | LOW | `runner_shared.parse_plan_file` docstring cites `TheRowWalkIsSharedWithTheRetirementGate` as enforcing the function-local import rule; `git show 19313eed7^:tests/test_orchestrator_probe_cache.py` shows that class was a row-walk spy test with no import assertion; `agy_runipd` comment "56 -> 53, re-measured in `tests/test_orchestrator_probe_cache.py`" cites the import-count baseline in the same deleted file | One mis-citation (the class never enforced the rule) and one historical number presented as re-measured by a live test. F-03's `runner_shared` site was explicitly deferred to this item by `dtelfb` F-05 (`- Carrier: 3tov52`). |
| F-04 | INFO | AST read of the inline `subcommands` sets in `oc_runipd.main` and `agy_runipd.main` -> both `['--help', '-h', 'audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']` | The lockstep invariant the deleted guard asserted still holds in fact, so the rewrite describes a true, unenforced convention. |
| F-06 | INFO | `tests/test_oc_runipd.py` `driver.main(["integrate", "mm6wuz"])` in `test_the_alias_names_the_subcommand_so_the_shim_cannot_rewrite_it`; `tests/test_agy_runipd_cli.py` `agy_runipd.main(["integrate", "agi001", ...])` | The bare-form not-rewritten claim is false for `stop` and `audit` but still behaviorally exercised for `integrate` in both drivers (added at review). E-05/E-06 must not over-correct into denying it. |
| F-05 | INFO | Backlog item text names only `runner_shared.py` and `agy_runipd.py` | `oc_runipd.main` carries the twin of the agy shim paragraph citing the same deleted test. Editing agy alone would leave the two drivers' comments contradicting each other on the same invariant, so the oc twin is in scope (E-06). |

## Proposed changes (ordered, validatable)

1. E-01, E-02: re-measure sites, deleting commits, and the shim-set invariant; record baselines. No file changes.
2. E-03: rewrite the three `runner_shared.py` docstring sites.
3. E-04: rewrite the three non-shim `agy_runipd.py` sites.
4. E-05, E-06: rewrite the twin implicit-start shim comments in `agy_runipd.main` and `oc_runipd.main`, pointing at `2ohbkj`.
5. E-07: rewrite the `AgyVerbosityFlagTests` docstring clause.

## Deferred / out of scope (with reason)

- Restoring BEHAVIORAL coverage that a bare `stop`/`audit` first token is not rewritten into `start` in both drivers. Real lost coverage, but it is test authoring, not comment retirement, and this item explicitly scopes comments.
  - Carrier: 2ohbkj
- The `test_no_new_module_level_first_party_import_in_runner_shared` citations in `runner_shared.py` and `ipd_lint.py`. Owned by plan `dtelfb`.
  - Carrier: 046nys
- Restoring `SharedPredicateTests`, `_shim_set`, the import-count baseline, or any other source-reading guard.
  - Carrier-Declined: forbidden by `AGENTS.md` and `GUIDING_PRINCIPLES` P16; the backlog item states these pins cannot return.
- Other dangling citations in these files to deleted test files outside this item's clusters (for example `tests/test_runner_refork_guard.py`, `tests/test_runner_item_dependencies.py`, `tests/test_rununify_*`).
  - Carrier: iosmvn

## Scope check

- Over-scope: `oc_runipd.py` and `tests/test_agy_runipd_cli.py` are outside the item's named files; both carry the same deleted-test claim as the agy shim paragraph (F-05) and are prose-only edits. V-06 proves no executable change by AST comparison of all four files.
- Under-scope: lost behavioral not-rewritten coverage is carried by `2ohbkj`; other deleted-file citations are carried by `iosmvn`.

## Required tests / validation

No test is authored or changed in behavior (P16; the only test-file edit is a docstring). Validation: (a) every edited passage quoted in full; (b) a post-edit re-run of E-01(a) shows each surviving mention sits in a retirement statement naming its deleting commit; (c) an AST comparison of all four edited files against `HEAD` with docstrings stripped prints EQUAL (comments are not in the AST, so this proves only prose changed); (d) E-01(d) re-run; (e) bare `python3 -m pytest` and the narrowed run match E-02's baselines.

## Spec / documentation sync

N/A with reason: `rg -n 'SharedPredicateTests|test_runner_stop_triggers\.py|TheRowWalkIsShared' .aw/records/specs/` returned no match at authoring HEAD `31c16869b`; no spec defines these comments, so `- Scope-Paths:` declares no `.spec.md`. No user-facing doc or CHANGELOG entry: internal comments only, no behavior change.

## Open questions

### OQ-01: Remove the citations outright, or keep them as retirement records?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The item says "remove or retire the dead citations". Retire (keep the test name inside an explicit retirement statement naming the deleting commit) is chosen because it tells a later reader why the KEEP-INLINE and re-export choices exist and that their guards are deliberately gone, matching the precedent wording in `dtelfb` and `should_color`'s docstring.

### OQ-02: Should the oc_runipd twin be edited although the item names only runner_shared and agy_runipd?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes (F-05). The two shim paragraphs describe one cross-driver invariant; fixing one would leave them contradicting each other, and the agy text itself says it changes "in lockstep with the oc twin".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of each E-01 command (a)-(d) with the exact command line; the site list with enclosing symbols; each deleting commit stated; the two printed shim sets. Any site-count drift from F-01..F-03 is stated and attributed. If (d) shows unequal sets, this item FAILS and the plan stops.
  - Observed evidence:
    Command (a):
    ```
    $ rg -n 'test_review_findings_cascade|test_runner_stop_triggers\.py|test_runner_stop_triggers\b|TheRowWalkIsSharedWithTheRetirementGate|re-measured in' agent_workflows/runner_shared.py agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py tests/test_agy_runipd_cli.py
    agent_workflows/agy_runipd.py
    461:# API-symmetry contract asserted by `tests/test_review_findings_cascade.py::SharedPredicateTests`
    1853:    # (tests/test_review_findings_cascade.py::test_no_runner_to_runner_import) stayed meaningful for
    1900:# backlog `cnwy8g` tracks by three (56 -> 53, re-measured in
    4126:    # IDENTICAL: `tests/test_runner_stop_triggers.py` regexes `subcommands = \{(.*?)\}` out of BOTH
    4131:    # `tests/test_runner_stop_triggers.py`, which pins all three equal.

    tests/test_agy_runipd_cli.py
    1875:    because `tests/test_runner_stop_triggers.py` regexes both source files.

    agent_workflows/oc_runipd.py
    5270:    # KEEP THIS AS AN INLINE SET LITERAL. `test_runner_stop_triggers` asserts structurally, by regexing
    5290:    # `tests/test_runner_stop_triggers.py`; all three must change together.

    agent_workflows/runner_shared.py
    13572:    `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`, because a
    23715:    `tests/test_review_findings_cascade.py::SharedPredicateTests` asserts the attribute exists on that
    28295:    without `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` having to be
    ```
    Site list with enclosing symbols:
    - `agent_workflows/agy_runipd.py:461`: module comment above `_findings_block_reason` import/re-export
    - `agent_workflows/agy_runipd.py:1853`: `enforce_dependency_preflight` comment
    - `agent_workflows/agy_runipd.py:1900`: `parse_plan_file` import comment block
    - `agent_workflows/agy_runipd.py:4126, 4131`: `main` implicit-start shim comment
    - `tests/test_agy_runipd_cli.py:1875`: `AgyVerbosityFlagTests` class docstring
    - `agent_workflows/oc_runipd.py:5270, 5290`: `main` implicit-start shim comment
    - `agent_workflows/runner_shared.py:13572`: `parse_plan_file` docstring
    - `agent_workflows/runner_shared.py:23715`: `_findings_block_reason` docstring
    - `agent_workflows/runner_shared.py:28295`: `resolve_prior_lane` docstring
    No drift from F-01..F-03.

    Command (b):
    ```
    $ ls tests/test_review_findings_cascade.py tests/test_runner_stop_triggers.py tests/test_orchestrator_probe_cache.py
    ls: cannot access 'tests/test_review_findings_cascade.py': No such file or directory
    ls: cannot access 'tests/test_runner_stop_triggers.py': No such file or directory
    ls: cannot access 'tests/test_orchestrator_probe_cache.py': No such file or directory
    ```
    All three absent.

    Command (c):
    ```
    $ git log --oneline -S 'class SharedPredicateTests' -- tests/
    19313eed7 test: trim test suite from 9,136 to under 2,000 tests
    da55651d3 feat(lane): materialize lane inputs by copy with a sealed manifest, localize attachments, and refuse a dirty tracked base
    d793058fb feat(revgate): block dependents of a plan with unresolved gating findings

    $ git log --oneline -S 'def test_no_runner_to_runner_import' -- tests/
    d27e5eac8 test: tabulate ten more over-sliced suites (781 -> 460 tests)
    d793058fb feat(revgate): block dependents of a plan with unresolved gating findings

    $ git log --oneline -S 'class TheRowWalkIsSharedWithTheRetirementGate' -- tests/
    19313eed7 test: trim test suite from 9,136 to under 2,000 tests
    b816200c7 feat(orchprobe): cache an orchestrator probe verdict against a content digest (8tgg6g)

    $ git log --oneline -S 'def _shim_set' -- tests/
    19313eed7 test: trim test suite from 9,136 to under 2,000 tests
    ba4f205b2 test: replace the signal-safety, sandbox and delegation pins with behavior (52 -> 30)
    ```
    Deleting commits confirmed: `SharedPredicateTests` in `19313eed7`; `test_no_runner_to_runner_import` folded in `d27e5eac8` and deleted in `19313eed7`; `TheRowWalkIsSharedWithTheRetirementGate` in `19313eed7`; `_shim_set` in `19313eed7`.

    Command (d):
    ```
    $ python3 -c "
    import ast

    def get_subcommands(filepath):
        with open(filepath) as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'main':
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id == 'subcommands':
                                if isinstance(stmt.value, ast.Set):
                                    return sorted([elt.value for elt in stmt.value.elts if isinstance(elt, ast.Constant)])
        return None

    oc = get_subcommands('agent_workflows/oc_runipd.py')
    agy = get_subcommands('agent_workflows/agy_runipd.py')
    print('oc_runipd:', oc)
    print('agy_runipd:', agy)
    print('Equal:', oc == agy)
    "
    oc_runipd: ['--help', '-h', 'audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']
    agy_runipd: ['--help', '-h', 'audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']
    Equal: True
    ```
    Both printed sets are identical.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted summary line and `FAILED` lines of the bare `python3 -m pytest` with a statement that no flags were added, pasted summary line and `FAILED` lines of the narrowed run, and `git rev-parse --short HEAD` output.
  - Observed evidence:
    Base commit:
    ```
    $ git rev-parse --short HEAD
    e6dd349aa
    ```
    Narrowed baseline run:
    ```
    $ python3 -m pytest tests/test_agy_runipd_cli.py tests/test_oc_runipd.py -o addopts=""
    ======================= 242 passed in 125.60s (0:02:05) ========================
    ```
    FAILED lines: none (0 failed).

    Bare `python3 -m pytest` baseline run (no flags added):
    ```
    $ python3 -m pytest
    7615 passed, 2 skipped, 3 warnings in 1081.55s (0:18:01)
    ```
    FAILED lines: none (0 failed).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the three rewritten `runner_shared.py` passages QUOTED IN FULL, each naming its deleting commit and containing no present-tense claim that a test asserts/enforces/requires; plus `git diff -U0 agent_workflows/runner_shared.py` showing no hunk touches a `test_no_new_module_level_first_party_import_in_runner_shared` site.
  - Observed evidence:
    Passage (a) (`_findings_block_reason` docstring):
    ```python
        one wrapper in front of one predicate. `agy_runipd` keeps the NAME bound (a re-export) for
        compatibility so both hosts still call one shared predicate. The contract test
        (`tests/test_review_findings_cascade.py::SharedPredicateTests`, a source-substring code pin) was
        deleted in `19313eed7` and will not return under P16, and nothing currently requires the name to stay
        bound.
    ```
    Passage (b) (`resolve_prior_lane` docstring):
    ```python
        implementation; what changes is WHERE it lives, and the shared module is a place agy may import
        without a runner-to-runner import. The substring guard
        (`tests/test_review_findings_cascade.py::test_no_runner_to_runner_import`) was retired (`d27e5eac8`
        folded it into `SharedPredicateTests`, deleted in `19313eed7`), so the no-runner-to-runner-import
        rule is now held by review.
    ```
    Passage (c) (`parse_plan_file` docstring):
    ```python
        functions that need them. No live test enforces this function-local convention (the historically cited
        `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`, deleted in `19313eed7`,
        was a row-walk spy test and never enforced imports), because a
        module-level import here changes the import graph for BOTH host drivers and for the twelve other
        modules that import this one.
    ```
    Each names its deleting commit (`19313eed7`) and makes no present-tense assertion claim.
    `git diff -U0 agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 42155f02b..bc2763f04 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -13571,2 +13571,3 @@ def parse_plan_file(path: Path, repo: Path) -> PlanRecord | None:
    -    functions that need them - a rule enforced by
    -    `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`, because a
    +    functions that need them. No live test enforces this function-local convention (the historically cited
    +    `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`, deleted in `19313eed7`,
    +    was a row-walk spy test and never enforced imports), because a
    @@ -23714,3 +23715,4 @@ def _findings_block_reason(repo: Path, dep: str) -> str | None:
    -    one wrapper in front of one predicate. `agy_runipd` keeps the NAME bound (a re-export) because
    -    `tests/test_review_findings_cascade.py::SharedPredicateTests` asserts the attribute exists on that
    -    module and that its source names `subject_gating_blocks`; the import line satisfies both.
    +    one wrapper in front of one predicate. `agy_runipd` keeps the NAME bound (a re-export) for
    +    compatibility so both hosts still call one shared predicate. The contract test
    +    (`tests/test_review_findings_cascade.py::SharedPredicateTests`, a source-substring code pin) was
    +    deleted in `19313eed7` and will not return under P16, and nothing currently requires the name to stay
    +    bound.
    @@ -28295,2 +28297,4 @@ def resolve_prior_lane(
    -    without `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` having to be
    -    satisfied on a technicality.
    +    without a runner-to-runner import. The substring guard
    +    (`tests/test_review_findings_cascade.py::test_no_runner_to_runner_import`) was retired (`d27e5eac8`
    +    folded it into `SharedPredicateTests`, deleted in `19313eed7`), so the no-runner-to-runner-import
    +    rule is now held by review.
    ```
    No hunk touches a `test_no_new_module_level_first_party_import_in_runner_shared` site.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the three rewritten `agy_runipd.py` non-shim passages QUOTED IN FULL; the `56 -> 53` numbers still present; no "still refuses" or "requires this module to CARRY" live claim remains.
  - Observed evidence:
    Passage (a) (module comment above `_findings_block_reason` re-export):
    ```python
    # `_findings_block_reason` is bound HERE ON PURPOSE as a harmless compatibility re-export so both
    # drivers carry the attribute. The historical cross-driver API-symmetry contract asserted by
    # `tests/test_review_findings_cascade.py::SharedPredicateTests` (which read this module's source for
    # `subject_gating_blocks`) was a source-substring code pin deleted in `19313eed7` that will not return
    # under P16; no live test requires this module to carry the attribute, but keeping the re-export
    # preserves backward compatibility without reimplementing the severity comparison.
    ```
    Passage (b) (`enforce_dependency_preflight` comment):
    ```python
        # THERE IS NO LONGER A RUNNER-TO-RUNNER IMPORT HERE AT ALL (runnerlayer Order 02 `1f7xno`,
        # backlog `cnwy8g`). This used to read `from agent_workflows.oc_runipd import
        # enforce_dependency_preflight`, and it carried a long note explaining that the SYMBOL-LEVEL
        # spelling was chosen over the module-alias spelling so revgate's substring guard
        # (tests/test_review_findings_cascade.py::test_no_runner_to_runner_import) stayed meaningful for
        # the blanket-dependency case it targets. That guard no longer exists (retired in `d27e5eac8` and
        # `19313eed7`). That note was an accommodation to a coupling that no longer exists: the preflight
        # is DEFINED in `runner_shared` now, so this import crosses no host-to-host boundary and the
        # spelling carries no significance beyond style.
    ```
    Passage (c) (`parse_plan_file` import-block comment):
    ```python
    # THE THREE READERS COME FROM `runner_shared` NOW, NOT FROM `oc_runipd`. They moved with
    # `parse_plan_file`, which closes over them, and the redirection REDUCES the oc-to-agy import coupling
    # backlog `cnwy8g` tracks by three (56 -> 53; the re-measuring test in
    # `tests/test_orchestrator_probe_cache.py` was an exact oc-to-agy import-count baseline deleted with that
    # file in `19313eed7`, so the count is a historical measurement, not a live assertion). `_read_kind`'s
    # old import comment here said the reader had to stay in `oc_runipd` "because moving it means moving
    # `_KIND_RE` and the whole front-matter reader family with it, which is `cnwy8g`'s job"; moving
    # `parse_plan_file` required exactly that, so it was done, and `_KIND_RE`/`_PLAN_FILENAME_RE` moved
    # too rather than being left as duplicate constants.
    ```
    The `56 -> 53` numbers are present; "requires this module to CARRY" and "still refuses" claims are removed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the rewritten `agy_runipd.main` shim comment QUOTED IN FULL, showing the per-verb misfire reasons intact, `19313eed7`, P16 or "code pin", and `2ohbkj`; and pasted `aw backlog` evidence (e.g. `ls .aw/records/backlog/open/ | grep 2ohbkj`) that `2ohbkj` resolves to a live item.
  - Observed evidence:
    Rewritten `agy_runipd.main` shim comment:
    ```python
        # THE IMPLICIT-START SHIM. Any first token NOT in this set is treated as a selector and gets
        # `start` prepended. runstop 71vjbn (E-03): `"stop"` MUST be listed here. This shim lives in
        # `main()` and NOT in `build_parser()`, so adding the `stop` subparser alone does not cover it -
        # `stop <run-id> --now` would be rewritten to `start stop <run-id> --now`, i.e. it would LAUNCH a
        # run with the literal selector `stop`. That is a silent misfire in the exact opposite direction
        # of the operator's intent. The behavioral `stop` not-rewritten tests were deleted in `19313eed7`;
        # restoring that coverage is tracked by backlog `2ohbkj`.
        #
        # streamfmt (mm6wuz) E-06 / OQ-02 (resolved): `"-v"` and `"--version"` USED TO BE LISTED HERE and
        # were REMOVED, in lockstep with the oc twin. `-v` now means `--verbose`, and while it sat in this
        # set a LEADING `-v` was treated as a subcommand and never prefixed with `start`. The removed
        # `--version` entry guarded a flag NEITHER driver registers. THE TWO DRIVERS' SETS MUST STILL STAY
        # IDENTICAL and every hazardous verb MUST still be listed. The structural guard that read this set
        # from source (`tests/test_runner_stop_triggers.py`) was a code pin deleted in `19313eed7` that will
        # not return under P16; until behavioral coverage returns under `2ohbkj`, lockstep of the two sets
        # is held by review.
        # integpath-04 (`rl67b0`) E-02: `"integrate"` MUST be listed here for the SAME reason `stop` must -
        # an unregistered first token becomes `start <token>`, so `integrate <id6>` would LAUNCH A RUN with
        # `integrate` as a selector. Added in lockstep with the oc twin. Unlike `stop` and `audit`, `integrate`
        # alone is still driven through the real `main` in this driver's tests (`tests/test_agy_runipd_cli.py`,
        # the `agy_runipd.main(["integrate", ...])` calls), which exercises its not-rewritten path, while
        # `stop` and `audit` have no such coverage.
        # reverify-01 (`mp289j`) E-05: `"audit"` MUST be listed here for the SAME measured reason `stop` and
        # `integrate` must, and it must match the oc copy token for token. An unregistered first token is
        # rewritten into `start <token>`, so `audit <id6>` would LAUNCH A RUN with `audit` as a selector.
        # Restoring coverage for `stop` and `audit` is tracked by backlog `2ohbkj`.
    ```
    Backlog evidence:
    ```
    $ ls .aw/records/backlog/open/ | grep 2ohbkj
    20261011-2ohbkj-01-2ohbkj-restore-bare-verb-not-rewritten-tests.backlog.md
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the rewritten `oc_runipd.main` shim comment QUOTED IN FULL; then the AST comparison script and its output for `agent_workflows/runner_shared.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/oc_runipd.py`, and `tests/test_agy_runipd_cli.py` against `git show <E-02 base commit>:<path>` with module/class/function docstrings stripped and `ast.dump(..., include_attributes=False)`, printing EQUAL for all four.
  - Observed evidence:
    Rewritten `oc_runipd.main` shim comment:
    ```python
        # THE IMPLICIT-START SHIM. Any first token NOT in this set is treated as a selector and gets
        # `start` prepended. runstop 71vjbn (E-03): `"stop"` MUST be listed here. This shim lives in
        # `main()` and NOT in `build_parser()`, so adding the `stop` subparser alone does not cover it -
        # `stop <run-id> --now` would be rewritten to `start stop <run-id> --now`, i.e. it would LAUNCH a
        # run with the literal selector `stop`. That is a silent misfire in the exact opposite direction
        # of the operator's intent. The behavioral tests asserting the bare form is not rewritten were
        # deleted in `19313eed7`; restoring that coverage for `stop` and `audit` is tracked by backlog `2ohbkj`.
        # KEEP THIS AS AN INLINE SET LITERAL. The inline literal is kept for symmetry with the agy twin and
        # because no test now constrains its form. The historical structural guard (`tests/test_runner_stop_triggers.py`),
        # which regexed `subcommands = \{(.*?)\}` in both drivers' sources, was a code pin deleted in `19313eed7`
        # that will not return under P16; until behavioral coverage returns under `2ohbkj`, lockstep of the two sets
        # is held by review.
        #
        # streamfmt (mm6wuz) E-05 / OQ-02 (resolved): `"-v"` and `"--version"` USED TO BE LISTED HERE and
        # were REMOVED. `-v` now means `--verbose` on `start` and `resume`, and while it sat in this set a
        # LEADING `-v` was treated as a subcommand and never prefixed with `start`, so `aw oc run -v SEL`
        # failed with `invalid choice: 'SEL'` while `aw oc run -vv SEL` (not in the set) failed
        # differently with `unrecognized arguments: -vv`. The reservation also guarded a `--version` flag
        # NEITHER driver registers (measured: `parse_args(["--version"])` exits 2 with
        # `unrecognized arguments`), so it protected nothing. If a real `--version` is ever added, add
        # BOTH tokens back to BOTH drivers together and give `--verbose` the long spelling only; the two
        # sets must stay IDENTICAL and lockstep is held by review.
        # integpath-04 (`rl67b0`) E-02: `"integrate"` MUST be listed here for the SAME measured reason
        # `stop` must: an unregistered first token is rewritten into `start <token>`, so
        # `integrate <id6>` would LAUNCH A RUN with `integrate` as a selector, which is the opposite of
        # the operator's intent and is silent. Added in lockstep with the agy twin. Unlike `stop` and
        # `audit`, `integrate` is still driven through the real `main` in `tests/test_oc_runipd.py` (e.g.
        # `driver.main(["integrate", "mm6wuz"])`), which exercises its not-rewritten path, while `stop`
        # and `audit` have no such coverage.
        # reverify-01 (`mp289j`) E-05: `"audit"` MUST be listed here for the SAME measured reason `stop`
        # and `integrate` must. An unregistered first token is rewritten into `start <token>`, so
        # `audit <id6>` would LAUNCH A RUN with `audit` as a selector - which for this verb is worse than
        # for the other two, because an operator asking for a cheap second opinion on FINISHED work would
        # instead pay for a full execution attempt against an already-executed plan. Neither `stop` nor
        # `audit` currently has live coverage driving the bare form through `main`, which is tracked by `2ohbkj`.
    ```
    AST comparison script:
    ```python
    import ast
    import subprocess

    def strip_docstrings(node):
        for n in ast.walk(node):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if n.body and isinstance(n.body[0], ast.Expr):
                    if isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
                        n.body = n.body[1:]
        return node

    base_commit = 'e6dd349aa'
    paths = [
        'agent_workflows/runner_shared.py',
        'agent_workflows/agy_runipd.py',
        'agent_workflows/oc_runipd.py',
        'tests/test_agy_runipd_cli.py'
    ]

    for p in paths:
        with open(p, 'r') as f:
            curr_src = f.read()
        base_src = subprocess.check_output(['git', 'show', f'{base_commit}:{p}'], text=True)

        curr_ast = strip_docstrings(ast.parse(curr_src, filename=p))
        base_ast = strip_docstrings(ast.parse(base_src, filename=p))

        curr_dump = ast.dump(curr_ast, include_attributes=False)
        base_dump = ast.dump(base_ast, include_attributes=False)

        if curr_dump == base_dump:
            print(f'{p}: EQUAL')
        else:
            print(f'{p}: NOT EQUAL')
    ```
    Script output:
    ```
    agent_workflows/runner_shared.py: EQUAL
    agent_workflows/agy_runipd.py: EQUAL
    agent_workflows/oc_runipd.py: EQUAL
    tests/test_agy_runipd_cli.py: EQUAL
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the rewritten `AgyVerbosityFlagTests` docstring QUOTED IN FULL; post-edit `rg -n 'test_review_findings_cascade|test_runner_stop_triggers\.py|test_runner_stop_triggers\b|TheRowWalkIsSharedWithTheRetirementGate' agent_workflows/runner_shared.py agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py tests/test_agy_runipd_cli.py` output with every hit shown inside a retirement statement; E-01(d) re-run output; and suite parity: the post-edit FAILED node-id sets of the bare `python3 -m pytest` and the narrowed run pasted beside V-02's baseline sets, showing no node id that fails only after the edit (a post-only failure is re-run singly once to rule out a load-sensitive flake, output pasted), or any difference attributed to a named intervening commit after re-baselining.
  - Observed evidence:
    Rewritten `AgyVerbosityFlagTests` docstring:
    ```python
    class AgyVerbosityFlagTests(unittest.TestCase):
        """streamfmt (mm6wuz) E-06/V-06: `-v` parses IDENTICALLY to the oc driver.

        The property under test is PARITY, so every case here mirrors
        `tests/test_oc_runipd_cli.py::VerbosityFlagTests`. A leading `-v` used to be swallowed by the
        implicit-start `subcommands` set in this driver too; both drivers' sets were changed together
        to keep the drivers identical (the regexing guard `tests/test_runner_stop_triggers.py` was
        deleted in `19313eed7`).
        """
    ```
    Post-edit `rg` output showing every hit inside a retirement statement:
    ```
    $ rg -n 'test_review_findings_cascade|test_runner_stop_triggers\.py|test_runner_stop_triggers\b|TheRowWalkIsSharedWithTheRetirementGate' agent_workflows/runner_shared.py agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py tests/test_agy_runipd_cli.py
    agent_workflows/runner_shared.py
    13572:    `tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate`, deleted in `19313eed7`,
    23717:    (`tests/test_review_findings_cascade.py::SharedPredicateTests`, a source-substring code pin) was
    28299:    (`tests/test_review_findings_cascade.py::test_no_runner_to_runner_import`) was retired (`d27e5eac8`

    agent_workflows/agy_runipd.py
    462:# `tests/test_review_findings_cascade.py::SharedPredicateTests` (which read this module's source for
    1852:    # (tests/test_review_findings_cascade.py::test_no_runner_to_runner_import) stayed meaningful for
    4130:    # from source (`tests/test_runner_stop_triggers.py`) was a code pin deleted in `19313eed7` that will

    agent_workflows/oc_runipd.py
    5272:    # because no test now constrains its form. The historical structural guard (`tests/test_runner_stop_triggers.py`),

    tests/test_agy_runipd_cli.py
    1875:    to keep the drivers identical (the regexing guard `tests/test_runner_stop_triggers.py` was
    ```
    E-01(d) re-run output:
    ```
    oc_runipd: ['--help', '-h', 'audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']
    agy_runipd: ['--help', '-h', 'audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']
    Equal: True
    ```
    Suite parity:
    - Narrowed run baseline: `242 passed in 125.60s (0:02:05)` | FAILED node-id set: `set()` (empty)
    - Narrowed run post-edit: `242 passed in 226.90s (0:03:46)` | FAILED node-id set: `set()` (empty)
    - Bare run baseline: `7615 passed, 2 skipped, 3 warnings in 1081.55s (0:18:01)` | FAILED node-id set: `set()` (empty)
    - Bare run post-edit: `7615 passed, 2 skipped, 3 warnings in 724.14s (0:12:04)` | FAILED node-id set: `set()` (empty)
    Zero failed node ids in either run; exact parity.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: E-03 and E-04 each enumerate three sites (lint advisory `IPD-Z602` on E-04), but every site is a prose-only rewrite in ONE file applying ONE rule (retire a citation of a deleted test, name the commit, keep the design point), verified by one V-item quoting the passages; splitting per site would add items without adding an independent test surface.

The plan must not execute before explicit human approval recorded through `aw ipd set approved`.

EXECUTION CONTRACT. Commit only the declared paths through `aw commit <plan> -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push. Verify the staged set with `git diff --cached --name-only` before committing. Paste actual command output for every measurement and suite claim. The one STOP condition is E-01(d) showing the two shim sets differ; a drifted site count is expected and is narrowed, not a stop. Plan `dtelfb` edits other paragraphs of `runner_shared.py`; if a site here has been concurrently changed in a way that cannot be safely combined, stop and report.

POST-GATE LIFECYCLE MOVE. After every `V-*` passes with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is tooled: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `3tov52` carries no `- Blocks-Release:`, so no gate is inherited; this plan is its sole carrier.
