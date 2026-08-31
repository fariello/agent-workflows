- Id: k1nity
- Status: graduated
- Set: resumedupe
- Priority: high
- Work-Kind: bug
- Summary: A resumed run re-executes work it already committed on its own lane, doubling spend, because telling the agent it is resuming is not enough to make it check

## Workflow history
- 2026-08-31 graduated (aw set): Graduated to plan resumedupe-01 (txc9l1), carrying From-Backlog: k1nity. Key finding that redirected the fix: the item's own Q1 (put the lane state in the prompt) is ALREADY BUILT - build_recovery_lane_notice (oc_runipd.py:3485) already renders the lane branch, 'it HOLDS N commit(s) beyond its base', the dirty state and the INTERRUPTED SNAPSHOT explanation - and the duplication was measured AFTER that landed. So this is decisive evidence that informing is necessary and not sufficient, which is the argument for Q2: move the judgment to the DRIVER, which already holds every fact via the non-mutating worktree_lease.inspect_lane. Q3's completeness signal is the shipped 'WIP INTERRUPTED SNAPSHOT (not finished work)' commit (worktree_lease.py:699), which is what makes a blanket skip-if-commits-exist safe to avoid. No Blocks-Release: the item carries none and it is wasted spend, not data loss.
- 2026-08-30 created (aw backlog): A resumed run re-executes work it already committed on its own lane, doubling spend, because telling the agent it is resuming is not enough to make it check

OBSERVED 2026-08-30 on at least three resumed runs, with the duplication VERIFIED byte-identical.

WHAT HAPPENS. A run is interrupted mid-turn. Its lane branch already holds the agent's own commits.
On `aw oc run resume`, the item is correctly reconciled `running` -> `interrupted` -> `queued` and
re-dispatched in recovery mode. The agent then REDOES the work from scratch and commits it again,
producing a second, functionally identical commit pair on the same lane.

MEASURED on `ntf6sx` (lane `aw/lane/ntf6sx_attempt2`): FOUR commits where two were expected -
`fb0774b2 feat(reporting)...` + `5b8c0004 lifecycle(...)`, then `7e9c4444 feat(reporting)...` +
`3558ce1f lifecycle(...)`. `git diff fb0774b2 7e9c4444` over the plan's own files is EMPTY, so the
second pass changed nothing: it was pure duplicated spend. `zhr6mc`, `9trlc3` and `bmh754` show the
same 2-attempt shape in `aw runs`.

WHY "JUST TELL THE AGENT" IS NOT THE FIX, which is the important part. The runner ALREADY tells it.
`build_prompt` takes a `recovery` flag and renders `Mode: RECOVERY/CONTINUATION`, and plan `zwnjp3`
E-11 (merged 2026-08-30) deliberately enriched that branch to say the previous attempt was
interrupted and that the agent must establish current state itself. The maintainer chose that
lightweight approach over a heavier acknowledgement gate, and it was the right call at the time - but
this is the evidence that INFORMING IS NECESSARY AND NOT SUFFICIENT. The agent was told and still
redid its own committed work.

WHAT TO SOLVE FOR.

1. Should the PROMPT carry the lane's actual state rather than just the fact of interruption? Telling
   the agent "your lane already contains commit <sha> touching <files>, and here is the diff" is a
   much stronger signal than "you are resuming". This is cheap and probably the first thing to try.
2. Should the RUNNER detect it instead of delegating? Before dispatching a recovery turn it could
   compare the lane tip against the frozen base and, if the plan's own work appears present, route to
   a VERIFY-AND-CONTINUE turn rather than a fresh execution. That shifts the judgment from the agent
   to the driver, which is where the observable facts already live.
3. Is the duplication ever CORRECT? A turn interrupted mid-edit may have committed something
   incomplete, in which case redoing it is right. So the answer cannot be a blanket "skip if commits
   exist"; it needs a completeness signal. Note `zwnjp3` E-09 now snapshots uncommitted lane work as a
   marked interrupted-snapshot commit, which is exactly such a signal and should be consumed here.
4. What does this cost? Roughly one full turn per resumed item. In this session's runs a turn ranged
   from about $3 to about $30, so the waste is material but not catastrophic; the stronger argument is
   that duplicate commits pollute the lane history a human then has to read at merge time.

NOT A DATA-SAFETY BUG. Nothing was lost and the resulting trees are correct. This is wasted spend plus
a confusing lane history.

RELATED. `zwnjp3` E-09/E-11 (the snapshot and the recovery notice) are the substrate to build on.
Backlog `novalnomerge` compounds it: with validation off, nothing self-finalizes, so lanes accumulate
and resumes become more likely.
