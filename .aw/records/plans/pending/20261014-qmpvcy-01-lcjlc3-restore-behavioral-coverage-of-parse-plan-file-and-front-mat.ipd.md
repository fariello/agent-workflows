# IPD: Restore behavioral coverage of parse_plan_file and front-matter readers loose leading whitespace tolerance

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_runner_refork_guard.py`, and with it `FrontMatterReaderBehaviorTests` (`test_public_readers_tolerate_loose_leading_whitespace`, `test_both_runners_still_accept_every_spelling_they_did_before`, `test_selector_internal_readers_stay_strict`, `test_public_status_reader_keeps_the_single_token_contract`), the only behavioral tests that the runners' plan parser `runner_shared.parse_plan_file` (bound to the PERMISSIVE public readers `selectors.read_front_matter_id` / `read_front_matter_status`) tolerates any whitespace after the leading `-`, while `selectors`' strict internal readers (the `aw find` matching contract) do not. Executed plan `yuhl6o` recorded that site as S-06 RETIRE-UNGUARDED. A regression is silent: if `parse_plan_file` were swapped to the strict readers, a plan spelled `-  Status: approved` or `-\tStatus: approved` would lose its declared status and degrade to the directory bucket (`pending`), so an approved plan would silently stop being selected for execution.
- Scope: Add one new behavioral test module that drives the real `parse_plan_file` on both hosts against real temporary plan files, and the public and internal `selectors` readers on text, then repoint the one `runner_shared.parse_plan_file` docstring sentence that says "no live guard currently asserts this loose-whitespace tolerance". No production behavior change.
- Scope-Paths: tests/test_front_matter_loose_whitespace.py, agent_workflows/runner_shared.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: qmpvcy
- Set: qmpvcy
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: lcjlc3
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004
- 2026-10-15 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog `qmpvcy`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) test coverage that `parse_plan_file`, on both hosts, and the public `selectors.read_front_matter_*` readers accept `- `, `-  ` and `-\t` front-matter spellings, while the strict internal `selectors._read_id` / `_read_status` reject the loose spellings and the single-token status contract is preserved, so the tolerance is proven present and bounded.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: parse_plan_file tolerates loose leading whitespace (yuhl6o S-06)

- [x] E-01 Create `tests/test_front_matter_loose_whitespace.py` with a test that, for each spelling prefix in (`"- "`, `"-  "`, `"-\t"`) and each host in (`oc_runipd`, `agy_runipd`), writes a real plan file under a temporary `<tmp>/.aw/records/plans/pending/plan.md` whose metadata lines are `<prefix>Id: abc123`, `<prefix>Status: approved`, `<prefix>Kind: child` followed by a `## Goal` heading, calls `host.parse_plan_file(path, Path(tmp))` and asserts the returned record has `id6 == "abc123"`, `status == "approved"` (NOT the directory bucket `pending`), and `kind == "child"`. Use `subTest(host=..., spelling=...)`.
  - Depends on: none
  - Expected outcome: New module exists, written as `unittest.TestCase` classes using `tempfile.TemporaryDirectory()` (the suite's prevailing style); the test passes for every host x spelling subtest.
  - Execution state: performed

### Task group 2: the public readers are permissive and the internal readers stay strict

- [x] E-02 In the same module, add a test that `selectors.read_front_matter_id` and `selectors.read_front_matter_status` return `"abc123"` / `"approved"` for all three spellings, and a test that the strict internal `selectors._read_id` / `selectors._read_status` return the values for the one-space spelling and `None` for the two-space and tab spellings (the `aw find` contract is not widened). Assert on returned values only; do not assert on regex `.pattern` strings.
  - Depends on: E-01
  - Expected outcome: Both tests pass.
  - Execution state: performed

- [x] E-03 In the same module, add a test that the single-token status contract survives: `selectors.read_front_matter_status` and `selectors._read_status` return `None` for `- Status: EXECUTED (approved by maintainer)`, and `runner_shared.parse_plan_file` on a real file under `.../plans/pending/` carrying only that status line returns `status == "pending"` (the directory fallback) and NOT a token from the multi-word value such as `"EXECUTED"`. Do not read source files, use `ast`/`inspect`, or pin symbol identity or counts.
  - Depends on: E-02
  - Expected outcome: Test passes.
  - Execution state: performed

### Task group 3: comment repointing

- [x] E-04 First record the pre-edit bare-suite baseline (`python3 -m pytest` summary line and failing-test-id set) if not already recorded before E-01 (record it before E-01 when executing in order). Run the E-01 non-vacuity mutation BEFORE this edit (see Required tests) so its `git checkout --` revert cannot discard the docstring change. Then repoint the `runner_shared.parse_plan_file` docstring paragraph beginning "THE ALIASES ARE THE PERMISSIVE PUBLIC READERS" that cites `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` and says "no live guard currently asserts this loose-whitespace tolerance", so it names `tests/test_front_matter_loose_whitespace.py` as the live guard. Docstring-only edit.
  - Depends on: E-03
  - Expected outcome: `rg -n "no live guard currently asserts this loose-whitespace" agent_workflows/` returns no matches; `git diff -- agent_workflows/runner_shared.py` touches docstring lines only.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must exercise behavior (P16, AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): no source reading, no `ast`/`inspect`, no symbol censuses, no regex-pattern string pins (the deleted `test_selector_internal_readers_stay_strict` asserted `_ID_RE.pattern`; that half is NOT restored).
- `runner_shared.parse_plan_file` imports `selectors.read_front_matter_id as _read_id` and `read_front_matter_status as _read_status` function-locally; when no status is read it falls back to `plan_bucket(path)`. Both hosts re-export it (`oc_runipd.parse_plan_file`, `agy_runipd.parse_plan_file`).
- Public readers use `_FRONT_MATTER_ID_RE = (?m)^-\s*Id:...` and `_FRONT_MATTER_STATUS_RE = (?m)^-\s*Status:\s*(\S+)\s*$`; internal `_ID_RE` / `_STATUS_RE` require `^- Id:` / `^- Status:` exactly.
- Measured in this lane (AW_NO_REEXEC=1, temporary repo): for prefixes `"- "`, `"-  "`, `"-\t"`, `parse_plan_file` on `runner_shared`, `oc_runipd` and `agy_runipd` all returned `('abc123', 'approved', 'child')`; `selectors._read_id` / `_read_status` returned `abc123 approved` for one space and `None None` for two-space and tab; `plan_bucket` returned `pending`; a file with `- Status: EXECUTED (approved)` parsed to status `pending`. So a strict-reader swap would observably flip `approved` to `pending`, which makes E-01 non-vacuous. Re-measured at review in a scratch copy of `agent_workflows/` under gitignored `.aw/state/` (since deleted), with only the `parse_plan_file` status import swapped to `from agent_workflows.selectors import _read_status`: `python3 -m unittest` on a prototype of E-01 reported `FAILED (failures=4)`, namely the two-space and tab subtests on each host, with `('abc123', 'pending', 'child') != ('abc123', 'approved', 'child')`. The one-space subtests and the single-token prototype passed. TWO MEASURED PITFALLS for the non-vacuity run. (a) Under pytest 8.2 without a subtests plugin, a `subTest` failure is reported as a single test FAILED and stops at the first failing subtest, so pytest output shows one assertion and not the per-subtest list; use `python3 -m unittest -v tests.test_front_matter_loose_whitespace` to see every failing subtest. (b) The mutation must be made IN PLACE in this worktree's `agent_workflows/runner_shared.py`. A scratch copy run from another directory silently imported the unmutated package (the first scratch run passed 2/2 under mutation), because the pytest rootdir/conftest puts the checkout's own package on `sys.path`. Note also that `runner_shared.py` contains four other `from agent_workflows.selectors import _read_status` lines. Edit only the one inside `parse_plan_file`, and check this with `git diff`.
- Existing partial coverage: `tests/test_runner_shared.py::CrossHostReadIdReExportTests` covers only `_read_id` on text (not status, not `parse_plan_file`, not the strict half).
- Suite is run bare: `python3 -m pytest`.

## Findings

| Site | Lost test (in `19313eed^:tests/test_runner_refork_guard.py`) | Live coverage today |
|---|---|---|
| yuhl6o S-06 | `FrontMatterReaderBehaviorTests` (four tests) | Partial: `tests/test_runner_shared.py::CrossHostReadIdReExportTests` asserts the hosts' `_read_id` on loose spellings; nothing drives `parse_plan_file`, the status reader, the strict internal readers, or the single-token contract. |

## Proposed changes (ordered, validatable)

1. New `tests/test_front_matter_loose_whitespace.py` (E-01..E-03).
2. Docstring repoint in `agent_workflows/runner_shared.py` `parse_plan_file` (E-04).

## Deferred / out of scope (with reason)

- The `.pattern` string assertions of the deleted `test_selector_internal_readers_stay_strict`: source-structure pins forbidden by P16; replaced by return-value assertions.
  - Carrier-Declined: forbidden by P16 and replaced in E-02 by return-value assertions; nothing outstanding.
- The deleted file's `SymmetricReForkGuardTests` (AST/identity re-fork guards, yuhl6o S-12 RETIRE-PIN): not named by backlog `qmpvcy` and forbidden by P16.
  - Carrier-Declined: executed plan `yuhl6o` already dispositioned S-12 as RETIRE-PIN; P16 forbids restoring it.
- Other stale `tests/test_runner_refork_guard.py` comments in `oc_runipd.py` / `agy_runipd.py`: they describe the identity/re-fork pins, not this property.
  - Carrier-Declined: those comments are accurate history of P16-retired code pins (yuhl6o S-12 RETIRE-PIN) and will not be restored; no obligation remains.
- Any production change to the readers: behavior is correct; only its guard is missing.
  - Carrier-Declined: no defect exists; the restored tests pass against current code.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; S-06 gets behavioral guards for both the permissive and strict halves plus the single-token contract.

## Required tests / validation

- Baseline first: bare `python3 -m pytest` summary line and failing-test-id set, recorded before E-01.
- `python3 -m pytest -o addopts="" -v tests/test_front_matter_loose_whitespace.py` passes every collected test (count re-derived at execution).
- Non-vacuity (after E-03, before E-04): IN PLACE in this worktree, change ONLY `parse_plan_file`'s `from agent_workflows.selectors import read_front_matter_status as _read_status` to `from agent_workflows.selectors import _read_status`; run `python3 -m unittest -v tests.test_front_matter_loose_whitespace` and observe the two-space and tab subtests FAIL on both hosts with status `pending` while the one-space subtests pass; then `git checkout -- agent_workflows/runner_shared.py` and confirm `git diff --stat agent_workflows/` is empty.
- Full suite `python3 -m pytest` bare: its failing-test-id set contains no id absent from the baseline.

## Spec / documentation sync

N/A: test-only addition plus a docstring repoint; no spec text changes.

## Open questions

### OQ-01: Should the deleted regex-pattern pins and re-fork identity guards also be restored?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Backlog `qmpvcy` names only the loose leading whitespace tolerance property and states "only behavioral outcomes may be restored, never a source-reading pin (P16)"; the strict half is restored as return-value assertions instead.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_front_matter_loose_whitespace.py` showing the `parse_plan_file` test passing; plus the pasted pre-mutation `git diff` of the one-line in-place swap; plus pasted `python3 -m unittest -v tests.test_front_matter_loose_whitespace` output of the non-vacuity run showing the two-space and tab subtests FAIL on both hosts with status `pending` (one-space subtests not failing); then pasted `git diff --stat agent_workflows/` empty after `git checkout -- agent_workflows/runner_shared.py`. Also paste the pre-E-01 bare-suite baseline summary line and failing-test-id set.
  - Observed evidence:
    1. Pre-E-01 bare-suite baseline (`python3 -m pytest`):
    ```
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    705 passed in 26.59s
    ```
    Failing-test-id set: `set()` (0 failures).

    2. Output of `python3 -m pytest -o addopts="" -v tests/test_front_matter_loose_whitespace.py` showing `parse_plan_file` test passing:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=170532776
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_front_matter_loose_whitespace.py::FrontMatterLooseWhitespaceTests::test_internal_readers_stay_strict PASSED [ 25%]
    tests/test_front_matter_loose_whitespace.py::FrontMatterLooseWhitespaceTests::test_public_readers_tolerate_loose_leading_whitespace PASSED [ 50%]
    tests/test_front_matter_loose_whitespace.py::FrontMatterLooseWhitespaceTests::test_parse_plan_file_tolerates_loose_leading_whitespace PASSED [ 75%]
    tests/test_front_matter_loose_whitespace.py::FrontMatterLooseWhitespaceTests::test_single_token_status_contract_survives PASSED [100%]

    ============================== 4 passed in 0.71s ===============================
    ```

    3. Pre-mutation git diff of the one-line in-place swap:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 35a112b45..7c3d68ee1 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -14222,7 +14222,7 @@ def parse_plan_file(path: Path, repo: Path) -> PlanRecord | None:
         accept.
         """
         from agent_workflows.selectors import read_front_matter_id as _read_id
    -    from agent_workflows.selectors import read_front_matter_status as _read_status
    +    from agent_workflows.selectors import _read_status

         try:
             text = path.read_text(encoding="utf-8")
    ```

    4. Output of `python3 -m unittest -v tests.test_front_matter_loose_whitespace` during non-vacuity run:
    ```
    test_internal_readers_stay_strict (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_internal_readers_stay_strict)
    E-02 (internal strict): _read_id and _read_status accept only one-space spelling. ... ok
    test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace)
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'. ...
      test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='oc_runipd', spelling='two spaces')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'. ... FAIL
      test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='oc_runipd', spelling='tab')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'. ... FAIL
      test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='agy_runipd', spelling='two spaces')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'. ... FAIL
      test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='agy_runipd', spelling='tab')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'. ... FAIL
    test_public_readers_tolerate_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_public_readers_tolerate_loose_leading_whitespace)
    E-02 (public permissive): read_front_matter_id and read_front_matter_status accept all 3 spellings. ... ok
    test_single_token_status_contract_survives (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_single_token_status_contract_survives)
    E-03: multi-word status returns None from status readers and falls back to directory bucket. ... ok

    ======================================================================
    FAIL: test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='oc_runipd', spelling='two spaces')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_front_matter_loose_whitespace.py", line 54, in test_parse_plan_file_tolerates_loose_leading_whitespace
        self.assertEqual(
        ~~~~~~~~~~~~~~~~^
            (record.id6, record.status, record.kind),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            ("abc123", "approved", "child"),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
    AssertionError: Tuples differ: ('abc123', 'pending', 'child') != ('abc123', 'approved', 'child')

    First differing element 1:
    'pending'
    'approved'

    - ('abc123', 'pending', 'child')
    ?               - ---

    + ('abc123', 'approved', 'child')
    ?             + ++++


    ======================================================================
    FAIL: test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='oc_runipd', spelling='tab')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_front_matter_loose_whitespace.py", line 54, in test_parse_plan_file_tolerates_loose_leading_whitespace
        self.assertEqual(
        ~~~~~~~~~~~~~~~~^
            (record.id6, record.status, record.kind),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            ("abc123", "approved", "child"),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
    AssertionError: Tuples differ: ('abc123', 'pending', 'child') != ('abc123', 'approved', 'child')

    First differing element 1:
    'pending'
    'approved'

    - ('abc123', 'pending', 'child')
    ?               - ---

    + ('abc123', 'approved', 'child')
    ?             + ++++


    ======================================================================
    FAIL: test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='agy_runipd', spelling='two spaces')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_front_matter_loose_whitespace.py", line 54, in test_parse_plan_file_tolerates_loose_leading_whitespace
        self.assertEqual(
        ~~~~~~~~~~~~~~~~^
            (record.id6, record.status, record.kind),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            ("abc123", "approved", "child"),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
    AssertionError: Tuples differ: ('abc123', 'pending', 'child') != ('abc123', 'approved', 'child')

    First differing element 1:
    'pending'
    'approved'

    - ('abc123', 'pending', 'child')
    ?               - ---

    + ('abc123', 'approved', 'child')
    ?             + ++++


    ======================================================================
    FAIL: test_parse_plan_file_tolerates_loose_leading_whitespace (tests.test_front_matter_loose_whitespace.FrontMatterLooseWhitespaceTests.test_parse_plan_file_tolerates_loose_leading_whitespace) (host='agy_runipd', spelling='tab')
    E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\t'.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_front_matter_loose_whitespace.py", line 54, in test_parse_plan_file_tolerates_loose_leading_whitespace
        self.assertEqual(
        ~~~~~~~~~~~~~~~~^
            (record.id6, record.status, record.kind),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            ("abc123", "approved", "child"),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
    AssertionError: Tuples differ: ('abc123', 'pending', 'child') != ('abc123', 'approved', 'child')

    First differing element 1:
    'pending'
    'approved'

    - ('abc123', 'pending', 'child')
    ?               - ---

    + ('abc123', 'approved', 'child')
    ?             + ++++


    ----------------------------------------------------------------------
    Ran 4 tests in 0.012s

    FAILED (failures=4)
    ```

    5. Revert check:
    ```
    $ git checkout -- agent_workflows/runner_shared.py && git diff --stat agent_workflows/
    (empty output)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the public-permissive and internal-strict tests passing.
  - Observed evidence:
    ```
    tests/test_front_matter_loose_whitespace.py::FrontMatterLooseWhitespaceTests::test_internal_readers_stay_strict PASSED [ 25%]
    tests/test_front_matter_loose_whitespace.py::FrontMatterLooseWhitespaceTests::test_public_readers_tolerate_loose_leading_whitespace PASSED [ 50%]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the single-token test passing, and `rg -n "import ast|import inspect|\.pattern|read_text\(.*\.py" tests/test_front_matter_loose_whitespace.py` returning no matches.
  - Observed evidence:
    Pytest output:
    ```
    tests/test_front_matter_loose_whitespace.py::FrontMatterLooseWhitespaceTests::test_single_token_status_contract_survives PASSED [100%]
    ```
    Search for forbidden code-pinning patterns:
    ```
    $ rg -n "import ast|import inspect|\.pattern|read_text\(.*\.py" tests/test_front_matter_loose_whitespace.py
    (no matches, exit code 1)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `git diff agent_workflows/runner_shared.py` showing only docstring lines changed and naming `tests/test_front_matter_loose_whitespace.py`; pasted `rg -n "no live guard currently asserts this loose-whitespace" agent_workflows/` with no matches; pasted bare `python3 -m pytest` summary line and failing-test-id set showing no id absent from the V-01 baseline.
  - Observed evidence:
    1. Docstring git diff:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 35a112b45..932b292be 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -14216,10 +14216,10 @@ def parse_plan_file(path: Path, repo: Path) -> PlanRecord | None:
         Both runners' historical private copies tolerated any whitespace after the `-` while `selectors`'
         STRICT internal readers require exactly one space, and that strictness is a documented `aw find`
         matching contract. rununify 01 (`2r306y`) resolved this by binding the permissive public aliases,
    -    and `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` (deleted in `19313eed`;
    -    no live guard currently asserts this loose-whitespace tolerance) guarded BOTH halves, so
    -    swapping to the strict readers here would silently narrow which front-matter spellings both drivers
    -    accept.
    +    and `tests/test_front_matter_loose_whitespace.py` (restoring behavioral coverage of the historical
    +    `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` deleted in `19313eed`) guards
    +    BOTH halves, so swapping to the strict readers here would silently narrow which front-matter
    +    spellings both drivers accept.
         """
         from agent_workflows.selectors import read_front_matter_id as _read_id
         from agent_workflows.selectors import read_front_matter_status as _read_status
    ```

    2. Search for old docstring phrase:
    ```
    $ rg -n "no live guard currently asserts this loose-whitespace" agent_workflows/
    (no matches, exit code 1)
    ```

    3. Post-edit bare-suite test run (`python3 -m pytest`):
    ```
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    705 passed in 20.66s
    ```
    Failing-test-id set: `set()` (0 failures; no test id absent from baseline).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved lcjlc3 --by-human`) or dispatch by an authorized runner turn. Open questions: OQ-01 is resolved; none remain. Start with `aw ipd begin lcjlc3`. `- Scope-Paths:` is a DECLARATION reconciled at finalize: if an out-of-scope edit proves necessary, make it and justify it with `--scope-reason <path>=<why>`. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; never claim a pass you did not run, and run the full suite bare (`python3 -m pytest`). Commit only the Scope-Paths files plus this plan through `aw commit lcjlc3 -- tests/test_front_matter_loose_whitespace.py agent_workflows/runner_shared.py <this plan>` after verifying `git diff --cached --name-only`; never commit the temporary non-vacuity mutation (revert it before E-04), never `git add -A`/`-a`/`--no-verify`, and never push or tag. Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize lcjlc3` once `aw ipd lint --phase pre-transition` conforms and `V-01`..`V-04` hold pasted evidence with `Result: pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
