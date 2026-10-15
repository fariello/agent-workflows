# Review findings: plan ksmdcd

- Subject-Id: ksmdcd
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`6fe0e0a4d`), so no snapshot was needed. `aw ipd lint --phase author` was clean before and after the revisions. Pre-transition lint shows only the expected not-yet-executed `IPD-S404` items, and both Deferred rows carry `Carrier:`.

A throwaway in-process probe was run under the gitignored `.aw/state/` and then deleted. It drove `tests.test_usage_refusal_agent_record._capture_cli`.

Current behavior:

- All 67 of the 67 `REQUIRED_LEAVES` exit 2 and emit `findings` under `--agent --fields cmd`, and none of them fails to refuse. This confirms F-01.
- Every edge case in E-04 currently emits `findings`.
- `--json --fields cmd` prints a pretty-printed multi-line object. Its keys are `changes, command, complete, data, diagnostics, evidence, exit_code, next_actions, schema, status, summary, verified`.

Simulated fix (sniffed `fields` injected into the AGENT `OutputContext` with the plan's exact rules):

- 0 of 67 leaves unhonored, and every record passes `validate_agent_record`.
- `findings` is absent for `--fields cmd`, global-flag position, `--fields=cmd` on `ipd set`, `nosuch`, `ipd nosuch`, `status --nosuchflag`, and `--fields cmd,findings --fields cmd`.
- `findings` is retained for no `--fields`, bare `--`, a trailing `--fields`, `--fields --agent`, `--fields cmd,findings`, `--fields=cmd,findings`, and `--fields cmd --fields cmd,findings`.

The `-k` selections were checked with `--collect-only`. The old V-03 expression `ipd_scaffold or research_new or storage_move or known_broken` collects only the 2 ceiling tests. The parametrize ids contain spaces, for example `test_fields_flag_honored_mutation[ipd scaffold]`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Verification feasibility | `--collect-only -k "ipd_scaffold or research_new or storage_move or known_broken"` -> `2/169 tests collected`; ids are `test_fields_flag_honored_mutation[ipd scaffold]` | The V-03 selection never ran the four retired leaves, so it could pass without proving them. The E-01/V-01 `-k "fields"` selection was over-broad and lacked `-rx` to show XFAIL. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced it with `-k "(fields and mutation and (scaffold or research or move)) or known_broken"` (verified to collect them), added `-rx`, and added `-o addopts=""` to the narrowed runs. |
| PR-002 | MEDIUM | IN-SCOPE | E. Test precision | probe: `--json --fields cmd` stdout is a multi-line object; `test_usage_refusal_agent_record.py:118` uses `json.loads(out)` | "Unprojected `--json`" had no observable criterion, and a last-line parse would fail on the pretty-printed object. Repeated `--fields` was asserted in one order only, which cannot distinguish last-wins from first-wins. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The `--json` case now parses the whole stdout and asserts the full payload keys. Last-flag-wins is asserted in both orders, and the agent-record parsing and validation rule is stated. |
| PR-003 | MEDIUM | IN-SCOPE | E. Mutation sensitivity | E-04 mutation text; `test_fields_flag_honored_mutation` uses `run_cli` (subprocess) | The mutation demanded that "the file" fail without saying which cases. Presence-side cases are expected to keep passing. The mutation has to be on disk for the subprocess sweep to see it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named the projection-side cases that must fail and the presence-side cases that must pass. Required an on-disk mutation that is never committed. V-04 is aligned. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` item 5; OQ-01 `Owner: none` | The gate told the executor to run `aw ipd finalize` unconditionally, which is wrong under the runner. It also had no `aw ipd begin`, no `--by-human` approval, no staged-set check, no never-tag rule, and no guidance on the siblings that edit the same `KNOWN_BROKEN` dict. The owner was a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Finalize ownership is now conditional (runner or by hand). Added the missing steps and sibling-merge guidance for `83ns86` and `pirm70`. Owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept the sniffing rules (stop at `--`, last-wins, skip a value starting with `-`)? | Yes; demonstrated by the review probe on every edge case | Reuse argparse partial parsing (cannot run inside `error()` without re-entrancy) | Review probe; `cli._sniff_mode_from_raw_argv` precedent | yes |
| D-2 | Accept OQ-01 (malformed `--fields` stays unprojected)? | Yes, as authored | Project to an empty field set | Probe: trailing `--fields` and `--fields --agent` both yield a valid record with `findings` retained | yes |
| D-3 | Accept dropping `assert seen_citations`? | Yes | Keep it (it would break whichever sibling lands last) | Siblings `83ns86` E-07 and `pirm70` E-05 make the same change | yes |
