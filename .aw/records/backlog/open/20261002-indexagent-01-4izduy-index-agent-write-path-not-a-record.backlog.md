- Id: 4izduy
- Status: open
- Blocks-Release: next
- Set: indexagent
- Priority: medium
- Work-Kind: bug
- Summary: aw index --agent emits bare human text instead of an aw.agent/v1 record on its write path, for every type

## Workflow history
- 2026-10-02 created (aw backlog): aw index --agent emits bare human text instead of an aw.agent/v1 record on its write path, for every type

MEASURED 2026-10-02 at HEAD cb61fe319 while authoring plan 2zvxhx from backlog item 4uw9gy.

THE WRITE PATH OF 'aw index' IGNORES --agent AND PRINTS HUMAN TEXT. Measured per type:

    aw index plans --agent    -> up to date   .aw/records/plans/INDEX.json, INDEX.md (1237 plans)
    aw index prompts --agent  -> wrote INDEX.json (17 prompts) / wrote INDEX.md
    aw index specs --agent    -> WARN     'index' is not supported for specs.
    aw index backlog --agent  -> WARN     'index' is not supported for backlog.
    aw index research --agent -> <a bare frontmatter-invalid line>

None of those is an aw.agent/v1 record. An agent calling the verb cannot parse the result, cannot tell 'wrote' from 'up to date' structurally, and on an unsupported type receives a WARN line rather than a cannot-run record with exit 2.

THE --check PATH IS ALREADY CORRECT, which is what makes this a gap rather than an unconverted verb: plans_index.run_index routes its --check branch through artifact_core.emit_index_check_result and emits a valid record ({"schema":"aw.agent/v1","kind":"result","cmd":"index",...}), converted by plan n9ua3b (executed, Set tsvagent) which covered the three --check surfaces only. The write path falls through to the legacy print lines.

WHY IT IS A BUG: docs/cli-output-contract.md Section 10 rules 'Exactly one canonical machine format (aw.agent/v1) is active', and the same ruling is what n9ua3b cited to convert the --check surfaces. A verb that accepts --agent and answers in human prose is the same user-perceptible defect class as a flag that is silently dropped. Per AGENTS.md a live bug gates the next release, hence Blocks-Release: next.

NOT A --limit DEFECT, AND THIS CORRECTS THE RECORD. Backlog item 4uw9gy states --limit is inert on 'aw index'. That is FALSE and was re-measured while authoring 2zvxhx: with INDEX.md settled at the default window it carried 41 '## ' Set sections, 'aw index plans --agent --limit 3' rewrote it to 4, and restoring the default returned it to 41. The hot-window meaning (plans_index.DEFAULT_INDEX_LIMIT, consumed by run_index as 'limit = getattr(args, "limit", None) or DEFAULT_INDEX_LIMIT') is honored under --agent exactly as in the human path. 4uw9gy's own evidence line compared the one-line status message on stdout rather than the index file the command writes. 'aw index' is therefore OUT of plan 2zvxhx's scope entirely.

THE FIX NEEDS A DESIGN DECISION, which is why it is filed rather than folded into 2zvxhx. 'index' is a MUTATION verb that reports what it wrote, so the record needs a shape for that: the three observed outcomes (wrote / updated / up to date) map naturally onto CommandResult.changes plus the 'applied' flag, and the unsupported-type case should be a cannot-run record at exit 2 like _run_check's unknown-type branch already is. Deciding that shape touches plans_index.run_index, prompts_index and research_index together, since all three carry the same human-print write path. Note also that INDEX.md and INDEX.json are gitignored (.aw/.gitignore), so a test must assert on the file it writes rather than on git state.

Related: 4uw9gy (the --limit item this was found under, and whose index claim this corrects), plan 2zvxhx (which proves index untouched in its V-07), n9ua3b (the executed plan that converted the --check surfaces), 9qya0k.
