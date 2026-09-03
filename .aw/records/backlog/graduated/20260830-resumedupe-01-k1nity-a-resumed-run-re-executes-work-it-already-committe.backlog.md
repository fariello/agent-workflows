- Id: k1nity
- Status: graduated
- Blocks-Release: next
- Set: resumedupe
- Priority: high
- Work-Kind: bug
- Summary: A resumed run re-executes work it already committed on its own lane, doubling spend, because telling the agent it is resuming is not enough to make it check

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the fix is not on main, so the item now carries Blocks-Release: next explicitly rather than relying on a successor plan to carry it.

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
