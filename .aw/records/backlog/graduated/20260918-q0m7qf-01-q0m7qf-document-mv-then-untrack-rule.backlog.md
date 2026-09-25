- Id: q0m7qf
- Status: graduated
- Graduated-To: smallfix
- Set: q0m7qf
- Priority: low
- Work-Kind: followup
- Summary: Order 05's plan demanded history-follow AND an ignored destination, which git cannot satisfy with git mv alone; record the resolution so a future plan does not re-derive it

## Workflow history
- 2026-09-25 graduated (aw set): graduated into smallfix (plan 0i4fkt); verified live at 8e74dcac
- 2026-09-18 created (aw backlog): Order 05's plan demanded history-follow AND an ignored destination, which git cannot satisfy with git mv alone; record the resolution so a future plan does not re-derive it

Found while executing wfartifacts Order 05 (y4pptx). This is a DESIGN CONCERN that had to be worked around, not a code bug.

THE GAP: plan y4pptx required both (i) a relocated committed run record keeps its history reachable via `git log --follow` (E-03/V-03) and (ii) the relocated files 'end up ignored', proven with `git check-ignore` (E-02/V-02). Measured, `git mv` alone satisfies (i) and FAILS (ii): the moved path stays in the INDEX, where gitignore rules do not apply. The plan named no mechanism, so the executor had to derive one.

THE RESOLUTION, now implemented and worth keeping findable: `git mv` (commit it, so the rename is in the graph and --follow can traverse) THEN `git rm --cached` (commit that, so the path leaves the index and the ignore rule governs it). Untracking costs no history: --follow still reaches the pre-migration commits afterwards. Also measured: a path-scoped `git commit -- <paths>` re-reads those paths from the WORKING TREE, so it cannot express an index-only removal while the file is present; the implementation moves the destination aside for the duration of that one commit and restores it in a finally.

WHY FILE IT: the same tension will arise for any future 'relocate tracked content into an ignored tree' work (the `.aw/state/` and INDEX manifest trees have the same shape). The reasoning currently lives in `engine._commit_relocation`'s docstring and this turn's decisions register; a short note in the records-taxonomy or gitignore spec would make it discoverable to a plan AUTHOR rather than only to someone reading the migration code.

WHERE: agent_workflows/engine.py (_commit_relocation), and the spec that documents run-scratch placement (20260817-2124-01, u7xtni).
