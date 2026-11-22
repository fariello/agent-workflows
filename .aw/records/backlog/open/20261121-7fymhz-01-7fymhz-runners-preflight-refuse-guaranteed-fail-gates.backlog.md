- Id: 7fymhz
- Status: open
- Set: 7fymhz
- Work-Kind: bug
- Priority: high
- Summary: aw runners should preflight-refuse items guaranteed to fail-gate before spending agent turns
- Short-Description: aw runners should preflight-refuse items guaranteed to fail-gate before spending agent turns
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): aw runners should preflight-refuse items guaranteed to fail-gate before spending agent turns

## Observed behavior

When running `aw agy run` (and `aw oc run`) over a backlog Set, the runner dispatches agent turns and creates lane worktrees even when a deterministic, pre-existing contract error on `main` or on the queued item guarantees the post-transition gate will refuse the handoff.

### Concrete example

A repository had three open `Work-Kind: bug` backlog items missing `- Blocks-Release:` (violating `check.live-bug-ungated`). `aw agy run` dispatched item 1/6 (`6hp1zu`), spent ~11 minutes and ~365K tokens authoring a complete multi-plan IPD Set in an isolated worktree, and only then failed the post-transition cross-tree check:

```text
[BACKLOG-CROSS-TREE] Backlog handoff violates check.live-bug-ungated: a LIVE (status 'graduated') Work-Kind: bug item carries no - Blocks-Release:
```

Worse, the runner then immediately moved on to item 2/6 (`q3bll1`, a `feature`), spending another ~240K+ tokens even though the same repo-wide `check.live-bug-ungated` error on the sibling open bugs guaranteed `q3bll1` and every remaining queued item would also `fail-gate`.

## Scope and required audit

1. **Preflight gate before spending turns:** Before creating lane worktrees or launching any agent turn in `aw agy run` and `aw oc run`, run the deterministic pre-existing checks whose failure guarantees a post-transition `fail-gate` (at minimum repo-level / cross-tree checks like `check.live-bug-ungated` and item-level preconditions that an agent turn cannot legitimately satisfy on its own), and refuse upfront with a clear, actionable remediation message.
2. **Codebase-wide audit for other guaranteed fail-gates:** Review all post-transition, post-execution, merge-and-revalidate, and handoff gates across `runner_shared.py`, `agy_runner.py`, `oc_runner.py`, `check_engine.py`, `backlog.py`, `ipd_lifecycle.py`, and `attention.py` to enumerate every check that can already be evaluated deterministically before dispatch (e.g., pre-existing `aw check all` errors, ungated live bugs, invalid `aw attention --check`, broken dependency/carrier invariants, missing required metadata, unauthored orchestrator children, etc.). Distinguish:
   - **Pre-existing guaranteed fail-gates** (the agent turn is NOT supposed to fix unrelated items on `main`, so dispatching wastes tokens -> MUST refuse upfront), vs.
   - **Checks the agent turn itself is meant to satisfy** (e.g., authoring the plans for the target backlog item -> must NOT block preflight).
3. **Avoid cascading futile dispatches:** If a repo-wide invariant (like `check.live-bug-ungated` on other open items) fails, stop the run / refuse the queue rather than dispatching remaining items one by one into the same guaranteed failure.
