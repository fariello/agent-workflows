# Review findings: plan r2wa38

- Subject-Id: r2wa38
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `371fac3b6`. The plan was
committed and byte-identical to the sealed lane input (rev-7, sha256 `5f640fae...`); no snapshot needed. `- Kind: child`,
so `IPD-S407` does not apply. `aw ipd lint --phase author` clean before; `review-finalize` clean after.

Re-measured: `production_checks._check_ipd_conformance` (block "6. Lints conforming at review-finalize":
`lint_file(p, checkpoint="review-finalize")`, every diagnostic copied when not conforming), `backlog_graduate_ipd`,
`backlog_graduate_count`, `backlog_gate_handoff`, `spec_plan_conformance`, `spec_plan_gate_carry`; both production branches
of `runner_shared.execute_item_core` (verifier call order, `host_name = "agy" if "agy" in host_labels.id else "oc"`,
`if findings:` -> `fail-gate`, `record_refusal`, `record_lane_preserved`; `else` -> `aw backlog set ... graduated` /
`aw specs set ... implementing`); `probe_orchestrator`'s `ask = asker if asker is not None else ask_orchestrator_probe`;
`probe_verdict_store_path` via `checkout_control_root`. Existing tests `tests/test_backlog_production.py` and
`tests/test_spec_production.py` drive `initialize_run` + `run_queue` with `_patch_host_agent` and produce only
`Kind: child` plans.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness / C duplicate paths | `production_checks._check_ipd_conformance` `lint_res = _lint.lint_file(p, checkpoint="review-finalize")`; `qs00nc` E-04 adds `IPD-S408` at `review-finalize`; E-02 placed the Set verifier AFTER the per-plan verifiers | After Order 03 the per-plan verifier already lints `IPD-S408`, READING the verdict store before the Set verifier has ASKED; a fresh orchestrator would be judged on an absent verdict (failing every graduation if `qs00nc` OQ-03 makes that an error) and a not-ready one would be reported twice under two codes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02/E-03 order the Set verifier before the per-plan verifier and drop `IPD-S408` from `_check_ipd_conformance`'s output; F-04 and a single-finding case added. |
| PR-002 | MEDIUM | IN-SCOPE | C failure handling / UX | spec `25kzda` 2.5d UNAVAILABILITY (production refuses on could-not-ask); `probe_orchestrator(..., retry_budget, ...)` | The plan did not say what a could-not-ask yields or which retry budget the ask uses; the existing remedy (`<host> run <id6>`) sends the operator to spend an agent turn on a host outage. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 makes could-not-ask a finding naming `aw ipd coverage`, passes `frozen_retry_budget(state)`; case added. |
| PR-003 | MEDIUM | IN-SCOPE | A correctness | `probe_argv` `if host == "agy"`; branch's `host_name`; `probe_verdict_store_path` | "Pass ... host" was unspecified (the CLI identity would mis-select opencode for agy, as in `5etev3` PR-001), and whether a verdict asked from the lane is visible to the next run was asserted only in the Goal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names `host_name` and the lane/control-root store. |
| PR-004 | MEDIUM | IN-SCOPE | E reachability | `execute_item_core` passes no asker; `_assert_probe_spawn_is_permitted` | The integration cases need a way to inject the probe through `run_queue`; none was named. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 patches `runner_shared.ask_orchestrator_probe` with a counting double; V-04 demands its call count. |
| PR-005 | LOW | IN-SCOPE | E/G | E-04; gate | No could-not-ask or duplicate-finding case, a single mutation, no host coverage; gate lacked scope fence and the paste-actual-output rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cases, an ordering mutation (with an honest not-observable clause tied to `qs00nc` OQ-03), both hosts, gate contract. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Avoid the double report of `IPD-S408` how? | Set verifier first, filter `IPD-S408` from the per-plan output | exempt orchestrators from the per-plan lint (loses its other checks); accept two findings | `_check_ipd_conformance` copies every diagnostic | yes |
| D-2 | Integration probe seam? | Patch `runner_shared.ask_orchestrator_probe` | thread an `asker` through `execute_item_core` (new production parameter used only by tests) | `probe_orchestrator` default seam | yes |
