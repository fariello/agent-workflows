# Review findings: plan 3jg79f

- Subject-Id: 3jg79f
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`251cbb822`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` clean after revisions.

Re-verified at review HEAD:
- `run_viewer._unresolvable_target_refusal` at `agent_workflows/run_viewer.py:3381` (plan cited 3392; anchor resolves, line drift only).
- Four `print(json.dumps({"error": err_msg, "exit_code": 2}))` refusals at `run_viewer.py:3578/3586/3594/3606`.
- `parse_since_timestamp` raises `ValueError(f"invalid date, timestamp, or timespec '{spec}'")` at `run_viewer.py:504` (plan cited 3229-3231; anchor resolves).
- Empty-state `if not summaries and not issues_only:` at :3755; `_issue_records` at :3853 with `rec["actual_path"] = str(...)`; `if is_agent:` at :3921 with three `{"kind": "excluded_runs"}` emits.
- `agent_schema.render_jsonl_record` validates before rendering; `validate_agent_record` rejects ANSI escapes and unredacted home paths; `redact_home_paths` does not strip ANSI (probe).
- `validate_agent_record` does not check outcome/exit parity for `summary` records (probe: `outcome: "findings", exit: 0` validates).
- No `RunSummary`, `StepSummary`, or `ArtifactAudit` field collides with envelope keys today (probe over dataclass fields).
- `artifact_audit.py:1364` builds `actual_file = Path(repo_root) / configured_file`, so `actual_path` is always absolute.
- Probe on an empty `git init` repo: `aw runs --issues --agent` printed 0 bytes at exit 0; `aw runs -s -S --agent` printed `{"error": ..., "exit_code": 2}` at exit 2.
- Other `aw runs --agent` consumers: `tests/test_selector_echo_sanitization.py`, `tests/test_agent_record_guard.py`, `tests/test_run_viewer.py` ANSI check around line 1984.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression / honest docs | `agent_workflows/run_viewer.py:3853` `_issue_records` (shared by `--json` :3878 and `--agent`); plan Goal and E-02 "`--json` success output remains unchanged" | E-02 normalizes `actual_path`/`collisions` inside the ONE builder that `--json` also uses, so `--json` `artifact_discrepancies` changes from absolute to repo-relative paths, and a collision stops raising `TypeError`. The plan claimed `--json` was unchanged, had no test for the change, and the docs and changelog did not mention it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-06/V-06 as a declared `--json` change with before/after evidence. Goal, Scope, E-02, E-03(f), E-04, E-05 and the gate order updated. |
| PR-002 | MEDIUM | IN-SCOPE | C. Correctness | plan Proposed changes item record `{"schema", "kind", "cmd", **_sanitize_agent_value(item_payload)}` | Payload keys were merged AFTER the envelope, so any future payload field named `kind`, `schema` or `cmd` would silently overwrite the envelope and produce a wrong or invalid record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Envelope keys now come last, so they win. E-02 states this explicitly. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing / G. Executability | `agent_schema.validate_agent_record` rejects ANSI; `redact_home_paths` leaves ANSI (probe) | E-02 named the helper `_sanitize_agent_payload` while Proposed changes named it `_sanitize_agent_value`, and only the Proposed changes text mentioned ANSI stripping. Without a test, a persisted step `summary` carrying ANSI would make `render_jsonl_record` raise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | One name, `_sanitize_agent_value`, now used throughout. E-02 requires both home-path redaction and ANSI stripping, and E-03(d) adds a home-path plus ANSI fixture. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Contract semantics | `command_surface` `runs` `exit_contract=(0, 2)`; human `--issues` and `--json` paths return 0 with issues; `docs/cli-output-contract.md` Section 11.1 (`findings: 0` on clean) | The plan emits `outcome: "clean"`, `exit: 0` with `findings: N>0` and never explains why. A consumer could reasonably read `findings > 0` as a nonzero verdict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added OQ-03 (resolved): keep clean/0 to preserve the declared exit contract, and document that `findings` is count data. E-04 must say so. Adopting the findings exit is left as a separate maintainer decision. |
| PR-005 | LOW | UNDER-SCOPE | E. Validation coverage | `tests/test_selector_echo_sanitization.py:202-245`, `tests/test_agent_record_guard.py:325-340` | The targeted validation list left out two suites that drive `aw runs --agent`. V-03 accepted "0 failures" on the bare suite without a rule for failures that already existed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both suites added to Required tests and V-03. V-03 now requires showing any bare-suite failure fails at the base commit too, and naming the new tests. |
| PR-006 | LOW | IN-SCOPE | G. Plan hygiene | plan Proposed changes "Wait: let's check whether ..."; stale line refs (3392-3421, 3229-3231) | Leftover authoring notes and drifted line citations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed the notes and corrected the line citations (the anchors already resolved). Added F-06 with the review probe. |
| PR-007 | LOW | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate told the executor to run `aw ipd finalize` unconditionally. It also lacked the scope fence, the honesty rule, and the commit and no-push rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Wrote a full execution contract with conditional runner or executor finalize ownership. OQ owners set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What outcome/exit does the `aw runs --agent` summary carry when issues exist (OQ-03)? | `clean` / `0`, with `findings` as count data | `findings` / exit 1 (changes the declared `exit_contract=(0, 2)` and every existing read-path exit) | `agent_workflows/command_surface.py` `runs` declaration; `run_viewer.py` `--json`/human `--issues` `return 0`; plan Goal "all exit codes" | yes |
| D-2 | Normalize `_issue_records` paths for both surfaces or only `--agent`? | Both (shared builder), declared as a `--json` change | Normalize only in the `--agent` branch (two builders, which r2i1b1 E-04 rejected so the surfaces cannot disagree) | `run_viewer.py:3853` docstring "ONE builder for `--json` and `--agent --issues`" | yes |
| D-3 | Envelope-first or payload-first merge for item records? | Payload first, envelope last (envelope wins) | Envelope first (payload can clobber `kind`) | `renderers.AgentRenderer.render_item` shape intent; validator requires `kind`/`cmd` | yes |
