# Review findings: plan tiwj2o

- Subject-Id: tiwj2o
- Subject-Type: ipd
- Reviewed-At: 2026-10-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fca4b91bd` in a runner lane worktree (non-interactive; questions go to the outcome
file). The lane-input copy is byte-identical to the tracked plan, which was committed and unmodified
(`f10f8f3cd`), so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author`
conformed; `aw ipd coverage tiwj2o` reported "Orchestrator tiwj2o is ready for review." before and
after revisions (it refreshed `- Coverage-Fingerprint:` after the edits); `--phase review-finalize`
conforms after revisions. No `IPD-S407` violation, so no repair loop ran.

Verified: all five children exist in `plans/pending/` with `- Set: revsteps`, `- Kind: child`, the
Orders and `- Item-Dependencies:` the table states (01, 02 none; 04 `executed:3bwrfx, executed:gv3smb`;
05 `executed:uiyoax`; 09 `executed:uiyoax, executed:is2xiv` and `- Attended: required`). Spec `k3yx72`
is `approved` (`.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`),
MD-20 and Section 15 match the Stage 1 / Stage 2 split exactly, and Section 15's Order 09 prerequisite
backlog `i2i81x` is `done`. `runner_shared.find_unauthored_child_rows` exists (cited by OQ-01). Cross-IPD
anchors resolve: `uiyoax` V-02 lists `steps/`; `uiyoax` E-06 item 6 is the S6 delegation point that
`is2xiv` E-05 wires into; `kk62qt` E-04 builds every cell from one pilot commit; `kk62qt` E-09 files the
Stage 2 backlog item. Every child's E/V items name its own test modules.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | medium | IN-SCOPE | G executability | `agent_workflows/runner_shared.py:23636` `hold_attended_plan`; plan child-table note "so the runner holds it for an interactive session" | The note implied any run handles Order 09. In fact only a terminal run opens an interactive session; an `--unattended` run freezes it `not-run`, so the orchestrator cannot retire unattended. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Note rewritten to state both routes, cite `hold_attended_plan`, and state the retirement consequence. |
| PR-002 | medium | UNDER-SCOPE | G execution contract | plan `## Approval and execution gate`; precedent `.aw/records/plans/executed/20261017-qchan-00-wpv9r7-*.ipd.md` gate | Gate lacked the resolved-open-questions statement, the paste-actual-output rule, the scope statement and the hand-execution path (table order, `aw ipd lint --phase pre-transition`, `aw ipd finalize` conditional on no runner). | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate now carries the full execution contract, runner/executor ownership conditional. |
| PR-003 | low | UNDER-SCOPE | traceability | spec `k3yx72` AC-09 (`- AC-09: A review ending \`no-go\` leaves the plan at \`reviewed\``); `uiyoax` E-09/V-09 | AC-09 is a Stage 1 behaviour but no completion criterion named an owner for it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Completion criterion for `uiyoax` now owns AC-09 first half (E-09/V-09 `completed-negative`) and cites existing `run_selection_policy.runner_action` refinement (ii) for the second half (D-1). |
| PR-004 | low | UNDER-SCOPE | spec sync | spec `k3yx72` AC-10..AC-13, AC-15; Section 15 Stage 2 rows | The plan did not say that Stage 2 ACs are undemonstrated by this Set, so a reader could expect the Set to bring the spec to `implemented`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Deferred section now lists the Stage 2-owned ACs and states the spec cannot reach `implemented` from Stage 1. |
| PR-005 | medium | UNDER-SCOPE | durable carrier | `aw commit` refusal `check.ipd-uncarried-obligation: ... deferred row 1, deferred row 2, deferred row 3 records an outstanding obligation with NO durable carrier` | All three Deferred rows were prose only; once this plan is `executed` they would vanish from `aw attention`. Post-cutover plan, so the rule is an error. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Rows 1 and 2 carry `- Carrier: kk62qt` (its E-09 files the Stage 2 backlog item and handles the sized-run offer); row 3 carries `- Carrier-Declined:` because it is a dependency note owned by spec `4iyd78`, not an obligation of this Set (D-2). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a child add a test that a `reviewed` + `no-go` plan is not re-dispatched for review (AC-09 second half)? | No; it is existing runner behaviour that steps mode does not touch, recorded as such in the completion criteria. | Add a case to `uiyoax` E-15. Rejected: it would test unchanged selection code, and `uiyoax` scope does not touch `run_selection_policy`. | `agent_workflows/run_selection_policy.py:425` "Refinement (ii): IPD reviewed -> execute" | yes |
| D-2 | Which carrier holds the deferred rows? | `kk62qt` for Stage 2 and the sized run; declined for the `4iyd78` note. | A new backlog item now. Rejected: spec MD-20 makes Stage 2 conditional on the pilot, and `kk62qt` E-09 already files the item when the gate says build. | spec `k3yx72` MD-20; `kk62qt` E-09; spec `4iyd78` workflow-history note 2026-10-24 ("Part 2 ... depends on k3yx72 Order 09") | yes |
