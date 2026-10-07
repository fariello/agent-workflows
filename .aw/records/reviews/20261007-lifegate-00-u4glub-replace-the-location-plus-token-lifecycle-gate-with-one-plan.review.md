# Review findings: plan u4glub

- Subject-Id: u4glub
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `c088e4915`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. `aw ipd coverage u4glub`: ready
(cached) before revision. After revision `--phase review-finalize` reported `IPD-S408 coverage-record-stale`
(expected after editing); re-running `aw ipd coverage u4glub --no-commit` (attempt 1 of 2) returned
`ready: true, findings: []`, then `review-finalize` was `clean`. Child table rows: 3 -> 3.

Verified at review: children `urv602` (`reviewed`, `go-pending-approval`), `e25iy9` (`to-review`, depends
`executed:urv602`), `m47znv` (`to-review`, depends `executed:e25iy9`) all pending with `From-Backlog: dvonrn`
and `Blocks-Release: next`; `m47znv` E-05/V-05 owns the four cross-IPD checks; `ipd_lifecycle.lane_worktree_active`,
`verify_driver_attestation`, `DRIVER_ATTEST_ENV = "AW_DRIVER_ATTEST"` and `runner_shared.get_run_attestation`
exist; two `if lane_worktree_active(repo_root):` blocks sit in `retire_orchestrator` and `finalize`;
`ipd_lifecycle.begin` has no role check, only `run_begin`/`run_finalize` call `_refuse_worker_role_verb` (F-5);
`run_lock` writes `pid=... started=...` only (F-3); both hosts set `child_env[_gch.RUN_ID_ENV]` (F-6);
spec `7ckptx` still in `approved/`, `llbr2b` still `to-review` (D8's in-place condition holds); `malgate`
children all executed, orchestrator `qtz0us` pending, `ariaau` open.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G (ownership contradiction) | Cross-IPD validation lead "cannot be performed by any child alone, which is why they live here"; V-03 "performed here and nowhere else"; each bullet tagged "[Owner: m47znv E-05]"; `m47znv` E-05 | The lead sentence and V-03 said the cross-checks belong to this plan. The owner tags and `m47znv` E-05 put them on the child. The runner skips orchestrator E/V on retirement, so the wording invited parent-only work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Lead sentence and V-03 now say `m47znv` E-05/V-05 performs them and V-03 quotes that evidence. |
| PR-002 | MEDIUM | IN-SCOPE | Project rule (`check.plan-spec-link-missing`) | `aw check` output: "20260930-lifegate-00-u4glub ... Fix: link it (aw ipd set u4glub --from-spec 7ckptx), write '- From-Spec: none'" | The orchestrator cites specs it does not derive from or edit, so `aw check` flagged it. | Overall:Low | FIXED | Added `- From-Spec: none`. The Set comes from backlog `dvonrn`, and only `e25iy9` edits specs. |
| PR-003 | LOW | IN-SCOPE | G (open questions) | OQ-01 and OQ-02 `Status: open` with full rationales; `dvonrn` D1 "NUDGE, never a refusal ... print one line"; `malgate` children in `plans/executed/` | Both questions are answered by repository evidence, so leaving them open was inaccurate. | Overall:Low | FIXED | Both are resolved and cite D1 and the malgate execution state. |
| PR-004 | LOW | IN-SCOPE | G (stale facts) | Deferred: "`ariaau`, now graduated"; Spec sync: "Pending plans `e9ekuj` and `uuh71v`" | `ariaau` is `open`, not graduated. `e9ekuj` is executed (`208bdd58b`). | Overall:Low | FIXED | Both statements now match the tree. |
| PR-005 | LOW | UNDER-SCOPE | G (execution contract) | Approval and execution gate | No paste-actual-output rule, no scope-fence declaration, and no by-hand retirement step for the orchestrator itself. | Overall:Low | FIXED | Added all three. The by-hand path uses `aw ipd finalize u4glub ... --apply` unless a runner already retired the plan. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep or drop Order 03 (nudge)? | Keep. | Drop as polish. REJECTED: maintainer's settled D1 mandates the nudge. | backlog `dvonrn` D1 (DECIDED 2026-09-26). | yes |
| D-2 | Wait for `malgate`? | No. | Add a dependency. REJECTED: malgate's overlapping child `dmjp0u` already executed; priority inverts. | `plans/executed/*malgate-0[123]*`. | yes |
| D-3 | Link `From-Spec` to `7ckptx` or write `none`? | `none`. | Link `7ckptx`. REJECTED: the Set graduates from backlog `dvonrn`, not a spec; `7ckptx` is amended by child `e25iy9`, which declares it. | `- From-Backlog: dvonrn`; `e25iy9` Scope-Paths. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`. `aw check` could not be re-run to completion after revision (timed out at 300s in this lane), so clearance of `check.plan-spec-link-missing` is asserted from the rule's own remedy text, not re-observed.
