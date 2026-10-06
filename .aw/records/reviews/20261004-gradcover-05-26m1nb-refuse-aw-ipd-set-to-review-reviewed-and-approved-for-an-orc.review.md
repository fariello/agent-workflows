# Review findings: plan 26m1nb

- Subject-Id: 26m1nb
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: round 2: PR-008 (HIGH, fixed), PR-009 (MEDIUM, fixed), PR-010 (LOW, fixed), PR-011 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `a5d5729a4`. The plan was
committed and byte-identical to the sealed lane input (rev-6, sha256 `1704c59f...`); no snapshot needed. `- Kind: child`,
so `IPD-S407` does not apply. `aw ipd lint --phase author` clean before; `review-finalize` after reports only the `info`
advisory `IPD-Z602` on E-06, accepted: E-06 is one concern (updating the pins of the old backward-edge contract) whose
clauses enumerate the pinned assertions.

Re-measured: `ipd_lifecycle._LEGAL_BACKWARD_EDGES` (three pairs), `validate_transition` (consults it, then refuses
`to_rank < from_rank`), `_PLAN_STATUS_RANKS` (`approved` and `auto-approved` both 3), `_plan_status_events` (reads the
history line's workflow token as the transition status); `check_engine.check_lifecycle_transitions`;
`status_set.apply_status_change` (`message = getattr(args, "message", None) or default_message`;
`hist_entry = f"- {today} {status_tag} ({actor}): {message}"`); `run_set_command` dry-run branch and the blocking-close
comment "BEFORE `is_dry_run`"; `write_item_dependencies` driving a same-status `run_set_command`;
`agent_schema.RECORD_KINDS = ("result", "summary", "item", "error")`. Existing tests: `tests/test_plan_transition_gate.py`
cases (a) and (c), `tests/test_ipd_lifecycle_backward_edges.py` case 4. Live tree: `aw check plans` reports five
`check.lifecycle-transition-invalid` findings, all `to-review -> draft`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D anti-regression | `tests/test_plan_transition_gate.py` `test_case_a_illegal_nonterminal_backwards_edges_refuse_and_preserve_file` (expects `approved -> draft` etc. refused) and `test_case_c_enumerated_legal_backward_recovery_edges_succeed` (no `--message`, expects 0); `tests/test_ipd_lifecycle_backward_edges.py` `test_case_4_controls_unenumerated_backward_edges_still_refused` | E-05 inverts the contract these tests pin and makes message-less backward moves fail; the files were not in scope, and V-05 mentioned only one of them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-06/V-06 name each test and its rewrite and require a caller search; both files added to Scope-Paths. |
| PR-002 | HIGH | IN-SCOPE | A data integrity | `ipd_lifecycle._plan_status_events` "the `workflow` token ... is the new status ONLY when it is a known plan status"; `status_set` `hist_entry = f"- {today} {status_tag} ..."` | E-05's history line `demoted <from> -> <to>: <reason>` would, if used as the token, drop the transition from the event stream and leave `check.lifecycle-transition-invalid` blind to it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 keeps the target status as the token, with the demotion text in the message; expected outcome adds the lifecycle-check effect. |
| PR-003 | MEDIUM | IN-SCOPE | E contract | `agent_schema.RECORD_KINDS = ("result", "summary", "item", "error")` | E-05 asked for a `warning` record, which is not a valid `aw.agent/v1` kind. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The warning is carried inside the terminal `result` record; V-05 validates it. |
| PR-004 | MEDIUM | IN-SCOPE | A correctness | `apply_status_change` `message = getattr(args, "message", None) or default_message`; `_PLAN_STATUS_RANKS` `approved`/`auto-approved` = 3; `write_item_dependencies` same-status `run_set_command` | "Require `--message`" could test the defaulted message and never refuse; "forward" was undefined for the same-rank pair; same-status no-op writes on a not-ready orchestrator could be refused. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 tests the explicit flag; E-01 defines forward by rank and exempts same-status writes; V-01 adds the no-op case. |
| PR-005 | MEDIUM | IN-SCOPE | E reachability | `run_set_command` `is_dry_run`; blocking-close comment "BEFORE `is_dry_run`" | The real-tree evidence relied on `--dry-run` refusing, but E-01 did not place the gate before the dry-run branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 sites the gate before the dry-run branch; required evidence states both possible outcomes for `axozpe`. |
| PR-006 | LOW | IN-SCOPE | Evidence / scope | OQ-01 "lists only the production action and `aw ipd coverage`"; `hm1h3l` A.6 now lists four asking consumers; Scope check left `orchestrator_readiness.py` undeclared | OQ-01 cites the pre-review spec text; the E-02 parameter was known up front but left for a finalize scope reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 aligned; `orchestrator_readiness.py` declared and the parameter named. |
| PR-007 | LOW | IN-SCOPE | G | Scope "OUT: backward transitions ... remain allowed unconditionally" vs E-05; gate | The Scope OUT clause contradicted E-05; the gate lacked a scope fence and the paste-actual-output rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope wording corrected; gate contract completed; lifecycle-check before/after evidence added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | History-line shape for a demotion? | Target status as token, `demoted <from> -> <to>: <reason>` as message | a new `demoted` token (invisible to the lifecycle event stream) | `_plan_status_events`; `check_lifecycle_transitions` | yes |
| D-2 | Agent-surface form of the demotion warning? | Inside the terminal `result` record | a separate record (invalid kind) | `agent_schema.RECORD_KINDS` | yes |
| D-3 | Is the same-rank `approved <-> auto-approved` move gated or treated as backward? | Neither | treat as backward (requires `--message` for a lateral move) | `_PLAN_STATUS_RANKS` | yes |

## Round 2

Re-review after the 2026-10-04 maintainer ruling moved the coverage answer into the plan (`25kzda` 2.5e). Lane
`review-sweep-run-20261006T040814Z-944` at HEAD `cabcc453b`; plan committed and byte-identical to the sealed lane input
(no snapshot). `- Kind: child`, `IPD-S407` n/a. `aw ipd lint --phase author` and `review-finalize` both report only the
`info` advisory `IPD-Z602` on E-06, accepted as in round 1. Orders 00 to 03 are `reviewed`, none executed.

Measured: a spy wrapping `status_set.apply_status_change` over the bare suite (`1 failed, 5082 passed, 2 skipped`; the one
failure is `tests/test_readiness_absence_invariant.py`, which flags this plan and `r2wa38` for carrying `- Readiness:` at
`to-review`, cleared for this plan by the `reviewed` transition below) recorded every non-terminal backward plan move:
nine, of which five pass no `--message`, three in `tests/test_plan_transition_gate.py` case (c) (already in E-06) and two in
`tests/test_status_set.py` (not in scope). Live tree: `aw check plans` reports five `check.lifecycle-transition-invalid`
findings, unchanged from round 1. `aw ipd set reviewed axozpe --dry-run` today previews the write (no gate yet), so the
real-tree evidence remains reachable only after E-01. In-tree production callers of a backward plan move: none found
(argv builders in `runner_shared` issue only `auto-approved`, `begin`, `finalize`, and spec/backlog setters; `work_cmd`
`aw finish` moves forward). `runner_shared.set_plan_approved` drives `aw set auto-approved`; its failures are caught by the
queue builder and `execute_item_core`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-008 | HIGH | UNDER-SCOPE | D anti-regression | `tests/test_status_set.py` `TestApprovedWritesApprovalField.test_approval_field_stripped_when_leaving_approved` (`approved -> reviewed`, no `--message`) and `ApprovalGateTests.test_the_override_is_not_recorded_when_it_had_no_effect` (`reviewed -> to-review`, no `--message`); measured by setter spy | E-05's `--message` requirement breaks two tests outside the declared files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 names both, requires re-derivation by bare suite; file added to Scope-Paths; V-06 updated. |
| PR-009 | MEDIUM | UNDER-SCOPE | C operability | `runner_shared.set_plan_approved` (`aw set auto-approved ... --yes`); queue build `set_plan_approved_fn` in `try/except`; `/plan-review` sets `reviewed` through the setter | Setter-routed orchestrator promotions by the runner and `/plan-review` inherit the new gate and will refuse without a coverage record; the plan did not state or test this. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-03 records the inheritance and the designed remedy (Order 07, Order 11); E-04 adds an `aw set auto-approved` refusal case; V-04 demands it. |
| PR-010 | LOW | IN-SCOPE | E contract / consistency | E-01 "absent or stale verdict"; `agent_schema.RECORD_KINDS` | Stale verdict wording after the ruling; refusal record shape unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Wording now says coverage record; agent refusal is one `result` record carrying code, subject and remedy. |
| PR-011 | LOW | IN-SCOPE | G executability | gate "a caller found by E-04's search" (the search is in E-06); "six Scope-Paths"; targeted test list | Cross-reference and count drift; `tests/test_scaffold_history_clock.py` (asserts no `check.lifecycle-transition-invalid`) missing from targeted run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected references and counts; test added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the runner's `aw set auto-approved` bypass the orchestrator gate? | No; it inherits the gate | an actor-keyed exemption (re-opens the bypass `d7bnhc` closed) | `status_set` approval-gate comment "a caller-side check is exactly what a DIFFERENT caller skips"; `25kzda` 2.5d CONSUMERS (Order 01) | yes |
| D-2 | Fix the two `test_status_set.py` tests how? | Add `--message`, assertions unchanged | exempt `-> reviewed` from the message rule (contradicts Order 01 E.1 "EVERY BACKWARD MOVE IS LOUD") | `hm1h3l` E.1 | yes |
