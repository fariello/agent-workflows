# Review findings: plan f4txy2

- Subject-Id: f4txy2
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `891f9124a`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `twz0tw`, Order 1), test-only.

Verified at the lane HEAD:
- `_gate_env` in `tests/test_core_tier_selection.py` sets `AW_SUITE_LOCK_DIR=str(lock_dir)` and pops `AW_SUITE_SLOT_HELD`; `_clean_env` does `env = dict(os.environ)` at call time.
- `tests/test_suite_cache.py` imports `_gate_env` (`test_run_full_suite_budget_only_failure_names_budget_in_reason`, `..._budget_control_with_failing_test`).
- `suite_cache.DEFAULT_AW_SUITE_SLOT_TIMEOUT: float = 3600.0`; `conftest._DEFAULT_TEST_WALL_TIMEOUT = 240.0`; `platform_lock` "NOT RE-ENTRANT, ON PURPOSE"; `platform_lock.held` exists; `d8b534637` subject matches; carrier backlog `jycfw3` exists.
- `suite_slot` prints its waiting line via `sys.stderr.write` in the parent process; `run_full_suite`'s `SuiteRunResult.stderr` is the child subprocess's stderr (`_run_streaming_subprocess`/`_run_captured_subprocess`).
- Probe (HOW demonstration): ambient dir with `suite-slot-0.lock` held in-process, `AW_SUITE_SLOTS=1`, timeout 2s, env inherited without private override: `run_full_suite` returned `{'slot_acquired': False, 'waited_seconds': 2.002, ...}`, `"waiting for a test-suite slot" in res.stderr` -> `False`, while the parent stderr carried `aw suite: waiting for a test-suite slot (1 of 1 held: unknown holder)`. With a private dir: `{'slot_acquired': True, 'slot_index': 0, 'waited_seconds': 0.001}`.
- Sibling plan `b9n3ad` (Set `ih2q1a`) is `reviewed` and proposes an equivalent, broader test in the same file.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Test correctness (vacuous assertion) | E-02 "`res.stderr` ... does not contain `waiting for a test-suite slot`"; probe above | `res.stderr` is the child's stderr; the waiting line goes to the parent's stderr, so that assertion can never fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires the `capfd` check and forbids the `res.stderr` assertion; V-02 demands it. |
| PR-002 | MEDIUM | UNDER-SCOPE | Duplicate work | `.aw/records/plans/pending/20261023-ih2q1a-01-b9n3ad-...ipd.md` E-02 | Sibling `b9n3ad` adds an equivalent test to the same file; running both plans unguarded adds two copies. | all Low | FIXED | E-02 has a reciprocal duplicate guard; F-5 and a Scope-check overlap note added; V-02/V-03 accept the reuse path; gate notes `--scope-ack`. |
| PR-003 | MEDIUM | IN-SCOPE | Test correctness (ordering) | `_clean_env` "env = dict(os.environ)" | Without an explicit order, `_gate_env` built before the ambient env is set makes the E-03 mutation inherit the developer's real lock dir, so the test may not go red. | all Low | FIXED | E-02 requires the ambient setenvs before `_gate_env` is called. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | Gate lacked the paste-actual-output rule, the scope-fence declaration, a staged-set check, and conditional finalize ownership. | all Low | FIXED | Gate rewritten as a full execution contract. |
| PR-005 | LOW | IN-SCOPE | Shared-host safety | E-01 background holder of real slots | The real-slot holder had no time bound; a crash could starve peer drivers. | all Low | FIXED | Holder releases after at most 120s and prints dir and indices. |
| PR-006 | LOW | IN-SCOPE | V-item bars | V-01 "the three `gate_suite` node ids"; bare gate demand | Fixed test count used as a bar; the treatment of a budget-only overrun on a loaded host was unstated. | all Low | FIXED | V-01 re-derives the count; Required tests records a budget-only overrun verbatim, not as a failure. |

`aw ipd lint --phase review-finalize --agent`: `clean` after `aw ipd set reviewed`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Retire f4txy2 as superseded by b9n3ad now? | No; add a reciprocal duplicate guard and leave retirement to the maintainer | Retire in this review (a disposition change is not a plan-review edit and is the maintainer's call) | plan-review Step 2.4 (surgical edits); b9n3ad deferred row | yes |
| D-2 | How to check for the waiting line? | `capfd` on the parent process | `res.stderr` (demonstrated vacuous) | probe output above; `suite_cache.suite_slot` `_say` writes `sys.stderr` | yes |
| D-3 | Does a budget-only overrun in the bare gate fail this plan? | No, record verbatim | Treat as failure (load-dependent) | `conftest.py` "CORE TIER BUDGET EXCEEDED"; review b9n3ad D-3 | yes |
