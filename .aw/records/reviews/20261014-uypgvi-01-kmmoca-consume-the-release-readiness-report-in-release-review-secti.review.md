# Review findings: plan kmmoca

- Subject-Id: kmmoca
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

This review ran in an isolated, non-interactive review lane with no human channel. The plan was committed and unchanged (`fce42ffea`), so no snapshot was taken. `aw ipd lint --phase author --agent` was clean before revision. After revision, `--phase review-finalize` reports only the expected `IPD-Q501` on the new blocking OQ-03.

Re-verified at review HEAD:
- `migration_complex.ReleaseReviewCoordinator` defines `STAGE_VERIFY` and accepts it in `enter_stage`, but no method enters it. `authorize_release(*, interactive, input_handler, approver)` does not read any report. No test or module outside `migration_complex.py` references `ReleaseReviewCoordinator` or `migration_complex`, so changing the `authorize_release` contract breaks no caller (F-02 holds).
- `release_readiness` exports NO `GATE_ORDER` (`hasattr(release_readiness, "GATE_ORDER")` is `False`). `build_report(..., run_subprocess_gates=True)` emits the 11 gate names the plan lists. With `run_subprocess_gates=False` it emits 9, without `leak_scan`/`ipd_lint` (PR-001).
- `build_report(suite_passed=True, run_subprocess_gates=True)` on this tree failed `['ipd_lint', 'capability_freshness', 'residual_risk']`. That matches the plan's standing-gate model.
- On a minimal managed-style tree, the following gates FAIL: `docs_checks` ("docs tree missing"), `workflow_disposition` ("could not run: FileNotFoundError"), `capability_freshness` ("capability matrix missing"), and `changelog_versioning`. `gate_leak_scan` on a bare temp dir returned "leak scan exit 2". `engine.collect_source_members` ships `.aw/system/workflows/release-review/08-final-ship-review.md` to managed repositories (PR-002).
- The F-01 grep also matches `.aw/system/workflows/benchmark/tools/bench_env.py` (an unrelated `build_report`) and `agent_workflows/command_surface.py` (the command declaration). The claim "only release_readiness.py and cli.py" is wrong as a grep result, but the underlying property holds: no release-review file, `RELEASING.md`, CI workflow, or hook consumes the report (PR-003).
- `tests/test_agent_surface_conformance.py -k readiness`: 2 passed.
- No em or en dashes in the four target docs.
- Security lens: the plan strengthens a release-authority gate and forges no attestation, because `--residual-risk-signer` is used only after human approval. PR-004 closes a fail-open path the plan itself introduced.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / Evidence | `agent_workflows/release_readiness.py` (`hasattr(..., "GATE_ORDER")` is False; `build_report` appends gates inline) | E-02 derives `READINESS_HARD_GATES` from `_readiness.GATE_ORDER`, which does not exist, so the module would fail with `AttributeError` at import. The only natural fix (adding it) is in a module the plan fences out. The partition also had no defined behavior for a gate added later. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The hard set is now a literal. Any unclassified failing gate is treated as HARD (fail closed). Added E-03 test (7), which proves the partition against the names `build_report` emits. V-02 updated. |
| PR-002 | HIGH | UNDER-SCOPE | D. Domain invariants / installed contract | `engine.collect_source_members` ships `08-final-ship-review.md`; measured gate failures on a managed-style tree (above) | Section 8/9 are installed into every managed repository, but `docs_checks`, `workflow_disposition`, and `changelog_versioning` (hard, non-waivable here) fail wherever this toolkit's own tree layout is absent. Mandating the step there forces a permanent NO-GO. The remedy changes a shipped workflow contract and is the maintainer's decision. | C:Medium; U:High; S:Low; F:Medium-High; Overall:High | OPEN | Raised OQ-03 (`Blocking: yes`, `Owner: maintainer`, `Finding: PR-002`) with three options. E-04 item 5 requires the docs to state applicability per the answer. |
| PR-003 | LOW | IN-SCOPE | Evidence / Re-derivation | F-01 grep output at review | E-01(a)/V-01(a) demanded that the grep match "only" two files, which is false at HEAD. Several bars were counts (6 tests, `80 passed`, `+6 passed`). | all Low | FIXED | E-01 now proves the property and re-derives the grep. Counts were replaced by behaviors. |
| PR-004 | MEDIUM | IN-SCOPE | B. Security / A. Correctness (fail-open) | plan E-02 item 3 (former `last_verification` fallback) | `authorize_release` could approve a release with no Section 9 report by falling back to Section 8's verification, which is unsigned by design. With `readiness_report=None` and no prior verification, it enforced nothing, so the readiness gate failed OPEN. | all Low | FIXED | `readiness_report` is now required. `None` raises `ReleaseAuthorityError` and there is no fallback. The E-03(6) test and V-02 cover this. |
| PR-005 | LOW | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate had no scope-fence declaration and no release-gate or backlog-close note, and it said "six" Scope-Paths. | all Low | FIXED | Added the scope fence (no STOP clause), the release-gate note, the OQ-03 dependency, and a generic path count. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the gate classes be defined without `GATE_ORDER`? | A literal hard set; unclassified failures treated as hard. | Adding `GATE_ORDER` to `release_readiness.py` (out of scope, owned by `w9l8ph`); deriving from `build_report` at import (needs a tree). | `release_readiness.build_report` body; the plan's own scope fence | yes |
| D-2 | Should `authorize_release` fall back to Section 8's verification? | No; it fails closed. | Keeping the fallback. | Section 8 is run unsigned by design (plan OQ-02.1), so it cannot satisfy Section 9 | yes |
| D-3 | Who decides where readiness applies (OQ-03)? | The maintainer, escalated as blocking. | The reviewer choosing option (a). | The shipped workflow contract for every managed repo; AGENTS.md "public contracts"; escalated as plan OQ-03 `Blocking: yes` (`Finding: PR-002`) | no |
