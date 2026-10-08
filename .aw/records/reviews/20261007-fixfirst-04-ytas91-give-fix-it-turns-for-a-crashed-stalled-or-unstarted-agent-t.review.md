# Review findings: plan ytas91

- Subject-Id: ytas91
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f6322f764`. The plan was committed and byte-identical to the sealed lane
input (sha256 prefix `bb096416bb0ec9f3`), so there was no pre-review snapshot. `aw ipd lint --phase author --agent`:
`clean` before review; `--phase review-finalize`: `clean` after revision. Not an orchestrator.

Verified by symbol: `TURN_RETRY_CLASSIFICATION`, `TURN_RETRYABLE_DISPOSITIONS`, `turn_failure_is_retryable`,
`turn_retry_decision`, `handle_turn_failure_retry` (single call site, after lane preservation); `reconcile_disposition`
rung 5; the `except StallTimeout:` arm of the spawn try in `execute_item_core` (ends in `return`); `turn_attempted_nothing`
and the silent-turn gate (`turn-silent-refused`); `handle_verification_refusal`/`VERIFICATION_REFUSED_KEY`;
`lane_containment.bound_expiry_reaper` (writes `item["turn_bound_expiry"]`), `BOUND_EXPIRY_DISPOSITION`;
`lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`; `oc_runipd.run_queue` `except DriverError`; `run_opencode` `subprocess.Popen`;
`allocate_isolation_worktree` / `worktree_lease.allocate_worktree` HOLDS-WORK attempt-scoping; `resume_via_launcher`;
`p47qfu` (Status reviewed, Set vmrhj0, `aw ipd set superseded p47qfu --dry-run` accepted).

Demonstrations through the real `oc_runipd.execute_item` with a patched launcher (lane-local `.aw/state/`):

```text
nonzero exit, no outcome | status: queued ... (verification send-back fired because --validate defaulted on)
V=True  status fail-verify | skipped: disposition 'fail-verify' is not retryable: verifier refused or turn fell short; not retryable as a host failure | refusal code: turn-silent-refused
V=False status fail-verify | skipped: disposition 'fail-verify' is not retryable: verifier refused or turn fell short; not retryable as a host failure | refusal code: turn-silent-refused
WORK status fail-gate | skipped: disposition 'fail-gate' is not retryable: lifecycle gate or clean-base gate refused; not a host failure to retry without human action | code: None
missing binary | RAISED FileNotFoundError [Errno 2] No such file or directory: '/nonexistent/opencode-xyz' | status: running
STALL status interrupted | skipped: None | session_id: None
LANE attempt 1 | lane wir001 | session_id kw None | resume None
LANE attempt 2 | lane wir001_attempt2 | session_id kw None | resume None
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric G (reachability) | demo `V=False status fail-verify ... turn-silent-refused` | E-01 placed `no-outcome` at `reconcile_disposition` rung 5, but a crash with no work is scored by the silent-turn gate as `fail-verify`, not rung 5. Marking only rung 5 would miss the commonest case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01(a) writes the kind right after the spawn returns, before either scorer. |
| PR-002 | HIGH | IN-SCOPE | Rubric G (reachability) | `except StallTimeout:` ... `return`; demo `STALL ... skipped: None` | The stall arm returns before `handle_turn_failure_retry`, so a `stall` marker could never be read. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | E-01(c) falls through to the retry site after the arm's existing work. |
| PR-003 | HIGH | IN-SCOPE | Rubric A / lane safety | demo `attempt 2 \| lane wir001_attempt2`; `allocate_worktree` HOLDS-WORK; `xd9sll` | E-05 assumed the fix-it turn runs "in the same lane worktree". It does not: a lane with work is attempt-scoped, so resuming the old session there is exactly the cross-tree hazard `xd9sll` prevents. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 re-adopts the failed lane when safe, then resumes; otherwise falls back. OQ-02, D-1. |
| PR-004 | HIGH | IN-SCOPE | Rubric G | demo `missing binary \| RAISED FileNotFoundError ... status: running` | E-02's site was vague and its outcome ("never a run crash") was unreachable via the host's `DriverError` arm, because the exception is not a `DriverError`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 wraps `spawn_executor(...)`, names the exception set and a pre-`Popen` marker, and sets `failed-safely`. |
| PR-005 | MEDIUM | IN-SCOPE | Rubric G | `bound_expiry_reaper._expire`: `item["turn_bound_expiry"] = record` | The turn-limit path "records `BOUND_EXPIRY_DISPOSITION`" only on the item, not as a disposition; E-01 named a site that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01(b) reads and clears the item record per attempt. |
| PR-006 | MEDIUM | UNDER-SCOPE | Rubric G | demo `STALL ... session_id: None` | A stalled attempt has no session id, so E-05 could never resume a stall. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-07/V-07. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric A (double counting) | demo first case: verification send-back spent its own counter on a crash | With `--validate` on, a crash can be sent back by the verification send-back; admitting the same attempt in the turn retry would double-spend. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 refuses when `VERIFICATION_REFUSED_KEY` is present; E-06 tests it. |
| PR-008 | MEDIUM | IN-SCOPE | Security lens | `_PRIOR_ATTEMPT_SAFE_KEYS` driver-only examples ("log: absolute filesystem path") | E-04 passed stderr/stream text and spawn errors that can carry absolute paths, without saying how. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Evidence goes only through the builder's redaction; only the fixed `turn_failure_kind` token is allowlisted. |
| PR-009 | LOW | IN-SCOPE | Rubric D | `tests/test_silent_turn_observability.py` `test_silent_turn_records_refusal_and_event` asserts `fail-verify` | A shipped test pins the silent-turn outcome; the plan did not say whether it changes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Its fake exits 0, so E-01 writes no kind; E-03 requires confirming it passes unchanged; added to Scope-Paths. |
| PR-010 | LOW | UNDER-SCOPE | Rubric G (execution contract) | original gate | Dependency reason, staged-set check, scope-fence wording and conditional finalize were missing; tests named no `run_queue` continuation check. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Contract added; E-06 asserts the next item runs. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the fix-it turn run? | Re-adopt the failed lane when safe, resume its session; else today's fresh lane and session | Resume the old session in the new attempt-scoped lane (cross-tree hazard); always fresh (agent rediscovers work, contradicting the Concern) | `xd9sll` comment in `execute_item_core`; `build_verify_and_continue_notice` "BRING FORWARD ... INTO YOUR OWN LANE" | yes |
| D-2 | Where is the kind written for a crash? | Immediately after the spawn returns, keyed on `exit_code` and outcome-file presence | At rung 5 only (misses the silent-turn scoring); inside `turn_attempted_nothing` (changes a verdict the plan excludes) | demo `fail-verify` vs `fail-gate` split | yes |
| D-3 | Does a stall fall through to the retry site? | Yes, after the arm's existing preservation and event | Leave it to `--retry-incomplete`/`requeue_interrupted` (requires a human resume, which is today's behavior the Concern rejects) | `requeue_interrupted` runs only on resume | yes |
