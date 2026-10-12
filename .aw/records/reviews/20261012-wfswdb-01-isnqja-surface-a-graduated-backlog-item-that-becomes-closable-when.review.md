# Review findings: plan isnqja

- Subject-Id: isnqja
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `68ae3dd07` in an isolated review lane. The plan was committed and unchanged (`2c123ead7`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified (probe under gitignored `.aw/state/`, since deleted):
- These symbols exist as cited: `check_engine.release_gate_warnings`, `_from_backlog_carrier_index`, `_carrier_is_executed`, `_status_meta`, `_read_item_id`, `rule_spec`, `resolve_evidence_artifact`, `check_graduation_incomplete`; `backlog._iter_items`; the `attention.run` release-gate block with its `"\n    Fix:"` partition and color 214. `release_gate_warnings` is consumed by `attention`, `production_checks` and `runner_shared` (twice), as F-05 says.
- An unregistered rule defaults to `error` (`_DEFAULT_RULESPEC`), so registration at `info` (E-03, case 9) is load-bearing.
- Census at this HEAD: 100 graduated items, 0 with all carriers terminal, and the graduated items with a spec carrier are `ms06pi` and `fcnz1r`. F-04's "61" has drifted, which is fine because E-01 re-derives it. `_from_backlog_carrier_index` took 0.41 s warm.
- Fix command: in a scratch repo, `aw backlog set bk0001 --status done --evidence <executed plan> --no-commit` exits 0 and moves a `graduated` item to `done/` in all three cases: same-gate carrier, different-gate carrier, and ungated item. This confirms F-07 and E-03's `--evidence` rationale.
- Pending sibling `0owirm` (gradfix) defers the `graduated` population to this plan by name.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing | plan E-03 "WHY `--evidence` IN THE FIX ... HANDOFF alone would refuse a gated item whose terminal carriers carry a different gate"; E-02 (7) tests only a same-gate item | The case E-03 gives as the reason for `--evidence` (a carrier with a different gate) was untested, so a regression there would leave a Fix line that does not work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 (7) now also runs the Fix command with a different-gate carrier (measured at review to work). |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Anti-regression | plan Scope "OUT ... the JSON/agent attention renderer"; E-04 "must not add to ... the JSON output, or the exit code"; E-02 (8) compares only the default exit code | The "human-view only" and "never affects `--check`" claims had no test, so the section could leak into `--agent` output or change `--check` without failing anything. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 (8) now also compares return codes under `--check` and asserts the rule id is absent from `attention --agent` stdout. |
| PR-003 | LOW | IN-SCOPE | G. Live criteria / coordination | V-05 "showing 9 passed"; pending `0owirm` predicate `backlog_item_already_complete` | V-05 used a test count as its bar. The plan also did not mention its sibling's overlapping predicate, whose "at least one IPD carrier" rule differs from this plan's non-empty-carrier rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now demands a per-case `-rA` listing. Added F-08 plus a Deferred entry recording the deliberate difference and why convergence is out of scope. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status line, the MUST-paste honesty rule, `aw ipd begin`, the concrete commit command, and the statement that the executor must not finalize under a runner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All of those elements are added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Align this predicate with `0owirm`'s "at least one IPD carrier" rule? | No: keep the non-empty carrier list (surfaces spec-only items) | Require an IPD carrier (would hide `ms06pi`-shaped items, which are the subject of the backlog item) | scratch probe: a spec-only close via `--evidence` works; `wfswdb` concerns spec carriers | yes |
| D-2 | Accept OQ-01 (attention surface rather than a setter-side close)? | Yes, as authored | Hook `aw specs set implemented` (third close predicate, covers one route) | `runner_shared.process_backlog_close` docstring; F-01/F-02 | yes |
