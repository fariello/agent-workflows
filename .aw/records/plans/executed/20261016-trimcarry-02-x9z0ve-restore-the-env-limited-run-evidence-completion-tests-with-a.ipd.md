# IPD: Restore the env-limited run evidence completion tests with an id6 spec lookup

- Date: 2026-10-16
- Kind: child
- Concern: Rollup backlog `9qvfie` outcome 3 is `tests/test_run_evidence_completion.py` (84 removed functions) with audit verdict `replay-env-limited`. The backlog says replay "requires specialized multi-agent environment", but the findings row (`hpjj44` `## Verdicts`) records the real cause: `error-collect` (`StopIteration`) because the module-level `rglob('20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md')` finds nothing after spec `25kzda` was renamed onto the id6 grammar (commit `d6b2fa000`). Measured at authoring HEAD with only that one filename corrected: `3 failed, 81 passed in 5.01s`. So 81 behavioral tests of evidence capture, false-completion validators, completion predicates, the read-only `aw runs show|evidence|verify-ledger` CLI and the adversarial deception suite are unguarded today for a one-line fixture reason.
- Scope: Restore the module from `19313eed^` at its original path with (a) the spec lookup made id6-based (`rglob("*-25kzda-*.spec.md")`, the shape `tests/test_run_finding_spec_transcription.py` `locate_spec_25kzda` already uses) and (b) the three tests that encode deliberately superseded contracts updated to the current contract, each change citing the commit that superseded it. No production code changes.
- Scope-Paths: tests/test_run_evidence_completion.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 2
- Highest E allocated: 03
- Author: opencode
- Id: x9z0ve

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: x9z0ve verified (set trimcarry, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Return the 84-test run-evidence suite to the tree as a passing behavioral guard, so the `replay-env-limited` outcome is closed by restored coverage rather than left as an environment excuse.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Restore with an id6 spec lookup

- [x] E-01 Confirm `git ls-files tests/test_run_evidence_completion.py` prints nothing (if the module already exists, STOP and report: another change recreated it). Write `git show 19313eed^:tests/test_run_evidence_completion.py > tests/test_run_evidence_completion.py`, then replace the module-level `_SPEC_PATH = next(... .rglob("20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"))` with a lookup by id6 glob `*-25kzda-*.spec.md` that yields exactly one match or makes `_SPEC_PATH` a non-existent path (so the existing `if not _SPEC_PATH.exists(): self.skipTest(...)` guards in `TestRunFindingCodeVocabulary.setUp` and the 1552-region test still apply, rather than a collection-time `StopIteration`). Run `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_run_evidence_completion.py` and record the pass/fail list.
  - Depends on: none
  - Expected outcome: the module collects with no `StopIteration`, and every failure is one whose behavior a cited commit deliberately changed. At authoring and at review (F4) that set was exactly `TestRunFindingCodeVocabulary::test_abort_class_set_is_verbatim_from_spec_4_1`, `TestRunFindingCodeVocabulary::test_conditional_abort_is_not_reported_as_unconditional` and `TestRunCLI::test_aw_run_verify_ledger_corrupted_chain_exits_2` (81 passed); the counts are context, not the bar.
  - Execution state: performed

### Task group 2: Update the three superseded-contract tests

- [x] E-02 Update each of the three failures to the CURRENT contract, keeping it a behavioral assertion: (a) `test_aw_run_verify_ledger_corrupted_chain_exits_2`: assert `exit_code == run_cli.EXIT_CORRUPTED_LEDGER` (currently 5; superseded by `f1f1bb5d7` "Return EXIT_CORRUPTED_LEDGER from the three run readers that hardcode exit 2") and keep `assertIn("Broken chain", out)`. Rename it to `test_aw_run_verify_ledger_corrupted_chain_exits_corrupted_ledger`. (b) `test_abort_class_set_is_verbatim_from_spec_4_1`: keep the spec-parse equality and drop the hard-coded `len(...) == 6` (spec `25kzda` 4.1 was amended to a single class, "Corrupt run ledger", by `552cf7f01` "amend spec 25kzda failure policy to fix first with only corrupt ledger aborting (tb6lw3)"). The equality against the spec-parsed list is the outcome that matters. (c) `test_conditional_abort_is_not_reported_as_unconditional`: since `552cf7f01` no code is `ABORT_CONDITIONAL` (authoring: `python3 -c "from agent_workflows import run_evidence as e; print(sum(1 for r in e.RUN_FINDING_CODES if r.abort==e.ABORT_CONDITIONAL))"` -> `0`), so replace `assertTrue(conditional)` with `assertEqual(conditional, [])` plus an assertion that every code whose `may_abort_run` is True is `ABORT_ALWAYS` and names a class in `ABORT_CLASSES` (the current partition), renaming the test to describe that. The SAME test also ends with `assertEqual(sorted(always), ["RUN-BASELINE-OWNERSHIP", "RUN-LEDGER-INTEGRITY"])`, which the first failure masks today: `552cf7f01` moved `RUN-BASELINE-OWNERSHIP` from `ABORT_ALWAYS` to `ABORT_NEVER` (spec `25kzda` 4.2 action now "FAIL ITEM; cascade dependents; continue independent items"), so update that list to `["RUN-LEDGER-INTEGRITY"]` citing the same commit (review F4: without this edit the module still fails one test). If execution HEAD differs (more or fewer failures), apply the same rule: update only an assertion whose behavior a cited commit deliberately changed, and record any other failure in V-02 as a suspected regression for Order 06 (`z2xs98`) to file as `bug`.
  - Depends on: E-01
  - Expected outcome: all tests in the module pass with zero failures and zero errors; each edited assertion carries a one-line comment citing its superseding commit.
  - Execution state: performed

- [x] E-03 Prove the restored module is load-bearing with an in-memory sabotage that edits no source: put a pytest plugin in an untracked scratch dir under the gitignored `.aw/state/` that rebinds `agent_workflows.run_evidence.is_complete` to `lambda *a, **k: True` at import, run `PYTHONPATH=<scratch>:. python3 -m pytest -o addopts="" -q -n0 -p <plugin> tests/test_run_evidence_completion.py`, and confirm failures in `TestCompletionPredicates`; delete the plugin. Then run the fast suite bare (`python3 -m pytest`) and commit only the module: `aw commit <this plan> -- tests/test_run_evidence_completion.py`.
  - Depends on: E-02
  - Expected outcome: the sabotaged run reports at least one `TestCompletionPredicates` failure (review F5 observed `test_model_prose_cannot_flip_completion` and `test_toggle_coordinator_authority_absent_prevents_completion`; non-binding pointers); unsabotaged module and fast suite green; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests exercise behavior, not code structure (`AGENTS.md`; `GUIDING_PRINCIPLES.md` P16). The module drives `run_evidence`, `run_ledger_store` and `cli.main(["runs", ...])` and asserts on results and exit codes. Its spec-table parse reads a SPEC record, not production source, which is the transcription-guard pattern `tests/test_run_finding_spec_transcription.py` also uses.
- Spec files are located by id6, never by dated legacy filename (`tests/test_run_finding_spec_transcription.py` `locate_spec_25kzda`: `specs_dir.rglob("*-25kzda-*.spec.md")`). Spec `25kzda` now lives at `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`.
- `run_cli.EXIT_CORRUPTED_LEDGER: int = 5` ("hash chain / schema / torn-line corruption").
- `run_evidence.ABORT_CLASSES: Tuple[str, ...] = ("Corrupt run ledger",)`.
- Routine gate is bare `python3 -m pytest`; this module is outside `testpaths` and runs in `make test-all`.
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | The `replay-env-limited` cause is a renamed spec filename, not a multi-agent environment. | `hpjj44` `## Verdicts` row `tests/test_run_evidence_completion.py`: "`error-collect` (`StopIteration`): module-level `rglob('20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md')` at line 1019 fails because spec was renamed to `20260826-25kzda-01-25kzda-...`". |
| F2 | With only the filename corrected the module runs `3 failed, 81 passed in 5.01s` at authoring HEAD `24988557b`. | Authoring run of a scratch copy (deleted afterwards) under `-o addopts="" -n 4`. |
| F3 | The three failures are deliberate contract changes: exit code `5 != 2` (`f1f1bb5d7`), `len(ABORT_CLASSES) 1 != 6` (`552cf7f01`), and no conditional-abort codes remain (`552cf7f01`). | Pasted assertion lines from the authoring run; `git log -G` on `EXIT_CORRUPTED_LEDGER` and `ABORT_CLASSES`. |
| F4 | Review re-measurement at HEAD `9232fa963` with the id6 lookup: the same three failures (`3 failed, 81 passed in 14.38s`). Applying E-02 (a)-(c) as originally worded left ONE failure: `test_conditional_abort_is_not_reported_as_unconditional`'s trailing `sorted(always)` assertion (`['RUN-LEDGER-INTEGRITY'] != ['RUN-BASELINE-OWNERSHIP', 'RUN-LEDGER-INTEGRITY']`), masked by the earlier assertion. With that list also updated: `84 passed in 8.11s`. | Review scratch copy under `.aw/state/` (deleted); `git show 552cf7f01 -- agent_workflows/run_evidence.py` (`RUN-BASELINE-OWNERSHIP` `abort=ABORT_ALWAYS` -> `ABORT_NEVER`); `python3 -c` -> `RUN-BASELINE-OWNERSHIP` `never () False`. |
| F5 | The E-03 sabotage mechanism works: a plugin `sabotage_iscomplete.py` on `PYTHONPATH` rebinding `run_evidence.is_complete`, run with `-n0 -p sabotage_iscomplete`, failed `TestCompletionPredicates::test_model_prose_cannot_flip_completion` and `::test_toggle_coordinator_authority_absent_prevents_completion`. | Review run at HEAD `9232fa963` (scratch deleted). |

## Proposed changes (ordered, validatable)

1. Restore with an id6 spec lookup (E-01).
2. Update the three superseded assertions with citations (E-02).
3. Sabotage proof, fast suite, commit (E-03).

## Deferred / out of scope (with reason)

- Splitting the 1,722-line module into smaller files: restructuring is not needed to restore the guard.
  - Carrier-Declined: deliberate non-goal; the restoration is the deliverable.
- Adding the module to `testpaths`: routine-gate composition is a maintainer decision.
  - Carrier-Declined: deliberate non-goal; it runs in `make test-all`.

## Scope check

- Over-scope: none.
- Under-scope: none; outcome 3 of `9qvfie` names exactly this file.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_run_evidence_completion.py` all pass (E-01, E-02).
- The `is_complete` sabotage run fails (E-03).
- Bare `python3 -m pytest` shows no failures (E-03).

## Spec / documentation sync

N/A: test-only restoration; the tests READ spec `25kzda` but do not change it, and no user-facing document describes this module.

## Open questions

### OQ-01: Is "replay requires a specialized multi-agent environment" accurate?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The findings row and F2 show the cause is a renamed spec filename; the module runs in a plain checkout. The backlog wording is a summary; the requirement (carry this outcome) is unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted empty `git ls-files` pre-check; pasted runner summary showing the module COLLECTS (no `StopIteration`) and the list of failing node ids, each mapped to its superseding commit, plus `git diff --no-index <(git show 19313eed^:tests/test_run_evidence_completion.py) tests/test_run_evidence_completion.py` showing only the `_SPEC_PATH` hunk at this point.
  - Observed evidence:
    `git ls-files tests/test_run_evidence_completion.py`:
    (empty)
    `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_run_evidence_completion.py` runner summary:
    ```
    FAILED tests/test_run_evidence_completion.py::TestRunCLI::test_aw_run_verify_ledger_corrupted_chain_exits_2 - AssertionError: 5 != 2
    FAILED tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_abort_class_set_is_verbatim_from_spec_4_1 - AssertionError: 1 != 6
    FAILED tests/test_run_evidence_completion.py::TestRunFindingCodeVocabulary::test_conditional_abort_is_not_reported_as_unconditional - AssertionError: [] is not true
    ========================= 3 failed, 81 passed in 5.87s =========================
    ```
    Failing node id mapping to superseding commits:
    - `TestRunCLI::test_aw_run_verify_ledger_corrupted_chain_exits_2`: superseded by `f1f1bb5d7` ("Return EXIT_CORRUPTED_LEDGER from the three run readers that hardcode exit 2", exit code changed from 2 to `run_cli.EXIT_CORRUPTED_LEDGER` (5)).
    - `TestRunFindingCodeVocabulary::test_abort_class_set_is_verbatim_from_spec_4_1`: superseded by `552cf7f01` ("amend spec 25kzda failure policy to fix first with only corrupt ledger aborting (tb6lw3)", spec 4.1 amended to single class "Corrupt run ledger", dropping hard-coded length 6).
    - `TestRunFindingCodeVocabulary::test_conditional_abort_is_not_reported_as_unconditional`: superseded by `552cf7f01` (no codes remain `ABORT_CONDITIONAL`, and `RUN-BASELINE-OWNERSHIP` moved from `ABORT_ALWAYS` to `ABORT_NEVER`).
    `git diff --no-index <(git show 19313eed^:tests/test_run_evidence_completion.py) tests/test_run_evidence_completion.py`:
    ```diff
    --- a/dev/fd/63
    +++ b/tests/test_run_evidence_completion.py
    @@ -1016,11 +1016,14 @@ class TestAdversarialSuite(unittest.TestCase):
     # ==================================================================================================


    -_SPEC_PATH = next(
    +_SPEC_MATCHES = sorted(
         (Path(__file__).resolve().parents[1] / ".aw" / "records" / "specs").rglob(
    -        "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
    +        "*-25kzda-*.spec.md"
         )
     )
    +_SPEC_PATH = _SPEC_MATCHES[0] if len(_SPEC_MATCHES) == 1 else (
    +    Path(__file__).resolve().parents[1] / ".aw" / "records" / "specs" / "nonexistent-25kzda.spec.md"
    +)


     def _parse_spec_run_code_table() -> Dict[str, Dict[str, str]]:
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `-v` output in which every collected test is PASSED and the summary shows no failures or errors (count pasted as context; 84 at review), and the full `git diff --no-index` against `19313eed^` showing only the `_SPEC_PATH` hunk plus the hunks in the three tests (including the `sorted(always)` update), each with its citing comment; any additional failure is listed with its suspected cause.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v -p no:randomly tests/test_run_evidence_completion.py` summary:
    ```
    ============================== 84 passed in 7.89s ==============================
    ```
    Full `git diff --no-index <(git show 19313eed^:tests/test_run_evidence_completion.py) tests/test_run_evidence_completion.py`:
    ```diff
    diff --git a/dev/fd/63 b/tests/test_run_evidence_completion.py
    index 000000000..71d003af8 100644
    --- a/dev/fd/63
    +++ b/tests/test_run_evidence_completion.py
    @@ -25,6 +25,7 @@ from typing import Any, Dict, List
     from unittest.mock import patch

     from agent_workflows import cli
    +from agent_workflows import run_cli
     from agent_workflows import run_evidence as evidence
     from agent_workflows import run_ledger_schema as schema
     from agent_workflows import run_ledger_store as store
    @@ -672,8 +673,8 @@ class TestRunCLI(unittest.TestCase):
             self.assertEqual(exit_code, 0)
             self.assertIn("Overall Status: PASS", out)

    -    def test_aw_run_verify_ledger_corrupted_chain_exits_2(self) -> None:
    -        """aw run verify-ledger exits 2 when hash chain is broken."""
    +    def test_aw_run_verify_ledger_corrupted_chain_exits_corrupted_ledger(self) -> None:
    +        """aw run verify-ledger exits EXIT_CORRUPTED_LEDGER when hash chain is broken."""
             records = _sample_run_records()
             for r in records:
                 self.store.append(r)
    @@ -689,7 +690,8 @@ class TestRunCLI(unittest.TestCase):
                 exit_code = cli.main(["runs", "verify-ledger", str(self.ledger_path)])
                 out = mock_stdout.getvalue()

    -        self.assertEqual(exit_code, 2)
    +        # Superseded by f1f1bb5d7: Return EXIT_CORRUPTED_LEDGER from the three run readers that hardcode exit 2
    +        self.assertEqual(exit_code, run_cli.EXIT_CORRUPTED_LEDGER)
             self.assertIn("Broken chain", out)

         def test_aw_run_makes_no_writes_by_default(self) -> None:
    @@ -1016,11 +1018,14 @@ class TestAdversarialSuite(unittest.TestCase):
     # ==================================================================================================


    -_SPEC_PATH = next(
    +_SPEC_MATCHES = sorted(
         (Path(__file__).resolve().parents[1] / ".aw" / "records" / "specs").rglob(
    -        "20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"
    +        "*-25kzda-*.spec.md"
         )
     )
    +_SPEC_PATH = _SPEC_MATCHES[0] if len(_SPEC_MATCHES) == 1 else (
    +    Path(__file__).resolve().parents[1] / ".aw" / "records" / "specs" / "nonexistent-25kzda.spec.md"
    +)


     def _parse_spec_run_code_table() -> Dict[str, Dict[str, str]]:
    @@ -1173,8 +1178,8 @@ class TestRunFindingCodeVocabulary(unittest.TestCase):
         # ---- spec 4.1: the abort set is EXHAUSTIVE ---------------------------------------------------

         def test_abort_class_set_is_verbatim_from_spec_4_1(self) -> None:
    +        # Superseded by 552cf7f01: spec 25kzda 4.1 amended to single class ("Corrupt run ledger"); dropped hard-coded len == 6
             self.assertEqual(list(evidence.ABORT_CLASSES), _parse_spec_abort_classes())
    -        self.assertEqual(len(evidence.ABORT_CLASSES), 6)

         def test_no_code_aborts_outside_the_six_enumerated_classes(self) -> None:
             """Spec 4.1: 'No other finding may abort the whole queue'."""
    @@ -1203,30 +1208,28 @@ class TestRunFindingCodeVocabulary(unittest.TestCase):
                         expected = evidence.ABORT_CONDITIONAL
                     self.assertEqual(row.abort, expected, f"{code}: action was {action!r}")

    -    def test_conditional_abort_is_not_reported_as_unconditional(self) -> None:
    -        """The specific harm F4 names: an item-local fault must not license aborting the queue."""
    +    def test_no_conditional_abort_codes_and_aborting_codes_are_always_abort(self) -> None:
    +        """No code is ABORT_CONDITIONAL; every aborting code is ABORT_ALWAYS with classes in ABORT_CLASSES."""
             conditional = [
                 r.code
                 for r in evidence.RUN_FINDING_CODES
                 if r.abort == evidence.ABORT_CONDITIONAL
             ]
    -        self.assertTrue(conditional)
    -        for code in conditional:
    -            with self.subTest(code=code):
    -                # `may_abort_run` is True, but the caller is told WHICH class is required.
    -                self.assertTrue(evidence.may_abort_run(code))
    -                self.assertTrue(evidence.abort_classes_for(code))
    -                self.assertNotEqual(
    -                    evidence.RUN_FINDING_CODES_BY_CODE[code].abort,
-                    evidence.ABORT_ALWAYS,
-                )
    +        # Superseded by 552cf7f01: no finding code has conditional abort under amended spec 25kzda
    +        self.assertEqual(conditional, [])
    +        for r in evidence.RUN_FINDING_CODES:
    +            if evidence.may_abort_run(r.code):
    +                self.assertEqual(r.abort, evidence.ABORT_ALWAYS)
    +                for cls in r.abort_classes:
    +                    self.assertIn(cls, evidence.ABORT_CLASSES)
             always = [
                 r.code
                 for r in evidence.RUN_FINDING_CODES
                 if r.abort == evidence.ABORT_ALWAYS
             ]
    +        # Superseded by 552cf7f01: RUN-BASELINE-OWNERSHIP moved from ABORT_ALWAYS to ABORT_NEVER
             self.assertEqual(
    -            sorted(always), ["RUN-BASELINE-OWNERSHIP", "RUN-LEDGER-INTEGRITY"]
    +            sorted(always), ["RUN-LEDGER-INTEGRITY"]
             )

         # ---- E-02: the bindings, re-measured rather than trusted -------------------------------------
    ```
    Zero failures and zero errors.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted sabotaged-run output with the failing `TestCompletionPredicates` node ids; pasted final summary of bare `python3 -m pytest`; pasted `aw commit` output and `git show --stat HEAD` listing only `tests/test_run_evidence_completion.py`; `git status --short` showing no scratch plugin tracked or staged.
  - Observed evidence:
    Sabotaged run (`PYTHONPATH=.aw/state/scratch_x9z0ve:. python3 -m pytest -o addopts="" -q -n0 -p sabotage_iscomplete tests/test_run_evidence_completion.py`):
    ```
    FAILED tests/test_run_evidence_completion.py::TestCompletionPredicates::test_toggle_coordinator_authority_absent_prevents_completion
    FAILED tests/test_run_evidence_completion.py::TestCompletionPredicates::test_model_prose_cannot_flip_completion
    2 failed, 82 passed in 8.80s
    ```
    Final summary line of bare `python3 -m pytest`:
    `707 passed in 28.42s`
    `aw commit x9z0ve -- tests/test_run_evidence_completion.py`:
    ```
    aw commit: committed 1 path(s): 8e4ee91d8008b8f160991a0be5c73ed64658784f
    ```
    `git show --stat HEAD`:
    ```
    commit 8e4ee91d8008b8f160991a0be5c73ed64658784f (HEAD -> aw/lane/x9z0ve)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 16 18:31:48 2026 -0400

        work(x9z0ve): Restore the env-limited run evidence completion tests with an id6 spec lookup

        AW-Run: run-20261016T221501Z-3469718
        AW-Item: x9z0ve
        AW-Runner: aw agy run

     tests/test_run_evidence_completion.py | 1733 +++++++++++++++++++++++++++++++++
     1 file changed, 1733 insertions(+)
    ```
    `git status --short`:
    (empty)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Scope fence: `- Scope-Paths:` declares only `tests/test_run_evidence_completion.py`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Scratch plugins live under the gitignored `.aw/state/` and are deleted. Paste the ACTUAL runner output for every pass claim; never claim success you did not run. Commit only this plan's own changed files through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
