# Review findings: plan 2va0jb

- Subject-Id: 2va0jb
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0d3ab57ab` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified (all live probes with `XDG_CONFIG_HOME` pointed at a scratch dir):
- `cli._run_config_exclude(args, term)` and its single caller `return _run_config_exclude(args, term)` in `_dispatch`; fall-through `term.status("fail", "Usage: aw config exclude {add|list|rm} ...")` / `return 2`.
- `config exclude --agent` and `--json`: rc 2, stdout `FAIL     Usage: ...`. `list --agent`: rc 0, `✓ CLEAN  never-install exclude list is empty` + Next. `add <p> --agent`: rc 0, `OK       Added ...`. `rm <nope> --agent`: rc 1, `WARN     No exclude entry matched`. `rm <p> --agent`: rc 0, `OK       Removed ...`.
- `command_surface` declares `config exclude add|list|rm` with `agent_record_kind="result"`; `list` is `read` with `exit_contract=(0, 2)`.
- `EXEMPTION_REGISTRY` has 7 `sanctioned_raw` entries including `config exclude list`; `0qdl9e` is still in `pending/`, and no `FAMILY_ROOT_EXEMPTION_REGISTRY` exists.
- `_emit_config_agent_record` sanitizes via `_sanitize_config_agent_value` and validates via `render_jsonl_record`.
- `_show_family_help` looks `cmd_name` up in the ROOT parser's `choices`; `aw ipd dependencies` (human) prints 229 lines of root help as a result. The `config exclude` subparser's own help shows `{add,list,rm}`.
- Proposed records with `applied` validate (`validate_agent_record` -> `[]`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | F. UX / D. Anti-regression | `cli._show_family_help` `subparser = subparsers_action.choices.get(cmd_name) ... else: help_text = parser.format_help()`; `aw ipd dependencies` human output measured | OQ-02 accepted the root-help fallback, but that turns today's one-line `config exclude {add|list|rm}` hint into about 229 lines of top-level help that never name the subcommands: a human-path regression the plan called acceptable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now routes only the agent branch through the helper, and the human branch prints the `config exclude` subparser's own help plus the `Next` line. OQ-02 revised, E-05(g) and V-01 assert `{add,list,rm}` present and the root `<command> ...` absent. |
| PR-002 | LOW | UNDER-SCOPE | C. Contract conformance | `docs/cli-output-contract.md` §11.3 "Applied mutations emit `applied: true`" | The `add`/`rm` mutation records carried no `applied` flag. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds `applied`, E-05(h) and V-03 assert it. |
| PR-003 | LOW | UNDER-SCOPE | B. Privacy | `_sanitize_config_agent_value`; stored entries are home-relative paths | There was no explicit outcome check that `add`/`rm` records never expose an absolute home path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(i) added. |
| PR-004 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate was missing several contract parts (listed in the resolution), and it implied the item was not yet graduated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now covers: scope as a declaration with `--scope-reason`/`--scope-ack`, an OQ status statement, the do-not-claim-done rule, who finalizes (runner or executor), base-commit attribution of suite failures, and the backlog item being `graduated`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the human bare `config exclude` refusal render? | The subparser's own help plus `Next  aw config exclude list`, exit 2 | Accept the root-help fallback (authored); teach `_show_family_help` nested lookup (changes `ipd dependencies` too, out of scope) | Measured root-help fallback on `ipd dependencies`; the helper's own human shape | yes |
| D-2 | Should `--json` on the bare root emit JSON? | No; it takes the human branch like every sibling root | Emit a JSON dict | `aw config --json` prints help today; root `--json` parity is excluded by `0qdl9e` Scope OUT | yes |
| D-3 | Add `applied` to `add`/`rm` records? | Yes, `applied` only, no `changes` list | Add `changes` with the config path; omit both | `docs/cli-output-contract.md` §11.3; sibling `config-add`/`config-remove` carry no `changes` | yes |
