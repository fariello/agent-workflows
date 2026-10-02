# Review: Stamp the scaffold's draft history record from the UTC clock

- Subject-Id: 9wcei0
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

The target plan was committed and unchanged (`3f84d12b3`), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits. After the edits, `--phase review-finalize` reports exactly one `IPD-Q501` error. That error comes from OQ-03, which this review raised as blocking on purpose.

I re-reproduced F-01 at lane HEAD `e4dba9b13` in a throwaway repo under `tmp/`.

Under `TZ=XXX-20` (local `2026-10-03`, UTC `2026-10-02`), the scaffold wrote `20261003-probeset-01-4z8q50-probe-plan.ipd.md` with `- Date: 2026-10-03`. The history then read `- 2026-10-02 to-review (aw set)` above `- 2026-10-03 draft (probe): created.`, and `aw check plans --agent` returned rc=1.

Under `Pacific/Honolulu` the same sequence returned rc=0.

I also confirmed the `build_skeleton(when=...)` single-value shape, `run_scaffold`'s `date.today()` sites, and that `tzset(` appears nowhere in `tests/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | Plan collision (C/G) | `.aw/records/plans/pending/20261002-lq2w86-01-rfyrvp-...ipd.md` declares `agent_workflows/ipd_authoring.py`, same split, `Blocks-Release: next`, committed `de75a42c1` (00:32) before this plan's `3f84d12b3` (01:03); `5ivkdh` E-05 "pending plans `9wcei0` and `rfyrvp` both own that split" | The plan's central F-02 claim, "THIS SITE IS IN NO OTHER PLAN'S SCOPE", is false. Two review-ready, release-gated plans make the same production edit, so executing both would apply the split twice. | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | Choosing which plan to retire, and which backlog gate (`jvw1kg` or `lq2w86`) inherits the fix, is the maintainer's scope call. Escalated as OQ-03 (`Blocking: yes`, `Finding: PR-001`). F-02 and the Concern are corrected, and a review note was added. |
| PR-002 | MEDIUM | IN-SCOPE | Test validity (E) | F-07 exposure fractions; review probe: `TZ=XXX-24` gives local `2026-10-03` vs UTC `2026-10-02`, and `XXX+23:59` gives local `2026-10-01` | E-04's guard named no zone. A real east zone is in the skew window for only part of each day, so the "RED at base" demand and the guard itself pass by wall-clock luck. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires fixed-offset zones that are always in the window (`XXX-24` east, `XXX+23:59` west). It also requires a loud precondition failure, not a skip, when `local_date != utc_date` does not hold. |
| PR-003 | MEDIUM | IN-SCOPE | Executability (G) | Review probe: `ipd scaffold` refused `--slug` ("unrecognized arguments"), then required `--author`, then `--priority and --work-kind required` | E-01's reproduction command, as written, cannot run. Also, its unconditional STOP would kill the additive guard if `rfyrvp` landed first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now spells out the required flags and passes the plan by `- Id:` with `--no-commit`. It records the review re-measurement. The STOP now applies only when the checker itself moved; if a sibling already landed the split, E-02/E-03 are marked `blocked` and E-04 still runs. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract (G) | Gate item 9 instructs `aw ipd finalize` unconditionally; there is no scope fence | The finalize instruction ignored runner ownership, and the gate declared no scope fence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE item and conditional runner/executor finalize ownership. Gate item 1 now names the blocking OQ-03. |
| PR-005 | LOW | IN-SCOPE | OQ owner | OQ-01/OQ-02 `Owner: none` | Both resolved questions had no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which zones should the guard use? | Fixed POSIX offsets `XXX-24` / `XXX+23:59` with a loud precondition | Real zones (time-of-day dependent); mocking `date.today` (pins structure, P16) | Review probe output; F-07 | yes |
| D-2 | Should the review resolve the `9wcei0`/`rfyrvp` collision itself? | No; escalate it as blocking OQ-03 with a recommendation | Retire `rfyrvp` from this review (it is not in this review's ledger, and retiring it is a scope decision) | AGENTS.md "asking the human ... when the decision is theirs (scope ...)"; plan-review Step 4 escalation rule | yes |
