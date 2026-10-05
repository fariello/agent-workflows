# Review findings: plan hm1h3l

- Subject-Id: hm1h3l
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (HIGH, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `5fe170aa6`. The plan
was committed and byte-identical to the sealed lane input (rev-2), so no pre-review snapshot was needed. First
`- Kind:` bullet is `child`, so `IPD-S407` does not apply. `aw ipd lint --phase author --agent` was clean before
review; after revision `review-finalize` reports only `IPD-Q501`, the intended effect of blocking OQ-03.

Re-measured against the five specs: every anchor A.1, A.3, A.6 ("after 2.5c"), A.8, A.9 (4.4, 4.8 `SPEC-PLAN-CONFORMANCE`,
4.9 `BACKLOG-GRADUATE-IPD`, both COUNT rows), 5.5's retry lists, B.1 ("THEREFORE: before a run spends"), B.2 (point 3),
C.1 ("THE PROBE answers"), C.2 ("That residue is the semantic probe"), C.3 (limit 5 "nothing detects the omission"),
and E.1 ("The only legal backward lifecycle transitions are") resolves. All five files exist with the stated statuses.
`2vev8j` 4.8 point 3 does name the IPD spec as the enumeration home. `ORCH_REASON_FINALIZE_REFUSED = "finalize-refused"`
exists. `action_for('orchestrator','to-review') == 'review'` and `'approved' -> 'orchestrate'` confirmed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Evidence / anchor | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md:468` `## 10. Deterministic linter contract`, `:470` "MUST make no model calls", item 18 at `:491`; `:422` `## 9. Lint checkpoints and lifecycle state` | D.1, E-04, Concern, F-07 and D.3 place the MUST-check list and the no-model-calls sentence in Section 9; both are in Section 10. An executor following "add item 19 to Section 9's MUST-check list" finds no such list. qs00nc repeats the wrong citation three times. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All hm1h3l mentions now cite Section 10 "Deterministic linter contract" with the list's opening quote; qs00nc's three citations corrected with a re-scope history line. |
| PR-002 | HIGH | IN-SCOPE | A/C contract consistency | hm1h3l A.6 "every consumer except the two that may ASK"; A.2 retirement re-check; `5etev3` E-02 `review_readiness(..., ask=True)` in `dispatch_orchestrator_item`; `nnsa2o` E-03 `ask=True` after review | 2.5d said only production and `aw ipd coverage` may ask, yet A.2 (retirement) and the children 5etev3 and nnsa2o ask too; a literal implementer would make 5etev3 and nnsa2o violate the spec. UNAVAILABILITY also did not cover retirement or post-review, while 5etev3 refuses on could-not-ask. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | 2.5d now names four asking consumers (production, post-review, retirement, `aw ipd coverage`) and states `aw ipd set`/lint/check never ask; UNAVAILABILITY covers all four, with a refused retirement leaving the plan in `pending/` without failing the run; A.2 states the miss and could-not-ask behavior. |
| PR-003 | HIGH | IN-SCOPE | C (sequencing / deadlock) | hm1h3l A.7 new 3.2 row "Yellow skip ... do not review it"; no child implements a pre-review skip (grep of Orders 02-13 for a review skip: none); `nnsa2o` E-03 reviews then checks | A.7 required a runner to SKIP review of any orchestrator failing 2.5d. With condition 4 unmet on every un-probed orchestrator (Order 02 invalidates all old verdicts), every orchestrator would be skipped forever, and the review path nnsa2o builds would be contradicted by the spec. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A.7's row now specifies review-then-check (`IPD-REVIEW-ORCHESTRATOR-READY`, demote to `to-review`, bounded correction), which is what nnsa2o implements. |
| PR-004 | MEDIUM | IN-SCOPE | A (claim accuracy) | hm1h3l E.1 "A demotion can never start a loop, because promotion and demotion of an orchestrator are decided by the same check" | E.1 makes backward moves legal for ALL plans but argues loop-freedom only for orchestrators, so the general claim is unsupported. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Claim scoped to AUTOMATED demotion: orchestrators by the shared check, and no tool demotes other plans automatically; E.2 history text updated. |
| PR-005 | LOW | IN-SCOPE | Wording | hm1h3l A.6 "names both legitimate remedies" followed by three | Count mismatch in the remedy sentence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | "names the legitimate remedies". |
| PR-006 | HIGH | IN-SCOPE | C/E feasibility | `agent_workflows/runner_shared.py:18391` `probe_verdict_store_path` (gitignored `/state/`); `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30`; hm1h3l D.1 "An absent or stale verdict is a finding"; qs00nc E-04 `error`; `.github/workflows/tests.yml` "aw check plans ... fail closed" | The contract this plan writes makes a machine-local, expiring verdict a hard requirement for model-free gates, so CI and every other clone fail permanently on every orchestrator at `to-review` or later. Same root cause as `1f4faf` PR-006; owned here because this plan writes the text. | C:Medium-High; U:High; S:Low; F:High; Overall:High | FIXED | RESOLVED 2026-10-04 by maintainer ruling, recorded in the plan's OQ-03 (now `Blocking: no`, `Status: resolved`): the coverage answer is STORED IN THE PLAN (new `25kzda` 2.5e: `Coverage`, `Coverage-Fingerprint`, `Coverage-Checked`, `## Coverage findings`), written only by the tool with a matching history line and refused otherwise by new lint rule `IPD-M112`, excluded from the execution-receipt fingerprint, retiring the gitignored 30-day cache. Every clone and CI read the same record, so an absent or out-of-date record is an error in `aw ipd lint` and `aw check` without CI or freeze-gate breakage. Applied in hm1h3l (A.2, A.3, A.6, 2.5e, B.2, D.1, rule 20), 8mabmu (E-03, E-06, E-07) and qs00nc (E-01, E-04, E-06). Previously: Escalated as hm1h3l OQ-03 (`Blocking: yes`, `Finding: PR-006`), cross-referenced to `1f4faf` OQ-03. |
| PR-007 | LOW | IN-SCOPE | E evidence / anchor | hm1h3l Required tests grep "`whose action in this run is \`orchestrate\``" vs A.1 text "WHOSE ACTION IN THIS RUN IS"; A.5 anchor "In an interactive terminal" occurs 3 times in `25kzda` (`grep -c` = 3) | The required grep cannot match A.1's capitalized text case-sensitively; A.5's anchor is ambiguous. Gate also lacked the paste-actual-output rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Grep marked case-insensitive; A.5 anchor quotes the `run uncovered` bullet; gate gains the honesty rule. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Widen 2.5d's asking consumers to match the children, or narrow the children? | Widen the spec to four asking consumers | make 5etev3/nnsa2o model-free (retirement would then refuse every un-probed orchestrator) | `5etev3` E-02 and `nnsa2o` E-03 both pass `ask=True`; a cached pass spends nothing (`read_probe_verdict`) | yes |
| D-2 | Replace A.7's pre-review skip with review-then-check, or add a child to implement the skip? | Review-then-check | implement the skip (deadlocks every orchestrator lacking a verdict) | `nnsa2o` E-03; `25kzda` 3.2 `to-review` row "Run plan review" | yes |
