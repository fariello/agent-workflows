# Review findings: plan 2eubdn

- Subject-Id: 2eubdn
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e547fdb41` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Reproduced (gitignored `tmp/pr/crash.py`, `tmp/pr/tmpfix.py`, no production edit):
- `aw check all --json` on this tree: absolute root in `data.policy_findings[].recovery` 9 times
  (`check.ipd-lint-diagnostic` 8, `check.system-layout-missing` 1) plus `data.repo_root` 1. Authoring
  measured 7+1; the difference is pending-plan drift and the property holds.
- Placement fixture (same plan in `pending/` and `executed/`) under `$HOME`: `--agent exit 1 stdout bytes 0`,
  `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'diagnostics[2].location'`.
  `--json` exit 1 with output.
- Same fixture under `/tmp`: `--agent` exits 1 with a record that still carries the absolute root 3 times;
  `--json` carries it 22 times (`diagnostics[].fix/detail/location`, `next_actions[].command`,
  `data.policy_findings[].recovery/detail/location`).
- Cited code resolves: `finding_dict` relativizes `location` only (`agent_workflows/check_engine.py:942-973`);
  `check_lifecycle_placement` `loc_header`/`recovery` (`:2088-2135`); collision detail strings (`:1840`, `:1865`);
  `aw install {root}` (`:3646`); lint recoveries (`:8443`, `:8550`); `specs.drift_location` "leak-free choice"
  (`agent_workflows/specs.py:352`); `doctor._normalize_rel_path`/`build_remediation` (`doctor.py:888`, `:931`);
  F-08 assertions (`tests/test_check_engine.py:1037-1062`); `data` exemption sentence
  (`docs/cli-output-contract.md:230`); `test_data_channel_exempt_and_unredacted`
  (`tests/test_json_surface_leak_posture.py:234`); `aw install` targets "Repo dirs (default: cwd)".
- `un6ppd` is a graduated backlog item whose plan `wqiofa` is pending, so it is a live carrier.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Traceability (durable carrier) | Deferred row "Unifying the three relativization helpers ... Carrier: w38q54"; `w38q54` is this plan's `- From-Backlog:` | The deferred P8 unification was carried by the plan's own source item, which closes when this plan executes, so the obligation would have vanished. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Filed backlog `qv0fi1` (chore, low) and re-pointed the Deferred row and Scope check to it. `aw backlog check` conforms; `check_durable_carrier` reports nothing for this plan. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (assertion strength) | `tmp/pr/tmpfix.py`: a `/tmp` fixture carries the absolute root 22x on `--json` and 3x on `--agent` with no validator objection; `data.repo_root` is declared out of scope | E-06 asserted only "zero `_HOME_PATH_RE` matches including `data`". That cannot pass while `data.repo_root` stays absolute, and it proves only "not under home", not "repo-relative". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now skips `data.repo_root` by name and additionally asserts that no field contains the fixture's resolved absolute root as a substring. |
| PR-003 | LOW | IN-SCOPE | E. Reachability | `check_ipd_lint_reach` guards `_m105_terminal_date_applies` (`ipd_lint.M105_TERMINAL_CUTOVER_DATE = "20260712"`) and `_schema._check_path_status` | V-04's second-site fixture did not state its two trigger preconditions, so a fixture with an early date would emit nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now names both preconditions, with an example. |
| PR-004 | LOW | IN-SCOPE | F. Consistency | `doctor.build_remediation` emits "run 'aw install' in this repo ..." (`doctor.py:1247`) | E-03's bare `aw install` form already has an in-repo precedent, which the plan did not cite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Precedent cited in E-03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who carries the deferred helper unification? | New backlog `qv0fi1` | Keep `w38q54` (closes with this plan); fold the unification into this plan (four modules, a behavior argument about which fallback wins, over-scope for a release-blocking leak fix) | `check_engine.check_durable_carrier` semantics; plan's own Deferred rationale | yes |
