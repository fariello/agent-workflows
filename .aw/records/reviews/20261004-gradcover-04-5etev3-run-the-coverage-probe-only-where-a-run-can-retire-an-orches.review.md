# Review findings: plan 5etev3

- Subject-Id: 5etev3
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: round 2: PR-007 (HIGH, fixed), PR-008 (MEDIUM, fixed), PR-009 (MEDIUM, fixed), PR-010 (MEDIUM, fixed), PR-011 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `b1ff0278e`. The plan was
committed and byte-identical to the sealed lane input (rev-5, sha256 `d43792bd...`); no snapshot needed. `- Kind: child`,
so `IPD-S407` does not apply. `aw ipd lint --phase author` clean before; `review-finalize` clean after.

Re-measured in `agent_workflows/runner_shared.py`: `queued_orchestrator_targets` (filters only `kind`),
`enforce_orchestrator_probe_gate(run_dir, state, *, repo, host, ..., retry_budget, asker, runner)` and its
`labels = AGY_HOST_LABELS if host == "agy" else OC_HOST_LABELS`; `probe_argv` `if host == "agy"`;
`dispatch_orchestrator_item` (no `host` parameter; RETIRE branch calls `_lifecycle.retire_orchestrator`; terminate tail
calls `record_refusal` and appends `orchestrator-deferred`); `ORCH_REASON_FINALIZE_REFUSED` remedy text ("retire the
orchestrator through `aw ipd finalize`"); `frozen_retry_budget`; `resolve_cli_host`; `state["host_capabilities"]["host"]`;
the `--full-auto` bridge `item["action"] = "execute"`; queue-build `status = "auto-approved"` before `action_for`.
Host loops: `oc_runipd.run_queue` and `agy_runipd.run_queue` both call `dispatch_orchestrator_item` under
`if runnable.get("action") == "orchestrate":` passing no host. Measured: `action_for('orchestrator', s)` for five
statuses; `resolve_cli_host` returns `opencode`/`antigravity`; `ask_orchestrator_probe` under `PYTEST_CURRENT_TEST`
raises `DriverError`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness | `runner_shared.probe_argv` `if host == "agy"`; `resolve_cli_host` returns `antigravity`/`opencode`; `oc_runipd.run_queue` / `agy_runipd.run_queue` `dispatch_orchestrator_item(` calls pass no host | E-03's "read it from `state`" would yield `antigravity`, which `probe_argv` treats as opencode, so an agy run's re-check would spawn the wrong binary. E-03 also claimed host modules may need no change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds a keyword `host` passed as `"oc"`/`"agy"` from each loop with a mapped fallback; host modules added to Scope-Paths; E-04 case (h); V-03 rewritten. |
| PR-002 | HIGH | UNDER-SCOPE | D anti-regression | `tests/test_orchestrator_retirement.py` `test_reconsidered_then_retired_in_the_same_run_on_both_hosts` patches only `retire_orchestrator`; `_assert_probe_spawn_is_permitted` | After E-02 every existing test reaching RETIRE asks the probe first and raises under pytest; that file was not in scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires seeding a pass verdict in those tests without changing assertions; file added to Scope-Paths; V-04 lists touched tests. |
| PR-003 | MEDIUM | IN-SCOPE | E/UX | `dispatch_orchestrator_item` terminate tail already calls `record_refusal`; `ORCH_REASON_FINALIZE_REFUSED` remedy "retire ... through `aw ipd finalize`" | E-02 asked for a second `record_refusal`, and the inherited remedy would tell the operator to finalize by hand, wrong for an uncovered-work refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Refusal flows through the existing tail; the detail carries the Order 03 shared remedy per finding; status follows existing `finalize-refused` behavior. |
| PR-004 | MEDIUM | IN-SCOPE | C operability | `probe_orchestrator(..., retry_budget, ...)` is required; `frozen_retry_budget(state)` | E-02 named no retry budget for the retirement-time ask. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 passes `frozen_retry_budget(state)`. |
| PR-005 | LOW | IN-SCOPE | A soundness | `execute_item_core` `item["action"] = "execute"` after `set_plan_approved`; queue build `status = "auto-approved"` before `action_for` | The frozen-action filter's soundness under `--full-auto` was unstated; empty-target behavior unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records why no item becomes `orchestrate` mid-run and specifies the empty-target event. |
| PR-006 | LOW | IN-SCOPE | E/G | E-04 cases; gate | No could-not-ask case at retirement, no second mutation for E-02, no pinning-test citation; gate lacked scope fence and paste-actual-output rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cases (g), (h) and a second mutation added; citation added; gate contract completed; required test list widened. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does `dispatch_orchestrator_item` learn the host? | Keyword `host` passed by each loop, fallback mapping from `host_capabilities.host` | read state only (needs a mapping anyway, implicit); new state field (more surface) | `probe_argv`; `resolve_cli_host` measured | yes |
| D-2 | Status of a retirement refused by the re-check? | Existing `finalize-refused` terminate path, plan left in `pending/` | new non-failing status (unspecified, touches renderers) | every other retirement refusal uses it; spec 2.5d says plan stays in `pending/` | yes |
| D-3 | Fix existing retirement tests how? | Seed a pass verdict in their setup | patch `review_readiness` (hides the new call from those tests) | `record_probe_verdict` exists; tests keep their assertions | yes |

## Round 2

Re-review after the 2026-10-04 maintainer ruling moved the coverage answer into the plan (`25kzda` 2.5e). Lane
`review-sweep-run-20261006T040814Z-944` at HEAD `c003d595e`; plan committed and byte-identical to the sealed lane input
(no snapshot). `- Kind: child`, `IPD-S407` n/a. `aw ipd lint --phase author` clean before, `review-finalize` clean after.
Orders 00 to 03 are `reviewed`, none executed, so `coverage_record` and `orchestrator_readiness` do not exist yet; their
contracts were read from `8mabmu` E-03/E-07 and `qs00nc` E-01. Measured: a dispatch spy over nine runner test files
(400 passed) shows exactly three tests reach the RETIRE branch, all in `tests/test_orchestrator_retirement.py`;
`evaluate_set_retirement` is eligible for a Set with a `superseded/` child; `lint_file(..., checkpoint="author")` on a
`pending/` child at `Status: executed` errors `IPD-S404`/`IPD-M105`; patching `ask_orchestrator_probe` with a wrapper over
a `runner` double records `argv[0] == "agy"` for `host="agy"`, and `probe_argv(host="oc")` begins `opencode`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-007 | HIGH | IN-SCOPE | A correctness / D regression | `runner_shared.evaluate_set_retirement`, `set_retirement_terminal_statuses` (`ipd_schema.TERMINAL`); `qs00nc` E-01 condition 2 and OQ-02 (ready list excludes `superseded`); `tests/test_orchestrator_retirement.py` `test_reconsidered_then_retired_in_the_same_run_on_both_hosts` fixture child at `pending/` + `Status: executed` | E-02 refused on any not-ready `review_readiness` result. Full 2.5d readiness is stricter than retirement eligibility: a Set with a deliberately superseded child (backlog `31y86f`) would never retire, and the existing mid-run fixture child would fail condition 2's `author` lint. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 refuses on condition-4 (coverage) findings only, with the reason and evidence (F-06, OQ-02); test (i) and a third mutation pin it; Scope updated; Order 01 given a re-scope note to make A.6 explicit. |
| PR-008 | MEDIUM | IN-SCOPE | A data integrity | `ipd_lifecycle._assert_rollup_touched_only_owned_paths`; `8mabmu` E-07 "COMMIT THE RECORD AT ONCE" | E-02 left the dirty-plan ordering as an executor choice ("record which"), but Order 02 already settled it by committing at write. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 states the settled ordering, forbids a second commit path, and names a stop condition if Order 02 as executed differs; V-02 demands the check. |
| PR-009 | MEDIUM | UNDER-SCOPE | E testability (reachability) | `dispatch_orchestrator_item` signature (no asker/runner); `oc_runipd.run_queue`/`agy_runipd.run_queue` | E-04 cases (d) to (h) require injecting an asker/runner into dispatch and `run_queue`, but no such seam exists or was planned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds `asker`/`runner` pass-through keywords; (h) patches `ask_orchestrator_probe` with a runner-recording wrapper (demonstrated at review); V-03 names the expected tokens. |
| PR-010 | MEDIUM | IN-SCOPE | D anti-regression / consistency | E-04 "seeding a `pass` verdict for each fixture orchestrator's digest"; `8mabmu` retires the verdict store | Stale wording from before the ruling contradicted the plan's own "write the coverage record" and was unmeasured as to which tests need it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with writing a current coverage record; the three affected tests named as context with re-derivation required. |
| PR-011 | LOW | IN-SCOPE | G executability | Required tests list; V-02/V-04 | `tests/test_driver_attestation_gate.py` (drives retirement) missing from the targeted run; mutation and V wording did not cover the new case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to targeted run; V-02, V-03, V-04 reconciled. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which readiness findings refuse a retirement? | Condition 4 (coverage) only | all four (regresses `31y86f`); new spec carve-out text in this plan (spec edit belongs to Order 01) | `hm1h3l` A.2 wording ("edited by a child's turn", "the quoted finding"); `evaluate_set_retirement` measured | yes |
| D-2 | How do tests inject the probe into dispatch and `run_queue`? | `asker`/`runner` keyword pass-throughs on dispatch; patch `ask_orchestrator_probe` for `run_queue` | thread asker through `run_queue` (widens both host loops) | demonstrated wrapper recording `argv[0]` | yes |
| D-3 | Dirty-plan ordering at retirement | Rely on Order 02's commit-at-write; no second commit path | commit in dispatch (a second commit path) | `8mabmu` E-07 | yes |
