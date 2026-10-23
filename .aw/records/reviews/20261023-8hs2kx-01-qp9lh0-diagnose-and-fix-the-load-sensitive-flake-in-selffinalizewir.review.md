# Review findings: plan qp9lh0

- Subject-Id: qp9lh0
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `41381dc2e`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author` and `--phase review-finalize` were clean (0 findings).

Re-verified:
- `tests/test_oc_runipd.py` `SelfFinalizeWiringTests.test_begin_precedes_run_opencode_on_success` ends with `self.assertEqual(order[:2], ["begin", "run"])`; `SelfFinalizeHelperTests.setUp` calls `support.declare_execution_role(self)` and `SelfFinalizeWiringTests` has no `setUp`.
- `runner_shared.execute_item_core` gates before the spawn: stale Scope-Paths (`item["scope_target_refusal"]`, attempt `scope_target_refused`), `preflight_host_capabilities` (attempt `host_capability_unavailable`, `record_refusal` writes `item["refusal"]` via `render_stream.REFUSAL_KEY = "refusal"`), clean base (`item["clean_base_refusal"]`), lane errors (`item["worktree_error"]`), `assert_child_tool_identity` (raises `ToolIdentityError`, cached in `_TOOL_IDENTITY_VERIFIED`), begin refusal (`item["begin_refusal"]`, event `ipd-begin-refused`, stderr "begin refused (no execution authority); not launching").
- Executed plan `h8peam` V-05 quotes the failing node and `1 failed, 385 passed in 446.09s (0:07:26)` with the three passing reruns.
- All seven modules of the E-01 set exist. `pytest_repeat` is not installed (re-measured: `ModuleNotFoundError`). Single node re-run here: `1 passed in 4.64s`.
- `conftest.py` `_DEFAULT_TEST_CPU_TIMEOUT = 60.0`, `_DEFAULT_TEST_WALL_TIMEOUT = 240.0`, `class TestHangTimeout(BaseException)`.
- `pyproject.toml` pytest-randomly note: reproduce with `-p randomly --randomly-seed=<n>`, not `-p no:randomly`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Diagnostic completeness | `agent_workflows/runner_shared.py` `execute_item_core` (attempt keys `host_capability_unavailable`, `scope_target_refused`, `clean_base_refused`, `begin_refused`; event `ipd-begin-refused`) | E-02's message listed only item-level fields. The host-capability preflight leaves no item-level field except the generic `refusal`, and the attempt dict and `events.jsonl` carry the precise gate. E-01 also did not ask for captured stderr, where every gate prints its refusal. So the next failure could still be undiagnosable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds the attempt gate keys, the last `events.jsonl` event names, a missing-key-tolerant helper, and a note that `ToolIdentityError` surfaces as its own traceback. E-01/V-01 capture "Captured stderr call". V-02 demands the `ipd-begin-refused` event in the message. |
| PR-002 | LOW | UNDER-SCOPE | E. Reproduction evidence | F-4 (ambient `AW_*` environment, load) | E-01 did not record the conditions F-4 names as candidate causes, so a reproduction could not be tied to them. It also stated no stopping bound or log location. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records `env \| grep '^AW_'` and `uptime`, writes logs to `/tmp/opencode/qp9lh0/` (never committed), and is bounded by the stated attempt counts or the first reproduction. |
| PR-003 | LOW | IN-SCOPE | G. Scope check vs. execution contract | old Scope check "stop and file a corrective plan instead" | A bare STOP over a scope question contradicts the runner contract (record and continue). The plan also did not say how to file the corrective work from a non-interactive run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Ship E-02, record the cause and fix as an outcome `proposal` (or `aw backlog new` by hand), mark E-03 `blocked`, and finish the independent work. |
| PR-004 | LOW | IN-SCOPE | E. Validation precision | old E-04 "under 3 fixed seeds"; Deferred "E-03 extends the same fix" not in E-03 | The seeds were unnamed and did not include a reproducing seed. The sibling-test extension was promised in Deferred but missing from E-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Seeds 1, 2, 3 plus any reproducing seed (E-04 and Required tests). E-03 now states the sibling extension. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the bounded attempt count (5 seeded module-set runs + 50 loaded single-node iterations) enough before shipping the diagnostic-only mitigation? | Yes, with stop-at-first-reproduction | An unbounded hunt; more seeds | F-2 shows no reproduction at authoring; plan goal makes the diagnostic message the fallback deliverable | yes |
| D-2 | Should a spec-touching production fix be done in this plan? | No; record a proposal and block E-03 | Amend a spec in this plan (none declared in Scope-Paths) | AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT" | yes |
