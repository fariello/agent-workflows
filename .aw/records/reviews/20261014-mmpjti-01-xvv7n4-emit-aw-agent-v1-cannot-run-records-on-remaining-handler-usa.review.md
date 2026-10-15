# Review findings: plan xvv7n4

- Subject-Id: xvv7n4
- Subject-Type: ipd
- Reviewed-At: 2026-10-14
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `eb0787c43`. The plan was committed and byte-identical to the
lane input (sha256 `b9b71593...`), so no pre-review snapshot. `aw ipd lint --phase author`: `conforming`.
Not an orchestrator. Inherits `Blocks-Release: next` and `Work-Kind: bug` from backlog `mmpjti` (checked).

Re-measured by driving `cli.main` in a scratch repo: `backlog new --summary ""` (wired) emits a valid
`aw.agent/v1` error record under `--agent`; `--priority bogus` (unwired) emits `""` on stdout. `specs new
--date 2026-13-45 --agent` emits `""`. `prompts new --kind nope --agent` emits `""`. `ipd scaffold --title ""
--agent` prints `error: --title is required` on stdout. Arm counts match the plan's table (backlog 13 with 2
wired, specs 6 with 1, prompts 6 with 1, scaffold 13 with 0).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E evidence feasibility | `renderers.JsonRenderer.render` (`result.to_dict()`); review probe: `validate_agent_record` on the `--json` output of a wired arm -> `["Invalid kind: 'None' ...", "Field 'cmd' must be a non-empty string"]`; `tests/test_usage_refusal_agent_record.py` `test_required_arg_leaf_json_mode` | E-07 and V-02..V-05 demanded `validate_agent_record` pass under `--json`, which is unsatisfiable: `--json` emits `CommandResult.to_dict()`, not an `aw.agent/v1` record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `--json` assertions now mirror `test_required_arg_leaf_json_mode` (`status`, `exit_code`, `next_actions`); `--agent` keeps `validate_agent_record`. Convention added. |
| PR-002 | HIGH | IN-SCOPE | E evidence feasibility | review probe: `--agent` error record keys `cmd, complete, exit, findings, kind, next, outcome, schema, verified` | E-06 asserted `"embedded newlines" in rec["msg"]`; the record has no message field, so the test as written cannot pass. | Overall:Low | FIXED | E-06 asserts the diagnostic on stderr (existing assertion kept) and adds a human-mode arm. |
| PR-003 | MEDIUM | IN-SCOPE | E reachability | `cli.py` `p_backlog_new` `--status choices=`; `p_ipd_scaffold` `--set`/`--order` `required=True`; `specs.run_new` date regex precedes containment (`tests/test_specs_date_containment.py`) | Four arms (backlog invalid status; scaffold `set_name is None`, `order is None`; specs containment) cannot be reached through `cli.main`, yet V-items demanded CLI-driven evidence for "all" arms. | Overall:Low | FIXED | E-02/E-03/E-05/E-07/V-05 name them and exercise them via direct handler calls or a monkeypatched `resolve_creation_path`. |
| PR-004 | MEDIUM | IN-SCOPE | B leak hygiene | `specs.run_new` containment message (`destination {dest} escapes records tree {specs_dir}`); review probe: `redact_home_paths('/tmp/x/y ...')` leaves `/tmp/x/y` | Routing that message through `emit_usage_refusal` would put absolute non-home paths into machine output. | Overall:Low | FIXED | E-03 requires repo-relative paths in the machine message; E-07 asserts no `tmp_path` string in stdout in every mode. |
| PR-005 | MEDIUM | UNDER-SCOPE | C machine contract | review probe: `ipd scaffold --author 'a (b)' --agent` and a 18-char `--set` print `note: ...` on stdout before the result record (exit 0) | E-05 routed `note:` to stderr only on refusal paths' wording; the success path also pollutes `--agent` stdout, and `_setid_length_guard` has no context to route by. | Overall:Low | FIXED | E-05 covers the success-path notes and threads `ctx` into `_setid_length_guard`; E-07/V-05 add a success-path arm. |
| PR-006 | MEDIUM | IN-SCOPE | G right-sizing / falsifiability | plan E-07 (tests + full suite + sanitize + commit); no RED demand | E-07 bundled authoring tests with suite/sanitize/commit, and no item required the new tests to be shown failing first. | Overall:Low | FIXED | Split into E-07 (tests, RED-then-GREEN) and new E-08/V-08 (suites by node id, sanitize, commit). |
| PR-007 | LOW | IN-SCOPE | G execution contract | plan gate; OQ-01 `Owner: antigravity` | The gate lacked the scope-fence, honesty and conditional-finalize clauses; OQ-01 owner named an agent, not a role. | Overall:Low | FIXED | Gate rewritten; owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What does `--json` refusal output look like? | Keep `CommandResult.to_dict()` (assert `status`/`exit_code`/`next_actions`). | Make `--json` emit `aw.agent/v1` (REJECTED: changes the `--json` contract repo-wide, out of scope). | `renderers.JsonRenderer`; `test_required_arg_leaf_json_mode`. | yes |
| D-2 | Accept the author's OQ-01 (scaffold keeps human `error:`/`note:` on stdout; machine modes move them to stderr)? | Accept, extended to the success-path notes. | Move human output to stderr too (REJECTED: breaks `tests/test_ipd_authoring.py` and `tests/test_ipd_lifecycle_cli.py` stdout assertions). | `IpdLifecycleCliTests.test_run_scaffold_notice_behavior`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
