# Review findings: plan d5ntkj

- Subject-Id: d5ntkj
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REJECT - NEEDS REPLAN

## Round 1

Reviewed at lane HEAD `ce551c597`. The plan was committed and byte-identical to the lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before review. After
revision, `--phase review-finalize` reports only `IPD-Q501` x3, for the three blocking questions
added to escalate PR-001..PR-003. That is the intended fail-closed state for a REJECT.

Driven at review (no production edit; scratch copies only via `tempfile`):
- `runner_shared.edge_satisfied(state:backlog:done:wcbpqf, {"action":"execute"}, {"repo":"."}, {})`
  -> `(False, "state:backlog:done:wcbpqf: backlog wcbpqf is 'graduated', needs exactly 'done'")`.
- `runner_shared.evaluate_backlog_close(repo, "wcbpqf", [<d5ntkj pending>, <d5ntkj executed>], executed_overrides={pending: executed})`
  -> `close=True, reason='every IPD carrier is executed and this run executed .../executed/...d5ntkj...'`.
  `grep -rln "From-Backlog: wcbpqf" .aw/records` -> only this plan.
- Scratch tree with `wcbpqf` in `graduated/` and d5ntkj in `executed/`:
  `aw backlog set wcbpqf --status done --evidence <d5ntkj> --dir <tmp> --no-commit` -> exit 0, item moved to `done/`.
- `runner_shared.enforce_freeze_time_refusal([pi3bk8 execute item with the two edges], repo=.)` ->
  `DriverError: [RUN-DEPENDENCY-UNSATISFIABLE] pi3bk8 requires state:backlog:done:wcbpqf; ... No work started, and nothing durable was created.`
- Tree state: `wcbpqf` graduated (`ab3fc2317`), `hc6n7r` graduated to `carriergate`/`rpw4sb` (`3f29baf48`),
  `x2dwu5` in `executed/`, `pi3bk8` OQ-01 `Status: resolved` (review kept `supports_deny_tcp_port`).
  Spec `25kzda` names `deny_tcp_port` 0 times (confirmed).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness (gate self-release) | `agent_workflows/runner_shared.py:37915` `evaluate_backlog_close`; `:36269` `close_backlog_item`; `:36462` `process_backlog_close`; plan front matter `- From-Backlog: wcbpqf` | This plan is the only `From-Backlog: wcbpqf` carrier. When it executes, the runner's post-execution close closes `wcbpqf` as `done` (driven: `close=True`, and the setter exits 0 from `graduated`). That satisfies `state:backlog:done:wcbpqf` with no maintainer answer, so the gate dissolves itself in the same run that installs it. The plan's own gate text names this hazard ("If the runner would transition `wcbpqf`, that is a finding") but treats it as hypothetical, and nothing in the plan prevents it. | C:High; U:Medium; S:Low; F:High; Overall:High | REPLAN | Escalated as OQ-03 (Blocking: yes). The alternative mechanisms are the maintainer's choice; see OQ-03. |
| PR-002 | HIGH | IN-SCOPE | C. Operability (blast radius) | `agent_workflows/runner_shared.py:19440` `enforce_freeze_time_refusal` section 3; spec `z7nbn1` 1.4 | The plan claims an unmet edge marks just those two plans `dependency-blocked` while the run continues. That holds only for edges that could be met in-run. A `state:backlog:done` edge on an item no run step can close counts as provably unsatisfiable and REFUSES THE WHOLE RUN (driven). Any selection containing a gated approved plan would run nothing. | C:Medium-High; U:High; S:Low; F:Medium-High; Overall:High | REPLAN | Escalated as OQ-04 (Blocking: yes). |
| PR-003 | HIGH | IN-SCOPE | G. Premises stale | `git log` `ab3fc2317`, `3f29baf48`; `.aw/records/plans/executed/...x2dwu5...`; Scope-Paths | `wcbpqf` and `hc6n7r` are `graduated`, not `open`. `x2dwu5` has executed, so its carried OQ-01 already closed unanswered. Two Scope-Paths point at `backlog/open/` files that no longer exist. E-03/E-04/V-03/V-04 assert `open` status, which cannot hold. `hc6n7r` is now carried by plan `rpw4sb`, whose F-08 already measured the `done`-edge mismatch. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium-High (bundled with PR-001 redesign) | REPLAN | Escalated as OQ-05 (Blocking: yes). |
| PR-004 | MEDIUM | IN-SCOPE | G. Premises | `.aw/records/plans/pending/...pi3bk8...` OQ-01 `Status: resolved`, Owner plan-review | Decision (2), the field name, is no longer open: `pi3bk8`'s review resolved it (keep `supports_deny_tcp_port`). The rationale for gating `pi3bk8` (F-02, E-02 "un-ruled name") is therefore stale. Whether that reviewer resolution is enough, or the maintainer must still rule, is a scope question for the replacement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | REPLAN | Recorded in OQ-05 for the replacement author. Not fixed in place, because the plan is being replaced. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Repair the plan in place or reject? | REJECT - NEEDS REPLAN; leave the body as authored | Rewrite to a new decision-item edge (picks OQ-03 for the maintainer); drop From-Backlog (breaks the handoff record) | PR-001/PR-002 driven; the mechanism choice is a human policy call (`hc6n7r`/`rpw4sb` OQ) | yes |
| D-2 | Escalate as blocking questions? | Yes, OQ-03..OQ-05 `Blocking: yes` | Report only | `plan-review.md` Step 4 escalation rule (gate threshold HIGH) | yes |
