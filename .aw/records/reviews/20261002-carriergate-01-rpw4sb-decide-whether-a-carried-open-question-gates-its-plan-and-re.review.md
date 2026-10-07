# Review findings: plan rpw4sb

- Subject-Id: rpw4sb
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `3d84ef876`. The plan was
committed and byte-identical to the sealed lane input (rev-7), so no snapshot was needed. `- Kind: child`, so
`IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author --agent` was clean before review.

Re-measured: `check_engine.rule_spec("check.ipd-carrier-ungated")` returns the `error` default and the id is not in
`RULE_REGISTRY` (F-11). Every cited symbol resolves (`evaluate_durable_carrier`, `check_durable_carrier` wired in
`check_content` inside `try/except`, `_CARRIER_LEGACY_SEVERITY`, `_CARRIER_LIVE_OQ_STATUSES`, `parse_item_dependencies`,
`parse_carrier_ids`, `_ITEM_DEP_STATE_STATUSES`, `edge_satisfied` with its "needs exactly" refusal). F-09 reproduces:
`dependency_target_id6(<parsed ItemDependency>)` returns `None`, and the call site reads
`target = dependency_target_id6(edge) or dep`. F-10 reproduces: `grep -c "Durable carrier"` is 0 in the template and
1 in the records README, and `engine.ensure_plans_readmes` pairs the two. `bs850k` exists (`open`,
`Blocks-Release: next`) and `hc6n7r` exists. `ipd_lint.parse` on this plan yields `Item-Dependencies: none` and
OQ-01 `open`, `Carrier=hc6n7r` (F-14). The existing template test in `tests/test_ipd_lint.py` asserts only tokens
that E-04's additive port keeps.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability / consistency | plan gate "file the F-09 defect as a backlog item before closing"; `## Spec / documentation sync` "NO FILING OBLIGATION IS LEFT TO THE EXECUTOR ... filed ... as backlog item `bs850k`"; `.aw/records/backlog/open/20261002-carriergate-01-bs850k-*.backlog.md` exists | The gate ordered the executor to file a defect that authoring had already filed, inviting a duplicate carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now says not to re-file and names `bs850k`. |
| PR-002 | MEDIUM | UNDER-SCOPE | E testing / reachability | E-05 case (e) "on a temp repo whose ONLY finding would be this rule, `aw check plans` exits 0"; `check_engine.evaluate_carrier_obligation` HANDOFF requires the carrier to resolve to a live record, `check.ipd-uncarried-obligation` registered `error` | If the fixture's `- Carrier:` resolves to nothing, or to a `done` item, the uncarried or discharged-carrier rule fires at `error` and case (e) fails for an unrelated reason. The plan did not say the carrier must exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires a live backlog carrier fixture and a pre-assertion that no other failing rule is present; V-05 demands that diagnostics list. |
| PR-003 | MEDIUM | IN-SCOPE | G execution contract | gate "move this plan to `.aw/records/plans/executed/` only through the tooled terminal transition" | The gate gave no conditional runner/executor ownership of finalize, and no scope-reconciliation wording. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added runner-owned finalize under `aw oc run`/`aw agy run`, `aw ipd finalize` by hand, and the `--scope-reason`/`--scope-ack` fence. |
| PR-004 | LOW | IN-SCOPE | G live-artifact criteria | E-05 expected outcome "a new test module of seven tests"; V-05 "all seven tests PASSING BY NAME"; F-07 "`aw check plans` observed exiting 0 at the shell" | The bar was a test count and names, which are artifacts of test organization. F-07's shell-exit observation has also drifted: `aw check plans --agent` now exits 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 now bar on the behaviors (a)-(g) plus cutover invariance; F-07 carries a dated drift note. |
