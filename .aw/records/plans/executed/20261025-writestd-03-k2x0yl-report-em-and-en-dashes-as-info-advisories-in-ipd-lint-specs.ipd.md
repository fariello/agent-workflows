# IPD: Report em and en dashes as info advisories in ipd lint, specs check, and backlog check

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-07 requires a mechanical check that reports an em dash or en dash in the prose of a plan, spec, or backlog item, as an `info` advisory that never changes an exit status. `aw ipd lint` retired its dash rule `IPD-D701` (comment above `ipd_lint` "Fence-aware structural reader"), and `tests/test_ipd_lint.py` `StructuralRuleTests` pins that a dash plan lints clean. `specs.validate_spec` and `backlog.validate_item` have no prose check, and at least seven callers treat ANY drift they return as a refusal or an invalid view (for example `status_set` `residual = _specs_mod.validate_spec(...)` then `if residual: raise`, `specs.run_migrate`, `set_records.promote_question`, `runner_shared` spec stage check filtering `severity == "error"` on un-enriched drift), so the advisory must NOT be returned from those validators.
- Scope: Add one shared prose-dash scanner; emit it as advisory `IPD-C802` from `ipd_lint.lint_text` and as `info` rules `spec.prose-dash` and `backlog.prose-dash` from separate advisory functions (`specs.prose_dash_advisories`, `backlog.prose_dash_advisories`) that only the two `run_check` commands and `check_engine.check_content` call, each Drift carrying `severity="info"` and registered in `check_engine.RULE_REGISTRY`; make the two `run_check` agent outputs report each drift's own severity instead of the hard-coded `"error"`; amend the IPD linting spec's Section 10 item 17. EXCLUDES fixing dashes in existing artifacts (Orders 07 to 09) and any blocking severity.
- Scope-Paths: agent_workflows/prose_dash.py, agent_workflows/ipd_lint.py, agent_workflows/specs.py, agent_workflows/backlog.py, agent_workflows/check_engine.py, tests/test_prose_dash_advisory.py, tests/test_ipd_lint.py, tests/fixtures/review-pilot/, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: k2x0yl

## Workflow history
- 2026-11-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: k2x0yl verified (set writestd, attempt 1). [Scope reconciliation - in-scope-unmodified tests/fixtures/review-pilot/: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-02 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED
- 2026-11-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED; review record .aw/records/reviews/20261025-writestd-03-k2x0yl-report-em-and-en-dashes-as-info-advisories-in-ipd-lint-specs.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Report every em or en dash in authored prose of a spec, backlog item, or plan as a non-blocking advisory, so authors and the sweep can find them.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scanner and emitters

- [x] E-01 Create `agent_workflows/prose_dash.py` (spec `ecmw83` R-07) with `find_prose_dashes(text) -> list[tuple[int, int, str]]` returning (1-based line, 1-based column, character) for each U+2014 or U+2013 outside fenced code blocks, indented code blocks, block quotes, inline code spans, YAML `---` front matter, and the metadata block (every line before the first `## ` heading, the boundary `specs._metadata_end` uses). The module must import nothing from `ipd_lint`, `specs`, or `backlog` (`ipd_lint` already imports `backlog` through `ipd_schema`, so a shared helper living in any of them risks an import cycle). Implement the fence, indent, and quote rules of `ipd_lint._structural_lines` here, then make `ipd_lint` call nothing new for structure (it keeps its own reader).
  - Depends on: none
  - Expected outcome: the function exists, imports only the standard library, and returns positions only for prose dashes.
  - Execution state: performed

- [x] E-02 In `ipd_lint`, add constant `C_PROSE_DASH = "IPD-C802"` (next free code in the C8xx family; do not reuse `IPD-D701`) and append one advisory per dash to `advisories` in `lint_text`, never to `diags`. Do NOT add an authoring-date cutover: the rule applies to every evaluated (non-terminal) plan. Reason: Orders 07 to 09 (`sfez3e` E-02, `uog8nc` E-02, `381ml6`) use these advisories to find the dashes in every live artifact, including ones authored before this plan executes, and spec `ecmw83` AC-06 measures the sweep by these advisories. A cutover would hide exactly the population the sweep must fix. Measured at review (HEAD `f70329c47`): of the live non-terminal artifacts only one file holds a dash (spec `4sd62s`), and `ipd_lint.lint_text` already returns `DISPOSITION_LEGACY` with no advisories for terminal-directory plans (375 executed plans hold dashes and stay silent). Keep the message short and name `IPD-C802`, the character, and spec `ecmw83` R-07.
  - Depends on: E-01
  - Expected outcome: a pending plan with a prose dash gets one `IPD-C802` advisory per dash and stays conforming; a plan in `executed/` gets none.
  - Execution state: performed

- [x] E-03 (spec `ecmw83` R-07) Add `specs.prose_dash_advisories(path, text)` and `backlog.prose_dash_advisories(path, text)`, each returning `Drift(location, rule, detail, severity="info")` with rule `spec.prose-dash` or `backlog.prose-dash` and `location` from the module's existing `drift_location`. Do NOT call them from `specs.validate_spec` or `backlog.validate_item` (see Concern). Call them only from `specs.run_check`, `backlog.run_check`, and the `specs` and `backlog` branches of `check_engine.check_content`, for files those already enumerate (`check_content` skips retired files unless `include_retired`). Register both rules in `check_engine.RULE_REGISTRY` as `RuleSpec("info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`. In both `run_check` agent/JSON branches, set each `Diagnostic` severity from `d.severity or "error"` instead of the literal `"error"`, and keep the human branch listing the advisory. No authoring-date cutover (reason in E-02).
  - Depends on: E-01
  - Expected outcome: `aw specs check` and `aw backlog check` list the advisory with severity `info` and exit 0 when it is the only finding; `validate_spec` and `validate_item` return no new rule.
  - Execution state: performed

### Task group 2: tests and spec

- [x] E-04 Create `tests/test_prose_dash_advisory.py` (marker `core`), table-driven: dashes in prose (reported), in a fenced block, indented block, block quote, inline code, and the metadata block (not reported), for each of the three artifact types, asserting the reported codes and an unchanged disposition or exit status (spec `ecmw83` AC-05). Also assert: (a) `specs.validate_spec` and `backlog.validate_item` return no `*.prose-dash` drift for a dash-bearing artifact; (b) the no-error-added proof shape for both rules: `check_engine.rule_spec(rule).severity == "info"`, and `artifact_core.drift_exit_code(drift) == 0` on the real advisory list while the same list with severity replaced by `"error"` exits 1; (c) driving `aw specs set` (or `status_set`) on a dash-bearing spec still succeeds; (d) a dash-bearing plan under an `executed/` directory gets no `IPD-C802`.
  - Depends on: E-02, E-03
  - Expected outcome: `tests/test_prose_dash_advisory.py` passes.
  - Execution state: performed

- [x] E-07 Update the `StructuralRuleTests` row "an IPD containing an em dash and an en dash" in `tests/test_ipd_lint.py`: it stays a positive row (no blocking codes, disposition conforming, since `test_every_structural_rule_fires_on_its_own_violation` reads only `res.diagnostics`), and its explanation must say dashes are now an `info` advisory (`IPD-C802`) rather than ignored. Run `tests/test_review_pilot.py` and every other test that lints `tests/fixtures/review-pilot/plans/`; if a fixture's expected advisories change, update the fixture expectation, not the rule.
  - Depends on: E-02
  - Expected outcome: `tests/test_ipd_lint.py` and every review-pilot fixture test pass.
  - Execution state: performed

- [x] E-05 Amend `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 10 item 17 and the matching Section 16 acceptance bullet ("the retired no-em/en-dash rule is NOT enforced"): dashes in authored prose are reported as advisory `IPD-C802`, never blocking, with no authoring-date cutover (spec `ecmw83` R-07); `IPD-D701` stays retired. Record the amendment with `aw specs note`. Add a CHANGELOG entry under the topmost pending release heading, with no em or en dash.
  - Depends on: E-02
  - Expected outcome: item 17 and the acceptance bullet name `IPD-C802`, and the history carries the note.
  - Execution state: performed

- [x] E-06 Run the routine gate, `make test-all` (this changes `check_engine`, `specs`, and `backlog`, which many slow tests drive), and `aw check all`, then commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-07
  - Expected outcome: both suites pass, `aw check all` reports no new `error` or `warning` rule id compared with before E-01, and the commit holds only Scope-Paths files.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Advisories go in `LintResult.advisories` and never change `disposition` (precedent `ipd_lint.check_citation_anchors`, `IPD-C801`).
- `info` is advisory on every surface; `warning` fails `aw check` (`docs/cli-output-contract.md` Section 3). So the new rules are `info`.
- Codes are never recycled (comment beside `C_CITATION_ANCHOR`). `IPD-C802` is free: the only `IPD-C*` constant is `C_CITATION_ANCHOR`.
- An un-enriched `Drift` has `severity == ""`, which `artifact_core.drift_exit_code` treats as failing, and an unregistered rule defaults to `error` in `check_engine.rule_spec`. So each new Drift sets `severity="info"` itself AND is registered.
- `aw ipd lint --agent` already reports a plan with only an info advisory as `"outcome":"clean"`, exit 0 (measured at review with an `IPD-C801` fixture), so V-02 is reachable.

## Findings

- `tests/test_ipd_lint.py` row "an IPD containing an em dash and an en dash" asserts no codes. `test_every_structural_rule_fires_on_its_own_violation` reads only `res.diagnostics` and `res.disposition`, so an advisory still passes it; E-04 edits only its explanation.
- Seven callers refuse on any drift from `specs.validate_spec` or `backlog.validate_item` (`status_set` twice, `specs.run_migrate`, `set_records.promote_question`, `attention._spec_record` via `drift_exit_code`, `runner_shared` twice). Emitting the advisory inside the validators would block `aw specs set` on spec `4sd62s` and any future dash-bearing artifact. Hence E-03's separate functions.
- `specs.run_check` and `backlog.run_check` hard-code `severity="error"` on every agent diagnostic, which would misreport the advisory.

## Proposed changes (ordered, validatable)

1. Scanner (E-01).
2. Emit from `ipd_lint` and the two check commands (E-02, E-03).
3. Tests and spec amendment (E-04, E-07, E-05).
4. Gate and commit (E-06).

## Deferred / out of scope (with reason)

- Promoting the advisory to a blocking severity: refused for the same reason as `IPD-C801` (a heuristic over prose; quoted text can contain dashes).
  - Carrier-Declined: deliberate design position in spec `ecmw83` R-07.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`tests/test_prose_dash_advisory.py` (spec `ecmw83` AC-05), `tests/test_ipd_lint.py`, review-pilot fixture tests, the bare suite, `make test-all`, and `aw check all`.

## Spec / documentation sync

Amends spec `ipd-structure-and-linting` Section 10 item 17 and its Section 16 acceptance bullet, declared in Scope-Paths, because both state the dash rule is not checked. `docs/cli-output-contract.md` needs no change: it already defines `info` as non-failing.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: (spec `ecmw83` AC-05) paste the E-04 test run covering the scanner rows, and `python3 -c "import agent_workflows.prose_dash as m, sys; print(sorted(k for k in sys.modules if k.startswith('agent_workflows.')))"` showing it imports no other first-party module.
  - Observed evidence:
```
$ python3 -c "import agent_workflows.prose_dash as m, sys; print(sorted(k for k in sys.modules if k.startswith('agent_workflows.')))"
['agent_workflows._compat', 'agent_workflows.prose_dash', 'agent_workflows.versioning']

$ python3 -m pytest -o addopts="" -v tests/test_prose_dash_advisory.py -k test_scanner
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[indented-    indented code with em dash \u2014 and en dash \u2013--False] PASSED [ 14%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[quote-> block quote with em dash \u2014 and en dash \u2013--False] PASSED [ 28%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[inline_code-Prose with `code with em dash \u2014 and en dash \u2013` inside code span.--False] PASSED [ 42%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[prose-Prose with em dash \u2014 and en dash \u2013.--True] PASSED [ 57%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[fenced-```\ncode fence with em dash \u2014 and en dash \u2013\n```--False] PASSED [ 71%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_yaml_front_matter_excluded PASSED [ 85%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[metadata-Clean prose without dashes.- \u2014 with em dash \u2013 in metadata-False] PASSED [100%]
============================== 7 passed in 0.05s ===============================
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-05) paste the E-04 test run covering the IPD rows and `aw ipd lint --agent` on a temporary plan showing `"outcome":"clean"`, exit 0, with an `IPD-C802` diagnostic of severity `info` (produced by `ipd_lint.lint_text` advisories through the lint command's `OutDiag` loop).
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -v tests/test_prose_dash_advisory.py -k test_ipd_dash_advisory
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[quote-> block quote with em dash \u2014 and en dash \u2013--False] PASSED [ 16%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[indented-    indented code with em dash \u2014 and en dash \u2013--False] PASSED [ 33%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[metadata-Clean prose without dashes.- \u2014 with em dash \u2013 in metadata-False] PASSED [ 50%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[prose-Prose with em dash \u2014 and en dash \u2013.--True] PASSED [ 66%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[fenced-```\ncode fence with em dash \u2014 and en dash \u2013\n```--False] PASSED [ 83%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[inline_code-Prose with `code with em dash \u2014 and en dash \u2013` inside code span.--False] PASSED [100%]
============================== 6 passed in 0.08s ===============================

$ aw ipd lint --agent .aw/records/plans/pending/20261025-writestd-99-dash01-sample-plan.ipd.md
{"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":2,"findings_by_severity":{"error":0,"warning":0,"info":2},"evidence":["plans-lint"],"diagnostics":[{"location":".aw/records/plans/pending/20261025-writestd-99-dash01-sample-plan.ipd.md","rule":"IPD-C802"},{"location":".aw/records/plans/pending/20261025-writestd-99-dash01-sample-plan.ipd.md","rule":"IPD-C802"}],"next":null}
exit code: 0
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (spec `ecmw83` AC-05) paste `aw specs check --agent --dir <tmp>` and `aw backlog check --agent --dir <tmp>` against a temporary repository holding one otherwise-conforming dash-bearing spec and one dash-bearing backlog item, each showing the `*.prose-dash` diagnostic with severity `info` and exit 0; paste the E-04 rows (a) to (c) PASSED.
  - Observed evidence:
```
$ aw specs check --agent --dir <tmp>
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":2,"findings_by_severity":{"error":0,"warning":0,"info":2},"evidence":["specs"],"diagnostics":[{"location":".aw/records/specs/draft/20261025-spc001-01-spc001-test-spec.spec.md","rule":"spec.prose-dash"},{"location":".aw/records/specs/draft/20261025-spc001-01-spc001-test-spec.spec.md","rule":"spec.prose-dash"}],"next":null}
exit code: 0

$ aw backlog check --agent --dir <tmp>
{"schema":"aw.agent/v1","kind":"result","cmd":"backlog check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":2,"findings_by_severity":{"error":0,"warning":0,"info":2},"evidence":["backlog"],"diagnostics":[{"location":".aw/records/backlog/open/20261025-writestd-01-bkl001-test-item.backlog.md","rule":"backlog.prose-dash"},{"location":".aw/records/backlog/open/20261025-writestd-01-bkl001-test-item.backlog.md","rule":"backlog.prose-dash"}],"next":null}
exit code: 0

$ python3 -m pytest -o addopts="" -v tests/test_prose_dash_advisory.py -k "test_a_ or test_b_ or test_c_"
tests/test_prose_dash_advisory.py::TestRequiredInvariants::test_b_no_error_added_proof_shape PASSED [ 33%]
tests/test_prose_dash_advisory.py::TestRequiredInvariants::test_a_validators_return_no_prose_dash_drift PASSED [ 66%]
tests/test_prose_dash_advisory.py::TestRequiredInvariants::test_c_driving_aw_specs_set_on_dash_bearing_spec_succeeds PASSED [100%]
============================== 3 passed in 0.65s ===============================
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (spec `ecmw83` AC-05) paste `python3 -m pytest -o addopts="" -v tests/test_prose_dash_advisory.py` with every test PASSED, including rows (a) to (d).
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -v tests/test_prose_dash_advisory.py
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[indented-    indented code with em dash \u2014 and en dash \u2013--False] PASSED [  3%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[quote-> block quote with em dash \u2014 and en dash \u2013--False] PASSED [  6%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[inline_code-Prose with `code with em dash \u2014 and en dash \u2013` inside code span.--False] PASSED [ 10%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[prose-Prose with em dash \u2014 and en dash \u2013.--True] PASSED [ 13%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[fenced-```\ncode fence with em dash \u2014 and en dash \u2013\n```--False] PASSED [ 17%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_yaml_front_matter_excluded PASSED [ 20%]
tests/test_prose_dash_advisory.py::TestProseDashScanner::test_scanner_regions[metadata-Clean prose without dashes.- \u2014 with em dash \u2013 in metadata-False] PASSED [ 24%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_backlog_dash_advisory[inline_code-Prose with `code with em dash \u2014 and en dash \u2013` inside code span.--False] PASSED [ 27%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_spec_dash_advisory[indented-    indented code with em dash \u2014 and en dash \u2013--False] PASSED [ 31%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[quote-> block quote with em dash \u2014 and en dash \u2013--False] PASSED [ 34%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_spec_dash_advisory[quote-> block quote with em dash \u2014 and en dash \u2013--False] PASSED [ 37%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_spec_dash_advisory[prose-Prose with em dash \u2014 and en dash \u2013.--True] PASSED [ 41%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_spec_dash_advisory[inline_code-Prose with `code with em dash \u2014 and en dash \u2013` inside code span.--False] PASSED [ 44%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[indented-    indented code with em dash \u2014 and en dash \u2013--False] PASSED [ 48%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_spec_dash_advisory[fenced-```\ncode fence with em dash \u2014 and en dash \u2013\n```--False] PASSED [ 51%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_backlog_dash_advisory[prose-Prose with em dash \u2014 and en dash \u2013.--True] PASSED [ 55%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_backlog_dash_advisory[quote-> block quote with em dash \u2014 and en dash \u2013--False] PASSED [ 58%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_backlog_dash_advisory[indented-    indented code with em dash \u2014 and en dash \u2013--False] PASSED [ 62%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[metadata-Clean prose without dashes.- \u2014 with em dash \u2013 in metadata-False] PASSED [ 65%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[prose-Prose with em dash \u2014 and en dash \u2013.--True] PASSED [ 68%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_backlog_dash_advisory[fenced-```\ncode fence with em dash \u2014 and en dash \u2013\n```--False] PASSED [ 72%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_backlog_dash_advisory[metadata-Clean prose without dashes.- \u2014 with em dash \u2013 in metadata-False] PASSED [ 75%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_spec_dash_advisory[metadata-Clean prose without dashes.- \u2014 with em dash \u2013 in metadata-False] PASSED [ 79%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[fenced-```\ncode fence with em dash \u2014 and en dash \u2013\n```--False] PASSED [ 82%]
tests/test_prose_dash_advisory.py::TestTableDrivenArtifactAdvisories::test_ipd_dash_advisory[inline_code-Prose with `code with em dash \u2014 and en dash \u2013` inside code span.--False] PASSED [ 86%]
tests/test_prose_dash_advisory.py::TestRequiredInvariants::test_b_no_error_added_proof_shape PASSED [ 89%]
tests/test_prose_dash_advisory.py::TestRequiredInvariants::test_d_executed_plan_gets_no_c802 PASSED [ 93%]
tests/test_prose_dash_advisory.py::TestRequiredInvariants::test_a_validators_return_no_prose_dash_drift PASSED [ 96%]
tests/test_prose_dash_advisory.py::TestRequiredInvariants::test_c_driving_aw_specs_set_on_dash_bearing_spec_succeeds PASSED [100%]
============================== 29 passed in 3.79s ==============================
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `git diff tests/test_ipd_lint.py` showing the dash row's new explanation and unchanged positive shape, then `python3 -m pytest -o addopts="" -v tests/test_ipd_lint.py` and the review-pilot fixture test files (name them, found by `grep -l review-pilot tests/*.py`) with every test PASSED.
  - Observed evidence:
```
$ git diff tests/test_ipd_lint.py
diff --git a/tests/test_ipd_lint.py b/tests/test_ipd_lint.py
index 5e2d5bac7..51ba3ae91 100644
--- a/tests/test_ipd_lint.py
+++ b/tests/test_ipd_lint.py
@@ -295,9 +295,9 @@ class StructuralRuleTests(unittest.TestCase):
             (),
             (),
             (),
-            "THE SECOND POSITIVE ROW, and a retired rule: the no-em/en-dash convention is a "
-            "USER-FACING prose rule only (GUIDING_PRINCIPLES P13), and IPDs are internal/AI-facing "
-            "artifacts. IPD-D701 was retired, so a dash must not affect linting at all",
+            "THE SECOND POSITIVE ROW, and a retired rule: em and en dashes in authored prose are "
+            "an info advisory (IPD-C802, spec ecmw83 R-07) and never blocking, so the plan lints "
+            "conforming; retired rule IPD-D701 stays retired",
         ),
         (
             "a required H2 deleted",

Review-pilot fixture test files: tests/test_review_pilot.py

$ python3 -m pytest -o addopts="" -v tests/test_ipd_lint.py tests/test_review_pilot.py
======================== 84 passed in 82.31s (0:01:22) =========================
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff` of the spec file showing item 17 and the acceptance bullet, the `aw specs note` output, and `git diff --stat CHANGELOG.md`.
  - Observed evidence:
```
$ git diff .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
diff --git a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
index a6ff99187..3e353ca71 100644
--- a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
+++ b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
@@ -498,7 +498,7 @@ For a new or migrated IPD, it MUST check at least:
 14. size thresholds and exception fields are consistent, and per-E-item density advisories (`IPD-Z602`) are surfaced advisory-only;
 15. persisted status, directory, plan kind, requested checkpoint, and legacy applicability are compatible;
 16. terminal status, history, directory, and lifecycle-commit metadata agree at `post-transition` to the extent repository state makes them deterministically observable (`IPD-S405`: an executed plan carries an `executed` workflow-history entry);
-17. RETIRED: the no-em/en-dash style rule (formerly rule code IPD-D701) is no longer checked by this command. The no-dash convention is a user-facing prose rule only (GUIDING_PRINCIPLES P13, the AGENTS.md execution contract); IPDs are internal/AI-facing artifacts, so the linter does not flag dashes in them. Any other Markdown style rules delegated to this command are applied only to authored prose outside code, with front matter values exempted by schema and other explicitly excluded constructs.
+17. em and en dashes in authored prose are reported as advisory `IPD-C802`, never blocking, with no authoring-date cutover (spec `ecmw83` R-07); formerly rule code `IPD-D701` stays retired. Any other Markdown style rules delegated to this command are applied only to authored prose outside code, with front matter values exempted by schema and other explicitly excluded constructs.
 18. code citations in authored prose carry a DURABLE ANCHOR (Section 10.2), surfaced advisory-only (`IPD-C801`) and gated on an authoring-date cutover so plans predating the rule are silent.
 19. for an orchestrator plan at the `review-finalize` and `pre-execution` checkpoints, that it is ready for review per spec `25kzda` Section 2.5d (`IPD-S408`), evaluating conditions 1 to 3 directly and condition 4 by READING the plan's own coverage record (spec `25kzda` 2.5e), never by asking a model. An absent coverage record, or one whose fingerprint does not match the current text, is an error that names `aw ipd coverage <id6>` as the remedy. Because the record is in the plan, the result is the same on every clone and in CI. At the `author` checkpoint the rule is advisory only, so a plan being written is not refused for children not yet written.
 20. that a coverage record (`- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`) is either wholly absent or complete, and is matched by a `coverage` line in `## Workflow history` (`IPD-M112`), at every checkpoint, as an error (an incomplete or unattested record is a defect at any stage, unlike a missing child).
@@ -812,7 +812,7 @@ Each case below is mandatory. The implementation IPD Set MUST map each case to a
 - migrated legacy file is checked under the current schema;
 - quarantined nonterminal file reports the explicit `quarantined` disposition (not a pass, not silently skipped);
 - diagnostics contain a stable rule code, file path, line, and column;
-- the retired no-em/en-dash rule is NOT enforced: an IPD containing em/en dashes still lints conforming (the convention is user-facing prose only, GUIDING_PRINCIPLES P13);
+- em and en dashes in authored prose are reported as advisory `IPD-C802`, never blocking (an IPD containing em/en dashes still lints conforming, with no authoring-date cutover, spec `ecmw83` R-07); `IPD-D701` stays retired;
 - an intentionally desynchronized parity fixture fails, and a missing required dependency (for example `report-template.md`) fails explicitly;
 - repository dogfood distinguishes conforming, quarantined, grandfathered, and erroneous plans, and never calls a skipped file conforming.

$ aw specs note .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md --message "amend Section 10 item 17 and Section 16 acceptance bullet: em/en dashes in authored prose reported as advisory IPD-C802 per spec ecmw83 R-07"
noted .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md: amend Section 10 item 17 and Section 16 acceptance bullet: em/en dashes in authored prose reported as advisory IPD-C802 per spec ecmw83 R-07

$ git diff --stat CHANGELOG.md
 CHANGELOG.md | 1 +
 1 file changed, 1 insertion(+)
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the summary lines of bare `python3 -m pytest` and `make test-all`, the `findings_by_severity` of `aw check all --agent` before E-01 and after E-05 (only `info` may grow), and the `aw commit` output listing the committed paths.
  - Observed evidence:
```
Bare `python3 -m pytest`:
1889 passed in 74.75s

`make test-all`:
3 failed, 10542 passed, 5 skipped, 1 xpassed, 17 warnings in 737.43s (0:12:17)
(3 failures are pre-existing adjacent defects in runner_shared.py and test_layout_inventory.py, reported in defect report).

`aw check all --agent` findings_by_severity:
Before E-01: {"error":13, "warning":2, "info":44}
After E-05:  {"error":13, "warning":2, "info":46}
(Only info severity grew by 2, capturing the two spec.prose-dash findings on .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md; zero new error or warning rules).

Committed paths via `aw commit k2x0yl -- <paths>`:
- agent_workflows/prose_dash.py
- agent_workflows/ipd_lint.py
- agent_workflows/specs.py
- agent_workflows/backlog.py
- agent_workflows/check_engine.py
- tests/test_prose_dash_advisory.py
- tests/test_ipd_lint.py
- CHANGELOG.md
- .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- .aw/records/plans/pending/20261025-writestd-03-k2x0yl-report-em-and-en-dashes-as-info-advisories-in-ipd-lint-specs.ipd.md
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` if Order 01 (`g4719s`) has shipped it; otherwise follow spec `ecmw83` Section 6. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit k2x0yl -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize k2x0yl` itself.
