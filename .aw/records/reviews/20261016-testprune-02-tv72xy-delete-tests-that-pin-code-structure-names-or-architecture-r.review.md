# Review findings: plan tv72xy

- Subject-Id: tv72xy
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b98923bb5`. Plan committed (last touched by `b50bcb58d`, which
recorded the maintainer's OQ-01 ruling) and byte-identical to the lane input, so no pre-review snapshot.
`aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Verified anchors: every test named in E-02..E-09 resolves by `def` name (12 sampled, all 1 hit; 5
`if hasattr(il, "_plan_status_event_groups")` guards in `tests/test_history_order.py`).
`agent_workflows/egress_policy.py` `EgressPolicy.__init__(self, destinations=())`: `EgressPolicy(allow_all=True)` and
`EgressPolicy(negation=True)` both raise `TypeError` today (probe), so the E-07 conversion is satisfiable.
`tests/test_egress_policy.py::test_policy_has_no_allow_all_or_negation_switch` currently asserts three
`not hasattr` lines plus a wildcard `ValueError`. `tests/test_worktree_lease_stdlib_only.py` asserts no
first-party module loads on import (docstring "imports no first-party `agent_workflows` modules"), cited at
`agent_workflows/worktree_lease.py:412,705,733`. Test-name citations outside tests: only `test_set_level_checks`,
from done backlog `2n9y3f`. No reviewed/approved external-target behavioral test of `edge_satisfied` found by
grep; E-04 already requires adding one if none exists.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Project rule (recorded maintainer decision) | OQ-01 "RESOLVED by the maintainer 2026-10-16 ... DELETE them"; E-07 (pre-review) "KEEP ... stdlib-only import tests ... ONLY if the maintainer confirms OQ-01"; OQ-01 tail "Default if unanswered by execution: KEEP" | After the ruling was recorded, E-07 still listed the three stdlib-only tests under KEEP and OQ-01 still carried the pre-ruling KEEP default, so an executor following E-07 would contradict the maintainer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 moves them to DELETE (convert only on a cited packaging promise); OQ-01's stale default marked superseded; E-07 expected outcome and V-07 demand their absence. |
| PR-002 | MEDIUM | IN-SCOPE | D (keep reason consistent with ruling) | `tests/test_worktree_lease_stdlib_only.py` docstring; E-07 KEEP | The kept `worktree_lease` test is named "stdlib_only", so a reader applying the ruling would delete it; its real reason (first-party import cost and cycle, measured) was not distinguished. | all Low | FIXED | E-07 records the keep reason in first-party/cycle terms and forbids renaming (three source citations). |
| PR-003 | MEDIUM | IN-SCOPE | G (consistency) | OQ-02 "E-07 deletes it unless E-01 finds a ... citation"; E-07 (pre-review) "keep ... only if OQ-02 resolves to keep" | E-07 still treated the resolved OQ-02 as pending. | all Low | FIXED | E-07 states delete-unless-cited, matching OQ-02. |
| PR-004 | MEDIUM | IN-SCOPE | E (verifiable bar) | E-08 "research table count equals `git diff --stat` test removals" | `--stat` counts lines, not tests or assertions, so the bar is unsatisfiable as written. | all Low | FIXED | Bar re-derived from `git diff <base>..HEAD -- tests/` counting removed `def test_` and removed assertions. |
| PR-005 | LOW | IN-SCOPE | D (coverage-loss remedy) | E-08 "justified ... or the deletion is reverted" | Revert was the only alternative to justification, skipping the better remedy of adding the missing behavioral assertion; test-function citations were not checked before deletion. | all Low | FIXED | E-08 adds "covered by a new behavioral assertion" and a citation grep over code, specs, and backlog. |
| PR-006 | LOW | IN-SCOPE | G (V evidence) | V-07, V-08 (pre-review) | V-07 did not demand the stdlib tests' absence or the egress test's `hasattr` removal; V-08 named a bare `aw check` without the machine form. | all Low | FIXED | Both strengthened. |
| PR-007 | LOW | IN-SCOPE | G (execution contract) | plan gate (pre-review) | Gate lacked scope-fence wording, the paste-actual-output MUST, and conditional finalize ownership. | all Low | FIXED | Gate rewritten; `worktree_lease.py` declared only for a citing-comment follow, with `--scope-ack` otherwise. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep `test_worktree_lease_stdlib_only.py` despite the ruling? | Keep, on first-party import cost and cycle grounds. | Delete as stdlib-only (REJECTED: the test asserts no FIRST-PARTY loads, a measured defect, not third-party avoidance). | test docstring; `worktree_lease.py:412,705,733`. | yes |
| D-2 | What counts as a packaging promise that saves a stdlib-only test? | A cited spec, decision, or install path running the module before deps are installed; a docstring adjective does not qualify. | Treat `ipd_lint`'s "stdlib-only" header as a promise (REJECTED: maintainer ruling; D138). | OQ-01 ruling; `DECISIONS.md` D138. | yes |

No decision is `Reversible: no` (a deleted test is restorable from git, and `vgus66` mutation-checks deletions). No finding was left `OPEN` or `DEFERRED`.
