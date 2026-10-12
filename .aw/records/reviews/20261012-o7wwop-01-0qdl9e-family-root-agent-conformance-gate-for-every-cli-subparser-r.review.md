# Review findings: plan 0qdl9e

- Subject-Id: 0qdl9e
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `9ff0658da`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Re-measured with the lane package (`PYTHONPATH=.`, `AW_NO_REEXEC=1`): the alias-excluding root walk yields 23 roots; BAD = `config exclude` (rc 2, `FAIL     Usage: aw config exclude {add|list|rm} ...`, no record) and `runs` (rc 0, `{"runs": []}`, no record); every other root OK, with `ipd` -> `ipd board` and `releases` -> `releases list` at exit 0 and the rest `error`/`cannot-run`/exit 2 with a non-null `next`. This reproduces F-01, F-02 and F-04. Confirmed `command_surface.discover_parser_leaves` and its alias rule, `conformance_matrix.Exemption`, `MUTATION_EXEMPTION_REGISTRY`, `conformance_matrix.run_cli`, `test_mutation_exemption_registry_contract`, and `0z7ds3`'s OUT clause.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (gate correctness) | `aw find backlog l5dq92` -> `.aw/records/backlog/graduated/20261002-l5dq92-...`; same for `o8cz48`; pending plans `t76qdk`, `2va0jb` carry `From-Backlog` | E-03/E-04(d) required each citation to be an OPEN item, with the path containing `/backlog/open/`. Both cited items are now `graduated`, so the contract test would fail on day one against the only two legitimate entries. F-03's "no plan yet graduates either" is stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The citation rule is now LIVE (`open/`, `graduated/`, `blocked/`) in E-03 and E-04(d). F-03 was re-measured and now records the ordering interaction with `t76qdk` and `2va0jb`. |
| PR-002 | LOW | UNDER-SCOPE | Scope fence | Plan E-01 "file a backlog item for it with `aw backlog new`"; `- Scope-Paths:` lacked `.aw/records/backlog/open/` | The conditional E-01 filing wrote outside the declared scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `.aw/records/backlog/open/` to Scope-Paths. |
| PR-003 | LOW | IN-SCOPE | Project rule (scope-fence wording) | Plan E-01 "STOP that root's admission" | Stop-wording on a scope question. The intent is "do not admit to the sweep". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded to "do not admit it to the sweep". |
| PR-004 | LOW | IN-SCOPE | A (evidence accuracy) | `aw find gm9baj` -> `no artifact matched selector`; OQ-01/OQ-02 `Owner: none`; review probe `wall 75.44` at load 86 | F-06's command did not resolve, as written, without a type. The resolved OQs had no owner. F-05's timing is host-sensitive. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed to `aw find plans gm9baj`, set `Owner: plan author` on both OQs, and noted the loaded-host timing in F-05 (the no-`slow` decision stands, since per-call CPU is about 0.6 s). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should a `known_broken` root exemption accept a `graduated` citation? | Yes: accept open, graduated or blocked (live states); refuse done and parked. | Open-only (fails today); any resolvable item (allows a done item to keep an exemption alive). | `.aw/records/backlog/README.md` maps `graduated/` to "design handed off ... code not yet written; still a release blocker"; `test_mutation_exemption_registry_contract` only requires resolution. | yes |
