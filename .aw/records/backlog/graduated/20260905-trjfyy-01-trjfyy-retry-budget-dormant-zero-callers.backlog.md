- Id: trjfyy
- Status: graduated
- Blocks-Release: next
- Set: trjfyy
- Priority: high
- Work-Kind: bug
- Summary: spec 25kzda 2.1 retry/correction budget is dormant: plan_retry and retry_budget_remaining have zero production callers, so a failed run item gets no automatic correction attempt

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan xipfy1 (Set retrywire, .aw/records/plans/pending/20260908-retrywire-01-xipfy1-...ipd.md), which carries From-Backlog: trjfyy and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done. THE SEQUENCING GATE THIS ITEM SET IS NOW SATISFIED, which is the main change since filing: it says 'Gate this behind uyeko5, which owns the flag and the frozen value; wiring consumption first would have nothing to read the operator's budget from.' uyeko5 is now EXECUTED (.aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md), so the flag, its precedence and the frozen effective value all exist and the plan has something to read; that is why the plan carries Item-Dependencies: none rather than an unmet edge. THE DORMANCY CLAIM STILL HOLDS, re-verified 2026-09-08 at HEAD a2e0438a by symbol search rather than by this item's line numbers: plan_retry (run_recovery.py:269) and retry_budget_remaining (:415) appear ONLY in their own module and in tests/test_run_recovery_cli.py, so a failed item still gets zero automatic correction attempts. ONE CLAIM IN THIS ITEM IS NOW STALE and is corrected here so nobody re-derives it: the item says plan_retry, retry_budget_remaining AND validate_retry_budget all have zero production callers. validate_retry_budget (:136) NOW HAS ONE, runner_shared.resolve_retry_budget (:1764), added by uyeko5. So the RANGE CHECK is wired and only the two SPENDING helpers remain dormant; the plan is narrowed to consumption accordingly and explicitly excludes the 0..10 bound (already shipped by executed sq61qd) and the flag surface. ALSO VERIFIED, because a consumption loop depends on it: the frozen value is resolved to its EFFECTIVE integer at freeze time (runner_shared.py:1836-1837) precisely so no later reader re-resolves it differently, which is exactly the property needed to keep a resumed run's budget stable, and 0 is a LEGAL budget meaning no retries (run_recovery.py:69-70 warns a falsy check must not treat it as unset), so the plan requires an is-None guard rather than a truthiness one. THE ADJACENT ITEMS ARE STILL DISTINCT AND STILL DO NOT CLOSE THIS, re-checked: dh3us4 covers ONLY the repository-policy middle tier and is blocked, and its own reasoning PRESUMES consumption exists; sq61qd (executed) added only the range validation and its history says the helpers 'remain DORMANT'. THIS ITEM'S ORDERING NOTE ABOUT wyw936 IS PRESERVED AS THE PLAN'S BLOCKING OPEN QUESTION rather than absorbed: wyw936 is still open with no plan, and I verified its fail-open is live (the verdict gate downgrades only on BLOCKED or NOT CONFORMING, and the schema's own CORRECTION_REQUIRED appears nowhere outside the prompt string), so a correction route with no budget is unbounded and a budget with no correction route is dead, exactly as this item argues. The plan's E-01 defines an ALLOWLIST of retryable classes rather than a denylist, specifically because failed-safely is documented as conflating a driver error with a possible DELIBERATE OPERATOR STOP (oc_runipd.py:5852-5853), and retrying an operator's stop would spend paid model turns fighting them. The item's warning not to confuse this with an integration-retry count is honored and recorded as out of scope.
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
