# Review findings: plan qrzowp

- Subject-Id: qrzowp
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `461fdf679`. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` clean after revisions.

Re-verified at review HEAD with throwaway temp-repo probes (nothing written to the tree):
- `RETIRE_REFUSED_*` = `unfinished-children`, `no-children`, `unauthored-child-rows`, `no-orchestrator`; `ORCH_REASON_UNFINISHED_CHILDREN = "children-unfinished"`.
- Decision mapping: `no-orchestrator -> terminate no-orchestrator`, `no-children -> terminate no-children`, `unauthored-child-rows -> terminate unauthored-child-rows`, `unfinished-children -> reconsider children-unfinished`; none hit the fallback text.
- The unauthored-row branch is masked by a non-terminal child (approved child + 2-row table -> `unfinished-children`), confirming the plan's ordering note.
- The table heading must be `## Child IPDs, sequence, and dependencies` (`runner_shared._CHILD_IPDS_HEADING`). With `## Child IPDs`, even an all-executed Set refuses `unauthored-child-rows`, so an unauthored-row subtest would pass for the wrong reason.
- `dispatch_orchestrator_item` on the unfinished fixture -> `reconsider`, item stays `queued`, `refusal_of_item` code `children-unfinished`, not the fallback.
- `orchestrator_refusal_text("unfinished-children" | "some-future-reason" | "" | None)` all return the fallback; `""`/`None` contain `(no reason recorded)`; the remedy contains `events.jsonl`. `Refusal(code="", ...)` raises `ValueError`.
- A mutation that makes the fallback raise `KeyError` raises for all three unknown inputs.
- `aw ipd lint --phase pre-transition` reported `check.ipd-uncarried-obligation` for all 3 deferred rows.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Test validity | `agent_workflows/runner_shared.py:19072` `_CHILD_IPDS_HEADING = "Child IPDs, sequence, and dependencies"`; `parse_declared_child_orders` | E-01 told the executor to write a `## Child IPDs` table. That heading is not parsed, so the unauthored-row subtest would refuse for "unparseable table" instead of "missing child", and pass vacuously. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 names the exact heading and row shape, and adds an eligible control subtest proving the table parses. |
| PR-002 | HIGH | UNDER-SCOPE | G. Lifecycle | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier` | All three Deferred rows lacked a carrier, so the plan could never finalize after a successful execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each row now carries `Carrier-Declined` with a reason. The pre-transition lint now reports only the expected not-yet-performed items. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Sensitivity | plan Required tests (a mutation check for S-10 only) | Nothing proved the S-11 fallback tests could fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added mutation check B (fallback raises `KeyError`, which the probe confirms raises for all inputs). V-03/V-04 demand it, plus an empty `git diff -- agent_workflows/` after revert. |
| PR-004 | MEDIUM | IN-SCOPE | E. Test correctness | `render_stream.Refusal.__post_init__` (empty field raises `ValueError`) | E-04 asked for a `Refusal` built from the `""` case. Passing `""` as `code` raises, so the test as literally written would fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now specifies a non-empty code for the record. |
| PR-005 | LOW | IN-SCOPE | E. Coverage strength | plan E-01, E-02 | E-01 asserted only "reason differs from input", which is vacuous for three branches whose values are identical in both vocabularies. Neither item asserted the dispatch outcome. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now asserts the expected `ORCH_REASON_*` and outcome per branch (mapping measured at review). E-02 asserts RECONSIDER and an unchanged `queued` status. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; OQ-01 `Owner: none` | The gate lacked the honesty rule, a bare-suite rule, a scope-fence declaration, OQ status, the mutation no-commit rule, and conditional finalize ownership. Owner was `none`. The unittest dual-runner check was absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten. Owner set to `plan author`. V-04 runs the module under `python3 -m unittest`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How do we close the uncarried Deferred rows? | `Carrier-Declined` with reasons | File three backlog items (two are out of scope by the backlog's own statement, and one is prohibited by P16) | `.aw/records/plans/README.md` carrier escapes; AGENTS.md P16 | yes |
| D-2 | What is the second mutation for S-11? | Fallback raises `KeyError` | Return an empty string (`Refusal` would then raise anyway, giving a weaker signal) | review probe: raises for all three unknown inputs | yes |
