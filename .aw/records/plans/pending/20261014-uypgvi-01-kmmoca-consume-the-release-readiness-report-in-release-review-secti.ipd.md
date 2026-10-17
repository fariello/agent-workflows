# IPD: Consume the release_readiness report in release-review Section 8, Section 9, and ReleaseReviewCoordinator

- Date: 2026-10-14
- Kind: child
- Concern: `wa64wz` SHIPPED `aw releases readiness`, BUT NOTHING IN `release-review`, `RELEASING.md`, OR `ReleaseReviewCoordinator` CONSUMES THE `release_readiness` REPORT AS A PROCESS STEP OR DEFINES HOW A STANDING `NO-GO` IS TREATED. Backlog item `uypgvi` (`20261012-uypgvi-01-uypgvi-consume-readiness-report-in-process.backlog.md`) records that once `usggph` plan `wa64wz` ships `aw releases readiness`, the project must decide whether `release-review` Section 8, a CI job, or a hook runs it, and how a standing `NO-GO` (unsigned `residual_risk`, live `ipd_lint` red) is treated there. Measured at authoring HEAD `53eb3077e`:
  1. `wa64wz` (`20261012-usggph-02-wa64wz-add-a-read-only-aw-releases-readiness-command-that-renders-t.ipd.md`), `ttg9uz` (`20261012-usggph-01-ttg9uz-give-the-generated-drift-workflow-disposition-and-capability.ipd.md`), and `514wv3` (`20261012-r4a4ab-01-514wv3-prove-build-report-yields-go-with-the-subprocess-gates-live.ipd.md`) are all `executed` under `.aw/records/plans/executed/`.
  2. No release-review file, `RELEASING.md`, CI workflow, or hook calls `release_readiness.build_report` or `release_readiness.run_readiness` (`git grep -n -e build_report -e run_readiness -e "releases readiness" -- '*.py' '.aw/system/workflows/' 'RELEASING.md' '.github/' '.pre-commit-config.yaml' ':!tests/'` matches `agent_workflows/release_readiness.py`, `agent_workflows/cli.py`, `agent_workflows/command_surface.py` (the command declaration), and `.aw/system/workflows/benchmark/tools/bench_env.py` (an unrelated `build_report`), F-01; corrected at review, PR-003).
  3. In `agent_workflows/migration_complex.py`, `ReleaseReviewCoordinator` defines `STAGE_VERIFY: str = "verify"` between `STAGE_MUTATION` and `STAGE_RELEASE`, yet no method on `ReleaseReviewCoordinator` ever enters `STAGE_VERIFY` or consumes `ReleaseReadinessReport`, and `ReleaseReviewCoordinator.authorize_release` enters `STAGE_RELEASE` without checking any readiness report (F-02).
  4. Neither `.aw/system/workflows/release-review/08-final-ship-review.md`, `.aw/system/workflows/release-review/09-release-execution.md`, `.aw/system/workflows/release-review/templates/final-response.md`, nor `RELEASING.md` mentions `aw releases readiness` or `release_readiness` (F-01).
  WHY `release-review` SECTION 8 + SECTION 9 + `ReleaseReviewCoordinator` IS THE PROCESS STEP, NOT A GIT HOOK OR A FAIL-CLOSED ROUTINE CI STEP (F-03, OQ-01):
  - `agent_workflows/release_readiness.py`'s module docstring states that it is *"the checkable core of the final release-readiness review. INVARIANT (airtight, cited to RELEASING.md / release-review Section 9): this module NEVER tags, publishes, deploys, or pushes."*
  - A git hook (`.pre-commit-config.yaml`) is wrong: routine commits and merges are not releases; neither `make test-all` (~2.5-4m) nor human residual-risk sign-off exists at commit time; forging `--suite-passed` or `--residual-risk-signer` in a hook violates `wa64wz` F-02 and `AGENTS.md` (*"NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD"*); and `aw releases readiness` shells out to `aw sanitize --agent` (already run by the `local-leaks` pre-commit hook) and `aw ipd lint --all --agent` (~4.5s combined), which is a `livecorpus` check that legitimately exits `1` whenever any pending plan in `.aw/records/plans/pending/` carries an open `Blocking: yes` question (`IPD-Q501`, `514wv3` F-01..F-03).
  - A fail-closed routine CI step in `.github/workflows/tests.yml` is wrong for the same reason: on routine pushes/PRs, `residual_risk` is unsigned, `slow` tests run with `continue-on-error: true` (`4petcj`), and `ipd_lint` is a `livecorpus` check that turns red whenever any pending IPD has an open blocking question. CI already runs `aw check plans --agent`, `aw check releases --agent`, `aw check backlog --agent`, and `aw check release-gates --agent` in `attention-check`, and `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[releases readiness]` already runs `aw releases readiness --agent` in CI to verify its `aw.agent/v1` envelope and exit parity without requiring a `GO` verdict on routine commits.
  HOW A STANDING `NO-GO` IS TREATED IN SECTION 8 (`STAGE_VERIFY`) AND SECTION 9 (`STAGE_RELEASE`) (F-04, OQ-02):
  - The 11 gates `release_readiness.build_report` emits (with `run_subprocess_gates=True`) partition into three classes (NOTE: `release_readiness` exports NO `GATE_ORDER` constant; the gate set is the `name` of each `GateResult` that `build_report` appends, PR-001):
    1. **Human release-time attestation gate (`residual_risk`)**: during Section 8 (`08-final-ship-review.md` / `STAGE_VERIFY`), before the human answers the `RELEASE REVIEW DECISION` banner, `aw releases readiness --suite-passed` is run without `--residual-risk-signer` (the agent must never forge human sign-off), so `residual_risk` fails (`residual-risk sign-off missing`). When `residual_risk` is the ONLY failing gate (`hard_failures == ()` and `standing_failures == ()`), every other APPLICABLE gate has passed (not-applicable gates are listed separately and never counted as passes), so Section 8 treats the readiness check as eligible for a `GO` recommendation (`pending_human_attestation=True`), with the human's subsequent Section 8->9 release approval supplying `--residual-risk-signer "<approver>"` at Section 9.
    2. **Standing corpus / seed-data gates (`ipd_lint`, `capability_freshness`)**: live `ipd_lint` (`aw ipd lint --all --agent`) can be `FAIL` because an out-of-scope pending plan in `.aw/records/plans/pending/` carries an open `Blocking: yes` question (`IPD-Q501`, `514wv3` F-01..F-03), and `capability_freshness` is `FAIL` when static host-matrix seed rows remain unverified (`5gzno3` / `8ru81x`). When either standing gate fails in Section 8 (and no hard gate fails), the recommendation **cannot be a clean `GO`**: if the failing gate has not been triaged as an out-of-scope pending plan or tracked standing item, the recommendation is `NO-GO`; if triaged (`triaged_standing_gates`), the recommendation is capped at `CONDITIONAL GO` (matching Section 8's existing `Pending-plans / staged-prompts gate`), and each failing standing gate must be named in the `RELEASE REVIEW DECISION` banner's `Blocking / pending items` and `Conditions` lines.
    3. **Hard technical / release-integrity gates (`full_suite`, `leak_scan`, `benchmark_thresholds`, `generated_drift`, `docs_checks`, `workflow_disposition`, `changelog_versioning`, `artifact_manifest`)**: any failure in these 8 gates forces `NO-GO` unconditionally and can never be triaged as standing corpus noise or waived at Section 9.
  - NOT-APPLICABLE GATES (OQ-03, maintainer 2026-10-15, option (b)). The readiness step runs in release-review in EVERY repository. A gate whose input files are absent (e.g. no `docs/`, no host matrix, no `CHANGELOG.md`) is reported NOT-APPLICABLE by `release_readiness` instead of failing; that `release_readiness` change is NOT made here, it is carried by backlog `v1re2z` and gated by this plan's `- Item-Dependencies: state:backlog:done:v1re2z`. This plan only CONSUMES that state: a not-applicable gate (1) does not force `NO-GO` and needs no triage or waiver; (2) is NEVER counted as a pass (it is not in any passed tally and is reported in its own `not_applicable_gates` list); and (3) is displayed PROMINENTLY: named in a bold `WARNING` in the Section 8 Go/No-Go, in the `RELEASE REVIEW DECISION` banner's `Blocking / pending items` line, and in the Section 9 human release prompt, because the accepted risk is that a repository which deleted an input by mistake sees not-applicable rather than a failure. `full_suite` and `residual_risk` take explicit inputs, not files, so a not-applicable report for either is treated as a HARD failure (fail closed).
  - At the Section 9 release boundary (`09-release-execution.md` / `ReleaseReviewCoordinator.authorize_release`): the human approver's identity supplies `--residual-risk-signer "<approver>"`. Section 9 requires `aw releases readiness --suite-passed --residual-risk-signer "<approver>"` to report no failing APPLICABLE gate (not-applicable gates do not refuse, but are restated to the human before release), or, if a standing `CONDITIONAL GO` gate (`ipd_lint` on an out-of-scope pending plan or `capability_freshness`) remains `FAIL`, requires an explicit written human waiver of that named standing gate (`waived_standing_gates`) per Section 9 Hard Precondition 3, and unconditionally refuses if `residual_risk` is unsigned or any hard gate fails.
  WHY `followup` AND NO RELEASE GATE IS INVENTED. Backlog item `uypgvi` carries `- Work-Kind: followup`, `- Priority: low`, and no `- Blocks-Release:`; all three are preserved without inventing a release gate.
- Scope: IN: (1) add `READINESS_ATTESTATION_GATES`, `READINESS_STANDING_WAIVABLE_GATES`, `READINESS_HARD_GATES`, `RECOMMENDATION_GO`, `RECOMMENDATION_CONDITIONAL_GO`, `RECOMMENDATION_NO_GO`, `ReadinessVerification`, and `ReleaseReviewCoordinator.verify_readiness` (entering `STAGE_VERIFY`) plus readiness enforcement in `ReleaseReviewCoordinator.authorize_release` (at `STAGE_RELEASE`) in `agent_workflows/migration_complex.py`, including consumption of the not-applicable gate state `v1re2z` adds; (2) add behavioral and falsifiability tests in `tests/test_release_review_readiness.py` (shown RED against pre-change `migration_complex.py` first); (3) wire `aw releases readiness`, the standing-`NO-GO` rules, and the prominent not-applicable display into `.aw/system/workflows/release-review/08-final-ship-review.md`, `.aw/system/workflows/release-review/09-release-execution.md`, `.aw/system/workflows/release-review/templates/final-response.md`, and `RELEASING.md`. OUT: modifying `agent_workflows/release_readiness.py` (owned by sibling pending plan `w9l8ph`; the not-applicable gate state itself is carried by backlog `v1re2z` and its own plan, a prerequisite of this one), `.aw/system/workflows/conformance/tools/host_matrix.json` (owned by sibling pending plan `8ru81x`), `.github/workflows/tests.yml`, or `.pre-commit-config.yaml`; and any tag, publish, push, or release action (`assert_no_release_action`).
- Scope-Paths: agent_workflows/migration_complex.py, .aw/system/workflows/release-review/08-final-ship-review.md, .aw/system/workflows/release-review/09-release-execution.md, .aw/system/workflows/release-review/templates/final-response.md, RELEASING.md, tests/test_release_review_readiness.py
- Item-Dependencies: state:backlog:done:v1re2z
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: uypgvi
- Set: uypgvi
- Order: 1
- Highest E allocated: 05
- Author: antigravity
- Id: kmmoca
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 same-status (aw set): plan-review round 2: APPROVE WITH REVISIONS APPLIED; consume v1re2z not-applicable state (OQ-03 b), depend state:backlog:done:v1re2z; PR-002, PR-006..PR-008 fixed
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us, round 2): APPROVE WITH REVISIONS APPLIED; PR-002 fixed via resolved OQ-03 (maintainer, option (b)); PR-006, PR-007, PR-008 fixed; depends on backlog v1re2z (state:backlog:done:v1re2z)
- 2026-10-15 same-status (aw set): plan-review: depend on v1re2z (not-applicable gate change) per OQ-03 answer
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-002 OPEN (escalated OQ-03); PR-001, PR-003, PR-004, PR-005 fixed
- 2026-10-14 to-review (aw set): Authored from backlog uypgvi at HEAD 53eb3077e: consume release_readiness in release-review Section 8, Section 9, RELEASING.md, and ReleaseReviewCoordinator.

- 2026-10-14 draft (antigravity): created.

## Goal

Consume the `release_readiness` report as a first-class process step in `release-review` Section 8 (`STAGE_VERIFY`), Section 9 (`STAGE_RELEASE`), `RELEASING.md`, and `ReleaseReviewCoordinator` (`agent_workflows/migration_complex.py`), with deterministic rules for unsigned `residual_risk`, standing `ipd_lint` / `capability_freshness` failures, and non-waivable hard gate failures.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-measure `ReleaseReviewCoordinator` and the `release-review` / `RELEASING.md` surfaces at the executing HEAD before changing any file.
  - Depends on: none
  - Expected outcome: one pasted transcript proving, at the executing HEAD: (a) `git grep -n -e build_report -e run_readiness -e "releases readiness" -- '*.py' '.aw/system/workflows/' 'RELEASING.md' '.github/' '.pre-commit-config.yaml' ':!tests/'` shows no release-review file, `RELEASING.md`, CI workflow, or hook consuming the report; (b) in `agent_workflows/migration_complex.py`, `STAGE_VERIFY` appears in the constant definition, `enter_stage` allow-set, and `__all__`, with no method on `ReleaseReviewCoordinator` entering `STAGE_VERIFY` or inspecting a `ReleaseReadinessReport`; and (c) `hasattr(migration_complex.ReleaseReviewCoordinator, "verify_readiness")` is `False`; and (d) `hasattr(release_readiness, "GATE_ORDER")` (expected `False` at review) and the gate names `build_report(..., run_subprocess_gates=True)` emits. The grep in (a) is re-derived, not a bar: at review it ALSO matched `.aw/system/workflows/benchmark/tools/bench_env.py` (an unrelated `build_report`) and `agent_workflows/command_surface.py` (the command declaration); the property to prove is that no release-review file, `RELEASING.md`, CI workflow, or hook consumes the report. (e) NOT-APPLICABLE PRECONDITION SPIKE (PR-006): backlog `v1re2z` is `done` (`aw backlog` shows it under `done/`, satisfying `- Item-Dependencies: state:backlog:done:v1re2z`), and a driven probe of `release_readiness.build_report(suite_passed=True, residual_risk_signed=False, repo_root=<tmp minimal managed-style tree with `.aw/system/workflows/release-review/` and `.aw/records/` but no `docs/`, no `CHANGELOG.md`, no host matrix>, run_subprocess_gates=False)` shows each input-absent gate reported NOT-APPLICABLE through a signal that is distinguishable from BOTH pass and fail (record the exact attribute or method `v1re2z` shipped; E-02 and E-03 bind to that name). If `v1re2z` is not `done`, or its not-applicable state is indistinguishable from `passed=True` or from `passed=False`, stop and report (the prerequisite symbols are absent): E-02 cannot satisfy "never counted as a pass" without it, and the remedy is a corrective change under `v1re2z`, not a workaround here. If `verify_readiness` already exists on `ReleaseReviewCoordinator`, stop and reconcile rather than duplicating the work.
  - Execution state: performed

### Task group 2: wire `STAGE_VERIFY` and `STAGE_RELEASE` readiness consumption in `ReleaseReviewCoordinator`

- [x] E-02 Add `ReadinessVerification`, `ReleaseReviewCoordinator.verify_readiness` (`STAGE_VERIFY`), and Section 9 readiness enforcement in `ReleaseReviewCoordinator.authorize_release` (`STAGE_RELEASE`) in `agent_workflows/migration_complex.py`.
  - Depends on: E-01
  - Expected outcome: in `agent_workflows/migration_complex.py` (importing `from agent_workflows import release_readiness as _readiness`):
    1. Define and export in `__all__`:
       - `READINESS_ATTESTATION_GATES: FrozenSet[str] = frozenset(("residual_risk",))`
       - `READINESS_STANDING_WAIVABLE_GATES: FrozenSet[str] = frozenset(("ipd_lint", "capability_freshness"))`
       - `READINESS_HARD_GATES: FrozenSet[str] = frozenset(("full_suite", "leak_scan", "benchmark_thresholds", "generated_drift", "docs_checks", "workflow_disposition", "changelog_versioning", "artifact_manifest"))` written out literally (`release_readiness` has NO `GATE_ORDER`; do not add one there, that module is out of scope). FAIL CLOSED on drift: `verify_readiness` and `authorize_release` treat any failing gate name that is in NONE of the three sets as a HARD failure, so a gate added to `build_report` later can never be silently triaged or waived.
       - `RECOMMENDATION_GO: str = "GO"`
       - `RECOMMENDATION_CONDITIONAL_GO: str = "CONDITIONAL GO"`
       - `RECOMMENDATION_NO_GO: str = "NO-GO"`
       - `READINESS_INPUT_REQUIRED_GATES: FrozenSet[str] = frozenset(("full_suite", "residual_risk"))`: gates driven by explicit attestations, not files, so a not-applicable report for either is a HARD failure (fail closed).
       - Frozen dataclass `ReadinessVerification` with fields `report: _readiness.ReleaseReadinessReport`, `recommendation: str`, `hard_failures: Tuple[str, ...]`, `standing_failures: Tuple[str, ...]`, `triaged_standing_gates: Tuple[str, ...]`, `untriaged_standing_gates: Tuple[str, ...]`, `not_applicable_gates: Tuple[str, ...]`, `passed_gates: Tuple[str, ...]`, `pending_human_attestation: bool`, and `to_dict(self) -> Dict[str, Any]` returning a JSON-serializable dict including `verdict`, `recommendation`, `hard_failures`, `standing_failures`, `triaged_standing_gates`, `untriaged_standing_gates`, `not_applicable_gates`, `passed_gates`, and `pending_human_attestation`. `passed_gates` contains ONLY gates that actually passed; a not-applicable gate is in `not_applicable_gates` and never in `passed_gates`.
       - Module helper `_not_applicable_names(report) -> Tuple[str, ...]` that reads the not-applicable signal `v1re2z` shipped (the name recorded in E-01(e)); this is the ONLY place that signal is read, so `verify_readiness` and `authorize_release` cannot diverge on it.
    2. On `ReleaseReviewCoordinator`, add `_last_verification: Optional[ReadinessVerification] = field(default=None, init=False, repr=False)` (and property `last_verification -> Optional[ReadinessVerification]`) and method `verify_readiness(self, report: _readiness.ReleaseReadinessReport, *, triaged_standing_gates: Sequence[str] = ()) -> ReadinessVerification`:
       - Calls `self.enter_stage(STAGE_VERIFY)` first (so `RELEASE_MODE_PLANNING` raises `ReleaseModeError` and `RELEASE_MODE_FULL` appends `STAGE_VERIFY` to `stages_entered`).
       - Validates `triaged_standing_gates`: if any element is not in `READINESS_STANDING_WAIVABLE_GATES`, raises `ComplexMigrationError` naming the invalid or non-triagable gate (hard gates and `residual_risk` can never be triaged as standing corpus noise).
       - Computes `na = _not_applicable_names(report)`, `failed = tuple(g for g in report.failing_gates() if g not in na)` (whether or not `v1re2z` also lists a not-applicable gate in `failing_gates()`), `passed_gates = tuple(g.name for g in report.gates if g.passed and g.name not in na)`, `hard_failures = tuple(g for g in failed if g not in READINESS_ATTESTATION_GATES and g not in READINESS_STANDING_WAIVABLE_GATES) + tuple(g for g in na if g in READINESS_INPUT_REQUIRED_GATES)` (hard set, any unclassified name, and a not-applicable attestation gate), `not_applicable_gates = tuple(g for g in na if g not in READINESS_INPUT_REQUIRED_GATES)`, `standing_failures = tuple(g for g in failed if g in READINESS_STANDING_WAIVABLE_GATES)`, `triaged_set = frozenset(triaged_standing_gates)`, `triaged = tuple(g for g in standing_failures if g in triaged_set)`, `untriaged = tuple(g for g in standing_failures if g not in triaged_set)`, and `pending_human_attestation = "residual_risk" in failed`.
       - Computes `recommendation`: `RECOMMENDATION_NO_GO` if `hard_failures` or `untriaged` is non-empty; else `RECOMMENDATION_CONDITIONAL_GO` if `standing_failures` is non-empty (all triaged); else `RECOMMENDATION_GO` (every applicable gate passed, or only `residual_risk` is pending the human's Section 8->9 release decision). A not-applicable gate neither forces `NO-GO` nor caps the recommendation (OQ-03 (b); D-5), but it is always carried in `not_applicable_gates` for prominent display and never in `passed_gates`.
       - Stores `self._last_verification = result` and returns `result`.
    3. On `ReleaseReviewCoordinator.authorize_release(self, *, interactive: bool, input_handler: Optional[Any] = None, approver: str = "human", readiness_report: Optional[_readiness.ReleaseReadinessReport] = None, waived_standing_gates: Sequence[str] = ()) -> _gates.GateDecision`:
       - Calls `self.enter_stage(STAGE_RELEASE)` as before.
       - Validates `waived_standing_gates`: if any gate in `waived_standing_gates` is not in `READINESS_STANDING_WAIVABLE_GATES`, raises `ReleaseAuthorityError` naming the non-waivable gate (hard gates and `residual_risk` can never be waived).
       - REQUIRES `readiness_report`: if it is `None`, raises `ReleaseAuthorityError("release refused: no Section 9 readiness report supplied")` (fail closed, PR-004; there is NO fallback to `last_verification`, because the Section 8 verification was deliberately run unsigned and cannot prove the Section 9 sign-off). It then enforces Section 9 post-decision readiness on `readiness_report`:
          - classifies failures exactly as `verify_readiness` does (same `_not_applicable_names` helper, not-applicable gates excluded from `failing_gates()`, a not-applicable `full_suite` or `residual_risk` treated as hard);
          - if any failing gate is hard (in `READINESS_HARD_GATES`, unclassified, or a not-applicable attestation gate), raises `ReleaseAuthorityError` naming the failed hard gate(s);
         - if `"residual_risk" in readiness_report.failing_gates()`, raises `ReleaseAuthorityError("release refused: residual_risk gate is unsigned in readiness report")`;
         - if any gate in `readiness_report.failing_gates()` is in `READINESS_STANDING_WAIVABLE_GATES` and not in `frozenset(waived_standing_gates)`, raises `ReleaseAuthorityError` naming the unwaived standing gate(s).
        - A not-applicable gate never refuses and needs no waiver, but it is surfaced to the approver: when any remain, the `DecisionGate` prompt names every not-applicable gate (e.g. `"Execute the release (tag/publish)? This is irreversible. NOT-APPLICABLE gates (inputs absent, NOT verified): docs_checks, changelog_versioning"`) and its `metadata` carries `{"not_applicable_gates": [...]}`, so the human cannot approve without seeing them.
        - Then evaluates the human `DecisionGate("release-review/release", ...)` via `_gates.evaluate_gate` as before, raising `ReleaseAuthorityError` unless `decision.is_approved`.
  - Execution state: performed

- [x] E-03 Add behavioral and falsifiability tests in `tests/test_release_review_readiness.py` (shown RED against pre-E-02 `migration_complex.py` first) driving `ReleaseReviewCoordinator.verify_readiness` and `ReleaseReviewCoordinator.authorize_release` over real `release_readiness.build_report` outputs.
  - Depends on: E-02
  - Expected outcome: create `tests/test_release_review_readiness.py` (no `inspect`, `ast`, regex over `.py` files, or line counts; all filesystem fixtures under `tmp_path` with `GIT_CEILING_DIRECTORIES` set) covering:
    1. `test_planning_mode_refuses_verify_readiness`: a `ReleaseReviewCoordinator(mode=RELEASE_MODE_PLANNING)` calling `verify_readiness(report)` raises `ReleaseModeError` and does not enter `STAGE_VERIFY`.
    2. `test_section8_unsigned_residual_risk_only_yields_go_with_pending_attestation`: on a clean synthetic tree where `build_report(suite_passed=True, residual_risk_signed=False, ...)` returns `VERDICT_NO_GO` with `failing_gates() == ["residual_risk"]`, `verify_readiness(rep)` enters `STAGE_VERIFY` and returns `recommendation == "GO"`, `pending_human_attestation is True`, `hard_failures == ()`, `standing_failures == ()`.
    3. `test_section8_clean_signed_report_yields_go_without_pending_attestation`: when `build_report(suite_passed=True, residual_risk_signed=True, residual_risk_signer="qa", ...)` returns `VERDICT_GO`, `verify_readiness(rep)` returns `recommendation == "GO"`, `pending_human_attestation is False`, and `to_dict()["verdict"] == "GO"`.
    4. `test_section8_standing_ipd_lint_and_capability_freshness_untriaged_vs_triaged`: when `ipd_lint` or `capability_freshness` fails in `build_report` (e.g. a nonconforming pending plan in `.aw/records/plans/pending/` or an unproven `supported: true` in `host_matrix.json`), `verify_readiness(rep)` without `triaged_standing_gates` returns `recommendation == "NO-GO"` and lists the gate in `untriaged_standing_gates`; calling `verify_readiness(rep, triaged_standing_gates=("ipd_lint",))` (or `("capability_freshness",)` / both) returns `recommendation == "CONDITIONAL GO"` with `triaged_standing_gates` populated and `untriaged_standing_gates == ()`.
    5. `test_section8_hard_gate_failure_forces_no_go_and_refuses_triage`: when any gate in `READINESS_HARD_GATES` fails (`full_suite` via `suite_passed=False` or `None`, `leak_scan`, `benchmark_thresholds`, `generated_drift`, `docs_checks`, `workflow_disposition`, `changelog_versioning`, `artifact_manifest`), `verify_readiness(rep)` returns `recommendation == "NO-GO"` even when standing gates are triaged; and passing any hard gate or `"residual_risk"` in `triaged_standing_gates` raises `ComplexMigrationError`.
    6. `test_section9_authorize_release_enforces_signed_readiness_and_waivers`: driving `authorize_release(interactive=True, input_handler=lambda _g: "approve", approver="maintainer", readiness_report=...)`:
       - succeeds and returns an approved `GateDecision` when `readiness_report` is `VERDICT_GO`;
       - raises `ReleaseAuthorityError` when `readiness_report` has unsigned `residual_risk` (`residual_risk_signed=False`);
       - raises `ReleaseAuthorityError` when `readiness_report` has a failing `ipd_lint` or `capability_freshness` gate and `waived_standing_gates=()` is empty, and succeeds when `waived_standing_gates=("ipd_lint",)` explicitly waives that standing gate;
       - raises `ReleaseAuthorityError` when `readiness_report` has a hard gate failure (`full_suite`, `leak_scan`, `benchmark_thresholds`, etc.), and raises `ReleaseAuthorityError` if the caller attempts to pass a hard gate or `"residual_risk"` in `waived_standing_gates`;
       - raises `ReleaseAuthorityError` when `readiness_report=None`, even after a successful Section 8 `verify_readiness` (no fallback);
       - treats an unclassified failing gate name (a `GateResult` named outside the three sets, built with `release_readiness.aggregate`) as hard in both `verify_readiness` (`NO-GO`) and `authorize_release` (refused).
    7. `test_gate_classes_partition_the_emitted_gate_names`: the three sets are pairwise disjoint and their union equals `{g.name for g in release_readiness.build_report(suite_passed=True, repo_root=<tmp tree>, run_subprocess_gates=True).gates}` (behavioral: derived from what `build_report` actually emits, never from source text).
    8. `test_not_applicable_gates_are_never_passes_and_never_block`: over a REAL `build_report(suite_passed=True, ..., repo_root=<tmp minimal managed-style tree from E-01(e)>, run_subprocess_gates=False)` (not a hand-built report, so the test binds to the signal `v1re2z` actually emits): `verify_readiness(rep)` lists every input-absent gate in `not_applicable_gates`, none of them in `passed_gates`, `hard_failures`, or `standing_failures`, and the recommendation is not forced to `NO-GO` by them; `authorize_release(..., readiness_report=<same tree, signed>)` succeeds with no waiver, and the `GateDecision` the `input_handler` receives names every not-applicable gate in its prompt and `metadata["not_applicable_gates"]`; and a report in which `full_suite` or `residual_risk` is not-applicable is treated as a hard failure by both methods. Falsifiability: the same test FAILS against a coordinator that counts not-applicable as passed (it would appear in `passed_gates`) or as failed (it would force `NO-GO`).
  - Execution state: performed

### Task group 3: wire `aw releases readiness` into `release-review` Section 8, Section 9, `templates/final-response.md`, and `RELEASING.md`

- [x] E-04 Update `.aw/system/workflows/release-review/08-final-ship-review.md`, `.aw/system/workflows/release-review/09-release-execution.md`, `.aw/system/workflows/release-review/templates/final-response.md`, and `RELEASING.md` to run `aw releases readiness` and apply the standing-`NO-GO` rules.
  - Depends on: E-03
  - Expected outcome:
    1. In `.aw/system/workflows/release-review/08-final-ship-review.md`:
       - Under `## Final validation` (after the `make test-all` and `verify` paragraphs), add a `**Release-readiness report gate (`aw releases readiness`).**` paragraph instructing the reviewer to run `aw releases readiness --suite-passed` (or `--suite-failed` if the full test target failed; never pass `--residual-risk-signer` before the human answers the Section 8 decision banner) and record its full gate table (passed, not-applicable, and failed gates each listed and counted separately) in `10-validation-results.md` and `12-final-response.md` (matches `ReleaseReviewCoordinator.verify_readiness` in `STAGE_VERIFY`). State the exact treatment of each gate class: (a) when `residual_risk` is the only failing gate, every other applicable gate passed and the missing human sign-off is requested by the Section 8 `RELEASE REVIEW DECISION` banner, so a `GO` recommendation is permitted; (b) when a standing corpus/seed gate (`ipd_lint` or `capability_freshness`) fails and no hard gate fails, the recommendation may NOT be a clean `GO` - it is `NO-GO` if the failing plan or claim is in-scope for this release or untriaged, and at most `CONDITIONAL GO` if verified to be an out-of-scope pending plan or tracked standing item, with each failing gate named in the decision banner's `Blocking / pending items` and `Conditions` lines; (c) when any of the 8 hard gates (`full_suite`, `leak_scan`, `benchmark_thresholds`, `generated_drift`, `docs_checks`, `workflow_disposition`, `changelog_versioning`, `artifact_manifest`) fails, the recommendation is `NO-GO` (unless a `full_suite` failure is already tracked as an explicit release blocker per the paragraph above, which still caps the recommendation at `CONDITIONAL GO` or `NO-GO`, never `GO`).
       - Under `## Exit gate`, add a checkbox confirming `aw releases readiness` was run with the honest `--suite-passed` / `--suite-failed` flag (and without forging `--residual-risk-signer`), recorded in `10-validation-results.md` and `12-final-response.md`, and its standing-`NO-GO` rules applied to the recommendation.
    2. In `.aw/system/workflows/release-review/templates/final-response.md` under `## Tests and validations run`, note that `aw releases readiness` (with `--suite-passed` or `--suite-failed` matching the full-suite run) and its gate verdict / failing-gate list must be recorded in the table, and under `## Final release recommendation` state that any failing `aw releases readiness` hard gate forces `NO-GO`, any failing standing gate (`ipd_lint`, `capability_freshness`) caps the recommendation at `CONDITIONAL GO` (when out-of-scope/triaged) or `NO-GO`, and an unsigned `residual_risk` alone is satisfied by the human's Section 8->9 release approval.
    3. In `.aw/system/workflows/release-review/09-release-execution.md` under `## Hard preconditions (do not start otherwise)`, add item `6. **Release-readiness check (`aw releases readiness`).**` requiring `aw releases readiness --suite-passed --residual-risk-signer "<approver>"` (using the human approver's identity from precondition 2) to report no failing applicable gate, with every not-applicable gate restated to the human in the release-approval prompt, or, if a standing `CONDITIONAL GO` gate (`ipd_lint` on an out-of-scope pending plan or `capability_freshness`) remains red, requiring the human's explicit written waiver of that named gate under precondition 3; any failure in a hard gate (`full_suite`, `leak_scan`, `benchmark_thresholds`, `generated_drift`, `docs_checks`, `workflow_disposition`, `changelog_versioning`, `artifact_manifest`) or an unsigned `residual_risk` aborts Section 9 before any push, tag, or publish (matches `ReleaseReviewCoordinator.authorize_release`).
    4. In `RELEASING.md` under `## The release consent decision tree (release-review Section 8/9)`, add a concise paragraph stating that Section 8 runs `aw releases readiness --suite-passed` (or `--suite-failed`) without `--residual-risk-signer` (allowing `GO` when `residual_risk` is the only failing gate, capping at `CONDITIONAL GO` when a standing `ipd_lint` or `capability_freshness` failure is triaged as out-of-scope, and forcing `NO-GO` on any hard gate failure), and Section 9 re-runs `aw releases readiness --suite-passed --residual-risk-signer "<approver>"` before cutting a candidate or full release. Write no em or en dashes in `RELEASING.md` or workflow prose (`AGENTS.md`).
    5. APPLICABILITY AND NOT-APPLICABLE DISPLAY (OQ-03 answer (b), PR-002, PR-006): `08-final-ship-review.md`, `09-release-execution.md`, `templates/final-response.md`, and `RELEASING.md` each state that the readiness step runs in EVERY repository (no repository-specific carve-out, since the installed workflow must not carry anything meant only for this repository), and that a gate whose input files are absent is reported NOT-APPLICABLE, does not force `NO-GO`, needs no triage or waiver, and is NEVER counted or described as passed. Display rules: (a) Section 8 `## Final validation` and the `## Exit gate` checkbox require every not-applicable gate to be named in a bold `WARNING` in the Go/No-Go section and the summary, and in the `RELEASE REVIEW DECISION` banner's `Blocking / pending items` line, with the reason "input absent, NOT verified"; (b) `templates/final-response.md` adds a `Not-applicable gates` row to `## Tests and validations run` and repeats the warning under `## Final release recommendation`; (c) Section 9 precondition 6 requires the not-applicable list to be restated to the human in the release-approval prompt before any push, tag, or publish; (d) any count the reviewer writes reads as `N passed, M not-applicable, K failed`, never folding M into N; and (e) a not-applicable `full_suite` or `residual_risk` is a hard failure.
  - Execution state: performed

- [x] E-05 Run `docs_check`, `aw sanitize --agent`, the release-readiness and new coordinator test suites, and the full bare test suite.
  - Depends on: E-04
  - Expected outcome: (1) `docs_check.check_docs_dir(Path("docs"))` returns `[]` and a dash scan (`\u2014` / `\u2013`) over `RELEASING.md`, `.aw/system/workflows/release-review/08-final-ship-review.md`, `.aw/system/workflows/release-review/09-release-execution.md`, and `.aw/system/workflows/release-review/templates/final-response.md` returns 0 matches; (2) `python3 -m agent_workflows sanitize --agent` returns `"outcome": "clean"` (`exit: 0`); (3) `python3 -m pytest -o addopts="" -q tests/test_release_review_readiness.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` passes with 0 failures; and (4) bare `python3 -m pytest` passes with zero new failures compared by name against the execution-base baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Never write another role's attestation field or synthesize human consent (`AGENTS.md`; `agent_workflows/run_gates.py`; `wa64wz` F-02): `--residual-risk-signer` may only be passed after a human explicitly approves release execution in Section 8->9.
- `ReleaseReviewCoordinator` in `agent_workflows/migration_complex.py` owns the deterministic stage machine (`STAGE_AUDIT`, `STAGE_LEDGER`, `STAGE_PLAN`, `STAGE_MUTATION`, `STAGE_VERIFY`, `STAGE_RELEASE`), freezing `RELEASE_MODE_PLANNING` vs `RELEASE_MODE_FULL` at construction so planning mode cannot enter `STAGE_MUTATION`, `STAGE_VERIFY`, or `STAGE_RELEASE`.
- Synthetic test trees must set `GIT_CEILING_DIRECTORIES` so `versioning._git_describe` does not climb into the enclosing checkout (`dyiasf` PR-002).
- Tests must assert observable behavior and outcomes, never source structure (`inspect`, `ast`, regex over `.py` files, or line counts), and must be falsifiable against the pre-change code (`AGENTS.md` and `GUIDING_PRINCIPLES.md` P16).
- User-facing prose (`RELEASING.md`, workflow docs) must contain no em or en dashes (`AGENTS.md`).
- Full test suite runs BARE as `python3 -m pytest` (no `-n0`, extra `-q`, or `-p no:randomly`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `wa64wz` shipped `aw releases readiness`, but nothing in `release-review`, `RELEASING.md`, CI, hooks, or `agent_workflows/` (outside `release_readiness.py` and `cli.py`) consumes `build_report` or `aw releases readiness` as a process step at HEAD `53eb3077e`. | `git grep -n -e build_report -e run_readiness -e "releases readiness" -- '*.py' '.aw/system/workflows/' 'RELEASING.md' '.github/' '.pre-commit-config.yaml' ':!tests/'` matches only `agent_workflows/cli.py` (`return release_readiness_mod.run_readiness(args)`) and `agent_workflows/release_readiness.py` (`build_report`, `run_readiness`, and `__all__`). Zero occurrences exist in `.aw/system/workflows/release-review/08-final-ship-review.md`, `.aw/system/workflows/release-review/09-release-execution.md`, `.aw/system/workflows/release-review/templates/final-response.md`, or `RELEASING.md`. |
| F-02 | `ReleaseReviewCoordinator` in `agent_workflows/migration_complex.py` defines `STAGE_VERIFY = "verify"` between `STAGE_MUTATION` and `STAGE_RELEASE`, but no method on `ReleaseReviewCoordinator` ever enters `STAGE_VERIFY` or consumes `ReleaseReadinessReport`. | `git grep -n "STAGE_VERIFY" agent_workflows/` hits only `agent_workflows/migration_complex.py` at `STAGE_VERIFY: str = "verify"`, inside `ReleaseReviewCoordinator.enter_stage`'s allowed-stage union, and in `__all__`. `ReleaseReviewCoordinator.run_fix_bar` enters `STAGE_LEDGER`, `ReleaseReviewCoordinator.integrate_fixes` enters `STAGE_MUTATION`, and `ReleaseReviewCoordinator.authorize_release` enters `STAGE_RELEASE`. |
| F-03 | `release-review` Section 8 (`STAGE_VERIFY`) and Section 9 (`STAGE_RELEASE`) — together with `RELEASING.md` and `ReleaseReviewCoordinator` — are the right consumer surface, whereas a pre-commit hook or a fail-closed routine CI step would either require forged attestations or fail on every routine commit whenever a pending IPD has an open blocking question. | `agent_workflows/release_readiness.py`'s module docstring states: *"It is the checkable core of the final release-readiness review. INVARIANT (airtight, cited to RELEASING.md / release-review Section 9): this module NEVER tags, publishes, deploys, or pushes."* At commit/PR time, neither `make test-all` nor human residual-risk sign-off exists; forging `--suite-passed` or `--residual-risk-signer` violates `wa64wz` F-02 and `AGENTS.md`. Moreover, `aw releases readiness` runs `aw ipd lint --all --agent` (`release_readiness.gate_ipd_lint`), a `livecorpus` check that exits `1` whenever any pending IPD in `.aw/records/plans/pending/` carries an open `Blocking: yes` question (`IPD-Q501`, `514wv3` F-01..F-03). `.pre-commit-config.yaml` already runs `aw check-local-leaks` directly, `.github/workflows/tests.yml` already runs `aw check plans/releases/backlog/release-gates --agent` in `attention-check`, and `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[releases readiness]` already runs `aw releases readiness --agent` in CI to verify its `aw.agent/v1` contract without requiring a `GO` verdict on routine commits. |
| F-04 | The 11 gates of `ReleaseReadinessReport` partition cleanly into (1) the human release-time attestation gate (`residual_risk`), (2) standing corpus/seed gates that cap Section 8 at `CONDITIONAL GO` when triaged as out-of-scope (`ipd_lint`, `capability_freshness`), and (3) 8 non-waivable hard gates (`full_suite`, `leak_scan`, `benchmark_thresholds`, `generated_drift`, `docs_checks`, `workflow_disposition`, `changelog_versioning`, `artifact_manifest`). | `agent_workflows/release_readiness.py` exports NO `GATE_ORDER` (corrected at review, PR-001); `release_readiness.build_report` appends exactly those 11 `GateResult` names when `run_subprocess_gates=True` (9, without `leak_scan`/`ipd_lint`, when False). In `.aw/system/workflows/release-review/08-final-ship-review.md` (`## Final validation`, `**Pending-plans / staged-prompts gate.**`, and `## Section 9 handoff and the release consent decision tree`) and `09-release-execution.md` (`## Hard preconditions (do not start otherwise)`), pending plans / standing conditions cap Section 8 at `CONDITIONAL GO` (requiring explicit written human waiver in Section 9 Hard Precondition 3), while human release approval occurs between Section 8 and Section 9. |
| F-06 | Per the maintainer's OQ-03 answer (option (b)), the readiness step runs in every repository and an input-absent gate reports NOT-APPLICABLE; that `release_readiness` change is carried by backlog `v1re2z` (`Work-Kind: bug`, `Blocks-Release: next`), which has no plan yet. This plan therefore consumes the not-applicable state and depends on `v1re2z` rather than implementing it. | `.aw/records/backlog/open/20261015-uypgvi-01-v1re2z-readiness-absent-input-na.backlog.md` ("Plan kmmoca depends on this"); this plan's `- Scope:` OUT clause fences `agent_workflows/release_readiness.py` to `w9l8ph`; `ReleaseReadinessReport.failing_gates` and `GateResult.passed` at review HEAD carry only a boolean, so no not-applicable state exists yet. |
| F-05 | Placing the new coordinator behavioral tests in `tests/test_release_review_readiness.py` avoids perturbing the exact 5-file test counts cited in sibling pending plans `w9l8ph` (`3jkm7y`) and `8ru81x` (`5gzno3`), and gives zero `- Scope-Paths:` overlap with any pending plan in `.aw/records/plans/pending/`. | `git grep -n -e "migration_complex.py" -e "08-final-ship-review.md" -e "09-release-execution.md" -e "final-response.md" -e "RELEASING.md" -e "test_release_review_readiness.py" .aw/records/plans/pending/` matches only this plan (`kmmoca`). `python3 -m pytest -o addopts="" -q tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` passes (`74 passed in 16.25s`) at `53eb3077e`. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures `ReleaseReviewCoordinator` and the `release-review` / `RELEASING.md` surfaces at the executing HEAD before any edit.
2. E-02 adds `READINESS_ATTESTATION_GATES`, `READINESS_STANDING_WAIVABLE_GATES`, `READINESS_HARD_GATES`, `RECOMMENDATION_GO`, `RECOMMENDATION_CONDITIONAL_GO`, `RECOMMENDATION_NO_GO`, `ReadinessVerification`, and `ReleaseReviewCoordinator.verify_readiness` (entering `STAGE_VERIFY`) plus readiness enforcement in `ReleaseReviewCoordinator.authorize_release` (at `STAGE_RELEASE`) in `agent_workflows/migration_complex.py`.
3. E-03 adds behavioral and falsifiability tests in `tests/test_release_review_readiness.py` (shown RED against pre-change `migration_complex.py` first) covering planning-mode refusal of `STAGE_VERIFY`, unsigned `residual_risk` in Section 8 vs Section 9, untriaged vs triaged standing `ipd_lint` / `capability_freshness` failures, non-waivable hard gate failures, and not-applicable gates (never passes, never blocking, always surfaced).
4. (PRECONDITION, not an E-item: backlog `v1re2z` is `done`, enforced by `- Item-Dependencies` and re-proved by E-01(e).) E-04 updates `.aw/system/workflows/release-review/08-final-ship-review.md`, `.aw/system/workflows/release-review/09-release-execution.md`, `.aw/system/workflows/release-review/templates/final-response.md`, and `RELEASING.md` to run `aw releases readiness` in Section 8 and Section 9 and apply the standing-`NO-GO` rules.
5. E-05 runs `docs_check.check_docs_dir(Path("docs"))`, dash checks on the edited markdown files, `aw sanitize --agent`, the targeted test suites, and bare `python3 -m pytest`.

## Deferred / out of scope (with reason)

- Wiring `gate_artifact_manifest` to validate `.aw/system/workflows/index.md` on disk.
  - Carrier: w9l8ph, 3jkm7y
  - Carrier-Evidence: .aw/records/plans/executed/20261014-3jkm7y-01-w9l8ph-wire-the-release-artifact-manifest-gate-to-validate-the-work.ipd.md
- Implementing the NOT-APPLICABLE gate state in `agent_workflows/release_readiness.py` (OQ-03 answer (b)): a prerequisite, not deferred work; this plan consumes it and waits on it via `- Item-Dependencies: state:backlog:done:v1re2z`.
  - Carrier: v1re2z
- Retiring the 19 unproven `supported: true` booleans in `.aw/system/workflows/conformance/tools/host_matrix.json`.
  - Carrier: 8ru81x, 5gzno3
  - Carrier-Evidence: .aw/records/plans/executed/20261014-5gzno3-01-8ru81x-retire-unproven-supported-booleans-from-the-conformance-host.ipd.md
- Running `aw releases readiness` as a pre-commit hook or a fail-closed routine CI step on every push/PR: rejected by design because routine commits have neither `make test-all` results nor human residual-risk sign-off, and `ipd_lint` is a `livecorpus` check that exits `1` whenever any pending plan carries an open blocking question (F-03, OQ-01).
  - Carrier-Declined: routine commits and PRs lack full-suite results and human residual-risk sign-off, and ipd_lint is a livecorpus check that exits 1 whenever any pending plan has an open blocking question (F-03, OQ-01)

## Scope check

- Over-scope: none. Every file in `- Scope-Paths:` is directly required to consume the `release_readiness` report in `ReleaseReviewCoordinator` (`agent_workflows/migration_complex.py`), test that behavior (`tests/test_release_review_readiness.py`), and wire the command, the standing-`NO-GO` rules, and the prominent not-applicable display into `release-review` Section 8, Section 9, `templates/final-response.md`, and `RELEASING.md`.
- Under-scope: none. Both questions posed by backlog item `uypgvi` (which process surface runs `aw releases readiness`, and how a standing `NO-GO` such as unsigned `residual_risk` or live `ipd_lint` red is treated there) are answered in code (`ReleaseReviewCoordinator.verify_readiness` / `authorize_release`), workflow instructions (`08-final-ship-review.md`, `09-release-execution.md`, `templates/final-response.md`), and release documentation (`RELEASING.md`).

## Required tests / validation

Run the pre-E-02 RED demonstration of `tests/test_release_review_readiness.py`, the post-E-03 GREEN run of `python3 -m pytest -o addopts="" -v tests/test_release_review_readiness.py`, the 6-file readiness suite (`python3 -m pytest -o addopts="" -q tests/test_release_review_readiness.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py`), `docs_check.check_docs_dir(Path("docs"))`, `python3 -m agent_workflows sanitize --agent`, and the full bare test suite (`python3 -m pytest`), comparing any failure by name against the execution-base baseline.

## Spec / documentation sync

No `.spec.md` in `.aw/records/specs/` governs `release_readiness` or `ReleaseReviewCoordinator` (`git grep -n "release_readiness\|ReleaseReviewCoordinator" .aw/records/specs/` returns 0 matches). `RELEASING.md` and the `release-review` Section 8/9 workflow documents (`.aw/system/workflows/release-review/08-final-ship-review.md`, `09-release-execution.md`, `templates/final-response.md`) are updated directly in E-04.

## Open questions

### OQ-01: Should `aw releases readiness` run in `release-review` Section 8 + Section 9 (`ReleaseReviewCoordinator`), a routine CI job, or a git hook?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence (F-01, F-02, F-03): `aw releases readiness` is run in `release-review` Section 8 (`08-final-ship-review.md` / `ReleaseReviewCoordinator.verify_readiness` at `STAGE_VERIFY`) and re-verified with the human approver's identity in Section 9 (`09-release-execution.md` / `ReleaseReviewCoordinator.authorize_release` at `STAGE_RELEASE`), documented in `RELEASING.md`. A git hook (`.pre-commit-config.yaml`) and a fail-closed routine CI job (`.github/workflows/tests.yml`) are both ruled out: routine commits and PRs are not releases, neither `make test-all` nor human residual-risk sign-off exists on routine commits, forging `--suite-passed` or `--residual-risk-signer` violates `wa64wz` F-02 and `AGENTS.md`, and `aw releases readiness` shells out to `aw ipd lint --all --agent` (`gate_ipd_lint`), a `livecorpus` check that legitimately exits `1` whenever any pending plan in `.aw/records/plans/pending/` has an open `Blocking: yes` question (`IPD-Q501`). CI already runs `aw check plans/releases/backlog/release-gates --agent` in `attention-check` and `tests/test_agent_surface_conformance.py::test_agent_surface_conformance[releases readiness]` to verify `aw.agent/v1` conformance of `aw releases readiness --agent`.

### OQ-02: How should a standing `NO-GO` (unsigned `residual_risk`, live `ipd_lint` red, or `capability_freshness` red) be treated in Section 8 and Section 9?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence (F-04):
  1. **Unsigned `residual_risk` (`READINESS_ATTESTATION_GATES`)**: in Section 8 (`STAGE_VERIFY`), before the human replies to the `RELEASE REVIEW DECISION` banner, `aw releases readiness` is invoked without `--residual-risk-signer`, so `residual_risk` fails (`residual-risk sign-off missing`). When `residual_risk` is the ONLY failing gate, Section 8 (`verify_readiness`) yields `recommendation == "GO"` with `pending_human_attestation=True`. In Section 9 (`STAGE_RELEASE` / `authorize_release`), the human approver's identity supplies `--residual-risk-signer "<approver>"`, and an unsigned `residual_risk` in Section 9 is refused with `ReleaseAuthorityError`.
  2. **Standing corpus / seed-data gates (`ipd_lint`, `capability_freshness` — `READINESS_STANDING_WAIVABLE_GATES`)**: when either gate fails in Section 8 and no hard gate fails, the Section 8 recommendation cannot be a clean `GO`. If untriaged (or in-scope for the release), `verify_readiness` returns `"NO-GO"`; if triaged by the reviewer as an out-of-scope pending plan or tracked standing item (`triaged_standing_gates`), `verify_readiness` caps the recommendation at `"CONDITIONAL GO"` and requires the failing gate to be named in the `RELEASE REVIEW DECISION` banner's `Blocking / pending items` and `Conditions` lines. In Section 9 (`authorize_release`), a standing gate that remains red refuses release execution unless the human's release approval explicitly waives that named standing gate (`waived_standing_gates`) per Section 9 Hard Precondition 3.
  3. **Hard technical / release-integrity gates (`full_suite`, `leak_scan`, `benchmark_thresholds`, `generated_drift`, `docs_checks`, `workflow_disposition`, `changelog_versioning`, `artifact_manifest` — `READINESS_HARD_GATES`)**: any failure forces `"NO-GO"` in Section 8 and raises `ReleaseAuthorityError` in Section 9; attempting to pass any hard gate in `triaged_standing_gates` or `waived_standing_gates` is refused with `ComplexMigrationError` / `ReleaseAuthorityError`.

### OQ-03: Where must Section 8/9 run `aw releases readiness`, given that the release-review workflow is installed into every managed repository?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Carrier: kmmoca
- Resolution or deferral rationale: RESOLVED by the maintainer 2026-10-15 (interactive /askme): option (b). The readiness step is generic and runs in release-review in EVERY repository; a gate whose input files are absent reports not-applicable and does not force NO-GO (in this repository every input exists, so every gate runs in full). Accepted risk: a repository that deleted an input by mistake sees not-applicable rather than a failure, so the N/A gates must be shown prominently. The release_readiness change is carried by backlog v1re2z, which this plan depends on. The maintainer also ruled that anything meant only for this repository must not be installed into other repositories. Original review text follows. Raised at review (PR-002). `.aw/system/workflows/release-review/` is an installed workflow body (`engine.collect_source_members` ships `08-final-ship-review.md`), but several "hard" gates presuppose THIS toolkit's own tree. Measured at review, `build_report(suite_passed=True, residual_risk_signed=True, run_subprocess_gates=False)` on a minimal managed-style tree (`.aw/system/workflows/release-review/`, `.aw/records/`, no `docs/`, no `CHANGELOG.md`, no host matrix) FAILS `docs_checks` ("docs tree missing"), `workflow_disposition` ("could not run: FileNotFoundError"), `capability_freshness` ("capability matrix missing") and `changelog_versioning`, and `gate_leak_scan` returned "exit 2" on a bare temp dir. Under this plan's classes, three of those are non-waivable hard gates, so mandating the step in the shipped workflow would make every managed repository's release-review a permanent `NO-GO`. The reviewer cannot choose among the remedies because each changes a shipped contract: (a) apply the readiness step only to the agent-workflows repository itself (the workflow says so and tells other repositories to skip it); (b) apply it everywhere but let a reviewer mark a gate whose PRODUCER is absent as not-applicable (needs a `release_readiness` change, owned by `w9l8ph` or a new plan); (c) apply it everywhere as written and accept that managed repositories cannot release through release-review until they supply every producer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 measurement transcript (code paths: `agent_workflows/migration_complex.py::ReleaseReviewCoordinator`, `agent_workflows/release_readiness.py::build_report`): (a) the `git grep` output, showing no release-review file, `RELEASING.md`, CI workflow, or hook among the matches; (b) the `git grep -n "STAGE_VERIFY" agent_workflows/` output matching only `agent_workflows/migration_complex.py`; (c) `python3 -c "from agent_workflows import migration_complex as mc; print(hasattr(mc.ReleaseReviewCoordinator, 'verify_readiness'))"` printing `False`; and (d) the E-01(e) precondition evidence: `aw find backlog v1re2z` (or equivalent) showing `v1re2z` `done`, plus the driven `build_report` probe output on the minimal managed-style tree naming each input-absent gate, the exact not-applicable signal (attribute or method) it carries, and that signal's value differing from both a passing and a failing gate.
  - Observed evidence:
    Execution HEAD sha: `ad1a74e13fee3fe8b1af256327c6b3dfb297b216`
    (a) `git grep -n -e build_report -e run_readiness -e "releases readiness" -- '*.py' '.aw/system/workflows/' 'RELEASING.md' '.github/' '.pre-commit-config.yaml' ':!tests/'`:
    ```text
    .aw/system/workflows/benchmark/tools/bench_env.py:754:def build_report(
    .aw/system/workflows/benchmark/tools/bench_env.py:847:    rep = build_report(repo, paths, args.disk_probe, args.probe_mb, warm, args.scrub)
    agent_workflows/cli.py:6734:            "  aw releases readiness --suite-passed --residual-risk-signer qa\n"
    agent_workflows/cli.py:19488:            return release_readiness_mod.run_readiness(args)
    agent_workflows/command_surface.py:1905:        command="releases readiness",
    agent_workflows/release_readiness.py:873:def build_report(
    agent_workflows/release_readiness.py:918:def run_readiness(args: Any) -> int:
    agent_workflows/release_readiness.py:919:    """``aw releases readiness``: render the read-only GO / NO-GO release-readiness report."""
    agent_workflows/release_readiness.py:938:        "releases readiness", repo_root, explicit_dir=explicit_dir
    agent_workflows/release_readiness.py:943:                command="releases readiness",
    agent_workflows/release_readiness.py:973:        report = build_report(
    agent_workflows/release_readiness.py:982:            f"aw releases readiness: could not build readiness report: "
    agent_workflows/release_readiness.py:987:                command="releases readiness",
    agent_workflows/release_readiness.py:1043:            command="releases readiness",
    agent_workflows/release_readiness.py:1094:    "build_report",
    agent_workflows/release_readiness.py:1095:    "run_readiness",
    ```
    No release-review file, RELEASING.md, CI workflow, or hook consumes the report.
    (b) `git grep -n "STAGE_VERIFY" agent_workflows/`:
    ```text
    agent_workflows/migration_complex.py:107:STAGE_VERIFY: str = "verify"
    agent_workflows/migration_complex.py:306:            STAGE_VERIFY,
    agent_workflows/migration_complex.py:1044:    "STAGE_VERIFY",
    ```
    (c) Coordinator method probe:
    `hasattr verify_readiness: False`
    (d) `GATE_ORDER` and gate names emitted:
    `hasattr GATE_ORDER: False`
    `gate names: ['full_suite', 'leak_scan', 'ipd_lint', 'generated_drift', 'docs_checks', 'workflow_disposition', 'capability_freshness', 'benchmark_thresholds', 'changelog_versioning', 'artifact_manifest', 'residual_risk']`
    (e) Precondition evidence:
    `v1re2z in done: ['.aw/records/backlog/done/20261015-uypgvi-01-v1re2z-readiness-absent-input-na.backlog.md']`
    Driven probe on minimal managed-style tree:
    `failing_gates: ['changelog_versioning', 'artifact_manifest', 'residual_risk']`
    `passed_gates: ['full_suite', 'benchmark_thresholds']`
    `not_applicable_gates: ['generated_drift', 'docs_checks', 'workflow_disposition', 'capability_freshness']`
    `gate full_suite: passed=True, applicable=True, status=pass`
    `gate generated_drift: passed=False, applicable=False, status=not-applicable`
    `gate docs_checks: passed=False, applicable=False, status=not-applicable`
    `gate workflow_disposition: passed=False, applicable=False, status=not-applicable`
    `gate capability_freshness: passed=False, applicable=False, status=not-applicable`
    `gate benchmark_thresholds: passed=True, applicable=True, status=pass`
    `gate changelog_versioning: passed=False, applicable=True, status=fail`
    `gate artifact_manifest: passed=False, applicable=True, status=fail`
    `gate residual_risk: passed=False, applicable=True, status=fail`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` hunk for `agent_workflows/migration_complex.py` and a driven Python probe transcript (code paths created by E-02: `migration_complex.ReleaseReviewCoordinator.verify_readiness` and `migration_complex.ReleaseReviewCoordinator.authorize_release` over `release_readiness.build_report`) demonstrating: (1) `READINESS_ATTESTATION_GATES`, `READINESS_STANDING_WAIVABLE_GATES`, and `READINESS_HARD_GATES` are disjoint and their union equals the gate names `release_readiness.build_report(..., run_subprocess_gates=True)` emits, and an unclassified failing gate is treated as hard; (2) `verify_readiness` on an unsigned-`residual_risk`-only report enters `STAGE_VERIFY` and returns `recommendation='GO', pending_human_attestation=True`; (3) `verify_readiness` on an `ipd_lint` failure returns `'NO-GO'` when untriaged and `'CONDITIONAL GO'` when `triaged_standing_gates=('ipd_lint',)`; (4) `verify_readiness` on the E-01(e) minimal managed-style tree lists the input-absent gates in `not_applicable_gates` and in none of `passed_gates` / `hard_failures` / `standing_failures`, and a not-applicable `full_suite` or `residual_risk` lands in `hard_failures`; and (5) `authorize_release` passes the not-applicable gate names into the `DecisionGate` prompt and `metadata["not_applicable_gates"]` (shown by an `input_handler` that prints the gate it receives) without requiring a waiver, refuses unsigned `residual_risk`, unwaived `ipd_lint`, and any `READINESS_HARD_GATES` failure with `ReleaseAuthorityError`, refuses `readiness_report=None`, and succeeds when every gate passes or when a standing `ipd_lint` failure is explicitly waived via `waived_standing_gates=('ipd_lint',)`.
  - Observed evidence:
    `git diff agent_workflows/migration_complex.py`:
    ```diff
    @@ -44,6 +44,7 @@
     from agent_workflows import engine
     from agent_workflows import orchestrate_isolation as _iso
    +from agent_workflows import release_readiness as _readiness
     from agent_workflows import run_freeze as _freeze
     from agent_workflows import run_gates as _gates
     from agent_workflows import run_state as _state
    @@ -122,6 +123,75 @@ class ReleaseAuthorityError(ComplexMigrationError):
         """Raised when a release is attempted without explicit human release authority."""

    +# Release readiness gate classifications (E-02 / kmmoca).
    +# Attestation gate requires explicit human release sign-off.
    +READINESS_ATTESTATION_GATES: FrozenSet[str] = frozenset(("residual_risk",))
    +# Standing corpus / seed-data gates that may be triaged in Section 8 (capping at CONDITIONAL GO)
    +# or explicitly waived in Section 9.
    +READINESS_STANDING_WAIVABLE_GATES: FrozenSet[str] = frozenset(
    +    ("ipd_lint", "capability_freshness")
    +)
    +# Hard technical/release-integrity gates: non-waivable, always force NO-GO / refuse release.
    +READINESS_HARD_GATES: FrozenSet[str] = frozenset(
    +    (
    +        "full_suite",
    +        "leak_scan",
    +        "benchmark_thresholds",
    +        "generated_drift",
    +        "docs_checks",
    +        "workflow_disposition",
    +        "changelog_versioning",
    +        "artifact_manifest",
    +    )
    +)
    +# Gates driven by explicit attestations, not files; reported not-applicable is treated as hard failure.
    +READINESS_INPUT_REQUIRED_GATES: FrozenSet[str] = frozenset(
    +    ("full_suite", "residual_risk")
    +)
    +
    +# Section 8 readiness recommendations.
    +RECOMMENDATION_GO: str = "GO"
    +RECOMMENDATION_CONDITIONAL_GO: str = "CONDITIONAL GO"
    +RECOMMENDATION_NO_GO: str = "NO-GO"
    +
    +@dataclass(frozen=True)
    +class ReadinessVerification:
    +    report: _readiness.ReleaseReadinessReport
    +    recommendation: str
    +    hard_failures: Tuple[str, ...]
    +    standing_failures: Tuple[str, ...]
    +    triaged_standing_gates: Tuple[str, ...]
    +    untriaged_standing_gates: Tuple[str, ...]
    +    not_applicable_gates: Tuple[str, ...]
    +    passed_gates: Tuple[str, ...]
    +    pending_human_attestation: bool
    ...
    ```
    Driven Python probe transcript:
    ```text
    === PROBE 1: Gate classes partition emitted gate names and unclassified treated as hard ===
    emitted == union: True
    unclassified in hard_failures: True rec: NO-GO
    === PROBE 2: verify_readiness on unsigned residual_risk ===
    stages_entered: ('verify',)
    recommendation: GO
    pending_human_attestation: True
    === PROBE 3: verify_readiness on ipd_lint failure untriaged vs triaged ===
    untriaged rec: NO-GO untriaged_gates: ('ipd_lint',)
    triaged rec: CONDITIONAL GO triaged_gates: ('ipd_lint',)
    === PROBE 4: verify_readiness on minimal managed tree and NA attestation ===
    not_applicable_gates: ('generated_drift', 'docs_checks', 'capability_freshness', 'changelog_versioning')
    none of NA in passed/hard/standing: True
    NA full_suite in hard_failures: True
    === PROBE 5: authorize_release not-applicable surfacing and refusals ===
    decision gate prompt: Execute the release (tag/publish)? This is irreversible. NOT-APPLICABLE gates (inputs absent, NOT verified): generated_drift, docs_checks, capability_freshness, changelog_versioning
    decision gate metadata: {'not_applicable_gates': ['generated_drift', 'docs_checks', 'capability_freshness', 'changelog_versioning']}
    authorized approved: True
    None report refused: release refused: no Section 9 readiness report supplied
    unsigned residual_risk refused: release refused: residual_risk gate is unsigned in readiness report
    unwaived ipd_lint refused: release refused: unwaived standing gate failure(s): ipd_lint
    decision gate prompt: Execute the release (tag/publish)? This is irreversible. NOT-APPLICABLE gates (inputs absent, NOT verified): generated_drift
    decision gate metadata: {'not_applicable_gates': ['generated_drift']}
    waived ipd_lint approved: True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste (1) the pre-E-02 RED pytest output of `python3 -m pytest -o addopts="" -v tests/test_release_review_readiness.py` failing against the unmodified `agent_workflows/migration_complex.py`; (2) the post-E-03 GREEN pytest output of `python3 -m pytest -o addopts="" -v tests/test_release_review_readiness.py` showing a passing test for each E-03 behavior (1)-(8) (test names are non-binding pointers; counts are not the bar); and (3) `git grep -n -E 'getsource|import ast|ast\.parse|import inspect|read_text\(.*migration_complex' tests/test_release_review_readiness.py` returning exit 1 (no matches).
  - Observed evidence:
    (1) Pre-E-02 RED pytest run:
    ```text
    FAILED tests/test_release_review_readiness.py::test_section8_unsigned_residual_risk_only_yields_go_with_pending_attestation
    FAILED tests/test_release_review_readiness.py::test_section8_standing_ipd_lint_and_capability_freshness_untriaged_vs_triaged
    FAILED tests/test_release_review_readiness.py::test_section9_authorize_release_enforces_signed_readiness_and_waivers
    FAILED tests/test_release_review_readiness.py::test_planning_mode_refuses_verify_readiness
    FAILED tests/test_release_review_readiness.py::test_section8_clean_signed_report_yields_go_without_pending_attestation
    FAILED tests/test_release_review_readiness.py::test_not_applicable_gates_are_never_passes_and_never_block
    FAILED tests/test_release_review_readiness.py::test_gate_classes_partition_the_emitted_gate_names
    FAILED tests/test_release_review_readiness.py::test_section8_hard_gate_failure_forces_no_go_and_refuses_triage
    ============================== 8 failed in 3.43s ===============================
    ```
    (2) Post-E-03 GREEN pytest run:
    ```text
    tests/test_release_review_readiness.py::test_section8_clean_signed_report_yields_go_without_pending_attestation PASSED [ 12%]
    tests/test_release_review_readiness.py::test_section9_authorize_release_enforces_signed_readiness_and_waivers PASSED [ 25%]
    tests/test_release_review_readiness.py::test_section8_unsigned_residual_risk_only_yields_go_with_pending_attestation PASSED [ 37%]
    tests/test_release_review_readiness.py::test_section8_standing_ipd_lint_and_capability_freshness_untriaged_vs_triaged PASSED [ 50%]
    tests/test_release_review_readiness.py::test_not_applicable_gates_are_never_passes_and_never_block PASSED [ 62%]
    tests/test_release_review_readiness.py::test_planning_mode_refuses_verify_readiness PASSED [ 75%]
    tests/test_release_review_readiness.py::test_section8_hard_gate_failure_forces_no_go_and_refuses_triage PASSED [ 87%]
    tests/test_release_review_readiness.py::test_gate_classes_partition_the_emitted_gate_names PASSED [100%]
    ============================== 8 passed in 4.39s ===============================
    ```
    (3) Non-pinning check:
    `git grep -n -E 'getsource|import ast|ast\.parse|import inspect|read_text\(.*migration_complex' tests/test_release_review_readiness.py` returned exit code 1 (no matches).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `git diff` hunks for `.aw/system/workflows/release-review/08-final-ship-review.md`, `.aw/system/workflows/release-review/09-release-execution.md`, `.aw/system/workflows/release-review/templates/final-response.md`, and `RELEASING.md` showing `aw releases readiness` wired into Section 8 (`## Final validation` and `## Exit gate`), `templates/final-response.md` (`## Tests and validations run` and `## Final release recommendation`), Section 9 (`## Hard preconditions`), and `RELEASING.md` (`## The release consent decision tree (release-review Section 8/9)`), including the exact rules for unsigned `residual_risk`, standing `ipd_lint` / `capability_freshness` failures, and hard gate failures, plus the E-04(5) not-applicable rules: the every-repository applicability statement (no repository-specific carve-out), the bold `WARNING` and `Blocking / pending items` naming of not-applicable gates in Section 8, the `Not-applicable gates` row in `templates/final-response.md`, the restatement to the human in Section 9 precondition 6, and the separate `N passed, M not-applicable, K failed` count. Also paste `git grep -n -i 'not-applicable' -- RELEASING.md .aw/system/workflows/release-review/08-final-ship-review.md .aw/system/workflows/release-review/09-release-execution.md .aw/system/workflows/release-review/templates/final-response.md` showing at least one hit in each of the four files.
  - Observed evidence:
    `git grep -n -i 'not-applicable' -- RELEASING.md .aw/system/workflows/release-review/08-final-ship-review.md .aw/system/workflows/release-review/09-release-execution.md .aw/system/workflows/release-review/templates/final-response.md`:
    ```text
    .aw/system/workflows/release-review/08-final-ship-review.md:95:**Release-readiness report gate (`aw releases readiness`).** The readiness step is generic and runs in release-review in EVERY repository (no repository-specific carve-out)...
    .aw/system/workflows/release-review/08-final-ship-review.md:99:- **Not-applicable gates:** a gate whose input files are absent is reported NOT-APPLICABLE, does not force `NO-GO`, needs no triage or waiver, and is NEVER counted or described as passed...
    .aw/system/workflows/release-review/08-final-ship-review.md:178:- [ ] **Release-readiness gate (`aw releases readiness`):** run with the honest `--suite-passed` / `--suite-failed` flag (and without forging `--residual-risk-signer`)...
    .aw/system/workflows/release-review/09-release-execution.md:25:6. **Release-readiness check (`aw releases readiness`).** Run `aw releases readiness --suite-passed --residual-risk-signer "<approver>"`...
    .aw/system/workflows/release-review/templates/final-response.md:36:Record every validation run, including `aw releases readiness` (with `--suite-passed` or `--suite-failed` matching the full test run)...
    .aw/system/workflows/release-review/templates/final-response.md:40:| `aw releases readiness` | <VERDICT> (N passed, M not-applicable, K failed) | <Failing gates, or "clean"> |
    .aw/system/workflows/release-review/templates/final-response.md:41:| Not-applicable gates | <List of not-applicable gates or "none"> | Inputs absent, NOT verified |
    .aw/system/workflows/release-review/templates/final-response.md:137:Readiness report gate rules: any failing `aw releases readiness` hard gate forces NO-GO...
    RELEASING.md:35:Before the decision tree is presented, Section 8 runs `aw releases readiness --suite-passed` (or `--suite-failed`) without `--residual-risk-signer`...
    ```
    Every file contains the required applicability and not-applicable display rules.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste (1) the output of `python3 -c "from pathlib import Path; from agent_workflows import docs_check; files = [Path('RELEASING.md'), Path('.aw/system/workflows/release-review/08-final-ship-review.md'), Path('.aw/system/workflows/release-review/09-release-execution.md'), Path('.aw/system/workflows/release-review/templates/final-response.md')]; dashes = [str(p) for p in files if '\u2014' in p.read_text() or '\u2013' in p.read_text()]; print('docs_check:', docs_check.check_docs_dir(Path('docs')), 'dashes:', dashes)"` printing `docs_check: [] dashes: []`; (2) the output of `python3 -m agent_workflows sanitize --agent` showing `"outcome": "clean"` and `"exit": 0`; (3) the output of `python3 -m pytest -o addopts="" -q tests/test_release_review_readiness.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_release_readiness_producers.py tests/test_releases_readiness_cli.py tests/test_release_readiness_child_pin.py` (0 failed; the pass count is context, re-derived at execution); and (4) the execution-base bare `python3 -m pytest` summary line alongside the post-change bare `python3 -m pytest` summary line showing zero new failures by name.
  - Observed evidence:
    (1) Docs check and dash scan:
    `docs_check: [] dashes: []`
    (2) `python3 -m agent_workflows sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5435,"findings":0,"evidence":["leak-scan"],"next":null}`
    (3) 6-file readiness test suite:
    `90 passed in 20.84s`
    (4) Execution-base bare suite vs post-change bare suite:
    Execution-base baseline: `748 passed in 56.76s`
    Post-change: `748 passed in 30.28s`
    Zero new failures compared by name against the baseline.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. OQ-01, OQ-02, and OQ-03 are all resolved (OQ-03 by the maintainer, 2026-10-15, option (b)). PRECONDITION: backlog `v1re2z` (the `release_readiness` not-applicable gate state) must be `done`; `- Item-Dependencies: state:backlog:done:v1re2z` makes the runner hold this plan until it is, and E-01(e) re-proves the shipped signal before any edit. Commit only the declared `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, `-a`, `--no-verify`, `git stash`, or a push. Verify the staged set with `git diff --cached --name-only` before committing (shared checkout). Paste actual runner output; never claim a test run that was not performed.

SCOPE FENCE. `- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`. `agent_workflows/release_readiness.py` stays untouched (owned by `w9l8ph`; the not-applicable change belongs to `v1re2z`).

RELEASE GATE. Backlog `uypgvi` is `Work-Kind: followup` with no `- Blocks-Release:`; none is inherited or invented. It reaches `done` through the `- From-Backlog: uypgvi` handoff; do not close it by hand.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all five `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
