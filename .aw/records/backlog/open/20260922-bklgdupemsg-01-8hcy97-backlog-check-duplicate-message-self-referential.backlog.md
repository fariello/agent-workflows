- Id: 8hcy97
- Status: open
- Blocks-Release: next
- Set: bklgdupemsg
- Priority: medium
- Work-Kind: bug
- Summary: aw backlog check's id-duplicate message names the file as its own duplicate, so it cannot locate the other copy

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing ty7w6o. All 20 violations read 'id X also in <the same filename>', which tells an operator nothing about where the other copy is.

`aw backlog check` reports 20 violations at HEAD 64eb8406 and EVERY message is self-referential, e.g.

    20260830-gatejrnl-01-gjadwm-executed-transition-pre-commit-gate-false-positive.backlog.md: backlog.id-duplicate: id gjadwm also in 20260830-gatejrnl-01-gjadwm-executed-transition-pre-commit-gate-false-positive.backlog.md

The location and the claimed duplicate are the SAME string, so the message cannot lead an operator to the other copy and reads like a bug in the checker rather than a finding about the data.

CAUSE, at `agent_workflows/backlog.py:906-922` in `run_check`: both the `Drift` location and the remembered `seen_ids[pid]` are `f.name`, a BASENAME. All 20 duplicates are the same basename living in two different status directories (measured: every one is a `done`/`graduated` pair), so the two paths differ ONLY in the directory component that `f.name` discards.

FIX: remember and report the repo-relative path (`f.relative_to(repo_root)`) rather than `f.name`, so the message names the two distinct files.

SCOPE NOTE, so this is not mistaken for a duplicate of existing items. The underlying DUPLICATION is already filed as `fwq5nu` (which says eight items; it is now 20, worth updating there) and `5bmq5f` (the `egqt32` instance). This item is ONLY about the checker's message being unable to name the second location, which is a separate defect in the reporting and survives fixing the data.

USER-PERCEPTIBLE IMPACT, per the bug/chore test: an operator reading `aw backlog check` cannot act on any of the 20 findings without independently searching the tree, and is likely to conclude the checker is broken. That is a wrong-output defect, not merely an inefficiency.
