# Review findings: plan b9n3ad

- Subject-Id: b9n3ad
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72da75876`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `ih2q1a`, Order 1), test-only.

Verified at the lane HEAD:
- `tests/test_core_tier_selection.py` `_gate_env` sets `AW_SUITE_LOCK_DIR=str(lock_dir)` and pops `AW_SUITE_SLOT_HELD`; all three gate_suite tests pass `temp_project / ".suite-locks"`; `pytestmark = pytest.mark.core`.
- F-03: `git merge-base --is-ancestor 548fa71da 686468e2a` exit 1; `548fa71da` IS an ancestor of HEAD (exit 0).
- F-01 text found in the rg7rnx executed plan ("That flake is tracked as backlog `ih2q1a`."). F-05 testprune row `[run-evidence] | 3.02s` found.
- `suite_cache.suite_slot`, `resolve_suite_slots` (default `max(1, cpus // 6)`, 2 on this 12-CPU host), `resolve_suite_slot_timeout`, `resolve_suite_lock_dir` (refuses group/other-writable dir), `SlotOutcome.to_dict` (`slot_acquired`, `waited_seconds`), and `run_full_suite` returning `slot=slot_info` all exist as described.
- Mechanism probe (HOW demonstration for E-02/E-03): holding every slot of an ambient dir in-process, `suite_slot` against it printed `waiting for a test-suite slot (2 of 2 held ...)` and returned `{'slot_acquired': False, 'waited_seconds': 2.003, ...}` at `AW_SUITE_SLOT_TIMEOUT=2`; against a private dir in the same process `{'slot_acquired': True, 'waited_seconds': 0.004, 'slot_index': 0}`. So the in-process hold is observed busy (non-re-entrant `platform_lock`) and the mutation is detectable.
- `_clean_env` copies `os.environ` at call time, so the E-03 mutation is only observable if the ambient `AW_SUITE_LOCK_DIR` is set before `_gate_env` is called.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Duplicate work across Sets | `.aw/records/plans/pending/20261023-twz0tw-01-f4txy2-verify-and-lock-in-the-gate-suite-slot-isolation-fix-in-test.ipd.md` E-02 | Sibling pending plan `f4txy2` (from duplicate backlog `twz0tw`) adds a near-identical regression test to the same file; executing both unguarded yields two copies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 gains a duplicate guard (extend an existing equivalent test instead of adding one); F-06 added; deferred twz0tw row names f4txy2. |
| PR-002 | MEDIUM | IN-SCOPE | Test correctness (ordering) | `tests/test_core_tier_selection.py` `_clean_env` "env = dict(os.environ)" | E-02 did not fix the setup order; if `_gate_env` is called before the ambient `AW_SUITE_LOCK_DIR` is set, the E-03 mutation inherits the developer's real dir and the test may not go red. Also unpinned slot count made the test host-dependent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 prescribes ordered setup, chmod 0o700 (`resolve_suite_lock_dir` refusal), `AW_SUITE_SLOTS=1`, delenv `AW_SUITE_SLOT_HELD`, `waited_seconds < 2.0`, and keeps `_gate_env` signature (imported by `tests/test_suite_cache.py`). |
| PR-003 | MEDIUM | IN-SCOPE | Safety on shared host | E-01 "hold every slot of the DEFAULT lock directory ... and sleeps" | Holding the real machine-wide slots unbounded can starve peer drivers if the executor dies; busy slots held by peers were not handled. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 bounds the holder to 120s, uses a gitignored scratch path, and records already-busy slots. |
| PR-004 | MEDIUM | IN-SCOPE | Executability (load harness) | E-04 "start `2 x os.cpu_count()` busy-loop processes"; V-04 loadavg demand | Unbounded busy loops can leak; 1-minute loadavg ramps slowly so V-04's "exceeds cpu_count" sample may never be taken. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 wraps loads in `timeout 900`, polls loadavg up to 180s before the first run, demands a `ps -p` no-survivor check; V-04 updated. |
| PR-005 | LOW | IN-SCOPE | Evidence drift | F-02 cited `.aw/records/backlog/open/20261018-twz0tw-...` | Item moved to `graduated/`; path no longer resolves. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Path corrected with note. |
| PR-006 | LOW | IN-SCOPE | V-item bars (test counts) | V-01 "`3 passed`", V-02 "`3 passed`", V-03 "`3 failed`" | Collected test counts are artifacts of test organization, not stable bars (rubric G re-derivation convention); also E-05 did not say how a budget-only overrun on a loaded host is treated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01..V-03 demand every named node/launch shape pass or fail by behavior; E-05 records a budget-only overrun verbatim and does not count it as failure. |

`aw ipd lint --phase review-finalize --agent`: `clean` (one info, IPD-Z602).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to avoid duplicating sibling f4txy2's test? | Duplicate guard in E-02: extend an existing equivalent test if present | Retire f4txy2 now (outside plan scope, maintainer's call); add an Item-Dependencies edge (cross-Set and would block if f4txy2 is never run) | f4txy2 E-02; AGENTS.md runner dependency semantics | yes |
| D-2 | Pin slot count in the regression test? | `AW_SUITE_SLOTS=1` | Hold `resolve_suite_slots()` slots (host-dependent) | `suite_cache.resolve_suite_slots`; `tests/test_suite_slot_lock.py` uses `AW_SUITE_SLOTS=1` | yes |
| D-3 | Does a budget-only overrun in the bare gate fail this plan? | No, record verbatim | Treat as failure (load-dependent, unsatisfiable on a busy host) | `conftest.py` "CORE TIER BUDGET EXCEEDED" enforcement; sibling review f6el0l D-2 | yes |
