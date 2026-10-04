# Review findings: plan 26m1nb

- Subject-Id: 26m1nb
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

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
