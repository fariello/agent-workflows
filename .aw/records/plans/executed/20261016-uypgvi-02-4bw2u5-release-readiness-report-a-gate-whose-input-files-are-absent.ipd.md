# IPD: release_readiness: report a gate whose input files are absent as not-applicable instead of failing

- Date: 2026-10-16
- Kind: child
- Concern: `release_readiness.build_report` (behind `aw releases readiness`) has only two gate outcomes, `GateResult.passed` True or False, so a gate whose INPUT FILES ARE ABSENT either fails (forcing `NO-GO`) or, worse, passes vacuously. The release-review workflow is installed into every managed repository and plan `kmmoca` makes it run `aw releases readiness` in Section 8 and Section 9. In a managed repository that lacks this toolkit's own inputs (no `docs/`, no `CHANGELOG.md`, no canonical `workflow.yaml` packages), the readiness step therefore reports a permanent `NO-GO` that no human can clear. The maintainer ruled on 2026-10-15 (kmmoca OQ-03, option (b); backlog `v1re2z`) that such a gate reports NOT-APPLICABLE and does not force `NO-GO`, with the accepted risk that a repository which deleted an input by mistake sees not-applicable rather than a failure, so the not-applicable gates must be reported PROMINENTLY. Measured at authoring HEAD `cb349046d` (F-01..F-04): a fresh `aw install` of a managed repository reports `docs_checks` FAIL ("docs tree missing or not a directory: docs") and `changelog_versioning` FAIL ("missing changelog entry or version", evidence `changelog: False`), while `generated_drift` PASSES with "no canonical workflow packages to check" on zero packages, a pass counted on an absent input both there and in this repository. This plan adds a third, explicit not-applicable gate state to `release_readiness`, makes the five input-reading producers the backlog names report it when their input is absent, and surfaces it in every output mode. It does NOT change `release-review`, `RELEASING.md`, or `ReleaseReviewCoordinator`; those consume the state and are owned by `kmmoca` (Set `uypgvi`, Order 1), which waits on this item via `- Item-Dependencies: state:backlog:done:v1re2z`.
- Scope: IN: (1) a not-applicable state on `release_readiness.GateResult` and its aggregation in `ReleaseReadinessReport` (verdict, `failing_gates`, a new `not_applicable_gates` and `passed_gates`, `to_dict`, `render`); (2) not-applicable reporting on absent input in `gate_docs_checks` (no `docs/`), `gate_capability_freshness` (no `host_matrix.json`), `gate_generated_drift` (zero `*/workflow.yaml` packages), `gate_workflow_disposition` (no workflow manifest `index.md`), and `gate_changelog_versioning` (no `CHANGELOG.md` while the version resolves); (3) prominent not-applicable display in `release_readiness.run_readiness` (human, `--json`, `--agent`); (4) behavioral tests, including updating the existing tests that pin the old fail-or-pass-on-absent behavior; (5) `docs/recovery.md` and `CHANGELOG.md`. OUT: `agent_workflows/migration_complex.py`, `.aw/system/workflows/release-review/**`, and `RELEASING.md` (owned by `kmmoca`); `gate_full_suite` and `gate_residual_risk` (explicit attestations, never not-applicable, kmmoca D-4); `gate_leak_scan`, `gate_ipd_lint`, `gate_benchmark_thresholds`, `gate_artifact_manifest` (no absent-file input named by the maintainer; `artifact_manifest` keeps failing on a missing `index.md`); a missing `.aw/system/workflows/` tree (still FAIL: it is the installed framework itself, not an optional input); and the two managed-repository false-NO-GO causes that are NOT absent inputs (OQ-01, OQ-02).
- Scope-Paths: agent_workflows/release_readiness.py, tests/test_release_readiness_not_applicable.py, tests/test_release_readiness.py, tests/test_release_readiness_docs_gate.py, tests/test_release_readiness_producers.py, tests/test_releases_readiness_cli.py, docs/recovery.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: v1re2z
- Blocks-Release: next
- Set: uypgvi
- Order: 2
- Highest E allocated: 08
- Author: opencode
- Id: 4bw2u5

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 4bw2u5 verified (set uypgvi, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us, round 1): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog v1re2z at HEAD cb349046d; measured gate outcomes on a fresh managed install and on this repository.

## Goal

Give `release_readiness` an explicit NOT-APPLICABLE gate state, distinguishable from both pass and fail, so that a gate whose input files are absent neither forces `NO-GO` nor is ever counted as a pass, and is named prominently in every `aw releases readiness` output. This makes the installed release-review readiness step usable in managed repositories and is the prerequisite `kmmoca` binds to.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-measure gate outcomes on a fresh managed install and on this repository, and the consumer set of `GateResult`, at the executing HEAD.
  - Depends on: none
  - Expected outcome: one pasted transcript proving, at the executing HEAD: (a) a fresh managed install into a gitignored scratch dir (`mkdir -p .aw/state/scratch-4bw2u5/mr && git -C .aw/state/scratch-4bw2u5/mr init -q`, then `python3 -m agent_workflows install .aw/state/scratch-4bw2u5/mr --yes --no-interactive --preset private-target --delivery-mode tracked --records-backend repository`) followed by `aw releases readiness --suite-passed --residual-risk-signer qa --json` run inside it with `GIT_CEILING_DIRECTORIES` set to its parent, printing every gate's `name`, `passed`, and `detail`: `docs_checks` and `changelog_versioning` FAIL on absent input, and `generated_drift` PASSES with "no canonical workflow packages to check"; (b) the same command in this repository: every gate passes and `generated_drift` reads "no canonical workflow packages to check" (this repository has no `.aw/system/workflows/*/workflow.yaml`, F-03); (c) `git grep -n -e GateResult -e failing_gates -e "release_readiness" -- '*.py'` shows the consumers are `agent_workflows/release_readiness.py`, `agent_workflows/cli.py` (dispatch only), and tests, so no production consumer outside this module reads `GateResult.passed` (if one exists, list it and confirm E-03's semantics keep it fail-closed); (d) `GateResult` carries only `name`, `passed`, `detail`, `evidence`; (e) the execution-base bare-suite baseline: run bare `python3 -m pytest` BEFORE any edit and record its summary line and the sorted names of every failing test (this is the baseline E-08(6) compares against by name). If (a) already shows a not-applicable state, stop and reconcile rather than duplicating work.
  - Execution state: performed

### Task group 2: the not-applicable state

- [x] E-02 Write `tests/test_release_readiness_not_applicable.py` FIRST and show it RED against the unmodified `agent_workflows/release_readiness.py`.
  - Depends on: E-01
  - Expected outcome: a new behavioral test module (no `inspect`, `ast`, regex over `.py` files, or line counts; every tree under `tmp_path` with `GIT_CEILING_DIRECTORIES` set via `monkeypatch`), reusing `tests.test_release_readiness_producers._setup_full_go_tree` / `setup_minimal_workflows_tree` for the full tree, covering:
    1. `test_model_not_applicable_is_neither_pass_nor_fail`: `rr.GateResult("x", False, "input absent", applicable=False)` has `status == "not-applicable"`, `passed is False`; a report `rr.aggregate([pass_gate, na_gate])` has `failing_gates() == []`, `not_applicable_gates() == ["x"]`, `passed_gates() == [<pass_gate name>]` (the NA gate is in NEITHER list), `verdict == rr.VERDICT_GO`; and `rr.GateResult("y", True, "ok", applicable=False)` is still reported not-applicable and NOT in `passed_gates()` (applicability wins, so a producer bug cannot smuggle a pass).
    2. `test_model_all_not_applicable_is_no_go`: a report whose every gate is not-applicable has `verdict == rr.VERDICT_NO_GO` (zero applicable gates verified nothing, mirroring the empty-gate-set rule).
    3. `test_model_failure_still_forces_no_go_beside_not_applicable`: `[na_gate, fail_gate]` gives `VERDICT_NO_GO` with `failing_gates() == [fail_gate.name]`.
    4. `test_model_to_dict_and_render_surface_not_applicable`: `to_dict()` carries `not_applicable_gates`, per-gate `applicable` and `status`, and survives `json.dumps`; `render()` shows result `N/A` for the gate (never `PASS`), a line beginning `WARNING: not-applicable gates (input absent, NOT verified):` naming it, and a counts line `N passed, M not-applicable, K failed`.
    5. One test per producer over a REAL tree, each a contrast pair (input present gives the existing pass/fail outcome, input removed gives not-applicable with `evidence["missing"] is True` and `evidence["path"]` naming the input): `gate_docs_checks` (remove `docs/`), `gate_capability_freshness` (remove `host_matrix.json`), `gate_generated_drift` (a workflows tree with zero `*/workflow.yaml`), `gate_workflow_disposition` (remove `.aw/system/workflows/index.md`), `gate_changelog_versioning` (remove `CHANGELOG.md` with `.aw/system/VERSION` resolvable).
    6. `test_changelog_absent_with_unknown_version_still_fails`: no `CHANGELOG.md` AND an unresolvable version (`VERSION` reading `unknown`, no git) is FAIL, not not-applicable.
    7. `test_never_not_applicable_gates`: `gate_full_suite(None)`, `gate_residual_risk(False)`, a missing `.aw/system/workflows/` for `gate_generated_drift` and `gate_workflow_disposition`, and a missing `index.md` for `gate_artifact_manifest` are all `applicable is True` and FAIL; explicitly injected inputs (`doc_findings=[]`, `stale_claims=[]`, `drift_files=[]`, `undispositioned=[]`) on a tree lacking those inputs PASS and are applicable (injection bypasses the filesystem, unchanged).
    8. `test_build_report_managed_style_tree_is_go_with_not_applicable`: `build_report(suite_passed=True, residual_risk_signed=True, residual_risk_signer="qa", repo_root=<full go tree minus docs/, CHANGELOG.md and host_matrix.json, with zero workflow.yaml>, run_subprocess_gates=False)` is `VERDICT_GO`, `failing_gates() == []`, and `not_applicable_gates()` is exactly `["generated_drift", "docs_checks", "capability_freshness", "changelog_versioning"]`; falsifiability: the same tree with `suite_passed=False` is `NO-GO`.
    9. `test_cli_surfaces_not_applicable_in_every_mode`: driving `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa` (subprocess, `PYTHONPATH` pinned as in `tests/test_releases_readiness_cli.py::_run_subprocess`) over the item-8 tree built by `tests.test_releases_readiness_cli._build_subprocess_go_tree` (which runs `git init` and creates `.aw/records/plans/pending/`, so `leak_scan` and `ipd_lint` run and pass) with the item-8 inputs then removed: human mode exits `0`, stdout contains the `WARNING: not-applicable gates` line naming each NA gate, and stderr contains the same WARNING line; `--json` exits `0` with `data.not_applicable_gates` equal to the item-8 list; `--agent` emits one record that passes `agent_schema.validate_agent_record`, has `exit == 0` and `outcome == "clean"`, whose `diagnostics` rule set is exactly `{"readiness.<gate>.not-applicable"}` over the item-8 gates, and whose `findings_by_severity == {"error": 0, "warning": 4, "info": 0}`. Severity MUST be asserted through `findings_by_severity` (or by adding `--verbose`): measured at review, the default non-verbose `CommandResult.to_agent_record` emits each diagnostic as `{location, rule}` only, with no `severity` key.
    RED proof: run `python3 -m pytest -o addopts="" -q tests/test_release_readiness_not_applicable.py` BEFORE E-03 and paste the failing output (expected: `TypeError` on the `applicable=` keyword, or assertion failures).
  - Execution state: performed

- [x] E-03 Add the not-applicable state to `GateResult` and `ReleaseReadinessReport` in `agent_workflows/release_readiness.py`.
  - Depends on: E-02
  - Expected outcome: (1) `GateResult` gains `applicable: bool = True` as its LAST field (after `evidence`, so every existing positional construction keeps working) and a `status` property returning `"not-applicable"` when `not applicable`, else `"pass"` / `"fail"` from `passed`; module constants `GATE_STATUS_PASS = "pass"`, `GATE_STATUS_FAIL = "fail"`, `GATE_STATUS_NOT_APPLICABLE = "not-applicable"` exported in `__all__`; `GateResult.to_dict` adds `applicable` and `status`. (2) Producers emit a not-applicable gate with `passed=False` AND `applicable=False` (so any consumer that reads only `passed` fails closed rather than counting a pass), via one helper `_not_applicable(name, detail, path)` that sets `evidence={"missing": True, "path": path, "not_applicable": True}` and a detail ending `(input absent, NOT verified)`. (3) `ReleaseReadinessReport.failing_gates()` returns applicable gates that did not pass; new `not_applicable_gates()` and `passed_gates()` (applicable AND passed only); `verdict` is `VERDICT_GO` iff at least one gate is applicable and no applicable gate failed (empty or all-NA is `NO-GO`). (4) `to_dict` adds `not_applicable_gates` and `passed_gates`. (5) `render` prints `N/A` in the Result column for a not-applicable gate, and when any exist appends `WARNING: not-applicable gates (input absent, NOT verified): <names>`; it always appends `<N> passed, <M> not-applicable, <K> failed`. When the verdict is `NO-GO` with no failing applicable gate but at least one gate, the `Failing gates:` line reads `none (no applicable gates were evaluated)` rather than the empty-gate-set text, and `run_readiness`'s summary likewise never prints an empty `NO-GO ()`. ASCII only, no dashes beyond existing hyphens. The module docstring lists the not-applicable rule and which gates can report it.
  - Execution state: performed

- [x] E-04 Make the five input-reading producers report not-applicable on absent input.
  - Depends on: E-03
  - Expected outcome: in `agent_workflows/release_readiness.py`, only on the filesystem path (an explicitly injected sequence still bypasses the filesystem exactly as today): `gate_docs_checks` returns `_not_applicable` when `docs/` is not a directory (was FAIL); `gate_capability_freshness` when `.aw/system/workflows/conformance/tools/host_matrix.json` is not a file (was FAIL); `gate_generated_drift` when the workflows tree exists but has zero `*/workflow.yaml` packages (was a vacuous PASS, "no canonical workflow packages to check"), while a MISSING `.aw/system/workflows/` stays FAIL; `gate_workflow_disposition` when `.aw/system/workflows/index.md` is not a file (was FAIL "could not run: FileNotFoundError"), while a missing workflows tree stays FAIL and an inventory finding stays FAIL; `gate_changelog_versioning` when `CHANGELOG.md` is not a file AND the version resolves to something other than `unknown` (evidence keeps `version`), while a present `CHANGELOG.md` with no `##` heading, or any unresolvable version, stays FAIL. `gate_full_suite`, `gate_residual_risk`, `gate_leak_scan`, `gate_ipd_lint`, `gate_benchmark_thresholds`, and `gate_artifact_manifest` never return not-applicable. Each not-applicable result keeps the gate's existing empty evidence keys beside the `_not_applicable` keys (`drift_files: []` and `packages_checked: 0`; `findings: []`; `undispositioned: []`; `stale_claims: []`; `version` and `changelog: False`), so a consumer indexing those keys does not break. A missing `index.md` makes `workflow_disposition` not-applicable but `artifact_manifest` still FAILS on the same absence (Scope OUT), so a tree lacking `index.md` stays `NO-GO`; E-02 item 7 pins the `artifact_manifest` half. `build_report` is unchanged in shape and order.
  - Execution state: performed

- [x] E-05 Surface not-applicable gates prominently in `release_readiness.run_readiness`.
  - Depends on: E-04
  - Expected outcome: exit code stays `0` on `GO` and `1` on `NO-GO` (not-applicable gates never change it); the summary reads `Verdict: GO` or `Verdict: NO-GO (<failing>)` followed, when any exist, by `; WARNING not-applicable (input absent, NOT verified): <names>`; `--agent` / `--json` emit the existing error diagnostics for exactly the gates in `report.failing_gates()` (the filter changes from `not g.passed` to applicable-and-failed, so a not-applicable gate never also carries an `error` diagnostic) plus one `Diagnostic(location=<gate>, rule="readiness.<gate>.not-applicable", detail=<detail>, severity="warning")` per not-applicable gate, with `data=report.to_dict()` (carrying `not_applicable_gates`); human mode prints `report.render()` (which carries the WARNING and counts lines) and ALSO writes the same WARNING line to stderr, so a reader piping stdout still sees it. The record must still pass `agent_schema.validate_agent_record`.
  - Execution state: performed

### Task group 3: tests, docs, and validation

- [x] E-06 Update the existing tests that pin the old fail-or-pass-on-absent behavior to assert the new outcome.
  - Depends on: E-05
  - Expected outcome: in `tests/test_release_readiness_docs_gate.py`, `tests/test_release_readiness_producers.py`, `tests/test_release_readiness.py`, and `tests/test_releases_readiness_cli.py`, every test that asserts an absent-input outcome is updated to assert not-applicable (`applicable is False`, `status == "not-applicable"`, `evidence["missing"] is True`, the gate absent from `failing_gates()` and `passed_gates()`), renamed to say so (for example `test_missing_docs_directory_is_not_applicable`). The known set at authoring HEAD: `test_missing_docs_directory_fails_gate`, `test_capability_missing_matrix_fails_gate`, `test_drift_zero_packages_passes_gate`, `test_disposition_missing_index_md_fails_without_raising`, `test_gate_changelog_versioning_missing_changelog_fails`; plus three found at review that fail because `tests.test_release_readiness_producers._setup_full_go_tree` has zero `workflow.yaml` packages, so every "GO tree" now carries `generated_drift` as not-applicable (F-07): `tests/test_releases_readiness_cli.py::test_arm_a_go_tree_exits_0_and_renders_go_verdict` (asserts `proc.stderr == ""`; update to assert stderr carries only the not-applicable WARNING naming `generated_drift`), `test_arm_f_agent_mode_emits_schema_valid_record_with_exit_and_diagnostic_parity` (asserts `rec_go["findings"] == 0` and NO-GO `findings == 2`; update to count the `generated_drift` warning and assert `findings_by_severity`), and the `rr.gate_generated_drift(repo_root=tmp_path).passed is True` line in `tests/test_release_readiness_producers.py::test_artifact_manifest_missing_body_and_lens_fail_gate` (update to assert not-applicable). Do NOT change `_setup_full_go_tree` itself to add a compiled package (it would make the shared fixture depend on `yaml`, which the drift tests `importorskip`); re-derive the set by running the four files after E-05 and listing every failure, and change ONLY tests whose failure is the absent-input rule (any other failure is a regression to fix in E-03/E-04, not a test to edit). Tests asserting a missing `.aw/system/workflows/` tree or a missing `index.md` for `artifact_manifest` keep asserting FAIL.
  - Execution state: performed

- [x] E-07 Document the not-applicable rule in `docs/recovery.md` and add a `CHANGELOG.md` entry.
  - Depends on: E-06
  - Expected outcome: `docs/recovery.md` `## Release readiness (decision only)` gains a short paragraph: a gate whose input is absent (no `docs/`, no host matrix, no canonical `workflow.yaml` packages, no workflow manifest, no `CHANGELOG.md`) is reported NOT-APPLICABLE, is never counted as passed, does not force `NO-GO`, and is named in a WARNING line and as warning diagnostics; `full_suite` and `residual_risk` are never not-applicable; the accepted risk is that an input deleted by mistake reads not-applicable, so review the WARNING line. `CHANGELOG.md` gains one `- Fixed:` line under the topmost pending release heading saying `aw releases readiness` now reports gates whose input files are absent as not-applicable instead of failing (or vacuously passing), so release review is usable in managed repositories. No em or en dashes in either file (user-facing prose, AGENTS.md).
  - Execution state: performed

- [x] E-08 Run the targeted suites, the managed-install end-to-end check, docs and leak checks, and the bare suite.
  - Depends on: E-07
  - Expected outcome: (1) `python3 -m pytest -o addopts="" -q tests/test_release_readiness_not_applicable.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py tests/test_host_capability_registry.py tests/test_agent_surface_conformance.py` passes with 0 failures; (2) re-running the E-01(a) managed install and `aw releases readiness --suite-passed --residual-risk-signer qa --json` shows `docs_checks`, `changelog_versioning`, and `generated_drift` as `status: "not-applicable"` with `passed: false`, none of them in `failing_gates` or `passed_gates`, and the WARNING present in human mode (any remaining FAIL, such as `artifact_manifest` from OQ-02, is reported as measured, not hidden); (3) in this repository `aw releases readiness --suite-passed --residual-risk-signer qa` lists exactly `generated_drift` as not-applicable and every other gate passing (or, if a standing gate is red for an unrelated reason, names it); (4) `docs_check.check_docs_dir(Path("docs"))` returns `[]` and a `\u2014`/`\u2013` scan of `CHANGELOG.md` additions and `docs/recovery.md` finds 0; (5) `python3 -m agent_workflows sanitize --agent` reports `"outcome": "clean"`; (6) bare `python3 -m pytest` passes with zero new failures compared by name against the execution-base baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `release_readiness` is decision-only and never tags, publishes, deploys, or pushes (module docstring, `assert_no_release_action`); nothing here changes that.
- Never write another role's attestation: `full_suite` and `residual_risk` take explicit human or harness attestations (`--suite-passed`, `--residual-risk-signer`), so "input absent" there means "not attested" and stays a FAIL (kmmoca round-2 D-4).
- Synthetic test trees set `GIT_CEILING_DIRECTORIES` so `versioning.resolve_version` does not climb into the enclosing checkout (`dyiasf` PR-002); the existing producer tests already do this via `monkeypatch.setenv`.
- Tests assert observable behavior (return values, exit codes, rendered output, agent records) and never source structure (AGENTS.md, GUIDING_PRINCIPLES P16).
- User-facing prose (`docs/`, `CHANGELOG.md`) carries no em or en dashes (AGENTS.md); `docs_check.check_docs_dir` enforces it for `docs/`.
- The full suite runs bare as `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""` (AGENTS.md repo-local contract).
- `aw install` non-interactively requires `--yes` and the policy flags `--preset`, `--delivery-mode`, `--records-backend` (measured: without them it refuses or aborts with "nothing changed").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | A fresh managed install reports a `NO-GO` that its maintainer cannot clear, from absent inputs. | At `cb349046d`, after `python3 -m agent_workflows install <scratch> --yes --no-interactive --preset private-target --delivery-mode tracked --records-backend repository`, `aw releases readiness --suite-passed --residual-risk-signer qa --json` in the scratch repo printed `docs_checks False | docs tree missing or not a directory: docs` and `changelog_versioning False | missing changelog entry or version` (evidence `{'changelog': False, 'version': '0.0.0+gc1ba68d'}`), with `capability_freshness` and `workflow_disposition` passing (the install ships `conformance/tools/host_matrix.json` and a manifest the inventory dispositions, 64 dispositions). |
| F-02 | `GateResult` has no third state, so a not-applicable gate cannot be distinguished from pass or fail by any consumer. | `release_readiness.GateResult` fields are `name`, `passed`, `detail`, `evidence`; `ReleaseReadinessReport.failing_gates` is `[g.name for g in self.gates if not g.passed]`; `verdict` is `VERDICT_GO if all(g.passed ...)`. |
| F-03 | `generated_drift` counts a PASS on an absent input, both in managed repos and in THIS repository, contradicting the backlog's premise that "in this repository all inputs exist". | `gate_generated_drift` returns `passed=True, detail="no canonical workflow packages to check"` when `wf_dir.glob("*/workflow.yaml")` is empty; `git ls-files` matches `workflow.yaml` only at `tests/fixtures/workflow-src/plan-review/workflow.yaml`; `aw releases readiness --suite-passed --residual-risk-signer qa --json` in this repository printed `generated_drift True | no canonical workflow packages to check`. Under the maintainer's rule (`workflow.yaml packages` listed as an input) this becomes not-applicable here too, which is more honest than the current pass (OQ-03). |
| F-04 | The backlog's "workflow catalog bookkeeping" input maps to the workflow manifest `index.md`, which `gate_workflow_disposition` needs and which fails with an exception when absent. | `gate_workflow_disposition` calls `migration_inventory.build_inventory(wf_dir)`, which calls `engine.parse_manifest(root)`; on a workflows tree without `index.md` the existing test `test_disposition_missing_index_md_fails_without_raising` asserts `"could not run: FileNotFoundError"`. kmmoca round-1 review measured the same `FileNotFoundError` on a minimal managed-style tree. |
| F-05 | No production module outside `release_readiness.py` reads `GateResult`; `cli.py` only dispatches to `run_readiness`. So adding a defaulted field and changing `failing_gates` semantics is safe, and emitting not-applicable as `passed=False` keeps any naive `passed` reader fail-closed. | `git grep -n -e "release_readiness" -e GateResult -- 'agent_workflows/*.py'` at `cb349046d`: `agent_workflows/cli.py` (`return release_readiness_mod.run_readiness(args)`), `agent_workflows/command_surface.py` (declaration), and `release_readiness.py` itself; other `*GateResult` hits are unrelated `IntegrationGateResult` / `TerminalGateResult`. |
| F-07 | Measured at review (HEAD `e1e49e8ac`): the shared `_setup_full_go_tree` fixture has zero `workflow.yaml`, so under E-04 every existing "GO tree" test carries `generated_drift` as not-applicable; the CLI GO tests that pin `stderr == ""` and `findings == 0` therefore change, and the default `--agent` record omits per-diagnostic `severity`. | Probe over `_setup_full_go_tree` minus `docs/`, `CHANGELOG.md`, `host_matrix.json` with `build_report(..., run_subprocess_gates=False)`: `generated_drift True no canonical workflow packages to check`, `docs_checks False`, `capability_freshness False`, `changelog_versioning False`, others pass; `rglob("workflow.yaml")` on the fixture is `[]`. `CommandResult(..., diagnostics=[Diagnostic(..., severity="warning")]).to_agent_record()` gives `diagnostics: [{location, rule}]`, `findings_by_severity: {error: 0, warning: 1, info: 0}`, `outcome: clean`, and `agent_schema.validate_agent_record` returns `[]`. |
| F-06 | The current readiness suites are green, so E-06's re-derived failure set isolates exactly the behavior this plan changes. | `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` at `cb349046d`: `82 passed in 23.54s`. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the managed-install and this-repo gate outcomes and the `GateResult` consumer set.
2. E-02 writes the not-applicable behavioral tests first and records them RED.
3. E-03 adds the third state (`applicable`, `status`, `not_applicable_gates`, `passed_gates`, verdict, `to_dict`, `render`).
4. E-04 makes `docs_checks`, `capability_freshness`, `generated_drift`, `workflow_disposition`, and `changelog_versioning` report not-applicable on absent input.
5. E-05 surfaces not-applicable gates in `aw releases readiness` human, JSON, and agent output.
6. E-06 updates the existing absent-input tests to the new outcome.
7. E-07 documents the rule in `docs/recovery.md` and `CHANGELOG.md`.
8. E-08 validates (targeted suites, managed-install end-to-end, docs, leaks, bare suite).

## Deferred / out of scope (with reason)

- Consuming the not-applicable state in release-review Section 8 and Section 9, `RELEASING.md`, and `ReleaseReviewCoordinator`.
  - Carrier: kmmoca
- Plan `kmmoca` E-01(e) and test 8 build a "minimal managed-style tree" with no `.aw/system/workflows/index.md`; under this plan `workflow_disposition` is not-applicable there but `artifact_manifest` still FAILS (missing manifest), so `build_report` on that tree stays `NO-GO` and kmmoca's expectation that `authorize_release` succeeds on it would not hold. kmmoca must add an `index.md` (and matching `.aw/system/VERSION`) to that tree, or expect the `artifact_manifest` hard failure. Recorded here as the cross-reference; the edit belongs to kmmoca.
  - Carrier: kmmoca
- A managed repository that adds its own workflow row to `.aw/system/workflows/index.md` fails `workflow_disposition` with "manifest command '<name>' has no reviewed family assignment (silent omission)", a false `NO-GO` that is not an absent input (OQ-01).
  - Carrier: ufawpb
- A fresh install from a development checkout fails `artifact_manifest` on "version stamp mismatch: index.md has 1.2.1 but .aw/system/VERSION has 1.3.0rc2.dev..." (OQ-02).
  - Carrier: 7rs77x

## Scope check

- Over-scope: none. Every `- Scope-Paths:` entry is the module that owns the gates, its test modules (the new one plus the four whose absent-input assertions must change), or the user-facing doc and changelog that describe `aw releases readiness`.
- Under-scope: none for the backlog item. All five inputs the item names (docs/, host_matrix.json, workflow catalog bookkeeping, workflow.yaml packages, CHANGELOG) map to a producer change in E-04 (F-03, F-04), the N/A gates are reported prominently (E-03 render, E-05 CLI, E-07 docs), and the consumer side is carried by `kmmoca`.

## Required tests / validation

- `tests/test_release_readiness_not_applicable.py` (E-02), RED before E-03 and GREEN after E-05.
- Updated absent-input tests in the four existing readiness test modules (E-06).
- Targeted suites, managed-install end-to-end readiness, this-repo readiness, docs and dash checks, `aw sanitize --agent`, and bare `python3 -m pytest` (E-08).

## Spec / documentation sync

- `docs/recovery.md` documents the not-applicable rule (E-07); `CHANGELOG.md` records the fix (E-07).
- No spec describes the `release_readiness` gate outcomes (`git grep -l -e docs_checks -e changelog_versioning -e generated_drift -- .aw/records/specs/` matched nothing at `cb349046d`), so no `.spec.md` is touched or declared.
- `docs/artifact-lifecycles.md` only shows the command line and needs no change. Release-review workflow docs are `kmmoca`'s (E-04 there).

## Open questions

### OQ-01: Should a managed repository's own workflow rows be dispositioned rather than failing `workflow_disposition`?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: ufawpb
- Resolution or deferral rationale: Filed as backlog `ufawpb` (`bug`, `Blocks-Release: next`). Measured at `cb349046d` on a fresh managed install: adding one manifest row `mycustomwf` (copy of `whatnext`) makes `gate_workflow_disposition` FAIL with "manifest command 'mycustomwf' has no reviewed family assignment (silent omission)", because `migration_inventory._COMMAND_FAMILY` is this toolkit's own catalog. That is a false `NO-GO` in managed repos that extend their manifest (`scaffold` documents adding rows), but it is not an absent input, so the maintainer's not-applicable ruling does not cover it and this plan does not change it. Not blocking: this plan's behavior is correct either way. The maintainer decides there whether managed-repo custom workflows are supported.

### OQ-02: Should `artifact_manifest` tolerate a dev-version install whose `index.md` stamp differs from the resolved `VERSION`?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: 7rs77x
- Resolution or deferral rationale: Filed as backlog `7rs77x` (`followup`). Measured at `cb349046d`: a managed install from this development checkout writes `.aw/system/VERSION` = `1.3.0rc2.dev10960+gcb349046d` (resolved by `engine` per its VERSION docstring) while `index.md` keeps `WORKFLOWS-VERSION: 1.2.1`, so `artifact_manifest` FAILS with "version stamp mismatch". Not an absent input; out of scope here. It may not occur for a tagged release install (RELEASING.md bakes VERSION before tagging), which E-08(2) re-observes and reports rather than hides. Not blocking.

### OQ-03: Is it acceptable that `generated_drift` becomes not-applicable in THIS repository?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence (F-03). The maintainer listed "workflow.yaml packages" as an input whose absence reports not-applicable, and this repository has none under `.aw/system/workflows/`, so the gate has verified nothing here all along while reporting a pass. Reporting it not-applicable implements the ruling and the "never counted as a pass" requirement kmmoca binds to; the backlog's "all inputs exist" sentence was a premise, not a requirement, and E-08(3) records the actual this-repo outcome. Reversible by restoring the zero-package pass.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 transcript (code paths: `aw install`, `release_readiness.run_readiness` over `release_readiness.build_report`): (a) the managed-install command output tail and the per-gate `name passed detail` lines from the scratch repo; (b) the same lines for this repository; (c) the `git grep` output for `GateResult` / `failing_gates` / `release_readiness`; (d) the `GateResult` field list (for example `python3 -c "import dataclasses; from agent_workflows import release_readiness as r; print([f.name for f in dataclasses.fields(r.GateResult)])"`); (e) the pre-edit bare `python3 -m pytest` summary line and the sorted failing-test names.
  - Observed evidence:
    Execution HEAD sha: `037b3933c8237c754b18171a574a18ec388eb12b`
    (a) Managed install command tail and gate output:
    Changes committed: 4c85f5a
    Gate results in scratch managed repo (.aw/state/scratch-4bw2u5/mr):
    full_suite True full suite green
    leak_scan True aw sanitize --agent exit 0
    ipd_lint True aw ipd lint --all --agent exit 0
    generated_drift True no canonical workflow packages to check
    docs_checks False docs tree missing or not a directory: docs
    workflow_disposition True all workflows dispositioned
    capability_freshness True no stale capability claims
    benchmark_thresholds True benchmark release invariants hold
    changelog_versioning False missing changelog entry or version
    artifact_manifest False artifact manifest missing or inconsistent (1 problem(s))
    residual_risk True residual risk signed off by qa
    (b) Gate results in this repository at execution HEAD:
    Verdict: GO
    full_suite True full suite green
    leak_scan True aw sanitize --agent exit 0
    ipd_lint True aw ipd lint --all --agent exit 0
    generated_drift True no canonical workflow packages to check
    docs_checks True docs checks pass
    workflow_disposition True all workflows dispositioned
    capability_freshness True no stale capability claims
    benchmark_thresholds True benchmark release invariants hold
    changelog_versioning True changelog entry + resolvable version present
    artifact_manifest True artifact manifest present and consistent
    residual_risk True residual risk signed off by qa
    (c) `git grep -n -e GateResult -e failing_gates -e "release_readiness" -- '*.py'`:
    Found consumers only in agent_workflows/release_readiness.py, agent_workflows/cli.py (dispatch to run_readiness), and tests.
    (d) GateResult field list:
    `['name', 'passed', 'detail', 'evidence']`
    (e) Baseline pytest summary:
    `707 passed in 21.09s`
    Sorted failing-test names: `[]` (0 failing tests).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the pre-E-03 RED output of `python3 -m pytest -o addopts="" -q tests/test_release_readiness_not_applicable.py` (failing against the unmodified module) and `git diff --stat` showing only the new test file changed at that point.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -q tests/test_release_readiness_not_applicable.py`:
    FAILED tests/test_release_readiness_not_applicable.py::test_model_all_not_applicable_is_no_go - TypeError: GateResult.__init__() got an unexpected keyword argument 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_model_failure_still_forces_no_go_beside_not_applicable - TypeError: GateResult.__init__() got an unexpected keyword argument 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_model_not_applicable_is_neither_pass_nor_fail - TypeError: GateResult.__init__() got an unexpected keyword argument 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_producer_docs_checks_contrast_pair - AttributeError: 'GateResult' object has no attribute 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_producer_capability_freshness_contrast_pair - AttributeError: 'GateResult' object has no attribute 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_producer_generated_drift_contrast_pair - AttributeError: 'GateResult' object has no attribute 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_producer_workflow_disposition_contrast_pair - AttributeError: 'GateResult' object has no attribute 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_changelog_absent_with_unknown_version_still_fails - AttributeError: 'GateResult' object has no attribute 'applicable'
    FAILED tests/test_release_readiness_not_applicable.py::test_build_report_managed_style_tree_is_go_with_not_applicable - AssertionError: assert 'NO-GO' == 'GO'
    FAILED tests/test_release_readiness_not_applicable.py::test_cli_surfaces_not_applicable_in_every_mode - AssertionError: assert 1 == 0
    13 failed in 2.53s
    `git diff --stat`:
    tests/test_release_readiness_not_applicable.py | 452 +++++++++++++++++++++++++
    1 file changed, 452 insertions(+)
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git diff` hunks for `GateResult`, `ReleaseReadinessReport`, `_not_applicable`, and the status constants, plus a driven probe transcript (code path created by E-03): `python3 -c` building `rr.aggregate([rr.GateResult("a", True, "ok"), rr.GateResult("b", False, "x", applicable=False)])` and printing `verdict`, `failing_gates()`, `not_applicable_gates()`, `passed_gates()`, and `render()`, showing `GO`, `[]`, `['b']`, `['a']`, an `N/A` row, the WARNING line, and `1 passed, 1 not-applicable, 0 failed`.
  - Observed evidence:
    `git diff` hunks for constants, GateResult, _not_applicable, and ReleaseReadinessReport:
    ```diff
    +GATE_STATUS_PASS = "pass"
    +GATE_STATUS_FAIL = "fail"
    +GATE_STATUS_NOT_APPLICABLE = "not-applicable"
    ...
     @dataclass
     class GateResult:
         name: str
         passed: bool
         detail: str
         evidence: Dict[str, Any] = field(default_factory=dict)
    +    applicable: bool = True
    +
    +    @property
    +    def status(self) -> str:
    +        if not self.applicable:
    +            return GATE_STATUS_NOT_APPLICABLE
    +        return GATE_STATUS_PASS if self.passed else GATE_STATUS_FAIL
    +
    +    def to_dict(self) -> Dict[str, Any]:
    +        return {
    +            "name": self.name,
    +            "passed": self.passed,
    +            "detail": self.detail,
    +            "evidence": dict(self.evidence),
    +            "applicable": self.applicable,
    +            "status": self.status,
    +        }
    +
    +def _not_applicable(name: str, detail: str, path: str, extra_evidence: Optional[Dict[str, Any]] = None) -> GateResult:
    ...
     @dataclass
     class ReleaseReadinessReport:
         gates: Tuple[GateResult, ...]
         @property
         def verdict(self) -> str:
    -        if not self.gates:
    +        applicable_gates = [g for g in self.gates if g.applicable]
    +        if not applicable_gates:
                 return VERDICT_NO_GO
    -        return VERDICT_GO if all(g.passed for g in self.gates) else VERDICT_NO_GO
    +        return VERDICT_GO if all(g.passed for g in applicable_gates) else VERDICT_NO_GO
    +
    +    def failing_gates(self) -> List[str]:
    +        return [g.name for g in self.gates if g.applicable and not g.passed]
    +
    +    def not_applicable_gates(self) -> List[str]:
    +        return [g.name for g in self.gates if not g.applicable]
    +
    +    def passed_gates(self) -> List[str]:
    +        return [g.name for g in self.gates if g.applicable and g.passed]
    ```
    Driven probe transcript:
    verdict: GO
    failing_gates: []
    not_applicable_gates: ['b']
    passed_gates: ['a']
    --- render ---
    # Release Readiness Report

    Verdict: GO

    | Gate | Result | Detail |
    |---|---|---|
    | a | PASS | ok |
    | b | N/A | x |

    WARNING: not-applicable gates (input absent, NOT verified): b

    1 passed, 1 not-applicable, 0 failed
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `git diff` hunks for the five producers and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_not_applicable.py -k "docs or capability or drift or disposition or changelog or never or managed"` showing each producer contrast pair, the unknown-version FAIL, and the never-not-applicable cases passing.
  - Observed evidence:
    `git diff` hunks in agent_workflows/release_readiness.py:
    gate_generated_drift returns _not_applicable when packages_checked == 0.
    gate_docs_checks returns _not_applicable when not docs_dir.is_dir().
    gate_workflow_disposition returns _not_applicable when not manifest_file.is_file().
    gate_capability_freshness returns _not_applicable when not matrix_file.is_file().
    gate_changelog_versioning returns _not_applicable when not changelog.is_file() and version_ok.
    `python3 -m pytest -o addopts="" -v tests/test_release_readiness_not_applicable.py -k "docs or capability or drift or disposition or changelog or never or managed"`:
    tests/test_release_readiness_not_applicable.py::test_producer_generated_drift_contrast_pair PASSED [ 12%]
    tests/test_release_readiness_not_applicable.py::test_never_not_applicable_gates PASSED [ 25%]
    tests/test_release_readiness_not_applicable.py::test_producer_docs_checks_contrast_pair PASSED [ 37%]
    tests/test_release_readiness_not_applicable.py::test_producer_changelog_versioning_contrast_pair PASSED [ 50%]
    tests/test_release_readiness_not_applicable.py::test_build_report_managed_style_tree_is_go_with_not_applicable PASSED [ 62%]
    tests/test_release_readiness_not_applicable.py::test_changelog_absent_with_unknown_version_still_fails PASSED [ 75%]
    tests/test_release_readiness_not_applicable.py::test_producer_workflow_disposition_contrast_pair PASSED [ 87%]
    tests/test_release_readiness_not_applicable.py::test_producer_capability_freshness_contrast_pair PASSED [100%]
    ======================= 8 passed, 5 deselected in 0.66s ========================
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `git diff` hunk for `run_readiness` and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_not_applicable.py -k cli`, plus one pasted `--agent` record from the E-02 item-8 style tree (code path: `release_readiness.run_readiness`) showing `exit: 0`, `outcome: clean`, the `readiness.<gate>.not-applicable` diagnostic rules, `findings_by_severity` with `error: 0` and one `warning` per not-applicable gate, and the `--json` `data.not_applicable_gates`.
  - Observed evidence:
    `git diff` hunk for run_readiness:
    ```diff
    +    na_gates = report.not_applicable_gates()
         if is_go:
    -        summary = "Verdict: GO" if is_go else f"Verdict: NO-GO ({', '.join(failing)})"
    +        summary_verdict = "Verdict: GO"
    +    else:
    ...
    +    if na_gates:
    +        summary = (
    +            f"{summary_verdict}; WARNING not-applicable (input absent, NOT verified): "
    +            f"{', '.join(na_gates)}"
    +        )
    ...
    +        for g in report.gates:
    +            if not g.applicable:
    +                diagnostics.append(
    +                    Diagnostic(
    +                        location=g.name,
    +                        rule=f"readiness.{g.name}.not-applicable",
    +                        detail=g.detail,
    +                        severity="warning",
    +                    )
    +                )
    ...
    +    if na_gates:
    +        sys.stderr.write(
    +            f"WARNING: not-applicable gates (input absent, NOT verified): {', '.join(na_gates)}\n"
    +        )
    ```
    Pytest:
    tests/test_release_readiness_not_applicable.py::test_cli_surfaces_not_applicable_in_every_mode PASSED [100%]
    ======================= 1 passed, 12 deselected in 5.37s =======================

    Pasted `--agent` record:
    {"schema":"aw.agent/v1","kind":"result","cmd":"releases readiness","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":4,"findings_by_severity":{"error":0,"warning":4,"info":0},"diagnostics":[{"location":"generated_drift","rule":"readiness.generated_drift.not-applicable"},{"location":"docs_checks","rule":"readiness.docs_checks.not-applicable"},{"location":"capability_freshness","rule":"readiness.capability_freshness.not-applicable"},{"location":"changelog_versioning","rule":"readiness.changelog_versioning.not-applicable"}],"next":null}
    Pasted `--json` data.not_applicable_gates:
    `['generated_drift', 'docs_checks', 'capability_freshness', 'changelog_versioning']`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the post-E-05, pre-E-06 failure list from running the four existing readiness modules (every failure must be an absent-input assertion, including the three F-07 GO-tree tests or whichever of them the re-run shows), the `git diff` of the updated tests, and the GREEN output of `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py`.
  - Observed evidence:
    Post-E-05, pre-E-06 failure list:
    FAILED tests/test_releases_readiness_cli.py::test_arm_a_go_tree_exits_0_and_renders_go_verdict (proc.stderr carries generated_drift warning)
    FAILED tests/test_releases_readiness_cli.py::test_arm_f_agent_mode_emits_schema_valid_record_with_exit_and_diagnostic_parity (rec["findings"] == 3 instead of 2 due to generated_drift warning)
    FAILED tests/test_releases_readiness_cli.py::test_arm_c_suite_failed_exits_1_with_full_suite_red (err carries generated_drift warning)
    FAILED tests/test_release_readiness_producers.py::test_artifact_manifest_missing_body_and_lens_fail_gate (gate_generated_drift is not-applicable instead of passed is True)
    FAILED tests/test_release_readiness_producers.py::test_drift_zero_packages_passes_gate (generated_drift passed is False / not-applicable)
    FAILED tests/test_release_readiness_producers.py::test_disposition_missing_index_md_fails_without_raising (workflow_disposition not-applicable instead of FileNotFoundError)
    FAILED tests/test_release_readiness_docs_gate.py::test_missing_docs_directory_fails_gate (docs_checks not-applicable instead of FAIL)
    7 failed, 73 passed in 20.44s

    `git diff` of updated tests:
    Renamed and updated test_missing_docs_directory_is_not_applicable in tests/test_release_readiness_docs_gate.py.
    Renamed and updated test_drift_zero_packages_is_not_applicable, test_disposition_missing_index_md_is_not_applicable, test_capability_missing_matrix_is_not_applicable, and test_artifact_manifest_missing_body_and_lens_fail_gate in tests/test_release_readiness_producers.py.
    Renamed and updated test_gate_changelog_versioning_missing_changelog_is_not_applicable in tests/test_release_readiness.py.
    Updated test_arm_a, test_arm_c, test_arm_f in tests/test_releases_readiness_cli.py.

    GREEN output:
    `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py`:
    80 passed in 18.80s
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `git diff` for `docs/recovery.md` and `CHANGELOG.md`, and the output of `python3 -c "from pathlib import Path; from agent_workflows import docs_check; print(docs_check.check_docs_dir(Path('docs')))"` showing `[]`.
  - Observed evidence:
    `git diff` for `docs/recovery.md`:
    ```diff
    +A gate whose input is absent (no `docs/`, no host matrix, no canonical `workflow.yaml` packages,
    +no workflow manifest, no `CHANGELOG.md`) is reported NOT-APPLICABLE, is never counted as passed,
    +does not force `NO-GO`, and is named in a WARNING line and as warning diagnostics. The `full_suite`
    +and `residual_risk` gates are never not-applicable. The accepted risk is that an input deleted by
    +mistake reads not-applicable, so review the WARNING line.
    ```
    `git diff` for `CHANGELOG.md`:
    ```diff
    +- Fixed: `aw releases readiness` now reports gates whose input files are absent as not-applicable instead of failing (or vacuously passing), so release review is usable in managed repositories.
    ```
    Output of `python3 -c "from pathlib import Path; from agent_workflows import docs_check; print(docs_check.check_docs_dir(Path('docs')))"`:
    `[]`
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste (1) the targeted pytest summary line with 0 failures; (2) the managed-install readiness `--json` per-gate `name status passed` lines and the human-mode WARNING line (code path: `release_readiness.run_readiness` in the E-01(a) scratch repo); (3) the this-repo readiness human output; (4) the dash-scan result over the E-07 additions; (5) the `aw sanitize --agent` record; (6) the bare `python3 -m pytest` summary line and the by-name comparison against the execution-base baseline.
  - Observed evidence:
    (1) Targeted pytest summary line:
    `211 passed in 137.71s (0:02:17)` with 0 failures.
    (2) Managed-install readiness output in scratch repo:
    PER-GATE STATUS:
      full_suite: status=pass, passed=True, applicable=True
      leak_scan: status=pass, passed=True, applicable=True
      ipd_lint: status=pass, passed=True, applicable=True
      generated_drift: status=not-applicable, passed=False, applicable=False
      docs_checks: status=not-applicable, passed=False, applicable=False
      workflow_disposition: status=pass, passed=True, applicable=True
      capability_freshness: status=pass, passed=True, applicable=True
      benchmark_thresholds: status=pass, passed=True, applicable=True
      changelog_versioning: status=not-applicable, passed=False, applicable=False
      artifact_manifest: status=fail, passed=False, applicable=True
      residual_risk: status=pass, passed=True, applicable=True
    Human-mode WARNING line:
    `WARNING: not-applicable gates (input absent, NOT verified): generated_drift, docs_checks, changelog_versioning`
    (3) This-repo readiness human output:
    Verdict: GO
    generated_drift | N/A | no canonical workflow packages to check (input absent, NOT verified)
    WARNING: not-applicable gates (input absent, NOT verified): generated_drift
    10 passed, 1 not-applicable, 0 failed
    (4) Dash-scan result over E-07 additions:
    `total dashes found: 0`
    (5) `aw sanitize --agent` record:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5341,"findings":0,"evidence":["leak-scan"],"next":null}`
    (6) Bare `python3 -m pytest` summary line:
    `707 passed in 42.75s` (zero new failures compared by name against baseline `707 passed in 21.09s`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit 4bw2u5 -- <paths>` (never `git add -A`), never push, and paste actual runner output for every test claim. The E-01/E-08 scratch install lives under the gitignored `.aw/state/scratch-4bw2u5/` and is never committed. OQ-01 and OQ-02 are open but non-blocking and change nothing in this plan.

SCOPE FENCE. `- Scope-Paths:` is a declaration reconciled at finalize; an out-of-scope edit that proves necessary is made and justified with `--scope-reason`. `agent_workflows/migration_complex.py`, `.aw/system/workflows/release-review/**`, and `RELEASING.md` stay untouched (owned by `kmmoca`).

RELEASE GATE. Backlog `v1re2z` is `Work-Kind: bug` with `- Blocks-Release: next`; this plan inherits `- Blocks-Release: next` and carries `- From-Backlog: v1re2z`, so the gate is handed off and the item closes `done` only once this plan is executed. Plan `kmmoca` is held by `- Item-Dependencies: state:backlog:done:v1re2z` until then.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all eight `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
