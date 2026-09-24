- Id: mlc6mj
- Status: open
- Blocks-Release: next
- Set: planstale
- Priority: medium
- Work-Kind: bug
- Summary: An approved plan can be silently invalidated when the artifact it edits moves to a terminal state before it runs

## Workflow history
- 2026-09-23 created (aw backlog): An approved plan can be silently invalidated when the artifact it edits moves to a terminal state before it runs

FOUND while executing stalecrit-01 tgop8e on 2026-09-23.

THE DEFECT. Plan `tgop8e` was approved 2026-09-12 and declares `- Scope-Paths: .aw/records/plans/pending/20260910-rdyrecheck-01-qhy3i3-...ipd.md`. Its E-01 and E-02 repair two success criteria inside `qhy3i3`. On 2026-09-21 `qhy3i3` was EXECUTED (commit fe120181) and moved to `.aw/records/plans/executed/`. When `tgop8e` reached the queue on 2026-09-23 its two primary items were UNPERFORMABLE: `AGENTS.md:78` forbids adding commits to a plan already in `executed/`, and the declared scope path no longer exists.

WHY IT MATTERS. Nothing warned. The plan stayed `approved` with queue action `execute`, so the runner dispatched an agent turn for work that could not be done, and an executor less willing to stop could have edited a completed plan's audit trail to make its own checklist pass. This is the same class of staleness `tgop8e` itself was written to fix (an authored reference that drifts before execution), one level up: there the stale thing was a criterion's POPULATION, here it is the plan's TARGET.

EVIDENCE. `ls` on the declared pending path -> No such file or directory. `find .aw/records/plans -name '*qhy3i3*'` -> the executed/ path only. `git log --follow` -> `fe120181 2026-09-21 lifecycle(qhy3i3): finalize qhy3i3 -> executed`, nine days after tgop8e was approved.

POSSIBLE FIX, not designed here. A cheap deterministic check: at queue build or dispatch, verify every `- Scope-Paths:` entry of an approved plan still RESOLVES, and refuse or warn when one names a path that has moved or vanished. A stronger variant recognizes the specific case of a scope path pointing INTO `plans/pending/` for a plan now in a terminal directory, which is the shape here. An `aw check` rule would also catch it before a run starts. Note the dangling-scope-path case is distinct from the existing `check.from-backlog-dangling`/`check.from-spec-dangling` rules, which validate id references rather than scope paths.
