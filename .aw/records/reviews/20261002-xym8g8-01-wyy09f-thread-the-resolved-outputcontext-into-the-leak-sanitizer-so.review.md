# Review findings: plan wyy09f

- Subject-Id: wyy09f
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `3c97bba81`. The plan was
committed and byte-identical to the sealed lane input (rev-11); no snapshot needed. `- Kind: child`. `aw ipd lint
--phase author` clean before review. F-01..F-04 and F-08 re-reproduced by driving the CLI and renderer against this
worktree (a `/tmp` scratch repo was refused by the lane sandbox). Carriers `mz9id3`, `uxq5mg` open; `9yd6tx` executed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E testing / reachability | `leak_sanitizer.main` machine branch "`if ctx.is_agent or ctx.is_json:` ... `return get_renderer(ctx).emit(res, ctx)`" precedes the human `print(..., file=sys.stderr)` | E-05 step 1 and V-05 block 1 demanded the prose "still on stderr" after the fix; the machine branch returns before any human print, so that demand is unsatisfiable and would force a FAIL on a correct fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten: stdout one parseable payload, no prose; the baseline `No local leaks found.` stderr line must be ABSENT as proof the machine branch ran. |
| PR-002 | MEDIUM | IN-SCOPE | E testing | Measured: `--json` render keys `command, status, exit_code, ...`; `--agent` keys `cmd, outcome, exit` | E-02 asserted `command`/`exit_code` without fixing the key vocabulary; an executor mixing in agent names would write a test that cannot pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the `--json` key set measured at review, adds `status` per tree state and a stream check; F-09 added. |
| PR-003 | MEDIUM | IN-SCOPE | E testing | Measured: `--json --fields cmd,outcome` renders unprojected; `renderers` applies `filter_record_fields` only on agent paths; `--fields` help "for --agent output" | E-03 could be read as also asserting projection under `--json`, which the renderer does not do. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 scoped to `--agent`, with the measured projected set `schema, kind, cmd, outcome, exit, verified, complete, next`. |
| PR-004 | MEDIUM | UNDER-SCOPE | F silent failure / carrier | Measured: `sanitize . --fix --dry-run --agent` rc 0, 0 stdout bytes; non-git dir `--agent` rc 2, 0 stdout bytes; both return before `select_output` | A second no-record defect on the same command, reached by no part of this plan and recorded nowhere. | C:Low; U:Low; S:Low; F:Low; Overall:Medium | FIXED | Filed backlog `k84fqu` (`bug`, `Blocks-Release: next`); Deferred row + F-10; E-04 forbids touching those branches. |
| PR-005 | MEDIUM | IN-SCOPE | Executability | E-05/V-05 "`git status --porcelain` ... clean for both production paths" | After E-04's uncommitted edit (and in a shared checkout) porcelain is non-empty, so the mutation-restore proof was unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with sha256 before-mutation vs after-restore equality. |
| PR-006 | LOW | IN-SCOPE | G execution contract / test hygiene | Gate prose; `tests/test_local_leaks.py` runtime token synthesis and `XDG_CONFIG_HOME` pin | Gate made `aw ipd finalize` unconditional and lacked scope-reason route; E-02 did not require runtime leak-token synthesis (a literal planted leak would trip the repo's own sanitizer), in-process call without cwd change, or XDG pin; E-04 did not say to keep forwarding `--agent`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fix the `--fix`/exit-2 no-record branches here? | No; file `k84fqu` | Widen this plan (three-branch shape change inside a focused release blocker) | `leak_sanitizer.main` control flow; plan Scope | yes |
| D-2 | Assert `--fields` under `--json`? | No, `--agent` only | Assert both (fails: renderer does not project `--json`) | measured render; `--fields` help text | yes |
