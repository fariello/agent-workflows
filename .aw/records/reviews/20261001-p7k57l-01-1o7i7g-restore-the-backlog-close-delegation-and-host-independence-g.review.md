# Review: Restore the backlog-close delegation and host-independence guards as behavioral tests

- Subject-Id: 1o7i7g
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean, apart from the advisory `IPD-Z602` on E-05. The plan pre-empts that advisory with a stated one-concern rationale, and the reviewer accepts it.

Re-verified in this lane, with the interpreter reading this tree (`agent_workflows.__file__` resolved inside the worktree):

- Four `SharedNotCopied` citations remain (`oc_runipd.py` x2, `agy_runipd.py` x1, `runner_shared.py` x1), and the test file does not exist.
- The delegation probe gives fake called once, `SENTINEL` returned, and `run_checked is host` True / `is peer` False, for all 8 wrapper/host pairs.
- The 11 re-exports satisfy `oc is agy is runner_shared`.
- In the host-independence subprocess probe, both hosts return `work-ok` with the peer blocked and absent.

The design is sound. The defects were stale premises from sibling work that has since landed, two orphaned carriers, and one under-specified injection assertion.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Traceability | plan Scope, Deferred row 5, Scope check, gate: "which V-05 proves by AST comparison" | The AST comparison is demanded by V-06 (E-06's validator), but five places cite V-05. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All five changed to V-06. |
| PR-002 | MEDIUM | IN-SCOPE | Evidence freshness | `.aw/records/plans/executed/20260929-2kspdy-01-nf71bz-...ipd.md`; `agent_workflows/oc_runipd.py:1324` `host_label=runner_shared.OC_HOST_LABELS.command`; `tests/test_backlog_close_host_label.py` | The plan treats `nf71bz` as "approved", not landed. It is EXECUTED. `host_label` is now a fourth required kwarg, so mutation (1)'s expected TypeError text ("missing 3") is stale, and the 2kspdy deferred row carries no Carrier-Evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Prose updated, Carrier-Evidence added, and mutation (1) re-measured ("missing 4"). The TypeError is the bar, not the count. |
| PR-003 | MEDIUM | UNDER-SCOPE | Testing (D/E) | `agent_workflows/oc_runipd.py` `process_backlog_close` passes `run_checked`, `close_backlog_item`, `commit_backlog_close`, `host_label`; design note "four in-tree tests patch `oc_runipd.close_backlog_item`" | E-03(c) asserted only `run_checked`. `process_backlog_close` injects FOUR host-varying values, and a wrapper passing the peer's closer or label, or an import-time-bound closer that bypasses spies, would pass every E-03 assertion. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03(c) now also asserts the closers are this host's and late-bound (spy reaches the fake), and that `host_label` is this host's. All three were re-driven and pass at review. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence feasibility (reachability) | review subprocess probe: finder consultation list contains the host and many `agent_workflows.*` modules but never the peer on a clean tree | V-04 suggested "the peer name recorded by the finder" as evidence that the finder was consulted. On a clean tree the peer is never requested, so that evidence is unobtainable in the passing case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now records consultations and asserts the HOST is among them. V-04 demands that list plus the E-05(5) `PEER BLOCKED` text. |
| PR-005 | HIGH | UNDER-SCOPE | Carrier integrity | `check.ipd-carrier-finished-unverified` on this plan; `xvp5vx` is `done`; `.aw/records/plans/executed/20260930-xvp5vx-01-oyh28b-...ipd.md` lists `p7k57l` as already-owned and did not re-file | Two deferred rows and OQ-01 named `xvp5vx` as carrier, but it is finished. Its census treated this file's residual as OWNED by `p7k57l`, so the 2703-line residual had no owner. The checker row's real carrier is `j7daih`, filed by `oyh28b`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Filed backlog `yf1p8y` for the residual. Residual row -> `yf1p8y`; checker row and OQ-01 -> `j7daih`. `aw check plans` no longer reports this plan. |
| PR-006 | LOW | UNDER-SCOPE | Under-scope disclosure | `agent_workflows/runner_shared.py` block "THE RE-HOMED HOST-NEUTRAL NAMES": "`tests/test_runner_layering.py` now freezes"; "`tests/test_runner_shared.py::ReHomedHostNeutralNameTests` proves it" (no such class) | The same file has two more dangling-guard claims about the same layering move, and the plan does not mention them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a deferred row carried by `yf1p8y`. E-06 is told not to edit them, so its four-site scope holds. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who carries the residual test_runner_backlog_close.py coverage now that xvp5vx is done? | File new backlog `yf1p8y` | Carrier-Declined, which is false because work remains; point at `e486tz`, which covers UNCITED files only and this file is cited | oyh28b deferred section lists p7k57l as owned; `e486tz` summary "uncited in comments" | yes |
| D-2 | Carrier for the dangling-citation checker row and OQ-01 | `j7daih` | Keep `xvp5vx`, which is finished and so fires the check | `.aw/records/backlog/open/20261001-j7daih-...backlog.md` summary | yes |
| D-3 | Should E-06 also fix the two extra runner_shared.py stale claims? | No; defer to `yf1p8y` | Widen E-06, which breaks the plan's measured four-site scope and its V-06 grep bar | plan Scope "the four `SharedNotCopied` citations" | yes |
| D-4 | Should E-03(c) cover all four injected values? | Yes | run_checked only | `oc_runipd.process_backlog_close` kwargs, re-driven at review | yes |
