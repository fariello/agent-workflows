- Id: 72qlya
- Status: graduated
- Graduated-To: setprompt
- Blocks-Release: next
- Set: 72qlya
- Priority: high
- Work-Kind: bug
- Summary: migrate-layout preflight REFUSES any repo carrying .agents/skills: classify_item returns block-unknown, so aw migrate-layout and an interactive install-time migration both fail closed on the 2.0.0 upgrade path

## Workflow history
- 2026-09-25 graduated (aw set): graduated into setprompt: vv6y7e fixes the classifier; je74a0 depends on it
- 2026-09-25 note (aw backlog): Maintainer ruling 2026-09-25 (/askme on je74a0 OQ-04): scope widened to all three refusal triggers, .agents/skills AND the partial-aw .aw/.gitignore and .aw/setup-repo-needed.md; fixed by plan vv6y7e (setprompt Order 01).
- 2026-09-23 created (aw backlog): migrate-layout preflight REFUSES any repo carrying .agents/skills: classify_item returns block-unknown, so aw migrate-layout and an interactive install-time migration both fail closed on the 2.0.0 upgrade path

Found while executing plan z1yefm (migleftover Order 01).

WHAT IS WRONG
`layout_inventory.classify_item("agents", "skills/...")` falls through every branch to the
terminal `{ownership: unknown, disposition: block-unknown}` (layout_inventory.py:261-266). The
inventory turns that into an `unknown-owner` ERROR per path (layout_inventory.py:589-599),
`analyze_migration_risks` copies inventory errors into its own error list
(layout_inventory.py:796-798), and `execute_migration` raises `PreflightGateError` when the plan
is not valid (layout_migration.py:745-749). So a repo holding `.agents/skills` cannot be migrated
at all by that path.

WHY IT MATTERS
`.agents/skills` is the INTENDED skills location for BOTH layouts (`engine.SKILLS_DIR`,
`engine.resolve_skills_dir`), and the installer has emitted skill packages there since commit
5af28bbb. Every repo installed by a version carrying that commit therefore holds the directory,
and 2.0.0 exists to move those repos to `.aw`.

MEASURED (fixtures, four shapes, this worktree)
  legacy-no-skills     -> inventory errors: none;  execute_migration(remove) -> OK
  legacy-with-skills   -> unknown-owner x3;        execute_migration(remove) -> PreflightGateError
  residue-no-skills    -> inventory errors: none;  execute_migration(remove) -> OK
  residue-with-skills  -> unknown-owner x3;        execute_migration(remove) -> PreflightGateError

SCOPE NOTE / WHY NOT FIXED IN z1yefm
z1yefm's Scope-Paths do not include `layout_inventory.py`, and the decision of what disposition
`.agents/skills` should carry is a real one (`preserve` in place, matching the host-adapter
branch, looks right since the directory is shared by both layouts and must not be relocated) that
deserves its own review rather than being taken inside an unrelated plan. z1yefm reached its own
goal through `_handle_leftovers`, which is the deletion phase and is not gated by the preflight.

SUGGESTED FIX
Give `skills` an explicit branch in `classify_item`'s `label == "agents"` arm with
`disposition: preserve` and `expected_destination_class: host-adapter-in-place` (the same
treatment the host-adapter shims get, and for the same reason: a host tool scans a fixed path).
Read the prefix from `engine.SKILLS_DIR` rather than re-spelling it.
