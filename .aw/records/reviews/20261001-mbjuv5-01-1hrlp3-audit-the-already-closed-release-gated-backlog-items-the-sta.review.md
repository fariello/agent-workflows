# Review findings: plan 1hrlp3

- Subject-Id: 1hrlp3
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (HIGH, fixed), PR-004 (LOW, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `45529f342`; the plan was committed (`d3273404c`) and the
tree clean, so no snapshot was needed. `aw ipd lint --phase author` and `--phase review-finalize`
both report clean. `- Kind: child`, so `IPD-S407` does not apply.

The plan was authored at HEAD `615e03f68` (2026-10-01 03:17). Two plans touching its core
mechanism were executed later THE SAME DAY and are not ancestors of that HEAD (checked with
`git merge-base --is-ancestor`): `b24o3q` (`d24e81a83`, at-rest whole-tree arm for
`check.blocking-item-closed-without-gate`, cutover `release_gate_at_rest: 2026-10-01`) and `f7igdu`
(`47f7d9727`, persists `- Close-Evidence:` on a SATISFIED close). Re-measured the census at review
HEAD by driving `evaluate_blocking_close` with `carrier_index=_from_backlog_carrier_index(root)`
over `backlog._iter_items` `done/` items: 53 findings, 46 no-carrier / 7 carrier-not-executed,
Work-Kind 47 bug / 3 feature / 2 followup / 1 chore, 0.12 s; `aw check release-gates` still
`errors 0`. So the population and the plan's purpose hold; the explanation and several mechanisms
did not.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | F (honest documentation); evidence | `check_engine.check_release_gate_consistency` comment "Rule 1 at-rest arm (gateatrest b24o3q E-03)"; `.aw/config/project.json` `"release_gate_at_rest": "2026-10-01"` | The plan's Concern, F-02, F-03, Scope, Deferred and Scope check state the rule is staged-scoped in every caller and defer "widening to whole-tree". That shipped since authoring (b24o3q); the 53 are now invisible because of cutover grandfathering. The report would have published a false mechanism, and the deferral row described already-done work. Pending `heh05a` now owns the advisory surface and explicitly cedes adjudication to this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern/Scope/F-02/Deferred/Scope check updated; F-11 added with the current mechanism and re-measured numbers; deferral row repointed to `heh05a`. |
| PR-002 | MEDIUM | IN-SCOPE | C (canonical mechanism) | `check_engine.evaluate_blocking_close` signature `carrier_index: Optional[...] = None`; at-rest arm passes `carrier_index=shared_carrier_idx` | E-03 told the executor to use the index only to classify while the predicate kept walking per item, and E-01 classified via `find_from_backlog_artifacts`; the predicate now takes `carrier_index=` directly, so the plan as written would still pay the per-item walk (re-measured: 2.2 s for 5 items unindexed vs 0.12 s for all 250 indexed). | all Low | FIXED | E-03 now passes `carrier_index=` per call, mirroring the at-rest arm; E-01 reason-class asks the shared index filtered by `_same_release`. |
| PR-003 | HIGH | IN-SCOPE | A (correctness of dating) | plan E-02 three-tag rule; `232wcg` history `- 2026-09-23 set (aw backlog): FIXED by runnerlayer ...`; 6 of 53 carry a `graduated` line | E-02 accepted `graduated` as a close tag, which dates the wrong event for any graduated-then-closed item, and its example implied a `status -> done`-only reading of the flag spelling, which would mis-bucket `232wcg` as undated. The shipped `_item_close_date` dates any newest record, including `created`, so it would silently date `j9v1kn`, the exact guess F-10 forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 matches `done (...)` and `set (aw backlog)` with any message and not `graduated`; requires the report to justify not using `_item_close_date`; V-02 and E-04 gain custom-message and graduated-before-done fixtures. |
| PR-004 | LOW | IN-SCOPE | G (consistency) | Findings table `no-carrier-no-evidence` vs E-01/E-04 class `no-carrier` | Two names for one reason class. | all Low | FIXED | Table uses `no-carrier`. |
| PR-005 | MEDIUM | IN-SCOPE | G (live-artifact criteria) | E-01 Expected outcome; E-06 "3 items"; V-06 "the three rows" | Live corpus counts were used as bars; the execution-time census can differ. The NEEDS-A-LOOK set (`av9hni`, `zv49ne` pre-predicate bare; `j9v1kn` undated) also overlaps GRANDFATHERED with no precedence rule, so "exactly one disposition" was not reproducible. | all Low | FIXED | Counts made context with re-derivation; V-06 demands every NEEDS-LOOK row; precedence rule (bare message wins over grandfathered) added and required in the report. |
| PR-006 | MEDIUM | UNDER-SCOPE | G (execution contract) | gate POST-GATE LIFECYCLE paragraph | Unconditional `aw ipd finalize` instruction, and no explicit paste-actual-output honesty rule. | all Low | FIXED | Conditional runner/hand ownership plus honesty rule added. |
| PR-007 | MEDIUM | UNDER-SCOPE | E (coverage) | `backlog.run_set` writes `set_close_evidence_line` on SATISFIED (f7igdu); predicate reads `_META_CLOSE_EVIDENCE_RE` | F-08 and E-05's first limit claimed `--evidence` is never persisted; it is now, for closes after `47f7d9727`. The limit still holds for all 53, but the report must say so precisely, and the auditor needs a fixture proving a persisted `Close-Evidence` is not reported. | all Low | FIXED | F-12 added; F-08 and E-05 limit reworded; Close-Evidence fixture added to E-04/V-04; the `--evidence` deferral row repointed to `f7igdu`/`byzkr7`. |
| PR-008 | LOW | IN-SCOPE | A (boundary semantics) | `orb9zb` finalize `844533abf` 2026-08-25 23:41 -0400; four of the 53 closed 2026-08-25 | History dates are day-granular, so the on-boundary-day comparison was unstated. | all Low | FIXED | E-02 states on-day = post-predicate and requires the same-day cohort to be named as boundary-ambiguous. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | With the at-rest arm and `heh05a` now existing, is this audit still needed or should it be retired as superseded? | Keep it; update its mechanism. | Retire as superseded by `b24o3q`/`heh05a`. | `heh05a` Scope "EXCLUDES the per-item adjudication ... which is plan `1hrlp3`'s deliverable"; re-measured 53 findings still reported by nothing. | yes |
| D-2 | Should a bare-message pre-predicate item be GRANDFATHERED or NEEDS A MAINTAINER LOOK? | NEEDS A MAINTAINER LOOK. | GRANDFATHERED (date wins). | Plan's own OQ-01 rationale that the report exists to surface rows asserting nothing; backlog `mbjuv5` "per-item decision". | yes |
| D-3 | Should the auditor reuse `check_engine._item_close_date` for dating? | No, unless the executor documents equivalence. | Reuse it for single-authority. | `_item_close_date` returns the newest dated record of any kind (`attention_contract.last_history_at`), dating `j9v1kn` by `created`, contradicting F-10. | yes |
