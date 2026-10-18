# IPD: Restore behavioral test coverage for run_analytics_taxonomy

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `aux1f6` (Set `trimgap`, group 4 of the `z2xs98` filing plan) records that 29 production keys in `agent_workflows/run_analytics_taxonomy.py` (416 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. The module's only behavioral test file, `tests/test_run_analytics_taxonomy.py`, was deleted by the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") and no surviving test imports the module except `tests/test_run_analytics_statistics.py`, which does not exercise the classifier. So a mutation that, for example, made `classify_command` drop a label from a multi-class command, made `assert_no_command_text` stop raising on a planted leak, or made `ClassAccounting.unclassified_regressed` always return `False` would pass the routine suite.
- Scope: Restore `tests/test_run_analytics_taxonomy.py` from `19313eed^` (51 tests in 9 classes, all of which pass unchanged against current HEAD, Finding F-02), add `pytestmark = pytest.mark.core` so the bare core-tier gate selects it, and add a small number of edge-case tests for the branches the restored file leaves unexecuted (Finding F-03). The 29 keys: `classify_command`, `classify_tool_call`, `ClassAccounting.format_report`, `_segment_head`, `ClassAccounting.to_dict`, `ClassAccounting.compare_to_baseline`, `Classification.to_dict`, `ClassAccounting.unclassified_regressed`, `assert_no_command_text`, `split_command_segments`, `_file_category`, `classify`, `LabelEvidence.to_dict`, `classify_corpus_calls`, `classify_segment.note`, `Classification.display_label`, `Classification.is_ambiguous`, `ClassAccounting._share`, `ClassAccounting.ambiguous_command_share`, `ClassAccounting.leading_cd_command_share`, `ClassAccounting.multi_class_command_share`, `ClassAccounting.multi_segment_command_share`, `ClassAccounting.single_class_command_share`, `ClassAccounting.unclassified_command_share`, `Classification.is_multi_class`, `Classification.is_unclassified`, `classify_segment`, `_closed_vocabulary`, `accumulate`. EXCLUDES any change to `agent_workflows/run_analytics_taxonomy.py` or any other production file, and EXCLUDES the sibling run-analytics modules owned by backlog items `n6h5eg` (`run_analytics_cli`), `yqpb7q` (`run_analytics_telemetry`) and `gjmiuw` (`run_analytics_submit`).
- Scope-Paths: tests/test_run_analytics_taxonomy.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: aux1f6
- Set: trimgap
- Order: 4
- Highest E allocated: 03
- Author: opencode
- Id: t8j7mn

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: t8j7mn verified (set trimgap, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-17 to-review (opencode): authored from backlog `aux1f6`. Replayed the deleted test file against HEAD `fafd612e1` (51 passed) and measured its line coverage of the module (97 percent, 11 missed lines) before writing any step, so the restore-verbatim decision and the residual edge cases below are observed rather than inferred.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 29 `unguarded-unreached` keys of `agent_workflows/run_analytics_taxonomy.py` from backlog `aux1f6` reached by the routine (bare, core-tier) test run, through behavioral tests that call the classifier and accounting and assert on their returned labels, shares, reports and raised errors. Done means a mutation that breaks multi-label classification, the regression floor, the privacy leak check, or the accounting shares turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the deleted module

- [x] E-01 Restore `tests/test_run_analytics_taxonomy.py` with `git show 19313eed^:tests/test_run_analytics_taxonomy.py > tests/test_run_analytics_taxonomy.py`, then make exactly one edit: after `import unittest`, add `import pytest` and a module-level `pytestmark = pytest.mark.core` so the core-tier hook (`conftest.pytest_collection_modifyitems`) selects it on a bare `python3 -m pytest`. Keep every restored test body and the module docstring unchanged; append one docstring sentence naming backlog `aux1f6`, findings `b1mx2w`, and the source revision `19313eed^`. Keep the existing `_FAKE_ABS_PATH` fixture as is (it is deliberately not home-directory shaped, so the leak sanitizer does not flag the tracked file). Disposition rule if a restored test fails at execution HEAD (none did at authoring, F-02, nor at review, F-05): do not mark this item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: the file exists, carries the `core` marker, every restored test passes, and a bare `python3 -m pytest --collect-only -q` lists `tests/test_run_analytics_taxonomy.py: N` with N equal to the restored test count (51 at authoring and review, re-derived at execution).
  - Execution state: performed

### Task group 2: residual branch coverage

- [x] E-02 Append one test class, `ResidualBranchTests(unittest.TestCase)`, covering the branches the restored file leaves unexecuted (F-03), each asserting a returned value observed at authoring: (a) `tax._segment_head("timeout 30s /usr/bin/pytest")` returns `("pytest", "")` (wrapper head plus a duration argument is skipped and an absolute head reduces to its basename) and `tax.classify_command("timeout 30s pytest -q").labels` contains `ActivityClass.TESTS`; (b) `tax._segment_head("   ")` and `tax._segment_head("xargs")` both return `("", "")`, and `tax.classify_command("xargs").labels == (ActivityClass.OTHER_UNKNOWN,)`; (c) `tax.classify_segment("   ")` returns `{}`; (d) `tax.classify_command("git frobnicate").evidence[ActivityClass.GIT]` has `rule == "git:other"` and `confidence == Confidence.MEDIUM` (an unknown git subcommand is still git); (e) `tax.classify_command("make wibble").evidence[ActivityClass.IMPLEMENTATION]` has `rule == "make:other"` and `confidence == Confidence.MEDIUM`; (f) `tax.classify_command("")` has `labels == (ActivityClass.OTHER_UNKNOWN,)`, `is_unclassified` True and `segment_count == 0`; (g) `tax._file_category("")` returns `"other"`; (h) `tax.Classification(labels=(), evidence={}, shares={}).display_label()` returns `ActivityClass.OTHER_UNKNOWN`; (i) `tax.accumulate([tax.classify_command("cd /x && git status")])` has `leading_cd_command_share == 1.0` and `multi_segment_command_share == 0.0`; (j) `tax.classify_corpus_calls([{"tool": "bash", "command": "git status"}, "not a mapping"])` returns a `(classifications, accounting)` tuple whose list has two items, the second with labels `(ActivityClass.OTHER_UNKNOWN,)`, and whose accounting has `command_count == 2` and `unclassified_command_share == 0.5` (the `TaxonomyError` fallback branch); (k) `tax._segment_head("xargs -0 grep foo")` returns `("grep", "foo")` (a wrapper's own flag is skipped: the loop `while parts and parts[0].startswith("-")` in `_segment_head`, the one line (a) to (j) leave unexecuted, F-05). Re-measure each value at execution HEAD before asserting it; if one has changed, apply the E-01 disposition rule.
  - Depends on: E-01
  - Expected outcome: the new class passes, and module line coverage is 100 percent (at review (a) to (j) reached 99 percent with only the wrapper-flag skip missed, and (k) covers it, F-05); any line still missed is named and explained in V-02.
  - Execution state: performed

### Task group 3: proof that every key is guarded

- [x] E-03 Run the full 29-key mutation sweep against the finished module: for each key in `b1mx2w` `## Rollup mutation results` rows `agent_workflows/run_analytics_taxonomy.py::*`, apply that row's assigned operator (`return-none`, `return-false`, `raise`) as a scratch edit to `agent_workflows/run_analytics_taxonomy.py` at the top of the key's body (after its docstring; for the nested `classify_segment.note`, at the top of the inner function), run `python3 -m pytest tests/test_run_analytics_taxonomy.py -o addopts="" -q -p no:randomly`, record KILLED (nonzero exit) or SURVIVED with the summary line, and restore the file before the next key. Keep any sweep driver script in a gitignored scratch location (for example `.aw/state/`) and never commit it. A survivor is a defect in this plan's deliverable: add the missing assertion and re-sweep that key; do not mark this item performed with a survivor outstanding.
  - Depends on: E-02
  - Expected outcome: all 29 keys KILLED (at review the restored file alone killed all 29, F-05); `git diff agent_workflows/` is empty afterwards.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). The restored file calls the classifier and asserts on labels, shares, reports and exceptions; it uses no `inspect`, `ast`, or source reads (checked by `rg -n "inspect|import ast|getsource|read_text" ` over the restored file at authoring: the only hits are the words "inspection" in test names). The two constant assertions it contains (`UNCLASSIFIED_SHARE_MARGIN == 0.02`, `CORPUS_BASELINE["unclassified_command_share"] == 0.087`) pin declared, review-time contract values that `unclassified_regressed` consumes, not code structure; they are restored as is.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget, so the restored module must carry `pytestmark = pytest.mark.core` (precedent: `tests/test_docs_check.py`, `tests/test_plans_index.py`). The restored file runs in about 0.3s to 1s, spawns no subprocess, and reads no live corpus (its docstring states hermeticity as a stop condition).
- Sibling plan precedent in the same Set: `33f8tn` (backlog `7df9md`) restores engine coverage as one core-marked module and validates with `-v` output, coverage output and reverted mutation spot-checks; this plan follows that shape.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows `agent_workflows/run_analytics_taxonomy.py::*`; `z2xs98` `## Filing plan` group 4 | Exactly 29 keys for this module carry `unreached` / `unguarded-unreached` (26 probed at `cost-cap`, plus `classify_segment`, `_closed_vocabulary`, `accumulate` listed `budget-exhausted` in the probe table but `unguarded-unreached` in the results table and assigned to group 4, so they are in this plan's scope and not `lrnh5f`'s; `lrnh5f` names no `run_analytics_taxonomy` key). `z2xs98` group 4 dedupe found zero live hits. |
| F-02 | `git show 19313eed^:tests/test_run_analytics_taxonomy.py` written to a scratch path inside the lane and run at HEAD `fafd612e1` with `-o addopts=""` | `51 passed in 0.80s`. Every deleted test still applies unchanged; no contract has drifted. With `pytestmark = pytest.mark.core` added and the file under `tests/`, a bare `python3 -m pytest --collect-only -q` listed it with 51 tests. The scratch copy was removed. |
| F-03 | same run with `--cov=agent_workflows.run_analytics_taxonomy --cov-report=term-missing` | `353 stmts, 11 miss, 97%`; missed lines are the wrapper duration-skip and empty-parts returns in `_segment_head`, the empty-labels fallback in `Classification.display_label`, the blank-segment early return in `classify_segment`, the unknown-git and unknown-make `note` branches, the empty-command return in `classify_command`, the blank-path return in `_file_category`, one `accumulate` counter, and the `TaxonomyError` fallback in `classify_corpus_calls`. Direct calls at HEAD produced the values E-02 asserts. |
| F-05 | plan review, HEAD `c2e7cb6f3`: restored file as a scratch test, coverage, direct calls, then scratch mutations of `agent_workflows/run_analytics_taxonomy.py` (restored after each; `git diff agent_workflows/` empty afterwards) | Restored file: `51 passed in 0.36s`, `353 stmts, 11 miss, 97%`, missing `320, 324, 716, 772, 808, 831, 913, 987, 1267, 1441-1442`. Every E-02 (a) to (j) value reproduced; with them added, `52 passed`, `353 stmts, 1 miss, 99%`, missing only `320`, the wrapper-flag skip `parts = parts[1:]` inside `while parts and parts[0].startswith("-")`. Deleting that loop SURVIVED both with and without (a) to (j) (`51 passed` / `52 passed`); `_segment_head("xargs -0 grep foo")` returns `('grep', 'foo')`, which (k) asserts. Sweep of all 29 keys with their `b1mx2w` operators against the restored file alone: 29 of 29 KILLED. The plan's named spot-checks are all KILLED: `classify_command` one-label (`9 failed`), `assert_no_command_text` no-op (`1 failed`), `unclassified_regressed` `(False, "")` (`2 failed`), duration-strip removal (`1 failed`; `2 failed` with E-02). Observation, not a finding: `_segment_head("timeout -k 5 30s pytest")` returns `('30s', 'pytest')`, because a flag's separate value is not skipped. |
| F-04 | `rg -ln run_analytics_taxonomy tests` at HEAD | Only `tests/test_run_analytics_statistics.py` references the module and it does not drive the classifier, consistent with the `unreached` measurement. No `tests/test_run_analytics_taxonomy.py` exists, so E-01 creates rather than overwrites. |

## Proposed changes (ordered, validatable)

1. E-01 restores the deleted test module verbatim plus the `core` marker.
2. E-02 adds residual edge-case tests for the 11 lines the restored file does not execute.
3. E-03 proves the Goal by sweeping every key with its assigned mutation operator.

## Deferred / out of scope (with reason)

- The other run-analytics modules are not covered here: each has its own backlog item in this Set.
  - Carrier: n6h5eg
- Telemetry and submit modules likewise belong to their own items (`yqpb7q`, `gjmiuw`); this plan declares only the taxonomy test file and changes nothing those items own.
  - Carrier-Declined: no work is owed by this plan; both are filed as separate open backlog items in Set `trimgap` and are tracked there.
- `_segment_head` does not skip a wrapper flag's separate value (`timeout -k 5 30s pytest` yields head `30s`, F-05). That is a production behavior question and this plan changes no production code; E-02 does not assert that case, so this plan freezes neither the current behavior nor a fix.
  - Carrier-Declined: no impact measured (analytics labels for a rare wrapper form). File it as a backlog item if a corpus measurement shows the form matters.

## Scope check

- Over-scope: none. One test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none for the 29 named keys; F-05 shows the restored file plus E-02 executes every key's body, and E-03 demonstrates each is guarded.

## Required tests / validation

- `python3 -m pytest tests/test_run_analytics_taxonomy.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes (core tier, including the restored module, within the 30s budget), with the summary line pasted.
- Reach: `python3 -m pytest tests/test_run_analytics_taxonomy.py -o addopts="" --cov=agent_workflows.run_analytics_taxonomy --cov-report=term-missing` shows every one of the 29 keys' bodies executed; paste the output.
- Mutation spot-check: in scratch edits that are NOT committed, apply one mutation at a time (make `classify_command` return only its display label as a one-label tuple; make `assert_no_command_text` return without raising; make `ClassAccounting.unclassified_regressed` return `(False, "")` immediately; make `_segment_head` skip the duration-argument strip; delete the `_segment_head` wrapper-flag skip loop), run the module, paste the failure for each, revert, and confirm `git diff agent_workflows/` is empty.
- Mutation sweep (E-03): all 29 keys with their `b1mx2w` assigned operators, one KILLED/SURVIVED line per key pasted.
- `aw sanitize --agent` reports no `fail` for the restored file.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the deleted file verbatim, or rewrite a smaller module?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: restore verbatim. The backlog item names `test_run_analytics_taxonomy.py` at `19313eed^` as the file to mine, all 51 of its tests pass unchanged at HEAD (F-02), it already reaches 97 percent of the module (F-03), and it runs in under one second, well inside the core budget. Rewriting would discard reviewed assertions for no measured benefit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff --stat` (and `git status --short`) showing only `tests/test_run_analytics_taxonomy.py` added; paste `git diff --no-index <(git show 19313eed^:tests/test_run_analytics_taxonomy.py) tests/test_run_analytics_taxonomy.py` (or equivalent) showing the only differences are the `pytest` import, the `pytestmark` line and the docstring sentence (plus E-02's appended class); paste the `-v` output listing every restored test as PASSED; paste `python3 -m pytest --collect-only -q | rg test_run_analytics_taxonomy` showing the module is selected by the bare core tier; paste the bare `python3 -m pytest` summary line (if it prints `CORE TIER BUDGET EXCEEDED`, paste that too with the same run's line without the module, and report it rather than un-marking tests; a pre-existing overrun is tracked separately, backlog `o58dro`); paste the `assert_no_command_text` and `unclassified_regressed` mutation failures (reverted afterwards); paste `aw sanitize --agent` showing no `fail` on the file.
  - Observed evidence:
    `git status --short`:
    ```
    ?? tests/test_run_analytics_taxonomy.py
    ```

    `git diff --no-index <(git show 19313eed^:tests/test_run_analytics_taxonomy.py) tests/test_run_analytics_taxonomy.py`:
    ```diff
    diff --git a/dev/fd/63 b/tests/test_run_analytics_taxonomy.py
    index 000000000..342c97139 100644
    --- a/dev/fd/63
    +++ b/tests/test_run_analytics_taxonomy.py
    @@ -12,6 +12,8 @@ WHAT THESE TESTS ASSERT THAT A WEAKER SUITE WOULD NOT. The plan's central correc
     single-label taxonomy DISCARDS a real class in two of every five commands, so the tests assert the
     LABEL SET rather than a winner, and `test_a_single_label_taxonomy_would_DISCARD_a_real_class` shows
     the loss concretely by simulating the rejected design.
    +
    +Restored for backlog aux1f6 and findings b1mx2w from source revision 19313eed^.
     """

     from __future__ import annotations
    @@ -19,6 +21,8 @@ from __future__ import annotations
     import json
     import unittest

    +import pytest
    +
     from agent_workflows import run_analytics_taxonomy as tax
     from agent_workflows.run_analytics_taxonomy import (
         ActivityClass,
    @@ -27,6 +31,8 @@ from agent_workflows.run_analytics_taxonomy import (
         TaxonomyError,
     )

    +pytestmark = pytest.mark.core
    +

     #: An absolute-looking path used ONLY to prove a classification record never carries one.
     #:
    @@ -599,5 +605,71 @@ class VersioningTests(unittest.TestCase):
             )


    +class ResidualBranchTests(unittest.TestCase):
    +    """Residual branch coverage for edge cases unexecuted by the restored suite (F-03, F-05)."""
    +
    +    def test_segment_head_wrapper_duration_and_absolute_path_reduction(self):
    +        self.assertEqual(
    +            tax._segment_head("timeout 30s /usr/bin/pytest"), ("pytest", "")
    +        )
    +        self.assertIn(
    +            ActivityClass.TESTS,
    +            tax.classify_command("timeout 30s pytest -q").labels,
    +        )
    +
    +    def test_segment_head_blank_and_xargs_returns_empty(self):
    +        self.assertEqual(tax._segment_head("   "), ("", ""))
    +        self.assertEqual(tax._segment_head("xargs"), ("", ""))
    +        self.assertEqual(
    +            tax.classify_command("xargs").labels,
    +            (ActivityClass.OTHER_UNKNOWN,),
    +        )
    +
    +    def test_classify_segment_blank_returns_empty_mapping(self):
    +        self.assertEqual(tax.classify_segment("   "), {})
    +
    +    def test_git_unknown_subcommand_has_medium_confidence(self):
    +        ev = tax.classify_command("git frobnicate").evidence[ActivityClass.GIT]
    +        self.assertEqual(ev.rule, "git:other")
    +        self.assertEqual(ev.confidence, Confidence.MEDIUM)
    +
    +    def test_make_unknown_target_has_medium_confidence(self):
    +        ev = tax.classify_command("make wibble").evidence[ActivityClass.IMPLEMENTATION]
    +        self.assertEqual(ev.rule, "make:other")
    +        self.assertEqual(ev.confidence, Confidence.MEDIUM)
    +
    +    def test_empty_command_is_unclassified_with_zero_segments(self):
    +        cmd = tax.classify_command("")
    +        self.assertEqual(cmd.labels, (ActivityClass.OTHER_UNKNOWN,))
    +        self.assertTrue(cmd.is_unclassified)
    +        self.assertEqual(cmd.segment_count, 0)
    +
    +    def test_file_category_empty_string_returns_other(self):
    +        self.assertEqual(tax._file_category(""), "other")
    +
    +    def test_classification_empty_labels_display_label_is_other_unknown(self):
    +        c = tax.Classification(labels=(), evidence={}, shares={})
    +        self.assertEqual(c.display_label(), ActivityClass.OTHER_UNKNOWN)
    +
    +    def test_accumulate_leading_cd_share_and_multi_segment_share(self):
    +        acc = tax.accumulate([tax.classify_command("cd /x && git status")])
    +        self.assertEqual(acc.leading_cd_command_share, 1.0)
    +        self.assertEqual(acc.multi_segment_command_share, 0.0)
    +
    +    def test_classify_corpus_calls_malformed_record_taxonomy_error_fallback(self):
    +        calls, acc = tax.classify_corpus_calls(
        [{"tool": "bash", "command": "git status"}, "not a mapping"]
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1].labels, (ActivityClass.OTHER_UNKNOWN,))
        self.assertEqual(acc.command_count, 2)
        self.assertEqual(acc.unclassified_command_share, 0.5)

    def test_segment_head_wrapper_flag_skip(self):
        self.assertEqual(
            tax._segment_head("xargs -0 grep foo"), ("grep", "foo")
        )


if __name__ == "__main__":
    unittest.main()
```

    `python3 -m pytest tests/test_run_analytics_taxonomy.py -o addopts="" -v` (51 restored tests passed):
    ```
    tests/test_run_analytics_taxonomy.py::AccountingTests::test_four_or_more_classes_are_counted_so_a_fixed_arity_is_visibly_wrong PASSED
    tests/test_run_analytics_taxonomy.py::AccountingTests::test_the_report_is_pasteable_and_names_both_shares PASSED
    tests/test_run_analytics_taxonomy.py::AccountingTests::test_class_segment_mass_does_not_double_count_a_multi_label_command PASSED
    tests/test_run_analytics_taxonomy.py::AccountingTests::test_every_share_is_computed_from_the_INPUT_not_the_baseline PASSED
    tests/test_run_analytics_taxonomy.py::AccountingTests::test_the_baseline_is_LABELED_as_a_snapshot_and_not_current PASSED
    tests/test_run_analytics_taxonomy.py::AccountingTests::test_compare_to_baseline_marks_EVERY_row_as_not_current PASSED
    tests/test_run_analytics_taxonomy.py::VersioningTests::test_the_accounting_records_the_version_too PASSED
    tests/test_run_analytics_taxonomy.py::VersioningTests::test_a_classification_records_the_version_that_produced_it PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_classify_accepts_the_mapping_shape_a_session_log_yields PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_a_bash_call_with_NO_command_recorded_counts_in_the_gap PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_the_measured_tool_census_is_recorded_and_has_ten_names PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_an_UNKNOWN_tool_name_is_unclassified_rather_than_guessed PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_classify_REFUSES_a_non_mapping PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_a_file_path_contributes_only_its_CATEGORY_never_the_path PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_a_file_tool_is_classified_from_its_TOOL_NAME PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_a_corpus_sweep_survives_a_malformed_call PASSED
    tests/test_run_analytics_taxonomy.py::StructuredToolSignalTests::test_the_measured_file_categories_are_all_reachable PASSED
    tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_evidence_carries_a_RULE_and_a_KIND_and_no_text_field PASSED
    tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_an_UNRECOGNIZED_aw_subcommand_does_not_reach_the_record PASSED
    tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_a_persisted_record_contains_NO_part_of_the_command PASSED
    tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_an_UNRECOGNIZED_python_module_does_not_reach_the_record PASSED
    tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_the_closed_vocabulary_is_DERIVED_from_the_tables PASSED
    tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_every_persisted_label_is_a_bare_enum_token PASSED
    tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_the_leak_CHECK_ITSELF_fires_on_a_planted_leak PASSED
    tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_a_wrapper_head_is_skipped_so_the_real_head_is_found PASSED
    tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_an_absolute_head_reduces_to_its_BASENAME PASSED
    tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_a_leading_cd_is_STRIPPED_and_reported PASSED
    tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_a_compound_command_splits_into_its_segments PASSED
    tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_an_env_prefix_is_stripped_so_the_real_head_is_found PASSED
    tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_every_separator_form_splits PASSED
    tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_an_empty_command_yields_NO_segment_rather_than_one_empty_one PASSED
    tests/test_run_analytics_taxonomy.py::RegressionFloorTests::test_the_ambiguous_share_is_reported_SEPARATELY_from_the_gap PASSED
    tests/test_run_analytics_taxonomy.py::RegressionFloorTests::test_a_clean_corpus_is_WITHIN_the_floor PASSED
    tests/test_run_analytics_taxonomy.py::RegressionFloorTests::test_the_floor_carries_a_DECLARED_margin_over_the_measured_baseline PASSED
    tests/test_run_analytics_taxonomy.py::RegressionFloorTests::test_the_unclassified_share_regression_floor_FAILS_when_coverage_regresses PASSED
    tests/test_run_analytics_taxonomy.py::RegressionFloorTests::test_an_EMPTY_corpus_does_not_regress PASSED
    tests/test_run_analytics_taxonomy.py::AmbiguityAndCoverageTests::test_an_AMBIGUOUS_command_is_NOT_counted_in_the_coverage_gap PASSED
    tests/test_run_analytics_taxonomy.py::AmbiguityAndCoverageTests::test_echo_is_NARRATION_rather_than_dumped_into_other_unknown PASSED
    tests/test_run_analytics_taxonomy.py::AmbiguityAndCoverageTests::test_a_bare_python3_is_AMBIGUOUS_with_low_confidence_not_a_guess PASSED
    tests/test_run_analytics_taxonomy.py::AmbiguityAndCoverageTests::test_a_resolvable_python_module_is_NOT_ambiguous PASSED
    tests/test_run_analytics_taxonomy.py::AmbiguityAndCoverageTests::test_the_measured_class_vocabulary_is_covered_by_rules PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_single_label_taxonomy_would_DISCARD_a_real_class PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_per_label_shares_sum_to_one_so_a_corpus_total_is_not_inflated PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_redirect_to_dev_null_or_a_fd_is_NOT_an_edit PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_git_inspection_subcommand_is_BOTH_git_and_inspection PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_command_that_is_simultaneously_git_and_test_yields_BOTH_labels PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_git_mutation_subcommand_is_git_and_NOT_inspection PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_display_precedence_covers_EVERY_class_so_it_is_total PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_grep_into_a_redirect_is_simultaneously_inspection_AND_editing PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_pipeline_of_inspection_into_editing_carries_both PASSED
    tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_the_display_label_is_PRESENTATION_ONLY_and_removes_nothing PASSED
    ```

    `python3 -m pytest --collect-only -q | grep test_run_analytics_taxonomy`:
    ```
    tests/test_run_analytics_taxonomy.py: 62
    ```

    Bare `python3 -m pytest` summary line:
    ```
    1338 passed in 28.65s
    ```

    `assert_no_command_text` mutation failure (reverted afterwards):
    ```
    FAILED tests/test_run_analytics_taxonomy.py::PrivacyBoundaryTests::test_the_leak_CHECK_ITSELF_fires_on_a_planted_leak
    1 failed, 61 passed in 0.31s
    ```

    `unclassified_regressed` mutation failures (reverted afterwards):
    ```
    FAILED tests/test_run_analytics_taxonomy.py::RegressionFloorTests::test_an_EMPTY_corpus_does_not_regress
    FAILED tests/test_run_analytics_taxonomy.py::RegressionFloorTests::test_the_unclassified_share_regression_floor_FAILS_when_coverage_regresses
    2 failed, 60 passed in 0.53s
    ```

    `aw sanitize --agent`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5909,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every `ResidualBranchTests` test as PASSED; paste the `--cov-report=term-missing` output for `agent_workflows/run_analytics_taxonomy.py` and, for any line still missed, name it and why it is unreachable or not one of the 29 keys; paste the failures from the `classify_command` one-label mutation, the `_segment_head` duration-strip mutation, and the `_segment_head` wrapper-flag-skip deletion (the last with the E-02 (k) test among the failures; it survives without (k), F-05), each reverted afterwards.
  - Observed evidence:
    `python3 -m pytest tests/test_run_analytics_taxonomy.py -k ResidualBranchTests -v` output:
    ```
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_accumulate_leading_cd_share_and_multi_segment_share PASSED [  9%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_classification_empty_labels_display_label_is_other_unknown PASSED [ 18%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_classify_corpus_calls_malformed_record_taxonomy_error_fallback PASSED [ 27%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_classify_segment_blank_returns_empty_mapping PASSED [ 36%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_empty_command_is_unclassified_with_zero_segments PASSED [ 45%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_file_category_empty_string_returns_other PASSED [ 54%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_git_unknown_subcommand_has_medium_confidence PASSED [ 63%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_make_unknown_target_has_medium_confidence PASSED [ 72%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_segment_head_blank_and_xargs_returns_empty PASSED [ 81%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_segment_head_wrapper_duration_and_absolute_path_reduction PASSED [ 90%]
    tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_segment_head_wrapper_flag_skip PASSED [100%]
    ```

    `python3 -m pytest tests/test_run_analytics_taxonomy.py -o addopts="" --cov=agent_workflows.run_analytics_taxonomy --cov-report=term-missing`:
    ```
    Name                                        Stmts   Miss  Cover   Missing
    -------------------------------------------------------------------------
    agent_workflows/run_analytics_taxonomy.py     353      0   100%
    -------------------------------------------------------------------------
    TOTAL                                         353      0   100%
    ```
    No line missed (100% line coverage).

    `classify_command` one-label mutation failures (reverted afterwards):
    ```
    FAILED tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_command_that_is_simultaneously_git_and_test_yields_BOTH_labels
    FAILED tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_git_inspection_subcommand_is_BOTH_git_and_inspection
    FAILED tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_grep_into_a_redirect_is_simultaneously_inspection_AND_editing
    FAILED tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_pipeline_of_inspection_into_editing_carries_both
    FAILED tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_a_single_label_taxonomy_would_DISCARD_a_real_class
    FAILED tests/test_run_analytics_taxonomy.py::MultiLabelClassificationTests::test_the_display_label_is_PRESENTATION_ONLY_and_removes_nothing
    FAILED tests/test_run_analytics_taxonomy.py::AccountingTests::test_class_segment_mass_does_not_double_count_a_multi_label_command
    FAILED tests/test_run_analytics_taxonomy.py::AccountingTests::test_every_share_is_computed_from_the_INPUT_not_the_baseline
    FAILED tests/test_run_analytics_taxonomy.py::AccountingTests::test_four_or_more_classes_are_counted_so_a_fixed_arity_is_visibly_wrong
    9 failed, 53 passed in 0.34s
    ```

    `_segment_head` duration-strip mutation failures (reverted afterwards):
    ```
    FAILED tests/test_run_analytics_taxonomy.py::SegmentSplittingTests::test_a_wrapper_head_is_skipped_so_the_real_head_is_found
    FAILED tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_segment_head_wrapper_duration_and_absolute_path_reduction
    2 failed, 60 passed in 0.27s
    ```

    `_segment_head` wrapper-flag-skip deletion failure (with E-02 (k) test failing, reverted afterwards):
    ```
    FAILED tests/test_run_analytics_taxonomy.py::ResidualBranchTests::test_segment_head_wrapper_flag_skip
    1 failed, 61 passed in 0.40s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the sweep output, one line per key naming the key, its operator, KILLED or SURVIVED, and the pytest summary line, covering all 29 `b1mx2w` keys with zero SURVIVED; paste a final empty `git diff agent_workflows/` and `git status --short` showing no sweep script staged or tracked.
  - Observed evidence:
    Full 29-key mutation sweep results:
    ```
    agent_workflows/run_analytics_taxonomy.py::classify_command | return-none | KILLED | 40 failed, 22 passed in 0.99s
    agent_workflows/run_analytics_taxonomy.py::classify_tool_call | return-none | KILLED | 7 failed, 55 passed in 0.75s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.format_report | return-none | KILLED | 1 failed, 61 passed in 1.37s
    agent_workflows/run_analytics_taxonomy.py::_segment_head | return-none | KILLED | 40 failed, 22 passed in 1.61s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.to_dict | return-none | KILLED | 1 failed, 61 passed in 0.32s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.compare_to_baseline | return-none | KILLED | 1 failed, 61 passed in 0.32s
    agent_workflows/run_analytics_taxonomy.py::Classification.to_dict | return-none | KILLED | 1 failed, 61 passed in 0.29s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.unclassified_regressed | return-none | KILLED | 4 failed, 58 passed in 0.33s
    agent_workflows/run_analytics_taxonomy.py::assert_no_command_text | raise | KILLED | 2 failed, 60 passed in 0.57s
    agent_workflows/run_analytics_taxonomy.py::split_command_segments | return-none | KILLED | 44 failed, 18 passed in 1.33s
    agent_workflows/run_analytics_taxonomy.py::_file_category | return-none | KILLED | 3 failed, 59 passed in 0.34s
    agent_workflows/run_analytics_taxonomy.py::classify | return-none | KILLED | 3 failed, 59 passed in 0.34s
    agent_workflows/run_analytics_taxonomy.py::LabelEvidence.to_dict | return-none | KILLED | 1 failed, 61 passed in 0.41s
    agent_workflows/run_analytics_taxonomy.py::classify_corpus_calls | return-none | KILLED | 2 failed, 60 passed in 0.37s
    agent_workflows/run_analytics_taxonomy.py::classify_segment.note | raise | KILLED | 38 failed, 24 passed in 1.61s
    agent_workflows/run_analytics_taxonomy.py::Classification.display_label | return-none | KILLED | 8 failed, 54 passed in 0.82s
    agent_workflows/run_analytics_taxonomy.py::Classification.is_ambiguous | return-none | KILLED | 3 failed, 59 passed in 0.40s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting._share | return-none | KILLED | 9 failed, 53 passed in 0.60s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.ambiguous_command_share | return-none | KILLED | 3 failed, 59 passed in 0.41s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.leading_cd_command_share | return-none | KILLED | 4 failed, 58 passed in 0.46s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.multi_class_command_share | return-none | KILLED | 4 failed, 58 passed in 0.40s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.multi_segment_command_share | return-none | KILLED | 4 failed, 58 passed in 0.36s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.single_class_command_share | return-none | KILLED | 4 failed, 58 passed in 0.34s
    agent_workflows/run_analytics_taxonomy.py::ClassAccounting.unclassified_command_share | return-none | KILLED | 7 failed, 55 passed in 2.83s
    agent_workflows/run_analytics_taxonomy.py::Classification.is_multi_class | return-false | KILLED | 1 failed, 61 passed in 0.31s
    agent_workflows/run_analytics_taxonomy.py::Classification.is_unclassified | return-none | KILLED | 7 failed, 55 passed in 0.39s
    agent_workflows/run_analytics_taxonomy.py::classify_segment | return-none | KILLED | 40 failed, 22 passed in 2.29s
    agent_workflows/run_analytics_taxonomy.py::_closed_vocabulary | return-none | KILLED | 3 failed, 59 passed in 0.41s
    agent_workflows/run_analytics_taxonomy.py::accumulate | return-none | KILLED | 13 failed, 49 passed in 0.50s
    ```
    TOTAL KEYS: 29, ALL KILLED: True (0 survived).

    `git diff agent_workflows/` is empty:
    ```
    ```

    `git status --short`:
    ```
    ?? tests/test_run_analytics_taxonomy.py
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:

- Open questions: all resolved (OQ-01).
- Scope fence: `tests/test_run_analytics_taxonomy.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under the E-01 disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks and the E-03 sweep are scratch edits to `agent_workflows/run_analytics_taxonomy.py` that must be reverted before commit and must be absent from the diff; any sweep script lives in a gitignored scratch location and is never committed. Delete any `.coverage` data file a coverage run leaves behind.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit t8j7mn -- tests/test_run_analytics_taxonomy.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize t8j7mn` instead. Never hand-`git mv` the plan.
