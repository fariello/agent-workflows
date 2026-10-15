# Review findings: plan f0kolj

- Subject-Id: f0kolj
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged at HEAD `0b1d53791`, so no snapshot was needed. `aw ipd lint --phase author` was clean before the review and `--phase review-finalize` is clean after it.

Evidence re-verified at review:

- `git merge-base --is-ancestor 44696b524 HEAD` returns 0. `cli._run_check`'s `if getattr(args, "source_anchors", False):` branch derives `rule_sev = ce.rule_spec("check.spec-anchor-stale").severity` and `exit_code = core.drift_exit_code(diagnostics)` (F-01 holds).
- `python3 -m agent_workflows check --source-anchors --agent` and `... check specs --source-anchors --agent` on the real tree both exit 0 with empty stderr and `outcome: "clean"`, `findings: 0`. The live count is 0 at this HEAD, not the 1 that backlog `g3ropl` recorded.
- `pytest --co tests/test_spec_citation_anchors.py` collects 13 tests.
- Prototype of test_g (subprocess, `--verbose`, two-block fixture): rc 0, empty stderr, `outcome: conforms`, `exit: 0`, `findings: 2`, `findings_by_severity {"error":0,"warning":0,"info":2}`, both evidence statuses `conforms`, `rules.value {"errors":0,"warnings":0,"info":2}`, and one attributed plus one unattributed `info` diagnostic.
- Prototype of test_h (in-process `cli.main`, registry `_replace(severity="error")`, one-anchor fixture): rc 1, empty stderr, `outcome: findings`, `exit: 1`, `findings_by_severity {"error":1,...}`, both evidence statuses `findings`, `rules.value {"errors":1,"warnings":0,"info":0}`.
- `agent_schema.validate_agent_record` returns `[]` on the test_h record. With `exit` forced to 0, it returns `["Exit code mismatch: exit=0 incompatible with negative outcome 'findings'"]`, which is the original `g3ropl` crash predicate.
- No artifact other than this plan carries `From-Backlog: g3ropl`, so this plan is the sole HANDOFF carrier (F-02 holds).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Verification feasibility | E-01 and V-01 "`aw check --source-anchors --agent` ... empty stderr"; the `aw` console script in a lane prints "aw: invoked in checkout ... re-running with ..." on stderr (observed at review) | The demand for empty stderr from the `aw` spelling cannot be met inside a lane worktree, because `checkout_pin.check_and_reexec` emits its re-exec notice there. An honest executor would have to record V-01 as failed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and V-01 now use `python3 -m agent_workflows check ...`, which was observed to give empty stderr. If `aw` is used anyway, the re-exec notice is the only stderr allowed. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact criteria (test counts and names as bars) | E-01 "all 13 existing tests"; V-01 "all 13 existing tests `PASSED`"; V-02 and Required tests "visible by name" | A collected test count and test function names are artifacts of test organization. They were used as V-item bars instead of the behavior being pinned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bars are now "every collected test passes (re-derived at execution)". Test names are kept only as non-binding pointers, and V-02 now states the behavior each new test pins. |
| PR-003 | LOW | IN-SCOPE | D. Invariant-to-test mapping | E-02 "a valid `aw.agent/v1` `result` record"; `agent_schema.assert_valid_agent_record` / `validate_agent_record` | The invariant broken in `g3ropl` is the envelope's exit/outcome pairing. The plan named it in Under-scope but never told the tests to assert the validator directly. F-04 also quoted `error: 2` for a fixture that differs from test_h's one-anchor fixture. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | test_g and test_h (E-02) and V-01/V-02 now require `agent_schema.validate_agent_record(rec) == []`. F-04 now records the re-measured one-anchor counts. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the real-tree CLI be invoked so that the empty-stderr demand can be met inside a lane? | `python3 -m agent_workflows check ...` | Keep `aw` and drop the stderr demand (this weakens the crash check); or allow arbitrary stderr | Observed at review: `aw check --source-anchors --agent` printed the re-exec notice on stderr, while `python3 -m agent_workflows` printed nothing and exited 0 | yes |
| D-2 | Should the real-tree command assert a finding count? | No. Require only `clean` or `conforms` and a valid record. | Pin 0 findings (this would be a live-tree census, which the plan's Scope excludes) | Plan Scope "EXCLUDES any live-tree census assertion"; the live count already moved from 1 to 0 | yes |
