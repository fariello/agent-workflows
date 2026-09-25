- Id: 7a53rm
- Status: graduated
- Graduated-To: gatesev
- Blocks-Release: next
- Set: 7a53rm
- Priority: high
- Work-Kind: bug
- Summary: aw commit and aw work begin refuse on ANY non-info plan finding, so any advisory warning rule silently acquires commit-blocking authority

## Workflow history
- 2026-09-25 graduated (aw set): graduated into gatesev plan s7cu7n (to-review)
- 2026-09-20 created (aw backlog): Measured while introducing check.ipd-lint (lintreach k9awrq): at warning severity the advisory rule refused aw commit.

## Detail

`work_cmd._validate_plan_via_engine`, which backs BOTH `aw work begin` and `aw commit`, runs
`check_engine.check_type(repo_root, "plans")` and then keeps every finding for the target plan EXCEPT
those whose severity is exactly `info`:

```python
enriched = _ce.enrich_drift(d)
if enriched.severity == "info":
    continue  # advisory nudge, not a blocking finding
out.append(enriched)
```

So the gate's real predicate is "not `info`", which means ANY rule registered `warning` acquires
COMMIT-BLOCKING authority the moment it fires on a plan. That is not what `warning` is documented to
mean anywhere else in the engine: `check.review-decision-unescalated`'s own `RuleSpec` comment states
that what the tier buys is that it "adds no LIFECYCLE gate", and plan `k9awrq`'s F-14 reached the same
(false) conclusion from `artifact_core.drift_exit_code`, which really does exempt only `info`.

MEASURED, not theorized. While introducing `check.ipd-lint` (an advisory whole-family lint umbrella)
at `warning`, `aw commit` began REFUSING with `aw commit: refusing - 1 finding(s) on
<plan>.ipd.md: check.ipd-lint: 9 IPD-* lint diagnostic(s)...`, breaking four tests in
`tests/test_work_primitives.py` (`test_commit_only_in_scope_paths`,
`test_commit_delegates_to_the_one_shared_commit_helper`,
`test_work_begin_validates_and_allocates_worktree`,
`test_work_begin_allocates_through_the_one_shared_worktree_lease`). Direct measurement of the gate:
`severity=warning -> blocks work/commit gate=True`, `severity=info -> blocks=False`.

WHY IT MATTERS. It makes severity a two-value dial (`info` = report, anything else = block commits) at
this gate while the rest of the engine treats it as three, so an author adding a deliberately advisory
`warning` rule silently changes what `aw commit` refuses. `k9awrq` worked around it by registering
`check.ipd-lint` as `info`, which is correct for that rule but leaves the general trap in place for the
next one. Note the two EXISTING `warning` plan-adjacent rules (`check.review-decision-unescalated`,
`check.identity-absent-from-name`) are also reachable in principle; they simply do not fire on the
fixtures that exercise this gate today.

TWO QUESTIONS FOR THE MAINTAINER, which is why this is filed rather than fixed: (1) should
`aw commit` / `aw work begin` gate on plan findings at ERROR severity only, and (2) should they gate on
structural lint at all, given `aw ipd begin` / `aw ipd finalize` already own that checkpoint. Either
answer is a behavior change to a commit path, so it needs a decision rather than a patch from a
reachability plan.

## Evidence

- `agent_workflows/work_cmd.py`, `_validate_plan_via_engine` (the `severity == "info"` skip).
- `agent_workflows/artifact_core.py`, `drift_exit_code` (exempts only `info`; the source of the
  mistaken inference that `warning` is gate-free).
- Plan `k9awrq` DECISION 16-k9awrq-D5 records the measurement and the workaround.
