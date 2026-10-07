- Id: 38hwvk
- Status: open
- Set: 38hwvk
- Priority: low
- Work-Kind: feature
- Summary: Add global fix-it turn caps per artifact, per Set, and per run on top of the per-kind retry budget

## Workflow history
- 2026-10-07 created (aw backlog): Maintainer request 2026-10-07 while scoping the correct-first retry policy

The runner bounds fix-it (correction) turns per FAILURE KIND: each kind (turn, finalize, verification, zero-work, merge-conflict send-back) has its own counter with the full `--retry-budget` (default 2; `run.retry_budget`; resolved by `runner_shared.resolve_retry_budget`, frozen per run via `frozen_retry_budget`). The correct-first retry policy (being planned 2026-10-07) makes many more failure kinds retryable, so one stubborn item can spend several paid turns across kinds.

Keep the per-kind default. ADD three global caps, each configurable:

- per artifact: total fix-it turns for one item across all kinds, default 20;
- per Set: max(20, 15 * number of Set members);
- per run: max(40, the per-Set max, 10 * number of artifacts in the run).

When a cap is hit, the item (or the remaining Set/run work) stops as needs-human with the cap named in the run report, rather than failing silently.

Low priority and NOT release-blocking (maintainer, 2026-10-07).
