- Id: a3ugp1
- Status: open
- Blocks-Release: next
- Set: a3ugp1
- Priority: high
- Work-Kind: bug
- Summary: The approval gate refuses three pending reaskscore plans on a stale negative verdict, failing tests/test_plan_readiness.py at HEAD

## What is wrong

`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`
FAILS at HEAD `c58ec3ab`, naming three live pending plans:

```
AssertionError: Lists differ: [...] != [] : pending plans falsely refused on their verdict
  '20260919-reaskscore-00-s0gnha-stop-a-completed-turn-being-scored-as-partial-and-cascading.ipd.md'
  '20260919-reaskscore-02-ty7w6o-record-a-host-truncated-agy-turn-as-truncated-instead-of-acc.ipd.md'
  '20260919-reaskscore-04-svacmz-prove-the-composed-reaskscore-fix-against-both-measured-shap.ipd.md'
```

`plan_readiness.newest_verdict` returns `negative` for all three. Measured directly:

```
s0gnha negative '- 2026-09-19 reviewed (...): /askme: OQ-03 RESOLVED FROM THE REPOSITORY WITHOUT ASKING, ... clearing this plan's only blocking question and with it its `no-go`. ...'
ty7w6o negative '- 2026-09-19 reviewed (...): /askme: OQ-04 RESOLVED BY THE MAINTAINER, clearing this plan's only blocking question and with it its `no-go`. ...'
svacmz negative '- 2026-09-19 reviewed (...): /askme: OQ-02 RESOLVED VIA THE RECOMMENDED SHAPE (a), clearing this plan's only blocking question and with it its `no-go`. ...'
```

So the NEWEST history entry on each plan is the one RESOLVING the blocking question, and it is
classified negative because it MENTIONS the `no-go` it is clearing. The test's own docstring states
the stakes: "A gate that refuses live, legitimately-reviewed plans is a lockout, not a safeguard."

## Why it matters

The refusal is not merely a red test: the auto-approve predicate reads this verdict, so three plans
whose blocking questions were deliberately resolved cannot be promoted, and a `--full-auto` run will
skip them. This is the same class of defect as a stale negative verdict on a retired predecessor,
which `test_the_three_item_13_successors_are_not_refused` exists to catch (F-5 in that file).

## Where

- `agent_workflows/plan_readiness.py`, `newest_verdict` (polarity classification)
- `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`
- The three `reaskscore` plans named above

## Provenance

Found as a PRE-EXISTING baseline failure while executing plan `z8ddk0` (unrelated scope: the
`should_color` unification). NOT caused by that plan and NOT fixed by it: `z8ddk0` touches only
`term.py`, `runner_shared.py`, `pwatch.py` and their tests, and this failure reproduces on a clean
tree at the same HEAD. Recorded rather than repaired because repairing a verdict classifier is
outside that plan's declared `Scope-Paths` and needs its own review.

## Workflow history
- 2026-09-19 created (aw backlog): The approval gate refuses three pending reaskscore plans on a stale negative verdict, failing tests/test_plan_readiness.py at HEAD
