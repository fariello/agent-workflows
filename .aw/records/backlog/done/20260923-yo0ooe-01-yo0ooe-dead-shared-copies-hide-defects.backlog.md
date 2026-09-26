- Id: yo0ooe
- Status: done
- Set: yo0ooe
- Priority: medium
- Work-Kind: chore
- Summary: a dead symbol in runner_shared can carry defects indefinitely: four of the twelve unified symbols had an unreferenced shared copy, and two of those copies were broken in ways that would have fired on first call

## Workflow history
- 2026-09-26 done (aw set): DECLINED by maintainer 2026-09-26 (retired, not implemented): a structural fork-scan guard reverses the decision recorded in plan 0i4fkt (Carrier-Declined: restoring a fingerprint/refork guard reverses a maintainer decision). The four dead copies this item named are gone (63b71d8b); the one remaining genuine dead host copy (_record_forced_stop) is deleted by approved plan 184tn9.
- 2026-09-23 created (aw backlog): Found by hostdedup Order 02 (nmlx47) E-01/E-03/E-05. The four copies are gone (commit 63b71d8b); what is filed here is the DETECTION GAP that let them rot.

MEASURED 2026-09-23 at HEAD 525442c4 with tools/runner_fork_scan.py --triples.

THE PATTERN. The scanner's `--triples` mode reports a symbol defined in BOTH hosts AND ALSO in `runner_shared`, with the hosts ignoring the shared copy. Its own docstring calls this 'strictly worse than a two-way fork (three bodies to keep in step, and the shared one is dead)'. Four of the twelve symbols hostdedup Order 02 unified were in exactly that state, and BEING DEAD IS WHAT LET TWO OF THEM BE BROKEN:

  * `classify_recovery_disposition` carried FOUR defects, each fatal on first call: it read `st.path` and `st.base_commit`, neither of which exists on `worktree_lease.LaneState` (they are `worktree_path` and `base_sha`), so any resolvable lane raised AttributeError; it classified snapshots by a prefix the writer never emits, so it recognised NONE and would have routed preserved mid-edit work to verify-and-continue; it consulted neither `st.exists` nor `st.commits_ahead`; and it hard-coded `dirty=False`, discarding the field that tells a resumed agent the prior lane has uncommitted edits.
  * `_record_forced_stop` called `git_status(repo)` without the keyword-only `run_checked` that the shared `git_status` requires, so the swallowed TypeError would have written `git_state = \"<unobserved: ...>\"` in place of the observed tree on every level-4 stop.
  * `build_verify_and_continue_notice` and `reconcile_disposition` had drifted but were not broken (the latter was in fact the IMPROVED version, with helpers already factored out of it by `fduoj4`, which nobody reached).

WHY NO GUARD CAUGHT IT. Every existing census answers 'is this symbol forked?' or 'does this host delegate?'. None answers 'is this shared definition REACHED BY ANYBODY?'. A dead definition is invisible to the test suite by construction: no test imports it, so no test exercises its bugs, and a type checker sees a plausible function. The scanner CAN see it (`--triples`) but nothing consumes that output as a gate.

THE WORK. Make an unreferenced `runner_shared` definition a REPORTED condition rather than a mode of a measuring tool. Options, in rising cost: (a) a test that fails when `--triples` is non-empty, which is cheap and would have caught all four; (b) extend `tools/runner_fork_scan.py` to report shared definitions no host reaches even when the hosts do NOT define a twin, which is the more general 'dead shared code' question; (c) surface it in the Set's Order 04 acceptance criteria. Option (a) is probably enough, but it needs a decision about whether a deliberately-unreached shared symbol is ever legitimate (a scaffold for a not-yet-migrated host, say), which is why this is filed rather than just written.
