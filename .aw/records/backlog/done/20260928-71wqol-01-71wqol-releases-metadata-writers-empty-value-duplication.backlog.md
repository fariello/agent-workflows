- Id: 71wqol
- Status: done
- Graduated-To: relwriteempty
- Blocks-Release: next
- Set: 71wqol
- Priority: medium
- Work-Kind: bug
- Summary: releases.set_from_backlog_line and set_blocks_release_line duplicate their field when an empty-valued line exists, because their \S+ value regex cannot match it; and aw ipd set --from-backlog writes any value unvalidated, so it can mint the dangling link check.from-backlog-dangling then errors on

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw oc run: IPD izh17y executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-relwriteempty-01-izh17y-make-the-releases-metadata-line-writers-tolerate-an-empty-va.ipd.md); evidence .aw/records/plans/executed/20260930-relwriteempty-01-izh17y-make-the-releases-metadata-line-writers-tolerate-an-empty-va.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: izh17y
- 2026-09-28 created (aw backlog): releases.set_from_backlog_line and set_blocks_release_line duplicate their field when an empty-valued line exists, because their \S+ value regex cannot match it; and aw ipd set --from-backlog writes any value unvalidated, so it can mint the dangling link check.from-backlog-dangling then errors on

MEASURED 2026-09-28 at HEAD `b471551a` during `/plan-review` of plan `0ykozn`, which found this while
being told to mirror `set_from_backlog_line` and correctly declined to inherit it.

DEFECT 1: THE WRITER DUPLICATES ITS OWN FIELD. `releases._FROM_BACKLOG_LINE_RE` is
`(?m)^- From-Backlog:[ \t]*\S+[ \t]*$\n?`. The `\S+` value group cannot match an EMPTY value, so the
idempotent strip that opens `set_from_backlog_line` misses an existing bare `- From-Backlog:` line and
the subsequent insert adds a second one:

        >>> from agent_workflows import releases as rel
        >>> t = "- Status: to-review\n- From-Backlog:\n- Id: abc123\n"
        >>> rel.set_from_backlog_line(t, "zzz999")
        '- Status: to-review\n- From-Backlog: zzz999\n- From-Backlog:\n- Id: abc123\n'
        >>> _.count("- From-Backlog:")
        2

The resulting duplicate is UNDIAGNOSABLE downstream, because every reader of the field uses
`.search()` and therefore sees only the FIRST match (`check_engine._ITEM_FROM_SPEC_RE` and
`releases._ITEM_FROM_BACKLOG_RE` alike). So the junk line is invisible to `aw check`.

THE CORRECT SHAPE IS ALREADY IN THE SAME MODULE, two functions away. `set_priority_line` and
`set_work_kind_line` use `[^\n]*` and their docstrings state the reason outright: "Tolerates any value
so an existing malformed line is still replaced." On the identical input they return ONE line:

        >>> rel.set_priority_line("- Status: to-review\n- Priority:\n- Id: abc123\n", "high")
        '- Status: to-review\n- Priority: high\n- Id: abc123\n'

`_ITEM_BLOCKS_RELEASE_RE` and `_ITEM_FROM_BACKLOG_RE` share the `\S+` shape and should be audited in
the same pass. `set_item_dependencies_line` already documents choosing differently from its `\S+`
siblings, so the module's inconsistency is known but was never resolved.

DEFECT 2: THE SETTER VALIDATES NOTHING. `aw ipd set --from-backlog <value>` writes whatever it is
handed: `status_set.apply_status_change`'s `from_backlog` block reads the value and calls the writer
with no resolution check, so an unresolvable id6 is persisted. `check.from-backlog-dangling` is
registered `error`, so the setter can mint exactly the finding CI then fails on. Its spec-side twin
`--from-spec` (shipping in plan `0ykozn`) is deliberately stricter and refuses an unresolvable value;
that asymmetry is the evidence this gap is a defect rather than a design choice.

WHY `bug` AND WHY IT GATES. Both defects are in shipped code on a tooled write path, and defect 2 lets
a sanctioned command produce a repository state that fails the repository's own error-severity check.
Per AGENTS.md a LIVE item whose work-kind is in the gating set must carry `- Blocks-Release:`.

HONEST LIMIT: NEITHER DEFECT IS LIVE TODAY. No artifact in the corpus carries an empty-valued
`- From-Backlog:`, `- Blocks-Release:` or `- From-Spec:` line (`rg -c "^- From-Spec:\s*$"
.aw/records/plans/` and the `From-Backlog` equivalent both return nothing), so nothing is corrupt right
now and this is latent rather than active corruption. It is filed because the trigger is a single
hand-edit or a cleared value away, and because plan `0ykozn` had to route around it.

RELATED. Plan `0ykozn` (`From-Spec` detector plus `--from-spec` setter) measured both defects, declined
to fix either as out of its declared scope, and carries this id6 in its `## Deferred` rows.
