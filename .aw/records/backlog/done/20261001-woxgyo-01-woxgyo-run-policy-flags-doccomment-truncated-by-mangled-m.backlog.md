- Id: woxgyo
- Status: done
- Graduated-To: woxgyo
- Set: woxgyo
- Priority: low
- Work-Kind: chore
- Summary: runner_shared RUN_POLICY_FLAGS doc-comment lost its final two lines to a mangled merge in 7dd1c486c, which also double-prefixed an ON_CONFLICT comment

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD 57v89t executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-woxgyo-01-57v89t-restore-the-two-truncated-run-policy-flags-doc-comment-lines.ipd.md); evidence .aw/records/plans/executed/20261002-woxgyo-01-57v89t-restore-the-two-truncated-run-policy-flags-doc-comment-lines.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: 57v89t
- 2026-10-01 created (aw backlog): Found while measuring rcp8c4's seven stale test_run_flag_surface citations: the same doc-comment block carries a separate, unrelated defect

MEASURED at HEAD `af30ba67f`. The `#:` doc-comment block immediately above `agent_workflows/runner_shared.RUN_POLICY_FLAGS` ends mid-sentence. Its last line reads:

    #: spells it `[--type <...>]...` - REPEATABLE, with 2.3 making repetition mean the UNION of the named
    #: #: Active runner conflict resolution modes.

Two defects in those two lines. FIRST, the sentence is TRUNCATED: `git show 7dd1c486c^:agent_workflows/runner_shared.py` shows the block ended with two further lines that no longer exist, namely `#: types, which is also what makes it the first flag able to produce a genuinely mixed selection and` / `#: therefore the first that can reach the shipped \`[RUN-MIXED-TYPES]\` gate.` SECOND, the line that replaced them carries a DOUBLED comment prefix (`#: #:`), which is the signature of a comment spliced into the wrong block rather than placed above its own symbol: `Active runner conflict resolution modes.` documents the `ON_CONFLICT_DROP`/`ON_CONFLICT_REFUSE`/`ON_CONFLICT_FORCE`/`ON_CONFLICT_PROMPT`/`ON_CONFLICT_ASK` constants that follow it, not `--type`'s multi-choice kind.

ATTRIBUTION: `git log -L` over those lines names `7dd1c486c` ("feat(runner): support configurable active runner conflict handling (drop, refuse, force, prompt)", 2026-09-25), whose diff shows the two surviving lines replaced by `+#: #: Active runner conflict resolution modes.` in a single hunk. So this is incidental damage from an unrelated feature commit, not a deliberate edit.

WHY THIS IS A `chore` AND NOT A `bug`, on the repository's perceptibility test: nothing executes, no operator sees it, and no computed behavior is wrong. A comment is invisible to the interpreter. The cost falls on a READER of the flag table, who meets a sentence that stops mid-clause and a stray prefix suggesting the block boundary is not where it appears.

THE FIX IS MECHANICAL AND THE PRIOR TEXT IS RECOVERABLE VERBATIM from `7dd1c486c^`: restore the two truncated lines to the end of the `RUN_POLICY_FLAGS` doc-comment, and give the `ON_CONFLICT` constants their own single-prefixed `#:` comment above `ON_CONFLICT_DROP`. No behavior changes and no test is needed beyond showing the module still imports and the suite count is unmoved.

NOT THE SAME DEFECT AS `rcp8c4`, which owns the seven stale `tests/test_run_flag_surface.py` guard citations in this same file (one of which sits in this very block). That item corrects FALSE CLAIMS about a deleted test; this one restores LOST PROSE and unpicks a misplaced comment. Surfaced by the measurement pass of `rcp8c4`'s graduation.
