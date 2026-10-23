# Review findings: plan f6el0l

- Subject-Id: f6el0l
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `306ad1182`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 29), one new test module.

Verified at the lane HEAD:
- `config.read_review_findings_gate` and `config.findings_gate_threshold` exist as described; `REVIEW_GATE_DEFAULT = "high"`, `REVIEW_GATE_THRESHOLDS = ("medium", "high", "blocker", "off")`.
- Every E-01 row reproduces by direct call on temp repos (recorded as plan F-07).
- F-03: no test under `tests/` names either function.
- F-02 premise: `tests/test_plan_readiness_recheck.py` `_mkrepo` writes `{"review_findings_gate": {"block_at": "high"}}`, equal to the default, so a None reader is invisible there. Two methods carry `@pytest.mark.core`.
- `tests/test_engine_restored_behavior.py` uses module-level `pytestmark = pytest.mark.core`.
- Sibling `p79jts` is pending and declares `tests/test_review_findings_gate.py`; no overlap with this plan's path.
- F-01 probe wall times (4 to 6 min per key) not re-run; the mechanism (probe reads committed HEAD) was confirmed for sibling `di5puw` at this HEAD.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Validation (kill not attributable) | E-03 / V-03 "verdict: killed" only; F-05 sibling `p79jts` core-marks `GateOutcomeTests`, which exercises `findings_gate_threshold` end to end | If `p79jts` lands first, the full-core probe could read `killed` from its tests alone, so V-03 would pass even if this module's assertions were weak. | all Low | FIXED | E-03, Required tests and V-03 now require `newly_failing` to include a test id from `tests/test_config_review_findings_gate.py` and `baseline_failing` to be recorded. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (bar vs pre-existing state) | bare run `1675 passed, 11 warnings in 34.68s` at `16d8abbb8`; `conftest.py` "Core tier wall time: ... exceeded budget of" | E-02 / V-02 did not say whether a budget overrun fails the plan; on this host the core tier already exceeds 30s before any change. | all Low | FIXED | E-02 and V-02 say an overrun is recorded verbatim, not a failure of this plan. |
| PR-003 | LOW | IN-SCOPE | Test isolation | `agent_workflows/project_context.py:1012` `project_config_dir` rule 2 (falls back to `<aw_home>/projects/<id>/config/project.json`); `conftest.py:442` home isolation | The "missing file" case silently depends on AW_HOME being sandboxed; an executor overriding AW_HOME could make it read a real home config. | all Low | FIXED | E-01 notes the dependency on the root conftest sandbox and forbids pointing AW_HOME at a real home. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | Gate lacked the paste-actual-output rule, scope-fence declaration wording, staged-set check, and conditional finalize ownership; it implied a hand move to `executed/`. No-production-change check covered only `<base>..HEAD`, not the working tree. | all Low | FIXED | Gate rewritten as a full execution contract; diff check covers both. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make the core-selection kill attributable to this plan's module? | Require a `newly_failing` entry from the new module | Probe only the new file (loses the full-gate proof OQ-02 chose); sequence after `p79jts` (adds a dependency for no gain) | `tools/mutation_probe.py` `newly_failing` output field; plan F-05 | yes |
| D-2 | Does a pre-existing core-tier wall-time overrun fail this plan? | No, record it verbatim | Keep implicit bar (unsatisfiable on this host) | bare run `34.68s` at `16d8abbb8`; siblings `btubm6`, `di5puw` same rule | yes |
