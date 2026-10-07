# Review findings: plan l4vw9o

- Subject-Id: l4vw9o
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261007T165339Z-456282` at HEAD `0fffb48f8`. The plan was committed and byte-identical to the sealed lane input rev-2 (sha256 `e1d439bc...7fecb`), so no snapshot was needed. `- Kind: orchestrator`. `aw ipd lint --phase author` was conforming. A prior review round exists (2026-09-30, `.aw/records/reviews/20260930-denypush-00-...review.md`); this is a re-review after two coverage round trips.

Re-measured at this HEAD:
- `x2dwu5` is in `executed/`, `Status: executed`, with V-items `Result: pass`.
- Spec `25kzda`: `grep -c "deny push-capable"` = 2 (5.2 bullet at the requirement list; 6.1 limit 4 "No-push and hook guarantees require control of execution"). 5.2 carries the `x2dwu5` "MEASURED FEASIBILITY AND BOUNDS" paragraph, which calls the credential half "strictly bounded rather than complete" (environment-carried tokens not withheld; hardened mode opt-in and Linux-only).
- `host_sandbox_profile.ACTION_CLASSES == (ACTION_READ_ONLY,)`. `len(run_evidence.RUN_FINDING_CODES) == 12`, no PUSH code. `supports_deny_push`, `CAP_DENY_PUSH` and `supports_deny_tcp_port` are absent from `agent_workflows/`. `DenyPushRemovedTests` is present.
- Backlog: `sv9ce4` is `open`. `wcbpqf` is `graduated` (graduated by `d5ntkj`, which is in `not-executed/` after REJECT - NEEDS REPLAN). `oq05nc` is `open` (reopened 2026-10-06 by the coverage return).
- `aw host capabilities opencode`: 0 refused, no deny row.
- `pi3bk8` OQ-01 is `resolved` (keep `supports_deny_tcp_port`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability / evidence | child table row 01 path `.aw/records/plans/pending/20260929-denypush-01-x2dwu5-...`; actual `.aw/records/plans/executed/...` | Child 01's path in the table was stale: `x2dwu5` has executed and moved. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row path points at `executed/`. |
| PR-002 | MEDIUM | IN-SCOPE | Honest documentation | Completion criterion 2 and child row 01: "the credential half of its bullet is already shipped in hardened mode"; spec 5.2 "protection is strictly bounded rather than complete" | The orchestrator overclaimed the credential half, contradicting the shipped spec amendment. That is the very overclaim this Set audits for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites now say BOUNDED, naming the env-credential and opt-in limits. |
| PR-003 | MEDIUM | IN-SCOPE | G ownership / coverage | Completion criteria all read "[Owner: x2dwu5, pi3bk8 and wzhe4n, each in its own V-items; wzhe4n last]" | A blanket owner on every criterion named no performing item, so a criterion such as `ACTION_CLASSES` had no specific checker. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each criterion names its owning child E/V items (wzhe4n E-01..E-04 sub-checks, pi3bk8 E-02/E-03/E-07, x2dwu5). |
| PR-004 | MEDIUM | IN-SCOPE | E evidence feasibility | V-03 "measured at review, `oq05nc` is ALREADY `graduated`"; gate "`wcbpqf` (verified `open`)" | Both status claims are false today (`oq05nc` open, `wcbpqf` graduated by a rejected plan). The V-03 guidance rested on a stale premise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now says not to use `oq05nc` status as evidence and to state `wcbpqf`'s status. The gate records the `d5ntkj` rejection and how to reopen. |
| PR-005 | LOW | IN-SCOPE | Consistency | Cross-IPD "Order 02's OQ-01 leaves the exact spelling open"; `pi3bk8` OQ-01 `Status: resolved` | The name question was resolved at review, so the claim was stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded to RESOLVED, with `wcbpqf` still available. |
| PR-006 | LOW | UNDER-SCOPE | G execution contract | gate "Move each child to `.aw/records/plans/executed/`" | The gate had no scope fence or conditional runner/executor finalize ownership, and its wording invites a hand move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full execution contract added: scope fence, honesty rule, commit/never-push, conditional finalize, no hand `git mv`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `wcbpqf` be reopened from `graduated` as part of this review? | No; record the drift in the plan and leave the backlog transition to the maintainer | Reopen via `aw backlog set` (outside the review's plans-only remit) | plan-review "Review plans only"; `d5ntkj` workflow history "rejected at review" | yes |
