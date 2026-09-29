- Id: 03aicr
- Status: graduated
- Graduated-To: 03aicr
- Blocks-Release: next
- Set: 03aicr
- Priority: medium
- Work-Kind: bug
- Summary: test_drain_and_cascade_mapped_reasons_rendered_once asserts against live repo state and now fails on a clean tree

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: jefifu
- 2026-09-28 created (aw backlog): Filed while authoring the plan for backlog 3f4ayi: the one bare-suite failure at HEAD 71aee0d3 is an unrelated test coupled to plan 5o1jye's live lifecycle status.

MEASURED 2026-09-28 at HEAD `71aee0d3` while authoring the plan for backlog item `3f4ayi`. A BARE `python3 -m pytest` reports `1 failed, 3034 passed, 2 skipped` and the one failure is unrelated to that item's scope:

    FAILED tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once
    assert not sat
    E   assert not True
    tests/test_dependency_block_reporting.py:122: AssertionError

THE CAUSE IS A TEST THAT ASSERTS AGAINST LIVE REPOSITORY STATE. The test hardcodes `"dependencies": ["executed:5o1jye"]` and asserts the dependency is UNSATISFIED. It passed when written because plan `5o1jye` was then `to-review` in `pending/`. That plan has since been executed and now lives in `.aw/records/plans/executed/`, so the `executed:` predicate it encodes is now legitimately TRUE and the assertion is legitimately false.

Confirmed directly, with the live checkout as `repo`: `dependency_status_detailed` over that item returns `(True, [], {})`.

So `dependency_status_detailed` is CORRECT here and the TEST is wrong: it couples a unit assertion about reason-rendering to the lifecycle status of one real plan in this repository, which means the test's verdict changes when unrelated work executes. It is a time bomb that fires on a healthy tree, and it is firing now.

WHY IT IS A BUG AND NOT A CHORE. A red suite on an unmodified checkout is USER-PERCEPTIBLE: every agent and human running the contract-mandated bare `python3 -m pytest` now sees a failure they did not cause, must stop to investigate whether their own change caused it, and may learn to treat a red summary line as normal. That last effect degrades the very gate the execution contract depends on, since the contract requires pasting actual runner output and comparing it to a baseline. Per AGENTS.md a live bug gates the next release, hence `Blocks-Release: next`.

SUGGESTED FIX: decouple the assertion from live repository state. Either point the dependency token at a synthesized artifact under a `tmp_path` repo root (the test already receives `tmp_path`), or use an id6 that cannot resolve at all so the unmet branch is reached by construction. Do NOT "fix" it by flipping the assertion to match today's state, which would re-arm the same bomb pointed the other way, and do not weaken it to a tautology.

RELATED BUT DISTINCT, so this is not a duplicate: `8mohre` (bug, gated) concerns `derive_item_disposition` MISLABELLING an in-queue unmet dependency as external, and `csjq81` (chore) concerns the reason string printing its token twice. Both were filed at `/plan-review` of plan `5o1jye` and both are about the PRODUCTION reason/disposition text. Neither mentions this test's coupling to live state, and neither would turn the suite green. `5mc38x` (followup) asks the adjacent STANDING-CONVENTION question (loud skip versus synthesize for a test that genuinely depends on the checkout root) and explicitly records that no test in the tree needed the answer at filing time; this item is the concrete instance that does, and its fix should follow whatever `5mc38x` settles.

NOT FIXED while authoring `3f4ayi`'s plan: `tests/test_dependency_block_reporting.py` is not in that plan's Scope-Paths, and that plan's fence is the `aw.agent/v1` field-projection contract. Filed so the failure has a carrier a release gate can see rather than living only in a run log.
