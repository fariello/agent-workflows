- Id: 8t5ghs
- Status: done
- Set: 8t5ghs
- Priority: high
- Kind: chore
- Summary: aw install must ensure .aw/records/runs/ is gitignored (ipdrunner durable run state must never be committed)
- Blocks-Release: next

## Workflow history
- 2026-08-25 done (aw set): Verified implemented: aw install idempotently back-fills records/runs/ into .aw/.gitignore (engine.py:4757, template covers it). Executed IPD s2ufeo, commit b78501b.
- 2026-08-24 open (aw set): status set to open
- 2026-08-24 open (aw set): Release blocker for 2.0.0: install must guarantee records/runs/ is gitignored.
- 2026-08-24 created (aw backlog): aw install must ensure .aw/records/runs/ is gitignored (ipdrunner durable run state must never be committed)

The ipdrunner IPD driver writes per-run durable state under .aw/records/runs/<run-id>/ (queue state.json, session JSONL logs, prompts, outcomes, driver.lock). This is box-local, ephemeral working material and must never be committed. It was manually added to .aw/.gitignore in this repo, but a fresh install must guarantee the same. Requirement: 'aw install' (the per-repo installer/bootstrap that lays down the framework-owned .aw/ tree, including .aw/.gitignore) MUST ensure 'records/runs/' is present in .aw/.gitignore, idempotently (add it if missing, do not duplicate if already there), alongside the existing ignored lanes (records/*/untracked/, setup-repo-needed.md, records/history.jsonl). Consider covering it the same way those other ignore entries are guaranteed by install, and add/extend an install test asserting a fresh install produces a .aw/.gitignore that ignores records/runs/. Origin: ipdrunner run dirs were showing up as untracked noise; user asked that the ignore be part of aw install so no repo has to add it by hand.
