- Id: trjfyy
- Status: open
- Blocks-Release: next
- Set: trjfyy
- Priority: high
- Work-Kind: bug
- Summary: spec 25kzda 2.1 retry/correction budget is dormant: plan_retry and retry_budget_remaining have zero production callers, so a failed run item gets no automatic correction attempt

## Workflow history
- 2026-09-05 created (aw backlog): spec 25kzda 2.1 retry/correction budget is dormant: plan_retry and retry_budget_remaining have zero production callers, so a failed run item gets no automatic correction attempt

THE DEFECT. `agent_workflows/run_recovery.py:53-64` states plainly that `plan_retry` and
`retry_budget_remaining` have "ZERO production callers today (only tests)". Verified 2026-09-05:
those two symbols plus `validate_retry_budget` appear in exactly two files in the package,
`run_recovery.py` (definitions) and `tests/test_run_recovery_cli.py`. Neither `oc_runipd.py` nor
`agy_runipd.py` imports `run_recovery` at all.

So the whole correction-budget layer specified by spec `25kzda` 2.1 / 4.1 / 5.5 is DORMANT: the
helpers exist, are tested, and are range-validated (0..10, default 2), but nothing in either shipped
runner ever spends the budget. A failed item today gets zero automatic correction attempts.

WHY THIS IS NOT ALREADY OWNED. Three artifacts touch the budget and none of them closes this:

  * `uyeko5` (approved, pending, runflags-01) registers the `--retry-budget` FLAG and its
    precedence, and freezes it into run state. Its E-04 binds the flag to the range validator; its
    V-04 evidence is entirely parse-level (--help output, out-of-range refused, 0/10 accepted,
    default still 2). Nothing in it demands a failed item be re-attempted. Its Scope-Paths do not
    include `run_recovery.py`. After it executes, `aw oc run --retry-budget 5` will parse,
    validate, and freeze 5, and a failed item will still get zero correction attempts.
  * `dh3us4` (blocked on `uyeko5`) covers ONLY the repository-policy middle precedence tier. It
    explicitly reasons the missing tier is not urgent because "the two shipped tiers give correct
    behavior for every invocation" - i.e. it PRESUMES consumption exists.
  * `sq61qd` (executed) added ONLY the 0..10 range validation, and its own history says both
    helpers "remain DORMANT (zero callers outside their own module)".

Adjacent but distinct: `wyw936` (open, Blocks-Release: next) names the same wiring gap from the
verdict side and would route `correction_required` back to runnable, but its fix sketch never
mentions `plan_retry`, `retry_budget_remaining`, or a bounded budget. These two should be
sequenced together, since a correction route with no budget is unbounded and a budget with no
correction route is dead.

WHAT DONE LOOKS LIKE. A runner-side correction loop that, on a RETRYABLE failure class, spends
budget through the shipped helpers: issues a correction packet containing only the failed
predicates, invalidates stale evidence, and escalates on exhaustion (spec 25kzda 5.5, 4.2, 5.2).
Non-retryable classes must stay non-retryable at every budget. The frozen budget must not change on
resume.

SEQUENCING. Gate this behind `uyeko5`, which owns the flag and the frozen value; wiring consumption
first would have nothing to read the operator's budget from.

DO NOT confuse this budget with an integration-retry count. A correction attempt costs a paid model
turn, which is why the default is 2 (`run_recovery.py:56-64`: "a retry cannot turn failure into
success by mere repetition"). Re-attempting a MERGE costs a `git status` and a `git merge-tree`
and repetition genuinely can succeed, because the blocker is another process's transient dirt. That
one is a separate knob with a much larger default; see the integration-deferral item.
