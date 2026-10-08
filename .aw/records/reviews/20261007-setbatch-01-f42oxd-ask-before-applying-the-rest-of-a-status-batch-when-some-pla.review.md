# Review findings: plan f42oxd

- Subject-Id: f42oxd
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `1f0c81fd4`. The plan was committed (`eb52f31e4`) and byte-identical to the lane input (sha256 `9d10437d...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review; `--phase review-finalize --agent`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.

Verified by reading `status_set.run_set_command` end to end: the six per-record gates and their exit codes; the whole-command refusals before them; the `executed` delegation sitting between the handoff gate and the terminal-reopen gate; the `--agent`/`--json` confirmation refusal after all gates; `_RETRY_FLAG_ALLOWLIST`; the five `cli.py` dispatch sites; `term.is_interactive` precedence (probed); `cli._confirm` prompt shape.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D (anti-regression) | `status_set.run_set_command` terminal-reopen (`status.terminal_reopen_refused`, `exit_code=2`, `return 2`) and backward-move (`status.backward_plan_message_required`, `return 2`); `tests/test_status_set.py` reopen test `assertEqual(rc, 2)`; `tests/test_plan_transition_gate.py` "Expected rc=2 for backward edge" | Plan claimed today's refusal exits 1 and that the refuse branch is "as today", but two gates exit 2 and tests pin it; "all refused" was undefined for mixed-gate batches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each refusal entry carries its gate's exit code; REFUSE exits the max; Concern corrected; test and invariant added. |
| PR-002 | HIGH | IN-SCOPE | Rubric F/B (silent hang, machine output) | `status_set.run_set_command` `ctx.is_agent or ctx.is_json` branches; `--dry-run` branch; `term.is_interactive` | E-02 would prompt under `--agent`/`--json` on a TTY (corrupting JSONL, blocking an agent) and left `--dry-run` undefined. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | ASK requires human mode and not dry-run; dry-run semantics for both flag states specified; invariant (3). |
| PR-003 | HIGH | IN-SCOPE | Rubric C (sequencing) | `juu1rj` (approved) E-02/E-04 rewrite the orchestrator, backward-move and terminal-reopen human output in `status_set.py` | Both plans restructure the same refusal branches; unordered, one silently reverts the other's wording or this plan's conversion strands juu1rj's edits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Item-Dependencies: executed:juu1rj`; E-02 must preserve the shipped rendering and asserted phrases. |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric F (recovery path) | `status_set._RETRY_FLAG_ALLOWLIST`; `_retry_command` callers in the confirmation refusal | `--agent --skip-refused` without `--yes` would emit a retry command missing `--skip-refused`, which then refuses the whole batch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds the allowlist entry; V-03 checks the echoed command. |
| PR-005 | MEDIUM | UNDER-SCOPE | Project rule (flag on every spelling) | `cli.py` `prompts set` dispatch `scoped_type="prompts"` | E-04 listed four spellings; `aw prompts set` also routes to `run_set_command`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Five parsers named; `--status` spellings documented inert. |
| PR-006 | MEDIUM | IN-SCOPE | Rubric A/E (output contract) | `agent_schema.validate_agent_record` greenwash rules; `CommandResult` shape in `run_set_command` | "`outcome: findings` with both lists" did not name keys, verified/complete, diagnostics, or a rule id for the orchestrator gate, which today hand-builds its record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 specifies `data.items`/`data.skipped` keys, one Diagnostic per skip with gate rule id, validation; E-01 names rule ids incl. new `status.orchestrator_not_ready`. |
| PR-007 | MEDIUM | IN-SCOPE | Rubric E (HOW demonstrated) | `term.is_interactive` precedence; review probe output in plan F-07/OQ-02 | "Simulated interactive" was undemonstrated; on CI `CI=1` beats `--interactive` and the test would silently take the non-interactive path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 resolved with probe; E-05 scrubs `CI`/`AW_NONINTERACTIVE` and uses `--interactive` with piped stdin; prompt shape follows `cli._confirm` and `term.yes_no_suffix`. |
| PR-008 | MEDIUM | UNDER-SCOPE | Rubric D/E | `tests/test_orchestrator_status_gate.py`, `test_plan_transition_gate.py`, `test_handoff_ready_gate.py`, `test_check_engine_release_gate.py`, `test_backlog_transition_gate.py` | Validation ran only `test_status_set.py`; the suites pinning the converted gates were not named. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests and V-05 list them; E-05 adds one mixed case per gate. |
| PR-009 | LOW | IN-SCOPE | Rubric G (clarity) | Plan Scope EXCLUDES sentence ("missing `--message` ... IS included" inside the exclusion list) | Self-contradictory scope sentence; also unstated whether a record refused by two gates yields two entries. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope rewritten with explicit whole-command list; one reason per record (first gate). |
| PR-010 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Plan "Approval and execution gate" | Gate lacked invariants, scope-fence declaration wording, conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What exit code does a mixed-gate refusal return? | Max of the refused entries' codes. | Always 1 (breaks reopen/backward tests); first gate's code (order-dependent). | `status_set.run_set_command` gate exit codes; tests cited in PR-001. | yes |
| D-2 | Should this plan wait for `juu1rj`? | Yes, `executed:juu1rj`. | Run in either order (both edit the same branches). | `juu1rj` E-02/E-04; it is approved. | yes |
| D-3 | Prompt under `--agent`/`--json`/`--dry-run`? | Never. | Prompt whenever a TTY exists. | AGENTS.md JSONL contract; `term.is_interactive` fail-closed docstring. | yes |
| D-4 | Declare the flag in `command_surface` `legacy_flags`? | Defer to `wy9aru`. | Declare now (expands scope to a sixth file; spec C5 is SHOULD and to-review). | `command_surface` `set`/`ipd set` declarations omit `--allow-terminal-reopen` today too. | yes |
| D-5 | New rule id for the orchestrator gate's diagnostics? | `status.orchestrator_not_ready`. | Reuse `check.graduation-incomplete` (wrong meaning). | Orchestrator gate currently emits no rule id. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
