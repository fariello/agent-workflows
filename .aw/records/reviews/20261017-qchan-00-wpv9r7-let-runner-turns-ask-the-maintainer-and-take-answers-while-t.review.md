# Review findings: plan wpv9r7

- Subject-Id: wpv9r7
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d2ec81544`. The plan was committed (`1149a64db`) and byte-identical to the lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` reported `clean`; `aw ipd coverage wpv9r7` reported ready. The plan is an orchestrator (first `- Kind:` bullet).

Verified:
- All 11 child files exist in `pending/` with matching `- Id:`, `- Order:`, `- Set: qchan`, `- From-Spec: 6kwd2e`, `- Status: to-review`; each child's `- Item-Dependencies:` matches the table's "Depends on" column and the E-item `Depends on` edges.
- Spec `6kwd2e` is `approved` (`.aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md`) and defines R1-R10 and A1-A55 (with A10a-A10h); every A-criterion appears in the child the plan's Cross-IPD map names, except as noted in PR-001 and PR-002.
- Cited research `xjsc9k`, `kdg4uz`, `cpcn9k`, `49sv63`, `js5p5k` exist under `.aw/records/research/`; deferred carrier `szjsgj` exists under `.aw/records/backlog/parked/`.
- `aw find plans 0jooqz` returns a `pending/` path today, so the V-items' demanded observation is reachable once children execute.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Cross-IPD validation (acceptance mapping) | spec `6kwd2e` A30 "A worker emitting an `AW_MISSING_INPUT` token is handled by the missing-input path and is NOT treated as a question"; child `0jooqz` E-05 lists A10a/A10b/A31 and no A30 | The orchestrator maps A29-A31 to `0jooqz`, but no `0jooqz` E- or V-item asserts A30, so the carrier-separation criterion had no test. | all Low | FIXED | `0jooqz` E-05 now requires both directions of the A30 separation (citing `lane_containment.format_missing_input_token`); its V-05 demands `-v` lines for those cases; the orchestrator map names E-05. |
| PR-002 | LOW | IN-SCOPE | Traceability | child `mtmqlm` E-04 "Add `tests/test_question_inbox.py`: schema round-trip" (no A-id) | The map assigns A11 and A42 to `mtmqlm`, whose tests covered them in substance but cited no criterion id, so the trace was not checkable. | all Low | FIXED | `mtmqlm` E-04 now names `6kwd2e` A11 and A42; orchestrator map points at it. |
| PR-003 | LOW | IN-SCOPE | Cross-IPD validation (accuracy) | plan "the final child `mrlblc` runs the full routine gate after the last merge" | Not guaranteed: `mrlblc` is deepest (depth 7) but shallower children (05, 06, 08) may merge later under parallel lanes. | all Low | FIXED | Rewritten to state the ordering truthfully and that post-merge revalidation is the runner's merge-and-revalidate gate, not parent work. A first rewording that put a hand-run gate on the parent was refused by `aw ipd coverage` (attempt 1: "uncovered obligation: a hand executor runs the routine gate once more ..."); attempt 2 removed that obligation and coverage passed. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean` for `wpv9r7`, `0jooqz`, `mtmqlm`. `aw ipd coverage wpv9r7`: ready for review.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the A30 test live? | In `0jooqz` E-05, as the orchestrator already maps A29-A31 there. | A new child (REJECTED: one test case, same module and carrier). | spec `6kwd2e` R2.4; plan Cross-IPD map. | yes |
| D-2 | Should the parent carry a final full-suite run? | No; leave post-merge validation to each child and the runner's merge gate. | Parent-level hand gate (REJECTED by the coverage gate as uncovered parent work); a new child (REJECTED: each child already runs the routine gate). | `aw ipd coverage wpv9r7` attempt-1 refusal; AGENTS.md orchestrator rule. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
