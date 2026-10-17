# Review findings: plan kn7xtw

- Subject-Id: kn7xtw
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `dbff2d34f`. The plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`. `aw ipd coverage kn7xtw`: ready for review. Orchestrator (Set `trimgap`, Order 0).

Verified in the lane:
- `runner_shared.read_set_membership(repo, "trimgap")` returns orchestrator `kn7xtw` and 21 children (Orders 02, 04 to 23), all `reviewed`. `runner_shared.evaluate_set_retirement` gates on every one of the 21 (reason `unfinished-children`, listing all 21).
- The child table listed only the 8 `q86fxm` children (Orders 16 to 23). Orders 02, 04 to 15 (13 plans, each `From-Backlog` a distinct `trimgap` backlog item) had no row, no E-item and no V-item.
- All 21 children declare `- Item-Dependencies: none`; `uniq -d` over every child's Scope-Paths is empty (no shared file).
- The V-item numbers cited in `## Cross-IPD validation` match each child's checklist (ivap17 V-06, vqr3xq V-05, zhoul7 V-06, 78g6ic V-02, 5e7czd V-03, y4bt1c V-05, 9gjvrq V-06, ya63p5 V-01/V-02).
- Bare core tier at HEAD `5c427b50c`: `753 passed in 22.97s`, within budget, which contradicts the Deferred entry's standing "already over budget" claim.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Orchestration completeness | `runner_shared.read_set_membership`; `runner_shared.evaluate_set_retirement` (`EVERY child's on-disk Status: is TERMINAL`); `## Child IPDs` table (8 rows) | Set `trimgap` has 21 children on disk, but the orchestrator tracked 8. When a human tells an agent to "execute trimgap" by hand, the agent follows the checklist and would skip 13 plans. The runner would also refuse to retire the plan until all 21 finish, which contradicts the plan's own Scope ("confirm each of the eight"). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added 13 table rows, E-09 to E-21 and V-09 to V-21. Updated Concern, Scope, Goal, Completion criteria (each per-item child meets its own Goal), Cross-IPD validation, Scope check and gate. `Highest E allocated: 21`. Size set to `exception` with a cohesion rationale (`IPD-Z601`). Coverage re-run: ready. |
| PR-002 | LOW | IN-SCOPE | Evidence | `## Deferred / out of scope`; review bare run `753 passed in 22.97s` | The plan stated the core-tier budget overrun as a standing fact, but it depends on machine load. | all Low | FIXED | Rewritten to record both measurements. Carrier `o58dro` kept. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract / precision | OQ-01 `Owner: none`; gate | The resolved question had no owner, and the gate did not state the open-question status. | all Low | FIXED | Owner set to plan author. Gate now says OQ-01 is resolved and none block. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings. `aw ipd coverage kn7xtw`: ready for review.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Track the 13 per-item children in this orchestrator, or give them a separate Set? | Track them here | Re-set the 13 children into a new Set with its own orchestrator (would touch 13 reviewed plans outside this review's scope) | `runner_shared.read_set_membership` reads membership from disk by `- Set:`, so they ARE this plan's children today | yes |
