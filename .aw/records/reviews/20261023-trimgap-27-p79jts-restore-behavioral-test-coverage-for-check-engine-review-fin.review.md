# Review findings: plan p79jts

- Subject-Id: p79jts
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `49e83b75a`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 27), tests only, three declared paths.

Verified at the lane HEAD:
- `19313eed^:tests/test_review_findings_gate.py` run from a scratch location: `11 passed in 1.71s`. It contains `SourceInvariantTests` (substring assertions over sliced source) and `SubjectFieldIndexTests.test_no_review_record_in_the_tree_carries_the_retired_field` (reads the live `.aw/records/reviews/`), as E-01 says.
- `tools/mutation_probe.py --op return-none --extra-test 19313eed:tests/test_review_findings_gate.py` with selection `tests/test_review_findings_gate.py::GateOutcomeTests`: `check_review_finding_unescalated` and `evaluate_review_finding_escalation` both `verdict: killed`, `baseline_failing: 0`, newly failing `GateOutcomeTests::test_the_gate_fires_exactly_when_it_should`.
- E-03 (`check_plan_priority_required`), E-04(a) (`_plan_disposition`, all seven rows) and E-04(b) (`check_ipd_draft_ready`) expected outputs reproduce exactly by direct call using `tests.test_plan_priority_required._build_test_plan`.
- The two E-05 tests exist in `CheckEngineSpecCriteriaTests`, use `TemporaryDirectory`, and call `check_engine.check_spec_criteria_uncovered`; no test in that file is core-collected today.
- A class-level `@pytest.mark.core` on a `unittest.TestCase` collects only that class under `-m core` (scratch module in `tests/`, deleted).
- F-02 full-core probe wall times (6 to 10 min per key) not re-run.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Safety / repository convention (hand-edits of production code) | old `## Required tests / validation` "scratch edits to `agent_workflows/check_engine.py` inserting `return None` ... then `git checkout --`"; `tools/mutation_probe.py` `run_probe` "against committed HEAD"; AGENTS.md shared-checkout rule | Six hand mutations of a high-contention production file in the checkout, each reverted with `git checkout --`, which would also discard any concurrent co-worker edit to that file; the repo's own probe tool does this in an isolated worktree, and sibling reviews (`a5drqh`, `di5puw`) already replaced the same pattern. The plan also had no explicit commit step before mutation evidence. | all Low | FIXED | Required tests and V-02..V-05 now use `tools/mutation_probe.py` after a commit; E-05 gains the commit step; each probe must show `baseline_failing: 0`, `verdict: killed` and a `newly_failing` entry from the test assigned to that key. Convention bullet updated. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (check fails on correct work) | `19313eed^:tests/test_review_findings_gate.py:468` `_Case` rationale and `:1104` failure message, both naming "`test_no_review_record_in_the_tree_carries_the_retired_field`" | After E-01 removes that test, two surviving strings still name it, so V-01's `rg` would exit 0 on correct work, and the strings would point readers at a guard that no longer exists. | all Low | FIXED | E-01 rewords both strings to say the corpus-level guard was not restored; V-01's `rg` pattern targets the definitions and any remaining reference. Added F-06. |
| PR-003 | LOW | IN-SCOPE | Execution contract wording | old gate "Scope fence: the three Scope-Paths test files only"; no-production-change check covered only the working tree | The fence read as a restriction rather than a declaration; the production diff check missed committed changes. | all Low | FIXED | Fence reworded as a declaration with `--scope-reason`/`--scope-ack`; diff checks cover `<base>..HEAD` and the working tree; honesty rule made a MUST. |

`aw ipd lint --phase review-finalize --agent`: `clean` (an intermediate `IPD-I305` from a parenthetical in E-05 `Depends on` was fixed).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Run the six mutation spot-checks by hand-editing `check_engine.py` or through the probe tool? | Probe tool after a commit | Keep hand edits with `git checkout --` revert (risks discarding a co-worker's edit, contradicts sibling plans) | `tools/mutation_probe.py` `run_probe`; AGENTS.md shared-checkout rule; reviews of `a5drqh`, `di5puw` | yes |
| D-2 | Delete or reword the two strings naming the removed live-corpus test? | Reword to state the guard was not restored | Delete the `_Case` row (loses the retired-field contrast row); leave strings (V-01 fails, misleads readers) | `19313eed^:tests/test_review_findings_gate.py:468`, `:1104` | yes |
