- Id: 82cles
- Status: open
- Set: 82cles
- Work-Kind: bug
- Priority: medium
- Summary: Orchestrator review readiness reads Set membership from the companion records root, not the lane, so children authored in a review lane look unauthored
- Short-Description: Orchestrator review readiness reads Set membership from the companion records root, not the lane, so children authored in a review lane look unauthored
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): Orchestrator review readiness reads Set membership from the companion records root, not the lane, so children authored in a review lane look unauthored

## Symptom

Observed 2026-11-21 while authoring plan `wknwwz` for backlog item `es4blt`. In a repository configured with companion records storage (`public-target-private-companion`), `agent_workflows/runner_shared.py::read_set_membership` called with a linked lane worktree as its repository root returns only the Set children stored in the companion records root. A child plan the review agent wrote into the lane at `.aw/records/plans/pending/` is not returned.

Reproduction: the `tests/test_companion_runner_integration.py::_provision_companion_repos` fixture, one child `chc001` in `<companion>/records/plans/pending/`, one child `chl002` written into `<lane>/.aw/records/plans/pending/`, then `read_set_membership(<lane>, "cmpset")`. Observed result: only `chc001`, with its companion path.

## Likely effect (not yet observed end to end)

`agent_workflows/orchestrator_readiness.py::review_readiness` takes Set membership from `_rs.read_set_membership(repo_path, setid)`. When a review correction turn authors a missing child inside the lane, as the correction prompt instructs, the gate would still report `CODE_CHILD_UNAUTHORED` for that child until the lane is integrated. The runner would then spend the correction budget and end in `fail-gate`. This effect was inferred from the code and the reproduction above; it has not been run end to end.

## Relationship to es4blt

Backlog item `es4blt` (plan `wknwwz`) fixes which copy of the ORCHESTRATOR plan file the gate reads. This item covers the separate CHILD membership lookup. `wknwwz` does not change it.

## Acceptance criteria

1. During an isolated review in companion storage, `review_readiness` counts a child plan that exists only in the lane's `.aw/records/plans/` tree as authored.
2. A regression test reproduces a lane-only child and asserts that no `CODE_CHILD_UNAUTHORED` finding names it.
