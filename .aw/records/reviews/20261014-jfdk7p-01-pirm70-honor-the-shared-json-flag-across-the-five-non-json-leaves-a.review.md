# Review findings: plan pirm70

- Subject-Id: pirm70
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`cf2cdd310`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review. `--phase review-finalize` is clean after the revisions. `--phase pre-transition` now reports only the expected not-yet-executed `IPD-S404` states, and the carrier error is cleared.

Baseline at HEAD `27826fbac`, driven with `--json`:

- `config get interactive` -> rc 2, stdout `FAIL     Unknown config key 'interactive'...`
- `config is interactive` -> rc 2, stdout `FAIL     Missing variable name...`
- `upgrade-test env dummy` and `upgrade-test probe dummy` -> rc 2, empty stdout, stderr `error: not a sandbox ...`
- `upgrade-test clean --root <empty>` -> rc 0, stdout `Nothing to clean.`

This confirms F-01 through F-04.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | B. Security / privacy | `agent_workflows/upgrade_rehearsal.py:627` `env = dict(os.environ)` in `sandbox_env`; review probe: 99 keys, planted `AW_FAKE_SECRET_TOKEN` present | E-03 (2) would print `json.dumps({"sandbox": ..., "env": env})`, which dumps the operator's whole environment, secrets included, to stdout. The `--agent` branch is safe only because the compact record drops `data` (the planted secret was absent even with `--agent --verbose`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-06. The `--json` branch now emits only the three keys the human branch exports. E-04 adds a planted-sentinel test, and V-03 demands that evidence. |
| PR-002 | MEDIUM | IN-SCOPE | C. Architecture (reuse canonical mechanism) | `agent_workflows/renderers.py:384` `def emit_usage_refusal(` (6 callers); review demo printed `"status": "cannot-run", "exit_code": 2, "summary": "... ~/x"`; existing ad-hoc shapes at `cli.py:12492`, `run_cli.py:541`, `run_viewer.py:3578` | The plan invented a new `{"command","error","exit_code"}` shape and a new `_emit_json_error` helper. The repo already has a canonical cannot-run emitter for `--json` that redacts `summary` and matches the `CommandResult` contract (`docs/cli-output-contract.md` Section 2). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02, E-03, Proposed changes and OQ-01 now delegate to `renderers.emit_usage_refusal(..., select_output(args))`. The new helper is removed. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `agent_workflows/upgrade_rehearsal.py:1607` `sub = parser.add_subparsers(dest="command", required=True)` | Proposed `main` code used `args.cmd`, which does not exist, so `main` would raise `AttributeError` inside the exception handler. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now uses `getattr(args, 'command', '')`, matching the existing `--agent` branch. |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation 2 obligation(s) name no durable carrier: deferred row 1, deferred row 2` | Both Deferred rows lacked carriers, so the plan could never finalize. Row 2 also misdescribed `4y614a` as two `--no-color` entries; `tests/test_shared_flag_honored.py:71-75` shows four `--fields` entries. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `Carrier: 83ns86` and `Carrier: ksmdcd` (pending IPD with `From-Backlog: 4y614a`), and corrected row 2. The carrier error is gone at pre-transition. |
| PR-005 | MEDIUM | IN-SCOPE | G. Execution contract | old `## Approval and execution gate` "moving the completed plan to `executed/` via `aw ipd set executed pirm70`" | The gate told the executor to move the plan with `aw ipd set executed` (not the lifecycle verb), with no runner/hand ownership split, no honesty rule, no scope fence, and no never-push rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced it with the standard execution contract (conditional `aw ipd begin`/`finalize` ownership, path-scoped `aw commit`, never push, paste the runner output, a scope fence with `--scope-reason`, and mutation-proof restore before commit). |
| PR-006 | LOW | UNDER-SCOPE | G. Docs sync | `CHANGELOG.md:7` `## 2.0.0 (pending)` with sibling `Fixed:` bullets | A user-visible bug fix carried no release-notes line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05/V-05 and `CHANGELOG.md` to Scope-Paths. |
| PR-007 | LOW | IN-SCOPE | E. Evidence accuracy | `agent_workflows/agent_schema.py:168` `redact_home_paths` rewrites to `~`; `OQ-01` cited a "legacy/data-only" Section 1 phrase that does not appear in `docs/cli-output-contract.md` | The tests were told to assert a `<home>` token that redaction never produces, and the OQ cited a nonexistent contract phrase. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Assertions now require the absence of `/home/` and `/Users/` and a `~` redaction. The OQ was rewritten on real evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `--json` refusal shape for config and upgrade-test? | Canonical `renderers.emit_usage_refusal` `CommandResult` document | Authored ad-hoc `{"command","error","exit_code"}` object | `renderers.py:384`; contract Section 2; review demo | yes |
| D-2 | What may `upgrade-test env --json` expose? | Only `XDG_CONFIG_HOME`, `AW_HOME`, `GIT_TERMINAL_PROMPT` (the human export set) | Full `sandbox_env` dict (leaks the environment); a redacted full dict (still leaks non-path secrets) | `upgrade_rehearsal.py:627`; human branch key tuple in `cmd_env` | yes |
| D-3 | `clean --json` empty-branch shape? | `[]`, same list type as the `-y` branch | `{"results": []}` mirroring `--agent` | `cmd_clean` `-y` branch prints `json.dumps(results)` | yes |
