# IPD: Restore behavioral test coverage for run_analytics_export

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `liybkg` (Set `trimgap`, group 7 of the `z2xs98` filing plan) records that 10 production keys in `agent_workflows/run_analytics_export.py` (291 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. The module's own behavioral test file, `tests/test_run_analytics_export.py`, was deleted by the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), and no surviving test drives the export module (only `tests/test_run_analytics_privacy_docs.py` and `tests/fixtures/run_analytics/__init__.py` mention it, F-04). So a mutation that, for example, let `build_redacted_events` copy an un-allowlisted field, made `archive_member_refusal` accept a `../` traversal, made `select_raw_files` default to everything, or made `build_manifest` drop checksums would pass the routine suite.
- Scope: Restore the behavioral part of `tests/test_run_analytics_export.py` from `19313eed^` (everything above its `# --- E-01: the surface contract` banner, minus the three tests that read production source text and the `_code_lines` helper they use, Finding F-02/F-03), add `pytestmark = pytest.mark.core` so the bare core-tier gate selects it, and append residual edge-case tests for the branches the restored file leaves unexecuted (F-05). The 10 keys: `build_manifest`, `_bundle_readme`, `_sha256_file`, `archive_member_refusal`, `select_raw_files`, `_categorize`, `ExportManifestEntry.to_dict`, `write_bundle`, `sanitizer_blind_spot_report`, `build_redacted_events`. EXCLUDES any change to `agent_workflows/run_analytics_export.py` or any other production file; EXCLUDES restoring `tests/test_run_analytics_privacy_boundary.py`, `tests/test_run_analytics_submit.py` and `tests/test_run_analytics_wizard.py`, which backlog item `gjmiuw` (`run_analytics_submit`) lists as its own files to mine and which `q86fxm` group 16 covers for the wizard; EXCLUDES the `runs export`/`runs submit` CLI surface-contract tests of the deleted file (F-03).
- Scope-Paths: tests/test_run_analytics_export.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: liybkg
- Set: trimgap
- Order: 7
- Highest E allocated: 02
- Author: opencode
- Id: 438gkf

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Readiness go-pending-approval. Review record .aw/records/reviews/20261017-trimgap-07-438gkf-restore-behavioral-test-coverage-for-run-analytics-export.review.md

- 2026-10-17 to-review (opencode): authored from backlog `liybkg`. Replayed the deleted test file (and, for comparison, `test_run_analytics_privacy_boundary.py`) against HEAD `314987396` and measured line coverage of the module before writing any step, so the restore-subset decision and the residual edge cases below are observed rather than inferred.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 10 `unguarded-unreached` keys of `agent_workflows/run_analytics_export.py` from backlog `liybkg` reached by the routine (bare, core-tier) test run, through behavioral tests that call the export functions and assert on returned payloads, written bundle files, manifests, checksums and raised refusals. Done means a mutation that breaks structural redaction, raw-tier selection, manifest checksumming, or hostile-archive refusal turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the behavioral part of the deleted module

- [ ] E-01 Create `tests/test_run_analytics_export.py` from `git show 19313eed^:tests/test_run_analytics_export.py`, keeping only the content ABOVE the `# --- E-01: the surface contract` banner, with the `_code_lines` helper and the three tests that call it on production source, `test_metrics_uses_order_02_allowlist_and_builds_no_second_projector`, `test_tarfile_data_filter_is_feature_detected_not_assumed` and `test_no_archive_precedent_existed_in_the_package` removed (they read `agent_workflows/*.py` text and assert on substrings, which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" forbids restoring), a module-level `pytestmark = pytest.mark.core` after `import pytest`, and a docstring sentence naming backlog `liybkg`, findings `b1mx2w`, source revision `19313eed^`, and that the source-reading and CLI-surface tests were deliberately not restored. Keep every other restored test body unchanged, including the runtime-assembled canary payloads (no canary is a committed literal). If any restored test fails at execution HEAD (none did at authoring, F-02; 28 passed in 0.52s at review), do not mark E-01 performed until that test is dispositioned: record the failure in Findings, determine whether the current behavior is an intended change (cite the commit) or a regression, and adjust only that test's expectation for an intended change; a regression is out of scope here and must be filed as a `bug` backlog item with `--blocks-release next` (via `aw backlog new`, outside this plan's Scope-Paths, justified at finalize with `--scope-reason`) and the failing test marked `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than papered over or deleted, then continue with the remaining items.
  - Depends on: none
  - Expected outcome: the file exists, carries the `core` marker, and its 28 restored test cases (20 test functions, one parametrized over 9 cases) pass; a bare `python3 -m pytest --collect-only -q` lists `tests/test_run_analytics_export.py` among selected items; `rg -n "_code_lines|getsource|import ast|import inspect|tokenize|agent_workflows/" tests/test_run_analytics_export.py` returns nothing, and `rg -n "read_text\(" tests/test_run_analytics_export.py` matches only reads of `bundle.manifest_path`, `bundle.root / "README.txt"` and extracted files under `dest`/`dest2` (5 matches in the restored subset at review), all of which the tests wrote under `tmp_path`.
  - Execution state: pending

### Task group 2: residual branch coverage

- [ ] E-02 Append one block of tests, `test_residual_*` functions (pytest style, matching the restored file), covering the branches the restored subset leaves unexecuted (F-05), each asserting a value observed at authoring: (a) `export.tier_is_sensitive("raw")` is True, `export.tier_is_sensitive("metrics")` and `("events-redacted")` are False, and `export.tier_is_sensitive("bogus")` raises `export.ExportRefusal`; (b) `export.build_redacted_events([env], max_events_per_run=2)` for an `_Envelope` whose `event_facts` is `["not a mapping", {"activity": 1, "prompt_text": "x"}, {"activity": 2}, {"activity": 3}]` returns `runs[0]["event_count"] == 2`, `runs[0]["events"] == [{"activity": 1}, {"activity": 2}]`, `dropped_field_names == ["prompt_text"]` and `dropped_field_occurrences == 1` (non-mapping skip and per-run cap); (c) `export.sanitizer_blind_spot_report(["see /home/" + "someone" + "/x.py"])` has a finding `{"location": "sample[0]:1", "rule": "home-path", "severity": "fail"}` and `finding_count >= 1` (the sample is fragment-assembled and uses no real home directory, so it does not depend on the machine); (d) `export.write_bundle(tmp_path / "m", tier="metrics", payload={"a": 1}, sanitizer_report={"k": "v"})` writes `payload.json` and `sanitizer-report.json`, its entries name both plus `README.txt`, and `bundle.to_dict()` has keys `entries, file_count, manifest_path, root, tier` with `file_count == len(bundle.entries)`; (e) `export.select_raw_files([tmp_path / "missing", run], include=["sub"])` returns only the file under `run/sub/` (a missing run dir is skipped), and `export.preview_raw_selection([tmp_path / "nope.txt"])` reports `total_bytes == 0` and `categories == {"other": {"count": 1, "bytes": 0}}` (stat failure counts zero bytes; `_categorize` falls back to `"other"`); (f) `export.build_manifest(d)` over a directory holding `manifest.json` and `k.txt` (content `hi`) returns exactly one entry whose `to_dict()` is `{"path": "k.txt", "size_bytes": 2, "sha256": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"}`; (g) `export.safe_extract` of a zip containing a `dir/` entry and `dir/f.txt` (`hey`) returns `["dir/f.txt"]` and writes that content, and of a tar containing a directory member `dd` plus `dd/g.txt` returns `["dd/g.txt"]` (directory members are validated but not listed or written). Re-measure each value at execution HEAD before asserting it; if one has changed, apply the same disposition rule as E-01 (intended change: cite the commit and adjust; regression: file a gated `bug` and mark the test `xfail(strict=True)`). All values (a) to (g) were re-measured at review and matched.
  - Depends on: E-01
  - Expected outcome: the residual tests pass, and module line coverage rises from the restored subset's 92 percent to at least 98 percent, with every remaining missed line named and explained in V-02.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). This is why E-01 drops the three source-text tests and the `_code_lines` tokenizer helper: they read `agent_workflows/run_analytics_export.py` (and every package module) as text and assert substrings such as `"re . compile"` counts, `filter="data"` and `extractall`. The archive behavior those tests guarded is still asserted behaviorally by the restored `test_benign_archive_extracts_identically_regardless_of_filter_support` and the hostile-archive tests.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget, so the restored module must carry `pytestmark = pytest.mark.core` (precedent: `tests/test_docs_check.py`). The restored subset ran in 0.47s at authoring, spawns no subprocess, and touches only `tmp_path`.
- Sibling plan precedent in the same Set: `t8j7mn` (backlog `aux1f6`) restores taxonomy coverage as one core-marked module plus a residual-branch block and validates with `-v` output, coverage output and reverted mutation spot-checks; this plan follows that shape.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows `agent_workflows/run_analytics_export.py::*`; `b1mx2w` per-module totals row (14 keys: `budget-exhausted` 4, `unguarded-unreached` 10); `z2xs98` `## Filing plan` group 7 | Exactly 10 keys carry `unguarded-unreached` and are this plan's scope. The other 4 (`preview_raw_selection`, `residual_risk_notes`, `_tier_rank`, `build_metrics_payload`) are `subprocess-only`/`budget-exhausted`, not in `liybkg`; the restored file reaches them in-process anyway (F-02). |
| F-02 | `git show 19313eed^:tests/test_run_analytics_export.py` copied to a scratch test path inside the lane and run at HEAD `314987396` with `-o addopts=""` | Whole file: `1 failed, 51 passed` together with privacy_boundary; the export file alone has 29 functions. The one failure is `test_no_new_undeclared_leaf_was_introduced` (`assert [] == ['oc profile ...profile show']`), stale since `f2cd41b19` declared the five `oc profile` commands; the same invariant is now owned by `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`. The E-01 subset (behavioral tests above the surface-contract banner, minus the three source readers) ran `28 passed in 0.47s`. Scratch copies were removed. |
| F-03 | Reading the deleted file | Below the `# --- E-01: the surface contract` banner are 6 tests on `runs export`/`runs submit` parser declarations, mutation gates and conformance-matrix rows. They exercise `agent_workflows/command_surface.py` and `tests/conformance_matrix.py`, not any of the 10 keys, and one is stale (F-02); they are excluded. Three tests above the banner read production source text (code-pinning) and are excluded. |
| F-04 | `rg -ln run_analytics_export tests` at HEAD | Only `tests/test_run_analytics_privacy_docs.py` and `tests/fixtures/run_analytics/__init__.py` mention the module; no `tests/test_run_analytics_export.py` exists, so E-01 creates rather than overwrites. |
| F-05 | E-01 subset run with `--cov=agent_workflows.run_analytics_export --cov-report=term-missing` | `271 stmts, 22 miss, 92%`. Missed: `tier_is_sensitive` body; `_projector_version` return of `SCHEMA_VERSION`; non-mapping skip and `max_events_per_run` break in `build_redacted_events`; findings append in `sanitizer_blind_spot_report`; `ExportBundle.to_dict`; missing-dir skip in `select_raw_files`; `OSError` stat fallback in `preview_raw_selection`; `"other"` return in `_categorize`; `manifest.json` skip in `build_manifest`; `payload`/`sanitizer_report` writes in `write_bundle`; the zip extraction branch of `safe_extract`; the tar non-file and `extractfile is None` skips. Direct calls at HEAD produced the values E-02 asserts. Two lines are expected to stay missed: `_projector_version` returning `SCHEMA_VERSION` is unreachable because `agent_workflows.run_analytics_cache` defines no `SCHEMA_VERSION` (observed `getattr(...) -> MISSING`, so it returns `EXPORT_SCHEMA_VERSION == 1`), and `extractfile(member) is None` is a defensive branch for a regular-file member, which tarfile does not produce. Neither is one of the 10 keys. |
| F-06 | `git show 19313eed^:tests/test_run_analytics_privacy_boundary.py` run at HEAD with the same coverage flags | `15 passed`, 55 percent of the module; it adds only the two `write_bundle` payload/sanitizer-report lines over the E-01 subset, which E-02 (d) covers directly. It also scans cache, report, receipts and the leak sanitizer across modules, and it is listed as a file to mine by `gjmiuw` too, so it is left to that item rather than split across two plans. |
| F-07 | `aw sanitize --agent` run while the scratch copies sat under `tests/` | `"outcome":"clean" ... "findings":0`: the runtime-assembled canaries (home directory, hostname, username built at test time) are not committed literals and do not trip the leak sanitizer. |

## Proposed changes (ordered, validatable)

1. E-01 restores the behavioral subset of the deleted test module plus the `core` marker.
2. E-02 adds residual edge-case tests for the branches the restored subset does not execute.

## Deferred / out of scope (with reason)

- `tests/test_run_analytics_privacy_boundary.py`, `tests/test_run_analytics_submit.py` (and the submit module's coverage) are restored by the submit item, which names the same three files to mine.
  - Carrier: gjmiuw
- `tests/test_run_analytics_wizard.py` belongs to the residual rollup (group 16, `agent_workflows/run_analytics_wizard.py`). Note for that carrier: the deleted submit and wizard files import `_code_lines` from `tests.test_run_analytics_export`, which this plan does not restore; those call sites are themselves source-text tests and should be dropped, not re-pointed.
  - Carrier: q86fxm
- The six `runs export`/`runs submit` CLI surface-contract tests (F-03) and the three source-reading tests are not restored.
  - Carrier-Declined: no work is owed; the undeclared-leaf invariant is enforced by `tests/test_command_surface_declarations.py`, the full conformance matrix runs in the slow tier, and source-text assertions are prohibited by `AGENTS.md`.

## Scope check

- Over-scope: none. One test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none for the 10 named keys; F-02 and F-05 show the restored subset plus E-02 executes every key's body.

## Required tests / validation

- `python3 -m pytest tests/test_run_analytics_export.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes (core tier, including the restored module, within the 30s budget), with the summary line pasted.
- Reach: `COVERAGE_FILE=/tmp/opencode/cov438gkf python3 -m pytest tests/test_run_analytics_export.py -o addopts="" -p no:cacheprovider --cov=agent_workflows.run_analytics_export --cov-report=term-missing` shows the module at or above 98 percent with every missed line named; paste the output. Set `COVERAGE_FILE` outside the repo (without it, pytest-cov writes an untracked `.coverage` into the worktree root, observed at review). At review, the restored subset plus a draft of E-02 (a) to (g) measured `271 stmts, 2 miss, 99%`, missing lines 309 and 800 (`_projector_version`'s `return value` and the `extractfile is None` `continue`), exactly the two F-05 predicts.
- Mutation spot-check: in scratch edits that are NOT committed, apply one mutation at a time (make `build_redacted_events` copy every key of each event; make `archive_member_refusal` return `None` immediately; make `select_raw_files` ignore an empty `include` and select everything; make `_sha256_file` return `""`; make `build_manifest` stop skipping `manifest.json`), run the module, paste the failure for each, revert, and confirm `git diff agent_workflows/` is empty.
- `aw sanitize --agent` reports no `fail` for the restored file.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the deleted file verbatim, or a behavioral subset?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: restore the behavioral subset. Verbatim restore would bring back one failing stale test (F-02), six CLI-surface tests that reach none of the 10 keys (F-03), and three source-text tests the repository's test contract forbids (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"). The remaining 28 cases all pass unchanged at HEAD and reach every key (F-02, F-05).

### OQ-02: Should this plan also restore `test_run_analytics_privacy_boundary.py`, which reaches the same keys?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. It adds only two lines of export coverage over the E-01 subset, which E-02 covers directly (F-06), and it is a cross-module privacy test that backlog `gjmiuw` also lists as a file to mine; restoring it here would make two plans claim the same file.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` and `git diff --stat HEAD` showing only `tests/test_run_analytics_export.py` added; paste a diff between `git show 19313eed^:tests/test_run_analytics_export.py` and the new file showing the only differences are the removed `_code_lines` helper, the three removed source-reading tests, the removed surface-contract section, the `pytestmark` line and the docstring sentence (plus E-02's appended tests); paste `rg -n "_code_lines|getsource|import ast|import inspect|tokenize|agent_workflows/" tests/test_run_analytics_export.py` returning nothing and the `rg -n "read_text\("` matches showing only reads of test-written files; paste the `-v` output listing the 28 restored cases as PASSED; paste `python3 -m pytest --collect-only -q | rg test_run_analytics_export` showing the module is selected by the bare core tier; paste the bare `python3 -m pytest` summary line and wall time within budget; paste the failures produced by the `build_redacted_events` copy-everything and `archive_member_refusal` return-None mutations (reverted afterwards); paste `aw sanitize --agent` showing no `fail`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every `test_residual_*` test as PASSED; paste the `--cov-report=term-missing` output (from the Reach command, with `COVERAGE_FILE` outside the repo) for `agent_workflows/run_analytics_export.py` showing at least 98 percent and, for each line still missed, name it and why it is unreachable or not one of the 10 keys (F-05 predicts the `_projector_version` `SCHEMA_VERSION` return and the `extractfile is None` skip); paste the failures from the `select_raw_files` select-everything, `_sha256_file` empty-digest and `build_manifest` no-skip mutations (reverted afterwards); paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- All open questions are resolved (OQ-01, OQ-02).
- Scope fence: `tests/test_run_analytics_export.py` is the only declared path; an out-of-scope edit (for example a gated `bug` backlog item filed under E-01's disposition rule) is made and justified at finalize (`--scope-reason`), not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (returned payloads, written bundle files, manifests, checksums, raised refusals), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Mutation spot-checks are scratch edits to `agent_workflows/run_analytics_export.py` that must be reverted before commit and must not appear in the diff; coverage data goes to `COVERAGE_FILE` outside the repo.
- Commit only through `aw commit <plan> -- tests/test_run_analytics_export.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only those paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming with every V-item at `Result: pass`, then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
